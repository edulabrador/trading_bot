# Informe de robustez: ema100_gbpjpy_h1

- Datos: `GBPJPY_H1.csv`, 2006-01-02 00:00:00 a 2026-10-30 23:00:00, 130,031 velas H1
- Spread por vela (pips): mediana 2.00, p95 7.50
- Preset: `v6_no_ao_exit` | corte IS/OOS: 2023-07-10 | semilla 42

## 1. Backtest base

| metrica | valor |
|---|---|
| trades | 530 |
| trades_per_year | 25.5 |
| win_rate_% | 38.49 |
| profit_factor | 1.161 |
| expectancy_pips | 16.64 |
| avg_win_pips | 311.8 |
| avg_loss_pips | -168.1 |
| total_pips | 8817.6 |
| max_dd_closed_pips | -6171.4 |
| max_dd_float_pips | -6261.5 |
| max_consec_losses | 13 |
| avg_hold_hours | 192.4 |
| exit_mix | {"SL": 324, "TP": 203, "SL_gap": 2, "END": 1} |
| exposure_% | 56.5 |
| cagr_% | 2.34 |

t-stat de la media por trade: **1.64** (por debajo de ~2 no es concluyente)

Periodo mas largo sin nuevo maximo de equity (cerrada): **3431 dias**

| tramo | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t |
|---|---|---|---|---|---|---|---|
| IS (antes del corte) | 450 | 6614 | 1.14 | 38.0 | 14.7 | -6171 | 1.33 |
| OOS (desde el corte) | 80 | 2204 | 1.28 | 41.2 | 27.6 | -752 | 1.04 |

Por anio (pips): 2006: 2021, 2007: -162, 2008: -2322, 2009: 718, 2010: -2464, 2011: -775, 2012: 1946, 2013: 1593, 2014: 682, 2015: 1132, 2016: 931, 2017: -288, 2018: -297, 2019: 361, 2020: 522, 2021: 1333, 2022: 848, 2023: -87, 2024: 3001, 2025: 9, 2026: 114

Anios negativos: 7 de 21

Trades con SL y TP tocados en la misma vela H1: 0 (si es >0, conviene usar datos M1/M15 con --ltf-csv)

## 2. Costes

| escenario | trades | net_pips | PF | win% | exp_pips | maxDD_pips | t | neto_cash |
|---|---|---|---|---|---|---|---|---|
| spread real por vela | 530 | 8818 | 1.16 | 38.5 | 16.6 | -6171 | 1.64 | 6172 |
| spread fijo 2.5 | 530 | 9085 | 1.17 | 38.5 | 17.1 | -5906 | 1.69 | 6359 |
| spread fijo 4.0 | 530 | 8290 | 1.15 | 38.5 | 15.6 | -6136 | 1.54 | 5803 |
| spread fijo 6.0 | 530 | 7230 | 1.13 | 38.5 | 13.6 | -6442 | 1.34 | 5061 |
| max_spread 4 | 490 | 8670 | 1.17 | 38.6 | 17.7 | -5652 | 1.67 | 6069 |
| comision 3.5/lado/lote | 530 | 8818 | 1.16 | 38.5 | 16.6 | -6171 | 1.64 | 5801 |

Swap estimado (markup 1.0%): +1435 en divisa de cuenta; neto con swap 7608 (sin swap 6172). Aproximacion con tipos oficiales; usa los swaps reales de tu broker.

Swap estimado (markup 2.0%): +61 en divisa de cuenta; neto con swap 6233 (sin swap 6172). Aproximacion con tipos oficiales; usa los swaps reales de tu broker.

## 3. Benchmark: entradas aleatorias con las mismas reglas

60 simulaciones, ~503 trades cada una (el bot: 530).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 16.6 | 12.1 | 1.7 | 20.4 | 77% |
| profit factor | 1.16 | 1.11 | 1.02 | 1.2 | 77% |
| ganancia media/trade OOS | 27.6 | 25.2 | 5.2 | 53.5 | 55% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +810 pips en todo el periodo; +2862 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -3589, p95 -5644, p99 -6824 pips (historico -6171) |
| bootstrap periodo completo | P(neto<0) 5.0%, neto p5/p50/p95 -13/8830/17831, maxDD p95 -6916 |
| bootstrap solo OOS | P(neto<0) 14.5% con 80 trades |
| horizonte 1 anio(s) (~25 trades) | P(perder) 32.9%, p5 -1331, p50 584 pips |
| horizonte 2 anio(s) (~51 trades) | P(perder) 28.5%, p5 -1840, p50 809 pips |
| horizonte 3 anio(s) (~76 trades) | P(perder) 27.0%, p5 -2165, p50 1188 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.07, p50 1.15; P(neto<0) 0.1% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 6824 pips = 478 por 0.01 lotes, 4777 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| fi_period | 15 | 596 | 5773 | 1.09 | 1.34 |
| fi_period | 18 | 562 | 5352 | 1.09 | 1.26 |
| fi_period | 20 | 546 | 7660 | 1.13 | 1.26 |
| fi_period | 22 | 530 | 8818 | 1.16 | 1.28 |
| fi_period | 24 | 532 | 4788 | 1.08 | 1.22 |
| fi_period | 26 | 500 | 6660 | 1.13 | 1.24 |
| fi_period | 29 | 480 | 3308 | 1.06 | 1.16 |
| trend_ema_period | 70 | 536 | 10219 | 1.19 | 1.36 |
| trend_ema_period | 80 | 533 | 9256 | 1.17 | 1.24 |
| trend_ema_period | 90 | 535 | 8399 | 1.15 | 1.26 |
| trend_ema_period | 100 | 530 | 8818 | 1.16 | 1.28 |
| trend_ema_period | 110 | 529 | 9477 | 1.17 | 1.28 |
| trend_ema_period | 120 | 519 | 9234 | 1.17 | 1.28 |
| trend_ema_period | 130 | 519 | 9726 | 1.18 | 1.25 |
| stop_loss_pips | 115 | 629 | 6338 | 1.12 | 1.07 |
| stop_loss_pips | 132 | 593 | 8726 | 1.16 | 1.2 |
| stop_loss_pips | 148 | 567 | 7819 | 1.14 | 1.3 |
| stop_loss_pips | 165 | 530 | 8818 | 1.16 | 1.28 |
| stop_loss_pips | 182 | 513 | 6941 | 1.12 | 1.19 |
| stop_loss_pips | 198 | 497 | 8318 | 1.14 | 1.26 |
| stop_loss_pips | 214 | 478 | 8342 | 1.14 | 1.19 |
| take_profit_pips | 221 | 686 | 9247 | 1.15 | 1.28 |
| take_profit_pips | 253 | 614 | 9448 | 1.16 | 1.3 |
| take_profit_pips | 284 | 576 | 7629 | 1.13 | 1.17 |
| take_profit_pips | 316 | 530 | 8818 | 1.16 | 1.28 |
| take_profit_pips | 348 | 498 | 11554 | 1.22 | 1.35 |
| take_profit_pips | 379 | 474 | 9936 | 1.19 | 1.23 |
| take_profit_pips | 411 | 451 | 9310 | 1.18 | 1.3 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 150/150, PF mediana 1.13, p5 1.06; OOS PF>1 en 150/150

PF por SL (filas) x TP (columnas):

| SL \ TP | 158 | 237 | 316 | 395 | 506 |
|---|---|---|---|---|---|
| 99.0 | 1.09 | 1.15 | 1.17 | 1.18 | 1.2 |
| 132.0 | 1.07 | 1.17 | 1.16 | 1.18 | 1.26 |
| 165.0 | 1.09 | 1.16 | 1.16 | 1.18 | 1.25 |
| 198.0 | 1.08 | 1.16 | 1.14 | 1.21 | 1.21 |
| 248.0 | 1.09 | 1.12 | 1.13 | 1.14 | 1.15 |

## 6. Presets del bot

| preset | trades | net_pips | PF | maxDD_pips | PF_OOS | net_OOS |
|---|---|---|---|---|---|---|
| baseline | 530 | 8818 | 1.16 | -6171 | 1.28 | 2204 |
| v6_no_ao_exit | 530 | 8818 | 1.16 | -6171 | 1.28 | 2204 |
| baseline_fixed_spread | 530 | 9085 | 1.17 | -5906 | 1.28 | 2233 |
| both_dirs | 884 | 14169 | 1.15 | -5596 | 1.07 | 955 |
| commission | 530 | 8818 | 1.16 | -6171 | 1.28 | 2204 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params fi_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2010 | 16/165/237 | 666 | -2293 | 40 | -2464 |
| 2011 | 22/124/237 | -206 | -37 | 26 | -775 |
| 2012 | 22/124/237 | -275 | 1663 | 24 | 1946 |
| 2013 | 22/124/237 | 273 | 803 | 39 | 1593 |
| 2014 | 29/165/237 | 226 | 908 | 23 | 682 |
| 2015 | 29/165/237 | 1025 | 1458 | 25 | 1132 |
| 2016 | 29/165/237 | 1408 | -350 | 31 | 931 |
| 2017 | 22/165/316 | 1085 | -288 | 19 | -288 |
| 2018 | 22/165/411 | 911 | -624 | 14 | -297 |
| 2019 | 22/165/411 | 395 | 790 | 16 | 361 |
| 2020 | 22/214/411 | 659 | 312 | 13 | 522 |
| 2021 | 22/124/411 | 440 | 654 | 20 | 1333 |
| 2022 | 16/165/316 | 543 | 844 | 38 | 848 |
| 2023 | 16/214/411 | 1128 | -813 | 24 | -86 |
| 2024 | 22/124/316 | 795 | 2323 | 30 | 3001 |
| 2025 | 29/214/237 | 1354 | -517 | 23 | 9 |
| 2026 | 22/124/316 | 1019 | 302 | 20 | 114 |

Total OOS walk-forward 5135 pips (base 8562); anios positivos 10/17; eficiencia 0.45 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 238 | 3405.5 | 14.3 |
| D1 > SMA200 | 292 | 5412.1 | 18.5 |

Por dia de entrada: lun 4150 (127), mar 3408 (97), mie 1863 (95), jue -3507 (108), vie 2903 (103)

Por hora de entrada (pips): 1h 43, 2h -452, 3h -1315, 4h 2368, 5h 2458, 6h -925, 7h 535, 8h 788, 9h -3167, 10h 1823, 11h 1194, 12h 2221, 13h 781, 14h 737, 15h -89, 16h -49, 17h 1201, 18h 520, 19h 206, 20h 486, 21h -547

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
