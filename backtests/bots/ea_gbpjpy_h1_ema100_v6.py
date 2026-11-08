"""
EA_GBPJPY_H1_EMA100_BUY_ONLY_v6.py
==================================

Backtester v6 para la variante EMA100 BUY ONLY (EA Studio GBPJPY H1 #00043898).

Cambio v6 respecto a v5:
  - Salida por Awesome Oscillator DESACTIVADA por defecto (use_ao_exit=False).
    Con ao_level=3.47 el AO de GBPJPY H1 solo supera ese nivel en el 0.09% de
    las velas (p99 = 1.86) y en 2006-2026 no cerro ni un solo trade: todas las
    salidas son SL/TP. Quitarla no cambia ningun resultado (530 trades, PF 1.161)
    y deja el codigo alineado con lo que el bot hace de verdad.
    Para recuperar el comportamiento v5: use_ao_exit=True.
  - En el MQ4 equivalente: eliminar la condicion de salida de ManageClose()
    (o dejar solo SL/TP).

--- Notas heredadas de v5 ---

Cambios v5 respecto a v4:
  FIXES DE FIABILIDAD
  1. Equity flotante: la curva de equity incluye el P&L no realizado barra a
     barra. max_dd_float_cash refleja el drawdown real, no solo el realizado.
  2. Fills con gap en SL: si una barra ABRE por debajo del SL (gap de fin de
     semana o de noticia), el fill es al open de esa barra, no al precio del SL.
     Los TP con gap a favor se rellenan al open (mejor precio), como haria el broker.
  3. MAE/MFE por trade (maximo dolor / maximo favor en pips).
  4. Paridad exacta con el MQ4:
       - Filtro EMA bloquea con Close[1] <= EMA[1] (antes era <).
       - Close_At_Session_Close y Close_At_Friday_Close implementados.
       - Max_Spread filter implementado.
  5. Spread real por barra: si el CSV trae columna de spread (points), se usa
     el spread de la barra de entrada en lugar de un spread fijo.

  GESTION DE POSICION OPCIONAL (para experimentos de mejora)
  6. Breakeven: mueve el SL a entrada+offset tras X pips de beneficio.
  7. Trailing stop por ATR(H1): SL = max(SL, high - mult * ATR[i-1]).
  8. Time stop: cierre forzado tras N horas en mercado.
  Todas desactivadas por defecto (paridad con el EA original).

  DATOS
  9. Carga el formato TSV exportado de MT5 (Time/OHLC/Volume + col. spread),
     ademas de CSV con cabecera y MT4 sin cabecera.
 10. Intrabar generalizado: sirve cualquier timeframe inferior (M1, M5, M15).

Notas de honestidad del modelo:
  - El historico es Bid. BUY abre a Ask (= Bid + spread barra) y cierra a Bid.
  - El spread por barra del CSV es el registrado por MT5 en esa barra; el
    spread del tick exacto de entrada puede diferir.
  - Los SL dentro de barra LTF se rellenan al precio exacto; solo los gaps
    ENTRE barras se rellenan al open. Con M15 el error residual es pequeno,
    con H1 (pre-2022) es mayor.
  - pip_value_per_lot fijo es una aproximacion: el valor real del pip de
    GBPJPY en divisa de cuenta varia con USDJPY. Las metricas en PIPS son
    las fiables; las de cash son orientativas.
  - Esto NO sustituye un backtest de MetaTrader con ticks reales ni un forward
    test en demo.

Uso:
    python EA_GBPJPY_H1_EMA100_BUY_ONLY_v5.py --h1-csv GBPJPY_H1.csv --ltf-csv GBPJPY_M15.csv
    python EA_GBPJPY_H1_EMA100_BUY_ONLY_v5.py --h1-csv GBPJPY_H1.csv --preset friday_close

Dependencias: pip install pandas numpy
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from dataclasses import asdict, dataclass, field, replace
from enum import IntEnum
from typing import Iterable, Optional

import numpy as np
import pandas as pd


# =============================================================================
# CONFIGURACION
# =============================================================================


class Direction(IntEnum):
    FLAT = -1
    BUY = 0
    SELL = 1


@dataclass
class Config:
    name: str = "ema100_buy_only"

    # Parametros del EA
    fixed_lots: float = 0.10
    stop_loss_pips: float = 165.0
    take_profit_pips: float = 316.0
    fi_period: int = 22
    ao_level: float = 3.47
    fi_formula: str = "mt4_faithful"  # o "raw_force_sma" (variante Elder, no MT4)
    use_ao_exit: bool = False         # v6: salida por AO desactivada (no actuaba nunca)
    sigma: float = 1e-6

    # Filtro de tendencia (el EA original: EMA100, solo BUY)
    use_trend_filter: bool = True
    trend_ema_period: int = 100
    direction_mode: str = "buy_only"  # "both", "buy_only", "sell_only"

    # Filtros opcionales de entrada
    blocked_weekdays: tuple[int, ...] = field(default_factory=tuple)   # lunes=0
    allowed_weekdays: Optional[tuple[int, ...]] = None
    blocked_entry_hours: tuple[int, ...] = field(default_factory=tuple)
    allowed_entry_hours: Optional[tuple[int, ...]] = None
    use_atr_filter: bool = False
    atr_period: int = 14
    atr_quantile_lookback: int = 5040
    atr_quantile_min: float = 0.0
    atr_quantile_max: float = 1.0

    # Costes / microestructura
    pip: float = 0.01
    point: float = 0.001
    spread_pips: float = 2.5          # fallback si no hay columna de spread
    use_bar_spread: bool = True       # usa el spread real de la barra si existe
    max_spread_pips: float = 0.0      # paridad Max_Spread_Points del MQ4 (0 = off)
    pip_value_per_lot: float = 7.0
    commission_per_lot_per_side: float = 0.0
    swap_long_per_lot_per_night: float = 0.0
    swap_short_per_lot_per_night: float = 0.0
    initial_capital: float = 10_000.0

    # Sesion (segundos desde medianoche, hora del servidor del CSV)
    session_mon_thu_open: int = 3600
    session_mon_thu_close: int = 75600
    session_fri_open: int = 3600
    session_fri_close: int = 64800
    ignore_sunday: bool = True
    close_at_session_close: bool = False
    close_at_friday_close: bool = False

    # Gestion v5 (0 = desactivado; por defecto todo off = paridad con el EA)
    breakeven_trigger_pips: float = 0.0
    breakeven_offset_pips: float = 0.0
    trail_atr_mult: float = 0.0
    trail_activate_pips: float = 0.0
    max_hold_hours: int = 0

    # Modelo de fills
    gap_aware_sl: bool = True
    close_open_position_at_end: bool = True


# =============================================================================
# CARGA DE DATOS
# =============================================================================


def load_price_csv(path: str) -> pd.DataFrame:
    """Carga precios en uno de estos formatos:

    1. TSV MT5: cabecera 'Time Open High Low Close Volume' (6 nombres) pero
       7 columnas de datos; la 7a es el spread en points.
    2. CSV/TSV con cabecera que incluya time/datetime/date + open/high/low/close
       [+ volume] [+ spread].
    3. MT4 sin cabecera: date,time,open,high,low,close,volume.

    Devuelve DataFrame indexado por datetime con columnas
    open, high, low, close, volume [, spread_points].
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        line1 = fh.readline().rstrip("\r\n")
        line2 = fh.readline().rstrip("\r\n")

    sep = "\t" if "\t" in line1 else (";" if ";" in line1 else ",")
    f1 = line1.split(sep)
    f2 = line2.split(sep)
    header_has_letters = any(re.search(r"[A-Za-z]", x) for x in f1)

    if header_has_letters and len(f2) == len(f1) + 1:
        # Formato 1: MT5 con columna extra de spread sin nombre.
        names = ["time", "open", "high", "low", "close", "volume", "spread_points"]
        df = pd.read_csv(path, sep=sep, skiprows=1, header=None, names=names)
        df.index = pd.to_datetime(df["time"], errors="coerce")
        df = df.drop(columns=["time"])
    elif header_has_letters:
        df = pd.read_csv(path, sep=sep)
        df.columns = [str(c).strip().lower() for c in df.columns]
        time_col = next((c for c in ("time", "datetime", "date") if c in df.columns), None)
        if time_col is None:
            raise ValueError(f"{path}: no encuentro columna time/datetime/date.")
        df.index = pd.to_datetime(df[time_col], errors="coerce")
        df = df.drop(columns=[time_col])
        if "spread" in df.columns:
            df = df.rename(columns={"spread": "spread_points"})
        if "volume" not in df.columns:
            df["volume"] = 1.0
    else:
        names = ["date", "time", "open", "high", "low", "close", "volume"]
        df = pd.read_csv(path, sep=sep, header=None, names=names,
                         dtype={"date": str, "time": str})
        df.index = pd.to_datetime(df["date"] + " " + df["time"],
                                  format="%Y.%m.%d %H:%M", errors="coerce")
        df = df.drop(columns=["date", "time"])

    df = df[~df.index.isna()].sort_index()
    df = df[~df.index.duplicated(keep="last")]

    keep = ["open", "high", "low", "close", "volume"]
    if "spread_points" in df.columns:
        keep.append("spread_points")
    df = df[keep].astype(float)

    valid = (df["high"] >= df[["open", "close", "low"]].max(axis=1)) & (
        df["low"] <= df[["open", "close", "high"]].min(axis=1)
    )
    df = df[valid]
    return df


def resample_to_h1(ltf: pd.DataFrame) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    if "spread_points" in ltf.columns:
        agg["spread_points"] = "first"
    return ltf.resample("1h", label="left", closed="left").agg(agg).dropna(
        subset=["open", "high", "low", "close"]
    )


# =============================================================================
# INDICADORES
# =============================================================================


def compute_indicators(h1: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    out = h1.copy()

    # Force Index oficial MT4: FORCE(i) = VOLUME(i) * (SMA_close[i] - SMA_close[i-1]).
    # Como VOLUME > 0, el SIGNO solo depende de la pendiente de la SMA:
    # la entrada equivale a "la SMA(fi_period) paso de subir a bajar".
    sma_close = out["close"].rolling(cfg.fi_period).mean()
    formula = cfg.fi_formula.lower()
    if formula in ("mt4_faithful", "sma_diff"):
        out["force_index"] = out["volume"] * (sma_close - sma_close.shift(1))
    elif formula == "raw_force_sma":
        raw = (out["close"] - out["close"].shift(1)) * out["volume"]
        out["force_index"] = raw.rolling(cfg.fi_period).mean()
    else:
        raise ValueError("fi_formula: usa 'mt4_faithful', 'sma_diff' o 'raw_force_sma'.")

    median_price = (out["high"] + out["low"]) / 2.0
    out["awesome_oscillator"] = median_price.rolling(5).mean() - median_price.rolling(34).mean()

    out["ema_trend"] = out["close"].ewm(span=cfg.trend_ema_period, adjust=False).mean()

    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [out["high"] - out["low"],
         (out["high"] - prev_close).abs(),
         (out["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    out["atr"] = tr.rolling(cfg.atr_period).mean()

    out["atr_q_min"] = np.nan
    out["atr_q_max"] = np.nan
    if cfg.use_atr_filter:
        lookback = max(int(cfg.atr_quantile_lookback), cfg.atr_period * 5, 50)
        min_periods = min(lookback, max(250, cfg.atr_period * 10))
        if cfg.atr_quantile_min > 0.0:
            out["atr_q_min"] = out["atr"].rolling(lookback, min_periods=min_periods).quantile(cfg.atr_quantile_min)
        if cfg.atr_quantile_max < 1.0:
            out["atr_q_max"] = out["atr"].rolling(lookback, min_periods=min_periods).quantile(cfg.atr_quantile_max)
    return out


# =============================================================================
# SESION (paridad exacta con el MQ4, incluido lastBarFix)
# =============================================================================

H1_SECONDS = 3600


def _secs(ts: pd.Timestamp) -> int:
    return ts.hour * 3600 + ts.minute * 60 + ts.second


def is_out_of_session(ts: pd.Timestamp, cfg: Config) -> bool:
    wd = ts.weekday()  # lunes=0 ... domingo=6
    secs = _secs(ts)
    if wd == 6:  # domingo
        return cfg.ignore_sunday
    if wd < 4:   # lunes-jueves
        fix = H1_SECONDS if cfg.close_at_session_close else 0
        return secs < cfg.session_mon_thu_open or secs + fix > cfg.session_mon_thu_close
    if wd == 4:  # viernes
        fix = H1_SECONDS if (cfg.close_at_friday_close or cfg.close_at_session_close) else 0
        return secs < cfg.session_fri_open or secs + fix > cfg.session_fri_close
    return True  # sabado


def is_force_session_close(ts: pd.Timestamp, cfg: Config) -> bool:
    if not (cfg.close_at_friday_close or cfg.close_at_session_close):
        return False
    wd = ts.weekday()
    secs = _secs(ts)
    if 0 <= wd < 4 and cfg.close_at_session_close:
        return secs + H1_SECONDS > cfg.session_mon_thu_close
    if wd == 4:
        return secs + H1_SECONDS > cfg.session_fri_close
    return False


# =============================================================================
# SENIALES
# =============================================================================


def entry_signal(fi_1: float, fi_2: float, close_1: float, ema_1: float, cfg: Config) -> Optional[Direction]:
    if np.isnan(fi_1) or np.isnan(fi_2):
        return None

    long_signal = fi_1 < -cfg.sigma and fi_2 > cfg.sigma
    short_signal = fi_1 > cfg.sigma and fi_2 < -cfg.sigma

    if long_signal:
        # Paridad MQ4: bloquea si Close[1] <= EMA[1]
        if cfg.use_trend_filter and close_1 <= ema_1:
            return None
        return Direction.BUY
    if short_signal:
        if cfg.use_trend_filter and close_1 >= ema_1:
            return None
        return Direction.SELL
    return None


def passes_entry_filters(direction: Direction, ts: pd.Timestamp, atr_value: float,
                         atr_q_min: float, atr_q_max: float, cfg: Config) -> bool:
    if cfg.direction_mode == "buy_only" and direction != Direction.BUY:
        return False
    if cfg.direction_mode == "sell_only" and direction != Direction.SELL:
        return False
    if cfg.direction_mode not in {"both", "buy_only", "sell_only"}:
        raise ValueError("direction_mode debe ser 'both', 'buy_only' o 'sell_only'.")

    wd, hour = int(ts.weekday()), int(ts.hour)
    if cfg.allowed_weekdays is not None and wd not in set(cfg.allowed_weekdays):
        return False
    if wd in set(cfg.blocked_weekdays):
        return False
    if cfg.allowed_entry_hours is not None and hour not in set(cfg.allowed_entry_hours):
        return False
    if hour in set(cfg.blocked_entry_hours):
        return False

    if cfg.use_atr_filter:
        if np.isnan(atr_value):
            return False
        if cfg.atr_quantile_min > 0.0 and (np.isnan(atr_q_min) or atr_value < atr_q_min):
            return False
        if cfg.atr_quantile_max < 1.0 and (np.isnan(atr_q_max) or atr_value > atr_q_max):
            return False
    return True


def exit_signal(direction: Direction, ao_1: float, ao_2: float, cfg: Config) -> bool:
    if not cfg.use_ao_exit:
        return False
    if direction == Direction.FLAT or np.isnan(ao_1) or np.isnan(ao_2):
        return False
    long_exit = ao_1 > cfg.ao_level + cfg.sigma and ao_2 < cfg.ao_level - cfg.sigma
    short_exit = ao_1 < -cfg.ao_level - cfg.sigma and ao_2 > -cfg.ao_level + cfg.sigma
    return (direction == Direction.BUY and long_exit) or (direction == Direction.SELL and short_exit)


# =============================================================================
# COSTES
# =============================================================================


def count_swap_nights(entry_time, exit_time) -> int:
    if entry_time is None or exit_time is None:
        return 0
    entry_time, exit_time = pd.Timestamp(entry_time), pd.Timestamp(exit_time)
    if exit_time <= entry_time:
        return 0
    nights = 0
    day = entry_time.normalize() + pd.Timedelta(days=1)
    end = exit_time.normalize()
    while day <= end:
        wd = day.weekday()
        if wd < 5:
            nights += 3 if wd == 2 else 1  # miercoles triple
        day += pd.Timedelta(days=1)
    return nights


# =============================================================================
# BACKTESTER
# =============================================================================


@dataclass
class _Pos:
    direction: Direction = Direction.FLAT
    entry_time: Optional[pd.Timestamp] = None
    entry_price: float = 0.0       # Ask en BUY, Bid en SELL
    stop_loss: float = 0.0         # nivel Bid en BUY, Ask en SELL
    take_profit: float = 0.0
    lots: float = 0.0
    spread_at_entry: float = 0.0   # pips
    mae_pips: float = 0.0
    mfe_pips: float = 0.0
    be_done: bool = False

    @property
    def is_open(self) -> bool:
        return self.direction != Direction.FLAT


def backtest(h1_input: pd.DataFrame, cfg: Config,
             ltf: Optional[pd.DataFrame] = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Backtest barra a barra sobre H1 con verificacion intrabar en LTF.

    Orden de eventos en el open de cada barra H1 (i):
      1. Cierre forzado de sesion (antes del filtro de sesion, como el MQ4).
      2. Time stop.
      3. Salida por AO (solo dentro de sesion), con barras cerradas i-1, i-2.
      4. Entrada por FI (solo dentro de sesion y sin posicion), barras i-1, i-2.
      5. SL/TP/BE/trailing procesados secuencialmente sobre las barras LTF de
         esa hora (o la propia barra H1 si no hay LTF). Los SL/TP se comprueban
         ANTES de actualizar BE/trailing con esa misma barra (conservador).
    """
    h1 = compute_indicators(h1_input, cfg)
    if h1.empty:
        raise ValueError("h1_input esta vacio.")

    idx = h1.index
    op = h1["open"].to_numpy(float)
    hi = h1["high"].to_numpy(float)
    lo = h1["low"].to_numpy(float)
    cl = h1["close"].to_numpy(float)
    fi = h1["force_index"].to_numpy(float)
    ao = h1["awesome_oscillator"].to_numpy(float)
    ema = h1["ema_trend"].to_numpy(float)
    atr = h1["atr"].to_numpy(float)
    aqmin = h1["atr_q_min"].to_numpy(float)
    aqmax = h1["atr_q_max"].to_numpy(float)

    if cfg.use_bar_spread and "spread_points" in h1.columns:
        spr = h1["spread_points"].to_numpy(float) * cfg.point / cfg.pip  # pips
    else:
        spr = np.full(len(h1), cfg.spread_pips)

    # LTF precalculado
    l_idx = l_op = l_hi = l_lo = None
    l_starts = l_ends = None
    if ltf is not None and not ltf.empty:
        l_idx = ltf.index
        l_op = ltf["open"].to_numpy(float)
        l_hi = ltf["high"].to_numpy(float)
        l_lo = ltf["low"].to_numpy(float)
        l_starts = l_idx.searchsorted(idx, side="left")
        l_ends = l_idx.searchsorted(idx + pd.Timedelta(hours=1), side="left")

    min_bars = max(
        34,
        cfg.fi_period + 2,
        cfg.trend_ema_period if cfg.use_trend_filter else 0,
        cfg.atr_period + 2,
        min(cfg.atr_quantile_lookback, 250) if cfg.use_atr_filter else 0,
    ) + 2
    if len(h1) <= min_bars:
        raise ValueError(f"Barras H1 insuficientes: necesito > {min_bars}, hay {len(h1)}.")

    trades: list[dict] = []
    equity_rows: list[dict] = []
    pos = _Pos()
    capital = cfg.initial_capital
    pip = cfg.pip
    use_be = cfg.breakeven_trigger_pips > 0
    use_trail = cfg.trail_atr_mult > 0
    max_hold = pd.Timedelta(hours=cfg.max_hold_hours) if cfg.max_hold_hours > 0 else None

    def _pnl_pips(exit_price: float) -> float:
        if pos.direction == Direction.BUY:
            return (exit_price - pos.entry_price) / pip
        return (pos.entry_price - exit_price) / pip

    def close_trade(exit_time, exit_price: float, reason: str) -> None:
        nonlocal pos, capital
        pips = _pnl_pips(exit_price)
        gross = pips * pos.lots * cfg.pip_value_per_lot
        commission = 2.0 * cfg.commission_per_lot_per_side * pos.lots
        nights = count_swap_nights(pos.entry_time, exit_time)
        swap_rate = (cfg.swap_long_per_lot_per_night if pos.direction == Direction.BUY
                     else cfg.swap_short_per_lot_per_night)
        swap = nights * swap_rate * pos.lots
        capital += gross - commission + swap
        hold_h = (pd.Timestamp(exit_time) - pd.Timestamp(pos.entry_time)).total_seconds() / 3600.0
        trades.append({
            "entry_time": pos.entry_time, "exit_time": exit_time,
            "direction": pos.direction.name,
            "entry_price": round(pos.entry_price, 5), "exit_price": round(float(exit_price), 5),
            "stop_loss": round(pos.stop_loss, 5), "take_profit": round(pos.take_profit, 5),
            "lots": pos.lots, "spread_at_entry_pips": round(pos.spread_at_entry, 2),
            "pnl_pips": round(float(pips), 3),
            "mae_pips": round(pos.mae_pips, 1), "mfe_pips": round(pos.mfe_pips, 1),
            "gross_cash": round(float(gross), 2), "commission_cash": round(float(commission), 2),
            "swap_cash": round(float(swap), 2),
            "pnl_cash": round(float(gross - commission + swap), 2),
            "hold_hours": round(hold_h, 1),
            "exit_reason": reason, "capital_after": round(float(capital), 2),
        })
        pos = _Pos()

    def open_pos(direction: Direction, bid_open: float, spread_pips: float, ts) -> _Pos:
        sp = spread_pips * pip
        ask_open = bid_open + sp
        sl_d = cfg.stop_loss_pips * pip
        tp_d = cfg.take_profit_pips * pip
        if direction == Direction.BUY:
            entry = ask_open
            sl = bid_open - sl_d if cfg.stop_loss_pips > 0 else -np.inf
            tp = bid_open + tp_d if cfg.take_profit_pips > 0 else np.inf
        else:
            entry = bid_open
            sl = ask_open + sl_d if cfg.stop_loss_pips > 0 else np.inf
            tp = ask_open - tp_d if cfg.take_profit_pips > 0 else -np.inf
        return _Pos(direction=direction, entry_time=ts, entry_price=float(entry),
                    stop_loss=float(sl), take_profit=float(tp), lots=cfg.fixed_lots,
                    spread_at_entry=float(spread_pips))

    def process_intrabar(i: int, spread_pips: float):
        """Procesa la hora i barra LTF a barra LTF. Devuelve (time, price, reason) o None.

        BUY: niveles SL/TP son niveles Bid; el historico es Bid, directo.
        SELL: SL/TP son niveles Ask; Ask ~= Bid + spread de la barra de entrada.
        """
        sp = spread_pips * pip
        if l_idx is not None:
            a, b = int(l_starts[i]), int(l_ends[i])
            if b <= a:
                bars = [(idx[i], op[i], hi[i], lo[i])]
            else:
                bars = [(l_idx[j], l_op[j], l_hi[j], l_lo[j]) for j in range(a, b)]
        else:
            bars = [(idx[i], op[i], hi[i], lo[i])]

        trail_ref = atr[i - 1] if i >= 1 else np.nan

        for (bts, bo, bh, bl) in bars:
            if pos.direction == Direction.BUY:
                # 1. SL/TP con el SL vigente (antes de mover BE/trailing)
                if bo <= pos.stop_loss and cfg.gap_aware_sl:
                    return bts, bo, "SL_gap"
                if bl <= pos.stop_loss:
                    # peor caso si SL y TP caen en la misma barra LTF
                    return bts, pos.stop_loss, "SL"
                if bo >= pos.take_profit:
                    return bts, bo, "TP_gap"
                if bh >= pos.take_profit:
                    return bts, pos.take_profit, "TP"
                # 2. MAE/MFE (bid vs entrada ask)
                pos.mae_pips = min(pos.mae_pips, (bl - pos.entry_price) / pip)
                pos.mfe_pips = max(pos.mfe_pips, (bh - pos.entry_price) / pip)
                # 3. Breakeven
                if use_be and not pos.be_done and (bh - pos.entry_price) / pip >= cfg.breakeven_trigger_pips:
                    pos.stop_loss = max(pos.stop_loss, pos.entry_price + cfg.breakeven_offset_pips * pip)
                    pos.be_done = True
                # 4. Trailing por ATR H1 de la barra cerrada previa
                if use_trail and not np.isnan(trail_ref) and (bh - pos.entry_price) / pip >= cfg.trail_activate_pips:
                    pos.stop_loss = max(pos.stop_loss, bh - cfg.trail_atr_mult * trail_ref)
            else:  # SELL
                b_ask_o, b_ask_h, b_ask_l = bo + sp, bh + sp, bl + sp
                if b_ask_o >= pos.stop_loss and cfg.gap_aware_sl:
                    return bts, b_ask_o, "SL_gap"
                if b_ask_h >= pos.stop_loss:
                    return bts, pos.stop_loss, "SL"
                if b_ask_o <= pos.take_profit:
                    return bts, b_ask_o, "TP_gap"
                if b_ask_l <= pos.take_profit:
                    return bts, pos.take_profit, "TP"
                pos.mae_pips = min(pos.mae_pips, (pos.entry_price - b_ask_h) / pip)
                pos.mfe_pips = max(pos.mfe_pips, (pos.entry_price - b_ask_l) / pip)
                if use_be and not pos.be_done and (pos.entry_price - b_ask_l) / pip >= cfg.breakeven_trigger_pips:
                    pos.stop_loss = min(pos.stop_loss, pos.entry_price - cfg.breakeven_offset_pips * pip)
                    pos.be_done = True
                if use_trail and not np.isnan(trail_ref) and (pos.entry_price - b_ask_l) / pip >= cfg.trail_activate_pips:
                    pos.stop_loss = min(pos.stop_loss, b_ask_l + cfg.trail_atr_mult * trail_ref)
        return None

    for i in range(min_bars, len(idx)):
        ts = idx[i]
        bid_open = float(op[i])
        spread_bar = float(spr[i])
        ask_open = bid_open + spread_bar * pip
        inside = not is_out_of_session(ts, cfg)

        # 1. Cierre forzado de sesion (antes del gate de sesion, como el MQ4)
        if pos.is_open and is_force_session_close(ts, cfg):
            close_trade(ts, bid_open if pos.direction == Direction.BUY else ask_open, "SESSION")

        # 2. Time stop
        if pos.is_open and max_hold is not None and (ts - pd.Timestamp(pos.entry_time)) >= max_hold:
            close_trade(ts, bid_open if pos.direction == Direction.BUY else ask_open, "TIME")

        # 3. Salida por AO
        if inside and pos.is_open and exit_signal(pos.direction, ao[i - 1], ao[i - 2], cfg):
            close_trade(ts, bid_open if pos.direction == Direction.BUY else ask_open, "SIGNAL")

        # 4. Entrada
        if inside and not pos.is_open:
            if not (cfg.max_spread_pips > 0 and spread_bar > cfg.max_spread_pips):
                sig = entry_signal(fi[i - 1], fi[i - 2], cl[i - 1], ema[i - 1], cfg)
                if sig is not None and passes_entry_filters(sig, ts, atr[i - 1], aqmin[i - 1], aqmax[i - 1], cfg):
                    pos = open_pos(sig, bid_open, spread_bar, ts)

        # 5. SL/TP/BE/trailing intrabar
        if pos.is_open:
            hit = process_intrabar(i, pos.spread_at_entry)
            if hit is not None:
                close_trade(hit[0], hit[1], hit[2])

        # Equity flotante al cierre de barra
        if pos.is_open:
            if pos.direction == Direction.BUY:
                fpips = (cl[i] - pos.entry_price) / pip
            else:
                fpips = (pos.entry_price - (cl[i] + spread_bar * pip)) / pip
            floating = fpips * pos.lots * cfg.pip_value_per_lot
        else:
            floating = 0.0
        equity_rows.append({"time": ts, "equity": capital + floating,
                            "capital_closed": capital,
                            "open_position": pos.direction.name})

    if pos.is_open and cfg.close_open_position_at_end:
        last_bid = float(cl[-1])
        exit_price = last_bid if pos.direction == Direction.BUY else last_bid + float(spr[-1]) * pip
        close_trade(idx[-1], exit_price, "END")

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_rows)
    metrics = compute_metrics(trades_df, cfg, idx[min_bars], idx[-1], equity_df)
    return trades_df, equity_df, metrics


# =============================================================================
# METRICAS
# =============================================================================


def max_consecutive_losses(pnl: Iterable[float]) -> int:
    max_run = current = 0
    for x in pnl:
        current = current + 1 if x < 0 else 0
        max_run = max(max_run, current)
    return max_run


def compute_metrics(trades: pd.DataFrame, cfg: Config, start, end,
                    equity: Optional[pd.DataFrame] = None) -> dict:
    base = {
        "name": cfg.name,
        "direction_mode": cfg.direction_mode,
        "trend_ema": cfg.trend_ema_period if cfg.use_trend_filter else 0,
        "sl_pips": cfg.stop_loss_pips, "tp_pips": cfg.take_profit_pips,
        "use_bar_spread": cfg.use_bar_spread, "spread_pips_fallback": cfg.spread_pips,
        "friday_close": cfg.close_at_friday_close,
        "be_trigger": cfg.breakeven_trigger_pips, "trail_atr_mult": cfg.trail_atr_mult,
        "max_hold_h": cfg.max_hold_hours,
        "atr_filter": cfg.use_atr_filter, "atr_q_max": cfg.atr_quantile_max,
        "start": str(start), "end": str(end),
        "trades": 0,
    }
    if trades.empty:
        return base

    pips = trades["pnl_pips"].astype(float)
    cash = trades["pnl_cash"].astype(float)
    wins, losses = pips[pips > 0], pips[pips < 0]

    gp, gl = float(wins.sum()), float(-losses.sum())
    pf = gp / gl if gl > 0 else math.inf

    eq_pips = pips.cumsum()
    dd_pips = eq_pips - eq_pips.cummax()

    eq_cash = cfg.initial_capital + cash.cumsum()
    dd_cash = eq_cash - eq_cash.cummax()

    days = max((pd.Timestamp(end) - pd.Timestamp(start)).days, 1)
    years = days / 365.25
    final_capital = float(eq_cash.iloc[-1])
    cagr = ((final_capital / cfg.initial_capital) ** (1 / years) - 1.0
            if final_capital > 0 else np.nan)

    base.update({
        "trades": int(len(trades)),
        "trades_per_year": round(len(trades) / years, 1),
        "win_rate_%": round(100.0 * len(wins) / len(trades), 2),
        "profit_factor": round(pf, 3) if math.isfinite(pf) else math.inf,
        "expectancy_pips": round(float(pips.mean()), 2),
        "avg_win_pips": round(float(wins.mean()), 1) if len(wins) else 0.0,
        "avg_loss_pips": round(float(losses.mean()), 1) if len(losses) else 0.0,
        "total_pips": round(float(pips.sum()), 1),
        "max_dd_closed_pips": round(float(dd_pips.min()), 1),
        "final_capital": round(final_capital, 2),
        "total_return_%": round(100.0 * (final_capital / cfg.initial_capital - 1.0), 2),
        "cagr_%": round(100.0 * cagr, 2) if not np.isnan(cagr) else np.nan,
        "max_dd_closed_cash": round(float(dd_cash.min()), 2),
        "max_consec_losses": int(max_consecutive_losses(pips)),
        "avg_hold_hours": round(float(trades["hold_hours"].mean()), 1),
        "avg_mae_pips": round(float(trades["mae_pips"].mean()), 1),
        "worst_mae_pips": round(float(trades["mae_pips"].min()), 1),
        "avg_mfe_pips": round(float(trades["mfe_pips"].mean()), 1),
        "exit_mix": json.dumps(trades["exit_reason"].value_counts().to_dict(), ensure_ascii=False),
    })

    if equity is not None and not equity.empty:
        eq = equity["equity"].astype(float)
        dd_float = eq - eq.cummax()
        base["max_dd_float_cash"] = round(float(dd_float.min()), 2)
        base["max_dd_float_pips"] = round(float(dd_float.min() / (cfg.fixed_lots * cfg.pip_value_per_lot)), 1)
        base["exposure_%"] = round(100.0 * float((equity["open_position"] != "FLAT").mean()), 1)
    return base


def metrics_by_period(trades: pd.DataFrame, cfg: Config, split: pd.Timestamp) -> tuple[dict, dict]:
    """Metricas antes (IS) y despues (OOS) de una fecha de corte, por exit_time."""
    if trades.empty:
        return {}, {}
    t = trades.copy()
    t["exit_time"] = pd.to_datetime(t["exit_time"])
    is_t = t[t["exit_time"] < split]
    oos_t = t[t["exit_time"] >= split]
    m_is = compute_metrics(is_t, cfg, t["exit_time"].min(), split) if len(is_t) else {}
    m_oos = compute_metrics(oos_t, cfg, split, t["exit_time"].max()) if len(oos_t) else {}
    return m_is, m_oos


def annual_metrics(trades: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    rows = []
    t = trades.copy()
    t["exit_time"] = pd.to_datetime(t["exit_time"])
    for year, group in t.groupby(t["exit_time"].dt.year):
        m = compute_metrics(group, cfg, pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year}-12-31"))
        m["year"] = int(year)
        rows.append(m)
    return pd.DataFrame(rows).sort_values("year")


# =============================================================================
# PRESETS
# =============================================================================


def get_presets() -> dict[str, Config]:
    """Presets definidos a priori. baseline = v6 (sin salida AO); baseline_v5 = paridad con el MQ4 v4.10."""
    b = Config()  # ema100_buy_only con spread real por barra
    return {
        "baseline": replace(b, name="baseline"),
        "baseline_v5_ao_exit": replace(b, name="baseline_v5_ao_exit", use_ao_exit=True),
        "baseline_fixed_spread": replace(b, name="baseline_fixed_spread", use_bar_spread=False),
        "friday_close": replace(b, name="friday_close", close_at_friday_close=True),
        "session_close": replace(b, name="session_close", close_at_session_close=True,
                                 close_at_friday_close=True),
        "be100": replace(b, name="be100", breakeven_trigger_pips=100, breakeven_offset_pips=5),
        "be160": replace(b, name="be160", breakeven_trigger_pips=160, breakeven_offset_pips=10),
        "trail_atr3": replace(b, name="trail_atr3", trail_atr_mult=3.0, trail_activate_pips=80),
        "trail_atr5": replace(b, name="trail_atr5", trail_atr_mult=5.0, trail_activate_pips=0),
        "time96": replace(b, name="time96", max_hold_hours=96),
        "time168": replace(b, name="time168", max_hold_hours=168),
        "fri_be": replace(b, name="fri_be", close_at_friday_close=True,
                          breakeven_trigger_pips=100, breakeven_offset_pips=5),
        "fri_be_trail": replace(b, name="fri_be_trail", close_at_friday_close=True,
                                breakeven_trigger_pips=100, breakeven_offset_pips=5,
                                trail_atr_mult=3.0, trail_activate_pips=80),
        "ema50": replace(b, name="ema50", trend_ema_period=50),
        "ema200": replace(b, name="ema200", trend_ema_period=200),
        "no_ema": replace(b, name="no_ema", use_trend_filter=False),
        "both_dirs": replace(b, name="both_dirs", direction_mode="both"),
        "low_atr50": replace(b, name="low_atr50", use_atr_filter=True, atr_quantile_max=0.50),
        "max_spread4": replace(b, name="max_spread4", max_spread_pips=4.0),
        "commission": replace(b, name="commission", commission_per_lot_per_side=3.5),
    }


# =============================================================================
# CLI
# =============================================================================


def save_outputs(outdir: str, cfg: Config, trades: pd.DataFrame,
                 equity: pd.DataFrame, metrics: dict) -> None:
    os.makedirs(outdir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_\-.]+", "_", cfg.name)
    trades.to_csv(os.path.join(outdir, f"trades_{safe}.csv"), index=False)
    equity.to_csv(os.path.join(outdir, f"equity_curve_{safe}.csv"), index=False)
    annual_metrics(trades, cfg).to_csv(os.path.join(outdir, f"annual_metrics_{safe}.csv"), index=False)
    pd.DataFrame([metrics]).to_csv(os.path.join(outdir, f"summary_metrics_{safe}.csv"), index=False)
    with open(os.path.join(outdir, f"config_{safe}.json"), "w", encoding="utf-8") as fh:
        json.dump(asdict(cfg), fh, indent=2, ensure_ascii=False, default=str)


def main() -> None:
    p = argparse.ArgumentParser(description="Backtester v6 EMA100 BUY ONLY GBPJPY H1")
    p.add_argument("--h1-csv", required=True, help="CSV/TSV H1 (o LTF si --resample)")
    p.add_argument("--ltf-csv", help="CSV/TSV de timeframe inferior (M1/M5/M15) para intrabar")
    p.add_argument("--resample", action="store_true",
                   help="Trata --h1-csv como LTF y construye H1 por resampleo")
    p.add_argument("--preset", default="baseline", choices=sorted(get_presets().keys()))
    p.add_argument("--outdir", default="./gbpjpy_v6_outputs")
    p.add_argument("--fixed-lots", type=float, default=None)
    p.add_argument("--spread-pips", type=float, default=None, help="fuerza spread fijo")
    p.add_argument("--split", default=None, help="fecha de corte IS/OOS, ej. 2022-07-11")
    args = p.parse_args()

    raw = load_price_csv(args.h1_csv)
    if args.resample:
        ltf = raw
        h1 = resample_to_h1(raw)
    else:
        h1 = raw
        ltf = load_price_csv(args.ltf_csv) if args.ltf_csv else None

    cfg = get_presets()[args.preset]
    if args.fixed_lots is not None:
        cfg = replace(cfg, fixed_lots=args.fixed_lots)
    if args.spread_pips is not None:
        cfg = replace(cfg, spread_pips=args.spread_pips, use_bar_spread=False)

    trades, equity, metrics = backtest(h1, cfg, ltf=ltf)
    save_outputs(args.outdir, cfg, trades, equity, metrics)

    print("\n=== RESUMEN ===")
    for k, v in metrics.items():
        print(f"{k:24s}: {v}")

    if args.split:
        m_is, m_oos = metrics_by_period(trades, cfg, pd.Timestamp(args.split))
        for tag, m in (("IS (antes del corte)", m_is), ("OOS (despues)", m_oos)):
            print(f"\n--- {tag} ---")
            for k in ("trades", "win_rate_%", "profit_factor", "expectancy_pips",
                      "total_pips", "max_dd_closed_pips"):
                if k in m:
                    print(f"{k:20s}: {m[k]}")

    print(f"\nOutputs en: {os.path.abspath(args.outdir)}")


if __name__ == "__main__":
    main()
