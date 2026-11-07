# Backtests y pruebas de robustez

Herramientas para evaluar los bots de este repo con datos de mercado reales y
una bateria de pruebas que intenta responder a una sola pregunta: **la ventaja
del bot es real o es un artefacto del periodo en el que se optimizo?**

```
backtests/
  dukascopy.py                  descarga velas H1 BID/ASK de Dukascopy -> CSV
  run_tests.py                  bateria de pruebas (8 bloques) -> report.md
  bots/
    ea_gbpjpy_h1_ema100_v5.py   backtester v5 del EA GBPJPY H1 EMA100 BUY ONLY
  reports/
    RESUMEN.md                  conclusiones de los 4 bots evaluados
    ea_gbpjpy_h1_ema100_v5.md   informe completo generado por run_tests.py
  data/                         CSV y cache de descargas (no se versiona)
```

## Instalacion

```bash
pip install -r backtests/requirements.txt
```

Solo necesita `pandas` y `numpy`.

## 1. Descargar datos

```bash
python backtests/dukascopy.py GBPJPY --start 2006
```

- Genera `backtests/data/GBPJPY_H1.csv` con columnas
  `time,open,high,low,close,volume,spread`. Los precios son BID y el spread es
  ASK - BID en points, medido en la apertura de cada vela.
- La hora queda en **hora de broker MT4/MT5 tipica**: GMT+2 en invierno y
  GMT+3 en verano, con la medianoche al cierre de Nueva York. Si tu broker usa
  otra zona horaria, las sesiones del EA caen en horas distintas. Usa
  `--tz utc` si prefieres UTC.
- Dukascopy limita la velocidad (HTTP 429) y a veces corta conexiones. El
  script reintenta y guarda cada mes en `backtests/data/raw/`, asi que si se
  interrumpe basta con relanzarlo. 20 anios de un par son unos 500 archivos y
  pueden tardar en torno a una hora.
- El mes en curso todavia no existe como archivo mensual y se omite.

Tambien puedes usar un CSV exportado de tu propio broker. Los formatos que
acepta el loader estan documentados en `load_price_csv` del bot.

## 2. Ejecutar la bateria de pruebas

```bash
python backtests/run_tests.py \
  --bot backtests/bots/ea_gbpjpy_h1_ema100_v5.py \
  --csv backtests/data/GBPJPY_H1.csv \
  --split 2022-07-11 --swap-gbpjpy
```

| Opcion | Para que sirve |
|---|---|
| `--split FECHA` | corte entre la muestra de optimizacion (IS) y la de validacion (OOS). Usa la fecha en la que se genero el bot |
| `--preset NOMBRE` | preset de `get_presets()` a evaluar (por defecto `baseline`) |
| `--params a,b,c` | parametros de `Config` a perturbar en la prueba de robustez |
| `--swap-gbpjpy` | estima el swap de GBPJPY con tipos oficiales del BoE y del BoJ. Es aproximado |
| `--quick` | menos simulaciones (unos 5 minutos en vez de 15) |
| `--outdir DIR` | carpeta de salida (por defecto `backtests/out/<bot>/`) |

Genera `report.md`, `trades_base.csv`, `anual.csv` y `sensibilidad.csv`.

### Que prueba cada bloque

1. **Backtest base**: metricas, t-stat, tiempo sin nuevos maximos, IS/OOS,
   desglose anual, comprobacion de que la salida por senal llega a actuar y de
   si SL y TP se tocan en la misma vela.
2. **Costes**: spread real frente a fijo de 2.5, 4 y 6 pips, filtro de spread
   maximo, comision y swap estimado.
3. **Entradas aleatorias**: el mismo bot pero entrando al azar con las mismas
   reglas (filtro, sesion, SL/TP), calibrado para tener un numero de trades
   parecido. Si el bot no supera con claridad el percentil 95, la senal de
   entrada aporta poco.
4. **Monte Carlo**: reordenar trades (distribucion del drawdown), bootstrap
   (probabilidad de acabar en perdida), probabilidad de perder a 1, 2 y 3 anios,
   y saltar un 20% de trades con slippage aleatorio.
5. **Robustez de parametros**: cada parametro de x0.7 a x1.3, todos a la vez
   +-20% y mapa SL x TP. Lo que se busca es una meseta, no un pico.
6. **Presets** del propio bot (breakeven, trailing, cierres de sesion...).
7. **Walk-forward**: reoptimiza fi_period/SL/TP con los N anios anteriores y
   prueba el siguiente. Eficiencia = pips OOS / pips IS por anio.
8. **Regimen, dia y hora**: solo para diagnostico. No filtres por esto sin
   validarlo fuera de muestra.

## Probar un bot nuevo

`run_tests.py` funciona con cualquier modulo que exponga la misma interfaz que
`bots/ea_gbpjpy_h1_ema100_v5.py`:

- `Config` (dataclass con `pip`, `point`, `stop_loss_pips`, `take_profit_pips`,
  `use_bar_spread`, `spread_pips`, `max_spread_pips`,
  `commission_per_lot_per_side`, `pip_value_per_lot`, `initial_capital`...)
- `get_presets() -> dict[str, Config]` con al menos `baseline`
- `load_price_csv(path) -> DataFrame`
- `backtest(h1, cfg) -> (trades, equity, metrics)`, donde `trades` tiene
  `entry_time, exit_time, direction, lots, stop_loss, take_profit, pnl_pips, pnl_cash`
- opcional: `entry_signal(...)` y `Direction`, para el benchmark aleatorio, y
  `count_swap_nights` para el swap

La forma mas rapida es copiar el v5 y cambiar `compute_indicators`,
`entry_signal` y `exit_signal`.

## Limites

- Es un modelo en Python, no el Strategy Tester de MetaTrader. Antes de operar
  en real, valida en MT4/MT5 con ticks reales y deja el bot unos meses en demo.
- Los resultados en dinero usan un `pip_value_per_lot` fijo. Los resultados en
  pips son los fiables.
- El swap de `--swap-gbpjpy` usa tipos oficiales aproximados y un margen de
  broker supuesto. Usa los swaps reales de tu broker.
- Con datos H1, SL y TP se comprueban con el maximo y el minimo de la vela. El
  informe avisa si algun trade toco ambos en la misma vela. En ese caso conviene
  pasar datos M1/M15 al backtester (`--ltf-csv` en el script del bot).
- Los datos de Dukascopy no se versionan en el repo: cada uno los descarga con
  `dukascopy.py`.
