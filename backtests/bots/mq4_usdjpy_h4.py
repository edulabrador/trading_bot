"""
USDJPY_H4_38025241.mq4 adaptado a la interfaz de run_tests.py (motor: backtests/engine.py).

Entrada (velas cerradas 1 y 2):
  LONG : +DI cruza por encima de -DI (ADX 12)
         y Accumulation/Distribution baja
         y Stochastic(13,12,15) main sube
  SHORT: espejo
Salida: cruce contrario de +DI/-DI con periodo 24 (largos: +DI cruza por encima)
SL 86 / TP 241 pips, 0.01 lotes. Sin filtro de sesion. Las velas H4 se construyen
desde el CSV H1, alineadas a 00/04/08... en hora de broker.
"""
import os, sys
from dataclasses import dataclass, replace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import engine as E
from engine import Direction, load_price_csv, count_swap_nights, set_entry_override  # noqa: F401

SIG = E.SIGMA
SENS_PARAMS = ["di_period_entry", "stoch_k", "stoch_slowing", "di_period_exit", "stop_loss_pips", "take_profit_pips"]
WF_PARAMS = ["di_period_entry", "stop_loss_pips", "take_profit_pips"]


@dataclass
class Config(E.BaseConfig):
    name: str = "baseline"
    timeframe: str = "H4"
    fixed_lots: float = 0.01
    stop_loss_pips: float = 86
    take_profit_pips: float = 241
    pip: float = 0.01
    point: float = 0.001
    spread_pips: float = 1.2
    use_bar_spread: bool = False   # el CSV mezcla datos sin ASK (hasta 2022) y con ASK: spread fijo en todo el periodo
    pip_value_per_lot: float = 7.0   # 1000 JPY / USDJPY ~ 140-150

    di_period_entry: int = 12
    stoch_k: int = 13
    stoch_d: int = 12          # no afecta a la linea principal
    stoch_slowing: int = 15
    di_period_exit: int = 24


def signals(b: pd.DataFrame, c: Config) -> pd.DataFrame:
    h, l, cl, v = (b[k].to_numpy(float) for k in ("high", "low", "close", "volume"))
    p, m = E.adx_di(h, l, cl, c.di_period_entry); d = p - m; d1, d2 = E.lag(d, 1), E.lag(d, 2)
    ad = E.accumulation_distribution(h, l, cl, v); a1, a2 = E.lag(ad, 1), E.lag(ad, 2)
    st = E.stochastic_main(h, l, cl, c.stoch_k, c.stoch_slowing); s1, s2 = E.lag(st, 1), E.lag(st, 2)
    p2, m2 = E.adx_di(h, l, cl, c.di_period_exit); e = p2 - m2; e1, e2 = E.lag(e, 1), E.lag(e, 2)
    return pd.DataFrame({
        "long_entry": (d1 > SIG) & (d2 < -SIG) & (a1 < a2 - SIG) & (s1 > s2 + SIG),
        "short_entry": (d1 < -SIG) & (d2 > SIG) & (a1 > a2 + SIG) & (s1 < s2 - SIG),
        "exit_long": (e1 > SIG) & (e2 < -SIG),
        "exit_short": (e1 < -SIG) & (e2 > SIG),
    }, index=b.index)


def get_presets() -> dict:
    b = Config()
    return {"baseline": b,
            "baseline_fixed_spread": replace(b, name="baseline_fixed_spread", use_bar_spread=False),
            "buy_only": replace(b, name="buy_only", direction_mode="buy_only"),
            "sell_only": replace(b, name="sell_only", direction_mode="sell_only"),
            "commission": replace(b, name="commission", commission_per_lot_per_side=3.5)}


def backtest(h1, cfg: Config = None, ltf=None):
    return E.backtest(h1, cfg or Config(), signals)
