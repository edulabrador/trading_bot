# S2: validacion en indices nunca vistos

Indices: N225 (2006-01 a 2018-05), CAC40 (2006-01 a 2018-05), ASX200 (2006-01 a 2018-05), AEX (2006-01 a 2018-05), IBEX35 (2006-01 a 2018-05), TSX (2006-01 a 2018-05), NZ50 (2006-01 a 2018-05)

**M0 original**: agregado {'trades': 531, 'PF': 1.19, 'R': np.float64(54.2), 'expR': np.float64(0.102), 't': np.float64(1.35), 'maxDD_R': -24.4}
| indice | trades | PF | R | t |
|---|---|---|---|---|
| AEX | 90 | 1.237 | 11.8 | 0.72 |
| ASX200 | 70 | 0.817 | -9.1 | -0.56 |
| CAC40 | 72 | 1.569 | 16.4 | 1.33 |
| IBEX35 | 68 | 1.718 | 17.7 | 1.45 |
| N225 | 72 | 1.306 | 11.4 | 0.78 |
| NZ50 | 86 | 1.075 | 3.4 | 0.26 |
| TSX | 73 | 1.053 | 2.6 | 0.13 |

**M1 salida RSI>70**: agregado {'trades': 500, 'PF': 1.319, 'R': np.float64(91.8), 'expR': np.float64(0.184), 't': np.float64(2.12), 'maxDD_R': -22.1}
| indice | trades | PF | R | t |
|---|---|---|---|---|
| AEX | 86 | 1.658 | 27.1 | 1.76 |
| ASX200 | 66 | 0.816 | -9.7 | -0.56 |
| CAC40 | 69 | 2.127 | 29.0 | 2.25 |
| IBEX35 | 63 | 1.734 | 21.0 | 1.43 |
| N225 | 68 | 1.271 | 11.1 | 0.69 |
| NZ50 | 76 | 0.967 | -1.7 | -0.11 |
| TSX | 72 | 1.318 | 15.0 | 0.7 |

S2 original en indices nuevos: PF agregado 1.19, 86% de indices con PF > 1 -> **NO GENERALIZA**

Variante M1 salida RSI>70: R/|DD| 4.15 frente a 2.22 del original -> **SE ADOPTA**
