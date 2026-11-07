# Resumen de las evaluaciones

Evaluacion de 4 bots (noviembre de 2026). Todas las cifras son en pips salvo
que se indique otra cosa. PF = profit factor (ganancias brutas / perdidas
brutas). OOS = fuera de muestra, es decir, datos que no se usaron para crear o
ajustar el bot.

| Bot | Periodo | Trades | PF total | PF OOS reciente | Veredicto |
|---|---|---|---|---|---|
| `R_EURUSD_H1.mq4` | 2007 a feb 2023 | 569 | 0.94 | sin datos | **No rentable** |
| `USDJPY_H4_38025241.mq4` | 2007 a feb 2026 | 569 | 1.10 a 1.39 segun la fuente de datos | 0.87 desde jul 2023 | **No rentable hoy** |
| `GBPJPY_H4_35839595.mq4` | 2007 a feb 2026 | 993 | 1.24 | 0.92 desde jul 2023 | **No rentable hoy** |
| EA GBPJPY H1 EMA100 BUY ONLY v5 | 2006 a oct 2026 | 530 | 1.16 | 1.23 desde jul 2022 | **Ventaja fina y riesgo alto** |

## Busqueda de mejoras (noviembre de 2026)

Se probaron 25 variantes con un protocolo cerrado: reglas fijadas de antemano,
datos de desarrollo hasta julio de 2023 y holdout reservado desde entonces.
Detalle en [`../research/RESULTADOS.md`](../research/RESULTADOS.md).

**Ninguna mejora se sostuvo de forma convincente en el holdout.** El EMA100
original (v6, sin la salida AO, con resultados identicos) sigue siendo el unico
candidato. GBPJPY H4 y EURUSD H1 no son rescatables con estas reglas. USDJPY H4
"solo largos" gano 77 pips en 33 trades en el holdout, que no es suficiente.

Informes completos generados con `run_tests.py` (holdout desde el 10/07/2023
para los EAs MQ4): [`mq4_eurusd_h1.md`](mq4_eurusd_h1.md),
[`mq4_usdjpy_h4.md`](mq4_usdjpy_h4.md), [`mq4_gbpjpy_h4.md`](mq4_gbpjpy_h4.md),
[`ea_gbpjpy_h1_ema100_v5.md`](ea_gbpjpy_h1_ema100_v5.md).

## Estrategia nueva que pasa: S2 (RSI(2) en indices)

De tres estrategias nuevas registradas antes de ver datos
([`../research/NUEVAS_ESTRATEGIAS.md`](../research/NUEVAS_ESTRATEGIAS.md)),
solo **S2** pasa: reversion a la media en S&P 500, Nasdaq 100 y DAX diarios.
PF 1.72 en desarrollo y **2.57 en el holdout** (97 trades), con correlacion
0.01 con el EMA100. Informe: [`s2_indices_rsi2.md`](s2_indices_rsi2.md). EA para
demo: `demo/RSI2_Indices_D1.mq4`.

## Cartera por merito individual

Ver [`CARTERA.md`](CARTERA.md): con el criterio de que cada bot sea rentable
por separado, la cartera queda en **EMA100 v6 en GBPJPY H1** (candidato para
real tras la demo) y **EMA100 v6 en EURJPY H1** (en demo). Ningun otro bot pasa.

## Candidatos para demo (noviembre de 2026)

En [`../../demo/`](../../demo/) hay tres `.mq4` listos para compilar: EMA100 v6
(candidato principal), USDJPY H4 solo compras y EURUSD R2c (hipotesis). Los
tres pasaron por la bateria completa:

| | PF total | PF holdout (desde 10/07/2023) | Pips holdout |
|---|---|---|---|
| EMA100 v6 | 1.16 | **1.28** | **+2,204** |
| USDJPY solo compras | 1.34 | 1.07 | +77 |
| EURUSD R2c | 1.75 | 1.02 | +40 |

Solo el EMA100 v6 mantiene la ventaja fuera de muestra. Las otras dos variantes
se ven muy bien en el periodo con el que se eligieron y quedan planas despues.
Combinar los tres reduce el drawdown a la mitad, pero casi toda la ganancia
reciente sigue viniendo del EMA100. Detalle en
[`../research/RESULTADOS.md`](../research/RESULTADOS.md).

## Los tres EAs MQ4 del repo

Primer analisis: traduccion a Python de cada `.mq4`, con datos H1 de Dukascopy
(2007 a 2023) y H4 de `tohaitrieu/market-history` (hasta febrero de 2026).
Ahora estan en `bots/mq4_*.py` y se evaluan con `run_tests.py` sobre datos de
Dukascopy hasta octubre de 2026: EURUSD PF 0.90 (holdout 0.78), USDJPY PF 1.08
(holdout 0.84), GBPJPY PF 1.15 (holdout 0.85). Como prueba OOS se uso el periodo
posterior a su publicacion (10 de julio de 2023).

- **EURUSD H1**: PF 0.94. Sin costes queda en PF 1.00 exacto. 33 de 36
  variantes de parametros tambien pierden. El SL y el TP de unos 325 pips
  nunca llegan a tocarse: todas las salidas son por el RVI.
- **USDJPY H4**: muy rentable en 2015 a 2019 (PF 1.86 a 2.44) y en perdidas
  desde 2020. El resultado cambia mucho segun la fuente de datos y la hora a la
  que empiezan las velas H4 (PF 1.10 a 1.22 con los mismos precios). Desde su
  publicacion: 56 trades, -227 pips.
- **GBPJPY H4**: es robusto ante cambios de parametros (24 de 24 variantes
  rentables), pero gana casi todo en 2009 y 2016 y llega a encadenar 25
  perdidas seguidas. Desde su publicacion: 104 trades, -418 pips.

Los tres siguen el mismo patron: van muy bien en 2015 a 2019 y se apagan
despues. Encaja con que se optimizaran sobre ese tramo (es una inferencia).

## EA GBPJPY H1 EMA100 BUY ONLY (v5)

Informe completo: [`ea_gbpjpy_h1_ema100_v5.md`](ea_gbpjpy_h1_ema100_v5.md).
Datos: Dukascopy GBPJPY H1 BID/ASK, de enero de 2006 a octubre de 2026, con el
spread real de cada vela. Corte IS/OOS: 11 de julio de 2022.

**Lo bueno**
- Rentable en el historico completo: PF 1.16 y +8,818 pips en 530 trades.
- Rentable despues del corte: PF 1.23 y +2,581 pips en 112 trades.
- Muy robusto: 150 de 150 combinaciones con todos los parametros a +-20%
  tienen PF > 1, y 149 de 150 tambien despues del corte. El mapa SL x TP es
  plano.
- Aguanta costes: PF 1.13 con 6 pips de spread fijo. El swap de las compras le
  favorece.
- Gano 6,236 pips entre 2006 y 2022, aunque GBPJPY cayo 3,906 pips en ese
  periodo.

**Lo malo**
- **La salida por Awesome Oscillator no actua nunca.** El AO supera 3.47 en el
  0.09% de las velas, y su percentil 99 es 1.86. Todas las salidas son por SL
  o TP.
- **La senal de entrada apenas mejora al azar.** Entrando al azar con las
  mismas reglas (EMA100, sesion, SL/TP), el bot queda en el percentil 88 del
  periodo completo y en el 67 despues del corte. La mayor parte del resultado
  viene de la estructura del sistema.
- **Riesgo alto.** Drawdown historico de -6,171 pips (2007 a 2012) y 3,431
  dias (unos 9.4 anios) sin nuevo maximo. En el Monte Carlo, el 1% de peores
  casos llega a -6,824 pips. Hay un 33% de probabilidad de cerrar un anio en
  perdida.
- t-stat de 1.64, no concluyente.
- Despues del corte el viento fue favorable: GBPJPY subio 4,717 pips, y casi
  toda la ganancia OOS es de 2024 (+3,001). 2023, 2025 y 2026 dan -87, +9 y
  +114 pips.
- Walk-forward: 10 de 17 anios positivos, eficiencia 0.52. Reoptimizar no
  mejora a los parametros fijos.

**Recomendacion**
1. Si se usa, con lote pequeno: 0.01 a 0.03 por cada 10,000 de cuenta.
   0.10 lotes supondria un drawdown de unos 4,800, cerca de la mitad de la
   cuenta.
2. Corregir o eliminar la salida por AO para que el codigo refleje lo que el
   bot hace de verdad.
3. Antes de poner dinero, dejarlo 3 a 6 meses en demo con el broker real y
   comparar contra este backtest, sobre todo spreads y swaps.
4. No anadir filtros por dia u hora sacados de las tablas del informe.

## Como reproducirlo

```bash
pip install -r backtests/requirements.txt
python backtests/dukascopy.py GBPJPY --start 2006
python backtests/run_tests.py --bot backtests/bots/ea_gbpjpy_h1_ema100_v5.py \
  --csv backtests/data/GBPJPY_H1.csv --split 2022-07-11 --swap-gbpjpy
```

Con la misma semilla (`--seed 42`) y los mismos datos, los numeros del informe
salen identicos. Si Dukascopy revisa su historico o descargas en otra fecha,
pueden variar ligeramente.
