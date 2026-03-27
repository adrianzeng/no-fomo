#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze price action and moving average patterns from trade data.

This script identifies K-line patterns, support/resistance levels,
and moving average interactions to help traders learn technical analysis.
"""

import sys
import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

# Import analysis utilities
sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import (
    detect_price_action_pattern,
    PRICE_ACTION_PATTERNS,
    MA_PATTERNS,
)


def load_trades():
    """Load trades from JSON file."""
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def extract_price_levels(reason: str) -> list:
    """Extract price levels mentioned in the reason."""
    # Match numbers that look like prices (4+ digits)
    prices = re.findall(r'\b(\d{4,})\b', reason)
    return list(set(prices))


def extract_ma_references(reason: str) -> list:
    """Extract moving average references."""
    ma_refs = []

    # Match patterns like "MA5", "MA10", "EMA20"
    ma_patterns = re.findall(r'\b(MA|EMA|SMA)\s*(\d+)?\b', reason, re.IGNORECASE)
    for ma_type, period in ma_patterns:
        ma_refs.append(f"{ma_type.upper()}{''.join(period) if period else ''}")

    # Match Chinese patterns like "均线", "五日线"
    if re.search(r'均线', reason):
        ma_refs.append("均线")
    if re.search(r'五日线', reason):
        ma_refs.append("MA5")
    if re.search(r'十日线', reason):
        ma_refs.append("MA10")
    if re.search(r'二十日线', reason):
        ma_refs.append("MA20")

    return ma_refs


def analyze_patterns_in_trades(trades: list) -> dict:
    """Analyze all trades for price action and MA patterns."""
    pattern_stats = defaultdict(lambda: {"total": 0, "wins": 0, "trades": []})
    ma_stats = defaultdict(lambda: {"total": 0, "wins": 0, "trades": []})

    for trade in trades:
        reason = trade.get("reason", "")
        if not reason:
            continue

        is_win = trade.get("result") == "WIN"

        # Analyze price action patterns
        pa_patterns = detect_price_action_pattern(reason)
        for pattern in pa_patterns:
            if pattern["type"] == "price_action":
                key = pattern["pattern"]
                pattern_stats[key]["total"] += 1
                if is_win:
                    pattern_stats[key]["wins"] += 1
                pattern_stats[key]["trades"].append(trade["id"])

        # Analyze MA patterns
        ma_patterns = detect_price_action_pattern(reason)
        for pattern in ma_patterns:
            if pattern["type"] == "ma_pattern":
                key = pattern["pattern"]
                ma_stats[key]["total"] += 1
                if is_win:
                    ma_stats[key]["wins"] += 1
                ma_stats[key]["trades"].append(trade["id"])

    # Calculate win rates
    for key in pattern_stats:
        if pattern_stats[key]["total"] > 0:
            pattern_stats[key]["win_rate"] = (
                pattern_stats[key]["wins"] / pattern_stats[key]["total"] * 100
            )
        else:
            pattern_stats[key]["win_rate"] = 0

    for key in ma_stats:
        if ma_stats[key]["total"] > 0:
            ma_stats[key]["win_rate"] = (
                ma_stats[key]["wins"] / ma_stats[key]["total"] * 100
            )
        else:
            ma_stats[key]["win_rate"] = 0

    return {
        "price_action": dict(pattern_stats),
        "ma_patterns": dict(ma_stats),
    }


def generate_pattern_insights(pattern_data: dict) -> list:
    """Generate insights from pattern analysis."""
    insights = []

    # Price action insights
    for pattern, stats in pattern_data.get("price_action", {}).items():
        if stats["total"] < 2:
            continue

        win_rate = stats["win_rate"]
        desc = PRICE_ACTION_PATTERNS.get(pattern, {}).get("description", pattern)

        if win_rate >= 60:
            insights.append({
                "type": "positive",
                "pattern": pattern,
                "description": desc,
                "win_rate": win_rate,
                "sample_size": stats["total"],
                "message": f"{desc} - 胜率 {win_rate:.0f}% (n={stats['total']})",
            })
        elif win_rate < 40:
            insights.append({
                "type": "negative",
                "pattern": pattern,
                "description": desc,
                "win_rate": win_rate,
                "sample_size": stats["total"],
                "message": f"{desc} - 胜率仅 {win_rate:.0f}% (n={stats['total']})",
            })

    # MA pattern insights
    for pattern, stats in pattern_data.get("ma_patterns", {}).items():
        if stats["total"] < 1:
            continue

        win_rate = stats["win_rate"]
        desc = MA_PATTERNS.get(pattern, {}).get("description", pattern)

        if win_rate >= 60:
            insights.append({
                "type": "positive",
                "pattern": pattern,
                "description": desc,
                "win_rate": win_rate,
                "sample_size": stats["total"],
                "message": f"{desc} - 胜率 {win_rate:.0f}% (n={stats['total']})",
            })
        elif win_rate < 40:
            insights.append({
                "type": "negative",
                "pattern": pattern,
                "description": desc,
                "win_rate": win_rate,
                "sample_size": stats["total"],
                "message": f"{desc} - 胜率仅 {win_rate:.0f}% (n={stats['total']})",
            })

    # Sort by win rate
    insights.sort(key=lambda x: x["win_rate"], reverse=True)

    return insights


def print_pattern_report(pattern_data: dict, insights: list):
    """Print formatted pattern analysis report."""
    print("=" * 60)
    print("K 线形态与均线模式分析报告")
    print("=" * 60)

    # Price Action Patterns
    print("\n【价格行为模式】")
    print("-" * 40)

    pa_data = pattern_data.get("price_action", {})
    if not pa_data:
        print("  暂无价格行为模式数据")
    else:
        for pattern, stats in sorted(pa_data.items(), key=lambda x: x[1]["win_rate"], reverse=True):
            desc = PRICE_ACTION_PATTERNS.get(pattern, {}).get("description", pattern)
            indicator = "[+]" if stats["win_rate"] >= 50 else "[-]"
            print(f"  {indicator} {desc}")
            print(f"      胜率：{stats['win_rate']:.0f}% (n={stats['total']})")

    # MA Patterns
    print("\n【均线模式】")
    print("-" * 40)

    ma_data = pattern_data.get("ma_patterns", {})
    if not ma_data:
        print("  暂无均线模式数据")
    else:
        for pattern, stats in sorted(ma_data.items(), key=lambda x: x[1]["win_rate"], reverse=True):
            desc = MA_PATTERNS.get(pattern, {}).get("description", pattern)
            indicator = "[+]" if stats["win_rate"] >= 50 else "[-]"
            print(f"  {indicator} {desc}")
            print(f"      胜率：{stats['win_rate']:.0f}% (n={stats['total']})")

    # Insights
    if insights:
        print("\n【关键洞察】")
        print("-" * 40)
        for insight in insights[:5]:
            if insight["type"] == "positive":
                print(f"  [✓] {insight['message']}")
            else:
                print(f"  [!] {insight['message']}")

    # Learning suggestions
    print("\n【学习建议】")
    print("-" * 40)

    high_win_patterns = [i for i in insights if i["type"] == "positive" and i["sample_size"] >= 3]
    low_win_patterns = [i for i in insights if i["type"] == "negative"]

    if high_win_patterns:
        print("  继续保持的模式:")
        for p in high_win_patterns[:3]:
            print(f"    • {p['description']} (胜率 {p['win_rate']:.0f}%)")

    if low_win_patterns:
        print("  需要改进的模式:")
        for p in low_win_patterns[:3]:
            print(f"    • {p['description']} (胜率 {p['win_rate']:.0f}%)")

    if not high_win_patterns and not low_win_patterns:
        print("  继续积累交易数据以获取更准确的分析")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze price action and MA patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_patterns.py              # Full report
  python analyze_patterns.py --json       # JSON output
  python analyze_patterns.py --symbol BTCUSDT  # Filter by symbol
        """
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--symbol",
        help="Filter by symbol"
    )

    args = parser.parse_args()

    trades = load_trades()

    if not trades:
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    # Filter by symbol if specified
    if args.symbol:
        trades = [t for t in trades if t.get("symbol") == args.symbol.upper()]
        if not trades:
            print(f"没有找到 {args.symbol} 的交易记录")
            return

    # Analyze patterns
    pattern_data = analyze_patterns_in_trades(trades)
    insights = generate_pattern_insights(pattern_data)

    if args.json:
        output = {
            "pattern_data": pattern_data,
            "insights": insights,
            "total_trades_analyzed": len(trades),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print_pattern_report(pattern_data, insights)


if __name__ == "__main__":
    main()
