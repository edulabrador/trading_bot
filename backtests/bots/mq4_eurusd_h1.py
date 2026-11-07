"""
R_EURUSD_H1.mq4 adaptado a la interfaz de run_tests.py (motor: backtests/engine.py).

Entrada (todas a la vez, velas cerradas 1 y 2):
  LONG : Williams %R(31) cruza hacia arriba el nivel -24
         y Stochastic(3,2,2) main baja
         y los "dientes" del Alligator (SMMA 6, shift 5, precio mediano) bajan
  SHORT: espejo (WPR cruza hacia abajo -100-(-24) = -76, Stoch sube, dientes suben)
Salida: giro del RVI(14) (largos: el RVI forma un minimo; cortos: un maximo)
SL 324 / TP 328 pips, 0.10 lotes. Sesion: lun-vie 02:00-22:00, sin domingos.
"""
import os, sys
from dataclasses import dataclass, replace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import engine as E
from engine import Direction, load_price_csv, count_swap_nights, set_entry_override  # noqa: F401

SIG = E.SIGMA
SENS_PARAMS = ["wpr_period", "wpr_level", "stoch_k", "stoch_slowing", "teeth_period", "teeth_shift",
               "rvi_period", "stop_loss_pips", "take_profit_pips"]
WF_PARAMS = ["wpr_period", "stop_loss_pips", "take_profit_pips"]


@dataclass
class Config(E.BaseConfig):
    name: str = "baseline"
    timeframe: str = "H1"
    fixed_lots: float = 0.10
    stop_loss_pips: float = 324
    take_profit_pips: float = 328
    pip: float = 0.0001
    point: float = 0.00001
    spread_pips: float = 1.0
    use_bar_spread: bool = False   # el CSV mezcla datos sin ASK (hasta 2022) y con ASK: spread fijo en todo el periodo
    pip_value_per_lot: float = 10.0
    session_mon_thu_open: int = 7200
    session_mon_thu_close: int = 79200
    session_fri_open: int = 7200
    session_fri_close: int = 79200
    ignore_sunday: bool = True

    wpr_period: int = 31
    wpr_level: float = -24.0
    stoch_k: int = 3
    stoch_d: int = 2          # no afecta a la linea principal
    stoch_slowing: int = 2
    teeth_period: int = 6
    teeth_shift: int = 5
    rvi_period: int = 14


def signals(b: pd.DataFrame, c: Config) -> pd.DataFrame:
    o, h, l, cl = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    w = E.wpr(h, l, cl, c.wpr_period); w1, w2 = E.lag(w, 1), E.lag(w, 2)
    i0l = (w1 > c.wpr_level + SIG) & (w2 < c.wpr_level - SIG)
    i0s = (w1 < -100 - c.wpr_level - SIG) & (w2 > -100 - c.wpr_level + SIG)
    st = E.stochastic_main(h, l, cl, c.stoch_k, c.stoch_slowing); s1, s2 = E.lag(st, 1), E.lag(st, 2)
    teeth = E.alligator_line(h, l, c.teeth_period, c.teeth_shift); t1, t2 = E.lag(teeth, 1), E.lag(teeth, 2)
    r = E.rvi_main(o, h, l, cl, c.rvi_period); r1, r2, r3 = E.lag(r, 1), E.lag(r, 2), E.lag(r, 3)
    return pd.DataFrame({
        "long_entry": i0l & (s1 < s2 - SIG) & (t1 < t2 - SIG),
        "short_entry": i0s & (s1 > s2 + SIG) & (t1 > t2 + SIG),
        "exit_long": (r1 > r2 + SIG) & (r2 < r3 - SIG),
        "exit_short": (r1 < r2 - SIG) & (r2 > r3 + SIG),
    }, index=b.index)


def get_presets() -> dict:
    b = Config()
    return {"baseline": b,
            "baseline_fixed_spread": replace(b, name="baseline_fixed_spread", use_bar_spread=False),
            "buy_only": replace(b, name="buy_only", direction_mode="buy_only"),
            "sell_only": replace(b, name="sell_only", direction_mode="sell_only"),
            "no_session": replace(b, name="no_session", session_mon_thu_open=0, session_mon_thu_close=86400,
                                  session_fri_open=0, session_fri_close=86400),
            "commission": replace(b, name="commission", commission_per_lot_per_side=3.5),
            # Candidato de la ronda 2 (R2c): sin salida RVI + SL/TP por ATR D1 + tendencia D1 SMA200.
            # Multiplos calibrados en desarrollo (ATR D1 mediano 94.2 pips -> 324/94.2, 328/94.2).
            "r2c": replace(b, name="r2c", use_signal_exit=False, sl_atr_mult=3.438, tp_atr_mult=3.481, d1_trend_sma=200)}


def round2_variants(base: Config, sl_mult: float, tp_mult: float) -> dict:
    """Ronda 2 del protocolo (research/PROTOCOLO.md), fijada antes de ejecutarla."""
    v4 = replace(base, use_signal_exit=False)
    return {"R2a_noexit+trend200": replace(v4, d1_trend_sma=200),
            "R2b_noexit+atr_sltp": replace(v4, sl_atr_mult=sl_mult, tp_atr_mult=tp_mult),
            "R2c_noexit+atr+trend": replace(v4, sl_atr_mult=sl_mult, tp_atr_mult=tp_mult, d1_trend_sma=200)}


def backtest(h1, cfg: Config = None, ltf=None):
    return E.backtest(h1, cfg or Config(), signals)
