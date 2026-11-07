"""
check_forward.py
================

Compara el forward en demo (o real) con lo que esperaba el backtest, con reglas
de decision fijadas de antemano (ver forward/README.md).

Uso:
    python forward/check_forward.py forward_trades.csv
    python forward/check_forward.py forward_trades.csv --desde 2026-12-01

forward_trades.csv es el que genera el script ExportTrades.mq4 (MQL4/Files/).
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Reglas de decision (no cambiarlas despues de ver resultados)
MIN_TRADES = 20          # antes de esto no se decide nada
ALERT_PCT = 5            # forward peor que el 95% de lo esperado -> parar y revisar
PROMOTE_PCT = 20         # para pasar a real: al menos en el percentil 20 de lo esperado
PROMOTE_MONTHS = 12      # y al menos 12 meses de forward
N_BOOT = 20000


def pf(p):
    p = np.asarray(p, float)
    gl = -p[p < 0].sum()
    return float(p[p > 0].sum() / gl) if gl > 0 else (np.inf if len(p) else np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--desde", default=None, help="ignora operaciones cerradas antes de esta fecha")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    cfg = json.load(open(os.path.join(HERE, "bots.json"), encoding="utf-8"))

    f = pd.read_csv(a.csv)
    f["open_time"] = pd.to_datetime(f["open_time"].astype(str).str.replace(".", "-", regex=False))
    f["close_time"] = pd.to_datetime(f["close_time"].astype(str).str.replace(".", "-", regex=False))
    if a.desde:
        f = f[f.close_time >= pd.Timestamp(a.desde)]
    pip = np.where(f["digits"].isin([2, 3]), 0.01, 0.0001)
    sign = np.where(f["type"] == "BUY", 1, -1)
    f["pips"] = sign * (f["close_price"] - f["open_price"]) / pip
    f["neto_dinero"] = f["profit"] + f["swap"] + f["commission"]

    for magic, g in f.groupby("magic"):
        info = cfg.get(str(magic))
        name = info["nombre"] if info else f"magic {magic} (sin referencia)"
        g = g.sort_values("close_time")
        p = g["pips"].to_numpy(float)
        months = (g.close_time.max() - g.open_time.min()).days / 30.44 if len(g) else 0
        print(f"\n=== {name} ===")
        print(f"trades {len(p)} | meses {months:.1f} | pips {p.sum():+.0f} | PF {pf(p):.2f} | "
              f"aciertos {100 * (p > 0).mean():.0f}% | media {p.mean():+.1f} pips | dinero {g.neto_dinero.sum():+.2f} "
              f"(swap {g.swap.sum():+.2f}, comision {g.commission.sum():+.2f})")
        if not info or len(p) == 0:
            continue
        ref = pd.read_csv(os.path.join(ROOT, info["backtest"]), parse_dates=["exit_time"])
        col = "pnl_pct" if info.get("unidad") == "pct" else "pnl_pips"
        if col == "pnl_pct":  # indices: se compara el % de variacion por trade, no pips
            p = (np.where(g["type"] == "BUY", 1, -1) * (g["close_price"] - g["open_price"]) / g["open_price"] * 100).to_numpy(float)
            print(f"  (unidad: % por trade) total {p.sum():+.2f}% | PF {pf(p):.2f}")
        r_all = ref[col].to_numpy(float)
        r_ho = ref[ref.exit_time >= pd.Timestamp(info["holdout_desde"])][col].to_numpy(float)
        rows = []
        for lab, r in (("backtest completo", r_all), ("holdout del backtest", r_ho)):
            if len(r) < 10:
                continue
            sims = rng.choice(r, size=(N_BOOT, len(p)), replace=True).sum(1)
            pct = 100 * (sims < p.sum()).mean()
            rows.append((lab, pct, np.percentile(sims, 5), np.percentile(sims, 50), np.percentile(sims, 95)))
            u = "%" if col == "pnl_pct" else "pips"
            print(f"  vs {lab}: percentil {pct:.0f} | esperado para {len(p)} trades: p5 {np.percentile(sims, 5):+.1f}, "
                  f"p50 {np.percentile(sims, 50):+.1f}, p95 {np.percentile(sims, 95):+.1f} {u}")
        pct = rows[0][1] if rows else 50
        if len(p) < MIN_TRADES:
            verdict = f"SEGUIR EN DEMO: pocos trades ({len(p)} < {MIN_TRADES}) para decidir"
        elif pct < ALERT_PCT:
            verdict = "ALERTA: peor que el 95% de lo esperado. Parar y revisar (ejecucion, spreads, cambio de mercado)"
        elif months >= PROMOTE_MONTHS and pf(p) > 1 and pct >= PROMOTE_PCT:
            verdict = "CANDIDATO A REAL con lote minimo (y seguir vigilando)"
        else:
            verdict = "SEGUIR EN DEMO: dentro de lo esperado, aun sin evidencia suficiente"
        print(f"  -> {verdict}")


if __name__ == "__main__":
    main()
