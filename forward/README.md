# Forward en demo

El holdout del backtest ya esta usado. La unica forma limpia que queda de
saber si un bot tiene ventaja es dejarlo operar con datos que todavia no
existen. Esta carpeta tiene lo necesario para hacerlo con reglas fijadas
**antes** de empezar.

## Que poner en demo

Cada bot en su propio grafico de la misma cuenta demo, con su magic number:

| EA | Grafico | Magic | Papel |
|---|---|---|---|
| `demo/EMA100_GBPJPY_H1_v6.mq4` | GBPJPY H1 | 43898 | Candidato principal |
| `demo/USDJPY_H4_38025241_buyonly.mq4` | USDJPY H4 | 38025242 | Hipotesis |
| `demo/R_EURUSD_H1_R2c.mq4` | EURUSD H1 | 31422196 | Hipotesis |
| `GBPJPY_H4_35839595.mq4` (original) | GBPJPY H4 | 35839595 | Control: el backtest dice que ya no funciona |

Si la validacion en otros pares (`backtests/research/RESULTADOS.md`) aprueba
algun bot en pares nuevos, anadelo tambien en esos pares. Para eso hay que
darle un magic distinto y anadirlo a `bots.json`.

- **Lotes:** 0.01 en todos, para que el resultado en pips sea comparable.
- **Broker:** el mismo que usarias en real, con hora de servidor GMT+2/GMT+3.
  Apunta el spread tipico de cada par.

## Cada mes (o cada trimestre)

1. En MetaTrader, abre la pestana **Historial de cuenta**, haz clic derecho y
   elige **Todo el historial**.
2. Ejecuta el script `forward/ExportTrades.mq4` (compilalo antes en MetaEditor).
   Genera `MQL4/Files/forward_trades.csv`.
3. Analizalo:

```bash
python forward/check_forward.py ruta/a/forward_trades.csv --desde FECHA_INICIO_DEMO
```

Para cada bot compara el resultado con la distribucion que espera el backtest
para ese mismo numero de trades (bootstrap del backtest completo y del
holdout), y aplica estas reglas:

| Situacion | Decision |
|---|---|
| Menos de 20 trades | Seguir en demo: no hay datos para decidir |
| Resultado por debajo del percentil 5 de lo esperado | **Alerta:** parar y revisar (ejecucion, spreads, swaps, cambio de mercado) |
| 12 meses o mas, PF > 1 y al menos en el percentil 20 | Candidato a real con lote minimo |
| Cualquier otro caso | Seguir en demo |

Estas reglas estan en el codigo (`MIN_TRADES`, `ALERT_PCT`, `PROMOTE_PCT`,
`PROMOTE_MONTHS`). **No las cambies despues de ver resultados.**

## Cuanto hay que esperar

| Bot | Trades al anio | 20 trades en |
|---|---|---|
| EMA100 v6 | ~25 | ~10 meses |
| USDJPY solo compras | ~15 | ~16 meses |
| EURUSD R2c | ~5 | ~4 anios |
| GBPJPY H4 original | ~50 | ~5 meses |

Con tan pocos trades, incluso 12 meses de forward dan una senal debil. El
forward sirve sobre todo para detectar pronto un bot que se porta peor de lo
esperado (la regla de alerta) y para medir costes reales. Que salga bien un
anio no demuestra que el bot tenga ventaja.

## Que mas mirar

- **Spreads y slippage reales** frente a los del backtest (2.0 a 2.5 pips en
  pares JPY, 1.0 en EURUSD).
- **Swap:** el EMA100 mantiene compras de GBPJPY una media de 8 dias, y el
  backtest supone que el swap es neutro o favorable.
- **Trades que no coinciden** con lo que haria el backtest en esas mismas
  fechas. Puedes descargar los datos de esos meses con `backtests/dukascopy.py`
  y correr el backtest para compararlos uno a uno.
