"""
s2_deep.py: pruebas en profundidad de S2 (RSI(2) de Connors en indices) tras
pasar las reglas de NUEVAS_ESTRATEGIAS.md. Genera reports/s2_indices_rsi2.md.
"""
from __future__ import annotations

import os
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import daily as D  # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "reports", "s2_indices_rsi2.md")
rng = np.random.default_rng(5)
md = []


def say(s=""):
    print(s)
    md.append(s)


def table(df):
    say("| " + " | ".join(map(str, df.columns)) + " |")
    say("|" + "---|" * len(df.columns))
    for _, r in df.iterrows():
        say("| " + " | ".join(str(v) for v in r.values) + " |")


def maxdd(x):
    eq = np.cumsum(x)
    return float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()) if len(x) else 0.0


VARIANT = sys.argv[1] if len(sys.argv) > 1 else "original"
data = D.universe(D.INDICES)
p0 = D.P() if VARIANT == "original" else D.P(exit_mode="rsi", exit_rsi=70.0)
if VARIANT != "original":
    OUT = os.path.join(ROOT, "reports", "s2_m1_indices_rsi2.md")
t = D.run_all(data, "S2", p0)
t["hold_days"] = (t.exit_time - t.entry_time).dt.days
dev, ho = t[t.exit_time < D.HOLDOUT], t[t.exit_time >= D.HOLDOUT]

say("# S2" + (" con mejora M1 (salida RSI(2) > 70)" if VARIANT != "original" else "") + ": reversion a la media en indices (RSI(2) de Connors)\n")
say("Reglas fijadas antes de ver resultados en "
    "[`../research/NUEVAS_ESTRATEGIAS.md`](../research/NUEVAS_ESTRATEGIAS.md). Entrada: solo largos si cierre > SMA(200) "
    "y RSI(2) < 10, ejecutando en la apertura del dia siguiente. Salida: cierre > SMA(5). Sin stop. Resultados en R "
    "(beneficio / ATR(20) diario en la entrada), con spread incluido y sin financiacion del CFD.\n")
say("Datos: S&P 500 (Yahoo, 2007-2026), Nasdaq 100 (Dukascopy, 2011-2025), DAX (Dukascopy, 2013-2025).\n")

say("## 1. Resultados\n")
rows = []
for lab, g in [("desarrollo (hasta 09/07/2023)", dev), ("holdout (desde 10/07/2023)", ho), ("total", t)]:
    s = D.st(g.R)
    rows.append({"tramo": lab, "trades": s["trades"], "PF": s["PF"], "R total": s["R"], "R/trade": s.get("expR"),
                 "t": s["t"], "maxDD (R)": s.get("maxDD_R"), "aciertos": f"{100 * (g.R > 0).mean():.0f}%"})
table(pd.DataFrame(rows))
say("")
rows = []
for n, g in t.groupby("sym"):
    for lab, gg in [("desarrollo", g[g.exit_time < D.HOLDOUT]), ("holdout", g[g.exit_time >= D.HOLDOUT])]:
        s = D.st(gg.R)
        rows.append({"indice": n, "tramo": lab, "trades": s["trades"], "PF": s["PF"], "R": s["R"], "t": s["t"]})
table(pd.DataFrame(rows))
y = t.groupby(t.exit_time.dt.year).R.sum().round(1)
say("\nR por anio: " + ", ".join(f"{k}: {v}" for k, v in y.items()))
say(f"\nAnios negativos: {(y < 0).sum()} de {len(y)}. Duracion media de cada trade: {t.hold_days.mean():.1f} dias "
    f"(mediana {t.hold_days.median():.0f}). Trades al anio: {len(t) / ((t.exit_time.max() - t.entry_time.min()).days / 365.25):.0f}.")

say("\n## 2. Peores trades (no hay stop)\n")
w = t.nsmallest(8, "R")[["sym", "entry_time", "exit_time", "hold_days", "R"]].copy()
w["entry_time"], w["exit_time"], w["R"] = w.entry_time.dt.date, w.exit_time.dt.date, w.R.round(2)
table(w)
say(f"\nEl peor trade pierde {t.R.min():.1f} R. Una posicion se mide en R = ATR(20) diario; con un riesgo de 0.5% de "
    f"la cuenta por R, el peor trade habria costado un {abs(t.R.min()) * 0.5:.1f}% de la cuenta.")

say("\n## 3. Costes\n")
rows = []
for mult in (1, 2, 3, 5):
    out = []
    for n, d in data.items():
        tt = D.backtest(d[d.index >= "2005-06-01"], "S2", p0, D.SPREAD[n] * mult)
        out.append(tt[tt.entry_time >= D.START])
    tt = pd.concat(out)
    s = D.st(tt.R)
    rows.append({"spread": f"x{mult}", "PF": s["PF"], "R total": s["R"], "PF holdout": D.st(tt[tt.exit_time >= D.HOLDOUT].R)["PF"]})
table(pd.DataFrame(rows))
say("\nFinanciacion del CFD (no incluida): con trades de unos pocos dias, un coste anual del 5-7% sobre el nominal "
    "supone del orden de 0.05-0.1% por trade. Conviene medirlo en la demo con el broker real.")

say("\n## 4. Sensibilidad de parametros (uno a uno)\n")
rows = []
for key, vals in {"rsi_lo": [5, 7.5, 10, 12.5, 15], "sma_trend": [100, 150, 200, 250, 300], "sma_exit": [3, 4, 5, 7, 10],
                  "rsi_n": [2, 3, 4]}.items():
    for v in vals:
        tt = D.run_all(data, "S2", replace(p0, **{key: v}))
        s, sh = D.st(tt[tt.exit_time < D.HOLDOUT].R), D.st(tt[tt.exit_time >= D.HOLDOUT].R)
        rows.append({"parametro": key, "valor": v, "trades": s["trades"], "PF desarrollo": s["PF"], "PF holdout": sh["PF"]})
table(pd.DataFrame(rows))

say("\n## 5. Monte Carlo\n")
r = t.R.to_numpy()
dd = np.array([maxdd(rng.permutation(r)) for _ in range(5000)])
tpy = len(r) / ((t.exit_time.max() - t.entry_time.min()).days / 365.25)
rows = [{"prueba": "reordenar trades", "resultado": f"maxDD p50 {np.percentile(dd, 50):.1f} R, p95 {np.percentile(dd, 5):.1f}, p99 {np.percentile(dd, 1):.1f} (historico {maxdd(r):.1f})"}]
boot = rng.choice(r, size=(10000, len(r)), replace=True).sum(1)
rows.append({"prueba": "bootstrap total", "resultado": f"P(neto<0) {100 * (boot < 0).mean():.2f}%"})
for h in (1, 2):
    k = max(1, int(round(tpy * h)))
    s = rng.choice(r, size=(20000, k), replace=True).sum(1)
    rows.append({"prueba": f"horizonte {h} anio(s) (~{k} trades)", "resultado": f"P(perder) {100 * (s < 0).mean():.1f}%, p5 {np.percentile(s, 5):.1f} R, p50 {np.percentile(s, 50):.1f} R"})
res = []
for _ in range(5000):
    keep = rng.random(len(r)) > 0.2
    q = (r + rng.normal(-0.05, 0.1, len(r)))[keep]
    res.append(D.pf(q))
rows.append({"prueba": "saltar 20% trades + slippage N(-0.05R, 0.1R)", "resultado": f"PF p5 {np.percentile(res, 5):.2f}, p50 {np.percentile(res, 50):.2f}"})
table(pd.DataFrame(rows))

say("\n## 6. Validacion en otro mercado registrada de antemano: oro\n")
g = D.universe(["XAUUSD"])["XAUUSD"]
tg = D.backtest(g[g.index >= "2005-06-01"], "S2", p0, D.SPREAD["XAUUSD"])
tg = tg[tg.entry_time >= D.START]
for lab, gg in [("desarrollo", tg[tg.exit_time < D.HOLDOUT]), ("holdout", tg[tg.exit_time >= D.HOLDOUT]), ("total", tg)]:
    s = D.st(gg.R)
    say(f"- XAUUSD {lab}: {s['trades']} trades, PF {s['PF']}, R {s['R']}, t {s['t']}")

say("\n## 7. Correlacion con el EMA100 v6 y cartera\n")
ema = pd.read_csv(os.path.join(ROOT, "..", "forward", "reference", "43898.csv"), parse_dates=["exit_time"])
ema_m = ema.groupby(ema.exit_time.dt.to_period("M")).pnl_pips.sum()
s2_m = t.groupby(t.exit_time.dt.to_period("M")).R.sum()
both = pd.concat([ema_m.rename("ema"), s2_m.rename("s2")], axis=1).fillna(0)
both = both[both.index >= pd.Period("2007-10", "M")]
c = both.corr().iloc[0, 1]
say(f"Correlacion mensual EMA100 v6 (GBPJPY) vs S2: **{c:.2f}** (la regla pide < 0.3).")
# cartera: EMA100 a riesgo comparable. 1 R de S2 = 0.5% cuenta; EMA100 0.01 lotes por 10k (SL 165 pips ~ 1.16% cuenta)
cap = 10000
ema_usd = ema.set_index("exit_time").pnl_pips * 0.01 * 7
s2_usd = t.set_index("exit_time").R * cap * 0.005
pm = pd.concat([ema_usd.groupby(ema_usd.index.to_period("M")).sum().rename("EMA100"),
                s2_usd.groupby(s2_usd.index.to_period("M")).sum().rename("S2")], axis=1).fillna(0)
pm = pm[pm.index >= pd.Period("2007-10", "M")]
pm["cartera"] = pm.sum(axis=1)
rows = []
for col in ["EMA100", "S2", "cartera"]:
    x = pm[col].to_numpy()
    rows.append({"componente": col, "neto (10k)": round(x.sum()), "anual medio": round(x.sum() / (len(x) / 12)),
                 "maxDD mensual": round(maxdd(x)), "meses negativos": f"{100 * (x < 0).mean():.0f}%",
                 "neto desde 07/2023": round(pm[pm.index >= pd.Period("2023-07", "M")][col].sum())})
table(pd.DataFrame(rows))
say("\nSupuestos: EMA100 v6 a 0.01 lotes (pips x 0.01 x 7 USD); S2 arriesgando el 0.5% de 10,000 por cada R "
    "(1 ATR diario). Sin swap ni financiacion. Drawdown calculado sobre resultados mensuales.")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(md) + "\n")
t.to_csv(os.path.join(HERE, "logs", "trades_S2.csv" if VARIANT == "original" else "trades_S2_M1.csv"), index=False)
