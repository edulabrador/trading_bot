# Informe de robustez: mq4_usdjpy_h4

- Datos: `USDJPY_H1.csv`, 2007-01-01 07:00:00 a 2026-10-30 23:00:00, 114,542 velas H1
- Spread por vela (pips): mediana 0.50, p95 3.80
- Preset: `baseline` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 587 |
| trades_per_year | 29.6 |
| win_rate_% | 57.24 |
| profit_factor | 1.076 |
| expectancy_pips | 1.91 |
| avg_win_pips | 47.3 |
| avg_loss_pips | -59.6 |
| total_pips | 1118.6 |
| max_dd_closed_pips | -1689.6 |
| max_dd_float_pips | -1775.9 |
| max_consec_losses | 6 |
| avg_hold_hours | 46.7 |
| exit_mix | {"SIGNAL": 420, "SL": 143, "TP": 16, "SL_gap": 7, "TP_gap": 1} |
| exposure_% | 16.2 |
| cagr_% | 0.04 |

t-stat de la media por trade: **0.64** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **2977 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 503 | 1551 | 1.13 | 59.4 | 3.1 | -1690 | 0.97 |
| OOS (desde el corte) | 84 | -433 | 0.84 | 44.0 | -5.2 | -736 | -0.59 |

Por anio (pips): 2007: -437, 2008: 136, 2009: -77, 2010: -763, 2011: 281, 2012: -133, 2013: 48, 2014: 720, 2015: 249, 2016: 628, 2017: 399, 2018: 439, 2019: 426, 2020: -49, 2021: -116, 2022: -338, 2023: -266, 2024: -155, 2025: 40, 2026: 86

Anios negativos: 9 de 20

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 587 | 1119 | 1.08 | 57.2 | 1.9 | -1690 | 0.64 | 79 |
| spread fijo 2.5 | 587 | 356 | 1.02 | 55.9 | 0.6 | -1870 | 0.2 | 24 |
| spread fijo 4.0 | 587 | -525 | 0.97 | 53.7 | -0.9 | -2082 | -0.3 | -37 |
| spread fijo 6.0 | 587 | -1699 | 0.89 | 50.8 | -2.9 | -2364 | -0.97 | -119 |
| max_spread 4 | 587 | 1119 | 1.08 | 57.2 | 1.9 | -1690 | 0.64 | 79 |
| comision 3.5/lado/lote | 587 | 1119 | 1.08 | 57.2 | 1.9 | -1690 | 0.64 | 38 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~598 trades cada una (el bot: 587).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 1.9 | -1.2 | -6.0 | 6.7 | 87% |
| profit factor | 1.08 | 0.96 | 0.82 | 1.22 | 90% |
| ganancia media/trade OOS | -5.2 | -4.5 | -16.0 | 9.7 | 45% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +3854 pips en todo el periodo; +1543 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -1490, p95 -2330, p99 -2715 pips (historico -1690) |
| bootstrap periodo completo | P(neto<0) 26.7%, neto p5/p50/p95 -1766/1086/3976, maxDD p95 -3076 |
| bootstrap solo OOS | P(neto<0) 72.0% con 84 trades |
| horizonte 1 anio(s) (~30 trades) | P(perder) 45.1%, p5 -565, p50 50 pips |
| horizonte 2 anio(s) (~59 trades) | P(perder) 43.1%, p5 -778, p50 96 pips |
| horizonte 3 anio(s) (~89 trades) | P(perder) 40.8%, p5 -928, p50 153 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 0.94, p50 1.04; P(neto<0) 26.6% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 2715 pips = 190 por 0.01 lotes, 1901 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| di_period_entry | 8 | 660 | 2783 | 1.16 | 1.08 |
| di_period_entry | 10 | 622 | 1827 | 1.11 | 1.17 |
| di_period_entry | 11 | 610 | 985 | 1.06 | 0.88 |
| di_period_entry | 12 | 587 | 1119 | 1.08 | 0.84 |
| di_period_entry | 13 | 571 | 1160 | 1.08 | 0.81 |
| di_period_entry | 14 | 578 | 1956 | 1.15 | 0.9 |
| di_period_entry | 16 | 583 | -348 | 0.98 | 0.72 |
| stoch_k | 9 | 604 | 528 | 1.03 | 0.81 |
| stoch_k | 10 | 590 | 932 | 1.06 | 0.87 |
| stoch_k | 12 | 584 | 1777 | 1.12 | 0.87 |
| stoch_k | 13 | 587 | 1119 | 1.08 | 0.84 |
| stoch_k | 14 | 583 | 956 | 1.07 | 0.88 |
| stoch_k | 16 | 578 | 852 | 1.06 | 0.91 |
| stoch_k | 17 | 579 | 438 | 1.03 | 0.81 |
| stoch_slowing | 10 | 593 | 1588 | 1.1 | 0.76 |
| stoch_slowing | 12 | 575 | 2511 | 1.18 | 0.85 |
| stoch_slowing | 14 | 576 | 747 | 1.05 | 0.76 |
| stoch_slowing | 15 | 587 | 1119 | 1.08 | 0.84 |
| stoch_slowing | 16 | 589 | 920 | 1.06 | 0.95 |
| stoch_slowing | 18 | 581 | -116 | 0.99 | 0.88 |
| stoch_slowing | 20 | 600 | 327 | 1.02 | 0.73 |
| di_period_exit | 17 | 623 | 388 | 1.03 | 0.81 |
| di_period_exit | 19 | 599 | 794 | 1.06 | 0.79 |
| di_period_exit | 22 | 593 | 1296 | 1.09 | 0.76 |
| di_period_exit | 24 | 587 | 1119 | 1.08 | 0.84 |
| di_period_exit | 26 | 581 | 1815 | 1.12 | 0.87 |
| di_period_exit | 29 | 572 | 2480 | 1.17 | 0.92 |
| di_period_exit | 31 | 563 | 2515 | 1.17 | 0.87 |
| stop_loss_pips | 60 | 606 | 1196 | 1.09 | 0.77 |
| stop_loss_pips | 69 | 600 | 1132 | 1.08 | 0.88 |
| stop_loss_pips | 77 | 594 | 1127 | 1.08 | 0.85 |
| stop_loss_pips | 86 | 587 | 1119 | 1.08 | 0.84 |
| stop_loss_pips | 95 | 586 | 1546 | 1.1 | 0.92 |
| stop_loss_pips | 103 | 586 | 1041 | 1.07 | 0.95 |
| stop_loss_pips | 112 | 579 | 466 | 1.03 | 1.01 |
| take_profit_pips | 169 | 594 | 429 | 1.03 | 0.74 |
| take_profit_pips | 193 | 591 | 777 | 1.05 | 0.79 |
| take_profit_pips | 217 | 589 | 1165 | 1.08 | 0.81 |
| take_profit_pips | 241 | 587 | 1119 | 1.08 | 0.84 |
| take_profit_pips | 265 | 586 | 1042 | 1.07 | 0.75 |
| take_profit_pips | 289 | 583 | 310 | 1.02 | 0.71 |
| take_profit_pips | 313 | 583 | 370 | 1.03 | 0.72 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 132/150, PF mediana 1.10, p5 0.96; OOS PF>1 en 49/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 120 | 181 | 241 | 301 | 386 |
|---|---|---|---|---|---|
| 52.0 | 0.98 | 1.03 | 1.07 | 1.02 | 1.01 |
| 69.0 | 1.01 | 1.04 | 1.08 | 1.03 | 1.02 |
| 86.0 | 1.01 | 1.04 | 1.08 | 1.03 | 1.01 |
| 103.0 | 1.01 | 1.04 | 1.07 | 1.02 | 1.01 |
| 129.0 | 0.93 | 0.96 | 0.98 | 0.94 | 0.92 |

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
| 2011 | 16/64/181 | -57 | -224 | 32 | 281 |
| 2012 | 9/64/241 | 65 | -57 | 32 | -133 |
| 2013 | 9/64/241 | -11 | 378 | 42 | 48 |
| 2014 | 9/64/313 | 3 | 528 | 29 | 720 |
| 2015 | 9/86/313 | 304 | -199 | 25 | 249 |
| 2016 | 12/86/313 | 246 | 700 | 25 | 628 |
| 2017 | 12/86/313 | 454 | 471 | 34 | 399 |
| 2018 | 12/86/313 | 542 | 386 | 34 | 439 |
| 2019 | 9/64/313 | 463 | 349 | 27 | 426 |
| 2020 | 9/64/313 | 631 | -362 | 33 | -49 |
| 2021 | 12/64/313 | 343 | -124 | 28 | -116 |
| 2022 | 12/112/241 | 206 | -624 | 27 | -338 |
| 2023 | 16/86/181 | 108 | -619 | 28 | -265 |
| 2024 | 9/112/313 | 264 | -908 | 25 | -155 |
| 2025 | 9/86/313 | 170 | -481 | 22 | 40 |
| 2026 | 9/86/181 | 155 | -192 | 32 | 86 |

Total OOS walk-forward -978 pips (base 2260); anios positivos 6/16; eficiencia -0.25 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 296 | 368.8 | 1.2 |
| D1 > SMA200 | 291 | 749.8 | 2.6 |

Por dia de entrada: lun 1161 (121), mar 267 (127), mie -202 (111), jue 710 (123), vie -817 (105)

Por hora de entrada (pips): 0h 401, 4h 1322, 8h -1205, 12h -1002, 16h 1123, 20h 479

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
