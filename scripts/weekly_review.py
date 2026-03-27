#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate weekly trading review reports.

This script creates comprehensive weekly reviews including:
- Performance summary
- Best and worst trades
- Impulse trading analysis
- Pattern insights
- Lessons learned
- Next week's improvement goals
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
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
    get_impulse_statistics,
    analyze_reason_quality,
    detect_price_action_pattern,
)


def load_trades():
    """Load trades from JSON file."""
    if not TRADES_FILE.exists():
        return []
    with open(TRADES_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("trades", [])


def get_trades_by_period(trades, days=7):
    """Get trades from the last N days."""
    now = datetime.now()
    cutoff = now - timedelta(days=days)

    recent_trades = []
    for trade in trades:
        try:
            trade_time = datetime.fromisoformat(trade["timestamp"])
            if trade_time >= cutoff:
                recent_trades.append(trade)
        except (KeyError, ValueError):
            continue

    return recent_trades


def calculate_performance_metrics(trades):
    """Calculate key performance metrics."""
    if not trades:
        return {}

    wins = [t for t in trades if t.get("result") == "WIN"]
    losses = [t for t in trades if t.get("result") == "LOSS"]

    total_pnl = sum(t.get("pnl_percent", 0) for t in trades)
    avg_win = sum(t.get("pnl_percent", 0) for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.get("pnl_percent", 0) for t in losses) / len(losses) if losses else 0

    win_rate = len(wins) / len(trades) * 100 if trades else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss else 0

    # Best and worst trades
    best_trade = max(trades, key=lambda x: x.get("pnl_percent", 0)) if trades else None
    worst_trade = min(trades, key=lambda x: x.get("pnl_percent", 0)) if trades else None

    return {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def analyze_reason_quality_distribution(trades):
    """Analyze the distribution of reason quality."""
    quality_counts = defaultdict(int)
    low_quality_trades = []

    for trade in trades:
        reason = trade.get("reason", "")
        analysis = analyze_reason_quality(reason)
        quality_counts[analysis["level"]] += 1

        if analysis["level"] in ["POOR", "IMPULSIVE"]:
            low_quality_trades.append({
                "trade": trade,
                "analysis": analysis,
            })

    return {
        "distribution": dict(quality_counts),
        "low_quality_trades": low_quality_trades,
    }


def generate_lessons_learned(trades, metrics):
    """Generate lessons learned from the trading period."""
    lessons = []

    # Analyze impulse trading impact
    impulse_stats = get_impulse_statistics(trades)
    if impulse_stats.get("impulse_count", 0) > 0:
        diff = impulse_stats.get("normal_win_rate", 0) - impulse_stats.get("impulse_win_rate", 0)
        if diff > 0:
            lessons.append({
                "category": "impulse_control",
                "lesson": f"避免冲动交易可以提高胜率约 {diff:.1f}%",
                "evidence": f"冲动交易胜率 {impulse_stats['impulse_win_rate']:.1f}% vs 理性交易 {impulse_stats['normal_win_rate']:.1f}%",
            })

    # Analyze best trade pattern
    if metrics.get("best_trade"):
        best = metrics["best_trade"]
        patterns = detect_price_action_pattern(best.get("reason", ""))
        if patterns:
            pattern_desc = ", ".join([p.get("description", "") for p in patterns])
            lessons.append({
                "category": "winning_pattern",
                "lesson": "成功的交易通常具备明确的技术面依据",
                "evidence": f"最佳交易 ({best['symbol']} +{best['pnl_percent']:.2f}%): {pattern_desc}",
            })

    # Analyze worst trade pattern
    if metrics.get("worst_trade"):
        worst = metrics["worst_trade"]
        reason_analysis = analyze_reason_quality(worst.get("reason", ""))
        if reason_analysis["level"] in ["POOR", "IMPULSIVE"]:
            lessons.append({
                "category": "loss_lesson",
                "lesson": "理由不充分的交易容易导致亏损",
                "evidence": f"最差交易 ({worst['symbol']} {worst['pnl_percent']:+.2f}%): {reason_analysis['feedback']}",
            })

    return lessons


def generate_improvement_goals(trades, metrics, lessons):
    """Generate specific improvement goals for next week."""
    goals = []

    # Impulse control goal
    impulse_stats = get_impulse_statistics(trades)
    impulse_count = impulse_stats.get("impulse_count", 0)
    if impulse_count > 2:
        goals.append({
            "goal": "减少冲动交易",
            "target": f"将冲动交易控制在每周≤2 次 (本周{impulse_count}次)",
            "action": "每次开仓前等待 5 分钟，写下明确的开仓理由",
        })

    # Reason quality goal
    quality_data = analyze_reason_quality_distribution(trades)
    low_quality_count = len(quality_data.get("low_quality_trades", []))
    if low_quality_count > 0:
        goals.append({
            "goal": "提高开仓理由质量",
            "target": "每笔交易都有明确的技术面依据",
            "action": "使用检查清单：突破位/支撑位、指标信号、盈亏比",
        })

    # Win rate goal
    win_rate = metrics.get("win_rate", 0)
    if win_rate < 50:
        goals.append({
            "goal": "提高胜率",
            "target": "胜率提升至 50% 以上",
            "action": "只在高胜率模式下开仓，避免低胜率模式",
        })

    # Trading frequency goal
    total_trades = metrics.get("total_trades", 0)
    if total_trades > 10:
        goals.append({
            "goal": "控制交易频率",
            "target": "每周交易≤10 笔",
            "action": "宁缺毋滥，等待最佳机会",
        })

    # Default goal if no specific issues
    if not goals:
        goals.append({
            "goal": "保持良好习惯",
            "target": "继续当前的理性交易方式",
            "action": "坚持记录每笔交易的开仓理由和复盘",
        })

    return goals


def print_weekly_report(period_days, metrics, quality_data, lessons, goals, impulse_stats):
    """Print formatted weekly review report."""
    print("=" * 60)
    print(f"交易周报复盘 (过去 {period_days} 天)")
    print("=" * 60)

    # Performance Summary
    print("\n【表现摘要】")
    print("-" * 40)
    print(f"  总交易数：{metrics['total_trades']}")
    print(f"  盈利：{metrics['wins']} | 亏损：{metrics['losses']}")
    print(f"  胜率：{metrics['win_rate']:.1f}%")
    print(f"  总 PnL: {metrics['total_pnl']:+.2f}%")
    if metrics['profit_factor'] > 0:
        print(f"  盈利因子：{metrics['profit_factor']:.2f}x")

    # Best and Worst Trades
    if metrics.get("best_trade"):
        best = metrics["best_trade"]
        print(f"\n  最佳交易：{best['symbol']} {best['direction']}")
        print(f"    PnL: +{best['pnl_percent']:.2f}%")
        print(f"    理由：{best.get('reason', 'N/A')[:50]}...")

    if metrics.get("worst_trade"):
        worst = metrics["worst_trade"]
        print(f"\n  最差交易：{worst['symbol']} {worst['direction']}")
        print(f"    PnL: {worst['pnl_percent']:+.2f}%")
        print(f"    理由：{worst.get('reason', 'N/A')[:50]}...")

    # Reason Quality Distribution
    print("\n【开仓理由质量分布】")
    print("-" * 40)
    dist = quality_data.get("distribution", {})
    for level in ["EXCELLENT", "GOOD", "WARNING", "POOR", "IMPULSIVE"]:
        count = dist.get(level, 0)
        if count > 0:
            indicator = "✓" if level in ["EXCELLENT", "GOOD"] else "!"
            print(f"  {indicator} {level}: {count} 笔")

    # Impulse Trading Analysis
    print("\n【冲动交易分析】")
    print("-" * 40)
    impulse_count = impulse_stats.get("impulse_count", 0)
    if impulse_count > 0:
        print(f"  冲动交易：{impulse_count} 笔 ({impulse_stats['impulse_percentage']:.1f}%)")
        print(f"  冲动交易胜率：{impulse_stats['impulse_win_rate']:.1f}%")
        print(f"  理性交易胜率：{impulse_stats['normal_win_rate']:.1f}%")
    else:
        print("  暂无冲动交易记录，继续保持！")

    # Lessons Learned
    print("\n【本周学到的教训】")
    print("-" * 40)
    if lessons:
        for i, lesson in enumerate(lessons, 1):
            print(f"  {i}. [{lesson['category']}]")
            print(f"     {lesson['lesson']}")
            print(f"     依据：{lesson['evidence']}")
    else:
        print("  继续积累数据以获取更多洞察")

    # Next Week Goals
    print("\n【下周改进目标】")
    print("-" * 40)
    for i, goal in enumerate(goals, 1):
        print(f"  {i}. {goal['goal']}")
        print(f"     目标：{goal['target']}")
        print(f"     行动：{goal['action']}")

    print("\n" + "=" * 60)


def generate_json_report(period_days, metrics, quality_data, lessons, goals, impulse_stats):
    """Generate JSON report for AI consumption."""
    # Convert best/worst trade to serializable format
    best_trade = metrics.get("best_trade")
    worst_trade = metrics.get("worst_trade")

    report = {
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
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "reason_quality": quality_data.get("distribution", {}),
        "impulse_trading": impulse_stats,
        "lessons_learned": lessons,
        "improvement_goals": goals,
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Generate weekly trading review report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python weekly_review.py                 # 7-day report
  python weekly_review.py --days 30       # 30-day report
  python weekly_review.py --json          # JSON output
  python weekly_review.py --save          # Save to file
        """
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to file"
    )

    args = parser.parse_args()

    trades = load_trades()

    if not trades:
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    # Get trades for the period
    period_trades = get_trades_by_period(trades, args.days)

    if not period_trades:
        print(f"过去 {args.days} 天没有交易记录")
        return

    # Calculate metrics
    metrics = calculate_performance_metrics(period_trades)
    quality_data = analyze_reason_quality_distribution(period_trades)
    impulse_stats = get_impulse_statistics(period_trades)
    lessons = generate_lessons_learned(period_trades, metrics)
    goals = generate_improvement_goals(period_trades, metrics, lessons)

    if args.json:
        report = generate_json_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_weekly_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)

    if args.save:
        # Save report to file
        report_dir = DATA_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"weekly_review_{timestamp}.txt"

        if args.json:
            report = generate_json_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)
            json_file = report_dir / f"weekly_review_{timestamp}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存至：{json_file}")
        else:
            # Re-generate text report to file
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                print_weekly_report(args.days, metrics, quality_data, lessons, goals, impulse_stats)
            report_content = f.getvalue()

            with open(report_file, "w", encoding="utf-8") as file:
                file.write(report_content)
            print(f"\n报告已保存至：{report_file}")


if __name__ == "__main__":
    main()
