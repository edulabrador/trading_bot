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

## Los tres EAs MQ4 del repo

Probados con una traduccion a Python de cada `.mq4`, con datos H1 de Dukascopy
(2007 a 2023) y H4 de `tohaitrieu/market-history` (hasta febrero de 2026).
Esa traduccion no esta en este repo. Como prueba OOS se uso el periodo
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
