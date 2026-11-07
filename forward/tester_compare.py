"""
tester_compare.py
=================

Compara el informe del Strategy Tester de MetaTrader 4 con los trades del
backtest en Python, trade a trade. Sirve para comprobar que el .mq4 hace lo
mismo que el modelo antes de ponerlo en demo.

Uso:
    python forward/tester_compare.py StrategyTester.htm --magic 43898
    python forward/tester_compare.py StrategyTester.htm --magic 22001 --tol-hours 48 --desde 2024-01-01 --hasta 2025-12-31

Como obtener el informe en MT4: Strategy Tester > ejecutar el EA (modelo
"Every tick" o "Control points") > pestana "Report" > clic derecho > "Save as
Report". Se genera un .htm. Solo usa la libreria estandar de Python y pandas.

--magic elige la referencia del backtest en forward/bots.json. El informe del
tester solo tiene un EA, asi que no hace falta filtrar por magic.

--tol-hours es cuanto puede diferir la hora de entrada para considerar que es el
mismo trade: 1-2 h para el EMA100 (H1) y 48 h para S2 (D1; el dia de los datos
de Yahoo/Dukascopy puede no coincidir con el dia del broker).
"""
from __future__ import annotations

import argparse
import json
import os
import re
from html.parser import HTMLParser

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATE_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}")
OPEN_TYPES = {"buy", "sell"}
CLOSE_TYPES = {"close", "s/l", "t/p", "close at stop", "close at end"}


class _Rows(HTMLParser):
    """Extrae todas las filas <tr> como listas de textos de celda."""

    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._in = [], None, [], False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._in, self._cell = True, []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._row is not None and self._in:
            self._row.append("".join(self._cell).strip())
            self._in = False
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._in:
            self._cell.append(data)


def parse_mt4_report(path: str) -> pd.DataFrame:
    """Devuelve un trade por fila: ticket, direction, lots, entry_time, entry_price, exit_time, exit_price, reason, profit."""
    raw = open(path, "rb").read()
    for enc in ("utf-8", "cp1252", "utf-16"):
        try:
            html = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    p = _Rows()
    p.feed(html)
    events = []
    for r in p.rows:
        # fila de operacion: #, Time, Type, Order, Size, Price, S/L, T/P, [Profit, Balance]
        if len(r) >= 6 and DATE_RE.match(r[1]) and r[0].isdigit():
            typ = r[2].strip().lower()
            try:
                events.append({"time": pd.to_datetime(r[1], format="%Y.%m.%d %H:%M"), "type": typ, "order": int(r[3]),
                               "size": float(r[4]), "price": float(r[5]),
                               "profit": float(r[8]) if len(r) > 8 and r[8] not in ("", None) else np.nan})
            except ValueError:
                continue
    if not events:
        raise SystemExit("No encuentro operaciones en el informe. Es un informe de Strategy Tester de MT4 (.htm)?")
    ev = pd.DataFrame(events)
    trades = []
    for order, g in ev.groupby("order"):
        o = g[g["type"].isin(OPEN_TYPES)]
        c = g[g["type"].isin(CLOSE_TYPES)]
        if o.empty:
            continue
        o = o.iloc[0]
        c = c.iloc[-1] if not c.empty else None
        trades.append({"ticket": order, "direction": o["type"].upper(), "lots": o["size"], "entry_time": o["time"],
                       "entry_price": o["price"], "exit_time": c["time"] if c is not None else pd.NaT,
                       "exit_price": c["price"] if c is not None else np.nan,
                       "reason": c["type"] if c is not None else "abierta", "profit": c["profit"] if c is not None else np.nan})
    return pd.DataFrame(trades).sort_values("entry_time").reset_index(drop=True)


def match(mt: pd.DataFrame, bt: pd.DataFrame, tol: pd.Timedelta):
    """Empareja por hora de entrada (misma direccion): primero los pares mas cercanos de todo el informe."""
    cand = []
    for i, r in mt.iterrows():
        same = bt[bt.direction == r.direction]
        d = (same.entry_time - r.entry_time).abs()
        for j, dj in d[d <= tol].items():
            cand.append((dj, i, j))
    used_m, used_b, pairs = set(), set(), []
    for _, i, j in sorted(cand):
        if i not in used_m and j not in used_b:
            used_m.add(i); used_b.add(j); pairs.append((i, j))
    return sorted(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--magic", required=True)
    ap.add_argument("--tol-hours", type=float, default=2.0)
    ap.add_argument("--desde", default=None)
    ap.add_argument("--hasta", default=None)
    ap.add_argument("--out", default=None, help="CSV con el detalle del emparejamiento")
    a = ap.parse_args()

    cfg = json.load(open(os.path.join(HERE, "bots.json"), encoding="utf-8"))
    info = cfg.get(str(a.magic))
    if not info:
        raise SystemExit(f"magic {a.magic} no esta en forward/bots.json")
    bt = pd.read_csv(os.path.join(ROOT, info["backtest"]), parse_dates=["entry_time", "exit_time"])
    if "direction" not in bt:
        bt["direction"] = "BUY"
    mt = parse_mt4_report(a.report)

    tol = pd.Timedelta(hours=a.tol_hours)
    lo = pd.Timestamp(a.desde) if a.desde else mt.entry_time.min()
    hi = pd.Timestamp(a.hasta) if a.hasta else mt.entry_time.max()
    mt = mt[(mt.entry_time >= lo) & (mt.entry_time <= hi)].reset_index(drop=True)
    # el backtest se recorta con margen = tolerancia, para no perder trades del borde por diferencias de hora
    bt = bt[(bt.entry_time >= lo - tol) & (bt.entry_time <= hi + tol)].reset_index(drop=True)

    pairs = match(mt, bt, tol)
    mi = {i for i, _ in pairs}
    bi = {j for _, j in pairs}
    pct = lambda r: (1 if r.direction == "BUY" else -1) * (r.exit_price - r.entry_price) / r.entry_price * 100

    rows = []
    for i, j in pairs:
        m, b = mt.loc[i], bt.loc[j]
        rows.append({"estado": "emparejado", "mt4_entrada": m.entry_time, "bt_entrada": b.entry_time,
                     "dif_entrada_h": round((m.entry_time - b.entry_time).total_seconds() / 3600, 1),
                     "mt4_precio_e": m.entry_price, "bt_precio_e": round(b.entry_price, 5),
                     "dif_precio_e_%": round((m.entry_price / b.entry_price - 1) * 100, 3),
                     "mt4_salida": m.exit_time, "bt_salida": b.exit_time,
                     "mt4_%": round(pct(m), 3) if pd.notna(m.exit_price) else np.nan, "bt_%": round(pct(b), 3),
                     "mt4_motivo": m.reason, "bt_motivo": b.get("exit_reason", "")})
    for i in set(mt.index) - mi:
        m = mt.loc[i]
        rows.append({"estado": "solo en MT4", "mt4_entrada": m.entry_time, "mt4_precio_e": m.entry_price,
                     "mt4_salida": m.exit_time, "mt4_%": round(pct(m), 3) if pd.notna(m.exit_price) else np.nan, "mt4_motivo": m.reason})
    for j in set(bt.index) - bi:
        b = bt.loc[j]
        rows.append({"estado": "solo en backtest", "bt_entrada": b.entry_time, "bt_precio_e": round(b.entry_price, 5),
                     "bt_salida": b.exit_time, "bt_%": round(pct(b), 3), "bt_motivo": b.get("exit_reason", "")})
    det = pd.DataFrame(rows).sort_values(["mt4_entrada", "bt_entrada"], na_position="last")

    n_mt, n_bt, n_p = len(mt), len(bt), len(pairs)
    em = det[det.estado == "emparejado"]
    same_exit = (em["mt4_salida"] - em["bt_salida"]).abs() <= pd.Timedelta(hours=max(a.tol_hours, 1))
    print(f"\n=== {info['nombre']} | {lo:%Y-%m-%d} a {hi:%Y-%m-%d} ===")
    print(f"Trades: MT4 {n_mt} | backtest {n_bt} | emparejados {n_p} "
          f"({100 * n_p / max(n_bt, 1):.0f}% del backtest, {100 * n_p / max(n_mt, 1):.0f}% de MT4)")
    if n_p:
        print(f"Entrada: diferencia mediana {em['dif_entrada_h'].abs().median():.1f} h; precio {em['dif_precio_e_%'].abs().median():.3f}% "
              f"(maximo {em['dif_precio_e_%'].abs().max():.3f}%)")
        print(f"Salida en el mismo momento (+-{max(a.tol_hours, 1):.0f} h): {100 * same_exit.mean():.0f}% de los emparejados")
        both = em.dropna(subset=["mt4_%", "bt_%"])
        if len(both) > 2:
            print(f"Resultado por trade: correlacion {both['mt4_%'].corr(both['bt_%']):.2f}; suma MT4 {both['mt4_%'].sum():+.2f}% "
                  f"frente a backtest {both['bt_%'].sum():+.2f}% en los trades emparejados")
    print(f"Solo en MT4: {n_mt - n_p} | solo en backtest: {n_bt - n_p}")
    share = n_p / max(n_bt, n_mt, 1)
    if share >= 0.9 and (not n_p or same_exit.mean() >= 0.8):
        verdict = "OK: el EA reproduce el backtest. Diferencias pequenas de precio son normales (datos y spread del broker)."
    elif share >= 0.7:
        verdict = ("REVISAR: coincide la mayoria, pero no todo. Mira las filas 'solo en ...': suelen ser la hora del servidor, "
                   "el corte de la vela diaria, festivos o el nombre/horario del CFD.")
    else:
        verdict = ("NO COINCIDE: no pongas el EA en demo todavia. Revisa la zona horaria del broker (--tol-hours), que el "
                   "grafico y el timeframe sean los correctos y que el periodo de prueba sea el mismo.")
    print("->", verdict)
    out = a.out or os.path.splitext(a.report)[0] + f"_vs_backtest_{a.magic}.csv"
    det.to_csv(out, index=False)
    print(f"Detalle: {out}")


if __name__ == "__main__":
    main()
