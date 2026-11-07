# S2 con mejora M1 (salida RSI(2) > 70): reversion a la media en indices (RSI(2) de Connors)

Reglas fijadas antes de ver resultados en [`../research/NUEVAS_ESTRATEGIAS.md`](../research/NUEVAS_ESTRATEGIAS.md). Entrada: solo largos si cierre > SMA(200) y RSI(2) < 10, ejecutando en la apertura del dia siguiente. Salida (mejora M1): RSI(2) > 70. Sin stop. Resultados en R (beneficio / ATR(20) diario en la entrada), con spread incluido y sin financiacion del CFD.

Datos: S&P 500 (Yahoo, 2007-2026), Nasdaq 100 (Dukascopy, 2011-2025), DAX (Dukascopy, 2013-2025).

## 1. Resultados

| tramo | trades | PF | R total | R/trade | t | maxDD (R) | aciertos |
|---|---|---|---|---|---|---|---|
| desarrollo (hasta 09/07/2023) | 267 | 2.124 | 123.1 | 0.461 | 4.7 | -12.5 | 76% |
| holdout (desde 10/07/2023) | 91 | 2.194 | 41.2 | 0.453 | 2.94 | -5.9 | 76% |
| total | 358 | 2.141 | 164.4 | 0.459 | 5.54 | -12.5 | 76% |

| indice | tramo | trades | PF | R | t |
|---|---|---|---|---|---|
| DAX | desarrollo | 72 | 1.272 | 10.8 | 0.68 |
| DAX | holdout | 26 | 2.026 | 9.6 | 1.59 |
| NAS100 | desarrollo | 90 | 2.911 | 55.5 | 4.24 |
| NAS100 | holdout | 31 | 2.263 | 13.7 | 1.71 |
| SP500 | desarrollo | 105 | 2.392 | 56.8 | 3.53 |
| SP500 | holdout | 34 | 2.252 | 17.9 | 1.8 |

R por anio: 2007: 2.5, 2009: 5.1, 2010: 4.3, 2011: -2.8, 2012: 7.2, 2013: 6.8, 2014: 9.2, 2015: 15.5, 2016: 5.3, 2017: 22.8, 2018: -7.7, 2019: 9.0, 2020: -0.5, 2021: 28.9, 2022: -1.0, 2023: 14.9, 2024: 25.7, 2025: 12.1, 2026: 7.0

Anios negativos: 4 de 19. Duracion media de cada trade: 6.3 dias (mediana 6). Trades al anio: 19.

## 2. Peores trades (no hay stop)

| sym | entry_time | exit_time | hold_days | R |
|---|---|---|---|---|
| DAX | 2020-02-23 | 2020-03-05 | 11 | -7.93 |
| DAX | 2021-11-23 | 2021-12-07 | 14 | -6.96 |
| SP500 | 2011-07-28 | 2011-08-16 | 19 | -6.24 |
| SP500 | 2025-02-24 | 2025-03-18 | 22 | -5.86 |
| NAS100 | 2025-02-23 | 2025-03-18 | 23 | -5.72 |
| SP500 | 2018-10-05 | 2018-10-17 | 12 | -4.79 |
| DAX | 2020-10-16 | 2020-11-03 | 18 | -4.62 |
| DAX | 2015-08-13 | 2015-08-27 | 14 | -4.33 |

El peor trade pierde -7.9 R. Una posicion se mide en R = ATR(20) diario; con un riesgo de 0.5% de la cuenta por R, el peor trade habria costado un 4.0% de la cuenta.

## 3. Costes

| spread | PF | R total | PF holdout |
|---|---|---|---|
| x1 | 2.141 | 164.4 | 2.194 |
| x2 | 2.073 | 156.6 | 2.161 |
| x3 | 2.007 | 148.8 | 2.129 |
| x5 | 1.878 | 133.3 | 2.065 |

Financiacion del CFD (no incluida): con trades de unos pocos dias, un coste anual del 5-7% sobre el nominal supone del orden de 0.05-0.1% por trade. Conviene medirlo en la demo con el broker real.

## 4. Sensibilidad de parametros (uno a uno)

| parametro | valor | trades | PF desarrollo | PF holdout |
|---|---|---|---|---|
| rsi_lo | 5.0 | 137 | 1.988 | 2.157 |
| rsi_lo | 7.5 | 211 | 2.047 | 2.262 |
| rsi_lo | 10.0 | 267 | 2.124 | 2.194 |
| rsi_lo | 12.5 | 329 | 2.0 | 2.538 |
| rsi_lo | 15.0 | 375 | 1.976 | 2.471 |
| sma_trend | 100.0 | 248 | 2.407 | 2.416 |
| sma_trend | 150.0 | 263 | 2.385 | 2.302 |
| sma_trend | 200.0 | 267 | 2.124 | 2.194 |
| sma_trend | 250.0 | 269 | 1.853 | 2.317 |
| sma_trend | 300.0 | 273 | 1.917 | 2.264 |
| sma_exit | 3.0 | 267 | 2.124 | 2.194 |
| sma_exit | 4.0 | 267 | 2.124 | 2.194 |
| sma_exit | 5.0 | 267 | 2.124 | 2.194 |
| sma_exit | 7.0 | 267 | 2.124 | 2.194 |
| sma_exit | 10.0 | 267 | 2.124 | 2.194 |
| rsi_n | 2.0 | 267 | 2.124 | 2.194 |
| rsi_n | 3.0 | 93 | 1.211 | 3.084 |
| rsi_n | 4.0 | 39 | 1.817 | 3.494 |

## 5. Monte Carlo

| prueba | resultado |
|---|---|
| reordenar trades | maxDD p50 -13.2 R, p95 -20.9, p99 -25.5 (historico -12.5) |
| bootstrap total | P(neto<0) 0.00% |
| horizonte 1 anio(s) (~19 trades) | P(perder) 11.0%, p5 -3.4 R, p50 9.2 R |
| horizonte 2 anio(s) (~38 trades) | P(perder) 4.2%, p5 0.9 R, p50 18.0 R |
| saltar 20% trades + slippage N(-0.05R, 0.1R) | PF p5 1.75, p50 1.98 |

## 6. Validacion en otro mercado registrada de antemano: oro

- XAUUSD desarrollo: 112 trades, PF 1.194, R 11.1, t 0.69
- XAUUSD holdout: 24 trades, PF 3.104, R 12.0, t 2.25
- XAUUSD total: 136 trades, PF 1.366, R 23.1, t 1.35

## 7. Correlacion con el EMA100 v6 y cartera

Correlacion mensual EMA100 v6 (GBPJPY) vs S2: **-0.04** (la regla pide < 0.3).
| componente | neto (10k) | anual medio | maxDD mensual | meses negativos | neto desde 07/2023 |
|---|---|---|---|---|---|
| EMA100 | 467 | 25 | -400 | 50% | 154 |
| S2 | 8218 | 434 | -763 | 15% | 2061 |
| cartera | 8686 | 459 | -765 | 37% | 2216 |

Supuestos: EMA100 v6 a 0.01 lotes (pips x 0.01 x 7 USD); S2 arriesgando el 0.5% de 10,000 por cada R (1 ATR diario). Sin swap ni financiacion. Drawdown calculado sobre resultados mensuales.

## 8. Financiacion, ejecucion y slippage (M1)

| escenario | PF | R | PF holdout |
|---|---|---|---|
| sin financiacion | 2.141 | 164.4 | 2.194 |
| con financiacion (tipo + 2.5%) | 1.916 | 141.0 | 1.796 |
| +0.05 ATR por lado | 1.839 | 128.6 | 1.875 |
| +0.1 ATR por lado | 1.57 | 92.8 | 1.591 |

Coste medio de financiacion: 0.065 R por trade (6.3 noches). Tipos aproximados de memoria.
