# Informe de robustez: ema100_gbpjpy_h1

- Datos: `CADJPY_H1_syn.csv`, 2007-01-01 07:00:00 a 2023-03-31 17:00:00, 86,956 velas H1
- Spread por vela (pips): mediana nan, p95 nan
- Preset: `v6_cadjpy` | corte IS/OOS: ninguno | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 406 |
| trades_per_year | 25.0 |
| win_rate_% | 36.45 |
| profit_factor | 1.036 |
| expectancy_pips | 2.29 |
| avg_win_pips | 181.7 |
| avg_loss_pips | -100.6 |
| total_pips | 928.5 |
| max_dd_closed_pips | -2003.3 |
| max_dd_float_pips | -2003.3 |
| max_consec_losses | 12 |
| avg_hold_hours | 167.1 |
| exit_mix | {"SL": 229, "TP": 132, "SL_gap": 29, "TP_gap": 15, "END": 1} |
| exposure_% | 49.0 |
| cagr_% | 0.39 |

t-stat de la media por trade: **0.34** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **2832 dias**

Por anio (pips): 2007: 817, 2008: -990, 2009: 198, 2010: -230, 2011: -501, 2012: 996, 2013: 960, 2014: 656, 2015: -115, 2016: 232, 2017: -559, 2018: 37, 2019: -452, 2020: 72, 2021: 373, 2022: -301, 2023: -264

Anios negativos: 8 de 17

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 406 | 928 | 1.04 | 36.5 | 2.3 | -2003 | 0.34 | 650 |
| spread fijo 2.5 | 406 | 928 | 1.04 | 36.5 | 2.3 | -2003 | 0.34 | 650 |
| spread fijo 4.0 | 406 | 319 | 1.01 | 36.5 | 0.8 | -2197 | 0.12 | 224 |
| spread fijo 6.0 | 406 | -493 | 0.98 | 36.5 | -1.2 | -2455 | -0.18 | -345 |
| max_spread 4 | 406 | 928 | 1.04 | 36.5 | 2.3 | -2003 | 0.34 | 650 |
| comision 3.5/lado/lote | 406 | 928 | 1.04 | 36.5 | 2.3 | -2003 | 0.34 | 366 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~393 trades cada una (el bot: 406).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 2.3 | 4.4 | -3.2 | 10.0 | 33% |
| profit factor | 1.04 | 1.07 | 0.95 | 1.16 | 37% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: -380 pips en todo el periodo

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -2608, p95 -4002, p99 -4743 pips (historico -2003) |
| bootstrap periodo completo | P(neto<0) 36.4%, neto p5/p50/p95 -3488/996/5564, maxDD p95 -5271 |
| horizonte 1 anio(s) (~25 trades) | P(perder) 44.8%, p5 -1077, p50 40 pips |
| horizonte 2 anio(s) (~50 trades) | P(perder) 44.7%, p5 -1439, p50 89 pips |
| horizonte 3 anio(s) (~75 trades) | P(perder) 44.6%, p5 -1786, p50 138 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 0.94, p50 1.02; P(neto<0) 35.6% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 4743 pips = 332 por 0.01 lotes, 3320 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| fi_period | 15 | 460 | 321 | 1.01 |  |
| fi_period | 18 | 432 | 1519 | 1.06 |  |
| fi_period | 20 | 417 | 646 | 1.02 |  |
| fi_period | 22 | 406 | 928 | 1.04 |  |
| fi_period | 24 | 393 | 662 | 1.03 |  |
| fi_period | 26 | 386 | 3386 | 1.14 |  |
| fi_period | 29 | 360 | 345 | 1.01 |  |
| trend_ema_period | 70 | 420 | 2301 | 1.09 |  |
| trend_ema_period | 80 | 411 | 1787 | 1.07 |  |
| trend_ema_period | 90 | 409 | 564 | 1.02 |  |
| trend_ema_period | 100 | 406 | 928 | 1.04 |  |
| trend_ema_period | 110 | 402 | 1065 | 1.04 |  |
| trend_ema_period | 120 | 405 | 1031 | 1.04 |  |
| trend_ema_period | 130 | 398 | 1720 | 1.07 |  |
| stop_loss_pips | 67 | 466 | 1922 | 1.08 |  |
| stop_loss_pips | 77 | 443 | 1607 | 1.07 |  |
| stop_loss_pips | 86 | 428 | 1151 | 1.05 |  |
| stop_loss_pips | 96 | 406 | 928 | 1.04 |  |
| stop_loss_pips | 106 | 393 | 510 | 1.02 |  |
| stop_loss_pips | 115 | 387 | -378 | 0.99 |  |
| stop_loss_pips | 125 | 374 | -430 | 0.98 |  |
| take_profit_pips | 128 | 494 | 178 | 1.01 |  |
| take_profit_pips | 146 | 456 | 1001 | 1.04 |  |
| take_profit_pips | 165 | 433 | 307 | 1.01 |  |
| take_profit_pips | 183 | 406 | 928 | 1.04 |  |
| take_profit_pips | 201 | 389 | 780 | 1.03 |  |
| take_profit_pips | 220 | 380 | 403 | 1.02 |  |
| take_profit_pips | 238 | 362 | -806 | 0.97 |  |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 132/150, PF mediana 1.06, p5 0.99

PF por SL (filas) x TP (columnas):

| SL \ TP | 92 | 137 | 183 | 229 | 293 |
|---|---|---|---|---|---|
| 58.0 | 1.0 | 1.11 | 1.1 | 1.11 | 1.09 |
| 77.0 | 0.96 | 1.07 | 1.07 | 1.05 | 1.04 |
| 96.0 | 0.96 | 1.02 | 1.04 | 0.99 | 0.96 |
| 115.0 | 0.94 | 1.01 | 0.99 | 0.97 | 0.97 |
| 144.0 | 0.9 | 0.94 | 0.97 | 0.95 | 0.94 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 225 | -441 | 0.98 | -3270 |  |  |
| v6_no_ao_exit | 225 | -441 | 0.98 | -3270 |  |  |
| baseline_fixed_spread | 225 | -441 | 0.98 | -3270 |  |  |
| both_dirs | 338 | -726 | 0.98 | -4959 |  |  |
| commission | 225 | -441 | 0.98 | -3270 |  |  |
| v6_eurjpy | 310 | -400 | 0.98 | -2595 |  |  |
| v6_audjpy | 391 | 735 | 1.03 | -2262 |  |  |
| v6_cadjpy | 406 | 928 | 1.04 | -2003 |  |  |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params fi_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 16/72/137 | 310 | -398 | 39 | -501 |
| 2012 | 16/72/137 | -229 | 821 | 31 | 996 |
| 2013 | 29/125/238 | 182 | 474 | 19 | 960 |
| 2014 | 22/72/238 | 519 | 854 | 15 | 656 |
| 2015 | 22/72/238 | 734 | -594 | 19 | -115 |
| 2016 | 22/96/183 | 624 | 232 | 31 | 232 |
| 2017 | 22/96/183 | 433 | -559 | 20 | -559 |
| 2018 | 29/96/183 | 153 | -204 | 16 | 37 |
| 2019 | 22/72/137 | 7 | -5 | 17 | -452 |
| 2020 | 16/72/238 | 137 | -26 | 17 | 72 |
| 2021 | 16/72/137 | 38 | -58 | 27 | 373 |
| 2022 | 22/72/137 | 137 | -684 | 48 | -301 |
| 2023 | 16/125/238 | 234 | -638 | 5 | -264 |

Total OOS walk-forward -785 pips (base 1134); anios positivos 4/13; eficiencia -0.24 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 200 | -1432.5 | -7.2 |
| D1 > SMA200 | 206 | 2361.0 | 11.5 |

Por dia de entrada: lun -136 (103), mar 816 (73), mie 172 (77), jue 647 (85), vie -571 (68)

Por hora de entrada (pips): 1h -632, 2h -114, 3h 203, 4h 27, 5h 204, 6h -115, 7h 532, 8h 609, 9h -3, 10h 597, 11h 127, 12h 823, 13h -860, 14h -684, 15h 491, 16h -221, 17h -333, 18h -8, 19h -230, 20h 131, 21h 384

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
