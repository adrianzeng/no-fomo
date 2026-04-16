#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-trade checklist to help traders make rational decisions before entering a position.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"
AI_REVIEWS_FILE = DATA_DIR / "ai_reviews.json"

sys.path.insert(0, str(Path(__file__).parent))
from ai_client import AIReviewError, request_ai_review  # noqa: E402
from trade_analysis_utils import analyze_reason_quality, detect_impulse_trade, detect_price_action_pattern  # noqa: E402


def build_json_response(report_type: str, data: dict[str, Any] | None = None, error: dict[str, str] | None = None) -> dict[str, Any]:
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


def load_trades() -> list[dict[str, Any]]:
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


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


def check_recent_losses(trades: list[dict[str, Any]], minutes: int = 60) -> dict[str, Any]:
    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)
    for trade in reversed(trades):
        if trade.get("result") != "LOSS":
            continue
        try:
            trade_time = datetime.fromisoformat(trade["timestamp"])
        except (KeyError, ValueError):
            continue
        if trade_time >= cutoff:
            return {
                "has_recent_loss": True,
                "minutes_ago": int((now - trade_time).total_seconds() / 60),
                "symbol": trade.get("symbol"),
                "pnl_percent": trade.get("pnl_percent"),
            }
    return {"has_recent_loss": False}


def analyze_trading_pattern(
    trades: list[dict[str, Any]],
    symbol: str,
    direction: str,
    timeframe: str | None = None,
) -> dict[str, Any]:
    matching_trades = [
        trade for trade in trades
        if trade.get("symbol") == symbol and trade.get("direction") == direction
    ]
    if timeframe:
        matching_trades = [trade for trade in matching_trades if trade.get("timeframe") == timeframe]

    if len(matching_trades) < 3:
        return {
            "sample_size": len(matching_trades),
            "win_rate": None,
            "message": "样本不足，继续积累数据。",
        }

    wins = len([trade for trade in matching_trades if trade.get("result") == "WIN"])
    win_rate = wins / len(matching_trades) * 100
    return {
        "sample_size": len(matching_trades),
        "win_rate": win_rate,
        "message": f"该模式历史胜率：{win_rate:.0f}% (n={len(matching_trades)})",
    }


def calculate_risk_summary(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.stop_loss is None:
        return None

    entry = float(args.entry)
    stop_loss = float(args.stop_loss)
    risk = abs(entry - stop_loss)
    reward = None
    ratio = None
    ratio_text = "N/A"

    if args.target is not None and risk > 0:
        target = float(args.target)
        reward = (target - entry) if args.direction.upper() == "LONG" else (entry - target)
        if reward > 0:
            ratio = reward / risk
            ratio_text = f"{ratio:.2f}:1"
        else:
            ratio_text = "目标价无效"

    return {
        "stop_loss": args.stop_loss,
        "target": args.target,
        "risk_amount": risk,
        "reward_amount": reward,
        "risk_reward_ratio": ratio,
        "risk_reward_text": ratio_text,
    }


def collect_check_result(args: argparse.Namespace, trades: list[dict[str, Any]]) -> dict[str, Any]:
    reason = args.reason or ""
    timeframe = args.timeframe.upper() if args.timeframe else None
    symbol = args.symbol.upper()
    direction = args.direction.upper()

    reason_analysis = analyze_reason_quality(reason)
    patterns = detect_price_action_pattern(reason)
    impulse_signals: list[dict[str, Any]] = []

    recent_loss = check_recent_losses(trades, minutes=60)
    if recent_loss.get("has_recent_loss"):
        impulse_signals.append({
            "type": "REVENGE",
            "message": f"{recent_loss['minutes_ago']} 分钟前在 {recent_loss['symbol']} 亏损 {recent_loss['pnl_percent']:+.2f}%",
            "suggestion": "亏损后建议至少休息 1 小时，避免在情绪未恢复时继续开仓。",
        })

    temp_trade = {"reason": reason, "timestamp": datetime.now().isoformat()}
    impulse_signals.extend(detect_impulse_trade(temp_trade, trades[-5:]))

    pattern_stats = analyze_trading_pattern(trades, symbol, direction, timeframe)
    opposite_direction = "SHORT" if direction == "LONG" else "LONG"
    opposite_stats = analyze_trading_pattern(trades, symbol, opposite_direction, timeframe)

    issues = []
    if reason_analysis["level"] in ["POOR", "IMPULSIVE", "MISSING"]:
        issues.append("开仓理由质量偏弱")
    if impulse_signals:
        issues.append("存在冲动交易风险")
    if pattern_stats["win_rate"] is not None and pattern_stats["win_rate"] < 40:
        issues.append(f"当前模式历史胜率偏低 ({pattern_stats['win_rate']:.0f}%)")

    return {
        "trade_plan": {
            "symbol": symbol,
            "direction": direction,
            "entry": args.entry,
            "timeframe": timeframe,
        },
        "risk_summary": calculate_risk_summary(args),
        "reason_text": reason,
        "reason_quality": reason_analysis,
        "detected_patterns": [pattern.get("description", "") for pattern in patterns],
        "impulse_signals": impulse_signals,
        "pattern_stats": pattern_stats,
        "opposite_direction_stats": {"direction": opposite_direction, **opposite_stats},
        "recommendation": "caution" if issues else "ok",
        "issues": issues,
    }


def build_ai_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_plan": result["trade_plan"],
        "risk_summary": result["risk_summary"],
        "reason_text": result["reason_text"],
        "reason_quality": {
            "score": result["reason_quality"]["score"],
            "level": result["reason_quality"]["level"],
            "feedback": result["reason_quality"]["feedback"],
        },
        "detected_patterns": result["detected_patterns"],
        "impulse_signals": result["impulse_signals"],
        "pattern_stats": result["pattern_stats"],
        "opposite_direction_stats": result["opposite_direction_stats"],
        "issues": result["issues"],
    }


def run_ai_review(result: dict[str, Any]) -> dict[str, Any]:
    payload = build_ai_payload(result)
    try:
        review = request_ai_review(payload)
        ai_result = {"success": True, "review": review}
    except AIReviewError as exc:
        ai_result = {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        }

    save_ai_review({
        "timestamp": datetime.now().isoformat(),
        "review_type": "pre_trade",
        "request": payload,
        "rule_check_summary": {
            "recommendation": result["recommendation"],
            "issues": result["issues"],
            "reason_quality": {
                "score": result["reason_quality"]["score"],
                "level": result["reason_quality"]["level"],
            },
        },
        "ai_review": ai_result,
        "success": ai_result["success"],
        "error": None if ai_result["success"] else ai_result["error"],
    })

    return ai_result


def print_text_report(result: dict[str, Any], args: argparse.Namespace) -> None:
    print("=" * 60)
    print("开仓前检查报告")
    print("=" * 60)

    timeframe = result["trade_plan"]["timeframe"]
    timeframe_suffix = f" ({timeframe})" if timeframe else ""
    print(f"\n交易计划：{result['trade_plan']['symbol']} {result['trade_plan']['direction']} @ {args.entry}{timeframe_suffix}")

    risk_summary = result["risk_summary"]
    if risk_summary:
        print(
            f"止损：{risk_summary['stop_loss']} | 目标：{risk_summary['target']} | "
            f"盈亏比：{risk_summary['risk_reward_text']}"
        )

    print("\n[理由质量]")
    print("-" * 40)
    level = result["reason_quality"]["level"]
    if level in ["EXCELLENT", "GOOD"]:
        status = "[OK]"
    elif level == "WARNING":
        status = "[!]"
    else:
        status = "[!!]"
    print(f"  {status} 评分：{result['reason_quality']['score']}/100 - {level}")
    print(f"  理由：{result['reason_text'][:120] if result['reason_text'] else '未提供'}")
    print(f"  反馈：{result['reason_quality']['feedback']}")
    if result["detected_patterns"]:
        print(f"  识别模式：{', '.join(result['detected_patterns'])}")

    print("\n[冲动检查]")
    print("-" * 40)
    if result["impulse_signals"]:
        print("  [!] 检测到潜在风险信号：")
        for signal in result["impulse_signals"]:
            print(f"    - [{signal['type']}] {signal['message']}")
            print(f"      建议：{signal['suggestion']}")
    else:
        print("  [OK] 未发现明显的冲动交易信号。")

    print("\n[历史模式匹配]")
    print("-" * 40)
    print(f"  {result['pattern_stats']['message']}")
    opposite_stats = result["opposite_direction_stats"]
    if opposite_stats["win_rate"] and result["pattern_stats"]["win_rate"]:
        if opposite_stats["win_rate"] > result["pattern_stats"]["win_rate"] + 15:
            print(
                f"  [!] 注意：{opposite_stats['direction']} 方向的历史胜率更高 "
                f"({opposite_stats['win_rate']:.0f}%)"
            )

    if args.interactive:
        print("\n[补充自检问题]")
        print("-" * 40)
        questions = [
            "当前趋势方向是什么？(向上/向下/盘整)",
            "这笔交易的盈亏比是多少？(例如 1:2)",
            "如果是追涨或追跌，是否已经出现关键位确认？",
            "当前价格与均线系统的位置关系是什么？",
            "MACD 当前是什么状态？(金叉/死叉/盘整)",
        ]
        answers = []
        for index, question in enumerate(questions, 1):
            try:
                answers.append(input(f"  {index}. {question} > "))
            except (EOFError, KeyboardInterrupt):
                print("\n  [跳过输入]")
                break
        if answers:
            print("\n  回答记录：")
            for index, answer in enumerate(answers, 1):
                print(f"    {index}. {answer}")

    print("\n[综合建议]")
    print("-" * 40)
    if result["issues"]:
        print("  [!] 建议谨慎：")
        for issue in result["issues"]:
            print(f"    - {issue}")
        print("\n  建议：先补全计划，再决定是否下单。")
    else:
        print("  [OK] 这笔交易计划具备基础执行条件。")
        print("  提醒：即使检查通过，也要严格执行止损和仓位管理。")

    if args.ai:
        print("\n[AI 审核]")
        print("-" * 40)
        ai_review = result.get("ai_review", {})
        if ai_review.get("success"):
            review = ai_review["review"]
            print(f"  评分：{review['score']}/100")
            print(f"  结论：{review['verdict']}")
            if review["strengths"]:
                print("  优点：")
                for item in review["strengths"]:
                    print(f"    - {item}")
            if review["risks"]:
                print("  风险：")
                for item in review["risks"]:
                    print(f"    - {item}")
            print(f"  行动建议：{review['action']}")
            print(f"  正向反馈：{review['encouragement']}")
        else:
            error = ai_review.get("error", {})
            print(f"  [!] AI 审核未完成：{error.get('message', '未知错误')}")

    print("\n" + "=" * 60)


def run_pre_trade_check(args: argparse.Namespace) -> None:
    trades = load_trades()
    result = collect_check_result(args, trades)
    if args.ai:
        result["ai_review"] = run_ai_review(result)

    if args.json:
        print(json.dumps(build_json_response("pre_trade_check", data=result), indent=2, ensure_ascii=False))
        return

    print_text_report(result, args)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-trade checklist for rational decision making",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 ^
    --reason "突破回踩确认，MA20 支撑"

  python pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 ^
    --stop-loss 84200 --target 87000 --ai

  python pre_trade_check.py --json --ai --symbol ETHUSDT --direction SHORT --entry 3200 ^
    --reason "4h 阻力回落，量能不足，预期反抽失败"
        """,
    )
    parser.add_argument("--symbol", required=True, help="Trading pair (e.g., BTCUSDT)")
    parser.add_argument("--direction", required=True, choices=["LONG", "SHORT", "long", "short"], help="Trade direction")
    parser.add_argument("--entry", required=True, type=float, help="Entry price")
    parser.add_argument("--timeframe", "-tf", help="Timeframe used for analysis (e.g., 15m, 1h, 4h, 1D)")
    parser.add_argument("--reason", help="Reason or thesis for entry")
    parser.add_argument("--stop-loss", dest="stop_loss", type=float, help="Stop loss price")
    parser.add_argument("--target", type=float, help="Target price")
    parser.add_argument("--interactive", action="store_true", help="Enable interactive checklist questions")
    parser.add_argument("--ai", action="store_true", help="Run AI review with an OpenAI-compatible API")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    run_pre_trade_check(args)


if __name__ == "__main__":
    main()
