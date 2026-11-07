# Pruebas exigentes y mejoras de EMA100 v6 y S2 (registro previo)

Escrito el 7 de noviembre de 2026, **antes de ejecutar nada de lo que sigue**.
El holdout (desde el 10/07/2023) del EMA100 original y de S2 original ya se ha
visto. Por eso las mejoras se eligen solo con datos de desarrollo y se validan
en **mercados nunca mirados**.

## Parte 1. Pruebas exigentes (diagnostico, sin ajustar nada)

Su objetivo es encontrar puntos debiles, no elegir parametros. Se anotan las
senales de alarma y no se cambia la estrategia por ellas, salvo un fallo grave
(por ejemplo, que deje de ser rentable con un retraso de ejecucion realista).

### EMA100 v6 (GBPJPY H1)
1. **Zona horaria del broker:** desplazar la hora de las velas -2, -1, +1 y +2
   horas (servidores GMT+0 a GMT+5). Cambia que velas caen en la sesion de
   01:00 a 21:00. Alarma: PF < 1 en la mayoria.
2. **Retraso de ejecucion:** entrar una vela H1 mas tarde, y anadir 1 y 3 pips
   de slippage por lado. Alarma: PF < 1.05 con 1 vela de retraso.
3. **Crisis:** resultado en ventanas de estres (sep 2008 - mar 2009, mar 2011,
   ago 2015, jun 2016, mar 2020, 2022, jul-ago 2024). Alarma: alguna ventana
   peor que el drawdown medio del Monte Carlo.
4. **Fuente de datos:** repetir con GBPJPY sintetico (GBPUSD x USDJPY,
   2007-2023), que no comparte las velas de GBPJPY. Alarma: PF < 1.

### S2 (indices D1)
1. **Fuente de datos y corte del dia:** S&P 500 de Yahoo (cierre de la bolsa)
   frente a Dukascopy USA500 (dias UTC), de 2011 a 2025, con las mismas reglas.
   Alarma: PF < 1.3 con Dukascopy.
2. **Ejecucion:** entrar al cierre del dia de la senal, a la apertura siguiente
   (base) o al cierre siguiente (un dia tarde), y anadir slippage de 0.1 ATR por
   lado. Alarma: PF < 1.2 con un dia de retraso.
3. **Crisis:** las mismas ventanas, mas feb 2018, oct-dic 2018 y 2022.
4. **Walk-forward:** reoptimizar rsi_lo {5, 10, 15} x sma_exit {3, 5, 10} con 5
   anios, probar el siguiente. Alarma: eficiencia < 0.5.
5. **Financiacion del CFD:** coste por noche = nominal x (tipo de referencia +
   2.5%) / 365, con tipos aproximados por anio (Fed para indices USA, BCE para
   el DAX). Se resta de cada trade en R. Alarma: PF < 1.3 tras financiacion.
6. **Mas simulaciones:** 100 entradas aleatorias y 150 combinaciones de
   parametros.

## Parte 2. Mejoras de S2

Variantes con motivo publicado o de gestion de riesgo, fijadas ahora:

| Variante | Cambio |
|---|---|
| M1 | Salida cuando RSI(2) > 70 en lugar de cierre > SMA(5) (salida alternativa de Connors) |
| M2 | Stop de emergencia a 3 x ATR(20) desde la entrada (ahora no tiene ninguno) |
| M3 | No entrar si la volatilidad (ATR(20)/precio) esta por encima de su percentil 90 de los ultimos 252 dias |
| M4 | Cierre por tiempo a los 10 dias si no ha salido antes |

**Seleccion (solo desarrollo: S&P 500, Nasdaq 100 y DAX hasta el 09/07/2023):**
una variante es candidata si mejora en al menos un 10% el cociente (R total /
|drawdown maximo en R|) frente a S2 original **y** mantiene PF >= 1.5. Entre las
candidatas se elige la de mayor t-stat.

**Validacion (mercados nunca vistos: FTSE 100, Euro Stoxx 50, Nikkei 225, CAC 40
y ASX 200, todo el periodo disponible):**
- S2 original **generaliza** si el PF agregado es >= 1.2 y al menos el 60% de los
  indices tiene PF > 1. Si generaliza, se pueden anadir **todos** los indices que
  cumplan la regla de datos (no solo los que salgan mejor).
- La variante elegida se adopta solo si en los indices nuevos tambien mejora el
  cociente R / |drawdown| frente al original, y tiene PF agregado > 1.

## Parte 3. Tamano por volatilidad en el EMA100

En vez de lotes fijos, cada trade pesa w = ATR(20) diario mediano / ATR(20)
diario en la entrada, limitado entre 0.5 y 2. La senal no cambia: es gestion
del riesgo. Se adopta si en desarrollo mejora al menos un 10% el cociente
(beneficio / |drawdown maximo|), **y** en el holdout ese cociente no es peor que
con lotes fijos. El holdout del EMA100 con lotes fijos ya se conoce; el de esta
variante, no.

## Enmienda: indices de validacion (antes de ejecutar la validacion)

Escrita despues de elegir la variante (M1) y **antes** de ejecutar la
validacion. Dukascopy empezo a cortar todas las conexiones y solo llegaron 3
de los 95 archivos de indices nuevos. Por eso se usa un conjunto coherente de
indices Yahoo publicado en GitHub (`hodacnghia/Graduation-thesis`), que cubre
de 2006 a mayo de 2018.

Regla mecanica para elegir la lista, sin mirar resultados: indices amplios de
mercados desarrollados, con OHLC y al menos 3,000 sesiones desde 2006, sin
incluir indices de EE. UU. (se solapan con S&P 500 y Nasdaq).

- **Resultado:** Nikkei 225, CAC 40, ASX 200, AEX, IBEX 35, S&P/TSX y NZX 50.
- **Excluidos por falta de datos:** FTSE 100 (300 sesiones) y Hang Seng (1,235).
- **Euro Stoxx 50:** no hay datos OHLC completos.
- **Spread fijo:** Nikkei 10, CAC 1.5, ASX 2, AEX 0.15, IBEX 5, TSX 5, NZX 50 5
  puntos (en torno al 0.02-0.05% del precio).

Las reglas de generalizacion y de adopcion de la variante no cambian.

## Resultados (7-8 de noviembre de 2026)

Informes: [`../reports/exigentes_ema100.md`](../reports/exigentes_ema100.md),
[`../reports/exigentes_s2.md`](../reports/exigentes_s2.md),
[`../reports/s2_validacion_indices_nuevos.md`](../reports/s2_validacion_indices_nuevos.md),
[`../reports/s2_m1_indices_rsi2.md`](../reports/s2_m1_indices_rsi2.md).

### EMA100 v6: ninguna alarma, pero sensible al retraso

| Prueba | Resultado | Alarma |
|---|---|---|
| Zona horaria (GMT+0 a GMT+5) | PF 1.16 a 1.18 en todas; holdout 1.21 a 1.35 | no |
| Slippage de 1 y 3 pips por lado | PF 1.15 / 1.11 | no |
| Entrada 1 vela tarde | PF 1.08 (holdout 1.17); con 3 pips mas, 1.03 | no (umbral 1.05), pero es el punto debil |
| Crisis | Peor ventana: crisis de 2008, -628 pips cerrados y -1,820 de caida flotante. Carry trade de 2024: +293 | no |
| GBPJPY sintetico (otra fuente) | PF 1.10 frente a 1.08 real en 2007-2023 | no |
| Tamano por volatilidad | Desarrollo: cociente 1.84 frente a 1.07; holdout: 1.46 frente a 2.40 | **no se adopta** (empeora en holdout) |

### S2: robusta en todo menos en el slippage alto

| Prueba | Resultado | Alarma |
|---|---|---|
| Yahoo frente a Dukascopy (2012-2025) | PF 2.34 frente a 2.30 | no |
| Al cierre / apertura / un dia tarde | PF 1.89 / 1.88 / 1.56 | no |
| Slippage de 0.1 ATR por lado (unas 10 veces el spread) | PF 1.31 | no, pero se come la mitad del beneficio |
| Crisis | COVID -13.5 R, feb 2018 -10.8 R, oct-dic 2018 -8.7 R, ago 2011 -8.2 R; 2008: sin trades (el filtro SMA200 la dejo fuera) | dentro del Monte Carlo |
| Walk-forward | 10/13 anios positivos, eficiencia 1.04 | no |
| Financiacion del CFD | PF 1.71 (holdout 2.17), 0.048 R por trade | no |
| 100 entradas aleatorias / 150 combinaciones | Supera al 100% / PF > 1 en 150/150 (desarrollo y holdout) | no |

### Mejoras de S2

- **Seleccion en desarrollo:** M1 (salida RSI(2) > 70) cociente 9.85 frente a 6.94; M3 (filtro de volatilidad) 8.62. M2 (stop) y M4 (cierre por tiempo) empeoran. Se elige **M1** por t-stat.
- **Validacion en 7 indices nunca vistos (2006-2018):**
  - S2 original: PF agregado 1.19, positiva en 6/7. Se queda a una centesima del umbral (1.2): **no generaliza** con la regla estricta.
  - **M1: PF 1.32, t = 2.12, cociente 4.15 frente a 2.22 -> se adopta.**
- **S2 con M1 en sus mercados:** desarrollo PF 2.12 (t = 4.7); holdout PF 2.19 (91 trades). Con financiacion, PF 1.92 (holdout 1.80). Probabilidad de perder en un anio: 11%.

No se anaden los indices nuevos a la cartera: la regla para anadirlos se
aplicaba a S2 original, y esta no generalizo.
