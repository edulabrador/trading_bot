"""
portfolio.py
============

Combina los trades de varios bots (los trades_base.csv que genera run_tests.py)
en una cartera y mide si la diversificacion ayuda: equity conjunta, drawdown,
correlacion mensual entre bots, IS/OOS y Monte Carlo de la cartera.

Uso:
    python backtests/portfolio.py --split 2023-07-10 \
        --bot "EMA100 v6=backtests/out/cand_ema100_v6/trades_base.csv:0.01:7" \
        --bot "USDJPY solo largos=backtests/out/cand_usdjpy_buyonly/trades_base.csv:0.01:7" \
        --bot "EURUSD R2c=backtests/out/cand_eurusd_r2c/trades_base.csv:0.01:10"

Cada --bot es "nombre=csv:lotes:valor_pip_por_lote". El resultado en dinero es
pips x lotes x valor del pip (aproximado, sin swap ni comision).
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd


def max_dd(x: np.ndarray) -> float:
    eq = np.cumsum(x)
    return float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()) if len(x) else 0.0


def pf(x) -> float:
    x = np.asarray(x, float)
    gl = -x[x < 0].sum()
    return float(x[x > 0].sum() / gl) if gl > 0 else np.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bot", action="append", required=True)
    ap.add_argument("--split", default=None)
    ap.add_argument("--out", default=None, help="markdown de salida")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)

    frames = []
    for spec in a.bot:
        name, rest = spec.split("=", 1)
        path, lots, pv = rest.rsplit(":", 2)
        t = pd.read_csv(path, parse_dates=["entry_time", "exit_time"])
        t["bot"] = name
        t["usd"] = t["pnl_pips"] * float(lots) * float(pv)
        frames.append(t[["bot", "entry_time", "exit_time", "pnl_pips", "usd"]])
    allt = pd.concat(frames).sort_values("exit_time").reset_index(drop=True)
    split = pd.Timestamp(a.split) if a.split else None
    md = []

    def say(s=""):
        print(s)
        md.append(s)

    say("# Cartera combinada\n")
    say("Resultado en divisa de cuenta = pips x lotes x valor del pip (aproximado, sin swap ni comision).\n")
    rows = []
    for name, g in list(allt.groupby("bot", sort=False)) + [("CARTERA", allt)]:
        u = g["usd"].to_numpy()
        r = {"bot": name, "trades": len(g), "neto": round(u.sum()), "PF": round(pf(u), 2), "maxDD": round(max_dd(u))}
        if split is not None:
            ui, uo = g[g.exit_time < split]["usd"].to_numpy(), g[g.exit_time >= split]["usd"].to_numpy()
            r.update({"neto IS": round(ui.sum()), "PF IS": round(pf(ui), 2), "neto OOS": round(uo.sum()),
                      "PF OOS": round(pf(uo), 2), "maxDD OOS": round(max_dd(uo))})
        rows.append(r)
    tab = pd.DataFrame(rows)
    say("| " + " | ".join(tab.columns) + " |")
    say("|" + "---|" * len(tab.columns))
    for _, r in tab.iterrows():
        say("| " + " | ".join(str(v) for v in r.values) + " |")

    m = allt.groupby([allt.exit_time.dt.to_period("M"), "bot"]).usd.sum().unstack(fill_value=0)
    say("\nCorrelacion de resultados mensuales entre bots:\n")
    c = m.corr().round(2)
    say("| | " + " | ".join(c.columns) + " |")
    say("|" + "---|" * (len(c.columns) + 1))
    for i, r in c.iterrows():
        say(f"| {i} | " + " | ".join(str(v) for v in r.values) + " |")

    tot = m.sum(axis=1)
    y = allt.groupby(allt.exit_time.dt.year).usd.sum().round(0)
    say("\nCartera por anio: " + ", ".join(f"{k}: {int(v)}" for k, v in y.items()))
    say(f"\nAnios negativos de la cartera: {(y < 0).sum()} de {len(y)}; meses negativos: {(tot < 0).mean() * 100:.0f}%")

    u = allt["usd"].to_numpy()
    dd = np.array([max_dd(rng.permutation(u)) for _ in range(5000)])
    k = max(1, int(round(len(u) / max((allt.exit_time.max() - allt.exit_time.min()).days / 365.25, 1e-9))))
    yr = rng.choice(u, size=(20000, k), replace=True).sum(1)
    say(f"\nMonte Carlo de la cartera: maxDD p50 {np.percentile(dd, 50):.0f}, p95 {np.percentile(dd, 5):.0f}, "
        f"p99 {np.percentile(dd, 1):.0f} (historico {max_dd(u):.0f}). "
        f"Probabilidad de perder en un anio (~{k} trades): {100 * (yr < 0).mean():.1f}%")
    sb = [max_dd(g["usd"].to_numpy()) for _, g in allt.groupby("bot")]
    say(f"\nSuma de los drawdowns individuales: {sum(sb):.0f}; drawdown de la cartera: {max_dd(u):.0f}. "
        "Si el de la cartera es claramente menor, la diversificacion esta ayudando.")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
