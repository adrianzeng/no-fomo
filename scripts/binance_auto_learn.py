#!/usr/bin/env python3
"""
Sync Binance trades, then trigger rule generation and optional memory update.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from binance_sync import import_binance_trades
from binance_client import BinanceClientError

BASE_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent


def run_script(script_name: str, extra_args: list[str] | None = None) -> int:
    command = [sys.executable, str(SCRIPTS_DIR / script_name)]
    if extra_args:
        command.extend(extra_args)
    completed = subprocess.run(command, cwd=BASE_DIR)
    return completed.returncode


def run_cycle(args: argparse.Namespace) -> int:
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

    print(
        f"Sync finished: imported={result['imported']} skipped={result['skipped']} "
        f"symbols={','.join(result['symbols']) if result['symbols'] else '-'}"
    )

    if args.dry_run or result["imported"] == 0:
        return 0

    if run_script("analyze.py") != 0:
        return 1

    if run_script("generate_rules.py") != 0:
        return 1

    if args.memory_path:
        if run_script("update_memory.py", ["--memory-path", args.memory_path]) != 0:
            return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-sync Binance Futures trades and refresh learned rules")
    parser.add_argument("--start-time", type=int, help="Unix timestamp in milliseconds")
    parser.add_argument("--end-time", type=int, help="Unix timestamp in milliseconds")
    parser.add_argument("--symbol", action="append", dest="symbols", help="Limit sync to one or more symbols")
    parser.add_argument("--memory-path", help="Optional MEMORY.md path to update after sync")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync without writing or learning")
    parser.add_argument("--watch", action="store_true", help="Poll Binance periodically")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds for --watch")
    args = parser.parse_args()

    if args.watch and args.interval < 10:
        print("ERROR: --interval must be at least 10 seconds in watch mode.")
        return 1

    if not args.watch:
        return run_cycle(args)

    while True:
        exit_code = run_cycle(args)
        if exit_code != 0:
            return exit_code
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
