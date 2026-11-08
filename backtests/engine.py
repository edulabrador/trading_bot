"""
engine.py
=========

Motor de backtest generico para EAs estilo EA Studio / MT4 con la misma
interfaz que el backtester v5 (``bots/ea_gbpjpy_h1_ema100_v5.py``), para que
``run_tests.py`` pueda evaluarlos.

Un bot solo tiene que definir:
  - una ``Config`` (subclase de ``BaseConfig``) con sus parametros
  - ``signals(bars, cfg) -> DataFrame`` con columnas booleanas
      long_entry, short_entry, exit_long, exit_short
    evaluadas en la APERTURA de cada vela i usando solo velas cerradas
    (equivalente a shift 1, 2... en MQL)

y envolver ``backtest`` (ver ``bots/mq4_*.py``).

Modelo de ejecucion (igual que el v5 y que la plantilla MQ4 de EA Studio):
  - Precios BID. BUY abre a Ask = Bid + spread y cierra a Bid.
  - En la apertura de cada vela: cierre forzado de sesion, salida por senal
    (solo dentro de sesion) y, si no hay posicion, entrada (solo en sesion).
  - SL/TP fijos en pips desde el Bid (BUY) o el Ask (SELL) de la apertura.
  - SL/TP se comprueban dentro de la vela con las velas H1 que contiene
    (si el timeframe es H4) o con la propia vela H1. Si SL y TP caen en la
    misma vela, se asume SL. Gaps a traves de SL/TP se rellenan a la apertura.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Optional

import numpy as np
import pandas as pd


class Direction(IntEnum):
    FLAT = -1
    BUY = 0
    SELL = 1


@dataclass
class BaseConfig:
    name: str = "baseline"
    timeframe: str = "H1"            # "H1" o "H4" (H4 se construye desde el CSV H1)
    fixed_lots: float = 0.01
    stop_loss_pips: float = 0.0       # 0 = sin SL
    take_profit_pips: float = 0.0     # 0 = sin TP

    pip: float = 0.0001
    point: float = 0.00001
    spread_pips: float = 1.0          # si no hay spread por vela o use_bar_spread=False
    use_bar_spread: bool = True
    max_spread_pips: float = 0.0
    pip_value_per_lot: float = 10.0   # divisa de cuenta por pip y lote (aproximado)
    commission_per_lot_per_side: float = 0.0
    swap_long_per_lot_per_night: float = 0.0
    swap_short_per_lot_per_night: float = 0.0
    initial_capital: float = 10_000.0

    # Sesion (segundos desde medianoche, hora del servidor del CSV), como el MQ4
    session_sunday_open: int = 0
    session_sunday_close: int = 86400
    session_mon_thu_open: int = 0
    session_mon_thu_close: int = 86400
    session_fri_open: int = 0
    session_fri_close: int = 86400
    ignore_sunday: bool = False
    close_at_session_close: bool = False
    close_at_friday_close: bool = False

    gap_aware_sl: bool = True
    close_open_position_at_end: bool = True
    direction_mode: str = "both"      # "both", "buy_only", "sell_only"

    # Mejoras opcionales (0 / "" = desactivado, paridad con el EA original)
    sl_atr_mult: float = 0.0          # SL = mult x ATR diario (dia cerrado anterior) en vez de pips fijos
    tp_atr_mult: float = 0.0          # TP = mult x ATR diario
    atr_period_d1: int = 14
    d1_trend_sma: int = 0             # >0: solo largos si cierre D1 > SMA(n) D1, solo cortos si <
    use_signal_exit: bool = True      # False: ignora la salida por senal (solo SL/TP)
    use_trend_filter: bool = False    # compatibilidad con run_tests


SIGMA = 1e-6
TF_SECONDS = {"H1": 3600, "H4": 14400}

# Hook para el benchmark de entradas aleatorias de run_tests.py:
# fn(i, long_ok, short_ok) -> (long_ok, short_ok)
_entry_override: Optional[Callable] = None


def set_entry_override(fn: Optional[Callable]) -> None:
    global _entry_override
    _entry_override = fn


# ----------------------------------------------------------------------------- datos
def load_price_csv(path: str) -> pd.DataFrame:
    """CSV con cabecera time,open,high,low,close[,volume][,spread] (p.ej. de dukascopy.py)."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    tcol = next(c for c in ("time", "datetime", "date") if c in df.columns)
    df.index = pd.to_datetime(df[tcol], errors="coerce")
    df = df.drop(columns=[tcol])
    df = df[~df.index.isna()].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if "spread" in df.columns:
        df = df.rename(columns={"spread": "spread_points"})
    if "volume" not in df.columns:
        df["volume"] = 1.0
    keep = ["open", "high", "low", "close", "volume"] + (["spread_points"] if "spread_points" in df.columns else [])
    return df[keep].astype(float)


def resample(h1: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "H1":
        return h1
    rule = {"H4": "4h"}[timeframe]
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    if "spread_points" in h1.columns:
        agg["spread_points"] = "first"
    return h1.resample(rule, label="left", closed="left").agg(agg).dropna(subset=["open", "high", "low", "close"])


# ----------------------------------------------------------------------------- indicadores MT4
def lag(x, k: int) -> np.ndarray:
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if k < len(x):
        out[k:] = x[: len(x) - k]
    return out


def sma(x, n):
    return pd.Series(x).rolling(n).mean().values


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().values


def smma(x, n):
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = x[:n].mean()
    for i in range(n, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def wpr(h, l, c, n):
    hh = pd.Series(h).rolling(n).max().values
    ll = pd.Series(l).rolling(n).min().values
    with np.errstate(invalid="ignore", divide="ignore"):
        return -100 * (hh - c) / (hh - ll)


def stochastic_main(h, l, c, k, slowing):
    """iStochastic(...,MODE_SMA,STO_LOWHIGH,MODE_MAIN). %D no afecta a la linea principal."""
    hh = pd.Series(h).rolling(k).max().values
    ll = pd.Series(l).rolling(k).min().values
    num = pd.Series(c - ll).rolling(slowing).sum().values
    den = pd.Series(hh - ll).rolling(slowing).sum().values
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den == 0, 100.0, 100 * num / den)


def alligator_line(h, l, period, shift):
    """Linea del Alligator (SMMA de precio mediano) desplazada 'shift' velas hacia delante."""
    return lag(smma((np.asarray(h) + np.asarray(l)) / 2, period), shift) if shift else smma((np.asarray(h) + np.asarray(l)) / 2, period)


def rvi_main(o, h, l, c, n):
    def w(x):
        s = pd.Series(x)
        return ((s + 2 * s.shift(1) + 2 * s.shift(2) + s.shift(3)) / 6).values
    num = pd.Series(w(c - o)).rolling(n).sum().values
    den = pd.Series(w(h - l)).rolling(n).sum().values
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den


def adx_di(h, l, c, n):
    """+DI y -DI como el ADX.mq4 de MT4 (EMA de +DM/TR y -DM/TR)."""
    h, l, c = (np.asarray(v, float) for v in (h, l, c))
    ph, pl, pc = lag(h, 1), lag(l, 1), lag(c, 1)
    pdm = np.maximum(h - ph, 0)
    mdm = np.maximum(pl - l, 0)
    eq = pdm == mdm
    pdm2 = np.where(eq | (pdm < mdm), 0, pdm)
    mdm2 = np.where(eq | (mdm < pdm), 0, mdm)
    tr = np.fmax.reduce([np.abs(h - l), np.abs(h - pc), np.abs(l - pc)])
    with np.errstate(invalid="ignore", divide="ignore"):
        psdi = np.where(tr == 0, 0, 100 * pdm2 / tr)
        msdi = np.where(tr == 0, 0, 100 * mdm2 / tr)
    psdi[0] = msdi[0] = 0
    return ema(np.nan_to_num(psdi), n), ema(np.nan_to_num(msdi), n)


def accumulation_distribution(h, l, c, v):
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        clv = np.where(rng == 0, 0, ((c - l) - (h - c)) / rng)
    return np.cumsum(clv * v)


def envelopes(c, n, deviation_pct):
    m = sma(c, n)
    return m * (1 + deviation_pct / 100), m * (1 - deviation_pct / 100)


def bulls_power(h, c, n):
    return h - ema(c, n)


# ----------------------------------------------------------------------------- sesion
def _secs(ts: pd.Timestamp) -> int:
    return ts.hour * 3600 + ts.minute * 60 + ts.second


def is_out_of_session(ts: pd.Timestamp, cfg: BaseConfig) -> bool:
    wd = ts.weekday()  # lunes=0 ... domingo=6
    secs, period = _secs(ts), TF_SECONDS[cfg.timeframe]
    if wd == 6:
        if cfg.ignore_sunday:
            return True
        fix = period if cfg.close_at_session_close else 0
        return secs < cfg.session_sunday_open or secs + fix > cfg.session_sunday_close
    if wd < 4:
        fix = period if cfg.close_at_session_close else 0
        return secs < cfg.session_mon_thu_open or secs + fix > cfg.session_mon_thu_close
    if wd == 4:
        fix = period if (cfg.close_at_friday_close or cfg.close_at_session_close) else 0
        return secs < cfg.session_fri_open or secs + fix > cfg.session_fri_close
    return True


def is_force_session_close(ts: pd.Timestamp, cfg: BaseConfig) -> bool:
    if not (cfg.close_at_friday_close or cfg.close_at_session_close):
        return False
    wd, secs, period = ts.weekday(), _secs(ts), TF_SECONDS[cfg.timeframe]
    if wd == 6 and cfg.close_at_session_close:
        return secs + period > cfg.session_sunday_close
    if wd < 4 and cfg.close_at_session_close:
        return secs + period > cfg.session_mon_thu_close
    if wd == 4:
        return secs + period > cfg.session_fri_close
    return False


def count_swap_nights(entry_time, exit_time) -> int:
    if entry_time is None or exit_time is None:
        return 0
    entry_time, exit_time = pd.Timestamp(entry_time), pd.Timestamp(exit_time)
    nights, day, end = 0, entry_time.normalize() + pd.Timedelta(days=1), exit_time.normalize()
    while day <= end:
        wd = day.weekday()
        if wd < 5:
            nights += 3 if wd == 2 else 1
        day += pd.Timedelta(days=1)
    return nights


# ----------------------------------------------------------------------------- contexto diario
def daily_context(h1: pd.DataFrame, index: pd.DatetimeIndex, cfg: BaseConfig) -> pd.DataFrame:
    """ATR(n) diario estilo MT4 (media simple del true range) y tendencia D1 vs SMA,
    ambos del ultimo dia CERRADO antes de cada vela (sin mirar el futuro)."""
    d = h1.resample("D").agg({"high": "max", "low": "min", "close": "last"}).dropna()
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(), (d["low"] - pc).abs()], axis=1).max(axis=1)
    out = pd.DataFrame({"atr": tr.rolling(cfg.atr_period_d1).mean()}, index=d.index)
    if cfg.d1_trend_sma > 0:
        sm = d["close"].rolling(cfg.d1_trend_sma).mean()
        out["trend_up"] = np.where(sm.isna(), np.nan, (d["close"] > sm).astype(float))
    else:
        out["trend_up"] = np.nan
    out = out.shift(1)  # valor disponible al dia siguiente
    day = index.normalize()
    return out.reindex(out.index.union(day)).ffill().reindex(day).set_axis(index)


# ----------------------------------------------------------------------------- backtest
def backtest(h1: pd.DataFrame, cfg: BaseConfig, signals_fn: Callable,
             warmup: int = 50) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    bars = resample(h1, cfg.timeframe)
    sig = signals_fn(bars, cfg)
    le, se = sig["long_entry"].to_numpy(bool), sig["short_entry"].to_numpy(bool)
    xl, xs = sig["exit_long"].to_numpy(bool), sig["exit_short"].to_numpy(bool)
    if not cfg.use_signal_exit:
        xl, xs = np.zeros_like(xl), np.zeros_like(xs)
    # filtros (no son el disparador): se aplican tambien a las entradas aleatorias del benchmark
    fl = sig["long_filter"].to_numpy(bool) if "long_filter" in sig else np.ones(len(sig), bool)
    fs = sig["short_filter"].to_numpy(bool) if "short_filter" in sig else np.ones(len(sig), bool)
    d1 = daily_context(h1, bars.index, cfg)
    if cfg.d1_trend_sma > 0:
        up = d1["trend_up"].to_numpy(float)
        fl = fl & (up == 1.0)
        fs = fs & (up == 0.0)
    le, se = le & fl, se & fs
    atr_d1 = d1["atr"].to_numpy(float)
    if cfg.direction_mode == "buy_only":
        se = np.zeros_like(se)
    elif cfg.direction_mode == "sell_only":
        le = np.zeros_like(le)

    idx = bars.index
    op, cl = bars["open"].to_numpy(float), bars["close"].to_numpy(float)
    if cfg.use_bar_spread and "spread_points" in bars.columns:
        spr = bars["spread_points"].to_numpy(float) * cfg.point / cfg.pip
    else:
        spr = np.full(len(bars), cfg.spread_pips)

    # velas intrabar (H1) para SL/TP
    l_idx, l_op, l_hi, l_lo = h1.index, h1["open"].to_numpy(float), h1["high"].to_numpy(float), h1["low"].to_numpy(float)
    period = pd.Timedelta(seconds=TF_SECONDS[cfg.timeframe])
    l_start = l_idx.searchsorted(idx, side="left")
    l_end = l_idx.searchsorted(idx + period, side="left")

    pip = cfg.pip
    trades, equity_rows = [], []
    capital = cfg.initial_capital
    pos = None  # dict

    def close(ts, price, reason):
        nonlocal pos, capital
        d = pos["dir"]
        pips = (price - pos["entry"]) / pip if d == Direction.BUY else (pos["entry"] - price) / pip
        gross = pips * cfg.fixed_lots * cfg.pip_value_per_lot
        comm = 2 * cfg.commission_per_lot_per_side * cfg.fixed_lots
        rate = cfg.swap_long_per_lot_per_night if d == Direction.BUY else cfg.swap_short_per_lot_per_night
        swap = count_swap_nights(pos["time"], ts) * rate * cfg.fixed_lots
        capital += gross - comm + swap
        trades.append({"entry_time": pos["time"], "exit_time": ts, "direction": d.name,
                       "entry_price": round(pos["entry"], 5), "exit_price": round(float(price), 5),
                       "stop_loss": round(pos["sl"], 5), "take_profit": round(pos["tp"], 5),
                       "lots": cfg.fixed_lots, "spread_at_entry_pips": round(pos["spread"], 2),
                       "pnl_pips": round(float(pips), 3), "mae_pips": round(pos["mae"], 1), "mfe_pips": round(pos["mfe"], 1),
                       "gross_cash": round(gross, 2), "commission_cash": round(comm, 2), "swap_cash": round(swap, 2),
                       "pnl_cash": round(gross - comm + swap, 2),
                       "hold_hours": round((pd.Timestamp(ts) - pd.Timestamp(pos["time"])).total_seconds() / 3600, 1),
                       "exit_reason": reason, "capital_after": round(capital, 2)})
        pos = None

    for i in range(warmup, len(idx)):
        ts, bid_open = idx[i], op[i]
        sp_bar = spr[i] if not np.isnan(spr[i]) else cfg.spread_pips
        ask_open = bid_open + sp_bar * pip
        inside = not is_out_of_session(ts, cfg)

        if pos is not None and is_force_session_close(ts, cfg):
            close(ts, bid_open if pos["dir"] == Direction.BUY else ask_open, "SESSION")
        if inside and pos is not None:
            if (pos["dir"] == Direction.BUY and xl[i]) or (pos["dir"] == Direction.SELL and xs[i]):
                close(ts, bid_open if pos["dir"] == Direction.BUY else ask_open, "SIGNAL")
        if inside and pos is None and not (cfg.max_spread_pips > 0 and sp_bar > cfg.max_spread_pips):
            lo_ok, so_ok = bool(le[i]), bool(se[i])
            if _entry_override is not None:
                lo_ok, so_ok = _entry_override(i, lo_ok, so_ok)
                lo_ok, so_ok = lo_ok and bool(fl[i]), so_ok and bool(fs[i])
                if cfg.direction_mode == "buy_only":
                    so_ok = False
                elif cfg.direction_mode == "sell_only":
                    lo_ok = False
            if lo_ok != so_ok:  # el MQ4 no abre si ambas senales coinciden
                d = Direction.BUY if lo_ok else Direction.SELL
                sl_d, tp_d = cfg.stop_loss_pips * pip, cfg.take_profit_pips * pip
                if cfg.sl_atr_mult > 0 and not np.isnan(atr_d1[i]):
                    sl_d = cfg.sl_atr_mult * atr_d1[i]
                if cfg.tp_atr_mult > 0 and not np.isnan(atr_d1[i]):
                    tp_d = cfg.tp_atr_mult * atr_d1[i]
                has_sl = cfg.stop_loss_pips > 0 or cfg.sl_atr_mult > 0
                has_tp = cfg.take_profit_pips > 0 or cfg.tp_atr_mult > 0
                if d == Direction.BUY:
                    entry = ask_open
                    sl = bid_open - sl_d if has_sl else -np.inf
                    tp = bid_open + tp_d if has_tp else np.inf
                else:
                    entry = bid_open
                    sl = ask_open + sl_d if has_sl else np.inf
                    tp = ask_open - tp_d if has_tp else -np.inf
                pos = {"dir": d, "time": ts, "entry": entry, "sl": sl, "tp": tp, "spread": sp_bar, "mae": 0.0, "mfe": 0.0}

        if pos is not None:
            sp = pos["spread"] * pip
            a, b = int(l_start[i]), int(l_end[i])
            sub = range(a, b) if b > a else []
            for j in sub:
                bo, bh, bl, bts = l_op[j], l_hi[j], l_lo[j], l_idx[j]
                if pos["dir"] == Direction.BUY:
                    if cfg.gap_aware_sl and bo <= pos["sl"]:
                        close(bts, bo, "SL_gap"); break
                    if bl <= pos["sl"]:
                        close(bts, pos["sl"], "SL"); break
                    if bo >= pos["tp"]:
                        close(bts, bo, "TP_gap"); break
                    if bh >= pos["tp"]:
                        close(bts, pos["tp"], "TP"); break
                    pos["mae"] = min(pos["mae"], (bl - pos["entry"]) / pip)
                    pos["mfe"] = max(pos["mfe"], (bh - pos["entry"]) / pip)
                else:
                    ao_, ah, al = bo + sp, bh + sp, bl + sp
                    if cfg.gap_aware_sl and ao_ >= pos["sl"]:
                        close(bts, ao_, "SL_gap"); break
                    if ah >= pos["sl"]:
                        close(bts, pos["sl"], "SL"); break
                    if ao_ <= pos["tp"]:
                        close(bts, ao_, "TP_gap"); break
                    if al <= pos["tp"]:
                        close(bts, pos["tp"], "TP"); break
                    pos["mae"] = min(pos["mae"], (pos["entry"] - ah) / pip)
                    pos["mfe"] = max(pos["mfe"], (pos["entry"] - al) / pip)

        if pos is not None:
            fp = (cl[i] - pos["entry"]) / pip if pos["dir"] == Direction.BUY else (pos["entry"] - cl[i] - sp_bar * pip) / pip
            floating = fp * cfg.fixed_lots * cfg.pip_value_per_lot
        else:
            floating = 0.0
        equity_rows.append({"time": ts, "equity": capital + floating, "capital_closed": capital,
                            "open_position": pos["dir"].name if pos else "FLAT"})

    if pos is not None and cfg.close_open_position_at_end:
        last = cl[-1] if pos["dir"] == Direction.BUY else cl[-1] + spr[-1] * pip
        close(idx[-1], last, "END")

    t, e = pd.DataFrame(trades), pd.DataFrame(equity_rows)
    return t, e, compute_metrics(t, cfg, idx[warmup], idx[-1], e)


def compute_metrics(t: pd.DataFrame, cfg: BaseConfig, start, end, equity=None) -> dict:
    m = {"name": cfg.name, "timeframe": cfg.timeframe, "sl_pips": cfg.stop_loss_pips, "tp_pips": cfg.take_profit_pips,
         "start": str(start), "end": str(end), "trades": 0}
    if t.empty:
        return m
    p, cash = t["pnl_pips"].astype(float), t["pnl_cash"].astype(float)
    w, lo = p[p > 0], p[p < 0]
    gl = -lo.sum()
    eq = p.cumsum()
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 1e-9)
    final = cfg.initial_capital + cash.sum()
    run = mx = 0
    for x in p:
        run = run + 1 if x < 0 else 0
        mx = max(mx, run)
    m.update({"trades": len(t), "trades_per_year": round(len(t) / years, 1),
              "win_rate_%": round(100 * len(w) / len(t), 2),
              "profit_factor": round(w.sum() / gl, 3) if gl > 0 else math.inf,
              "expectancy_pips": round(p.mean(), 2), "avg_win_pips": round(w.mean(), 1) if len(w) else 0.0,
              "avg_loss_pips": round(lo.mean(), 1) if len(lo) else 0.0, "total_pips": round(p.sum(), 1),
              "max_dd_closed_pips": round((eq - eq.cummax()).min(), 1), "max_consec_losses": mx,
              "avg_hold_hours": round(t["hold_hours"].mean(), 1), "final_capital": round(final, 2),
              "cagr_%": round(100 * ((final / cfg.initial_capital) ** (1 / years) - 1), 2) if final > 0 else np.nan,
              "exit_mix": json.dumps(t["exit_reason"].value_counts().to_dict())})
    if equity is not None and not equity.empty:
        ev = equity["equity"].astype(float)
        dd = (ev - ev.cummax()).min()
        m["max_dd_float_cash"] = round(dd, 2)
        m["max_dd_float_pips"] = round(dd / (cfg.fixed_lots * cfg.pip_value_per_lot), 1)
        m["exposure_%"] = round(100 * (equity["open_position"] != "FLAT").mean(), 1)
    return m
