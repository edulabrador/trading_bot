# Informe de robustez: mq4_eurusd_h1

- Datos: `EURUSD_H1.csv`, 2007-01-01 07:00:00 a 2026-10-30 23:00:00, 120,657 velas H1
- Spread por vela (pips): mediana 0.50, p95 1.70
- Preset: `baseline` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 718 |
| trades_per_year | 36.2 |
| win_rate_% | 49.03 |
| profit_factor | 0.904 |
| expectancy_pips | -1.36 |
| avg_win_pips | 26.0 |
| avg_loss_pips | -27.9 |
| total_pips | -974.8 |
| max_dd_closed_pips | -1475.0 |
| max_dd_float_pips | -1549.5 |
| max_consec_losses | 14 |
| avg_hold_hours | 14.5 |
| exit_mix | {"SIGNAL": 718} |
| exposure_% | 6.0 |
| cagr_% | -0.52 |

t-stat de la media por trade: **-0.9** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **5940 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 581 | -654 | 0.92 | 49.2 | -1.1 | -1475 | -0.63 |
| OOS (desde el corte) | 137 | -321 | 0.78 | 48.2 | -2.3 | -522 | -0.94 |

Por anio (pips): 2007: -450, 2008: 354, 2009: 97, 2010: -362, 2011: -471, 2012: -163, 2013: -48, 2014: 233, 2015: -208, 2016: 292, 2017: -9, 2018: 205, 2019: 321, 2020: -82, 2021: 108, 2022: -198, 2023: -88, 2024: -105, 2025: -188, 2026: -213

Anios negativos: 13 de 20

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 718 | -975 | 0.9 | 49.0 | -1.4 | -1475 | -0.9 | -975 |
| spread fijo 2.5 | 718 | -2052 | 0.81 | 45.3 | -2.9 | -2241 | -1.89 | -2052 |
| spread fijo 4.0 | 718 | -3129 | 0.72 | 42.2 | -4.4 | -3130 | -2.88 | -3129 |
| spread fijo 6.0 | 718 | -4565 | 0.62 | 38.9 | -6.4 | -4529 | -4.19 | -4565 |
| max_spread 4 | 718 | -975 | 0.9 | 49.0 | -1.4 | -1475 | -0.9 | -975 |
| comision 3.5/lado/lote | 718 | -975 | 0.9 | 49.0 | -1.4 | -1475 | -0.9 | -1477 |

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~757 trades cada una (el bot: 718).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | -1.4 | -0.4 | -3.0 | 1.0 | 32% |
| profit factor | 0.9 | 0.96 | 0.77 | 1.09 | 33% |
| ganancia media/trade OOS | -2.3 | -0.1 | -3.2 | 3.6 | 10% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: -2038 pips en todo el periodo; +190 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -1632, p95 -2242, p99 -2543 pips (historico -1475) |
| bootstrap periodo completo | P(neto<0) 81.9%, neto p5/p50/p95 -2757/-973/767, maxDD p95 -3149 |
| bootstrap solo OOS | P(neto<0) 82.0% con 137 trades |
| horizonte 1 anio(s) (~36 trades) | P(perder) 57.4%, p5 -451, p50 -45 pips |
| horizonte 2 anio(s) (~73 trades) | P(perder) 61.7%, p5 -673, p50 -104 pips |
| horizonte 3 anio(s) (~109 trades) | P(perder) 63.2%, p5 -853, p50 -141 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 0.76, p50 0.84; P(neto<0) 99.8% |

Guia de tamano (pip_value_per_lot=10.0): maxDD p99 de reordenar = 2543 pips = 254 por 0.01 lotes, 2543 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| wpr_period | 22.0 | 1004 | -2316 | 0.85 | 0.65 |
| wpr_period | 25.0 | 893 | -3140 | 0.78 | 0.57 |
| wpr_period | 28.0 | 812 | -1371 | 0.88 | 0.67 |
| wpr_period | 31.0 | 718 | -975 | 0.9 | 0.78 |
| wpr_period | 34.0 | 698 | -919 | 0.91 | 0.94 |
| wpr_period | 37.0 | 681 | -424 | 0.96 | 0.93 |
| wpr_period | 40.0 | 671 | 8 | 1.0 | 0.91 |
| wpr_level | -16.8 | 646 | -1190 | 0.88 | 0.85 |
| wpr_level | -19.2 | 684 | -1267 | 0.88 | 0.79 |
| wpr_level | -21.6 | 689 | -713 | 0.93 | 0.86 |
| wpr_level | -24.0 | 718 | -975 | 0.9 | 0.78 |
| wpr_level | -26.4 | 743 | -335 | 0.97 | 0.63 |
| wpr_level | -28.8 | 762 | -1306 | 0.88 | 0.98 |
| wpr_level | -31.2 | 818 | -2047 | 0.84 | 0.91 |
| stoch_k | 2.0 | 706 | -1402 | 0.87 | 1.05 |
| stoch_k | 2.0 | 706 | -1402 | 0.87 | 1.05 |
| stoch_k | 3.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_k | 3.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_k | 3.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_k | 4.0 | 656 | -1152 | 0.88 | 0.87 |
| stoch_k | 4.0 | 656 | -1152 | 0.88 | 0.87 |
| stoch_slowing | 1.0 | 572 | -1328 | 0.86 | 0.89 |
| stoch_slowing | 2.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_slowing | 2.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_slowing | 2.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_slowing | 2.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_slowing | 2.0 | 718 | -975 | 0.9 | 0.78 |
| stoch_slowing | 3.0 | 708 | 501 | 1.06 | 0.84 |
| teeth_period | 4.0 | 800 | -546 | 0.95 | 0.87 |
| teeth_period | 5.0 | 761 | -982 | 0.91 | 0.79 |
| teeth_period | 5.0 | 761 | -982 | 0.91 | 0.79 |
| teeth_period | 6.0 | 718 | -975 | 0.9 | 0.78 |
| teeth_period | 7.0 | 694 | -1059 | 0.89 | 0.79 |
| teeth_period | 7.0 | 694 | -1059 | 0.89 | 0.79 |
| teeth_period | 8.0 | 681 | -1333 | 0.86 | 0.75 |
| teeth_shift | 4.0 | 670 | -1345 | 0.87 | 0.7 |
| teeth_shift | 4.0 | 670 | -1345 | 0.87 | 0.7 |
| teeth_shift | 4.0 | 670 | -1345 | 0.87 | 0.7 |
| teeth_shift | 5.0 | 718 | -975 | 0.9 | 0.78 |
| teeth_shift | 6.0 | 719 | -854 | 0.92 | 0.84 |
| teeth_shift | 6.0 | 719 | -854 | 0.92 | 0.84 |
| teeth_shift | 6.0 | 719 | -854 | 0.92 | 0.84 |
| rvi_period | 10.0 | 714 | -1702 | 0.85 | 0.84 |
| rvi_period | 11.0 | 718 | -978 | 0.91 | 0.98 |
| rvi_period | 13.0 | 713 | -825 | 0.92 | 0.79 |
| rvi_period | 14.0 | 718 | -975 | 0.9 | 0.78 |
| rvi_period | 15.0 | 717 | -1837 | 0.83 | 0.91 |
| rvi_period | 17.0 | 717 | -951 | 0.91 | 0.85 |
| rvi_period | 18.0 | 718 | -2059 | 0.81 | 0.86 |
| stop_loss_pips | 227.0 | 718 | -1000 | 0.9 | 0.78 |
| stop_loss_pips | 259.0 | 718 | -1011 | 0.9 | 0.78 |
| stop_loss_pips | 292.0 | 718 | -975 | 0.9 | 0.78 |
| stop_loss_pips | 324.0 | 718 | -975 | 0.9 | 0.78 |
| stop_loss_pips | 356.0 | 718 | -975 | 0.9 | 0.78 |
| stop_loss_pips | 389.0 | 718 | -975 | 0.9 | 0.78 |
| stop_loss_pips | 421.0 | 718 | -975 | 0.9 | 0.78 |
| take_profit_pips | 230.0 | 718 | -912 | 0.91 | 0.78 |
| take_profit_pips | 262.0 | 718 | -880 | 0.91 | 0.78 |
| take_profit_pips | 295.0 | 718 | -975 | 0.9 | 0.78 |
| take_profit_pips | 328.0 | 718 | -975 | 0.9 | 0.78 |
| take_profit_pips | 361.0 | 718 | -975 | 0.9 | 0.78 |
| take_profit_pips | 394.0 | 718 | -975 | 0.9 | 0.78 |
| take_profit_pips | 426.0 | 718 | -975 | 0.9 | 0.78 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 14/150, PF mediana 0.92, p5 0.80; OOS PF>1 en 17/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 164 | 246 | 328 | 410 | 525 |
|---|---|---|---|---|---|
| 194.0 | 0.92 | 0.91 | 0.9 | 0.9 | 0.9 |
| 259.0 | 0.92 | 0.91 | 0.9 | 0.9 | 0.9 |
| 324.0 | 0.92 | 0.91 | 0.9 | 0.9 | 0.9 |
| 389.0 | 0.92 | 0.91 | 0.9 | 0.9 | 0.9 |
| 486.0 | 0.92 | 0.91 | 0.9 | 0.9 | 0.9 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |
| baseline_fixed_spread | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |
| buy_only | 352 | -900 | 0.83 | -1013 | 0.62 | -344 |
| sell_only | 389 | -358 | 0.93 | -936 | 0.85 | -109 |
| no_session | 799 | -1667 | 0.84 | -2142 | 0.7 | -512 |
| commission | 718 | -975 | 0.9 | -1475 | 0.78 | -321 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params wpr_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2011 | 40/243/246 | -17 | -339 | 45 | -471 |
| 2012 | 40/243/246 | 42 | -157 | 29 | -163 |
| 2013 | 40/243/246 | -23 | -117 | 22 | -48 |
| 2014 | 40/243/246 | -92 | 17 | 40 | 233 |
| 2015 | 31/324/246 | -112 | -208 | 34 | -208 |
| 2016 | 23/243/246 | 14 | 42 | 52 | 292 |
| 2017 | 31/243/246 | 67 | -9 | 23 | -9 |
| 2018 | 40/243/246 | 84 | -53 | 27 | 205 |
| 2019 | 31/243/246 | 70 | 321 | 39 | 321 |
| 2020 | 31/243/246 | 202 | -82 | 44 | -82 |
| 2021 | 40/243/246 | 127 | 257 | 31 | 108 |
| 2022 | 40/243/246 | 146 | 99 | 25 | -198 |
| 2023 | 40/243/246 | 184 | 101 | 35 | -88 |
| 2024 | 40/243/246 | 156 | -43 | 42 | -105 |
| 2025 | 40/243/246 | 103 | -217 | 38 | -188 |
| 2026 | 40/243/246 | -15 | -95 | 31 | -213 |

Total OOS walk-forward -483 pips (base -614); anios positivos 6/16; eficiencia -0.52 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 383 | 101.3 | 0.3 |
| D1 > SMA200 | 335 | -1076.1 | -3.2 |

Por dia de entrada: lun -356 (134), mar -424 (174), mie -9 (143), jue -364 (137), vie 178 (130)

Por hora de entrada (pips): 2h -43, 3h -284, 4h 62, 5h -110, 6h 36, 7h -59, 8h 240, 9h 164, 10h -82, 11h -61, 12h -33, 13h -584, 14h -187, 15h 307, 16h -66, 17h -128, 18h -96, 19h 193, 20h -357, 21h 40, 22h 73

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
