"""Partes 1 (EMA100) y 3 de PRUEBAS_EXIGENTES.md. Genera reports/exigentes_ema100.md."""
from __future__ import annotations

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
import ema100_gbpjpy_h1 as M  # noqa: E402

HOLD = pd.Timestamp("2023-07-10")
md = []


def say(s=""):
    print(s, flush=True)
    md.append(s)


def table(df):
    say("| " + " | ".join(map(str, df.columns)) + " |")
    say("|" + "---|" * len(df.columns))
    for _, r in df.iterrows():
        say("| " + " | ".join(str(v) for v in r.values) + " |")


def st(p):
    p = np.asarray(p, float)
    if len(p) < 3:
        return {"trades": len(p), "PF": np.nan, "net": round(p.sum()) if len(p) else 0, "maxDD": 0}
    gl = -p[p < 0].sum()
    eq = np.cumsum(p)
    return {"trades": len(p), "PF": round(p[p > 0].sum() / gl, 2), "net": round(p.sum()),
            "maxDD": round(float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()))}


def bt(h1, cfg, sigfn=M.signals):
    with redirect_stdout(io.StringIO()):
        t, e, m = E.backtest(h1, cfg, sigfn, warmup=M.WARMUP)
    t["entry_time"], t["exit_time"] = pd.to_datetime(t.entry_time), pd.to_datetime(t.exit_time)
    return t, e


h1 = M.load_price_csv(os.path.join(ROOT, "data", "GBPJPY_H1.csv"))
base = M.get_presets()["v6_no_ao_exit"]
t0, e0 = bt(h1, base)

say("# Pruebas exigentes: EMA100 v6 (GBPJPY H1)\n")
say("Registradas antes de ejecutarlas en [`../research/PRUEBAS_EXIGENTES.md`](../research/PRUEBAS_EXIGENTES.md). "
    "Resultados en pips. Holdout: desde el 10/07/2023.\n")
b = st(t0.pnl_pips)
say(f"Referencia: {b['trades']} trades, PF {b['PF']}, {b['net']:+} pips, maxDD {b['maxDD']}.\n")

say("## 1. Zona horaria del broker\n")
rows = []
for k in (-2, -1, 0, 1, 2):
    hh = h1.copy()
    hh.index = hh.index + pd.Timedelta(hours=k)
    t, _ = bt(hh, base)
    s, so = st(t.pnl_pips), st(t[t.exit_time >= HOLD].pnl_pips)
    rows.append({"desplazamiento": f"{k:+d} h (GMT{2 + k:+d}/{3 + k:+d})", "trades": s["trades"], "PF": s["PF"], "pips": s["net"],
                 "PF holdout": so["PF"]})
table(pd.DataFrame(rows))

say("\n## 2. Retraso de ejecucion y slippage\n")


def lagged(bars, cfg):
    s = M.signals(bars, cfg)
    for c in ("long_entry", "short_entry"):
        s[c] = s[c].shift(1, fill_value=False)
    return s


rows = []
for lab, cfg, fn in [("base (spread real)", base, M.signals),
                     ("spread fijo 2.0", replace(base, use_bar_spread=False, spread_pips=2.0), M.signals),
                     ("+1 pip por lado", replace(base, use_bar_spread=False, spread_pips=4.0), M.signals),
                     ("+3 pips por lado", replace(base, use_bar_spread=False, spread_pips=8.0), M.signals),
                     ("entrada 1 vela tarde", base, lagged),
                     ("1 vela tarde + 3 pips por lado", replace(base, use_bar_spread=False, spread_pips=8.0), lagged)]:
    t, _ = bt(h1, cfg, fn)
    s, so = st(t.pnl_pips), st(t[t.exit_time >= HOLD].pnl_pips)
    rows.append({"escenario": lab, "trades": s["trades"], "PF": s["PF"], "pips": s["net"], "PF holdout": so["PF"]})
table(pd.DataFrame(rows))

say("\n## 3. Crisis\n")
W = [("crisis financiera", "2008-09-01", "2009-03-31"), ("Fukushima / yen", "2011-03-01", "2011-04-30"),
     ("devaluacion China", "2015-08-01", "2015-09-30"), ("Brexit", "2016-06-01", "2016-07-31"),
     ("COVID", "2020-02-15", "2020-04-30"), ("2022 (tipos)", "2022-01-01", "2022-12-31"),
     ("deshacer carry yen", "2024-07-01", "2024-08-31")]
eq = e0.set_index("time")["equity"]
rows = []
for name, a, z in W:
    seg = t0[(t0.exit_time >= a) & (t0.exit_time <= z)]
    ee = eq[(eq.index >= a) & (eq.index <= z)]
    dd = (ee - ee.cummax()).min() / (base.fixed_lots * base.pip_value_per_lot) if len(ee) else 0
    rows.append({"ventana": name, "desde": a, "hasta": z, "trades cerrados": len(seg), "pips": round(seg.pnl_pips.sum()),
                 "peor caida dentro (pips, equity flotante)": round(dd)})
table(pd.DataFrame(rows))
say("\nReferencia: drawdown mediano del Monte Carlo = -3,589 pips; el 5% de peores casos, -5,644.")

say("\n## 4. Otra fuente de datos: GBPJPY sintetico (GBPUSD x USDJPY), 2007 a 2023\n")
gu = pd.read_csv(os.path.join(ROOT, "data", "GBPUSD_H1_2007_2023.csv"), parse_dates=["time"]).set_index("time")
uj = pd.read_csv(os.path.join(ROOT, "data", "USDJPY_H1.csv"), parse_dates=["time"]).set_index("time")
j = gu.join(uj, how="inner", lsuffix="_a", rsuffix="_b")
o, c = j.open_a * j.open_b, j.close_a * j.close_b
top, bot = np.maximum(o, c), np.minimum(o, c)
syn = pd.DataFrame({"open": o, "high": top + 0.5 * (j.high_a * j.high_b - top), "low": bot - 0.5 * (bot - j.low_a * j.low_b),
                    "close": c, "volume": j.volume_a})
ts, _ = bt(syn, replace(base, use_bar_spread=False, spread_pips=2.5))
tr = t0[(t0.exit_time >= syn.index[0]) & (t0.exit_time <= syn.index[-1])]
table(pd.DataFrame([{"datos": "Dukascopy GBPJPY (real)", **st(tr.pnl_pips)},
                    {"datos": "sintetico GBPUSD x USDJPY", **st(ts.pnl_pips)}]))

say("\n## 5. Tamano por volatilidad (Parte 3)\n")
ctx = E.daily_context(h1, h1.index, replace(base, atr_period_d1=20))
atr_e = ctx["atr"].reindex(pd.DatetimeIndex(t0.entry_time)).to_numpy(float) / base.pip
dev_mask = (t0.exit_time < HOLD).to_numpy()
med = np.nanmedian(E.daily_context(h1[h1.index < HOLD], h1.index[h1.index < HOLD], replace(base, atr_period_d1=20))["atr"]) / base.pip
w = np.clip(med / atr_e, 0.5, 2.0)
w = np.where(np.isnan(w), 1.0, w)
pf_ = t0.pnl_pips.to_numpy(float)
pv = pf_ * w
rows = []
for lab, x in [("lotes fijos", pf_), ("tamano por volatilidad", pv)]:
    for tramo, m in [("desarrollo", dev_mask), ("holdout", ~dev_mask)]:
        s = st(x[m])
        rows.append({"metodo": lab, "tramo": tramo, "PF": s["PF"], "neto (pips equivalentes)": s["net"], "maxDD": s["maxDD"],
                     "neto / |maxDD|": round(s["net"] / abs(s["maxDD"]), 2) if s["maxDD"] else np.nan})
vt = pd.DataFrame(rows)
table(vt)
r_dev_f, r_dev_v = vt.iloc[0]["neto / |maxDD|"], vt.iloc[2]["neto / |maxDD|"]
r_ho_f, r_ho_v = vt.iloc[1]["neto / |maxDD|"], vt.iloc[3]["neto / |maxDD|"]
adopt = (r_dev_v >= 1.10 * r_dev_f) and (r_ho_v >= r_ho_f)
say(f"\nATR(20) diario mediano en desarrollo: {med:.0f} pips; peso medio {w.mean():.2f}. Regla: mejorar >= 10% en "
    f"desarrollo ({r_dev_v} frente a {r_dev_f}) y no empeorar en holdout ({r_ho_v} frente a {r_ho_f}) -> "
    f"**{'SE ADOPTA' if adopt else 'NO SE ADOPTA'}**.")

open(os.path.join(ROOT, "reports", "exigentes_ema100.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
