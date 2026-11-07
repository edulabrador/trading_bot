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
| `demo/EMA100_GBPJPY_H1_v6.mq4` con `Stop_Loss=127`, `Take_Profit=243`, `Magic_Number=43899` | EURJPY H1 | 43899 | Segundo candidato (paso la validacion en otros pares) |
| `demo/RSI2_Indices_D1.mq4` | S&P 500 D1 (US500 o similar) | 22001 | **S2: candidato principal** (estrategia nueva) |
| `demo/RSI2_Indices_D1.mq4` | Nasdaq 100 D1 (US100) | 22002 | S2 |
| `demo/RSI2_Indices_D1.mq4` | DAX D1 (GER40) | 22003 | S2 |

Si la validacion en otros pares (`backtests/research/RESULTADOS.md`) aprueba
algun bot en pares nuevos, anadelo tambien en esos pares. Para eso hay que
darle un magic distinto y anadirlo a `bots.json`.

- **Lotes:** 0.01 en todos, para que el resultado en pips sea comparable.
- **Broker:** el mismo que usarias en real, con hora de servidor GMT+2/GMT+3.
  Apunta el spread tipico de cada par.

## Antes de la demo: comprobar el EA en el Strategy Tester

Antes de dejarlo correr en demo, comprueba que el `.mq4` hace lo mismo que el
backtest en Python:

1. Compila el EA en MetaEditor.
2. Pasalo por el Strategy Tester de MT4 con datos de tu broker, en un periodo
   que este en el backtest (por ejemplo 2024-2025) y con el mismo par y
   timeframe.
3. En la pestana **Report**, haz clic derecho, elige **Save as Report** y guarda
   el `.htm`.
4. Compara:

```bash
python forward/tester_compare.py StrategyTester.htm --magic 43898 --tol-hours 2    # EMA100 v6 (H1)
python forward/tester_compare.py StrategyTester.htm --magic 22001 --tol-hours 48   # S2-M1 en S&P 500 (D1)
```

Empareja cada trade de MT4 con el del backtest por hora de entrada y da un
veredicto:
- **OK:** al menos el 90% de los trades coinciden, y salen en el mismo momento.
- **REVISAR:** coincide entre el 70% y el 90%.
- **NO COINCIDE:** menos del 70%.

Ademas guarda un CSV con el detalle, incluidas las filas "solo en MT4" y "solo en
backtest". Las causas tipicas de diferencias son:
- la hora del servidor (prueba con `--tol-hours` mayor, o compara con otra zona
  horaria);
- el corte de la vela diaria en los indices;
- festivos y horario del CFD;
- el spread del broker (pequenas diferencias de precio son normales).

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
| EMA100 v6 (GBPJPY y EURJPY) | ~25 cada uno | ~10 meses |
| USDJPY solo compras | ~15 | ~16 meses |
| EURUSD R2c | ~5 | ~4 anios |
| GBPJPY H4 original | ~50 | ~5 meses |
| S2 RSI(2) (por indice) | ~7 (unos 20 entre los tres) | ~3 anios por indice; ~1 anio los tres juntos |

Con tan pocos trades, incluso 12 meses de forward dan una senal debil. El
forward sirve sobre todo para detectar pronto un bot que se porta peor de lo
esperado (la regla de alerta) y para medir costes reales. Que salga bien un
anio no demuestra que el bot tenga ventaja.

Para los indices (S2), `check_forward.py` compara el **% de variacion por
trade** en lugar de pips (`"unidad": "pct"` en `bots.json`).

## Que mas mirar

- **Spreads y slippage reales** frente a los del backtest (2.0 a 2.5 pips en
  pares JPY, 1.0 en EURUSD).
- **Swap:** el EMA100 mantiene compras de GBPJPY una media de 8 dias, y el
  backtest supone que el swap es neutro o favorable.
- **Trades que no coinciden** con lo que haria el backtest en esas mismas
  fechas. Puedes descargar los datos de esos meses con `backtests/dukascopy.py`
  y correr el backtest para compararlos uno a uno.
