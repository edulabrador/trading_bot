# Resultados de la busqueda de mejoras (noviembre de 2026)

Protocolo: [`PROTOCOLO.md`](PROTOCOLO.md). Registro de todas las variantes
probadas: [`logs/variantes.csv`](logs/variantes.csv) (25 variantes en total,
contando los originales). Holdout revelado: [`logs/holdout.csv`](logs/holdout.csv).

- **Desarrollo:** hasta el 9 de julio de 2023.
- **Holdout:** del 10 de julio de 2023 a octubre de 2026.

## Conclusion

**Ninguna mejora se ha sostenido de forma convincente en el holdout.** El unico
bot que sigue siendo candidato es el EMA100 de GBPJPY H1 **original** (v6, que
es el original sin la salida AO, con resultados identicos). Ninguna de las
variantes probadas lo mejora.

| Bot | Variante elegida por las reglas | Holdout del original | Holdout de la variante | Veredicto |
|---|---|---|---|---|
| EMA100 GBPJPY H1 | V2 tendencia D1 SMA200 | 80 trades, PF 1.28, +2,204 | 65 trades, PF 1.02, +153 | La variante empeora. **Se queda el original (v6)** |
| GBPJPY H4 | V5 solo largos | 120 trades, PF 0.85, -1,048 | 59 trades, PF 0.74, -856 | **No rescatable** |
| USDJPY H4 | V5 solo largos | 84 trades, PF 0.84, -433 | 33 trades, PF 1.07, +77 | Mejora, pero sin significacion (t = 0.15). **No es suficiente** |
| EURUSD H1 | Ninguna (rondas 1 y 2) | 137 trades, PF 0.78, -321 | sin revelar | **No rescatable con estas reglas** |

## Detalle por bot (datos de desarrollo)

PF = profit factor. A = 2006 a 2014, B = 2015 a julio de 2023. Robustez = %
de 30 combinaciones con todos los parametros a +-20% que tienen PF > 1. Azar =
% de simulaciones con entradas aleatorias que el bot supera.

### EMA100 GBPJPY H1

| Variante | Trades | PF | t | PF A | PF B | Robustez | Azar | Pasa |
|---|---|---|---|---|---|---|---|---|
| V0 original | 450 | 1.14 | 1.33 | 1.05 | 1.28 | 100% | 90% | si |
| V1 SL/TP por ATR | 373 | 1.15 | 1.14 | 1.02 | 1.33 | 93% | 100% | si |
| V2 tendencia D1 | 236 | 1.17 | 1.17 | 1.31 | 1.06 | 97% | 95% | si |
| V3 ATR + tendencia | 226 | 1.13 | 0.85 | 1.27 | 1.02 | 90% | 100% | si |
| V4 sin salida AO | 450 | 1.14 | 1.33 | 1.05 | 1.28 | 100% | 90% | si (identica a V0) |

Todas pasan y ninguna mejora de verdad al original: las diferencias de PF son
de 0.01 a 0.03. La regla eligio V2, que en el holdout rindio mucho peor que el
original. **Leccion:** cuando el original ya pasa, elegir entre variantes que
difieren en centesimas de PF es elegir ruido.

### GBPJPY H4

| Variante | Trades | PF | t | PF A | PF B | Robustez | Azar | Pasa |
|---|---|---|---|---|---|---|---|---|
| V0 original | 924 | 1.19 | 1.83 | 0.98 | 1.54 | 100% | 100% | no (A < 1) |
| V1 SL/TP por ATR | 862 | 1.14 | 1.23 | 0.95 | 1.48 | 100% | 100% | no |
| V2 tendencia D1 | 492 | 1.13 | 0.91 | 1.07 | 1.21 | 100% | 90% | si |
| V3 ATR + tendencia | 473 | 1.09 | 0.62 | 0.97 | 1.31 | 100% | 85% | no |
| V4 sin salida | 798 | 1.24 | 2.01 | 1.11 | 1.44 | 100% | 100% | si |
| V5 solo largos | 412 | 1.43 | 2.52 | 1.18 | 1.84 | 100% | 100% | si, elegida |

V5 parecia la mejor variante de todo el estudio en desarrollo (t = 2.52), y en
el holdout perdio. Aviso: el resultado de "solo largos" en ese periodo ya se
habia visto en la tabla de presets del analisis anterior, asi que este holdout
no estaba del todo limpio para esa variante. El resultado no cambia.

### USDJPY H4

| Variante | Trades | PF | t | PF A | PF B | Robustez | Azar | Pasa |
|---|---|---|---|---|---|---|---|---|
| V0 original | 503 | 1.13 | 0.97 | 0.97 | 1.35 | 73% | 80% | no |
| V1 SL/TP por ATR | 505 | 0.97 | -0.21 | 0.80 | 1.20 | 60% | 40% | no |
| V2 tendencia D1 | 233 | 1.33 | 1.53 | 0.96 | 1.90 | 100% | 65% | no |
| V3 ATR + tendencia | 233 | 1.22 | 1.06 | 0.98 | 1.54 | 100% | 60% | no |
| V4 sin salida | 276 | 1.39 | 2.42 | 1.31 | 1.48 | 97% | 100% | si |
| V5 solo largos | 250 | 1.39 | 1.86 | 1.33 | 1.46 | 100% | 100% | si, elegida |

V4 y V5 empataron (PF 1.389 frente a 1.390). La regla eligio V5, que gano 77
pips en 33 trades en el holdout. Es positivo, pero con tan pocos trades no se
distingue del azar. El holdout de V4 no se ha mirado.

### EURUSD H1

| Variante | Trades | PF | t | PF A | PF B | Robustez | Azar | Pasa |
|---|---|---|---|---|---|---|---|---|
| V0 original | 581 | 0.92 | -0.63 | 0.84 | 1.05 | 23% | 35% | no |
| V1 SL/TP por ATR | 581 | 0.92 | -0.63 | 0.84 | 1.05 | 17% | 30% | no (identica: el SL/TP nunca se toca) |
| V2 tendencia D1 | 292 | 0.93 | -0.41 | 0.85 | 1.05 | 27% | 25% | no |
| V3 ATR + tendencia | 292 | 0.93 | -0.41 | 0.85 | 1.05 | 20% | 25% | no |
| V4 sin salida RVI | 144 | 1.22 | 1.18 | 1.11 | 1.49 | 63% | 95% | no (robustez) |
| R2a sin salida + tendencia | 106 | 1.41 | 1.76 | 1.59 | 1.16 | 97% | 75% | no (azar) |
| R2b sin salida + ATR | 102 | 1.13 | 0.56 | 0.94 | 1.55 | 67% | 80% | no |
| R2c sin salida + ATR + tendencia | 80 | 1.91 | 2.63 | 2.05 | 1.73 | 100% | 100% | no (menos de 100 trades) |

R2c tiene las mejores cifras de todo el estudio, pero con solo 80 trades en 17
anios (menos de 5 al anio) y no cumple el minimo de trades fijado de antemano.
No se ha revelado su holdout. Es la ultima de 8 variantes probadas sobre este
bot, asi que hay que descontar el efecto de haber buscado. Como mucho es una
hipotesis para un forward en demo.

## Lo que se aprende

1. **Simplificar ayuda en desarrollo, pero no se ha confirmado fuera.** Quitar
   la salida por indicador mejoro tres de los cuatro bots en desarrollo, y
   "solo largos" en pares contra el yen tambien. En el holdout solo se pudo
   comprobar en dos casos, con un resultado malo (GBPJPY H4) y otro
   insignificante (USDJPY H4).
2. **El SL/TP por ATR no ayudo en ningun bot.**
3. **El filtro de tendencia D1** suaviza el drawdown, pero no mejora de forma
   consistente.
4. **Una buena cifra en desarrollo no garantiza nada.** La mejor variante en
   desarrollo de la ronda 1 (GBPJPY H4 V5, t = 2.52) perdio en el holdout.
   Esto refuerza que estos bots, generados por EA Studio, no tienen una ventaja
   estable.

## Siguiente paso honesto

Con estos datos ya no se puede seguir iterando sin hacer trampa: el holdout de
tres bots ya esta revelado. La unica validacion que queda es un **forward en
demo**, con datos que todavia no existen:

- EMA100 v6 (candidato principal).
- Opcionalmente, como hipotesis: USDJPY H4 V5 (solo largos) y EURUSD R2c.

## Bateria completa de los candidatos (noviembre de 2026)

Los tres candidatos pasaron por `run_tests.py` completo, con corte en el
10/07/2023. Informes: [`cand_ema100_v6.md`](../reports/cand_ema100_v6.md),
[`cand_usdjpy_buyonly.md`](../reports/cand_usdjpy_buyonly.md),
[`cand_eurusd_r2c.md`](../reports/cand_eurusd_r2c.md) y cartera
[`cartera_candidatos.md`](../reports/cartera_candidatos.md).

El holdout de EURUSD R2c se revelo **fuera del protocolo**, a peticion del
usuario, y queda marcado como exploratorio en `logs/holdout.csv`.

| | EMA100 v6 | USDJPY solo compras | EURUSD R2c |
|---|---|---|---|
| Trades (total / holdout) | 530 / 80 | 283 / 33 | 101 / 21 |
| PF total | 1.16 | 1.34 | 1.75 |
| PF holdout | **1.28** | 1.07 | 1.02 |
| Pips holdout | **+2,204** | +77 | +40 |
| t-stat total | 1.64 | 1.77 | 2.51 |
| Drawdown maximo (pips) | -6,171 | -972 | -2,104 |
| Tiempo maximo sin nuevo maximo | 3,431 dias | 1,842 dias | 1,439 dias |
| Entrada vs azar (total / holdout) | percentil 77 / 55 | 93 / 57 | 100 / 80 |
| Parametros +-20%: PF > 1 (total / holdout) | 150/150 / 150/150 | 150/150 / 147/150 | 145/150 / 60/150 |
| Walk-forward: anios positivos, eficiencia | 10/17, 0.45 | 10/16, 0.60 | 11/16, 0.21 |
| P(perder en 1 anio) | 33% | 35% | 27% |
| PF con spread de 6 pips | 1.13 | 1.13 | 1.70 |

Nota: el benchmark aleatorio del EMA100 da ahora percentil 77, y no 88 como en
el primer informe, porque las entradas aleatorias respetan tambien el filtro
EMA100. Es la comparacion mas justa.

**Lectura:**

- **EMA100 v6** es el unico con un holdout claramente positivo y totalmente
  robusto ante cambios de parametros, tambien en el holdout. Su debilidad
  sigue siendo el riesgo (9.4 anios sin maximos) y que su entrada apenas
  supera al azar.
- **USDJPY solo compras** y **EURUSD R2c** brillan en el periodo con el que se
  eligieron y quedan planos en el holdout. Es el patron tipico de una mejora
  que se ajusto al pasado. En EURUSD R2c solo 60 de 150 combinaciones de
  parametros son rentables en el holdout.
- **Cartera (0.01 lotes cada uno):** las correlaciones mensuales entre bots son
  casi nulas (-0.02 a 0.13). El drawdown de la cartera (-351) es la mitad de la
  suma de los individuales (-710), y solo 2 de 21 anios son negativos. Pero en
  el holdout la cartera gana +164, de los que +154 son del EMA100. La
  diversificacion reduce el riesgo, no crea ventaja.

## Validacion en otros mercados (sin cambiar reglas)

Reglas fijadas antes en [`PROTOCOLO.md`](PROTOCOLO.md). Registro completo en
`logs/cross_market.csv`. Los cruces JPY son sinteticos (EURJPY = EURUSD x
USDJPY hasta octubre de 2026; AUDJPY y CADJPY hasta marzo de 2023). Los pares
USD son datos Dukascopy de 2007 a marzo de 2023.

| Bot | Pares nuevos con PF > 1 | PF agregado | Generaliza |
|---|---|---|---|
| EMA100 v6 | 3/3 (EURJPY 1.10, AUDJPY 1.09, CADJPY 1.04) | 1.08 | **si** |
| USDJPY H4 original | 1/3 | 1.02 | no |
| USDJPY H4 solo compras | 2/3 | 1.04 | no |
| GBPJPY H4 original | 3/3 | 1.08 | si (historico) |
| GBPJPY H4 solo compras | 3/3 | 1.09 | si (historico) |
| EURUSD H1 original | 1/5 | 0.91 | no |
| EURUSD H1 R2c | 3/5 | 0.96 | no |

En EURJPY, el unico par nuevo con datos hasta 2026, el periodo desde el
10/07/2023 confirma la diferencia:

| Bot en EURJPY | Hasta 09/07/2023 | Desde 10/07/2023 |
|---|---|---|
| EMA100 v6 | 418 trades, PF 1.06 | **86 trades, PF 1.34, +2,221 pips** |
| GBPJPY H4 original | 800 trades, PF 1.09 | 125 trades, PF 0.80, -1,036 |
| GBPJPY H4 solo compras | 367 trades, PF 1.12 | 63 trades, PF 0.67, -918 |

EMA100 v6 en los tres pares nuevos, con la bateria completa (informes
`ema100_v6_eurjpy.md`, `ema100_v6_audjpy.md`, `ema100_v6_cadjpy.md`):

| | EURJPY | AUDJPY | CADJPY |
|---|---|---|---|
| PF total | 1.10 | 1.09 | 1.04 |
| Supera al azar (percentil) | 82 | 60 | 33 |
| Parametros +-20% con PF > 1 | 142/150 | 143/150 | 132/150 |
| Walk-forward (anios positivos, eficiencia) | 10/16, 0.44 | 6/13, -0.19 | 4/13, -0.24 |
| P(perder en 1 anio) | 45% | 40% | 45% |

Conclusion en [`../reports/CARTERA.md`](../reports/CARTERA.md).
