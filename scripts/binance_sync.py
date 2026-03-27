#!/usr/bin/env python3
"""
Import completed Binance Futures round-trips into data/trades.json.
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from binance_client import BinanceClientError, BinanceFuturesClient

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"
SOURCE_NAME = "binance_futures"


def load_trade_store() -> dict[str, Any]:
    if TRADES_FILE.exists():
        with open(TRADES_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"trades": [], "metadata": {"created": datetime.now().isoformat(), "version": "1.1.0"}}


def save_trade_store(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data.setdefault("metadata", {})
    data["metadata"]["updated"] = datetime.now().isoformat()
    data["metadata"]["version"] = "1.1.0"
    with open(TRADES_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def iso_from_millis(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).replace(tzinfo=None).isoformat()


def dedupe_income_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    output = []
    for row in rows:
        key = (
            str(row.get("symbol", "")),
            str(row.get("time", "")),
            str(row.get("income", "")),
            str(row.get("tradeId", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(row)
    return output


def fetch_symbols_with_realized_pnl(
    client: BinanceFuturesClient,
    start_time: int | None,
    end_time: int | None,
    explicit_symbols: list[str] | None,
) -> tuple[list[str], dict[str, list[dict[str, Any]]]]:
    if explicit_symbols:
        symbols = sorted({symbol.upper() for symbol in explicit_symbols})
        by_symbol: dict[str, list[dict[str, Any]]] = {}
        for symbol in symbols:
            rows = client.get_income_history(start_time=start_time, end_time=end_time, symbol=symbol)
            realized = [row for row in rows if row.get("incomeType") == "REALIZED_PNL"]
            by_symbol[symbol] = dedupe_income_rows(realized)
        return symbols, by_symbol

    rows = client.get_income_history(start_time=start_time, end_time=end_time)
    realized = dedupe_income_rows([row for row in rows if row.get("incomeType") == "REALIZED_PNL" and row.get("symbol")])
    by_symbol = defaultdict(list)
    for row in realized:
        by_symbol[str(row["symbol"]).upper()].append(row)
    return sorted(by_symbol.keys()), dict(by_symbol)


def split_fill(fill: dict[str, Any], active: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    qty = to_float(fill.get("qty"))
    if qty <= 0:
        return None, None

    side = str(fill.get("side", "")).upper()
    delta = qty if side == "BUY" else -qty
    current_position = active["net_qty"]

    if current_position == 0 or current_position * delta > 0:
        return fill, None

    closing_qty = min(abs(current_position), abs(delta))
    opening_qty = abs(delta) - closing_qty
    closing_fill = dict(fill)
    closing_fill["qty"] = closing_qty

    opening_fill = None
    if opening_qty > 0:
        opening_fill = dict(fill)
        opening_fill["qty"] = opening_qty
        opening_fill["realizedPnl"] = 0

    return opening_fill, closing_fill


def start_cycle(fill: dict[str, Any], key: tuple[str, str]) -> dict[str, Any]:
    qty = to_float(fill.get("qty"))
    price = to_float(fill.get("price"))
    side = str(fill.get("side", "")).upper()
    net_qty = qty if side == "BUY" else -qty
    opened_at = to_int(fill.get("time"))
    return {
        "symbol": key[0],
        "position_side": key[1],
        "direction": "LONG" if net_qty > 0 else "SHORT",
        "opened_at": opened_at,
        "closed_at": opened_at,
        "entry_notional": price * qty,
        "entry_qty": qty,
        "close_notional": 0.0,
        "closed_qty": 0.0,
        "fees": to_float(fill.get("commission")),
        "net_qty": net_qty,
        "realized_pnl": 0.0,
        "fill_ids": [str(fill.get("id"))],
        "order_ids": [str(fill.get("orderId"))],
    }


def apply_fill(active: dict[str, Any], fill: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    completed: list[dict[str, Any]] = []
    pending_open, pending_close = split_fill(fill, active)

    if pending_close:
        close_qty = to_float(pending_close.get("qty"))
        price = to_float(pending_close.get("price"))
        side = str(pending_close.get("side", "")).upper()
        delta = close_qty if side == "BUY" else -close_qty

        active["close_notional"] += price * close_qty
        active["closed_qty"] += close_qty
        active["fees"] += to_float(pending_close.get("commission"))
        active["realized_pnl"] += to_float(pending_close.get("realizedPnl"))
        active["net_qty"] += delta
        active["closed_at"] = to_int(pending_close.get("time"))
        active["fill_ids"].append(str(pending_close.get("id")))
        active["order_ids"].append(str(pending_close.get("orderId")))

        if abs(active["net_qty"]) < 1e-12:
            completed.append(dict(active))

    next_cycle: dict[str, Any] = active
    if pending_open:
        if abs(active["net_qty"]) < 1e-12 and active["closed_qty"] > 0:
            next_cycle = start_cycle(pending_open, (active["symbol"], active["position_side"]))
        else:
            qty = to_float(pending_open.get("qty"))
            price = to_float(pending_open.get("price"))
            side = str(pending_open.get("side", "")).upper()
            delta = qty if side == "BUY" else -qty
            active["entry_notional"] += price * qty
            active["entry_qty"] += qty
            active["fees"] += to_float(pending_open.get("commission"))
            active["net_qty"] += delta
            active["closed_at"] = to_int(pending_open.get("time"))
            active["fill_ids"].append(str(pending_open.get("id")))
            active["order_ids"].append(str(pending_open.get("orderId")))
    elif completed:
        next_cycle = {}

    return completed, next_cycle


def cycle_to_trade(cycle: dict[str, Any]) -> dict[str, Any] | None:
    if cycle["entry_qty"] <= 0 or cycle["closed_qty"] <= 0:
        return None

    entry_price = cycle["entry_notional"] / cycle["entry_qty"]
    exit_price = cycle["close_notional"] / cycle["closed_qty"]
    pnl_percent = 0.0
    basis = cycle["entry_notional"]
    if basis > 0:
        pnl_percent = (cycle["realized_pnl"] / basis) * 100

    close_dt = datetime.fromtimestamp(cycle["closed_at"] / 1000)
    unique_fill_ids = sorted(set(cycle["fill_ids"]))
    source_cycle_id = f"{SOURCE_NAME}:{cycle['symbol']}:{cycle['position_side']}:{cycle['closed_at']}:{'-'.join(unique_fill_ids)}"

    return {
        "id": source_cycle_id[-32:],
        "timestamp": iso_from_millis(cycle["closed_at"]),
        "symbol": cycle["symbol"],
        "direction": cycle["direction"],
        "entry": round(entry_price, 8),
        "exit": round(exit_price, 8),
        "pnl_percent": round(pnl_percent, 4),
        "result": "WIN" if cycle["realized_pnl"] >= 0 else "LOSS",
        "leverage": None,
        "reason": "Imported automatically from Binance Futures",
        "indicators": {},
        "market_context": {
            "source": SOURCE_NAME,
            "position_side": cycle["position_side"],
            "fees": round(cycle["fees"], 8),
            "realized_pnl": round(cycle["realized_pnl"], 8),
        },
        "notes": f"Imported from Binance Futures fills: {', '.join(unique_fill_ids)}",
        "day_of_week": close_dt.strftime("%A").lower(),
        "hour": close_dt.hour,
        "source": SOURCE_NAME,
        "source_cycle_id": source_cycle_id,
        "exchange_fill_ids": unique_fill_ids,
        "exchange_order_ids": sorted(set(cycle["order_ids"])),
    }


def build_completed_trades(user_trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for fill in user_trades:
        symbol = str(fill.get("symbol", "")).upper()
        if not symbol:
            continue
        position_side = str(fill.get("positionSide", "BOTH")).upper()
        grouped[(symbol, position_side)].append(fill)

    completed: list[dict[str, Any]] = []
    for key, fills in grouped.items():
        fills.sort(key=lambda item: (to_int(item.get("time")), to_int(item.get("id"))))
        active: dict[str, Any] = {}

        for fill in fills:
            if not active:
                active = start_cycle(fill, key)
                continue

            just_completed, active = apply_fill(active, fill)
            completed.extend(just_completed)

        if active and abs(active.get("net_qty", 0.0)) < 1e-12 and active.get("closed_qty", 0.0) > 0:
            completed.append(active)

    trades = []
    for cycle in completed:
        trade = cycle_to_trade(cycle)
        if trade:
            trades.append(trade)
    trades.sort(key=lambda item: item["timestamp"])
    return trades


def import_binance_trades(
    start_time: int | None,
    end_time: int | None,
    symbols: list[str] | None,
    dry_run: bool,
) -> dict[str, Any]:
    client = BinanceFuturesClient()
    target_symbols, income_by_symbol = fetch_symbols_with_realized_pnl(client, start_time, end_time, symbols)

    if not target_symbols:
        return {"imported": 0, "skipped": 0, "symbols": [], "message": "No realized PnL rows found in Binance Futures."}

    user_trades: list[dict[str, Any]] = []
    for symbol in target_symbols:
        income_rows = income_by_symbol.get(symbol, [])
        if not income_rows:
            continue
        window_start = min(to_int(row.get("time")) for row in income_rows) - 86_400_000
        window_end = max(to_int(row.get("time")) for row in income_rows) + 86_400_000
        user_trades.extend(client.get_user_trades(symbol, start_time=window_start, end_time=window_end))

    imported_candidates = build_completed_trades(user_trades)

    store = load_trade_store()
    existing_ids = {trade.get("source_cycle_id") for trade in store.get("trades", []) if trade.get("source_cycle_id")}

    new_trades = [trade for trade in imported_candidates if trade["source_cycle_id"] not in existing_ids]
    skipped = len(imported_candidates) - len(new_trades)

    if not dry_run and new_trades:
        store.setdefault("trades", []).extend(new_trades)
        store["trades"].sort(key=lambda item: item.get("timestamp", ""))
        save_trade_store(store)

    return {
        "imported": len(new_trades),
        "skipped": skipped,
        "symbols": target_symbols,
        "trades": new_trades,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import completed Binance Futures trades into trades.json")
    parser.add_argument("--start-time", type=int, help="Unix timestamp in milliseconds")
    parser.add_argument("--end-time", type=int, help="Unix timestamp in milliseconds")
    parser.add_argument("--symbol", action="append", dest="symbols", help="Limit import to one or more symbols")
    parser.add_argument("--dry-run", action="store_true", help="Preview imported trades without writing")
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    args = parser.parse_args()

    try:
        result = import_binance_trades(
            start_time=args.start_time,
            end_time=args.end_time,
            symbols=args.symbols,
            dry_run=args.dry_run,
        )
    except BinanceClientError as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print("Binance Futures sync summary")
    print("=" * 40)
    print(f"Symbols scanned: {', '.join(result['symbols']) if result['symbols'] else '-'}")
    print(f"Imported trades: {result['imported']}")
    print(f"Skipped existing: {result['skipped']}")
    if result.get("message"):
        print(result["message"])
    if args.dry_run and result["trades"]:
        print("\nDry-run imports:")
        for trade in result["trades"]:
            print(
                f"- {trade['timestamp']} {trade['symbol']} {trade['direction']} "
                f"entry={trade['entry']} exit={trade['exit']} pnl={trade['pnl_percent']:+.2f}%"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
