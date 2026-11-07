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
