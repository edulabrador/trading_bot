"""
iterate.py
==========

Busqueda de mejoras con protocolo cerrado para no sobreoptimizar.
Ver research/PROTOCOLO.md. Resumen:

  - DESARROLLO: velas hasta el 2023-07-09 (trades cerrados antes de HOLDOUT).
    Dividido en dos mitades: A (< 2015-01-01) y B (2015-01-01 a HOLDOUT).
  - HOLDOUT: desde el 2023-07-10 (fecha en que se subieron los EAs al repo).
    No se mira para elegir variantes. Solo se revela con --reveal y solo para
    la variante que el script elige automaticamente con las reglas fijas.
  - Variantes fijadas de antemano (mismas para todos los bots), sin optimizar
    sus parametros: los multiplicadores ATR se calibran para igualar la
    distancia mediana original en desarrollo, no para maximizar beneficio.

Uso:
    python backtests/research/iterate.py --bot ema100_gbpjpy_h1 --csv backtests/data/GBPJPY_H1.csv
    python backtests/research/iterate.py ... --reveal      # al final, una sola vez
"""
from __future__ import annotations

import argparse
import importlib
import io
import json
import os
import sys
from contextlib import redirect_stdout
from dataclasses import fields, replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bots"))
sys.path.insert(0, os.path.dirname(HERE))
import engine as E  # noqa: E402

HOLDOUT = pd.Timestamp("2023-07-10")
HALF = pd.Timestamp("2015-01-01")

# Reglas de aceptacion (fijadas antes de ver resultados)
RULES = {"PF_dev_min": 1.10, "PF_half_min": 1.00, "robust_min": 0.80, "rand_pct_min": 0.80, "trades_dev_min": 100}


def pf(p):
    p = np.asarray(p, float)
    gl = -p[p < 0].sum()
    return float(p[p > 0].sum() / gl) if gl > 0 else (np.inf if len(p) else np.nan)


def stats(t: pd.DataFrame) -> dict:
    p = t["pnl_pips"].to_numpy(float) if len(t) else np.array([])
    if len(p) < 3:
        return {"trades": len(p), "PF": np.nan, "exp": np.nan, "net": float(p.sum()) if len(p) else 0, "t": np.nan, "maxDD": 0}
    eq = np.cumsum(p)
    return {"trades": len(p), "PF": round(pf(p), 3), "exp": round(p.mean(), 2), "net": round(p.sum()),
            "t": round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2),
            "maxDD": round(float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True, help="modulo en backtests/bots (sin .py)")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--n-robust", type=int, default=30)
    ap.add_argument("--n-random", type=int, default=20)
    ap.add_argument("--reveal", action="store_true", help="evalua en HOLDOUT la variante elegida (una sola vez)")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    bot = importlib.import_module(a.bot)
    h1 = bot.load_price_csv(a.csv)
    base = bot.Config()
    rng = np.random.default_rng(a.seed)
    fnames = {f.name for f in fields(base)}

    def run(cfg):
        with redirect_stdout(io.StringIO()):
            t, _, _ = bot.backtest(h1, cfg)
        if len(t) == 0:
            return pd.DataFrame({"exit_time": pd.Series(dtype="datetime64[ns]"), "pnl_pips": pd.Series(dtype=float)})
        t["exit_time"] = pd.to_datetime(t["exit_time"])
        return t

    def dev(t):
        return t[t.exit_time < HOLDOUT]

    # --- calibracion ATR en desarrollo (no usa resultados de trading)
    ctx = E.daily_context(h1[h1.index < HOLDOUT], h1.index[h1.index < HOLDOUT], base)
    med_atr_pips = float(np.nanmedian(ctx["atr"].to_numpy(float))) / base.pip
    sl_mult = round(base.stop_loss_pips / med_atr_pips, 3) if base.stop_loss_pips > 0 else 0.0
    tp_mult = round(base.take_profit_pips / med_atr_pips, 3) if base.take_profit_pips > 0 else 0.0
    is_jpy_cross = base.pip == 0.01

    # --- variantes fijadas de antemano (ronda 1)
    V = {
        "V0_baseline": base,
        "V1_atr_sltp": replace(base, sl_atr_mult=sl_mult, tp_atr_mult=tp_mult),
        "V2_d1_trend200": replace(base, d1_trend_sma=200),
        "V3_atr+trend": replace(base, sl_atr_mult=sl_mult, tp_atr_mult=tp_mult, d1_trend_sma=200),
        "V4_no_signal_exit": replace(base, use_signal_exit=False),
    }
    if is_jpy_cross and base.direction_mode == "both":
        V["V5_carry_long_only"] = replace(base, direction_mode="buy_only")
    if a.round >= 2 and hasattr(bot, "round2_variants"):
        V.update(bot.round2_variants(base, sl_mult, tp_mult))

    sens = [p for p in getattr(bot, "SENS_PARAMS", []) if p in fnames and p not in ("stop_loss_pips", "take_profit_pips")]

    def perturb(cfg):
        kw = {}
        for k in sens + ["stop_loss_pips", "take_profit_pips", "sl_atr_mult", "tp_atr_mult"]:
            v0 = getattr(cfg, k)
            if not v0:
                continue
            v = v0 * rng.uniform(0.8, 1.2)
            kw[k] = (max(1, int(round(v))) if v0 > 0 else int(round(v))) if isinstance(v0, int) else v
        return replace(cfg, **kw)

    def random_pct(cfg, t_dev):
        target = len(t_dev)
        exps = []
        prob = 0.02
        for it in range(a.n_random + 3):
            r = np.random.default_rng(1000 + it)

            def ov(i, lo, so, r=r, prob=prob):
                if r.random() >= prob:
                    return False, False
                go = r.random() < 0.5 if cfg.direction_mode == "both" else cfg.direction_mode == "buy_only"
                return go, not go
            E.set_entry_override(ov)
            try:
                tt = dev(run(cfg))
            finally:
                E.set_entry_override(None)
            if it < 3:  # calibrar frecuencia
                prob = min(0.9, prob * target / max(len(tt), 1))
                continue
            exps.append(tt.pnl_pips.mean() if len(tt) else np.nan)
        exps = np.array(exps, float)
        return float(np.nanmean(exps < t_dev.pnl_pips.mean()))

    rows = []
    for name, cfg in V.items():
        t = run(cfg)
        d = dev(t)
        sd, sa, sb = stats(d), stats(d[d.exit_time < HALF]), stats(d[d.exit_time >= HALF])
        rob = [pf(dev(run(perturb(cfg))).pnl_pips) for _ in range(a.n_robust)]
        rob_ok = float(np.mean(np.array(rob) > 1.0))
        rp = random_pct(cfg, d)
        passed = (sd["trades"] >= RULES["trades_dev_min"] and sd["PF"] >= RULES["PF_dev_min"]
                  and sa["PF"] >= RULES["PF_half_min"] and sb["PF"] >= RULES["PF_half_min"]
                  and rob_ok >= RULES["robust_min"] and rp >= RULES["rand_pct_min"])
        rows.append({"bot": a.bot, "round": a.round, "variant": name, "trades_dev": sd["trades"], "PF_dev": sd["PF"],
                     "exp_dev": sd["exp"], "t_dev": sd["t"], "maxDD_dev": sd["maxDD"], "PF_A_2006_14": sa["PF"],
                     "PF_B_2015_23": sb["PF"], "robust_PF>1": round(rob_ok, 2), "rand_pct": round(rp, 2),
                     "pasa_reglas": passed})
        print({k: rows[-1][k] for k in ("variant", "trades_dev", "PF_dev", "t_dev", "PF_A_2006_14", "PF_B_2015_23",
                                        "robust_PF>1", "rand_pct", "pasa_reglas")}, flush=True)

    res = pd.DataFrame(rows)
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    log = os.path.join(HERE, "logs", "variantes.csv")
    if not a.reveal:  # la revelacion repite la ronda; no duplicar el registro
        res.to_csv(log, mode="a", header=not os.path.exists(log), index=False)
    print(f"\ncalibracion ATR: ATR D1 mediano en desarrollo = {med_atr_pips:.1f} pips -> sl_mult {sl_mult}, tp_mult {tp_mult}")

    cand = res[res.pasa_reglas & (res.variant != "V0_baseline")]
    chosen = cand.sort_values("PF_dev", ascending=False).variant.iloc[0] if len(cand) else None
    print(f"variante elegida por las reglas: {chosen or 'NINGUNA'}")
    sel = {"bot": a.bot, "round": a.round, "chosen": chosen, "rules": RULES, "sl_mult": sl_mult, "tp_mult": tp_mult}
    with open(os.path.join(HERE, "logs", f"seleccion_{a.bot}_r{a.round}.json"), "w") as fh:
        json.dump(sel, fh, indent=2)

    if a.reveal:
        print("\n=== HOLDOUT (desde 2023-07-10) ===")
        for name in ["V0_baseline"] + ([chosen] if chosen else []):
            t = run(V[name])
            ho = t[t.exit_time >= HOLDOUT]
            s = stats(ho)
            print(name, s)
            with open(os.path.join(HERE, "logs", "holdout.csv"), "a") as fh:
                fh.write(f"{a.bot},{a.round},{name},{s['trades']},{s['PF']},{s['net']},{s['exp']},{s['t']},{s['maxDD']}\n")


if __name__ == "__main__":
    main()
