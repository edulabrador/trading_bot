"""
GBPJPY_H4_35839595.mq4 adaptado a la interfaz de run_tests.py (motor: backtests/engine.py).

Entrada:
  LONG : la apertura de la vela actual esta por encima de la Envelope superior
         (SMA 34, 0.87%) de la vela 1, y la apertura de la vela 1 estaba por
         debajo de la Envelope superior de la vela 2 (ruptura al alza)
  SHORT: espejo con la Envelope inferior
Salida: Bulls Power(23) cruza el nivel -0.0012 hacia arriba (cierra largos) o
        +0.0012 hacia abajo (cierra cortos). En un par JPY el nivel es casi 0.
SL 68 / TP 486 pips, 0.01 lotes. Sin filtro de sesion. Velas H4 desde el CSV H1.
"""
import os, sys
from dataclasses import dataclass, replace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import engine as E
from engine import Direction, load_price_csv, count_swap_nights, set_entry_override  # noqa: F401

SIG = E.SIGMA
SENS_PARAMS = ["env_period", "env_deviation", "bulls_period", "stop_loss_pips", "take_profit_pips"]
WF_PARAMS = ["env_period", "stop_loss_pips", "take_profit_pips"]


@dataclass
class Config(E.BaseConfig):
    name: str = "baseline"
    timeframe: str = "H4"
    fixed_lots: float = 0.01
    stop_loss_pips: float = 68
    take_profit_pips: float = 486
    pip: float = 0.01
    point: float = 0.001
    spread_pips: float = 2.5
    pip_value_per_lot: float = 7.0   # 1000 JPY / USDJPY ~ 140-150

    env_period: int = 34
    env_deviation: float = 0.87
    bulls_period: int = 23
    bulls_level: float = -0.0012


def signals(b: pd.DataFrame, c: Config) -> pd.DataFrame:
    o, h, cl = (b[k].to_numpy(float) for k in ("open", "high", "close"))
    up, dn = E.envelopes(cl, c.env_period, c.env_deviation)
    up1, up2, dn1, dn2, o1 = E.lag(up, 1), E.lag(up, 2), E.lag(dn, 1), E.lag(dn, 2), E.lag(o, 1)
    bp = E.bulls_power(h, cl, c.bulls_period); b1, b2 = E.lag(bp, 1), E.lag(bp, 2)
    lv = c.bulls_level
    return pd.DataFrame({
        "long_entry": (o > up1 + SIG) & (o1 < up2 - SIG),
        "short_entry": (o < dn1 - SIG) & (o1 > dn2 + SIG),
        "exit_long": (b1 > lv + SIG) & (b2 < lv - SIG),
        "exit_short": (b1 < -lv - SIG) & (b2 > -lv + SIG),
    }, index=b.index)


def get_presets() -> dict:
    b = Config()
    return {"baseline": b,
            "baseline_fixed_spread": replace(b, name="baseline_fixed_spread", use_bar_spread=False),
            "buy_only": replace(b, name="buy_only", direction_mode="buy_only"),
            "sell_only": replace(b, name="sell_only", direction_mode="sell_only"),
            "no_signal_exit": replace(b, name="no_signal_exit", bulls_level=1e9),
            "commission": replace(b, name="commission", commission_per_lot_per_side=3.5)}


def backtest(h1, cfg: Config = None, ltf=None):
    return E.backtest(h1, cfg or Config(), signals)
