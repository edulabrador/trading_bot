# Pruebas exigentes: EMA100 v6 (GBPJPY H1)

Registradas antes de ejecutarlas en [`../research/PRUEBAS_EXIGENTES.md`](../research/PRUEBAS_EXIGENTES.md). Resultados en pips. Holdout: desde el 10/07/2023.

Referencia: 530 trades, PF 1.16, +8818 pips, maxDD -6171.

## 1. Zona horaria del broker

| desplazamiento | trades | PF | pips | PF holdout |
|---|---|---|---|---|
| -2 h (GMT+0/+1) | 527 | 1.17 | 9456 | 1.35 |
| -1 h (GMT+1/+2) | 529 | 1.18 | 9539 | 1.35 |
| +0 h (GMT+2/+3) | 530 | 1.16 | 8818 | 1.28 |
| +1 h (GMT+3/+4) | 529 | 1.16 | 8942 | 1.21 |
| +2 h (GMT+4/+5) | 527 | 1.16 | 8631 | 1.22 |

## 2. Retraso de ejecucion y slippage

| escenario | trades | PF | pips | PF holdout |
|---|---|---|---|---|
| base (spread real) | 530 | 1.16 | 8818 | 1.28 |
| spread fijo 2.0 | 530 | 1.17 | 9350 | 1.29 |
| +1 pip por lado | 530 | 1.15 | 8290 | 1.27 |
| +3 pips por lado | 530 | 1.11 | 6170 | 1.22 |
| entrada 1 vela tarde | 513 | 1.08 | 4244 | 1.17 |
| 1 vela tarde + 3 pips por lado | 513 | 1.03 | 1567 | 1.11 |

## 3. Crisis

| ventana | desde | hasta | trades cerrados | pips | peor caida dentro (pips, equity flotante) |
|---|---|---|---|---|---|
| crisis financiera | 2008-09-01 | 2009-03-31 | 29 | -628 | -1820 |
| Fukushima / yen | 2011-03-01 | 2011-04-30 | 4 | 291 | -372 |
| devaluacion China | 2015-08-01 | 2015-09-30 | 3 | -21 | -377 |
| Brexit | 2016-06-01 | 2016-07-31 | 6 | -41 | -551 |
| COVID | 2020-02-15 | 2020-04-30 | 2 | 145 | -418 |
| 2022 (tipos) | 2022-01-01 | 2022-12-31 | 38 | 848 | -1057 |
| deshacer carry yen | 2024-07-01 | 2024-08-31 | 4 | 293 | -413 |

Referencia: drawdown mediano del Monte Carlo = -3,589 pips; el 5% de peores casos, -5,644.

## 4. Otra fuente de datos: GBPJPY sintetico (GBPUSD x USDJPY), 2007 a 2023

| datos | trades | PF | net | maxDD |
|---|---|---|---|---|
| Dukascopy GBPJPY (real) | 416 | 1.08 | 3717 | -6171 |
| sintetico GBPUSD x USDJPY | 388 | 1.1 | 3955 | -6076 |

## 5. Tamano por volatilidad (Parte 3)

| metodo | tramo | PF | neto (pips equivalentes) | maxDD | neto / |maxDD| |
|---|---|---|---|---|---|
| lotes fijos | desarrollo | 1.14 | 6614 | -6171 | 1.07 |
| lotes fijos | holdout | 1.28 | 2204 | -920 | 2.4 |
| tamano por volatilidad | desarrollo | 1.22 | 8902 | -4836 | 1.84 |
| tamano por volatilidad | holdout | 1.19 | 1419 | -970 | 1.46 |

ATR(20) diario mediano en desarrollo: 154 pips; peso medio 0.91. Regla: mejorar >= 10% en desarrollo (1.84 frente a 1.07) y no empeorar en holdout (1.46 frente a 2.4) -> **NO SE ADOPTA**.
