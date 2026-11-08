# Informe de robustez: mq4_eurusd_h1

- Datos: `EURUSD_H1.csv`, 2007-01-01 07:00:00 a 2026-10-30 23:00:00, 120,657 velas H1
- Spread por vela (pips): mediana 0.50, p95 1.70
- Preset: `r2c` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 101 |
| trades_per_year | 5.1 |
| win_rate_% | 65.35 |
| profit_factor | 1.748 |
| expectancy_pips | 98.89 |
| avg_win_pips | 353.7 |
| avg_loss_pips | -381.6 |
| total_pips | 9987.9 |
| max_dd_closed_pips | -2103.5 |
| max_dd_float_pips | -2680.7 |
| max_consec_losses | 4 |
| avg_hold_hours | 1157.6 |
| exit_mix | {"TP": 63, "SL": 34, "TP_gap": 3, "SL_gap": 1} |
| exposure_% | 67.7 |
| cagr_% | 3.56 |

t-stat de la media por trade: **2.51** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **1439 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 80 | 9947 | 1.91 | 70.0 | 124.3 | -2103 | 2.63 |
| OOS (desde el corte) | 21 | 40 | 1.02 | 47.6 | 1.9 | -1344 | 0.04 |

Por anio (pips): 2007: 666, 2008: 1324, 2009: 122, 2010: 326, 2011: 1457, 2012: 853, 2013: 852, 2014: 1088, 2015: 149, 2016: 576, 2017: 176, 2018: 846, 2019: 645, 2020: 24, 2021: 336, 2022: 590, 2023: -93, 2024: -1077, 2025: 709, 2026: 421

Anios negativos: 2 de 20

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 101 | 9988 | 1.75 | 65.3 | 98.9 | -2103 | 2.51 | 9988 |
| spread fijo 2.5 | 101 | 9836 | 1.73 | 65.3 | 97.4 | -2106 | 2.48 | 9836 |
| spread fijo 4.0 | 101 | 9685 | 1.72 | 65.3 | 95.9 | -2109 | 2.44 | 9685 |
| spread fijo 6.0 | 101 | 9483 | 1.7 | 65.3 | 93.9 | -2113 | 2.39 | 9483 |
| max_spread 4 | 101 | 9988 | 1.75 | 65.3 | 98.9 | -2103 | 2.51 | 9988 |
| comision 3.5/lado/lote | 101 | 9988 | 1.75 | 65.3 | 98.9 | -2103 | 2.51 | 9917 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~104 trades cada una (el bot: 101).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 98.9 | 26.9 | -2.6 | 61.2 | 100% |
| profit factor | 1.75 | 1.16 | 0.99 | 1.4 | 100% |
| ganancia media/trade OOS | 1.9 | -26.7 | -74.8 | 31.5 | 80% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: -2038 pips en todo el periodo; +190 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -2171, p95 -3482, p99 -4262 pips (historico -2103) |
| bootstrap periodo completo | P(neto<0) 0.7%, neto p5/p50/p95 3507/10059/16430, maxDD p95 -4080 |
| bootstrap solo OOS | P(neto<0) 48.6% con 21 trades |
| horizonte 1 anio(s) (~5 trades) | P(perder) 27.2%, p5 -1011, p50 547 pips |
| horizonte 2 anio(s) (~11 trades) | P(perder) 19.7%, p5 -1114, p50 1130 pips |
| horizonte 3 anio(s) (~16 trades) | P(perder) 15.7%, p5 -1096, p50 1633 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.44, p50 1.72; P(neto<0) 0.0% |

Guia de tamano (pip_value_per_lot=10.0): maxDD p99 de reordenar = 4262 pips = 426 por 0.01 lotes, 4262 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| wpr_period | 22.0 | 101 | 3152 | 1.18 | 0.91 |
| wpr_period | 25.0 | 109 | 6583 | 1.38 | 0.71 |
| wpr_period | 28.0 | 106 | 7783 | 1.49 | 1.04 |
| wpr_period | 31.0 | 101 | 9988 | 1.75 | 1.02 |
| wpr_period | 34.0 | 106 | 6992 | 1.44 | 0.84 |
| wpr_period | 37.0 | 106 | 5793 | 1.35 | 0.82 |
| wpr_period | 40.0 | 102 | 6996 | 1.44 | 0.98 |
| wpr_level | -16.8 | 107 | 1362 | 1.07 | 0.67 |
| wpr_level | -19.2 | 94 | 2246 | 1.14 | 0.91 |
| wpr_level | -21.6 | 90 | 6263 | 1.45 | 0.78 |
| wpr_level | -24.0 | 101 | 9988 | 1.75 | 1.02 |
| wpr_level | -26.4 | 107 | 6365 | 1.39 | 1.16 |
| wpr_level | -28.8 | 108 | 2610 | 1.14 | 0.78 |
| wpr_level | -31.2 | 111 | 3077 | 1.16 | 0.91 |
| stoch_k | 2.0 | 106 | 9135 | 1.65 | 0.89 |
| stoch_k | 2.0 | 106 | 9135 | 1.65 | 0.89 |
| stoch_k | 3.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_k | 3.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_k | 3.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_k | 4.0 | 103 | 7452 | 1.5 | 0.92 |
| stoch_k | 4.0 | 103 | 7452 | 1.5 | 0.92 |
| stoch_slowing | 1.0 | 96 | 3505 | 1.22 | 0.66 |
| stoch_slowing | 2.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_slowing | 2.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_slowing | 2.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_slowing | 2.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_slowing | 2.0 | 101 | 9988 | 1.75 | 1.02 |
| stoch_slowing | 3.0 | 97 | 3381 | 1.21 | 0.82 |
| teeth_period | 4.0 | 98 | 10913 | 1.86 | 1.16 |
| teeth_period | 5.0 | 101 | 10514 | 1.79 | 1.18 |
| teeth_period | 5.0 | 101 | 10514 | 1.79 | 1.18 |
| teeth_period | 6.0 | 101 | 9988 | 1.75 | 1.02 |
| teeth_period | 7.0 | 110 | 8444 | 1.55 | 0.89 |
| teeth_period | 7.0 | 110 | 8444 | 1.55 | 0.89 |
| teeth_period | 8.0 | 111 | 8039 | 1.52 | 1.02 |
| teeth_shift | 4.0 | 103 | 8260 | 1.55 | 1.01 |
| teeth_shift | 4.0 | 103 | 8260 | 1.55 | 1.01 |
| teeth_shift | 4.0 | 103 | 8260 | 1.55 | 1.01 |
| teeth_shift | 5.0 | 101 | 9988 | 1.75 | 1.02 |
| teeth_shift | 6.0 | 104 | 9061 | 1.61 | 1.39 |
| teeth_shift | 6.0 | 104 | 9061 | 1.61 | 1.39 |
| teeth_shift | 6.0 | 104 | 9061 | 1.61 | 1.39 |
| rvi_period | 10.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 11.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 13.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 14.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 15.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 17.0 | 101 | 9988 | 1.75 | 1.02 |
| rvi_period | 18.0 | 101 | 9988 | 1.75 | 1.02 |
| sl_atr_mult | 2.4066 | 128 | 6964 | 1.43 | 0.97 |
| sl_atr_mult | 2.7504 | 121 | 6525 | 1.4 | 0.89 |
| sl_atr_mult | 3.0942 | 112 | 8302 | 1.55 | 1.01 |
| sl_atr_mult | 3.438 | 101 | 9988 | 1.75 | 1.02 |
| sl_atr_mult | 3.7818 | 95 | 7464 | 1.5 | 0.83 |
| sl_atr_mult | 4.1256 | 90 | 7910 | 1.56 | 1.29 |
| sl_atr_mult | 4.4694 | 87 | 5697 | 1.36 | 1.39 |
| tp_atr_mult | 2.4367 | 137 | 5494 | 1.32 | 1.15 |
| tp_atr_mult | 2.7848 | 122 | 4571 | 1.27 | 0.89 |
| tp_atr_mult | 3.1329 | 107 | 8166 | 1.58 | 0.91 |
| tp_atr_mult | 3.481 | 101 | 9988 | 1.75 | 1.02 |
| tp_atr_mult | 3.8291 | 91 | 7694 | 1.56 | 0.91 |
| tp_atr_mult | 4.1772 | 80 | 5892 | 1.43 | 0.91 |
| tp_atr_mult | 4.5253 | 76 | 5064 | 1.36 | 0.73 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 145/150, PF mediana 1.25, p5 1.04; OOS PF>1 en 60/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 1.74 | 2.61 | 3.48 | 4.35 | 5.57 |
|---|---|---|---|---|---|
| 2.06 | 1.17 | 1.06 | 1.32 | 1.31 | 1.19 |
| 2.75 | 1.28 | 1.25 | 1.39 | 1.38 | 1.15 |
| 3.44 | 1.24 | 1.29 | 1.74 | 1.45 | 1.44 |
| 4.13 | 1.28 | 1.37 | 1.55 | 1.43 | 1.25 |
| 5.16 | 1.11 | 1.15 | 1.23 | 1.15 | 0.79 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |
| baseline_fixed_spread | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |
| buy_only | 352 | -900 | 0.83 | -1013 | 0.62 | -344 |
| sell_only | 389 | -358 | 0.93 | -936 | 0.85 | -109 |
| no_session | 799 | -1667 | 0.84 | -2142 | 0.7 | -512 |
| commission | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |
| r2c | 101 | 9988 | 1.75 | -2103 | 1.02 | 40 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params wpr_period/sl_atr_mult/tp_atr_mult | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 40/2.58/4.53 | 894 | -474 | 4 | 1457 |
| 2012 | 40/2.58/2.61 | 884 | 303 | 8 | 853 |
| 2013 | 40/2.58/2.61 | 854 | 590 | 8 | 852 |
| 2014 | 31/3.44/3.48 | 872 | 1088 | 6 | 1088 |
| 2015 | 31/3.44/3.48 | 1062 | 149 | 5 | 149 |
| 2016 | 40/3.44/4.53 | 744 | -724 | 2 | 576 |
| 2017 | 31/3.44/3.48 | 666 | 176 | 3 | 176 |
| 2018 | 40/3.44/3.48 | 531 | 552 | 4 | 846 |
| 2019 | 31/3.44/3.48 | 437 | 645 | 3 | 645 |
| 2020 | 31/3.44/3.48 | 561 | 24 | 5 | 24 |
| 2021 | 23/2.58/4.53 | 582 | -308 | 4 | 336 |
| 2022 | 31/3.44/3.48 | 463 | 590 | 6 | 590 |
| 2023 | 23/3.44/3.48 | 487 | -647 | 8 | -93 |
| 2024 | 31/2.58/4.53 | 517 | -981 | 9 | -1077 |
| 2025 | 40/4.47/4.53 | 318 | 464 | 3 | 709 |
| 2026 | 40/4.47/4.53 | 373 | 655 | 2 | 421 |

Total OOS walk-forward 2102 pips (base 7552); anios positivos 11/16; eficiencia 0.21 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 49 | 4772.5 | 97.4 |
| D1 > SMA200 | 52 | 5215.4 | 100.3 |

Por dia de entrada: lun -702 (16), mar 4085 (21), mie 4959 (25), jue 729 (15), vie 916 (24)

Por hora de entrada (pips): 3h -345, 4h -259, 5h 467, 6h 639, 7h -596, 8h 425, 9h -500, 10h -1162, 11h -1140, 12h -456, 13h 796, 14h 487, 15h 100, 16h 1764, 17h 3180, 18h 3261, 19h -807, 20h 735, 21h 628, 22h 2769

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
