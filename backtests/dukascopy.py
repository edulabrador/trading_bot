"""
dukascopy.py
============

Descarga velas H1 (BID y ASK) del datafeed publico de Dukascopy y las guarda
en un CSV listo para los backtesters de este repo.

Salida (una fila por vela H1, solo velas con volumen > 0):
    time,open,high,low,close,volume,spread
  - Precios BID.
  - spread = (ASK_open - BID_open) en points (0.001 en pares JPY).
  - time en "hora de broker" MT4/MT5 tipica: GMT+2 en invierno / GMT+3 en
    verano (medianoche = cierre de Nueva York). Asi las velas H4 empiezan a
    las 00/04/08... y no hay velas de domingo. Usa --tz utc para dejarlo en UTC.

Uso:
    python backtests/dukascopy.py GBPJPY --start 2006 --end 2026
    python backtests/dukascopy.py EURUSD --start 2010 --end 2026 --out data/EURUSD_H1.csv

Notas:
  - Dukascopy limita la velocidad (HTTP 429) y a veces corta conexiones; el
    script reintenta con backoff y guarda cada archivo mensual en cache
    (backtests/data/raw), asi que puedes relanzarlo y continua donde iba.
  - El mes en curso no existe todavia como archivo mensual (404): se omite.
  - Formato bi5 de velas: registros de 24 bytes big-endian
    (segundos desde inicio de mes, open, close, low, high: int32; volumen: float32).
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import lzma
import os
import time
import urllib.error
import urllib.request

import numpy as np
import pandas as pd

BASE_URL = "https://datafeed.dukascopy.com/datafeed"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw")


def point_for(symbol: str) -> float:
    """Tamano del point en el datafeed (escala de los enteros del bi5)."""
    return 0.001 if symbol.upper().endswith("JPY") else 0.00001


def _opener():
    handlers = []
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"https": proxy}))
    op = urllib.request.build_opener(*handlers)
    op.addheaders = [("User-Agent", "Mozilla/5.0 (backtest data download)")]
    return op


def _fetch(path: str, opener, retries: int = 8) -> str:
    dst = os.path.join(RAW_DIR, path.replace("/", "_"))
    if os.path.exists(dst):
        return "cached"
    for k in range(retries):
        try:
            with opener.open(f"{BASE_URL}/{path}", timeout=40) as r:
                data = r.read()
            with open(dst, "wb") as fh:
                fh.write(data)
            return "ok"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return "404"  # no se cachea: el mes en curso aparecera mas adelante
            time.sleep(min(2 ** k, 30))
        except Exception:
            time.sleep(min(2 ** k, 30))
    return "FAIL"


def download(symbol: str, start: int, end: int, workers: int = 3) -> dict:
    os.makedirs(RAW_DIR, exist_ok=True)
    now = pd.Timestamp.now("UTC")
    paths = []
    for y in range(start, end + 1):
        for m in range(12):  # Dukascopy usa meses 0-11
            if (y, m + 1) >= (now.year, now.month):
                break
            for side in ("BID", "ASK"):
                paths.append(f"{symbol}/{y}/{m:02d}/{side}_candles_hour_1.bi5")
    opener = _opener()
    stats: dict = {}
    with cf.ThreadPoolExecutor(workers) as ex:
        for n, status in enumerate(ex.map(lambda p: _fetch(p, opener), paths), 1):
            stats[status] = stats.get(status, 0) + 1
            if n % 50 == 0 or n == len(paths):
                print(f"  {n}/{len(paths)} {stats}", flush=True)
    return stats


def _read_month(symbol: str, y: int, m: int, side: str, pt: float):
    f = os.path.join(RAW_DIR, f"{symbol}_{y}_{m:02d}_{side}_candles_hour_1.bi5")
    if not os.path.exists(f) or os.path.getsize(f) == 0:
        return None
    raw = lzma.decompress(open(f, "rb").read())
    ints = np.frombuffer(raw, dtype=">i4").reshape(-1, 6)
    vol = np.frombuffer(raw, dtype=">f4").reshape(-1, 6)[:, 5].astype(float)
    t0 = pd.Timestamp(year=y, month=m + 1, day=1)
    idx = t0 + pd.to_timedelta(ints[:, 0], unit="s")
    return pd.DataFrame({"open": ints[:, 1] * pt, "high": ints[:, 4] * pt, "low": ints[:, 3] * pt,
                         "close": ints[:, 2] * pt, "volume": vol}, index=idx)


def build_h1(symbol: str, start: int, end: int, tz: str = "broker") -> pd.DataFrame:
    pt = point_for(symbol)
    bids, asks = [], []
    for y in range(start, end + 1):
        for m in range(12):
            b = _read_month(symbol, y, m, "BID", pt)
            a = _read_month(symbol, y, m, "ASK", pt)
            if b is not None:
                bids.append(b)
            if a is not None:
                asks.append(a)
    if not bids:
        raise SystemExit("No hay datos descargados para ese rango.")
    bid = pd.concat(bids).sort_index()
    ask = pd.concat(asks).sort_index() if asks else None
    bid = bid[bid["volume"] > 0]  # fuera velas planas de fin de semana / festivos
    df = bid.copy()

    if ask is not None:
        sp = ((ask["open"].reindex(df.index) - df["open"]) / pt).round()
        sp = sp.where(sp > 0)  # cotizaciones erroneas o ASK ausente -> NaN
        sp = sp.fillna(sp.rolling(500, min_periods=1).median()).fillna(sp.median())
        df["spread"] = sp.clip(lower=5)
    if tz == "broker":
        ny = df.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
        df.index = ny + pd.Timedelta(hours=7)
    df = df[~df.index.duplicated()]
    df.index.name = "time"
    return df


def main() -> None:
    p = argparse.ArgumentParser(description="Descarga velas H1 BID/ASK de Dukascopy a CSV")
    p.add_argument("symbol", help="ej. GBPJPY, EURUSD, USDJPY")
    p.add_argument("--start", type=int, default=2006)
    p.add_argument("--end", type=int, default=pd.Timestamp.now("UTC").year)
    p.add_argument("--out", default=None, help="CSV de salida (por defecto backtests/data/<SYM>_H1.csv)")
    p.add_argument("--tz", choices=["broker", "utc"], default="broker")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--no-download", action="store_true", help="solo reconstruye el CSV desde la cache")
    a = p.parse_args()
    sym = a.symbol.upper()
    if not a.no_download:
        print(f"Descargando {sym} {a.start}-{a.end} ...")
        stats = download(sym, a.start, a.end, a.workers)
        if stats.get("FAIL"):
            print(f"AVISO: {stats['FAIL']} archivos fallaron; relanza el comando para reintentarlos.")
    df = build_h1(sym, a.start, a.end, a.tz)
    out = a.out or os.path.join(HERE, "data", f"{sym}_H1.csv")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    df.to_csv(out, float_format="%.6f")
    print(f"OK: {len(df)} velas H1 {df.index[0]} -> {df.index[-1]} en {out}")
    if "spread" in df:
        print(f"Spread mediano {df.spread.median() * point_for(sym) / (0.01 if sym.endswith('JPY') else 0.0001):.2f} pips")


if __name__ == "__main__":
    main()
