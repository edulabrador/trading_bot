# Cartera por merito individual (noviembre de 2026)

Criterio: un bot solo entra si es rentable **por separado**, con sus mejoras
fijadas sin optimizar y pasando las pruebas. La cartera no puede depender de
que unos bots compensen a otros.

## Quien entra

| Bot | Par | PF total | PF desde 10/07/2023 | Supera al azar | Generaliza a otros pares | Decision |
|---|---|---|---|---|---|---|
| **EMA100 v6** | **GBPJPY H1** | 1.16 | **1.28** (80 trades) | percentil 77 | si (3 de 3 pares, PF agregado 1.08) | **Entra: candidato principal** |
| EMA100 v6 | EURJPY H1* | 1.10 | **1.34** (86 trades) | percentil 82 | (es uno de los pares de validacion) | **Entra en demo**, no en real todavia |
| EMA100 v6 | AUDJPY H1* | 1.09 | sin datos recientes | percentil 60 | | No: no supera al azar, walk-forward negativo |
| EMA100 v6 | CADJPY H1* | 1.04 | sin datos recientes | percentil 33 | | No: no supera al azar, walk-forward negativo |
| USDJPY H4 solo compras | USDJPY | 1.34** | 1.07 (33 trades) | percentil 93 | **no** (2 de 3, PF agregado 1.04) | No |
| EURUSD H1 R2c | EURUSD | 1.75** | 1.02 (21 trades) | percentil 100 | **no** (3 de 5, PF agregado 0.96) | No |
| GBPJPY H4 (original y solo compras) | GBPJPY | 1.15 | 0.85 / 0.74 | percentil 98 | si en el historico, pero **pierde tambien en EURJPY desde 2023** (PF 0.80) | No: la ventaja se apago |
| USDJPY H4 original | USDJPY | 1.08 | 0.84 | percentil 90 | no (1 de 3) | No |
| EURUSD H1 original | EURUSD | 0.90 | 0.78 | percentil 33 | no (1 de 5) | No |

\* Cruces sinteticos construidos a partir de los pares contra el dolar (el
mismo metodo dio un PF de 1.24 frente a 1.25 con datos reales de GBPJPY).
AUDJPY y CADJPY solo llegan a marzo de 2023.
\*\* Inflado: la variante se eligio mirando esos datos.

EMA100 en EURJPY no cumple del todo las reglas de desarrollo del protocolo:
PF 1.06 hasta julio de 2023, con la mitad 2015-2023 en 0.99. Pero se fijo sin
ningun ajuste (SL/TP escalados por volatilidad) y gana desde 2023. Por eso
entra en demo y no en real.

## La cartera resultante

**EMA100 v6 en GBPJPY H1** como unico bot para real (tras la demo), y **EMA100
v6 en EURJPY H1** en demo, como segundo candidato.

GBPJPY + EURJPY a 0.01 lotes cada uno
([`cartera_ema100_gbpjpy_eurjpy.md`](cartera_ema100_gbpjpy_eurjpy.md)):

| | Trades | Neto | PF | maxDD | Neto desde 10/07/2023 | PF desde 10/07/2023 |
|---|---|---|---|---|---|---|
| GBPJPY | 530 | +617 | 1.16 | -432 | +154 | 1.28 |
| EURJPY | 504 | +297 | 1.10 | -213 | +155 | 1.34 |
| Cartera | 1,034 | +914 | 1.14 | -530 | +310 | 1.31 |

En divisa de cuenta: pips x 0.01 x 7, aproximado, sin swap.

- Cada componente es rentable por separado, y la cartera tambien.
- La diversificacion es limitada: la correlacion mensual entre los dos es 0.53
  (ambos son compras de cruces contra el yen). El drawdown conjunto (-530) es
  solo algo menor que la suma de los individuales (-645).
- La probabilidad de perder en un anio sigue en torno al 34%, y hay 6 anios
  negativos de 21.

## Lo que no se ha conseguido

No hay una cartera de varios bots **distintos** que sean rentables por
separado. Los otros tres EAs, con todas las mejoras que se probaron sin
sobreoptimizar, no pasan: o no generalizan a otros pares, o han dejado de
funcionar desde 2023. Forzar su entrada exigiria ajustarlos a datos ya vistos.

Para diversificar de verdad hacen falta bots nuevos, sobre otros mercados o
con otras logicas (por ejemplo, no comprar siempre cruces contra el yen),
pasados por el mismo protocolo desde el principio.
