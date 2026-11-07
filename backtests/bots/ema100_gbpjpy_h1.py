"""
EA GBPJPY H1 EMA100 BUY ONLY (EA Studio #00043898) sobre el motor generico
(backtests/engine.py), para poder aplicarle las mismas mejoras que a los demas.
Reproduce el backtester v5 (bots/ea_gbpjpy_h1_ema100_v5.py) en su preset baseline.

Entrada LONG : Force Index(22) (MT4: volumen x pendiente de la SMA22) pasa de
               positivo a negativo (vela 2 > 0, vela 1 < 0) y Close[1] > EMA100[1].
Salida       : Awesome Oscillator cruza al alza ao_level (3.47). En GBPJPY H1 el AO
               casi nunca llega a ese nivel, asi que en la practica no actua.
               Con exit_mode="none" se elimina (version v6, solo SL/TP).
SL 165 / TP 316 pips, 0.10 lotes. Sesion lun-jue 01:00-21:00, vie 01:00-18:00.
"""
import os, sys
from dataclasses import dataclass, replace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import engine as E
from engine import Direction, load_price_csv, count_swap_nights, set_entry_override  # noqa: F401

SIG = E.SIGMA
SENS_PARAMS = ["fi_period", "trend_ema_period", "stop_loss_pips", "take_profit_pips"]
WF_PARAMS = ["fi_period", "stop_loss_pips", "take_profit_pips"]
WARMUP = 102  # igual que min_bars del v5


@dataclass
class Config(E.BaseConfig):
    name: str = "baseline"
    timeframe: str = "H1"
    fixed_lots: float = 0.10
    stop_loss_pips: float = 165
    take_profit_pips: float = 316
    pip: float = 0.01
    point: float = 0.001
    spread_pips: float = 2.5
    pip_value_per_lot: float = 7.0
    session_mon_thu_open: int = 3600
    session_mon_thu_close: int = 75600
    session_fri_open: int = 3600
    session_fri_close: int = 64800
    ignore_sunday: bool = True
    direction_mode: str = "buy_only"
    use_trend_filter: bool = True

    fi_period: int = 22
    ao_level: float = 3.47
    trend_ema_period: int = 100
    exit_mode: str = "ao"     # "ao" (original) o "none" (v6: sin salida por senal)


def signals(b: pd.DataFrame, c: Config) -> pd.DataFrame:
    h, l, cl, v = (b[k].to_numpy(float) for k in ("high", "low", "close", "volume"))
    s = E.sma(cl, c.fi_period)
    fi = v * (s - E.lag(s, 1)); f1, f2 = E.lag(fi, 1), E.lag(fi, 2)
    em = E.ema(cl, c.trend_ema_period); c1, e1 = E.lag(cl, 1), E.lag(em, 1)
    med = (h + l) / 2
    ao = E.sma(med, 5) - E.sma(med, 34); a1, a2 = E.lag(ao, 1), E.lag(ao, 2)
    trend_l = (c1 > e1) if c.use_trend_filter else np.ones(len(b), bool)
    trend_s = (c1 < e1) if c.use_trend_filter else np.ones(len(b), bool)
    exit_on = c.exit_mode == "ao"
    return pd.DataFrame({
        "long_entry": (f1 < -SIG) & (f2 > SIG) & trend_l,
        "short_entry": (f1 > SIG) & (f2 < -SIG) & trend_s,
        "exit_long": exit_on & (a1 > c.ao_level + SIG) & (a2 < c.ao_level - SIG),
        "exit_short": exit_on & (a1 < -c.ao_level - SIG) & (a2 > -c.ao_level + SIG),
        "long_filter": trend_l,
        "short_filter": trend_s,
    }, index=b.index)


def get_presets() -> dict:
    b = Config()
    return {"baseline": b,
            "v6_no_ao_exit": replace(b, name="v6_no_ao_exit", exit_mode="none"),
            "baseline_fixed_spread": replace(b, name="baseline_fixed_spread", use_bar_spread=False),
            "both_dirs": replace(b, name="both_dirs", direction_mode="both"),
            "commission": replace(b, name="commission", commission_per_lot_per_side=3.5)}


def backtest(h1, cfg: Config = None, ltf=None):
    return E.backtest(h1, cfg or Config(), signals, warmup=WARMUP)
