# S2: reversion a la media en indices (RSI(2) de Connors)

Reglas fijadas antes de ver resultados en [`../research/NUEVAS_ESTRATEGIAS.md`](../research/NUEVAS_ESTRATEGIAS.md). Entrada: solo largos si cierre > SMA(200) y RSI(2) < 10, ejecutando en la apertura del dia siguiente. Salida: cierre > SMA(5). Sin stop. Resultados en R (beneficio / ATR(20) diario en la entrada), con spread incluido y sin financiacion del CFD.

Datos: S&P 500 (Yahoo, 2007-2026), Nasdaq 100 (Dukascopy, 2011-2025), DAX (Dukascopy, 2013-2025).

## 1. Resultados

| tramo | trades | PF | R total | R/trade | t | maxDD (R) | aciertos |
|---|---|---|---|---|---|---|---|
| desarrollo (hasta 09/07/2023) | 276 | 1.72 | 85.4 | 0.309 | 3.22 | -12.3 | 72% |
| holdout (desde 10/07/2023) | 97 | 2.571 | 41.8 | 0.431 | 3.61 | -6.3 | 75% |
| total | 373 | 1.876 | 127.2 | 0.341 | 4.4 | -12.3 | 73% |

| indice | tramo | trades | PF | R | t |
|---|---|---|---|---|---|
| DAX | desarrollo | 76 | 1.17 | 7.1 | 0.44 |
| DAX | holdout | 27 | 2.17 | 9.6 | 1.72 |
| NAS100 | desarrollo | 91 | 2.295 | 39.1 | 3.13 |
| NAS100 | holdout | 32 | 2.282 | 12.6 | 1.57 |
| SP500 | desarrollo | 109 | 1.846 | 39.2 | 2.32 |
| SP500 | holdout | 38 | 3.289 | 19.6 | 3.07 |

R por anio: 2007: 1.6, 2009: 5.1, 2010: 3.4, 2011: -6.7, 2012: 6.6, 2013: 4.8, 2014: 5.1, 2015: 10.9, 2016: 4.3, 2017: 20.5, 2018: -19.3, 2019: 6.2, 2020: 3.2, 2021: 25.3, 2022: -1.8, 2023: 12.8, 2024: 26.2, 2025: 14.8, 2026: 4.3

Anios negativos: 3 de 19. Duracion media de cada trade: 4.8 dias (mediana 4). Trades al anio: 20.

## 2. Peores trades (no hay stop)

| sym | entry_time | exit_time | hold_days | R |
|---|---|---|---|---|
| DAX | 2021-11-23 | 2021-12-03 | 10 | -8.32 |
| SP500 | 2011-07-28 | 2011-08-12 | 15 | -8.17 |
| DAX | 2020-02-23 | 2020-03-05 | 11 | -7.93 |
| NAS100 | 2025-02-23 | 2025-03-16 | 21 | -6.33 |
| SP500 | 2018-10-05 | 2018-10-17 | 12 | -4.79 |
| DAX | 2015-08-13 | 2015-08-27 | 14 | -4.33 |
| SP500 | 2018-02-05 | 2018-02-13 | 8 | -4.01 |
| NAS100 | 2018-10-05 | 2018-10-15 | 10 | -3.93 |

El peor trade pierde -8.3 R. Una posicion se mide en R = ATR(20) diario; con un riesgo de 0.5% de la cuenta por R, el peor trade habria costado un 4.2% de la cuenta.

## 3. Costes

| spread | PF | R total | PF holdout |
|---|---|---|---|
| x1 | 1.876 | 127.2 | 2.571 |
| x2 | 1.808 | 119.2 | 2.523 |
| x3 | 1.742 | 111.2 | 2.474 |
| x5 | 1.615 | 95.1 | 2.379 |

Financiacion del CFD (no incluida): con trades de unos pocos dias, un coste anual del 5-7% sobre el nominal supone del orden de 0.05-0.1% por trade. Conviene medirlo en la demo con el broker real.

## 4. Sensibilidad de parametros (uno a uno)

| parametro | valor | trades | PF desarrollo | PF holdout |
|---|---|---|---|---|
| rsi_lo | 5.0 | 138 | 1.515 | 3.09 |
| rsi_lo | 7.5 | 216 | 1.538 | 3.254 |
| rsi_lo | 10.0 | 276 | 1.72 | 2.571 |
| rsi_lo | 12.5 | 347 | 1.624 | 2.885 |
| rsi_lo | 15.0 | 401 | 1.685 | 2.508 |
| sma_trend | 100.0 | 253 | 1.906 | 2.71 |
| sma_trend | 150.0 | 270 | 1.92 | 2.591 |
| sma_trend | 200.0 | 276 | 1.72 | 2.571 |
| sma_trend | 250.0 | 278 | 1.535 | 2.779 |
| sma_trend | 300.0 | 281 | 1.583 | 2.755 |
| sma_exit | 3.0 | 293 | 1.4 | 2.069 |
| sma_exit | 4.0 | 287 | 1.582 | 3.097 |
| sma_exit | 5.0 | 276 | 1.72 | 2.571 |
| sma_exit | 7.0 | 268 | 2.099 | 2.129 |
| sma_exit | 10.0 | 263 | 1.684 | 2.563 |
| rsi_n | 2.0 | 276 | 1.72 | 2.571 |
| rsi_n | 3.0 | 100 | 1.386 | 2.73 |
| rsi_n | 4.0 | 40 | 2.072 | 1.566 |

## 5. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -14.6 R, p95 -22.7, p99 -27.8 (historico -12.3) |
| bootstrap total | P(neto<0) 0.00% |
| horizonte 1 anio(s) (~20 trades) | P(perder) 15.1%, p5 -5.0 R, p50 7.4 R |
| horizonte 2 anio(s) (~39 trades) | P(perder) 8.3%, p5 -3.1 R, p50 13.9 R |
| saltar 20% trades + slippage N(-0.05R, 0.1R) | PF p5 1.51, p50 1.71 |

## 6. Validacion en otro mercado registrada de antemano: oro

- XAUUSD desarrollo: 124 trades, PF 1.269, R 14.1, t 0.94
- XAUUSD holdout: 25 trades, PF 3.955, R 11.4, t 2.72
- XAUUSD total: 149 trades, PF 1.452, R 25.4, t 1.63

## 7. Correlacion con el EMA100 v6 y cartera

Correlacion mensual EMA100 v6 (GBPJPY) vs S2: **0.01** (la regla pide < 0.3).
| componente | neto (10k) | anual medio | maxDD mensual | meses negativos | neto desde 07/2023 |
|---|---|---|---|---|---|
| EMA100 | 467 | 25 | -400 | 50% | 154 |
| S2 | 6361 | 335 | -1039 | 18% | 2092 |
| cartera | 6829 | 359 | -1070 | 37% | 2246 |

Supuestos: EMA100 v6 a 0.01 lotes (pips x 0.01 x 7 USD); S2 arriesgando el 0.5% de 10,000 por cada R (1 ATR diario). Sin swap ni financiacion. Drawdown calculado sobre resultados mensuales.
