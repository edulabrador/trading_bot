# Estrategias nuevas sin relacion con el yen (registro previo)

Escrito el 7 de noviembre de 2026, **antes de programar el backtest y antes de
ver ningun resultado**. Los parametros son los valores clasicos publicados para
cada idea, no salen de ninguna optimizacion. No se cambiaran despues de ver
resultados. Si una estrategia falla, se descarta; no se "arregla".

Objetivo: anadir a la cartera fuentes de rentabilidad **distintas** del EMA100
(que es, en la practica, comprar cruces contra el yen en tendencia). Cada
estrategia tiene que ser rentable por si sola.

## Datos

- **Diarios.** Las estrategias de timeframe diario son mas faciles de llevar a
  MT4, mas baratas en costes y permiten usar otros activos.
- **Divisas** (sin pares con yen): EURUSD, GBPUSD, AUDUSD, USDCAD, USDCHF.
  Velas D1 de `tohaitrieu/market-history`, hasta febrero de 2026.
- **Oro:** XAUUSD (Dukascopy). Si no se puede descargar, se usa GOLD D1 de
  `tohaitrieu/market-history`.
- **Indices y petroleo** (Dukascopy D1): S&P 500, Nasdaq 100, DAX y Brent, si
  la descarga termina. Si no, la estrategia de indices queda pendiente.
- **Desarrollo:** hasta el 9 de julio de 2023. **Holdout:** desde el 10 de julio
  de 2023. Es el mismo corte que en el resto del estudio.

## Ejecucion comun

- La senal se calcula al **cierre** del dia; la orden se ejecuta en la
  **apertura** del dia siguiente.
- Una posicion por instrumento.
- **Costes:** se paga el spread completo en cada operacion (mitad al entrar,
  mitad al salir). EURUSD 1.0 pip, GBPUSD 1.5, AUDUSD 1.2, USDCAD 1.8, USDCHF
  1.8, XAUUSD 0.35 USD, S&P 500 0.6 puntos, Nasdaq 100 2.0, DAX 2.0, Brent
  0.05 USD.
- Swap y financiacion de CFDs **no incluidos**. Se estimaran aparte para las
  estrategias que mantienen posiciones mucho tiempo.
- Para poder sumar instrumentos distintos, el resultado de cada trade se mide
  en **R** = beneficio / ATR(20) diario en la entrada.

## S1. Tendencia multi-activo (sistema Turtle 2, clasico)

- **Idea:** el momentum de series temporales (seguir tendencias) es una de las
  primas mejor documentadas en todos los mercados, y suele ganar en las crisis.
  Por eso tiende a estar poco correlacionado con el carry.
- **Entrada:** largo si el cierre supera el maximo de los 55 dias anteriores;
  corto si cae por debajo del minimo de los 55 dias anteriores.
- **Salida:** largo si el cierre cae por debajo del minimo de 20 dias; corto si
  supera el maximo de 20 dias.
- **Stop inicial:** 2 x ATR(20) desde la entrada, comprobado dentro del dia
  (con hueco: se ejecuta a la apertura).
- **Universo:** las 5 divisas, oro, indices y Brent.

## S2. Reversion a la media en indices (RSI(2) de Connors, clasico)

- **Idea:** los indices de bolsa tienden a rebotar tras caidas de pocos dias
  cuando la tendencia de fondo es alcista.
- **Entrada (solo largos):** cierre > SMA(200) y RSI(2) < 10.
- **Salida:** cierre > SMA(5). Sin stop (version clasica).
- **Universo:** S&P 500, Nasdaq 100 y DAX. Como validacion en otros mercados:
  oro.

## S3. Reversion a la media en divisas (la misma logica, en ambos sentidos)

- **Idea:** comprobar si el mismo efecto existe en divisas sin yen. Es una
  hipotesis mas debil.
- **Largo:** cierre > SMA(200) y RSI(2) < 10. **Corto:** cierre < SMA(200) y
  RSI(2) > 90.
- **Salida:** largo cuando el cierre > SMA(5); corto cuando el cierre < SMA(5).
  Sin stop.
- **Universo:** las 5 divisas.

## Reglas para aceptar una estrategia (todas)

Con los trades de todo su universo juntos, en R, y solo con datos de desarrollo:

1. Al menos 100 trades.
2. PF >= 1.10.
3. PF >= 1.00 en cada mitad: A (2007 a 2014) y B (2015 a julio de 2023).
4. PF > 1 en al menos el 60% de los instrumentos.
5. Robustez: con todos los parametros a +-20% a la vez (30 combinaciones), el
   PF agregado es > 1 en al menos el 80%.
6. Supera a entradas aleatorias (misma frecuencia y mismas salidas) en al
   menos el 80% de 20 simulaciones.

Si pasa, se revela el **holdout una sola vez**. Entra en la cartera solo si en
el holdout el PF agregado es > 1 **y** su correlacion mensual con el EMA100 es
menor de 0.3.

## Enmienda de datos (antes de ejecutar S1 y S2)

Escrita despues de la descarga y **antes** de correr S1 y S2. S3 ya se habia
ejecutado (no paso) y no le afecta.

En Dukascopy, el historico diario de indices empieza tarde: S&P 500 y Nasdaq
100 en 2011, DAX en septiembre de 2013 y Brent a finales de 2010. El ano 2026
no existe todavia como archivo anual, asi que esos datos llegan a diciembre de
2025. Cambios:

- **S&P 500:** se usa el indice cash diario de Yahoo (^GSPC), publicado en
  GitHub (`CodeBeckZero/MADDQN` hasta 2019 y `george962/FearGreedIndex` desde
  noviembre de 2019; coinciden en el solape). Cubre de 2007 a octubre de 2026.
- **Nasdaq 100, DAX, oro y Brent:** Dukascopy, con el periodo que haya. Los
  instrumentos que empiezan despues de 2007 tienen menos trades en la mitad A.
- Las reglas de aceptacion no cambian.

## Resultados (7 de noviembre de 2026)

Cada estrategia se ejecuto una sola vez con las reglas de arriba. Registros en
`logs/nueva_S*.json`.

| Estrategia | Trades (desarrollo) | PF | Mitad A / B | Instrumentos con PF > 1 | Robustez | Azar | Veredicto |
|---|---|---|---|---|---|---|---|
| S1 tendencia Turtle | 677 | 1.11 | 1.07 / 1.14 | **5 de 10 (50%)** | 100% | 85% | **No pasa** (regla 4). Holdout no revelado |
| S2 RSI(2) indices | 276 | **1.72** | 1.79 / 1.70 | 3 de 3 | 100% | 100% | **Pasa** |
| S3 RSI(2) divisas | 925 | **1.01** | 1.01 / 1.01 | 3 de 5 | 83% | **70%** | **No pasa**. Holdout no revelado |

**Holdout de S2** (desde el 10/07/2023, revelado una vez): 97 trades, **PF 2.57**,
+41.8 R, t = 3.61, positivo en los tres indices (S&P 500 PF 3.29, Nasdaq 100
2.28, DAX 2.17). Correlacion mensual con el EMA100: **0.01**. Entra en la
cartera.

Pruebas en profundidad: [`../reports/s2_indices_rsi2.md`](../reports/s2_indices_rsi2.md).
