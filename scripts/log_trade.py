#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Log trades with full context for self-learning analysis.
Includes reason quality analysis, impulse trade detection, and optional AI post-trade review.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

from ai_client import AIReviewError, request_ai_review
from trade_analysis_utils import analyze_reason_quality, detect_impulse_trade, detect_price_action_pattern


DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"
AI_REVIEWS_FILE = DATA_DIR / "ai_reviews.json"


def load_trades() -> dict[str, Any]:
    if TRADES_FILE.exists():
        with open(TRADES_FILE, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"trades": [], "metadata": {"created": datetime.now().isoformat()}}


def save_trades(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data.setdefault("metadata", {})
    data["metadata"]["updated"] = datetime.now().isoformat()
    with open(TRADES_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def load_ai_reviews() -> dict[str, Any]:
    if not AI_REVIEWS_FILE.exists():
        return {"reviews": [], "metadata": {"created": datetime.now().isoformat()}}
    with open(AI_REVIEWS_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_ai_review(entry: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = load_ai_reviews()
    data.setdefault("reviews", [])
    data.setdefault("metadata", {})
    data["reviews"].append(entry)
    data["metadata"]["updated"] = datetime.now().isoformat()
    with open(AI_REVIEWS_FILE, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def build_post_trade_payload(trade: dict[str, Any], reason_analysis: dict[str, Any], impulse_signals: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = detect_price_action_pattern(trade.get("reason", "") or "")
    return {
        "trade": {
            "id": trade["id"],
            "symbol": trade["symbol"],
            "direction": trade["direction"],
            "entry": trade["entry"],
            "exit": trade["exit"],
            "pnl_percent": trade["pnl_percent"],
            "result": trade["result"],
            "timeframe": trade.get("timeframe"),
            "leverage": trade.get("leverage"),
        },
        "reason_text": trade.get("reason", ""),
        "reason_quality": {
            "score": reason_analysis["score"],
            "level": reason_analysis["level"],
            "feedback": reason_analysis["feedback"],
        },
        "detected_patterns": [pattern.get("description", "") for pattern in patterns],
        "impulse_signals": impulse_signals,
        "notes": trade.get("notes"),
        "market_context": trade.get("market_context", {}),
        "indicators": trade.get("indicators", {}),
    }


def run_post_trade_ai_review(trade: dict[str, Any], reason_analysis: dict[str, Any], impulse_signals: list[dict[str, Any]]) -> dict[str, Any]:
    payload = build_post_trade_payload(trade, reason_analysis, impulse_signals)
    try:
        review = request_ai_review(payload, review_type="post_trade")
        ai_result = {"success": True, "review": review}
    except AIReviewError as exc:
        ai_result = {
            "success": False,
            "error": {"code": exc.code, "message": exc.message},
        }

    save_ai_review({
        "timestamp": datetime.now().isoformat(),
        "review_type": "post_trade",
        "request": payload,
        "rule_check_summary": {
            "reason_quality": {
                "score": reason_analysis["score"],
                "level": reason_analysis["level"],
            },
            "impulse_signal_count": len(impulse_signals),
        },
        "ai_review": ai_result,
        "success": ai_result["success"],
        "error": None if ai_result["success"] else ai_result["error"],
    })

    return ai_result


def log_trade(args: argparse.Namespace) -> dict[str, Any]:
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

    reason_analysis = analyze_reason_quality(args.reason or "")
    trade["reason_quality"] = {
        "score": reason_analysis["score"],
        "level": reason_analysis["level"],
        "feedback": reason_analysis["feedback"],
    }

    recent_trades = data.get("trades", [])
    impulse_signals = detect_impulse_trade(trade, recent_trades)
    if impulse_signals:
        trade["impulse_signals"] = impulse_signals

    if args.ai:
        trade["ai_review"] = run_post_trade_ai_review(trade, reason_analysis, impulse_signals)

    data["trades"].append(trade)
    save_trades(data)

    label = "[WIN]" if trade["result"] == "WIN" else "[LOSS]"
    print(f"{label} 已记录交易：{trade['symbol']} {trade['direction']} | PnL: {trade['pnl_percent']:+.2f}% | ID: {trade['id']}")
    print_reason_quality_feedback(reason_analysis)

    if impulse_signals:
        print_impulse_warnings(impulse_signals)

    if args.ai:
        print_post_trade_ai_review(trade.get("ai_review", {}))

    return trade


def print_reason_quality_feedback(analysis: Dict[str, Any]) -> None:
    """Print reason quality feedback with ASCII-friendly indicators."""
    level = analysis.get("level", "UNKNOWN")

    if level in ["EXCELLENT", "GOOD"]:
        indicator = "[OK]"
    elif level == "WARNING":
        indicator = "[!]"
    else:
        indicator = "[!!]"

    print(f"\n{indicator} 理由质量：{level} (得分：{analysis['score']}/100)")
    print(f"    {analysis['feedback']}")

    if analysis.get("positive_signals"):
        print(f"    优点标签：{', '.join(analysis['positive_signals'])}")

    if analysis.get("signals"):
        print(f"    风险标签：{', '.join(analysis['signals'])}")


def print_impulse_warnings(signals: List[Dict[str, Any]]) -> None:
    """Print impulse trading warnings."""
    print(f"\n[WARNING] 检测到 {len(signals)} 个潜在风险信号")
    for signal in signals:
        print(f"  - [{signal['type']}] {signal['message']}")
        print(f"    建议：{signal['suggestion']}")


def print_post_trade_ai_review(ai_review: dict[str, Any]) -> None:
    print("\n[AI 复盘]")
    print("-" * 40)
    if ai_review.get("success"):
        review = ai_review["review"]
        print(f"  评分：{review['score']}/100")
        print(f"  结论：{review['verdict']}")
        if review.get("strengths"):
            print("  做得好的地方：")
            for item in review["strengths"]:
                print(f"    - {item}")
        if review.get("risks"):
            print("  需要警惕的问题：")
            for item in review["risks"]:
                print(f"    - {item}")
        print(f"  下次行动：{review['action']}")
        print(f"  正向反馈：{review['encouragement']}")
    else:
        error = ai_review.get("error", {})
        print(f"  [!] AI 复盘未完成：{error.get('message', '未知错误')}")


def list_trades(args: argparse.Namespace) -> None:
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


def show_stats() -> None:
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
    profit_factor = abs(avg_win / avg_loss) if avg_loss else None
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

Profit Factor:   {f'{profit_factor:.2f}x' if profit_factor is not None else 'N/A (no losing trades yet)'} (if > 1 = profitable)
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


def main() -> None:
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
    parser.add_argument("--ai", action="store_true", help="Run AI post-trade review after logging the trade")
    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.list or args.last:
        list_trades(args)
    elif args.symbol and args.direction and args.entry and args.exit and args.pnl_percent is not None and args.result:
        log_trade(args)
    else:
        parser.print_help()
        print("\nTo log a trade, provide: --symbol, --direction, --entry, --exit, --pnl_percent, --result")


if __name__ == "__main__":
    main()
