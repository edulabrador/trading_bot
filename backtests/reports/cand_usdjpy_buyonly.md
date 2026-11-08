# Informe de robustez: mq4_usdjpy_h4

- Datos: `USDJPY_H1.csv`, 2007-01-01 07:00:00 a 2026-10-30 23:00:00, 114,542 velas H1
- Spread por vela (pips): mediana 0.50, p95 3.80
- Preset: `buy_only` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 283 |
| trades_per_year | 14.3 |
| win_rate_% | 60.42 |
| profit_factor | 1.342 |
| expectancy_pips | 8.12 |
| avg_win_pips | 52.7 |
| avg_loss_pips | -60.5 |
| total_pips | 2296.6 |
| max_dd_closed_pips | -971.8 |
| max_dd_float_pips | -1120.0 |
| max_consec_losses | 6 |
| avg_hold_hours | 48.4 |
| exit_mix | {"SIGNAL": 202, "SL": 70, "TP": 10, "SL_gap": 1} |
| exposure_% | 7.9 |
| cagr_% | 0.08 |

t-stat de la media por trade: **1.77** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **1842 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 250 | 2220 | 1.39 | 62.0 | 8.9 | -972 | 1.86 |
| OOS (desde el corte) | 33 | 77 | 1.07 | 48.5 | 2.3 | -532 | 0.15 |

Por anio (pips): 2007: -145, 2008: 50, 2009: -151, 2010: -252, 2011: 228, 2012: 20, 2013: 634, 2014: 647, 2015: 280, 2016: -120, 2017: 242, 2018: 342, 2019: 198, 2020: -157, 2021: 21, 2022: -142, 2023: 277, 2024: -18, 2025: -38, 2026: 381

Anios negativos: 8 de 20

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 283 | 2297 | 1.34 | 60.4 | 8.1 | -972 | 1.77 | 161 |
| spread fijo 2.5 | 283 | 1929 | 1.28 | 59.4 | 6.8 | -1028 | 1.49 | 134 |
| spread fijo 4.0 | 283 | 1504 | 1.21 | 57.2 | 5.3 | -1092 | 1.16 | 105 |
| spread fijo 6.0 | 283 | 938 | 1.13 | 54.4 | 3.3 | -1180 | 0.73 | 66 |
| max_spread 4 | 283 | 2297 | 1.34 | 60.4 | 8.1 | -972 | 1.77 | 161 |
| comision 3.5/lado/lote | 283 | 2297 | 1.34 | 60.4 | 8.1 | -972 | 1.77 | 141 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~288 trades cada una (el bot: 283).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 8.1 | 1.5 | -4.9 | 10.2 | 93% |
| profit factor | 1.34 | 1.05 | 0.86 | 1.35 | 93% |
| ganancia media/trade OOS | 2.3 | -0.3 | -18.9 | 18.6 | 57% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +3854 pips en todo el periodo; +1543 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -763, p95 -1230, p99 -1483 pips (historico -972) |
| bootstrap periodo completo | P(neto<0) 3.5%, neto p5/p50/p95 195/2292/4460, maxDD p95 -1451 |
| bootstrap solo OOS | P(neto<0) 44.3% con 33 trades |
| horizonte 1 anio(s) (~15 trades) | P(perder) 35.3%, p5 -345, p50 111 pips |
| horizonte 2 anio(s) (~29 trades) | P(perder) 29.2%, p5 -426, p50 222 pips |
| horizonte 3 anio(s) (~44 trades) | P(perder) 24.2%, p5 -453, p50 343 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.13, p50 1.30; P(neto<0) 0.2% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 1483 pips = 104 por 0.01 lotes, 1038 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| di_period_entry | 8 | 327 | 3572 | 1.43 | 1.49 |
| di_period_entry | 10 | 304 | 2652 | 1.35 | 1.3 |
| di_period_entry | 11 | 292 | 1896 | 1.25 | 1.06 |
| di_period_entry | 12 | 283 | 2297 | 1.34 | 1.07 |
| di_period_entry | 13 | 273 | 1799 | 1.28 | 1.07 |
| di_period_entry | 14 | 272 | 2682 | 1.49 | 1.32 |
| di_period_entry | 16 | 271 | 919 | 1.15 | 0.8 |
| stoch_k | 9 | 294 | 1819 | 1.25 | 1.25 |
| stoch_k | 10 | 290 | 1951 | 1.28 | 1.23 |
| stoch_k | 12 | 287 | 2660 | 1.41 | 1.1 |
| stoch_k | 13 | 283 | 2297 | 1.34 | 1.07 |
| stoch_k | 14 | 280 | 2145 | 1.31 | 1.21 |
| stoch_k | 16 | 276 | 1779 | 1.27 | 1.17 |
| stoch_k | 17 | 276 | 1587 | 1.23 | 1.16 |
| stoch_slowing | 10 | 284 | 3406 | 1.54 | 1.33 |
| stoch_slowing | 12 | 286 | 2792 | 1.43 | 1.0 |
| stoch_slowing | 14 | 284 | 2304 | 1.36 | 1.29 |
| stoch_slowing | 15 | 283 | 2297 | 1.34 | 1.07 |
| stoch_slowing | 16 | 284 | 2194 | 1.32 | 1.61 |
| stoch_slowing | 18 | 289 | 2495 | 1.37 | 1.44 |
| stoch_slowing | 20 | 313 | 1272 | 1.16 | 1.33 |
| di_period_exit | 17 | 297 | 1611 | 1.23 | 1.08 |
| di_period_exit | 19 | 288 | 1622 | 1.23 | 0.86 |
| di_period_exit | 22 | 286 | 2020 | 1.3 | 0.9 |
| di_period_exit | 24 | 283 | 2297 | 1.34 | 1.07 |
| di_period_exit | 26 | 284 | 2874 | 1.43 | 1.19 |
| di_period_exit | 29 | 280 | 2468 | 1.36 | 1.25 |
| di_period_exit | 31 | 279 | 2950 | 1.43 | 1.25 |
| stop_loss_pips | 60 | 290 | 1566 | 1.24 | 0.86 |
| stop_loss_pips | 69 | 286 | 2367 | 1.37 | 1.21 |
| stop_loss_pips | 77 | 284 | 2319 | 1.35 | 1.19 |
| stop_loss_pips | 86 | 283 | 2297 | 1.34 | 1.07 |
| stop_loss_pips | 95 | 283 | 3001 | 1.47 | 1.46 |
| stop_loss_pips | 103 | 283 | 2936 | 1.44 | 1.62 |
| stop_loss_pips | 112 | 281 | 2657 | 1.39 | 1.5 |
| take_profit_pips | 169 | 283 | 2140 | 1.33 | 1.2 |
| take_profit_pips | 193 | 283 | 2541 | 1.39 | 1.28 |
| take_profit_pips | 217 | 283 | 2197 | 1.33 | 1.03 |
| take_profit_pips | 241 | 283 | 2297 | 1.34 | 1.07 |
| take_profit_pips | 265 | 283 | 2422 | 1.36 | 1.12 |
| take_profit_pips | 289 | 283 | 2462 | 1.37 | 1.02 |
| take_profit_pips | 313 | 283 | 2572 | 1.38 | 1.04 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 150/150, PF mediana 1.37, p5 1.19; OOS PF>1 en 147/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 120 | 181 | 241 | 301 | 386 |
|---|---|---|---|---|---|
| 52.0 | 1.12 | 1.2 | 1.17 | 1.2 | 1.18 |
| 69.0 | 1.26 | 1.38 | 1.37 | 1.41 | 1.39 |
| 86.0 | 1.25 | 1.36 | 1.34 | 1.38 | 1.36 |
| 103.0 | 1.34 | 1.46 | 1.44 | 1.48 | 1.46 |
| 129.0 | 1.24 | 1.36 | 1.33 | 1.37 | 1.35 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 587 | 1119 | 1.08 | -1690 | 0.84 | -433 |
| baseline_fixed_spread | 587 | 1119 | 1.08 | -1690 | 0.84 | -433 |
| buy_only | 283 | 2297 | 1.34 | -972 | 1.07 | 77 |
| sell_only | 358 | -1406 | 0.85 | -1820 | 0.71 | -602 |
| commission | 587 | 1119 | 1.08 | -1690 | 0.84 | -433 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params di_period_entry/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 12/64/181 | 8 | -49 | 20 | 228 |
| 2012 | 12/64/181 | 42 | 42 | 11 | 20 |
| 2013 | 9.00/86/181 | 78 | 569 | 18 | 634 |
| 2014 | 9.00/86/313 | 188 | 713 | 17 | 647 |
| 2015 | 9.00/86/313 | 426 | -258 | 17 | 280 |
| 2016 | 12/112/313 | 446 | -250 | 13 | -120 |
| 2017 | 16/64/313 | 417 | 452 | 16 | 242 |
| 2018 | 16/64/313 | 327 | 220 | 13 | 343 |
| 2019 | 16/64/313 | 247 | 154 | 18 | 198 |
| 2020 | 9.00/64/313 | 300 | -164 | 19 | -157 |
| 2021 | 9.00/64/313 | 212 | 79 | 16 | 21 |
| 2022 | 9.00/112/313 | 156 | -79 | 11 | -142 |
| 2023 | 9.00/112/313 | 70 | 762 | 8 | 277 |
| 2024 | 9.00/112/313 | 212 | -397 | 8 | -18 |
| 2025 | 9.00/86/181 | 180 | 12 | 15 | -38 |
| 2026 | 9.00/86/181 | 175 | 295 | 13 | 381 |

Total OOS walk-forward 2101 pips (base 2796); anios positivos 10/16; eficiencia 0.60 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 156 | -245.6 | -1.6 |
| D1 > SMA200 | 127 | 2542.2 | 20.0 |

Por dia de entrada: lun 39 (58), mar 518 (66), mie 420 (47), jue 1460 (57), vie -141 (55)

Por hora de entrada (pips): 0h 616, 4h 1083, 8h -538, 12h -127, 16h 785, 20h 477

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
