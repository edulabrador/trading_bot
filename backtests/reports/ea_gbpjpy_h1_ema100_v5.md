# Informe de robustez: ea_gbpjpy_h1_ema100_v5

- Datos: `GBPJPY_H1.csv`, 2006-01-02 00:00:00 a 2026-10-30 23:00:00, 130,031 velas H1
- Spread por vela (pips): mediana 2.00, p95 7.50
- Preset: `baseline` | corte IS/OOS: 2022-07-11 | semilla 42

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
| IS (antes del corte) | 418 | 6236 | 1.14 | 38.0 | 14.9 | -6171 | 1.3 |
| OOS (desde el corte) | 112 | 2581 | 1.23 | 40.2 | 23.0 | -1031 | 1.04 |

Por anio (pips): 2006: 2021, 2007: -162, 2008: -2322, 2009: 718, 2010: -2464, 2011: -775, 2012: 1946, 2013: 1593, 2014: 682, 2015: 1132, 2016: 931, 2017: -288, 2018: -297, 2019: 361, 2020: 522, 2021: 1333, 2022: 848, 2023: -87, 2024: 3001, 2025: 9, 2026: 114

Anios negativos: 7 de 21

Chequeo salida AO: el AO supera ao_level=3.47 en el 0.09% de las velas (p99 = 1.86). Si es ~0%, la salida por senal no actua.

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

60 simulaciones, ~501 trades cada una (el bot: 530).

| metrica | bot | aleatorio p50 | p5 | p95 | percentil del bot |
|---|---|---|---|---|---|
| ganancia media/trade (pips) | 16.6 | 10.0 | 1.5 | 19.7 | 88% |
| profit factor | 1.16 | 1.09 | 1.01 | 1.19 | 88% |
| ganancia media/trade OOS | 23.0 | 19.4 | -2.9 | 42.1 | 67% |

Si el bot no supera claramente el p95, la senal de entrada aporta poco frente a la estructura (filtro, SL/TP).

Buy & hold del simbolo: +810 pips en todo el periodo; +4717 desde el corte

## 4. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -3589, p95 -5644, p99 -6824 pips (historico -6171) |
| bootstrap periodo completo | P(neto<0) 5.0%, neto p5/p50/p95 -13/8830/17831, maxDD p95 -6916 |
| bootstrap solo OOS | P(neto<0) 16.0% con 112 trades |
| horizonte 1 anio(s) (~25 trades) | P(perder) 33.0%, p5 -1329, p50 584 pips |
| horizonte 2 anio(s) (~51 trades) | P(perder) 28.4%, p5 -1843, p50 818 pips |
| horizonte 3 anio(s) (~76 trades) | P(perder) 27.2%, p5 -2165, p50 1190 pips |
| saltar 20% trades + slippage N(-1,2) | PF p5 1.07, p50 1.15; P(neto<0) 0.2% |

Guia de tamano (pip_value_per_lot=7.0): maxDD p99 de reordenar = 6824 pips = 478 por 0.01 lotes, 4777 por 0.10 lotes.

## 5. Robustez de parametros

| param | valor | trades | net_pips | PF | PF_OOS |
|---|---|---|---|---|---|
| fi_period | 15.0 | 596 | 5773 | 1.09 | 1.21 |
| fi_period | 18.0 | 562 | 5176 | 1.09 | 1.09 |
| fi_period | 20.0 | 546 | 7660 | 1.13 | 1.25 |
| fi_period | 22.0 | 530 | 8818 | 1.16 | 1.23 |
| fi_period | 24.0 | 532 | 4788 | 1.08 | 1.21 |
| fi_period | 26.0 | 500 | 6660 | 1.13 | 1.19 |
| fi_period | 29.0 | 480 | 3308 | 1.06 | 1.04 |
| ao_level | 2.429 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 2.776 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 3.123 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 3.47 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 3.817 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 4.164 | 530 | 8818 | 1.16 | 1.23 |
| ao_level | 4.511 | 530 | 8818 | 1.16 | 1.23 |
| stop_loss_pips | 115.5 | 627 | 6788 | 1.13 | 1.21 |
| stop_loss_pips | 132.0 | 593 | 8726 | 1.16 | 1.28 |
| stop_loss_pips | 148.5 | 567 | 7639 | 1.14 | 1.28 |
| stop_loss_pips | 165.0 | 530 | 8818 | 1.16 | 1.23 |
| stop_loss_pips | 181.5 | 513 | 7094 | 1.12 | 1.11 |
| stop_loss_pips | 198.0 | 497 | 8318 | 1.14 | 1.26 |
| stop_loss_pips | 214.5 | 477 | 8428 | 1.15 | 1.27 |
| take_profit_pips | 221.2 | 686 | 9311 | 1.15 | 1.27 |
| take_profit_pips | 252.8 | 614 | 9395 | 1.16 | 1.34 |
| take_profit_pips | 284.4 | 576 | 7721 | 1.13 | 1.19 |
| take_profit_pips | 316.0 | 530 | 8818 | 1.16 | 1.23 |
| take_profit_pips | 347.6 | 498 | 11479 | 1.22 | 1.3 |
| take_profit_pips | 379.2 | 474 | 9969 | 1.19 | 1.3 |
| take_profit_pips | 410.8 | 451 | 9280 | 1.18 | 1.3 |
| trend_ema_period | 70.0 | 536 | 10221 | 1.19 | 1.35 |
| trend_ema_period | 80.0 | 533 | 9258 | 1.17 | 1.28 |
| trend_ema_period | 90.0 | 535 | 8399 | 1.15 | 1.3 |
| trend_ema_period | 100.0 | 530 | 8818 | 1.16 | 1.23 |
| trend_ema_period | 110.0 | 528 | 9646 | 1.18 | 1.23 |
| trend_ema_period | 120.0 | 518 | 9403 | 1.18 | 1.27 |
| trend_ema_period | 130.0 | 518 | 9895 | 1.19 | 1.23 |

Todos los parametros +-20% a la vez (150 combinaciones): PF>1 en 150/150, PF mediana 1.13, p5 1.07; OOS PF>1 en 149/150

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
| baseline | 530 | 8818 | 1.16 | -6171 | 1.23 | 2581 |
| baseline_fixed_spread | 530 | 9085 | 1.17 | -5906 | 1.24 | 2645 |
| friday_close | 905 | 7628 | 1.14 | -5129 | 1.17 | 1966 |
| session_close | 1753 | 4827 | 1.1 | -2212 | 1.19 | 1930 |
| be100 | 733 | 7744 | 1.18 | -4499 | 1.21 | 1802 |
| be160 | 627 | 7805 | 1.17 | -4946 | 1.5 | 4102 |
| trail_atr3 | 1068 | 9535 | 1.16 | -3584 | 1.18 | 2287 |
| trail_atr5 | 984 | 6653 | 1.14 | -4163 | 1.29 | 2715 |
| time96 | 904 | 8360 | 1.15 | -3821 | 1.15 | 1801 |
| time168 | 730 | 7324 | 1.13 | -4977 | 1.3 | 3352 |
| fri_be | 991 | 9254 | 1.19 | -4122 | 1.16 | 1678 |
| fri_be_trail | 1259 | 8558 | 1.15 | -4102 | 1.16 | 1895 |
| ema50 | 563 | 10078 | 1.17 | -6734 | 1.41 | 4511 |
| ema200 | 503 | 6641 | 1.13 | -7177 | 1.27 | 2860 |
| no_ema | 893 | 10374 | 1.11 | -7644 | 1.4 | 7036 |
| both_dirs | 884 | 14169 | 1.15 | -5596 | 0.91 | -1725 |
| low_atr50 | 409 | 1799 | 1.04 | -5237 | 0.98 | -198 |
| max_spread4 | 490 | 8670 | 1.17 | -5652 | 1.27 | 2854 |
| commission | 530 | 8818 | 1.16 | -6171 | 1.23 | 2581 |

Ojo: elegir el mejor preset mirando esta tabla es sobreoptimizar. Decide la variante antes de ver resultados.

## 7. Walk-forward

| anio | params fi_period/stop_loss_pips/take_profit_pips | IS pips/anio | OOS pips | OOS trades | base pips |
|---|---|---|---|---|---|
| 2010 | 16/165/237 | 666 | -2293 | 40 | -2464 |
| 2011 | 22/124/237 | -198 | -33 | 26 | -775 |
| 2012 | 22/124/237 | -268 | 1666 | 24 | 1946 |
| 2013 | 22/124/237 | 279 | 809 | 39 | 1593 |
| 2014 | 29/165/237 | 226 | 908 | 23 | 682 |
| 2015 | 29/165/237 | 1025 | 1458 | 25 | 1132 |
| 2016 | 29/165/237 | 1408 | -350 | 31 | 931 |
| 2017 | 22/165/316 | 1085 | -288 | 19 | -288 |
| 2018 | 22/165/411 | 910 | -625 | 14 | -297 |
| 2019 | 22/165/411 | 393 | 788 | 16 | 361 |
| 2020 | 22/214/411 | 652 | 307 | 13 | 522 |
| 2021 | 22/124/411 | 443 | 657 | 20 | 1333 |
| 2022 | 16/165/316 | 543 | 844 | 38 | 848 |
| 2023 | 16/214/411 | 1122 | -606 | 23 | -86 |
| 2024 | 22/214/316 | 694 | 2506 | 25 | 3001 |
| 2025 | 29/214/237 | 1349 | -523 | 23 | 9 |
| 2026 | 16/214/316 | 1024 | 673 | 16 | 114 |

Total OOS walk-forward 5898 pips (base 8562); anios positivos 10/17; eficiencia 0.52 (>0.5 suele considerarse aceptable)

## 8. Regimen, dia y hora

| regimen | trades | pips | media |
|---|---|---|---|
| D1 < SMA200 | 238 | 3405.5 | 14.3 |
| D1 > SMA200 | 292 | 5412.1 | 18.5 |

Por dia de entrada: lun 4150 (127), mar 3408 (97), mie 1863 (95), jue -3507 (108), vie 2903 (103)

Por hora de entrada (pips): 1h 43, 2h -452, 3h -1315, 4h 2368, 5h 2458, 6h -925, 7h 535, 8h 788, 9h -3167, 10h 1823, 11h 1194, 12h 2221, 13h 781, 14h 737, 15h -89, 16h -49, 17h 1201, 18h 520, 19h 206, 20h 486, 21h -547

No filtres por dia u hora a partir de estas tablas sin validarlo fuera de muestra: es la forma mas facil de sobreajustar.
