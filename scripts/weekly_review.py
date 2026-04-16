#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate weekly trading review reports.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    import io as sys_io

    sys.stdout = sys_io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import analyze_reason_quality, detect_price_action_pattern, get_impulse_statistics  # noqa: E402


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


def get_trades_by_period(trades, days=7):
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    recent = []
    for trade in trades:
        try:
            trade_time = datetime.fromisoformat(trade["timestamp"])
        except (KeyError, ValueError):
            continue
        if trade_time >= cutoff:
            recent.append(trade)
    return recent


def calculate_performance_metrics(trades):
    wins = [trade for trade in trades if trade.get("result") == "WIN"]
    losses = [trade for trade in trades if trade.get("result") == "LOSS"]
    total_pnl = sum(trade.get("pnl_percent", 0) for trade in trades)
    avg_win = sum(trade.get("pnl_percent", 0) for trade in wins) / len(wins) if wins else 0
    avg_loss = sum(trade.get("pnl_percent", 0) for trade in losses) / len(losses) if losses else 0
    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(trades) * 100 if trades else 0,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": abs(avg_win / avg_loss) if avg_loss else None,
        "best_trade": max(trades, key=lambda trade: trade.get("pnl_percent", 0)) if trades else None,
        "worst_trade": min(trades, key=lambda trade: trade.get("pnl_percent", 0)) if trades else None,
    }


def analyze_reason_quality_distribution(trades):
    distribution = defaultdict(int)
    low_quality = []
    for trade in trades:
        analysis = analyze_reason_quality(trade.get("reason", ""))
        distribution[analysis["level"]] += 1
        if analysis["level"] in ["POOR", "IMPULSIVE", "MISSING"]:
            low_quality.append({"trade": trade, "analysis": analysis})
    return {"distribution": dict(distribution), "low_quality_trades": low_quality}


def generate_lessons_learned(trades, metrics):
    lessons = []
    impulse_stats = get_impulse_statistics(trades)
    if impulse_stats.get("impulse_count", 0) > 0:
        diff = impulse_stats.get("normal_win_rate", 0) - impulse_stats.get("impulse_win_rate", 0)
        if diff > 0:
            lessons.append({
                "category": "impulse_control",
                "lesson": f"减少冲动交易，理论上可提升胜率约 {diff:.1f}%。",
                "evidence": f"冲动交易胜率 {impulse_stats['impulse_win_rate']:.1f}% vs 理性交易胜率 {impulse_stats['normal_win_rate']:.1f}%",
            })
        else:
            lessons.append({
                "category": "impulse_control",
                "lesson": "即使冲动交易短期盈利，也不能把结果当作方法有效的证明。",
                "evidence": f"本周期识别到 {impulse_stats['impulse_count']} 笔冲动交易，短期结果不能替代稳定方法。",
            })

    best_trade = metrics.get("best_trade")
    if best_trade:
        best_reason = analyze_reason_quality(best_trade.get("reason", ""))
        patterns = detect_price_action_pattern(best_trade.get("reason", ""))
        if patterns and best_reason["level"] not in ["POOR", "IMPULSIVE", "MISSING"]:
            pattern_desc = ", ".join(pattern.get("description", "") for pattern in patterns)
            lessons.append({
                "category": "winning_pattern",
                "lesson": "表现最好的交易通常具备更清晰的结构依据与执行纪律。",
                "evidence": f"最佳交易 ({best_trade['symbol']} {best_trade['pnl_percent']:+.2f}%): {pattern_desc}",
            })

    worst_trade = metrics.get("worst_trade")
    if worst_trade:
        worst_reason = analyze_reason_quality(worst_trade.get("reason", ""))
        if worst_reason["level"] in ["POOR", "IMPULSIVE", "MISSING"]:
            lessons.append({
                "category": "loss_lesson",
                "lesson": "理由不充分的交易会明显削弱决策质量，需要在开仓前被拦下来。",
                "evidence": f"最差交易 ({worst_trade['symbol']} {worst_trade['pnl_percent']:+.2f}%): {worst_reason['feedback']}",
            })
    return lessons


def generate_improvement_goals(trades, metrics):
    goals = []
    impulse_stats = get_impulse_statistics(trades)
    if impulse_stats.get("impulse_count", 0) > 2:
        goals.append({
            "goal": "减少冲动交易",
            "target": f"将冲动交易控制在每周 2 笔以内（本周 {impulse_stats['impulse_count']} 笔）",
            "action": "每次开仓前至少停 5 分钟，写下明确的入场依据与失效条件。",
        })

    quality_data = analyze_reason_quality_distribution(trades)
    if quality_data.get("low_quality_trades"):
        goals.append({
            "goal": "提高开仓理由质量",
            "target": "每笔交易都有明确的技术依据、止损和无效条件",
            "action": "固定使用 checklist：结构、关键位、指标、止损、盈亏比。",
        })

    if metrics.get("win_rate", 0) < 50:
        goals.append({
            "goal": "提高胜率",
            "target": "将胜率提升到 50% 以上",
            "action": "减少低质量尝试，只做自己最熟悉的 setup。",
        })

    if metrics.get("total_trades", 0) > 10:
        goals.append({
            "goal": "控制交易频率",
            "target": "每周交易不超过 10 笔",
            "action": "减少无计划试单，把精力放在高确定性机会。",
        })

    if not goals:
        goals.append({
            "goal": "保持当前习惯",
            "target": "继续维持理性交易与固定复盘节奏",
            "action": "坚持记录每笔交易的理由、执行和复盘结论。",
        })
    return goals


def print_weekly_report(period_days, metrics, quality_data, lessons, goals, impulse_stats):
    print("=" * 60)
    print(f"交易周报复盘（过去 {period_days} 天）")
    print("=" * 60)

    print("\n[表现摘要]")
    print("-" * 40)
    print(f"  总交易数：{metrics['total_trades']}")
    print(f"  盈利：{metrics['wins']} | 亏损：{metrics['losses']}")
    print(f"  胜率：{metrics['win_rate']:.1f}%")
    print(f"  总 PnL: {metrics['total_pnl']:+.2f}%")
    if metrics["profit_factor"] is not None:
        print(f"  盈利因子：{metrics['profit_factor']:.2f}x")
    elif metrics["wins"] > 0 and metrics["losses"] == 0:
        print("  盈利因子：N/A（当前周期无亏损交易）")

    if metrics.get("best_trade"):
        best_trade = metrics["best_trade"]
        print(f"\n  最佳交易：{best_trade['symbol']} {best_trade['direction']}")
        print(f"    PnL: {best_trade['pnl_percent']:+.2f}%")
        print(f"    理由：{best_trade.get('reason', 'N/A')[:50]}...")

    if metrics.get("worst_trade"):
        worst_trade = metrics["worst_trade"]
        print(f"\n  最差交易：{worst_trade['symbol']} {worst_trade['direction']}")
        print(f"    PnL: {worst_trade['pnl_percent']:+.2f}%")
        print(f"    理由：{worst_trade.get('reason', 'N/A')[:50]}...")

    print("\n[开仓理由质量分布]")
    print("-" * 40)
    for level in ["EXCELLENT", "GOOD", "WARNING", "POOR", "IMPULSIVE", "MISSING"]:
        count = quality_data["distribution"].get(level, 0)
        if count > 0:
            indicator = "[OK]" if level in ["EXCELLENT", "GOOD"] else "[!]"
            print(f"  {indicator} {level}: {count} 笔")

    print("\n[冲动交易分析]")
    print("-" * 40)
    if impulse_stats.get("impulse_count", 0) > 0:
        print(f"  冲动交易：{impulse_stats['impulse_count']} 笔 ({impulse_stats['impulse_percentage']:.1f}%)")
        print(f"  冲动交易胜率：{impulse_stats['impulse_win_rate']:.1f}%")
        print(f"  理性交易胜率：{impulse_stats['normal_win_rate']:.1f}%")
    else:
        print("  暂无冲动交易记录，继续保持。")

    print("\n[本周学到的教训]")
    print("-" * 40)
    if lessons:
        for index, lesson in enumerate(lessons, 1):
            print(f"  {index}. [{lesson['category']}]")
            print(f"     {lesson['lesson']}")
            print(f"     依据：{lesson['evidence']}")
    else:
        print("  暂无明显结论，继续积累数据。")

    print("\n[下周改进目标]")
    print("-" * 40)
    for index, goal in enumerate(goals, 1):
        print(f"  {index}. {goal['goal']}")
        print(f"     目标：{goal['target']}")
        print(f"     行动：{goal['action']}")

    print("\n" + "=" * 60)


def generate_report_data(period_days, metrics, quality_data, lessons, goals, impulse_stats):
    return {
        "period_days": period_days,
        "generated_at": datetime.now().isoformat(),
        "performance": {
            "total_trades": metrics["total_trades"],
            "wins": metrics["wins"],
            "losses": metrics["losses"],
            "win_rate": metrics["win_rate"],
            "total_pnl": metrics["total_pnl"],
            "avg_win": metrics["avg_win"],
            "avg_loss": metrics["avg_loss"],
            "profit_factor": metrics["profit_factor"],
        },
        "best_trade": metrics.get("best_trade"),
        "worst_trade": metrics.get("worst_trade"),
        "reason_quality": quality_data.get("distribution", {}),
        "impulse_trading": impulse_stats,
        "lessons_learned": lessons,
        "improvement_goals": goals,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate weekly trading review report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python weekly_review.py
  python weekly_review.py --days 30
  python weekly_review.py --json
  python weekly_review.py --save
        """,
    )
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    args = parser.parse_args()

    trades = load_trades()
    if not trades:
        if args.json:
            print(json.dumps(build_json_response(
                "weekly_review",
                error={"code": "no_trades", "message": "No trades logged yet."},
            ), indent=2, ensure_ascii=False))
            return
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    period_trades = get_trades_by_period(trades, args.days)
    if not period_trades:
        if args.json:
            print(json.dumps(build_json_response(
                "weekly_review",
                error={"code": "no_trades_in_period", "message": f"No trades found in the last {args.days} days."},
            ), indent=2, ensure_ascii=False))
            return
        print(f"过去 {args.days} 天没有交易记录。")
        return

    metrics = calculate_performance_metrics(period_trades)
    quality_data = analyze_reason_quality_distribution(period_trades)
    impulse_stats = get_impulse_statistics(period_trades)
    lessons = generate_lessons_learned(period_trades, metrics)
    goals = generate_improvement_goals(period_trades, metrics)
    report = generate_report_data(args.days, metrics, quality_data, lessons, goals, impulse_stats)

    if args.json:
        print(json.dumps(build_json_response("weekly_review", data=report), indent=2, ensure_ascii=False))
    else:
        print_weekly_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)

    if args.save:
        report_dir = DATA_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.json:
            json_file = report_dir / f"weekly_review_{timestamp}.json"
            with open(json_file, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, ensure_ascii=False)
        else:
            report_file = report_dir / f"weekly_review_{timestamp}.txt"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                print_weekly_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)
            with open(report_file, "w", encoding="utf-8") as handle:
                handle.write(buffer.getvalue())
            print(f"\n报告已保存至：{report_file}")


if __name__ == "__main__":
    main()
