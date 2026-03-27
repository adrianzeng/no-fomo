#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Log trades with full context for self-learning analysis.
Includes reason quality analysis and impulse trade detection.
"""

import argparse
import json
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Fix Windows console encoding for Chinese characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from trade_analysis_utils import (
    analyze_reason_quality,
    detect_impulse_trade,
)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"


def load_trades():
    if TRADES_FILE.exists():
        with open(TRADES_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"trades": [], "metadata": {"created": datetime.now().isoformat()}}


def save_trades(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data.setdefault("metadata", {})
    data["metadata"]["updated"] = datetime.now().isoformat()
    with open(TRADES_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def log_trade(args):
    data = load_trades()
    now = datetime.now()

    trade = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": now.isoformat(),
        "symbol": args.symbol.upper(),
        "direction": args.direction.upper(),
        "entry": float(args.entry),
        "exit": float(args.exit),
        "pnl_percent": float(args.pnl_percent),
        "result": args.result.upper(),
        "leverage": int(args.leverage) if args.leverage else None,
        "reason": args.reason,
        "indicators": json.loads(args.indicators) if args.indicators else {},
        "market_context": json.loads(args.market_context) if args.market_context else {},
        "notes": args.notes,
        "day_of_week": now.strftime("%A").lower(),
        "hour": now.hour,
        "timeframe": args.timeframe.upper() if args.timeframe else None,
    }

    # Analyze reason quality
    reason_analysis = analyze_reason_quality(args.reason or "")
    trade["reason_quality"] = {
        "score": reason_analysis["score"],
        "level": reason_analysis["level"],
        "feedback": reason_analysis["feedback"],
    }

    # Detect impulse signals
    recent_trades = data.get("trades", [])
    impulse_signals = detect_impulse_trade(trade, recent_trades)
    if impulse_signals:
        trade["impulse_signals"] = impulse_signals

    data["trades"].append(trade)
    save_trades(data)

    label = "[WIN]" if trade["result"] == "WIN" else "[LOSS]"
    print(f"{label} Trade logged: {trade['symbol']} {trade['direction']} | PnL: {trade['pnl_percent']:+.2f}% | ID: {trade['id']}")

    # Print reason quality feedback
    print_reason_quality_feedback(reason_analysis)

    # Print impulse warnings if any
    if impulse_signals:
        print_impulse_warnings(impulse_signals)

    return trade


def print_reason_quality_feedback(analysis: Dict):
    """Print reason quality feedback with color-coded output."""
    level = analysis.get("level", "UNKNOWN")

    # ASCII-friendly color indicators
    if level in ["EXCELLENT", "GOOD"]:
        indicator = "[OK]"
    elif level == "WARNING":
        indicator = "[!]"
    else:
        indicator = "[!!]"

    print(f"\n{indicator} 理由质量：{level} (得分：{analysis['score']}/100)")
    print(f"    {analysis['feedback']}")

    if analysis.get("positive_signals"):
        print(f"    优点：{', '.join(analysis['positive_signals'])}")

    if analysis.get("signals"):
        print(f"    警告：{', '.join(analysis['signals'])}")


def print_impulse_warnings(signals: List[Dict]):
    """Print impulse trading warnings."""
    print(f"\n[WARNING] 检测到 {len(signals)} 个潜在风险信号:")
    for signal in signals:
        print(f"  - [{signal['type']}] {signal['message']}")
        print(f"    建议：{signal['suggestion']}")


def list_trades(args):
    data = load_trades()
    trades = data["trades"]
    if not trades:
        print("No trades logged yet.")
        return

    count = args.last if args.last else len(trades)
    recent = trades[-count:]

    print(f"\nLast {len(recent)} trades:\n")
    print(f"{'ID':<10} {'Date':<12} {'Symbol':<10} {'Dir':<6} {'PnL %':<8} {'Result':<6}")
    print("-" * 60)

    for trade in recent:
        timestamp = datetime.fromisoformat(trade["timestamp"]).strftime("%m/%d %H:%M")
        print(f"{trade['id']:<10} {timestamp:<12} {trade['symbol']:<10} {trade['direction']:<6} {trade['pnl_percent']:+.2f}%   {trade['result']}")


def show_stats():
    data = load_trades()
    trades = data["trades"]
    if not trades:
        print("No trades logged yet.")
        return

    wins = [trade for trade in trades if trade["result"] == "WIN"]
    losses = [trade for trade in trades if trade["result"] == "LOSS"]
    total_pnl = sum(trade["pnl_percent"] for trade in trades)
    avg_win = sum(trade["pnl_percent"] for trade in wins) / len(wins) if wins else 0
    avg_loss = sum(trade["pnl_percent"] for trade in losses) / len(losses) if losses else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss else 0
    win_rate = len(wins) / len(trades) * 100 if trades else 0

    print(
        f"""
TRADING STATISTICS
{'=' * 40}

Total Trades:    {len(trades)}
Wins:            {len(wins)} ({win_rate:.1f}%)
Losses:          {len(losses)} ({100 - win_rate:.1f}%)

Total PnL:       {total_pnl:+.2f}%
Avg Win:         {avg_win:+.2f}%
Avg Loss:        {avg_loss:+.2f}%

Profit Factor:   {profit_factor:.2f}x (if > 1 = profitable)
"""
    )

    longs = [trade for trade in trades if trade["direction"] == "LONG"]
    shorts = [trade for trade in trades if trade["direction"] == "SHORT"]

    if longs:
        long_wins = len([trade for trade in longs if trade["result"] == "WIN"])
        print(f"LONG Win Rate:   {long_wins / len(longs) * 100:.1f}% (n={len(longs)})")

    if shorts:
        short_wins = len([trade for trade in shorts if trade["result"] == "WIN"])
        print(f"SHORT Win Rate:  {short_wins / len(shorts) * 100:.1f}% (n={len(shorts)})")


def main():
    parser = argparse.ArgumentParser(description="Log and analyze trades")
    parser.add_argument("--list", action="store_true", help="List trades")
    parser.add_argument("--last", type=int, help="Show last N trades")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--symbol", help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument("--direction", choices=["LONG", "SHORT", "long", "short"], help="Trade direction")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--exit", type=float, help="Exit price")
    parser.add_argument("--pnl_percent", "--pnl", type=float, help="PnL percentage")
    parser.add_argument("--leverage", type=int, help="Leverage used")
    parser.add_argument("--reason", help="Reason for entry")
    parser.add_argument("--indicators", help="JSON string with indicators")
    parser.add_argument("--market_context", help="JSON string with market context")
    parser.add_argument("--result", choices=["WIN", "LOSS", "win", "loss"], help="Trade result")
    parser.add_argument("--notes", help="Additional notes")
    parser.add_argument("--timeframe", "-tf", help="Timeframe used for analysis (e.g., 15m, 1h, 4h, 1D)")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.list or args.last:
        list_trades(args)
    elif args.symbol and args.direction and args.entry and args.exit and args.pnl_percent and args.result:
        log_trade(args)
    else:
        parser.print_help()
        print("\nTo log a trade, provide: --symbol, --direction, --entry, --exit, --pnl_percent, --result")


if __name__ == "__main__":
    main()
