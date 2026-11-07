# Informe de robustez: mq4_gbpjpy_h4

- Datos: `GBPJPY_H1.csv`, 2006-01-02 00:00:00 a 2026-10-30 23:00:00, 130,031 velas H1
- Spread por vela (pips): mediana 2.00, p95 7.50
- Preset: `baseline` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 1044 |
| trades_per_year | 50.2 |
| win_rate_% | 25.67 |
| profit_factor | 1.149 |
| expectancy_pips | 7.7 |
| avg_win_pips | 231.2 |
| avg_loss_pips | -69.5 |
| total_pips | 8041.4 |
| max_dd_closed_pips | -3720.0 |
| max_dd_float_pips | -3895.8 |
| max_consec_losses | 24 |
| avg_hold_hours | 58.1 |
| exit_mix | {"SL": 719, "SIGNAL": 237, "TP": 79, "SL_gap": 6, "TP_gap": 3} |
| exposure_% | 32.6 |
| cagr_% | 0.26 |

t-stat de la media por trade: **1.53** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **2287 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 924 | 9090 | 1.19 | 26.3 | 9.8 | -3720 | 1.83 |
| OOS (desde el corte) | 120 | -1048 | 0.85 | 20.8 | -8.7 | -2541 | -0.63 |

Por anio (pips): 2006: -795, 2007: -543, 2008: 164, 2009: 2225, 2010: -1625, 2011: -750, 2012: 297, 2013: -269, 2014: 604, 2015: 1391, 2016: 4469, 2017: 876, 2018: 538, 2019: 1673, 2020: 631, 2021: 26, 2022: 412, 2023: -540, 2024: 1029, 2025: -1168, 2026: -601

Anios negativos: 8 de 21

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 1044 | 8041 | 1.15 | 25.7 | 7.7 | -3720 | 1.53 | 563 |
| spread fijo 2.5 | 1044 | 9913 | 1.19 | 26.0 | 9.5 | -3633 | 1.89 | 691 |
| spread fijo 4.0 | 1044 | 8347 | 1.16 | 25.5 | 8.0 | -4012 | 1.59 | 584 |
| spread fijo 6.0 | 1044 | 6259 | 1.11 | 25.3 | 6.0 | -4536 | 1.19 | 438 |
| max_spread 4 | 860 | 9108 | 1.22 | 27.0 | 10.6 | -3781 | 1.94 | 637 |
| comision 3.5/lado/lote | 1044 | 8041 | 1.15 | 25.7 | 7.7 | -3720 | 1.53 | 490 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~1031 trades cada una (el bot: 1044).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 7.7 | -3.2 | -8.5 | 3.4 | 98% |
| profit factor | 1.15 | 0.93 | 0.81 | 1.08 | 98% |
| ganancia media/trade OOS | -8.7 | -8.0 | -18.9 | 3.5 | 47% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +810 pips en todo el periodo; +2862 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -3464, p95 -5444, p99 -6484 pips (historico -3720) |
| bootstrap periodo completo | P(neto<0) 6.3%, neto p5/p50/p95 -600/8029/16915, maxDD p95 -6602 |
| bootstrap solo OOS | P(neto<0) 74.4% con 120 trades |
| horizonte 1 anio(s) (~50 trades) | P(perder) 38.3%, p5 -1406, p50 346 pips |
| horizonte 2 anio(s) (~101 trades) | P(perder) 32.7%, p5 -1818, p50 727 pips |
| horizonte 3 anio(s) (~151 trades) | P(perder) 29.7%, p5 -2067, p50 1071 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.04, p50 1.13; P(neto<0) 0.5% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 6484 pips = 454 por 0.01 lotes, 4539 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| env_period | 24.0 | 1016 | 6260 | 1.12 | 0.81 |
| env_period | 27.0 | 1038 | 6828 | 1.12 | 0.77 |
| env_period | 31.0 | 1039 | 7068 | 1.13 | 0.8 |
| env_period | 34.0 | 1044 | 8041 | 1.15 | 0.85 |
| env_period | 37.0 | 1051 | 8046 | 1.15 | 0.88 |
| env_period | 41.0 | 1038 | 11952 | 1.23 | 0.94 |
| env_period | 44.0 | 1048 | 11058 | 1.21 | 0.95 |
| env_deviation | 0.609 | 1367 | 7690 | 1.11 | 0.93 |
| env_deviation | 0.696 | 1256 | 9721 | 1.15 | 0.94 |
| env_deviation | 0.783 | 1122 | 12128 | 1.22 | 0.99 |
| env_deviation | 0.87 | 1044 | 8041 | 1.15 | 0.85 |
| env_deviation | 0.957 | 950 | 8838 | 1.18 | 0.84 |
| env_deviation | 1.044 | 877 | 6743 | 1.14 | 0.95 |
| env_deviation | 1.131 | 803 | 4972 | 1.11 | 1.04 |
| bulls_period | 16.0 | 1087 | 4905 | 1.09 | 0.63 |
| bulls_period | 18.0 | 1083 | 6061 | 1.11 | 0.68 |
| bulls_period | 21.0 | 1056 | 6961 | 1.13 | 0.77 |
| bulls_period | 23.0 | 1044 | 8041 | 1.15 | 0.85 |
| bulls_period | 25.0 | 1038 | 8893 | 1.16 | 0.9 |
| bulls_period | 28.0 | 1020 | 9081 | 1.17 | 0.87 |
| bulls_period | 30.0 | 1015 | 8897 | 1.17 | 0.88 |
| stop_loss_pips | 48.0 | 1137 | 5502 | 1.12 | 0.87 |
| stop_loss_pips | 54.0 | 1107 | 9075 | 1.18 | 0.88 |
| stop_loss_pips | 61.0 | 1069 | 8612 | 1.17 | 0.85 |
| stop_loss_pips | 68.0 | 1044 | 8041 | 1.15 | 0.85 |
| stop_loss_pips | 75.0 | 1013 | 6838 | 1.12 | 0.81 |
| stop_loss_pips | 82.0 | 988 | 6058 | 1.11 | 0.78 |
| stop_loss_pips | 88.0 | 969 | 6768 | 1.12 | 0.75 |
| take_profit_pips | 340.0 | 1086 | 4789 | 1.09 | 0.68 |
| take_profit_pips | 389.0 | 1074 | 5722 | 1.1 | 0.76 |
| take_profit_pips | 437.0 | 1058 | 8018 | 1.15 | 0.82 |
| take_profit_pips | 486.0 | 1044 | 8041 | 1.15 | 0.85 |
| take_profit_pips | 535.0 | 1031 | 5932 | 1.11 | 0.72 |
| take_profit_pips | 583.0 | 1027 | 7087 | 1.13 | 0.75 |
| take_profit_pips | 632.0 | 1025 | 7408 | 1.14 | 0.69 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 150/150, PF mediana 1.15, p5 1.08; OOS PF>1 en 19/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 243 | 364 | 486 | 608 | 778 |
|---|---|---|---|---|---|
| 41.0 | 0.99 | 1.11 | 1.15 | 1.11 | 1.09 |
| 54.0 | 1.04 | 1.12 | 1.18 | 1.15 | 1.12 |
| 68.0 | 1.03 | 1.08 | 1.15 | 1.12 | 1.09 |
| 82.0 | 1.02 | 1.05 | 1.11 | 1.09 | 1.08 |
| 102.0 | 1.01 | 1.02 | 1.1 | 1.07 | 1.06 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 1044 | 8041 | 1.15 | -3720 | 0.85 | -1048 |
| baseline_fixed_spread | 1044 | 9913 | 1.19 | -3633 | 0.94 | -375 |
| buy_only | 471 | 8482 | 1.34 | -1924 | 0.74 | -856 |
| sell_only | 591 | -1623 | 0.95 | -4712 | 0.89 | -403 |
| no_signal_exit | 898 | 9565 | 1.17 | -3708 | 0.73 | -1854 |
| commission | 1044 | 8041 | 1.15 | -3720 | 0.85 | -1048 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params env_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2010 | 26/68/632 | 1072 | -1592 | 75 | -1625 |
| 2011 | 26/68/632 | 912 | 563 | 56 | -750 |
| 2012 | 26/51/632 | 652 | 485 | 39 | 297 |
| 2013 | 26/51/364 | 810 | -465 | 56 | -269 |
| 2014 | 26/51/632 | 97 | 349 | 31 | 604 |
| 2015 | 26/51/632 | 402 | 1211 | 41 | 1391 |
| 2016 | 44/51/486 | 878 | 5567 | 57 | 4469 |
| 2017 | 44/68/632 | 2188 | 724 | 42 | 876 |
| 2018 | 44/68/632 | 2409 | -449 | 46 | 538 |
| 2019 | 44/68/632 | 2195 | 379 | 35 | 1673 |
| 2020 | 44/68/632 | 1941 | -273 | 46 | 631 |
| 2021 | 34/51/486 | 981 | -90 | 32 | 26 |
| 2022 | 34/68/486 | 717 | 412 | 62 | 412 |
| 2023 | 26/88/486 | 946 | -478 | 40 | -540 |
| 2024 | 26/88/486 | 481 | 1140 | 41 | 1029 |
| 2025 | 44/88/486 | 724 | -1947 | 41 | -1168 |
| 2026 | 26/88/486 | 429 | -602 | 18 | -601 |

Total OOS walk-forward 4934 pips (base 6993); anios positivos 9/17; eficiencia 0.28 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 562 | 4643.6 | 8.3 |
| D1 > SMA200 | 482 | 3397.8 | 7.0 |

Por dia de entrada: lun 1765 (214), mar 1582 (197), mie -194 (197), jue 7069 (227), vie -2180 (209)

Por hora de entrada (pips): 0h 245, 4h 490, 8h -129, 12h 2488, 16h 3549, 20h 1399

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
