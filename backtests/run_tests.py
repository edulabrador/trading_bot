"""
run_tests.py
============

Bateria de pruebas de robustez para un bot con la interfaz del backtester v5
(``bots/ea_gbpjpy_h1_ema100_v5.py``):

    Config (dataclass), get_presets(), load_price_csv(path),
    backtest(h1, cfg) -> (trades, equity, metrics), entry_signal(...)

Pruebas:
  1. Backtest base + IS/OOS + desglose anual + chequeos de modelo
  2. Costes (spread fijo, max spread, comision, swap opcional)
  3. Benchmark contra entradas aleatorias con las mismas reglas
  4. Monte Carlo (reordenar, bootstrap, horizontes, saltar trades + slippage)
  5. Robustez de parametros (uno a uno, todos a la vez, mapa SL x TP)
  6. Presets del propio bot
  7. Walk-forward (reoptimiza en N anios, prueba el siguiente)
  8. Regimen de mercado, dia de la semana y hora

Uso:
    python backtests/dukascopy.py GBPJPY --start 2006
    python backtests/run_tests.py --bot backtests/bots/ea_gbpjpy_h1_ema100_v5.py \
        --csv backtests/data/GBPJPY_H1.csv --split 2022-07-11

    # rapido (menos simulaciones):
    python backtests/run_tests.py ... --quick

Genera backtests/out/<nombre>/report.md, trades y tablas CSV.
Las metricas en PIPS son las fiables; las de dinero usan pip_value_per_lot fijo.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import sys
import warnings
from contextlib import redirect_stdout
from dataclasses import fields, replace

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DEFAULT_PARAMS = ["fi_period", "ao_level", "stop_loss_pips", "take_profit_pips", "trend_ema_period"]


# ----------------------------------------------------------------------------- utilidades
def load_bot(path: str):
    spec = importlib.util.spec_from_file_location("bot_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bot_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def summary(t: pd.DataFrame) -> dict:
    if t is None or len(t) == 0:
        return {"trades": 0, "net_pips": 0, "PF": np.nan, "win%": np.nan, "exp_pips": np.nan, "maxDD_pips": 0, "t": np.nan}
    p = t["pnl_pips"].astype(float)
    gl = -p[p < 0].sum()
    eq = p.cumsum()
    return {"trades": int(len(p)), "net_pips": round(float(p.sum())),
            "PF": round(float(p[p > 0].sum() / gl), 2) if gl > 0 else np.inf,
            "win%": round(100 * float((p > 0).mean()), 1), "exp_pips": round(float(p.mean()), 1),
            "maxDD_pips": round(float((eq - eq.cummax()).min())),
            "t": round(float(p.mean() / p.std(ddof=1) * np.sqrt(len(p))), 2) if len(p) > 2 else np.nan}


def max_dd(x: np.ndarray) -> float:
    eq = np.cumsum(x)
    return float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min())


def pf(p) -> float:
    p = np.asarray(p, float)
    gl = -p[p < 0].sum()
    return float(p[p > 0].sum() / gl) if gl > 0 else np.inf


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.values) + " |")
    return "\n".join(out)


# ----------------------------------------------------------------------------- swap GBPJPY (opcional)
# Tipos oficiales aproximados (BoE y BoJ). Fuente: memoria, revisar antes de usar en serio.
_BOE = [("2006-01-01", 4.5), ("2007-07-05", 5.75), ("2007-12-06", 5.5), ("2008-04-10", 5.0), ("2008-10-08", 4.5),
        ("2008-11-06", 3.0), ("2008-12-04", 2.0), ("2009-01-08", 1.5), ("2009-02-05", 1.0), ("2009-03-05", 0.5),
        ("2016-08-04", 0.25), ("2017-11-02", 0.5), ("2018-08-02", 0.75), ("2020-03-11", 0.25), ("2020-03-19", 0.1),
        ("2021-12-16", 0.25), ("2022-02-03", 0.5), ("2022-03-17", 0.75), ("2022-05-05", 1.0), ("2022-06-16", 1.25),
        ("2022-08-04", 1.75), ("2022-09-22", 2.25), ("2022-11-03", 3.0), ("2022-12-15", 3.5), ("2023-02-02", 4.0),
        ("2023-03-23", 4.25), ("2023-05-11", 4.5), ("2023-06-22", 5.0), ("2023-08-03", 5.25), ("2024-08-01", 5.0),
        ("2024-11-07", 4.75), ("2025-02-06", 4.5), ("2025-05-08", 4.25), ("2025-08-07", 4.0)]
_BOJ = [("2006-01-01", 0.0), ("2006-07-14", 0.25), ("2007-02-21", 0.5), ("2008-10-31", 0.3), ("2008-12-19", 0.1),
        ("2016-02-16", -0.1), ("2024-03-19", 0.05), ("2024-07-31", 0.25), ("2025-01-24", 0.5)]


def _step(tab):
    return pd.Series([v for _, v in tab], index=pd.to_datetime([d for d, _ in tab]))


def swap_cash_gbpjpy(t: pd.DataFrame, h1: pd.DataFrame, cfg, count_nights, markup: float = 1.0) -> np.ndarray:
    """Swap estimado de compras GBPJPY: (BoE - BoJ - markup)% anual sobre 100k GBP, en divisa de cuenta
    via pip_value_per_lot (1 pip = 1000 JPY por lote)."""
    boe, boj = _step(_BOE), _step(_BOJ)
    out = []
    for _, r in t.iterrows():
        diff = boe.asof(r.entry_time) - boj.asof(r.entry_time) - markup
        jpy_per_night = 100000 * h1["close"].asof(r.entry_time) * diff / 100 / 365
        acct = jpy_per_night / 1000.0 * cfg.pip_value_per_lot
        sign = 1 if r.direction == "BUY" else -1
        out.append(sign * acct * count_nights(r.entry_time, r.exit_time) * r.lots)
    return np.array(out)


# ----------------------------------------------------------------------------- pruebas
def main() -> None:
    ap = argparse.ArgumentParser(description="Bateria de pruebas de robustez para bots con interfaz v5")
    ap.add_argument("--bot", required=True)
    ap.add_argument("--csv", required=True, help="CSV H1 (p.ej. generado por dukascopy.py)")
    ap.add_argument("--preset", default="baseline")
    ap.add_argument("--split", default=None, help="fecha de corte IS/OOS (YYYY-MM-DD)")
    ap.add_argument("--params", default=",".join(DEFAULT_PARAMS), help="parametros de Config a perturbar")
    ap.add_argument("--wf-train-years", type=int, default=4)
    ap.add_argument("--swap-gbpjpy", action="store_true", help="estima el swap de GBPJPY con tipos BoE/BoJ")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default=None)
    a = ap.parse_args()

    ea = load_bot(a.bot)
    h1 = ea.load_price_csv(a.csv)
    cfg0 = ea.get_presets()[a.preset]
    rng = np.random.default_rng(a.seed)
    name = os.path.splitext(os.path.basename(a.bot))[0]
    outdir = a.outdir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", name)
    os.makedirs(outdir, exist_ok=True)
    split = pd.Timestamp(a.split) if a.split else None
    n_mc = 2000 if a.quick else 10000
    n_rand = 20 if a.quick else 60
    n_joint = 40 if a.quick else 150
    fnames = {f.name for f in fields(cfg0)}
    params = [p for p in a.params.split(",") if p in fnames]

    md: list[str] = []

    def say(s: str = "") -> None:
        print(s)
        md.append(s)

    def run(cfg):
        buf = io.StringIO()
        with redirect_stdout(buf):
            t, e, m = ea.backtest(h1, cfg)
        if len(t):
            t["entry_time"] = pd.to_datetime(t["entry_time"])
            t["exit_time"] = pd.to_datetime(t["exit_time"])
        return t, e, m

    def is_oos(t):
        if split is None or len(t) == 0:
            return None, None
        return t[t.exit_time < split], t[t.exit_time >= split]

    say(f"# Informe de robustez: {name}")
    say()
    say(f"- Datos: `{os.path.basename(a.csv)}`, {h1.index[0]} a {h1.index[-1]}, {len(h1):,} velas H1")
    if "spread_points" in h1:
        sp = h1["spread_points"] * cfg0.point / cfg0.pip
        say(f"- Spread por vela (pips): mediana {sp.median():.2f}, p95 {sp.quantile(.95):.2f}")
    say(f"- Preset: `{a.preset}` | corte IS/OOS: {a.split or 'ninguno'} | semilla {a.seed}")

    # 1. base -------------------------------------------------------------------------------
    t, eq, m = run(cfg0)
    t.to_csv(os.path.join(outdir, "trades_base.csv"), index=False)
    say("\n## 1. Backtest base\n")
    keys = ["trades", "trades_per_year", "win_rate_%", "profit_factor", "expectancy_pips", "avg_win_pips",
            "avg_loss_pips", "total_pips", "max_dd_closed_pips", "max_dd_float_pips", "max_consec_losses",
            "avg_hold_hours", "exit_mix", "exposure_%", "cagr_%"]
    say(md_table(pd.DataFrame({"metrica": keys, "valor": [m.get(k) for k in keys]})))
    s = summary(t)
    say(f"\nt-stat de la media por trade: **{s['t']}** (por debajo de ~2 no es concluyente)")
    p = t.pnl_pips.values
    e_ = np.cumsum(p)
    pk = np.maximum.accumulate(e_)
    uw, start, longest = e_ < pk, None, pd.Timedelta(0)
    for d, u in zip(t.exit_time, uw):
        if u and start is None:
            start = d
        if not u and start is not None:
            longest, start = max(longest, d - start), None
    if start is not None:
        longest = max(longest, t.exit_time.iloc[-1] - start)
    say(f"\nPeriodo mas largo sin nuevo maximo de equity (cerrada): **{longest.days} dias**")
    i_oos = is_oos(t)
    if i_oos[0] is not None:
        rows = [{"tramo": "IS (antes del corte)", **summary(i_oos[0])}, {"tramo": "OOS (desde el corte)", **summary(i_oos[1])}]
        say("\n" + md_table(pd.DataFrame(rows)))
    y = t.groupby(t.exit_time.dt.year).pnl_pips.agg(trades="size", pips="sum").round(0).astype(int)
    y.to_csv(os.path.join(outdir, "anual.csv"))
    say("\nPor anio (pips): " + ", ".join(f"{k}: {v}" for k, v in y.pips.items()))
    say(f"\nAnios negativos: {(y.pips < 0).sum()} de {len(y)}")
    # chequeos de modelo
    if "awesome_oscillator" in ea.compute_indicators(h1, cfg0).columns and hasattr(cfg0, "ao_level"):
        ao = ea.compute_indicators(h1, cfg0)["awesome_oscillator"]
        say(f"\nChequeo salida AO: el AO supera ao_level={cfg0.ao_level} en el {100 * (ao > cfg0.ao_level).mean():.2f}% "
            f"de las velas (p99 = {ao.quantile(.99):.2f}). Si es ~0%, la salida por senal no actua.")
    amb = sum(int(((h1.loc[r.entry_time:r.exit_time].low <= r.stop_loss) &
                   (h1.loc[r.entry_time:r.exit_time].high >= r.take_profit)).any()) for _, r in t.iterrows())
    say(f"\nTrades con SL y TP tocados en la misma vela H1: {amb} (si es >0, conviene usar datos M1/M15 con --ltf-csv)")

    # 2. costes -----------------------------------------------------------------------------
    say("\n## 2. Costes\n")
    rows = []
    for lab, cfg in [("spread real por vela", cfg0),
                     ("spread fijo 2.5", replace(cfg0, use_bar_spread=False, spread_pips=2.5)),
                     ("spread fijo 4.0", replace(cfg0, use_bar_spread=False, spread_pips=4.0)),
                     ("spread fijo 6.0", replace(cfg0, use_bar_spread=False, spread_pips=6.0)),
                     ("max_spread 4", replace(cfg0, max_spread_pips=4.0)),
                     ("comision 3.5/lado/lote", replace(cfg0, commission_per_lot_per_side=3.5))]:
        tt, _, mm = run(cfg)
        rows.append({"escenario": lab, **summary(tt), "neto_cash": round(mm.get("final_capital", 0) - cfg.initial_capital)})
    say(md_table(pd.DataFrame(rows)))
    if a.swap_gbpjpy:
        for mk in (1.0, 2.0):
            sw = swap_cash_gbpjpy(t, h1, cfg0, ea.count_swap_nights, mk)
            gross = t.pnl_cash.values
            say(f"\nSwap estimado (markup {mk}%): {sw.sum():+.0f} en divisa de cuenta; neto con swap {gross.sum() + sw.sum():.0f} "
                f"(sin swap {gross.sum():.0f}). Aproximacion con tipos oficiales; usa los swaps reales de tu broker.")

    # 3. benchmark aleatorio ----------------------------------------------------------------
    say("\n## 3. Benchmark: entradas aleatorias con las mismas reglas\n")
    if hasattr(ea, "entry_signal"):
        orig = ea.entry_signal
        target = len(t)

        def rand_run(prob, seed):
            r = np.random.default_rng(seed)

            def fake(fi_1, fi_2, close_1, ema_1, cfg):
                if r.random() >= prob:
                    return None
                if cfg.use_trend_filter and close_1 <= ema_1:
                    return None
                return ea.Direction.BUY if cfg.direction_mode != "sell_only" else ea.Direction.SELL
            ea.entry_signal = fake
            try:
                tt, _, _ = run(cfg0)
            finally:
                ea.entry_signal = orig
            return tt
        # calibrar probabilidad para un numero de trades parecido
        prob = 0.01
        for _ in range(4):
            n = max(len(rand_run(prob, 999)), 1)
            prob = min(0.9, prob * target / n)
        R = []
        for sd in range(n_rand):
            tt = rand_run(prob, sd)
            ri, ro = is_oos(tt)
            R.append({"trades": len(tt), "PF": pf(tt.pnl_pips), "exp": tt.pnl_pips.mean(),
                      "exp_OOS": ro.pnl_pips.mean() if ro is not None and len(ro) else np.nan})
        R = pd.DataFrame(R)
        say(f"{n_rand} simulaciones, ~{int(R.trades.median())} trades cada una (el bot: {len(t)}).\n")
        rows = [{"metrica": "ganancia media/trade (pips)", "bot": s["exp_pips"], "aleatorio p50": round(R.exp.median(), 1),
                 "p5": round(R.exp.quantile(.05), 1), "p95": round(R.exp.quantile(.95), 1),
                 "percentil del bot": f"{100 * (R.exp < s['exp_pips']).mean():.0f}%"},
                {"metrica": "profit factor", "bot": s["PF"], "aleatorio p50": round(R.PF.median(), 2),
                 "p5": round(R.PF.quantile(.05), 2), "p95": round(R.PF.quantile(.95), 2),
                 "percentil del bot": f"{100 * (R.PF < s['PF']).mean():.0f}%"}]
        if i_oos[1] is not None:
            eo = summary(i_oos[1])["exp_pips"]
            rows.append({"metrica": "ganancia media/trade OOS", "bot": eo, "aleatorio p50": round(R.exp_OOS.median(), 1),
                         "p5": round(R.exp_OOS.quantile(.05), 1), "p95": round(R.exp_OOS.quantile(.95), 1),
                         "percentil del bot": f"{100 * (R.exp_OOS < eo).mean():.0f}%"})
        say(md_table(pd.DataFrame(rows)))
        say("\nSi el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).")
    c = h1["close"]
    say(f"\nBuy & hold del simbolo: {(c.iloc[-1] - c.iloc[0]) / cfg0.pip:+.0f} pips en todo el periodo"
        + (f"; {(c.iloc[-1] - c.asof(split)) / cfg0.pip:+.0f} desde el corte" if split is not None else ""))

    # 4. monte carlo ------------------------------------------------------------------------
    say("\n## 4. Monte Carlo\n")
    n = len(p)
    yrs = max((t.exit_time.iloc[-1] - t.exit_time.iloc[0]).days / 365.25, 1e-9)
    rows = []
    dd_shuf = np.array([max_dd(rng.permutation(p)) for _ in range(n_mc // 2)])
    rows.append({"prueba": "reordenar trades", "resultado": f"maxDD p50 {np.percentile(dd_shuf, 50):.0f}, p95 {np.percentile(dd_shuf, 5):.0f}, "
                 f"p99 {np.percentile(dd_shuf, 1):.0f} pips (historico {max_dd(p):.0f})"})
    boot = rng.choice(p, size=(n_mc, n), replace=True)
    net = boot.sum(1)
    dds = np.array([max_dd(b) for b in boot[: n_mc // 4]])
    rows.append({"prueba": "bootstrap periodo completo", "resultado": f"P(neto<0) {100 * (net < 0).mean():.1f}%, neto p5/p50/p95 "
                 f"{np.percentile(net, 5):.0f}/{np.percentile(net, 50):.0f}/{np.percentile(net, 95):.0f}, maxDD p95 {np.percentile(dds, 5):.0f}"})
    if i_oos[1] is not None and len(i_oos[1]) > 5:
        po = i_oos[1].pnl_pips.values
        bo = rng.choice(po, size=(n_mc, len(po)), replace=True).sum(1)
        rows.append({"prueba": "bootstrap solo OOS", "resultado": f"P(neto<0) {100 * (bo < 0).mean():.1f}% con {len(po)} trades"})
    for h in (1, 2, 3):
        k = max(1, int(round(n / yrs * h)))
        sm = rng.choice(p, size=(n_mc * 2, k), replace=True).sum(1)
        rows.append({"prueba": f"horizonte {h} anio(s) (~{k} trades)",
                     "resultado": f"P(perder) {100 * (sm < 0).mean():.1f}%, p5 {np.percentile(sm, 5):.0f}, p50 {np.percentile(sm, 50):.0f} pips"})
    res = []
    for _ in range(n_mc // 2):
        keep = rng.random(n) > 0.2
        q = (p + rng.normal(-1.0, 2.0, n))[keep]
        res.append((q.sum(), pf(q)))
    res = np.array(res)
    rows.append({"prueba": "saltar 20% trades + slippage N(-1,2)", "resultado": f"PF p5 {np.percentile(res[:, 1], 5):.2f}, p50 "
                 f"{np.percentile(res[:, 1], 50):.2f}; P(neto<0) {100 * (res[:, 0] < 0).mean():.1f}%"})
    say(md_table(pd.DataFrame(rows)))
    pv = cfg0.pip_value_per_lot
    say(f"\nGuia de tamano (pip_value_per_lot={pv}): maxDD p99 de reordenar = {abs(np.percentile(dd_shuf, 1)):.0f} pips "
        f"= {abs(np.percentile(dd_shuf, 1)) * pv * 0.01:.0f} por 0.01 lotes, {abs(np.percentile(dd_shuf, 1)) * pv * 0.10:.0f} por 0.10 lotes.")

    # 5. parametros -------------------------------------------------------------------------
    say("\n## 5. Robustez de parametros\n")
    rows = []
    for key in params:
        v0 = getattr(cfg0, key)
        for f in (0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
            v = type(v0)(round(v0 * f)) if isinstance(v0, int) else round(v0 * f, 4)
            tt, _, _ = run(replace(cfg0, **{key: v}))
            ss = summary(tt)
            so = summary(is_oos(tt)[1]) if split is not None else {}
            rows.append({"param": key, "valor": v, "trades": ss["trades"], "net_pips": ss["net_pips"], "PF": ss["PF"],
                         "PF_OOS": so.get("PF", "")})
    sens = pd.DataFrame(rows)
    sens.to_csv(os.path.join(outdir, "sensibilidad.csv"), index=False)
    say(md_table(sens))
    jr = []
    for _ in range(n_joint):
        kw = {}
        for key in params:
            v0 = getattr(cfg0, key)
            v = v0 * rng.uniform(0.8, 1.2)
            kw[key] = max(1, int(round(v))) if isinstance(v0, int) else v
        tt, _, _ = run(replace(cfg0, **kw))
        jr.append((summary(tt)["PF"], summary(is_oos(tt)[1])["PF"] if split is not None else np.nan))
    jr = np.array(jr, float)
    say(f"\nTodos los parametros +-20% a la vez ({n_joint} combinaciones): PF>1 en {(jr[:, 0] > 1).sum()}/{n_joint}, "
        f"PF mediana {np.nanmedian(jr[:, 0]):.2f}, p5 {np.nanpercentile(jr[:, 0], 5):.2f}"
        + (f"; OOS PF>1 en {(jr[:, 1] > 1).sum()}/{n_joint}" if split is not None else ""))
    if {"stop_loss_pips", "take_profit_pips"} <= fnames:
        sl0, tp0 = cfg0.stop_loss_pips, cfg0.take_profit_pips
        grid = {}
        for fs in (0.6, 0.8, 1.0, 1.2, 1.5):
            for ft in (0.5, 0.75, 1.0, 1.25, 1.6):
                tt, _, _ = run(replace(cfg0, stop_loss_pips=round(sl0 * fs), take_profit_pips=round(tp0 * ft)))
                grid[(round(sl0 * fs), round(tp0 * ft))] = summary(tt)["PF"]
        g = pd.Series(grid).unstack()
        g.index.name = "SL \\ TP"
        say("\nPF por SL (filas) x TP (columnas):\n")
        say(md_table(g.reset_index()))

    # 6. presets ----------------------------------------------------------------------------
    say("\n## 6. Presets del bot\n")
    rows = []
    for pname, cfg in ea.get_presets().items():
        tt, _, _ = run(cfg)
        ss = summary(tt)
        so = summary(is_oos(tt)[1]) if split is not None else {}
        rows.append({"preset": pname, "trades": ss["trades"], "net_pips": ss["net_pips"], "PF": ss["PF"],
                     "maxDD_pips": ss["maxDD_pips"], "PF_OOS": so.get("PF", ""), "net_OOS": so.get("net_pips", "")})
    say(md_table(pd.DataFrame(rows)))
    say("\nOjo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.")

    # 7. walk-forward -----------------------------------------------------------------------
    say("\n## 7. Walk-forward\n")
    wf_keys = [k for k in ("fi_period", "stop_loss_pips", "take_profit_pips") if k in fnames]
    if wf_keys:
        levels = [(0.75, 1.0, 1.3)] * len(wf_keys)
        combos = [dict(zip(wf_keys, c)) for c in np.array(np.meshgrid(*levels)).T.reshape(-1, len(wf_keys))]
        cache = {}
        for c in combos:
            kw = {k: (int(round(getattr(cfg0, k) * f)) if isinstance(getattr(cfg0, k), int) else getattr(cfg0, k) * f)
                  for k, f in c.items()}
            tt, _, _ = run(replace(cfg0, **kw))
            cache[tuple(kw.values())] = tt
        tr = a.wf_train_years
        y0, y1 = t.exit_time.dt.year.min() + tr, t.exit_time.dt.year.max()
        rows = []
        for ty in range(y0, y1 + 1):
            A, B, C = pd.Timestamp(f"{ty - tr}-01-01"), pd.Timestamp(f"{ty}-01-01"), pd.Timestamp(f"{ty + 1}-01-01")

            def score(tt):
                ss = tt[(tt.exit_time >= A) & (tt.exit_time < B)].pnl_pips
                return ss.sum() if len(ss) >= 10 else -1e18
            best = max(cache, key=lambda k: score(cache[k]))
            bt = cache[best]
            o = bt[(bt.exit_time >= B) & (bt.exit_time < C)].pnl_pips
            base_y = t[(t.exit_time >= B) & (t.exit_time < C)].pnl_pips
            rows.append({"anio": ty, "params " + "/".join(wf_keys): "/".join(f"{v:.0f}" for v in best),
                         "IS pips/anio": round(score(bt) / tr), "OOS pips": round(o.sum()), "OOS trades": len(o),
                         "base pips": round(base_y.sum())})
        wf = pd.DataFrame(rows)
        say(md_table(wf))
        eff = wf["OOS pips"].mean() / wf["IS pips/anio"].mean() if wf["IS pips/anio"].mean() > 0 else np.nan
        say(f"\nTotal OOS walk-forward {wf['OOS pips'].sum():.0f} pips (base {wf['base pips'].sum():.0f}); "
            f"anios positivos {(wf['OOS pips'] > 0).sum()}/{len(wf)}; eficiencia {eff:.2f} (>0.5 suele considerarse aceptable)")

    # 8. regimen ----------------------------------------------------------------------------
    say("\n## 8. Regimen, dia y hora\n")
    d1 = h1["close"].resample("D").last().dropna()
    up = (d1 > d1.rolling(200).mean()).reindex(t.entry_time, method="ffill").values
    t["regimen"] = np.where(up, "D1 > SMA200", "D1 < SMA200")
    say(md_table(t.groupby("regimen").pnl_pips.agg(trades="size", pips="sum", media="mean").round(1).reset_index()))
    dow = t.groupby(t.entry_time.dt.dayofweek).pnl_pips.agg(trades="size", pips="sum").round(0)
    dow.index = [["lun", "mar", "mie", "jue", "vie", "sab", "dom"][i] for i in dow.index]
    say("\nPor dia de entrada: " + ", ".join(f"{k} {int(v.pips)} ({int(v.trades)})" for k, v in dow.iterrows()))
    hr = t.groupby(t.entry_time.dt.hour).pnl_pips.sum().round(0)
    say("\nPor hora de entrada (pips): " + ", ".join(f"{k}h {int(v)}" for k, v in hr.items()))
    say("\nNo filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.")

    with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print(f"\nInforme: {os.path.join(outdir, 'report.md')}")


if __name__ == "__main__":
    main()
