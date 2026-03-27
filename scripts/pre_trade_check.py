#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-trade checklist to help traders make rational decisions before entering a position.

This tool forces you to pause and think before opening a position,
checking for common pitfalls like FOMO, revenge trading, and poor risk management.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

# Import analysis utilities
sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import (
    analyze_reason_quality,
    detect_impulse_trade,
    detect_price_action_pattern,
)


def load_trades():
    """Load trades from JSON file."""
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def check_recent_losses(trades, minutes=60):
    """Check if there was a recent loss."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)

    for trade in reversed(trades):
        if trade.get("result") != "LOSS":
            continue
        try:
            trade_time = datetime.fromisoformat(trade["timestamp"])
            if trade_time >= cutoff:
                time_ago = (now - trade_time).total_seconds() / 60
                return {
                    "has_recent_loss": True,
                    "minutes_ago": int(time_ago),
                    "symbol": trade["symbol"],
                    "pnl_percent": trade["pnl_percent"],
                }
        except (KeyError, ValueError):
            continue

    return {"has_recent_loss": False}


def analyze_trading_pattern(trades, symbol, direction, timeframe=None):
    """Analyze historical performance for similar setups."""
    # Filter trades with same symbol and direction
    matching_trades = [
        t for t in trades
        if t.get("symbol") == symbol and t.get("direction") == direction
    ]

    # Filter by timeframe if provided
    if timeframe:
        matching_trades = [t for t in matching_trades if t.get("timeframe") == timeframe]

    if len(matching_trades) < 3:
        return {
            "sample_size": len(matching_trades),
            "win_rate": None,
            "message": "样本不足，继续积累数据",
        }

    wins = len([t for t in matching_trades if t.get("result") == "WIN"])
    win_rate = wins / len(matching_trades) * 100

    return {
        "sample_size": len(matching_trades),
        "win_rate": win_rate,
        "message": f"该模式下历史胜率：{win_rate:.0f}% (n={len(matching_trades)})",
    }


def run_pre_trade_check(args):
    """Run pre-trade checklist."""
    trades = load_trades()

    print("=" * 60)
    print("开仓前检查报告")
    print("=" * 60)

    # Basic trade info
    timeframe_str = f" ({args.timeframe.upper()})" if args.timeframe else ""
    print(f"\n交易计划：{args.symbol.upper()} {args.direction.upper()} @ {args.entry}{timeframe_str}")
    if args.stop_loss:
        risk = abs(float(args.entry) - float(args.stop_loss))
        reward = risk * (float(args.target) / float(args.entry) - 1) if args.target else 0
        rr = reward / risk if risk > 0 else 0
        print(f"止损：{args.stop_loss} | 目标：{args.target} | 盈亏比：{rr:.2f}:1")

    # 1. Reason Quality Check
    print("\n【理由质量】")
    print("-" * 40)

    reason = args.reason or ""
    reason_analysis = analyze_reason_quality(reason)

    score = reason_analysis["score"]
    level = reason_analysis["level"]

    if level in ["EXCELLENT", "GOOD"]:
        status = "✅"
    elif level == "WARNING":
        status = "⚠️"
    else:
        status = "❌"

    print(f"  {status} 评分：{score}/100 - {level}")
    print(f"  理由：{reason[:80] if reason else '未提供'}")
    print(f"  反馈：{reason_analysis['feedback']}")

    # Detect patterns
    patterns = detect_price_action_pattern(reason)
    if patterns:
        pattern_desc = ", ".join([p.get("description", "") for p in patterns])
        print(f"  识别模式：{pattern_desc}")

    # 2. Impulse Trading Check
    print("\n【冲动检查】")
    print("-" * 40)

    impulse_signals = []

    # Check recent losses
    recent_loss = check_recent_losses(trades, minutes=60)
    if recent_loss.get("has_recent_loss"):
        impulse_signals.append({
            "type": "REVENGE",
            "message": f"{recent_loss['minutes_ago']} 分钟前在 {recent_loss['symbol']} 亏损 {recent_loss['pnl_percent']:+.2f}%",
            "suggestion": "亏损后建议休息至少 1 小时，避免报复性交易",
        })

    # Check reason-based impulse signals
    temp_trade = {"reason": reason, "timestamp": datetime.now().isoformat()}
    reason_signals = detect_impulse_trade(temp_trade, trades[-5:])
    impulse_signals.extend(reason_signals)

    if impulse_signals:
        print("  ⚠️ 检测到潜在风险信号:")
        for signal in impulse_signals:
            print(f"    - [{signal['type']}] {signal['message']}")
            print(f"      建议：{signal['suggestion']}")
    else:
        print("  ✅ 通过 - 无明显的冲动交易信号")

    # 3. Historical Pattern Match
    print("\n【历史模式匹配】")
    print("-" * 40)

    timeframe = args.timeframe.upper() if args.timeframe else None
    pattern_stats = analyze_trading_pattern(trades, args.symbol.upper(), args.direction.upper(), timeframe)
    print(f"  {pattern_stats['message']}")

    # Check for conflicting patterns in history
    opposite_direction = "SHORT" if args.direction.upper() == "LONG" else "LONG"
    opposite_stats = analyze_trading_pattern(trades, args.symbol.upper(), opposite_direction, timeframe)
    if opposite_stats["win_rate"] and pattern_stats["win_rate"]:
        if opposite_stats["win_rate"] > pattern_stats["win_rate"] + 15:
            print(f"  ⚠️ 注意：{opposite_direction} 方向的历史胜率更高 ({opposite_stats['win_rate']:.0f}%)")

    # 4. Checklist Questions (Interactive)
    if args.interactive:
        print("\n【检查清单】")
        print("-" * 40)
        print("请回答以下问题（帮助确认开仓逻辑）:\n")

        questions = [
            "当前趋势方向是什么？(向上/向下/盘整)",
            "这个位置的盈亏比是多少？(如：1:2)",
            "如果是追涨/追跌，是否已经突破关键阻力/支撑？",
            "均线系统在什么位置？(价格在 MA 上/下方)",
            "MACD 是什么状态？(金叉/死叉/盘整)",
        ]

        answers = []
        for i, q in enumerate(questions, 1):
            try:
                ans = input(f"  {i}. {q} > ")
                answers.append(ans)
            except (EOFError, KeyboardInterrupt):
                print("\n  [跳过输入]")
                break

        if answers:
            print("\n  回答记录:")
            for i, (q, a) in enumerate(zip(questions, answers), 1):
                print(f"    {i}. {a}")

    # 5. Final Recommendation
    print("\n【综合建议】")
    print("-" * 40)

    issues = []

    if reason_analysis["level"] in ["POOR", "IMPULSIVE"]:
        issues.append("理由质量较差")

    if impulse_signals:
        issues.append("存在冲动交易风险")

    if pattern_stats["win_rate"] and pattern_stats["win_rate"] < 40:
        issues.append(f"历史模式胜率偏低 ({pattern_stats['win_rate']:.0f}%)")

    if issues:
        print("  ⚠️ 建议谨慎:")
        for issue in issues:
            print(f"    - {issue}")
        print("\n  建议：再等一等，或者重新评估这笔交易的必要性")
    else:
        print("  ✅ 可以考虑开仓")
        print("  提醒：即使检查通过，也要做好止损和仓位管理")

    print("\n" + "=" * 60)

    # JSON output for AI consumption
    if args.json:
        output = {
            "trade_plan": {
                "symbol": args.symbol.upper(),
                "direction": args.direction.upper(),
                "entry": args.entry,
            },
            "reason_quality": reason_analysis,
            "impulse_signals": impulse_signals,
            "pattern_stats": pattern_stats,
            "recommendation": "caution" if issues else "ok",
            "issues": issues,
        }
        print("\nJSON Output:")
        print(json.dumps(output, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Pre-trade checklist for rational decision making",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 \\
    --reason "突破回踩确认，MA 支撑"

  python pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 \\
    --stop-loss 84200 --target 87000

  python pre_trade_check.py --interactive  # Enable interactive checklist

  python pre_trade_check.py --json  # JSON output for AI
        """
    )

    parser.add_argument("--symbol", required=True, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument("--direction", required=True, choices=["LONG", "SHORT", "long", "short"],
                        help="Trade direction")
    parser.add_argument("--entry", required=True, type=float, help="Entry price")
    parser.add_argument("--timeframe", "-tf", help="Timeframe used for analysis (e.g., 15m, 1h, 4h, 1D)")
    parser.add_argument("--reason", help="Reason for entry")
    parser.add_argument("--stop-loss", dest="stop_loss", type=float, help="Stop loss price")
    parser.add_argument("--target", type=float, help="Target price")
    parser.add_argument("--interactive", action="store_true",
                        help="Enable interactive checklist questions")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    run_pre_trade_check(args)


if __name__ == "__main__":
    main()
