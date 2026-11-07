"""
cross_market.py
===============

Valida un bot en pares que no se usaron para crearlo ni para mejorarlo, sin
cambiar sus reglas (ver research/PROTOCOLO.md, "Validacion en otros mercados").

Uso:
    python backtests/research/cross_market.py --bot ema100_gbpjpy_h1 --preset v6_no_ao_exit \
        --base backtests/data/GBPJPY_H1.csv --pairs EURJPY,AUDJPY,CADJPY
"""
from __future__ import annotations

import argparse
import importlib
import io
import os
import sys
from contextlib import redirect_stdout
from dataclasses import replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "bots"))
sys.path.insert(0, ROOT)
import engine as E  # noqa: E402

SPREADS = {"EURJPY": 2.0, "AUDJPY": 2.0, "CADJPY": 2.5, "GBPUSD": 1.5, "AUDUSD": 1.2,
           "USDCAD": 1.8, "USDCHF": 1.8, "NZDUSD": 2.0}
DEV_END = pd.Timestamp("2023-07-10")


def find_csv(sym):
    for name in (f"{sym}_H1.csv", f"{sym}_H1_2007_2023.csv"):
        p = os.path.join(ROOT, "data", name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(sym)


def med_atr_pips(h1, cfg, pip):
    d = h1[(h1.index >= "2007-01-01") & (h1.index < DEV_END)]
    ctx = E.daily_context(d, d.index, cfg)
    return float(np.nanmedian(ctx["atr"].to_numpy(float))) / pip


def stats(p):
    p = np.asarray(p, float)
    if len(p) < 3:
        return {"trades": len(p), "PF": np.nan, "net": round(p.sum()), "exp": np.nan, "t": np.nan, "maxDD": 0}
    gl = -p[p < 0].sum()
    eq = np.cumsum(p)
    return {"trades": len(p), "PF": round(p[p > 0].sum() / gl, 2) if gl > 0 else np.inf, "net": round(p.sum()),
            "exp": round(p.mean(), 1), "t": round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2),
            "maxDD": round(float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", required=True)
    ap.add_argument("--preset", default="baseline")
    ap.add_argument("--base", required=True, help="CSV del par original (para el escalado por ATR)")
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--min-share", type=float, default=0.6)
    ap.add_argument("--min-pooled-pf", type=float, default=1.05)
    a = ap.parse_args()

    bot = importlib.import_module(a.bot)
    cfg0 = bot.get_presets()[a.preset]
    base = bot.load_price_csv(a.base)
    atr_base = med_atr_pips(base, cfg0, cfg0.pip)
    atr_mode = cfg0.sl_atr_mult > 0 and cfg0.tp_atr_mult > 0

    rows, pooled = [], []
    for sym in a.pairs.split(","):
        h1 = bot.load_price_csv(find_csv(sym))
        pip = 0.01 if sym.endswith("JPY") else 0.0001
        point = pip / 10
        atr_new = med_atr_pips(h1, replace(cfg0, pip=pip), pip)
        ratio = atr_new / atr_base
        cfg = replace(cfg0, pip=pip, point=point, use_bar_spread=False, spread_pips=SPREADS[sym])
        if not atr_mode:
            cfg = replace(cfg, stop_loss_pips=round(cfg0.stop_loss_pips * ratio),
                          take_profit_pips=round(cfg0.take_profit_pips * ratio))
        with redirect_stdout(io.StringIO()):
            t, _, _ = bot.backtest(h1, cfg)
        p = t["pnl_pips"].to_numpy(float) if len(t) else np.array([])
        # normalizar a "unidades de SL original" para poder agregar pares de distinta volatilidad
        pooled.append(p / ratio)
        s = stats(p)
        rows.append({"par": sym, "datos": f"{h1.index[0]:%Y-%m} a {h1.index[-1]:%Y-%m}", "ATR ratio": round(ratio, 2),
                     "SL/TP": "ATR" if atr_mode else f"{cfg.stop_loss_pips:.0f}/{cfg.take_profit_pips:.0f}", **s})
        print(rows[-1], flush=True)
    res = pd.DataFrame(rows)
    allp = np.concatenate(pooled) if pooled else np.array([])
    sp = stats(allp)
    share = float((res.PF > 1).mean())
    ok = share >= a.min_share and sp["PF"] >= a.min_pooled_pf
    print(f"\nAGREGADO (pips normalizados por volatilidad): {sp}")
    print(f"Pares con PF>1: {(res.PF > 1).sum()}/{len(res)} | GENERALIZA: {'SI' if ok else 'NO'}")
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    res.assign(bot=a.bot, preset=a.preset).to_csv(os.path.join(HERE, "logs", "cross_market.csv"), mode="a",
                                                  header=not os.path.exists(os.path.join(HERE, "logs", "cross_market.csv")), index=False)
    with open(os.path.join(HERE, "logs", "cross_market_summary.csv"), "a") as fh:
        fh.write(f"{a.bot},{a.preset},{(res.PF > 1).sum()}/{len(res)},{sp['PF']},{sp['t']},{sp['trades']},{'SI' if ok else 'NO'}\n")


if __name__ == "__main__":
    main()
