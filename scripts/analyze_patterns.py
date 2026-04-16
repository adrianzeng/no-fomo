#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze price action and moving average patterns from trade data.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import MA_PATTERNS, PRICE_ACTION_PATTERNS, detect_price_action_pattern  # noqa: E402


def build_json_response(report_type, data=None, error=None):
    response = {
        "meta": {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "status": "error" if error else "ok",
        }
    }
    if error:
        response["error"] = error
    else:
        response["data"] = data
    return response


def load_trades():
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def analyze_patterns_in_trades(trades):
    pattern_stats = defaultdict(lambda: {"total": 0, "wins": 0, "trades": []})
    ma_stats = defaultdict(lambda: {"total": 0, "wins": 0, "trades": []})

    for trade in trades:
        reason = trade.get("reason", "")
        if not reason:
            continue
        detected_patterns = detect_price_action_pattern(reason)
        is_win = trade.get("result") == "WIN"
        for pattern in detected_patterns:
            target = pattern_stats if pattern["type"] == "price_action" else ma_stats
            key = pattern["pattern"]
            target[key]["total"] += 1
            if is_win:
                target[key]["wins"] += 1
            target[key]["trades"].append(trade["id"])

    for stats_map in (pattern_stats, ma_stats):
        for stats in stats_map.values():
            stats["win_rate"] = (stats["wins"] / stats["total"] * 100) if stats["total"] else 0

    return {"price_action": dict(pattern_stats), "ma_patterns": dict(ma_stats)}


def generate_pattern_insights(pattern_data):
    insights = []

    for pattern, stats in pattern_data.get("price_action", {}).items():
        if stats["total"] < 2:
            continue
        description = PRICE_ACTION_PATTERNS.get(pattern, {}).get("description", pattern)
        if stats["win_rate"] >= 60:
            insight_type = "positive"
        elif stats["win_rate"] < 40:
            insight_type = "negative"
        else:
            continue
        insights.append({
            "type": insight_type,
            "pattern": pattern,
            "description": description,
            "win_rate": stats["win_rate"],
            "sample_size": stats["total"],
            "message": f"{description} - 胜率 {stats['win_rate']:.0f}% (n={stats['total']})",
        })

    for pattern, stats in pattern_data.get("ma_patterns", {}).items():
        if stats["total"] < 1:
            continue
        description = MA_PATTERNS.get(pattern, {}).get("description", pattern)
        if stats["win_rate"] >= 60:
            insight_type = "positive"
        elif stats["win_rate"] < 40:
            insight_type = "negative"
        else:
            continue
        insights.append({
            "type": insight_type,
            "pattern": pattern,
            "description": description,
            "win_rate": stats["win_rate"],
            "sample_size": stats["total"],
            "message": f"{description} - 胜率 {stats['win_rate']:.0f}% (n={stats['total']})",
        })

    insights.sort(key=lambda item: item["win_rate"], reverse=True)
    return insights


def print_pattern_report(pattern_data, insights):
    print("=" * 60)
    print("价格行为与均线模式分析报告")
    print("=" * 60)

    print("\n[价格行为模式]")
    print("-" * 40)
    pa_data = pattern_data.get("price_action", {})
    if not pa_data:
        print("  暂无价格行为模式数据")
    else:
        for pattern, stats in sorted(pa_data.items(), key=lambda item: item[1]["win_rate"], reverse=True):
            description = PRICE_ACTION_PATTERNS.get(pattern, {}).get("description", pattern)
            indicator = "[+]" if stats["win_rate"] >= 50 else "[-]"
            print(f"  {indicator} {description}")
            print(f"      胜率：{stats['win_rate']:.0f}% (n={stats['total']})")

    print("\n[均线模式]")
    print("-" * 40)
    ma_data = pattern_data.get("ma_patterns", {})
    if not ma_data:
        print("  暂无均线模式数据")
    else:
        for pattern, stats in sorted(ma_data.items(), key=lambda item: item[1]["win_rate"], reverse=True):
            description = MA_PATTERNS.get(pattern, {}).get("description", pattern)
            indicator = "[+]" if stats["win_rate"] >= 50 else "[-]"
            print(f"  {indicator} {description}")
            print(f"      胜率：{stats['win_rate']:.0f}% (n={stats['total']})")

    if insights:
        print("\n[关键洞察]")
        print("-" * 40)
        for insight in insights[:5]:
            prefix = "[OK]" if insight["type"] == "positive" else "[!]"
            print(f"  {prefix} {insight['message']}")

    print("\n[学习建议]")
    print("-" * 40)
    high_win_patterns = [item for item in insights if item["type"] == "positive" and item["sample_size"] >= 3]
    low_win_patterns = [item for item in insights if item["type"] == "negative"]
    if high_win_patterns:
        print("  继续保持的模式：")
        for pattern in high_win_patterns[:3]:
            print(f"    - {pattern['description']} (胜率 {pattern['win_rate']:.0f}%)")
    if low_win_patterns:
        print("  需要改进的模式：")
        for pattern in low_win_patterns[:3]:
            print(f"    - {pattern['description']} (胜率 {pattern['win_rate']:.0f}%)")
    if not high_win_patterns and not low_win_patterns:
        print("  继续积累交易数据，以获得更准确的模式结论。")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze price action and MA patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_patterns.py
  python analyze_patterns.py --json
  python analyze_patterns.py --symbol BTCUSDT
        """,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--symbol", help="Filter by symbol")
    args = parser.parse_args()

    trades = load_trades()
    if not trades:
        if args.json:
            print(json.dumps(build_json_response(
                "pattern_analysis",
                error={"code": "no_trades", "message": "No trades logged yet."},
            ), indent=2, ensure_ascii=False))
            return
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    if args.symbol:
        trades = [trade for trade in trades if trade.get("symbol") == args.symbol.upper()]
        if not trades:
            if args.json:
                print(json.dumps(build_json_response(
                    "pattern_analysis",
                    error={"code": "no_matching_trades", "message": f"No trades found for symbol: {args.symbol.upper()}"},
                ), indent=2, ensure_ascii=False))
                return
            print(f"没有找到 {args.symbol.upper()} 的交易记录。")
            return

    pattern_data = analyze_patterns_in_trades(trades)
    insights = generate_pattern_insights(pattern_data)

    if args.json:
        output = {
            "pattern_data": pattern_data,
            "insights": insights,
            "total_trades_analyzed": len(trades),
        }
        print(json.dumps(build_json_response("pattern_analysis", data=output), indent=2, ensure_ascii=False))
        return

    print_pattern_report(pattern_data, insights)


if __name__ == "__main__":
    main()
