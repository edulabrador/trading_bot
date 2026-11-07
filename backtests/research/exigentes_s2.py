"""Parte 1 (S2) y Parte 2 de PRUEBAS_EXIGENTES.md.

    python backtests/research/exigentes_s2.py            # pruebas + seleccion de mejora (solo desarrollo)
    python backtests/research/exigentes_s2.py --validate # validacion en los 5 indices nuevos (una vez)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import daily as D  # noqa: E402

# Indices nuevos (nunca mirados). Spread fijado antes de ver resultados, conservador.
NEW = {"FTSE100": ("GBRIDXGBP", 1.5), "ESTX50": ("EUSIDXEUR", 2.0), "N225": ("JPNIDXJPY", 10.0),
       "CAC40": ("FRAIDXEUR", 1.5), "ASX200": ("AUSIDXAUD", 2.0)}
VARIANTS = {"M0 original": {}, "M1 salida RSI>70": {"exit_mode": "rsi", "exit_rsi": 70.0},
            "M2 stop 3 ATR": {"emerg_stop_atr": 3.0}, "M3 filtro volatilidad p90": {"vol_filter_pct": 90.0},
            "M4 cierre a 10 dias": {"time_stop_days": 10}}
SEL_FILE = os.path.join(HERE, "logs", "s2_mejora_seleccion.json")
md = []


def say(s=""):
    print(s, flush=True)
    md.append(s)


def table(df):
    say("| " + " | ".join(map(str, df.columns)) + " |")
    say("|" + "---|" * len(df.columns))
    for _, r in df.iterrows():
        say("| " + " | ".join(str(v) for v in r.values) + " |")


def ratio(s):
    return round(s["R"] / abs(s["maxDD_R"]), 2) if s.get("maxDD_R") else np.nan


def run_on(data, p, spreads=None):
    out = []
    for n, d in data.items():
        tt = D.backtest(d[d.index >= "2005-06-01"], "S2", p, (spreads or D.SPREAD)[n])
        tt["sym"] = n
        out.append(tt[tt.entry_time >= D.START])
    return pd.concat(out, ignore_index=True)


def backtest_timing(d, p, spread, mode, slip_atr=0.0):
    """mode: 'close' (al cierre del dia de la senal), 'open' (apertura siguiente, base), 'nextclose' (un dia tarde)."""
    sig = D.signals(d, "S2", p)
    o, c = d["open"].to_numpy(), d["close"].to_numpy()
    L, XL, A = sig["long"].to_numpy(bool), sig["exit_long"].to_numpy(bool), sig["atr"].to_numpy(float)
    half, idx, tr, pos = spread / 2, d.index, [], 0
    for i in range(1, len(d) - 1):
        px_e = {"close": c[i - 1], "open": o[i], "nextclose": c[i]}[mode]
        if pos and XL[i - 1]:
            tr.append((et, idx[i], entry, px_e - half - slip_atr * risk, risk)); pos = 0
        if not pos and L[i - 1] and A[i - 1] > 0:
            pos, entry, risk, et = 1, px_e + half + slip_atr * A[i - 1], A[i - 1], idx[i]
    t = pd.DataFrame(tr, columns=["entry_time", "exit_time", "entry", "exit", "risk"])
    t["R"] = (t.exit - t.entry) / t.risk
    return t[t.entry_time >= D.START]


# tipos de referencia aproximados (media anual, de memoria; revisar con datos oficiales)
FED = {2007: 5.0, 2008: 1.9, 2009: 0.15, 2010: 0.15, 2011: 0.1, 2012: 0.15, 2013: 0.1, 2014: 0.1, 2015: 0.15, 2016: 0.4,
       2017: 1.0, 2018: 1.8, 2019: 2.2, 2020: 0.4, 2021: 0.1, 2022: 1.7, 2023: 5.0, 2024: 5.1, 2025: 4.3, 2026: 3.9}
ECB = {2007: 3.0, 2008: 3.2, 2009: 0.5, 2010: 0.25, 2011: 0.5, 2012: 0.1, 2013: 0.0, 2014: 0.0, 2015: -0.2, 2016: -0.35,
       2017: -0.4, 2018: -0.4, 2019: -0.45, 2020: -0.5, 2021: -0.5, 2022: 0.2, 2023: 3.3, 2024: 3.7, 2025: 2.3, 2026: 2.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    data = D.universe(D.INDICES)
    p0 = D.P()

    if a.validate:
        sel = json.load(open(SEL_FILE))
        # Enmienda en PRUEBAS_EXIGENTES.md: Dukascopy bloqueado -> indices Yahoo 2006-2018
        ydir = os.path.join(ROOT, "data", "indices_yahoo")
        spreads = {"N225": 10.0, "CAC40": 1.5, "ASX200": 2.0, "AEX": 0.15, "IBEX35": 5.0, "TSX": 5.0, "NZ50": 5.0}
        new = {k: pd.read_csv(os.path.join(ydir, f"{k}.csv"), parse_dates=["time"]).set_index("time") for k in spreads}
        say("# S2: validacion en indices nunca vistos\n")
        say("Indices: " + ", ".join(f"{k} ({v.index[0]:%Y-%m} a {v.index[-1]:%Y-%m})" for k, v in new.items()) + "\n")
        res = {}
        for name in ["M0 original"] + ([sel["chosen"]] if sel.get("chosen") else []):
            p = replace(p0, **VARIANTS[name])
            t = run_on(new, p, spreads)
            per = {n: D.st(g.R) for n, g in t.groupby("sym")}
            s = D.st(t.R)
            res[name] = {"agregado": s, "por_indice": per}
            say(f"**{name}**: agregado {s}")
            table(pd.DataFrame([{"indice": n, "trades": v["trades"], "PF": v["PF"], "R": v["R"], "t": v["t"]} for n, v in per.items()]))
            say("")
        m0 = res["M0 original"]
        share = np.mean([v["PF"] > 1 for v in m0["por_indice"].values()])
        gen = m0["agregado"]["PF"] >= 1.2 and share >= 0.6
        say(f"S2 original en indices nuevos: PF agregado {m0['agregado']['PF']}, {share:.0%} de indices con PF > 1 -> "
            f"**{'GENERALIZA' if gen else 'NO GENERALIZA'}**")
        if sel.get("chosen"):
            v = res[sel["chosen"]]
            ok = ratio(v["agregado"]) > ratio(m0["agregado"]) and v["agregado"]["PF"] > 1
            say(f"\nVariante {sel['chosen']}: R/|DD| {ratio(v['agregado'])} frente a {ratio(m0['agregado'])} del original -> "
                f"**{'SE ADOPTA' if ok else 'NO SE ADOPTA'}**")
        open(os.path.join(ROOT, "reports", "s2_validacion_indices_nuevos.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
        json.dump(res, open(os.path.join(HERE, "logs", "s2_validacion.json"), "w"), indent=2, default=str)
        return

    t0 = D.run_all(data, "S2", p0)
    say("# Pruebas exigentes: S2 (RSI(2) en indices)\n")
    say("Registradas antes de ejecutarlas en [`../research/PRUEBAS_EXIGENTES.md`](../research/PRUEBAS_EXIGENTES.md). "
        "Resultados en R. Holdout: desde el 10/07/2023.\n")

    say("## 1. Fuente de datos y corte del dia: S&P 500 Yahoo frente a Dukascopy (2011-09 a 2025-12)\n")
    y = data["SP500"]
    dk = D.load_duka_d1("USA500IDXUSD")
    rows = []
    for lab, d in [("Yahoo (cierre de bolsa)", y), ("Dukascopy USA500 (dias UTC, CFD)", dk)]:
        t = D.backtest(d, "S2", p0, D.SPREAD["SP500"])
        t = t[(t.entry_time >= "2012-07-01") & (t.exit_time <= "2025-12-31")]  # tras el calentamiento de la SMA200 en ambos
        s = D.st(t.R)
        rows.append({"datos": lab, "trades": s["trades"], "PF": s["PF"], "R": s["R"], "t": s["t"]})
    table(pd.DataFrame(rows))

    say("\n## 2. Momento de ejecucion y slippage\n")
    rows = []
    for lab, mode, slip in [("al cierre del dia de la senal", "close", 0), ("apertura siguiente (base)", "open", 0),
                            ("un dia tarde (cierre siguiente)", "nextclose", 0), ("apertura + 0.1 ATR por lado", "open", 0.1),
                            ("un dia tarde + 0.1 ATR por lado", "nextclose", 0.1)]:
        t = pd.concat([backtest_timing(d[d.index >= "2005-06-01"], p0, D.SPREAD[n], mode, slip) for n, d in data.items()])
        s, sh = D.st(t.R), D.st(t[t.exit_time >= D.HOLDOUT].R)
        rows.append({"escenario": lab, "trades": s["trades"], "PF": s["PF"], "R": s["R"], "PF holdout": sh["PF"]})
    table(pd.DataFrame(rows))

    say("\n## 3. Crisis\n")
    W = [("crisis financiera", "2008-09-01", "2009-03-31"), ("agosto 2011", "2011-07-15", "2011-10-15"),
         ("devaluacion China", "2015-08-01", "2015-09-30"), ("feb 2018 (volmageddon)", "2018-01-25", "2018-03-15"),
         ("oct-dic 2018", "2018-10-01", "2018-12-31"), ("COVID", "2020-02-15", "2020-04-30"), ("2022", "2022-01-01", "2022-12-31"),
         ("deshacer carry yen", "2024-07-15", "2024-08-31"), ("aranceles 2025", "2025-02-15", "2025-04-30")]
    rows = []
    for name, x, z in W:
        seg = t0[(t0.exit_time >= x) & (t0.exit_time <= z)]
        rows.append({"ventana": name, "trades": len(seg), "R": round(seg.R.sum(), 1), "peor trade (R)": round(seg.R.min(), 1) if len(seg) else ""})
    table(pd.DataFrame(rows))

    say("\n## 4. Walk-forward (rsi_lo x sma_exit, 5 anios de entrenamiento)\n")
    grid = [(lo, ex) for lo in (5, 10, 15) for ex in (3, 5, 10)]
    cache = {g: D.run_all(data, "S2", replace(p0, rsi_lo=g[0], sma_exit=g[1])) for g in grid}
    rows = []
    for ty in range(2013, 2026):
        A_, B_, C_ = pd.Timestamp(f"{ty - 5}-01-01"), pd.Timestamp(f"{ty}-01-01"), pd.Timestamp(f"{ty + 1}-01-01")
        sc = lambda tt: tt[(tt.exit_time >= A_) & (tt.exit_time < B_)].R.sum()
        best = max(grid, key=lambda g: sc(cache[g]))
        bt_ = cache[best]
        o = bt_[(bt_.exit_time >= B_) & (bt_.exit_time < C_)].R.sum()
        base_y = t0[(t0.exit_time >= B_) & (t0.exit_time < C_)].R.sum()
        rows.append({"anio": ty, "rsi_lo/sma_exit": f"{best[0]}/{best[1]}", "IS R/anio": round(sc(bt_) / 5, 1), "OOS R": round(o, 1),
                     "base R": round(base_y, 1)})
    wf = pd.DataFrame(rows)
    table(wf)
    say(f"\nTotal OOS {wf['OOS R'].sum():.1f} R (base {wf['base R'].sum():.1f}); anios positivos {(wf['OOS R'] > 0).sum()}/{len(wf)}; "
        f"eficiencia {wf['OOS R'].mean() / wf['IS R/anio'].mean():.2f}")

    say("\n## 5. Financiacion del CFD\n")
    tt = t0.copy()
    nights = (tt.exit_time - tt.entry_time).dt.days.clip(lower=0)
    yr = tt.entry_time.dt.year
    rate = np.where(tt.sym == "DAX", yr.map(ECB), yr.map(FED)) + 2.5
    cost_R = tt.entry * rate / 100 / 365 * nights / tt.risk
    tt["R_fin"] = tt.R - cost_R
    s, sf = D.st(tt.R), D.st(tt.R_fin)
    sh, shf = D.st(tt[tt.exit_time >= D.HOLDOUT].R), D.st(tt[tt.exit_time >= D.HOLDOUT].R_fin)
    table(pd.DataFrame([{"version": "sin financiacion", "PF": s["PF"], "R": s["R"], "PF holdout": sh["PF"]},
                        {"version": "con financiacion (tipo + 2.5%)", "PF": sf["PF"], "R": sf["R"], "PF holdout": shf["PF"]}]))
    say(f"\nCoste medio por trade: {cost_R.mean():.3f} R ({nights.mean():.1f} noches de media). Tipos aproximados de memoria.")

    say("\n## 6. Mas simulaciones\n")
    rng = np.random.default_rng(3)
    dev = t0[t0.exit_time < D.HOLDOUT]
    rexp = [D.run_all(data, "S2", p0, rand_seed=500 + k) for k in range(100)]
    rexp = np.array([x[x.exit_time < D.HOLDOUT].R.mean() for x in rexp])
    say(f"- 100 entradas aleatorias: S2 supera al {100 * (rexp < dev.R.mean()).mean():.0f}% (media aleatoria {rexp.mean():.3f} R/trade, S2 {dev.R.mean():.3f}).")
    pfs = []
    for _ in range(150):
        f = lambda v: v * rng.uniform(0.8, 1.2)
        p = replace(p0, rsi_lo=f(p0.rsi_lo), sma_trend=round(f(p0.sma_trend)), sma_exit=max(2, round(f(p0.sma_exit))), atr_n=round(f(p0.atr_n)))
        x = D.run_all(data, "S2", p)
        pfs.append((D.pf(x[x.exit_time < D.HOLDOUT].R), D.pf(x[x.exit_time >= D.HOLDOUT].R)))
    pfs = np.array(pfs)
    say(f"- 150 combinaciones (+-20% a la vez): PF > 1 en {(pfs[:, 0] > 1).sum()}/150 en desarrollo (mediana {np.median(pfs[:, 0]):.2f}, "
        f"minimo {pfs[:, 0].min():.2f}) y en {(pfs[:, 1] > 1).sum()}/150 en holdout (mediana {np.median(pfs[:, 1]):.2f}).")

    say("\n## 7. Mejoras (Parte 2): seleccion solo con desarrollo\n")
    rows, cand = [], []
    s0 = None
    for name, kw in VARIANTS.items():
        x = D.run_all(data, "S2", replace(p0, **kw))
        s = D.st(x[x.exit_time < D.HOLDOUT].R)
        if name == "M0 original":
            s0 = s
        rr = ratio(s)
        is_c = name != "M0 original" and rr >= 1.10 * ratio(s0) and s["PF"] >= 1.5
        if is_c:
            cand.append((s["t"], name))
        rows.append({"variante": name, "trades": s["trades"], "PF": s["PF"], "R": s["R"], "maxDD (R)": s["maxDD_R"], "R/|DD|": rr,
                     "t": s["t"], "candidata": "si" if is_c else "no"})
    table(pd.DataFrame(rows))
    chosen = max(cand)[1] if cand else None
    say(f"\nVariante elegida para validar en indices nuevos: **{chosen or 'ninguna (se mantiene S2 original)'}**")
    json.dump({"chosen": chosen}, open(SEL_FILE, "w"))
    open(os.path.join(ROOT, "reports", "exigentes_s2.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
