#!/usr/bin/env python3
"""
Analyze trade patterns to discover what works and what doesn't.
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"


def load_trades():
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def calculate_win_rate(trades):
    if not trades:
        return 0, 0
    wins = len([trade for trade in trades if trade["result"] == "WIN"])
    return wins / len(trades) * 100, len(trades)


def analyze_by_field(trades, field, min_trades=3):
    groups = defaultdict(list)
    for trade in trades:
        value = trade.get(field)
        if value is not None:
            groups[value].append(trade)

    results = []
    for value, group_trades in groups.items():
        if len(group_trades) < min_trades:
            continue
        win_rate, n = calculate_win_rate(group_trades)
        avg_pnl = sum(trade["pnl_percent"] for trade in group_trades) / n
        results.append(
            {
                "value": value,
                "win_rate": win_rate,
                "n": n,
                "avg_pnl": avg_pnl,
            }
        )

    return sorted(results, key=lambda item: item["win_rate"], reverse=True)


def analyze_by_indicator(trades, indicator_name, ranges, min_trades=3):
    results = []
    for range_name, (low, high) in ranges.items():
        matching = []
        for trade in trades:
            indicator_value = trade.get("indicators", {}).get(indicator_name)
            if indicator_value is not None and low <= indicator_value < high:
                matching.append(trade)

        if len(matching) < min_trades:
            continue

        win_rate, n = calculate_win_rate(matching)
        results.append({"range": range_name, "win_rate": win_rate, "n": n})

    return results


def generate_insights(trades, min_trades=3):
    insights = []
    overall_win_rate, _ = calculate_win_rate(trades)

    direction_stats = analyze_by_field(trades, "direction", min_trades)
    for stat in direction_stats:
        diff = stat["win_rate"] - overall_win_rate
        if abs(diff) > 10:
            insights.append(
                {
                    "type": "direction",
                    "label": "[+]" if diff > 0 else "[!]",
                    "action": "PREFER" if diff > 0 else "CAUTION",
                    "message": f"{stat['value']} trades (win rate: {stat['win_rate']:.0f}%, n={stat['n']})",
                    "impact": diff,
                }
            )

    day_stats = analyze_by_field(trades, "day_of_week", min_trades)
    for stat in day_stats:
        diff = stat["win_rate"] - overall_win_rate
        if abs(diff) > 15:
            insights.append(
                {
                    "type": "day",
                    "label": "[+]" if diff > 0 else "[-]",
                    "action": "PREFER" if diff > 0 else "AVOID",
                    "message": f"Trading on {stat['value'].title()} (win rate: {stat['win_rate']:.0f}%, n={stat['n']})",
                    "impact": diff,
                }
            )

    leverage_stats = analyze_by_field(trades, "leverage", min_trades)
    for stat in leverage_stats:
        if stat["value"] and stat["value"] >= 10 and stat["win_rate"] < 50:
            insights.append(
                {
                    "type": "leverage",
                    "label": "[!]",
                    "action": "CAUTION",
                    "message": f"High leverage ({stat['value']}x) trades (win rate: {stat['win_rate']:.0f}%, n={stat['n']})",
                    "impact": stat["win_rate"] - overall_win_rate,
                }
            )

    rsi_ranges = {
        "oversold (<30)": (0, 30),
        "neutral (30-70)": (30, 70),
        "overbought (>70)": (70, 100),
    }
    if any(trade.get("indicators", {}).get("rsi") is not None for trade in trades):
        for stat in analyze_by_indicator(trades, "rsi", rsi_ranges, min_trades):
            diff = stat["win_rate"] - overall_win_rate
            if abs(diff) > 15:
                insights.append(
                    {
                        "type": "rsi",
                        "label": "[+]" if diff > 0 else "[-]",
                        "action": "PREFER" if diff > 0 else "AVOID",
                        "message": f"RSI {stat['range']} (win rate: {stat['win_rate']:.0f}%, n={stat['n']})",
                        "impact": diff,
                    }
                )

    insights.sort(key=lambda item: abs(item["impact"]), reverse=True)
    return insights


def main():
    parser = argparse.ArgumentParser(description="Analyze trading patterns")
    parser.add_argument("--symbol", help="Filter by symbol")
    parser.add_argument("--direction", help="Filter by direction")
    parser.add_argument("--min-trades", type=int, default=3, help="Minimum trades for analysis")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    trades = load_trades()
    if not trades:
        print("No trades logged yet. Use log_trade.py to log your first trade.")
        return

    if args.symbol:
        trades = [trade for trade in trades if trade["symbol"] == args.symbol.upper()]
    if args.direction:
        trades = [trade for trade in trades if trade["direction"] == args.direction.upper()]

    if len(trades) < args.min_trades:
        print(f"Not enough trades ({len(trades)}) for meaningful analysis. Need at least {args.min_trades}.")
        return

    overall_win_rate, total = calculate_win_rate(trades)
    total_pnl = sum(trade["pnl_percent"] for trade in trades)

    print(
        f"""
TRADE PATTERN ANALYSIS
{'=' * 50}

Overall Performance:
   Total Trades: {total}
   Win Rate: {overall_win_rate:.1f}%
   Total PnL: {total_pnl:+.2f}%
"""
    )

    print("By Direction:")
    for stat in analyze_by_field(trades, "direction", args.min_trades):
        label = "[+]" if stat["win_rate"] >= 50 else "[-]"
        print(f"   {label} {stat['value']}: {stat['win_rate']:.0f}% win rate (n={stat['n']}, avg PnL: {stat['avg_pnl']:+.2f}%)")

    day_stats = analyze_by_field(trades, "day_of_week", args.min_trades)
    if day_stats:
        print("\nBy Day of Week:")
        for stat in day_stats:
            label = "[+]" if stat["win_rate"] >= 50 else "[-]"
            print(f"   {label} {stat['value'].title()}: {stat['win_rate']:.0f}% (n={stat['n']})")

    timeframe_stats = analyze_by_field(trades, "timeframe", args.min_trades)
    if timeframe_stats:
        print("\nBy Timeframe:")
        for stat in timeframe_stats:
            label = "[+]" if stat["win_rate"] >= 50 else "[-]"
            print(f"   {label} {stat['value']}: {stat['win_rate']:.0f}% (n={stat['n']}, avg PnL: {stat['avg_pnl']:+.2f}%)")

    symbol_stats = analyze_by_field(trades, "symbol", args.min_trades)
    if len(symbol_stats) > 1:
        print("\nBy Symbol:")
        for stat in symbol_stats:
            label = "[+]" if stat["win_rate"] >= 50 else "[-]"
            print(f"   {label} {stat['value']}: {stat['win_rate']:.0f}% (n={stat['n']})")

    insights = generate_insights(trades, args.min_trades)
    if insights:
        print(f"\n{'=' * 50}")
        print("KEY INSIGHTS:")
        print(f"{'=' * 50}\n")
        for insight in insights[:5]:
            print(f"{insight['label']} {insight['action']}: {insight['message']}")
        print()

    if args.json:
        output = {
            "overall": {"win_rate": overall_win_rate, "total_trades": total, "total_pnl": total_pnl},
            "by_direction": analyze_by_field(trades, "direction", args.min_trades),
            "by_day": day_stats,
            "insights": insights,
        }
        print("\nJSON Output:")
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
