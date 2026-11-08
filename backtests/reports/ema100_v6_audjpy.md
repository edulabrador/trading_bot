# Informe de robustez: ema100_gbpjpy_h1

- Datos: `AUDJPY_H1_syn.csv`, 2007-01-01 07:00:00 a 2023-03-29 06:00:00, 85,679 velas H1
- Spread por vela (pips): mediana nan, p95 nan
- Preset: `v6_audjpy` | corte IS/OOS: ninguno | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 395 |
| trades_per_year | 24.3 |
| win_rate_% | 37.47 |
| profit_factor | 1.093 |
| expectancy_pips | 6.1 |
| avg_win_pips | 191.9 |
| avg_loss_pips | -105.2 |
| total_pips | 2409.6 |
| max_dd_closed_pips | -2028.9 |
| max_dd_float_pips | -2094.0 |
| max_consec_losses | 11 |
| avg_hold_hours | 179.2 |
| exit_mix | {"SL": 227, "TP": 140, "SL_gap": 20, "TP_gap": 8} |
| exposure_% | 50.8 |
| cagr_% | 0.97 |

t-stat de la media por trade: **0.84** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **3271 dias**

Por anio (pips): 2007: 910, 2008: 680, 2009: -18, 2010: 520, 2011: 159, 2012: 540, 2013: -349, 2014: 598, 2015: -414, 2016: -333, 2017: 578, 2018: -672, 2019: -355, 2020: 468, 2021: 584, 2022: 29, 2023: -515

Anios negativos: 7 de 17

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 395 | 2410 | 1.09 | 37.5 | 6.1 | -2029 | 0.84 | 1687 |
| spread fijo 2.5 | 395 | 2212 | 1.08 | 37.5 | 5.6 | -2098 | 0.77 | 1549 |
| spread fijo 4.0 | 395 | 1620 | 1.06 | 37.5 | 4.1 | -2307 | 0.56 | 1134 |
| spread fijo 6.0 | 395 | 830 | 1.03 | 37.5 | 2.1 | -2585 | 0.29 | 581 |
| max_spread 4 | 395 | 2410 | 1.09 | 37.5 | 6.1 | -2029 | 0.84 | 1687 |
| comision 3.5/lado/lote | 395 | 2410 | 1.09 | 37.5 | 6.1 | -2029 | 0.84 | 1410 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~382 trades cada una (el bot: 395).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 6.1 | 5.0 | -0.7 | 12.5 | 60% |
| profit factor | 1.09 | 1.08 | 0.99 | 1.19 | 58% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: -575 pips en todo el periodo

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -2319, p95 -3620, p99 -4280 pips (historico -2029) |
| bootstrap periodo completo | P(neto<0) 20.1%, neto p5/p50/p95 -2336/2396/7165, maxDD p95 -4727 |
| horizonte 1 anio(s) (~25 trades) | P(perder) 40.1%, p5 -1098, p50 73 pips |
| horizonte 2 anio(s) (~49 trades) | P(perder) 40.6%, p5 -1308, p50 245 pips |
| horizonte 3 anio(s) (~74 trades) | P(perder) 36.9%, p5 -1569, p50 446 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 0.99, p50 1.08; P(neto<0) 8.3% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 4280 pips = 300 por 0.01 lotes, 2996 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| fi_period | 15 | 443 | 2353 | 1.08 |  |
| fi_period | 18 | 411 | 2825 | 1.1 |  |
| fi_period | 20 | 401 | 1976 | 1.07 |  |
| fi_period | 22 | 395 | 2410 | 1.09 |  |
| fi_period | 24 | 395 | 802 | 1.03 |  |
| fi_period | 26 | 383 | -352 | 0.99 |  |
| fi_period | 29 | 378 | -420 | 0.98 |  |
| trend_ema_period | 70 | 406 | 3302 | 1.12 |  |
| trend_ema_period | 80 | 400 | 3347 | 1.13 |  |
| trend_ema_period | 90 | 397 | 2792 | 1.11 |  |
| trend_ema_period | 100 | 395 | 2410 | 1.09 |  |
| trend_ema_period | 110 | 390 | 3849 | 1.15 |  |
| trend_ema_period | 120 | 387 | 3372 | 1.13 |  |
| trend_ema_period | 130 | 389 | 3180 | 1.13 |  |
| stop_loss_pips | 71 | 448 | 3740 | 1.16 |  |
| stop_loss_pips | 81 | 423 | 4398 | 1.19 |  |
| stop_loss_pips | 91 | 410 | 3255 | 1.13 |  |
| stop_loss_pips | 101 | 395 | 2410 | 1.09 |  |
| stop_loss_pips | 111 | 380 | 3189 | 1.12 |  |
| stop_loss_pips | 121 | 365 | 3685 | 1.14 |  |
| stop_loss_pips | 131 | 349 | 3725 | 1.14 |  |
| take_profit_pips | 135 | 482 | 3660 | 1.14 |  |
| take_profit_pips | 154 | 451 | 2898 | 1.11 |  |
| take_profit_pips | 174 | 416 | 3146 | 1.12 |  |
| take_profit_pips | 193 | 395 | 2410 | 1.09 |  |
| take_profit_pips | 212 | 366 | 1824 | 1.07 |  |
| take_profit_pips | 232 | 345 | 1615 | 1.07 |  |
| take_profit_pips | 251 | 328 | 2021 | 1.09 |  |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 143/150, PF mediana 1.09, p5 1.01

PF por SL (filas) x TP (columnas):

| SL \ TP | 96 | 145 | 193 | 241 | 309 |
|---|---|---|---|---|---|
| 61.0 | 1.24 | 1.26 | 1.22 | 1.15 | 1.18 |
| 81.0 | 1.22 | 1.24 | 1.19 | 1.16 | 1.18 |
| 101.0 | 1.15 | 1.14 | 1.09 | 1.07 | 1.08 |
| 121.0 | 1.15 | 1.16 | 1.14 | 1.09 | 1.11 |
| 152.0 | 1.09 | 1.15 | 1.13 | 1.08 | 1.12 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 216 | 2767 | 1.12 | -2125 |  |  |
| v6_no_ao_exit | 216 | 2767 | 1.12 | -2125 |  |  |
| baseline_fixed_spread | 216 | 2767 | 1.12 | -2125 |  |  |
| both_dirs | 354 | 424 | 1.01 | -5528 |  |  |
| commission | 216 | 2767 | 1.12 | -2125 |  |  |
| v6_eurjpy | 298 | 1877 | 1.08 | -1935 |  |  |
| v6_audjpy | 395 | 2410 | 1.09 | -2029 |  |  |
| v6_cadjpy | 417 | 3579 | 1.14 | -2132 |  |  |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params fi_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 29/131/145 | 803 | -984 | 24 | 159 |
| 2012 | 16/101/193 | 489 | 501 | 26 | 540 |
| 2013 | 16/131/145 | 530 | -371 | 34 | -349 |
| 2014 | 22/76/251 | 433 | 594 | 14 | 598 |
| 2015 | 22/76/251 | 564 | -649 | 20 | -414 |
| 2016 | 16/131/251 | 451 | -3 | 23 | -333 |
| 2017 | 16/131/251 | 150 | 679 | 12 | 578 |
| 2018 | 16/131/251 | 320 | -583 | 13 | -672 |
| 2019 | 22/76/251 | -45 | 30 | 8 | -355 |
| 2020 | 16/131/145 | 244 | 228 | 19 | 468 |
| 2021 | 29/76/145 | 262 | -103 | 28 | 584 |
| 2022 | 22/131/251 | 190 | 379 | 23 | 29 |
| 2023 | 16/131/193 | 489 | -665 | 5 | -515 |

Total OOS walk-forward -947 pips (base 318); anios positivos 6/13; eficiencia -0.19 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 204 | 776.6 | 3.8 |
| D1 > SMA200 | 191 | 1633.1 | 8.6 |

Por dia de entrada: lun 752 (83), mar 926 (82), mie 125 (66), jue -182 (85), vie 790 (79)

Por hora de entrada (pips): 1h 765, 2h 538, 3h 86, 4h -384, 5h 513, 6h -321, 7h -379, 8h 9, 9h -323, 10h 282, 11h 1086, 12h -90, 13h -971, 14h 588, 15h -532, 16h 1394, 17h 232, 18h 489, 19h 736, 20h -266, 21h -1043

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
