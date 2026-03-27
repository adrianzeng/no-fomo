#!/usr/bin/env python3
"""
Generate trading rules from historical trade data.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"
RULES_FILE = DATA_DIR / "learned_rules.json"


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


def generate_rules(trades, min_trades=5, confidence_threshold=65):
    rules = []

    directions = defaultdict(list)
    for trade in trades:
        directions[trade["direction"]].append(trade)

    for direction, group in directions.items():
        if len(group) < min_trades:
            continue
        win_rate, n = calculate_win_rate(group)
        if win_rate >= confidence_threshold:
            rules.append(
                {
                    "type": "PREFER",
                    "category": "direction",
                    "condition": f"direction == {direction}",
                    "rule": f"PREFER {direction} positions",
                    "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                    "win_rate": win_rate,
                    "sample_size": n,
                    "confidence": "HIGH" if n >= 10 else "MEDIUM",
                }
            )
        elif win_rate <= (100 - confidence_threshold):
            rules.append(
                {
                    "type": "AVOID",
                    "category": "direction",
                    "condition": f"direction == {direction}",
                    "rule": f"AVOID {direction} positions",
                    "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                    "win_rate": win_rate,
                    "sample_size": n,
                    "confidence": "HIGH" if n >= 10 else "MEDIUM",
                }
            )

    days = defaultdict(list)
    for trade in trades:
        day = trade.get("day_of_week")
        if day:
            days[day].append(trade)

    for day, group in days.items():
        if len(group) < min_trades:
            continue
        win_rate, n = calculate_win_rate(group)
        if win_rate >= confidence_threshold + 10:
            rules.append(
                {
                    "type": "PREFER",
                    "category": "timing",
                    "condition": f"day_of_week == {day}",
                    "rule": f"PREFER trading on {day.title()}",
                    "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                    "win_rate": win_rate,
                    "sample_size": n,
                    "confidence": "HIGH" if n >= 10 else "MEDIUM",
                }
            )
        elif win_rate <= (100 - confidence_threshold - 10):
            rules.append(
                {
                    "type": "AVOID",
                    "category": "timing",
                    "condition": f"day_of_week == {day}",
                    "rule": f"AVOID trading on {day.title()}",
                    "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                    "win_rate": win_rate,
                    "sample_size": n,
                    "confidence": "HIGH" if n >= 10 else "MEDIUM",
                }
            )

    high_leverage = [trade for trade in trades if trade.get("leverage") and trade["leverage"] >= 10]
    if len(high_leverage) >= min_trades:
        win_rate, n = calculate_win_rate(high_leverage)
        if win_rate <= 45:
            rules.append(
                {
                    "type": "AVOID",
                    "category": "risk",
                    "condition": "leverage >= 10",
                    "rule": "AVOID leverage >= 10x",
                    "evidence": f"Win rate: {win_rate:.0f}% over {n} high-leverage trades",
                    "win_rate": win_rate,
                    "sample_size": n,
                    "confidence": "HIGH" if n >= 10 else "MEDIUM",
                }
            )

    rsi_trades = [trade for trade in trades if trade.get("indicators", {}).get("rsi") is not None]
    oversold = [trade for trade in rsi_trades if trade["indicators"]["rsi"] < 30]
    overbought = [trade for trade in rsi_trades if trade["indicators"]["rsi"] > 70]

    if len(oversold) >= min_trades:
        oversold_longs = [trade for trade in oversold if trade["direction"] == "LONG"]
        if len(oversold_longs) >= 3:
            win_rate, n = calculate_win_rate(oversold_longs)
            if win_rate >= confidence_threshold:
                rules.append(
                    {
                        "type": "PREFER",
                        "category": "indicator",
                        "condition": "RSI < 30 AND direction == LONG",
                        "rule": "PREFER LONG when RSI < 30 (oversold)",
                        "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                        "win_rate": win_rate,
                        "sample_size": n,
                        "confidence": "HIGH" if n >= 10 else "MEDIUM",
                    }
                )

    if len(overbought) >= min_trades:
        overbought_shorts = [trade for trade in overbought if trade["direction"] == "SHORT"]
        if len(overbought_shorts) >= 3:
            win_rate, n = calculate_win_rate(overbought_shorts)
            if win_rate >= confidence_threshold:
                rules.append(
                    {
                        "type": "PREFER",
                        "category": "indicator",
                        "condition": "RSI > 70 AND direction == SHORT",
                        "rule": "PREFER SHORT when RSI > 70 (overbought)",
                        "evidence": f"Win rate: {win_rate:.0f}% over {n} trades",
                        "win_rate": win_rate,
                        "sample_size": n,
                        "confidence": "HIGH" if n >= 10 else "MEDIUM",
                    }
                )

    rules.sort(key=lambda item: (item["confidence"] == "HIGH", item["win_rate"]), reverse=True)
    return rules


def save_rules(rules):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "total_rules": len(rules),
        "rules": rules,
    }
    with open(RULES_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return RULES_FILE


def main():
    trades = load_trades()
    if not trades:
        print("No trades logged yet. Log some trades first.")
        return

    if len(trades) < 5:
        print(f"Only {len(trades)} trades. Need at least 5 for rule generation.")
        print("Keep logging trades to discover patterns.")
        return

    rules = generate_rules(trades)

    print(
        f"""
LEARNED TRADING RULES
{'=' * 50}
Generated from {len(trades)} trades
{'=' * 50}
"""
    )

    if not rules:
        print("Not enough data to generate confident rules yet.")
        print("Keep trading. Patterns will emerge with more data.")
        return

    prefer_rules = [rule for rule in rules if rule["type"] == "PREFER"]
    avoid_rules = [rule for rule in rules if rule["type"] == "AVOID"]

    if prefer_rules:
        print("PREFER (high win rate patterns):\n")
        for rule in prefer_rules:
            confidence = "[HIGH]" if rule["confidence"] == "HIGH" else "[MEDIUM]"
            print(f"   {confidence} {rule['rule']}")
            print(f"      - {rule['evidence']}\n")

    if avoid_rules:
        print("AVOID (low win rate patterns):\n")
        for rule in avoid_rules:
            confidence = "[HIGH]" if rule["confidence"] == "HIGH" else "[MEDIUM]"
            print(f"   {confidence} {rule['rule']}")
            print(f"      - {rule['evidence']}\n")

    rules_file = save_rules(rules)
    print(f"Rules saved to: {rules_file}")


if __name__ == "__main__":
    main()
