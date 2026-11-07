# EAs para forward en demo

Tres `.mq4` generados a partir de la plantilla EA Studio de este repo, con las
variantes que salieron del estudio de mejoras
([`backtests/research/RESULTADOS.md`](../backtests/research/RESULTADOS.md)).
Los EAs originales de la raiz del repo no se han modificado.

> **No estan compilados ni probados en MetaTrader.** Antes de ponerlos en una
> cuenta demo: compilalos en MetaEditor, corrige cualquier aviso y comprueba
> en el Strategy Tester (con ticks reales de tu broker) que los trades se
> parecen a los del backtest en Python. **No los uses en real** sin unos meses
> de demo.

| Archivo | Que es | Estado | Magic |
|---|---|---|---|
| `EMA100_GBPJPY_H1_v6.mq4` | EMA100 BUY ONLY sin la salida por AO (que no actuaba nunca) | **Candidato principal** | 43898 |
| `USDJPY_H4_38025241_buyonly.mq4` | USDJPY H4 solo compras | Hipotesis | 38025242 |
| `R_EURUSD_H1_R2c.mq4` | EURUSD H1 sin salida RVI, SL/TP por ATR diario, tendencia D1 SMA200 | Hipotesis | 31422196 |
| `RSI2_Indices_D1.mq4` | **S2:** RSI(2) de Connors en indices (solo largos, D1, tamano por riesgo) | **Candidato principal** (estrategia nueva) | 22001 / 22002 / 22003 |

**EMA100 v6 en EURJPY H1:** usa el mismo `EMA100_GBPJPY_H1_v6.mq4` en un grafico
EURJPY H1 con `Stop_Loss=127`, `Take_Profit=243` y `Magic_Number=43899`. Es el
SL/TP escalado por volatilidad. Paso la validacion en otros pares (ver
`backtests/reports/CARTERA.md`). El magic es `static input`, asi que si tu
terminal no deja cambiarlo en los parametros, edita la linea en el codigo y
compila una copia.

## Uso

1. Copia el `.mq4` a `MQL4/Experts` de tu terminal y compilalo en MetaEditor.
2. Abrelo en un grafico del par y el timeframe indicados (GBPJPY H1, USDJPY H4,
   EURUSD H1).
3. Ajusta `Entry_Amount`. Recomendacion: **0.01 lotes por cada 10.000** de
   cuenta, y como mucho 0.03.
4. Las sesiones estan pensadas para un broker con hora de servidor GMT+2/GMT+3
   (medianoche = cierre de Nueva York), la mas comun. Si tu broker usa otra
   zona horaria, las horas de sesion de los EAs H1 caen en otro momento.

**S2 (`RSI2_Indices_D1.mq4`):** ponlo en el grafico **D1** de cada indice
(S&P 500, Nasdaq 100, DAX), con un `Magic_Number` distinto en cada uno. El
tamano se calcula solo: `Risk_Percent` (0.5 por defecto) es el % del balance
que supone un movimiento de 1 ATR(20) diario. No tiene stop: el peor trade del
backtest perdio 8.3 ATR (un 4.2% de la cuenta con 0.5%). En el backtest:
PF 1.72 en desarrollo y 2.57 en el holdout, 20 trades al anio entre los tres
indices, 15% de probabilidad de perder en un anio.

## Que esperar segun el backtest (2006-2026, Dukascopy)

Cifras en pips. Holdout = del 10 de julio de 2023 a octubre de 2026.

| EA | PF total | Trades/anio | maxDD | Holdout | Prob. perder en 1 anio |
|---|---|---|---|---|---|
| EMA100 v6 | 1.16 | 25 | -6,171 | 80 trades, PF 1.28, +2,204 | 33% |
| USDJPY solo compras | 1.34* | 15 | -972 | 33 trades, PF 1.07, +77 | 35% |
| EURUSD R2c | 1.75* | 5 | -2,104 | 21 trades, PF 1.02, +40 | 27% |

\* Estas dos variantes se eligieron mirando los datos hasta julio de 2023, asi
que su PF total esta inflado. La cifra honesta es la del holdout, que es
practicamente plana.

Para decidir despues de la demo, compara el resultado contra el holdout del
backtest y contra el Monte Carlo de cada informe en `backtests/reports/`.
Ojo: con 25 trades al anio o menos, harian falta varios anios de forward para
distinguir ventaja de azar.
