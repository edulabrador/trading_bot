# Pruebas exigentes: S2 (RSI(2) en indices)

Registradas antes de ejecutarlas en [`../research/PRUEBAS_EXIGENTES.md`](../research/PRUEBAS_EXIGENTES.md). Resultados en R. Holdout: desde el 10/07/2023.

## 1. Fuente de datos y corte del dia: S&P 500 Yahoo frente a Dukascopy (2011-09 a 2025-12)

| datos | trades | PF | R | t |
|---|---|---|---|---|
| Yahoo (cierre de bolsa) | 113 | 2.34 | 50.0 | 3.49 |
| Dukascopy USA500 (dias UTC, CFD) | 119 | 2.297 | 50.0 | 3.39 |

## 2. Momento de ejecucion y slippage

| escenario | trades | PF | R | PF holdout |
|---|---|---|---|---|
| al cierre del dia de la senal | 373 | 1.888 | 130.0 | 3.103 |
| apertura siguiente (base) | 373 | 1.876 | 127.2 | 2.571 |
| un dia tarde (cierre siguiente) | 373 | 1.559 | 94.8 | 1.681 |
| apertura + 0.1 ATR por lado | 373 | 1.313 | 52.6 | 1.698 |
| un dia tarde + 0.1 ATR por lado | 373 | 1.103 | 20.2 | 1.119 |

## 3. Crisis

| ventana | trades | R | peor trade (R) |
|---|---|---|---|
| crisis financiera | 0 | 0.0 |  |
| agosto 2011 | 1 | -8.2 | -8.2 |
| devaluacion China | 1 | -4.3 | -4.3 |
| feb 2018 (volmageddon) | 3 | -10.8 | -4.0 |
| oct-dic 2018 | 2 | -8.7 | -4.8 |
| COVID | 4 | -13.5 | -7.9 |
| 2022 | 8 | -1.8 | -2.7 |
| deshacer carry yen | 6 | 3.1 | -0.8 |
| aranceles 2025 | 5 | -4.5 | -6.3 |

## 4. Walk-forward (rsi_lo x sma_exit, 5 anios de entrenamiento)

| anio | rsi_lo/sma_exit | IS R/anio | OOS R | base R |
|---|---|---|---|---|
| 2013 | 15/10 | 4.6 | 13.5 | 4.8 |
| 2014 | 15/10 | 7.3 | 25.8 | 5.1 |
| 2015 | 15/10 | 11.0 | 12.6 | 10.9 |
| 2016 | 15/10 | 12.8 | 1.5 | 4.3 |
| 2017 | 15/10 | 13.0 | 40.5 | 20.5 |
| 2018 | 15/10 | 18.8 | -10.4 | -19.3 |
| 2019 | 15/10 | 14.0 | 10.9 | 6.2 |
| 2020 | 15/10 | 11.0 | -36.9 | 3.2 |
| 2021 | 15/5 | 5.8 | 31.2 | 25.3 |
| 2022 | 15/5 | 11.6 | -1.6 | -1.8 |
| 2023 | 15/5 | 5.6 | 13.7 | 12.8 |
| 2024 | 15/5 | 11.6 | 28.6 | 26.2 |
| 2025 | 15/5 | 14.9 | 17.9 | 14.8 |

Total OOS 147.3 R (base 113.0); anios positivos 10/13; eficiencia 1.04

## 5. Financiacion del CFD

| version | PF | R | PF holdout |
|---|---|---|---|
| sin financiacion | 1.876 | 127.2 | 2.571 |
| con financiacion (tipo + 2.5%) | 1.713 | 109.2 | 2.166 |

Coste medio por trade: 0.048 R (4.8 noches de media). Tipos aproximados de memoria.

## 6. Mas simulaciones

- 100 entradas aleatorias: S2 supera al 100% (media aleatoria 0.103 R/trade, S2 0.309).
- 150 combinaciones (+-20% a la vez): PF > 1 en 150/150 en desarrollo (mediana 1.74, minimo 1.34) y en 150/150 en holdout (mediana 2.87).

## 7. Mejoras (Parte 2): seleccion solo con desarrollo

| variante | trades | PF | R | maxDD (R) | R/|DD| | t | candidata |
|---|---|---|---|---|---|---|---|
| M0 original | 276 | 1.72 | 85.4 | -12.3 | 6.94 | 3.22 | no |
| M1 salida RSI>70 | 267 | 2.124 | 123.1 | -12.5 | 9.85 | 4.7 | si |
| M2 stop 3 ATR | 300 | 1.605 | 84.6 | -12.0 | 7.05 | 3.28 | no |
| M3 filtro volatilidad p90 | 262 | 1.761 | 84.5 | -9.8 | 8.62 | 3.26 | si |
| M4 cierre a 10 dias | 276 | 1.626 | 78.6 | -12.4 | 6.34 | 2.8 | no |

Variante elegida para validar en indices nuevos: **M1 salida RSI>70**
