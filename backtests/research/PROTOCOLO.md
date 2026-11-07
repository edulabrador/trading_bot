# Protocolo de mejora sin sobreoptimizar

El objetivo es mejorar los bots sin fabricar una curva bonita en el backtest.
Si se prueban suficientes variantes, alguna saldra rentable por azar. Por eso
las reglas se fijan **antes** de ver ningun resultado y no se cambian despues.

## Datos

- **Desarrollo:** todo lo anterior al **10 de julio de 2023**, dividido en
  dos mitades: A (2006 a 2014) y B (2015 a julio de 2023).
- **Holdout:** desde el **10 de julio de 2023** (la fecha en que los EAs se
  subieron al repo) hasta el final de los datos. No se usa para elegir nada.

Aviso de honestidad: el resultado del holdout del bot **original** ya se vio en
el analisis previo. Lo que no se ha visto es el holdout de ninguna variante.

## Variantes de la ronda 1

Son las mismas para todos los bots, con motivo estructural y sin optimizar
sus parametros:

| Variante | Que cambia | Por que |
|---|---|---|
| V1 SL/TP por ATR | SL y TP = multiplo del ATR(14) diario del dia anterior | 20 anios de pips fijos ignoran que la volatilidad cambia mucho. El multiplo se **calibra** para que la distancia mediana en desarrollo sea la del original, no para maximizar beneficio |
| V2 tendencia D1 | Solo largos si el cierre diario esta por encima de su SMA200, solo cortos si esta por debajo | Filtro de tendencia estandar, con un parametro clasico y no ajustado |
| V3 = V1 + V2 | Las dos cosas a la vez | |
| V4 sin salida por senal | Solo SL/TP | Comprueba si el indicador de salida aporta algo |
| V5 solo largos (pares JPY) | Solo compras | En pares contra el yen el swap favorece a los largos (carry) |

## Reglas para aceptar una variante (todas, solo con datos de desarrollo)

1. Al menos 100 trades.
2. PF >= 1.10 en todo el desarrollo.
3. PF >= 1.00 en **cada** mitad (A y B).
4. Robustez: con todos los parametros a +-20% a la vez (30 combinaciones),
   PF > 1 en al menos el 80%.
5. La entrada supera a entradas aleatorias (con los mismos filtros, SL/TP y
   salidas) en al menos el 80% de 20 simulaciones.

Si varias variantes pasan, se elige la de mayor PF en desarrollo. Si ninguna
pasa, el bot se declara **no rescatable** en esa ronda.

## Holdout

Solo se revela (`--reveal`) para la variante elegida y para el original, y
una sola vez por bot. Si la variante tambien funciona en el holdout (PF > 1),
se considera candidata para demo. Con unos 100 trades no puede ser
estadisticamente concluyente: es una condicion necesaria, no suficiente.

Una vez visto el holdout de un bot, no se itera mas sobre ese bot con esos
datos: cualquier cambio posterior estaria contaminado.

## Rondas siguientes

Solo si ninguna variante pasa en desarrollo. Las nuevas ideas se anotan aqui
antes de probarlas, y cada variante probada queda registrada en
`logs/variantes.csv` (tambien las que fallan), para que se sepa cuantas
pruebas hubo en total.

## Ronda 2 (solo EURUSD H1), anotada antes de ejecutarla

En la ronda 1 ninguna variante de EURUSD paso las reglas. La unica senal
prometedora fue quitar la salida por RVI (V4: PF 1.22 en desarrollo, positiva
en ambas mitades), que fallo solo por robustez (63% de combinaciones con PF > 1,
el minimo es 80%). Hipotesis: el giro del RVI en H1 cierra los trades por ruido,
y sin el, el SL/TP pasa a decidir. Variantes (con las mismas reglas):

| Variante | Que cambia |
|---|---|
| R2a | V4 + filtro de tendencia D1 SMA200 |
| R2b | V4 + SL/TP por ATR diario (multiplos calibrados como en V1) |
| R2c | V4 + SL/TP por ATR + tendencia D1 |

Los otros tres bots no pasan a ronda 2: los dos de GBPJPY y el de USDJPY ya
tuvieron una variante elegida y su holdout revelado (ver resultados).
