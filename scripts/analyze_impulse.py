#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze impulse trading patterns from historical trade data.

This script analyzes all logged trades to identify impulse trading patterns
including FOMO chasing, revenge trading, and emotional decisions.
"""

import sys
import json
import argparse
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

# Import analysis utilities
sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import (
    get_impulse_statistics,
    format_impulse_report,
    detect_impulse_trade,
)


def load_trades():
    """Load trades from JSON file."""
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def analyze_impulse_trades(args):
    """Main analysis function."""
    trades = load_trades()

    if not trades:
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    # Get impulse statistics
    stats = get_impulse_statistics(trades)

    if args.json:
        # Output JSON for AI consumption
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return

    # Print readable report
    print(format_impulse_report(stats))

    # Print detailed breakdown if requested
    if args.detail:
        print_detailed_breakdown(stats)


def print_detailed_breakdown(stats):
    """Print detailed breakdown of impulse trades."""
    print("\n" + "=" * 50)
    print("冲动交易明细")
    print("=" * 50)

    impulse_trades = stats.get("impulse_trades", [])
    if not impulse_trades:
        print("暂无冲动交易记录")
        return

    for trade in impulse_trades:
        print(f"\n[{trade['timestamp'][:10]}] {trade['symbol']} {trade['direction']}")
        print(f"  结果：{trade['result']} | PnL: {trade['pnl_percent']:+.2f}%")
        print(f"  理由：{trade.get('reason', 'N/A')}")

        signals = trade.get("impulse_signals", [])
        if signals:
            print(f"  风险信号:")
            for signal in signals:
                print(f"    - {signal['type']}: {signal['message']}")


def analyze_single_trade(args):
    """Analyze a single trade for impulse signals."""
    trades = load_trades()

    # Find the trade by ID
    target_trade = None
    for trade in trades:
        if trade["id"] == args.trade_id:
            target_trade = trade
            break

    if not target_trade:
        print(f"未找到交易 ID: {args.trade_id}")
        return

    # Analyze this trade with context from previous trades
    trade_index = trades.index(target_trade)
    previous_trades = trades[:trade_index]

    signals = detect_impulse_trade(target_trade, previous_trades)

    if args.json:
        output = {
            "trade_id": target_trade["id"],
            "trade": target_trade,
            "impulse_signals": signals,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    # Print readable output
    print(f"\n交易分析：{target_trade['symbol']} {target_trade['direction']}")
    print(f"时间：{target_trade['timestamp']}")
    print(f"结果：{target_trade['result']} | PnL: {target_trade['pnl_percent']:+.2f}%")
    print(f"理由：{target_trade.get('reason', 'N/A')}")

    if signals:
        print(f"\n检测到 {len(signals)} 个风险信号:")
        for signal in signals:
            print(f"\n  [{signal['type']}] - {signal['severity'].upper()}")
            print(f"  {signal['message']}")
            print(f"  建议：{signal['suggestion']}")
    else:
        print("\n[OK] 未检测到冲动交易信号，这是一次理性决策")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze impulse trading patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_impulse.py                    # Full report
  python analyze_impulse.py --json             # JSON output for AI
  python analyze_impulse.py --detail           # Detailed breakdown
  python analyze_impulse.py --trade abc123     # Analyze single trade
        """
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON for AI consumption"
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show detailed breakdown of each impulse trade"
    )
    parser.add_argument(
        "--trade-id",
        dest="trade_id",
        help="Analyze a specific trade by ID"
    )

    args = parser.parse_args()

    if args.trade_id:
        analyze_single_trade(args)
    else:
        analyze_impulse_trades(args)


if __name__ == "__main__":
    main()
