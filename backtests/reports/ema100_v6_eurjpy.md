# Informe de robustez: ema100_gbpjpy_h1

- Datos: `EURJPY_H1_syn.csv`, 2007-01-01 07:00:00 a 2026-10-30 23:00:00, 111,700 velas H1
- Spread por vela (pips): mediana nan, p95 nan
- Preset: `v6_eurjpy` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 504 |
| trades_per_year | 25.4 |
| win_rate_% | 37.5 |
| profit_factor | 1.102 |
| expectancy_pips | 8.41 |
| avg_win_pips | 243.1 |
| avg_loss_pips | -132.4 |
| total_pips | 4236.7 |
| max_dd_closed_pips | -3049.9 |
| max_dd_float_pips | -3230.6 |
| max_consec_losses | 10 |
| avg_hold_hours | 183.8 |
| exit_mix | {"SL": 295, "TP": 182, "SL_gap": 20, "TP_gap": 7} |
| exposure_% | 54.4 |
| cagr_% | 1.32 |

t-stat de la media por trade: **1.03** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **3396 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 418 | 2016 | 1.06 | 36.6 | 4.8 | -3050 | 0.54 |
| OOS (desde el corte) | 86 | 2221 | 1.34 | 41.9 | 25.8 | -662 | 1.3 |

Por anio (pips): 2007: 690, 2008: -1168, 2009: 2140, 2010: -1770, 2011: -683, 2012: 2323, 2013: 340, 2014: 287, 2015: -618, 2016: -173, 2017: 484, 2018: -1066, 2019: -550, 2020: 234, 2021: 560, 2022: 332, 2023: 329, 2024: 1327, 2025: 1585, 2026: -365

Anios negativos: 8 de 20

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 504 | 4237 | 1.1 | 37.5 | 8.4 | -3050 | 1.03 | 2966 |
| spread fijo 2.5 | 504 | 3985 | 1.1 | 37.5 | 7.9 | -3098 | 0.97 | 2789 |
| spread fijo 4.0 | 504 | 3229 | 1.08 | 37.5 | 6.4 | -3242 | 0.79 | 2260 |
| spread fijo 6.0 | 504 | 2221 | 1.05 | 37.5 | 4.4 | -3557 | 0.54 | 1554 |
| max_spread 4 | 504 | 4237 | 1.1 | 37.5 | 8.4 | -3050 | 1.03 | 2966 |
| comision 3.5/lado/lote | 504 | 4237 | 1.1 | 37.5 | 8.4 | -3050 | 1.03 | 2613 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~492 trades cada una (el bot: 504).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 8.4 | 4.5 | -3.5 | 10.4 | 82% |
| profit factor | 1.1 | 1.05 | 0.96 | 1.13 | 82% |
| ganancia media/trade OOS | 25.8 | 21.2 | -1.9 | 40.5 | 72% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +1874 pips en todo el periodo; +1991 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -3217, p95 -4985, p99 -6007 pips (historico -3050) |
| bootstrap periodo completo | P(neto<0) 15.0%, neto p5/p50/p95 -2602/4211/11123, maxDD p95 -6265 |
| bootstrap solo OOS | P(neto<0) 9.8% con 86 trades |
| horizonte 1 anio(s) (~26 trades) | P(perder) 44.6%, p5 -1198, p50 286 pips |
| horizonte 2 anio(s) (~51 trades) | P(perder) 36.2%, p5 -1734, p50 419 pips |
| horizonte 3 anio(s) (~77 trades) | P(perder) 34.6%, p5 -1924, p50 631 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.01, p50 1.09; P(neto<0) 3.9% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 6007 pips = 420 por 0.01 lotes, 4205 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| fi_period | 15 | 545 | -130 | 1.0 | 1.32 |
| fi_period | 18 | 516 | 582 | 1.01 | 1.16 |
| fi_period | 20 | 504 | 4654 | 1.11 | 1.3 |
| fi_period | 22 | 504 | 4237 | 1.1 | 1.34 |
| fi_period | 24 | 474 | 2326 | 1.06 | 1.28 |
| fi_period | 26 | 474 | 2878 | 1.07 | 1.38 |
| fi_period | 29 | 441 | 1550 | 1.04 | 1.27 |
| trend_ema_period | 70 | 516 | 4158 | 1.1 | 1.23 |
| trend_ema_period | 80 | 505 | 5170 | 1.12 | 1.33 |
| trend_ema_period | 90 | 507 | 4901 | 1.12 | 1.37 |
| trend_ema_period | 100 | 504 | 4237 | 1.1 | 1.34 |
| trend_ema_period | 110 | 502 | 2266 | 1.05 | 1.26 |
| trend_ema_period | 120 | 492 | 2354 | 1.06 | 1.24 |
| trend_ema_period | 130 | 491 | 2116 | 1.05 | 1.22 |
| stop_loss_pips | 89 | 589 | 2478 | 1.06 | 1.18 |
| stop_loss_pips | 102 | 551 | 4858 | 1.12 | 1.23 |
| stop_loss_pips | 114 | 525 | 4664 | 1.11 | 1.31 |
| stop_loss_pips | 127 | 504 | 4237 | 1.1 | 1.34 |
| stop_loss_pips | 140 | 476 | 5485 | 1.13 | 1.46 |
| stop_loss_pips | 152 | 455 | 6218 | 1.15 | 1.49 |
| stop_loss_pips | 165 | 441 | 5229 | 1.12 | 1.44 |
| take_profit_pips | 170 | 641 | 2296 | 1.05 | 1.3 |
| take_profit_pips | 194 | 602 | 2142 | 1.05 | 1.31 |
| take_profit_pips | 219 | 547 | 3931 | 1.09 | 1.27 |
| take_profit_pips | 243 | 504 | 4237 | 1.1 | 1.34 |
| take_profit_pips | 267 | 470 | 3254 | 1.08 | 1.44 |
| take_profit_pips | 292 | 441 | 3029 | 1.08 | 1.44 |
| take_profit_pips | 316 | 418 | 3246 | 1.09 | 1.43 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 142/150, PF mediana 1.07, p5 1.00; OOS PF>1 en 150/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 122 | 182 | 243 | 304 | 389 |
|---|---|---|---|---|---|
| 76.0 | 0.99 | 1.07 | 1.03 | 1.08 | 1.14 |
| 102.0 | 1.02 | 1.08 | 1.12 | 1.14 | 1.17 |
| 127.0 | 1.03 | 1.05 | 1.1 | 1.09 | 1.15 |
| 152.0 | 1.04 | 1.09 | 1.15 | 1.12 | 1.14 |
| 190.0 | 1.02 | 1.07 | 1.12 | 1.06 | 1.06 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 372 | 2990 | 1.07 | -3427 | 1.23 | 1486 |
| v6_no_ao_exit | 372 | 2990 | 1.07 | -3427 | 1.23 | 1486 |
| baseline_fixed_spread | 372 | 2990 | 1.07 | -3427 | 1.23 | 1486 |
| both_dirs | 603 | -5881 | 0.91 | -7929 | 1.1 | 881 |
| commission | 372 | 2990 | 1.07 | -3427 | 1.23 | 1486 |
| v6_eurjpy | 504 | 4237 | 1.1 | -3050 | 1.34 | 2221 |
| v6_audjpy | 653 | 3216 | 1.07 | -3237 | 1.26 | 2016 |
| v6_cadjpy | 687 | 3664 | 1.08 | -3439 | 1.28 | 2145 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params fi_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 16/127/182 | 321 | -1334 | 36 | -683 |
| 2012 | 22/95/182 | 53 | 2256 | 31 | 2323 |
| 2013 | 22/95/316 | 843 | 550 | 29 | 340 |
| 2014 | 22/95/316 | 591 | 49 | 21 | 287 |
| 2015 | 22/95/316 | 687 | -490 | 22 | -618 |
| 2016 | 22/165/182 | 727 | 205 | 24 | -173 |
| 2017 | 22/165/316 | 347 | 263 | 16 | 484 |
| 2018 | 22/165/243 | 314 | -1023 | 11 | -1066 |
| 2019 | 22/165/316 | 31 | -521 | 6 | -550 |
| 2020 | 29/95/243 | 138 | 764 | 20 | 234 |
| 2021 | 29/95/243 | 436 | 470 | 12 | 560 |
| 2022 | 29/95/243 | 125 | -534 | 28 | 332 |
| 2023 | 29/95/182 | 215 | 192 | 38 | 329 |
| 2024 | 22/95/316 | 407 | 1335 | 33 | 1327 |
| 2025 | 22/127/316 | 854 | 1480 | 16 | 1585 |
| 2026 | 22/127/182 | 1130 | -495 | 23 | -365 |

Total OOS walk-forward 3167 pips (base 4346); anios positivos 10/16; eficiencia 0.44 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 232 | 2453.9 | 10.6 |
| D1 > SMA200 | 272 | 1782.9 | 6.6 |

Por dia de entrada: lun 592 (110), mar 2084 (110), mie 1322 (103), jue -1509 (94), vie 1748 (87)

Por hora de entrada (pips): 1h 70, 2h -343, 3h -1453, 4h -52, 5h -639, 6h 458, 7h 1361, 8h 612, 9h -346, 10h -1134, 11h 1737, 12h 794, 13h 1478, 14h 1214, 15h 415, 16h -185, 17h 856, 18h 135, 19h -422, 20h 27, 21h -346

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
