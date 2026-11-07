"""
daily.py
========

Backtest diario de las estrategias registradas en research/NUEVAS_ESTRATEGIAS.md
(S1 tendencia Turtle 55/20, S2 RSI(2) en indices, S3 RSI(2) en divisas) con las
reglas de aceptacion de ese documento.

Uso:
    python backtests/research/daily.py --strategy S1            # solo desarrollo
    python backtests/research/daily.py --strategy S1 --reveal   # + holdout (una vez)
"""
from __future__ import annotations

import argparse
import glob
import json
import lzma
import os
from dataclasses import dataclass, replace

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDOUT = pd.Timestamp("2023-07-10")
HALF = pd.Timestamp("2015-01-01")
START = pd.Timestamp("2007-01-01")
TOH = "/home/user/data_src/tohaitrieu_market-history/data"
DUKA_D1 = "/home/user/duka/d1"
# S&P 500 cash diario (Yahoo, via GitHub): Dukascopy solo lo tiene desde 2011 (ver NUEVAS_ESTRATEGIAS.md)
SP500_YAHOO = os.path.join(os.path.dirname(HERE), "data", "SP500_D1_yahoo.csv")

# spread completo por operacion, en unidades de precio (NUEVAS_ESTRATEGIAS.md)
SPREAD = {"EURUSD": 0.00010, "GBPUSD": 0.00015, "AUDUSD": 0.00012, "USDCAD": 0.00018, "USDCHF": 0.00018,
          "XAUUSD": 0.35, "SP500": 0.6, "NAS100": 2.0, "DAX": 2.0, "BRENT": 0.05}
FX = ["EURUSD", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF"]
INDICES = ["SP500", "NAS100", "DAX"]
DUKA_SYMS = {"SP500": "USA500IDXUSD", "NAS100": "USATECHIDXUSD", "DAX": "DEUIDXEUR", "XAUUSD": "XAUUSD", "BRENT": "BRENTCMDUSD"}

RULES = {"trades_min": 100, "PF_min": 1.10, "PF_half_min": 1.00, "share_min": 0.6, "robust_min": 0.8, "rand_min": 0.8}


# ----------------------------------------------------------------------------- datos
def load_toh(sym: str) -> pd.DataFrame:
    p = f"{TOH}/forex/{sym}/{sym}-D1.csv" if sym != "GOLD" else f"{TOH}/commodities/GOLD/GOLD-D1.csv"
    d = pd.read_csv(p, parse_dates=["Time"])
    d = d.rename(columns=str.lower).set_index("time")[["open", "high", "low", "close"]]
    d.index = d.index.normalize()
    d = d[~d.index.duplicated(keep="last")].sort_index()
    return d[d.index >= "2005-06-01"]


def load_duka_d1(sym: str, scale: float | None = None) -> pd.DataFrame | None:
    files = sorted(glob.glob(f"{DUKA_D1}/{sym}_*_BID_candles_day_1.bi5"))
    rows = []
    for f in files:
        if os.path.getsize(f) == 0:
            continue
        y = int(os.path.basename(f).split("_")[1])
        raw = lzma.decompress(open(f, "rb").read())
        a = np.frombuffer(raw, dtype=">i4").reshape(-1, 6)
        v = np.frombuffer(raw, dtype=">f4").reshape(-1, 6)[:, 5]
        idx = pd.Timestamp(year=y, month=1, day=1) + pd.to_timedelta(a[:, 0], unit="s")
        rows.append(pd.DataFrame({"open": a[:, 1], "high": a[:, 4], "low": a[:, 3], "close": a[:, 2], "vol": v}, index=idx))
    if not rows:
        return None
    d = pd.concat(rows).sort_index()
    d = d[d["vol"] > 0][["open", "high", "low", "close"]].astype(float)
    if scale is None:  # escala del entero: indices/oro/brent cotizan con 3 decimales en el datafeed
        scale = 1000.0
    d = d / scale
    d.index = d.index.normalize()
    return d[~d.index.duplicated()]


def universe(names):
    out = {}
    for n in names:
        if n in FX:
            out[n] = load_toh(n)
        elif n == "SP500" and os.path.exists(SP500_YAHOO):
            d = pd.read_csv(SP500_YAHOO, parse_dates=["time"]).set_index("time")[["open", "high", "low", "close"]]
            out[n] = d
        elif n in DUKA_SYMS:
            d = load_duka_d1(DUKA_SYMS[n])
            if d is None and n == "XAUUSD":
                d = load_toh("GOLD")
            if d is not None and len(d) > 1000:
                out[n] = d
    return out


# ----------------------------------------------------------------------------- indicadores
def atr(d, n=20):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(), (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def rsi_wilder(c, n=2):
    delta = c.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


# ----------------------------------------------------------------------------- estrategias
@dataclass
class P:
    entry_n: int = 55
    exit_n: int = 20
    stop_atr: float = 2.0
    atr_n: int = 20
    rsi_n: int = 2
    rsi_lo: float = 10.0
    rsi_hi: float = 90.0
    sma_trend: int = 200
    sma_exit: int = 5
    # variantes de mejora de S2 (PRUEBAS_EXIGENTES.md); por defecto = S2 original
    exit_mode: str = "sma"       # "sma" (cierre > SMA5) o "rsi" (RSI(2) > exit_rsi)
    exit_rsi: float = 70.0
    emerg_stop_atr: float = 0.0  # >0: stop de emergencia a N x ATR
    vol_filter_pct: float = 0.0  # >0: no entrar si ATR/precio > percentil (p.ej. 90) de 252 dias
    time_stop_days: int = 0      # >0: cerrar tras N dias de trading


def signals(d: pd.DataFrame, strat: str, p: P) -> pd.DataFrame:
    """Senales calculadas al CIERRE del dia i (se ejecutan en la apertura de i+1)."""
    c, h, l = d["close"], d["high"], d["low"]
    s = pd.DataFrame(index=d.index)
    if strat == "S1":
        hh = h.rolling(p.entry_n).max().shift(1)
        ll = l.rolling(p.entry_n).min().shift(1)
        xh = h.rolling(p.exit_n).max().shift(1)
        xl = l.rolling(p.exit_n).min().shift(1)
        s["long"], s["short"] = c > hh, c < ll
        s["exit_long"], s["exit_short"] = c < xl, c > xh
    else:
        r = rsi_wilder(c, p.rsi_n)
        trend = c.rolling(p.sma_trend).mean()
        ex = c.rolling(p.sma_exit).mean()
        s["long"] = (c > trend) & (r < p.rsi_lo)
        s["short"] = ((c < trend) & (r > p.rsi_hi)) if strat == "S3" else False
        if p.vol_filter_pct > 0:
            nv = atr(d, p.atr_n) / c
            lim = nv.rolling(252, min_periods=120).quantile(p.vol_filter_pct / 100)
            s["long"] = s["long"] & ~(nv > lim)
        if p.exit_mode == "rsi":
            s["exit_long"], s["exit_short"] = r > p.exit_rsi, r < 100 - p.exit_rsi
        else:
            s["exit_long"], s["exit_short"] = c > ex, c < ex
    s["atr"] = atr(d, p.atr_n)
    return s.fillna(False)


def backtest(d, strat, p, spread, rand=None):
    """rand: (prob, rng) -> entradas aleatorias con la misma frecuencia y las mismas salidas."""
    sig = signals(d, strat, p)
    o, h, l = d["open"].to_numpy(), d["high"].to_numpy(), d["low"].to_numpy()
    L, S = sig["long"].to_numpy(bool), sig["short"].to_numpy(bool)
    XL, XS, A = sig["exit_long"].to_numpy(bool), sig["exit_short"].to_numpy(bool), sig["atr"].to_numpy(float)
    if rand is not None:
        prob, rng = rand
        hit = rng.random(len(d)) < prob
        if strat == "S2":
            L, S = hit, np.zeros(len(d), bool)
        else:
            up = rng.random(len(d)) < 0.5
            L, S = hit & up, hit & ~up
    use_stop = strat == "S1" or p.emerg_stop_atr > 0
    stop_mult = p.stop_atr if strat == "S1" else p.emerg_stop_atr
    ei = 0
    idx = d.index
    trades = []
    pos = 0
    entry = stop = risk = 0.0
    et = None
    half = spread / 2
    for i in range(1, len(d)):
        # 1) ordenes decididas al cierre de i-1, ejecutadas en la apertura de i
        if pos == 1 and XL[i - 1]:
            trades.append((et, idx[i], 1, entry, o[i] - half, risk)); pos = 0
        elif pos == -1 and XS[i - 1]:
            trades.append((et, idx[i], -1, entry, o[i] + half, risk)); pos = 0
        if pos == 0 and not np.isnan(A[i - 1]) and A[i - 1] > 0 and (L[i - 1] != S[i - 1]):
            pos = 1 if L[i - 1] else -1
            entry = o[i] + half * pos
            risk = A[i - 1]
            stop = entry - pos * stop_mult * risk
            et = idx[i]
            ei = i
        # 1b) cierre por tiempo (en la apertura tras N dias)
        if pos != 0 and p.time_stop_days > 0 and i - ei >= p.time_stop_days:
            px = o[i] - half if pos == 1 else o[i] + half
            trades.append((et, idx[i], pos, entry, px, risk)); pos = 0
        # 2) stop dentro del dia
        if use_stop and pos != 0:
            if pos == 1 and (o[i] <= stop or l[i] <= stop):
                px = min(o[i], stop) - half
                trades.append((et, idx[i], 1, entry, px, risk)); pos = 0
            elif pos == -1 and (o[i] >= stop or h[i] >= stop):
                px = max(o[i], stop) + half
                trades.append((et, idx[i], -1, entry, px, risk)); pos = 0
    t = pd.DataFrame(trades, columns=["entry_time", "exit_time", "dir", "entry", "exit", "risk"])
    if len(t):
        t["R"] = t["dir"] * (t["exit"] - t["entry"]) / t["risk"]
    else:
        t["R"] = []
    return t


# ----------------------------------------------------------------------------- metricas
def pf(x):
    x = np.asarray(x, float)
    gl = -x[x < 0].sum()
    return float(x[x > 0].sum() / gl) if gl > 0 else (np.inf if len(x) else np.nan)


def st(x):
    x = np.asarray(x, float)
    if len(x) < 3:
        return {"trades": len(x), "PF": np.nan, "R": round(x.sum(), 1) if len(x) else 0, "t": np.nan}
    eq = np.cumsum(x)
    return {"trades": len(x), "PF": round(pf(x), 3), "R": round(x.sum(), 1), "expR": round(x.mean(), 3),
            "t": round(x.mean() / x.std(ddof=1) * np.sqrt(len(x)), 2),
            "maxDD_R": round(float((eq - np.maximum.accumulate(np.maximum(eq, 0))).min()), 1)}


def run_all(data, strat, p, rand_seed=None):
    out = []
    for n, d in data.items():
        d = d[d.index >= "2005-06-01"]
        rand = None
        if rand_seed is not None:
            base = backtest(d, strat, p, SPREAD[n])
            nb = len(base[base.entry_time < HOLDOUT])
            days = int((d.index < HOLDOUT).sum())
            rand = (max(nb, 1) / max(days, 1), np.random.default_rng(rand_seed + hash(n) % 1000))
        t = backtest(d, strat, p, SPREAD[n], rand)
        t["sym"] = n
        out.append(t)
    t = pd.concat(out, ignore_index=True)
    return t[t.entry_time >= START]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True, choices=["S1", "S2", "S3"])
    ap.add_argument("--reveal", action="store_true")
    ap.add_argument("--n-robust", type=int, default=30)
    ap.add_argument("--n-random", type=int, default=20)
    ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    names = {"S1": FX + ["XAUUSD", "SP500", "NAS100", "DAX", "BRENT"], "S2": INDICES, "S3": FX}[a.strategy]
    data = universe(names)
    print("instrumentos:", {k: f"{v.index[0]:%Y-%m}..{v.index[-1]:%Y-%m}" for k, v in data.items()})
    p0 = P()
    rng = np.random.default_rng(a.seed)

    t = run_all(data, a.strategy, p0)
    dev = t[t.exit_time < HOLDOUT]
    sd = st(dev.R)
    sa, sb = st(dev[dev.exit_time < HALF].R), st(dev[dev.exit_time >= HALF].R)
    per = {n: st(g.R) for n, g in dev.groupby("sym")}
    share = np.mean([v["PF"] > 1 for v in per.values()])

    def perturb():
        f = lambda v: v * rng.uniform(0.8, 1.2)
        return replace(p0, entry_n=max(2, round(f(p0.entry_n))), exit_n=max(2, round(f(p0.exit_n))), stop_atr=f(p0.stop_atr),
                       atr_n=max(2, round(f(p0.atr_n))), rsi_n=max(2, round(f(p0.rsi_n))), rsi_lo=f(p0.rsi_lo),
                       rsi_hi=100 - f(100 - p0.rsi_hi), sma_trend=max(5, round(f(p0.sma_trend))), sma_exit=max(2, round(f(p0.sma_exit))))
    rob = []
    for _ in range(a.n_robust):
        tt = run_all(data, a.strategy, perturb())
        rob.append(pf(tt[tt.exit_time < HOLDOUT].R))
    rob_ok = float(np.mean(np.array(rob) > 1))
    rexp = []
    for k in range(a.n_random):
        tt = run_all(data, a.strategy, p0, rand_seed=100 + k)
        rexp.append(tt[tt.exit_time < HOLDOUT].R.mean())
    rand_pct = float(np.mean(np.array(rexp) < dev.R.mean()))

    checks = {"trades>=100": sd["trades"] >= RULES["trades_min"], "PF>=1.10": sd["PF"] >= RULES["PF_min"],
              "mitad A>=1": sa["PF"] >= 1, "mitad B>=1": sb["PF"] >= 1, "60% instrumentos": share >= RULES["share_min"],
              "robustez>=80%": rob_ok >= RULES["robust_min"], "azar>=80%": rand_pct >= RULES["rand_min"]}
    passed = all(checks.values())
    print(f"\n=== {a.strategy} DESARROLLO (hasta 2023-07-09) ===")
    print("agregado:", sd)
    print("mitad A 2007-2014:", sa, "| mitad B 2015-2023:", sb)
    print("por instrumento:", {k: (v["trades"], v["PF"]) for k, v in per.items()})
    print(f"robustez: {rob_ok:.0%} con PF>1 | azar: supera al {rand_pct:.0%}")
    print("reglas:", checks, "->", "PASA" if passed else "NO PASA")

    res = {"strategy": a.strategy, "dev": sd, "A": sa, "B": sb, "per_instrument": per, "robust": rob_ok,
           "rand_pct": rand_pct, "checks": {k: bool(v) for k, v in checks.items()}, "passed": bool(passed),
           "instruments": list(data)}
    if a.reveal:
        if not passed:
            print("\nNo pasa las reglas: el holdout NO se revela.")
        else:
            ho = t[t.exit_time >= HOLDOUT]
            res["holdout"] = st(ho.R)
            res["holdout_per_instrument"] = {n: st(g.R) for n, g in ho.groupby("sym")}
            print("\n=== HOLDOUT (desde 2023-07-10) ===")
            print("agregado:", res["holdout"])
            print("por instrumento:", {k: (v["trades"], v["PF"]) for k, v in res["holdout_per_instrument"].items()})
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    with open(os.path.join(HERE, "logs", f"nueva_{a.strategy}{'_reveal' if a.reveal else ''}.json"), "w") as fh:
        json.dump(res, fh, indent=2, default=lambda x: None if isinstance(x, float) and np.isnan(x) else str(x))
    t.to_csv(os.path.join(HERE, "logs", f"trades_{a.strategy}.csv"), index=False) if a.reveal and passed else None


if __name__ == "__main__":
    main()
