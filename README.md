# trading_bot
In this repository, I showcase some trading bots that I have developed myself,
together with the tools used to test whether they really work.

## Estado de los bots (noviembre de 2026)

Resumen de las pruebas con datos reales (Dukascopy y Yahoo, 2006-2026), con un
periodo reservado desde el 10/07/2023. Detalle en
[`backtests/reports/RESUMEN.md`](backtests/reports/RESUMEN.md) y
[`backtests/reports/CARTERA.md`](backtests/reports/CARTERA.md).

| Bot | Archivo | Estado |
|---|---|---|
| **S2-M1: RSI(2) en indices (S&P 500, Nasdaq 100, DAX, D1)** | [`demo/RSI2_Indices_D1.mq4`](demo/RSI2_Indices_D1.mq4) | **Candidato principal para demo.** PF 2.12 en desarrollo y 2.19 fuera de muestra |
| **EMA100 v6: GBPJPY H1, solo compras** | [`demo/EMA100_GBPJPY_H1_v6.mq4`](demo/EMA100_GBPJPY_H1_v6.mq4) | **Candidato para demo.** PF 1.16 en el historico y 1.28 fuera de muestra; ventaja pequena y riesgo alto |
| EMA100 v6 en EURJPY H1 | mismo `.mq4`, otros parametros | Solo demo |
| GBPJPY H4 | [`GBPJPY_H4_35839595.mq4`](GBPJPY_H4_35839595.mq4) | No rentable desde 2023 |
| USDJPY H4 | [`USDJPY_H4_38025241.mq4`](USDJPY_H4_38025241.mq4) | No rentable desde 2020 |
| EURUSD H1 | [`R_EURUSD_H1.mq4`](R_EURUSD_H1.mq4) | No rentable |

> Ningun `.mq4` de `demo/` esta compilado todavia. Hay que compilarlos en
> MetaEditor, comprobarlos con el Strategy Tester (`forward/tester_compare.py`)
> y dejarlos unos meses en demo antes de usar dinero real.

## Estructura

| Carpeta | Contenido |
|---|---|
| [`backtests/`](backtests/) | Descarga de datos (Dukascopy), motor de backtest, bateria de pruebas de robustez, informes |
| [`backtests/research/`](backtests/research/) | Protocolos registrados antes de cada prueba, mejoras probadas y resultados |
| [`demo/`](demo/) | EAs candidatos listos para compilar |
| [`forward/`](forward/) | Kit de forward: comparacion con el Strategy Tester, exportacion de trades y reglas de decision |
