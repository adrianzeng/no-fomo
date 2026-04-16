#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze impulse trading patterns from historical trade data.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
TRADES_FILE = DATA_DIR / "trades.json"

sys.path.insert(0, str(Path(__file__).parent))
from trade_analysis_utils import detect_impulse_trade, format_impulse_report, get_impulse_statistics  # noqa: E402


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


def summarize_stats(stats):
    return {
        "summary": {
            "total_trades": stats["total_trades"],
            "impulse_count": stats["impulse_count"],
            "impulse_percentage": stats["impulse_percentage"],
            "impulse_win_rate": stats["impulse_win_rate"],
            "normal_win_rate": stats["normal_win_rate"],
        },
        "impulse_types": stats["impulse_types"],
        "impulse_trades": stats["impulse_trades"],
        "normal_trades": stats["normal_trades"],
    }


def analyze_impulse_trades(args):
    trades = load_trades()
    if not trades:
        if args.json:
            print(json.dumps(build_json_response(
                "impulse_analysis",
                error={"code": "no_trades", "message": "No trades logged yet."},
            ), indent=2, ensure_ascii=False))
            return
        print("暂无交易数据。请先使用 log_trade.py 记录交易。")
        return

    stats = get_impulse_statistics(trades)
    if args.json:
        print(json.dumps(build_json_response("impulse_analysis", data=summarize_stats(stats)), indent=2, ensure_ascii=False))
        return

    print(format_impulse_report(stats))
    if args.detail:
        print_detailed_breakdown(stats)


def print_detailed_breakdown(stats):
    print("\n" + "=" * 50)
    print("冲动交易明细")
    print("=" * 50)

    impulse_trades = stats.get("impulse_trades", [])
    if not impulse_trades:
        print("暂无冲动交易记录")
        return

    for trade in impulse_trades:
        print(f"\n[{trade['timestamp'][:10]}] {trade['symbol']} {trade['direction']}")
        print(f"  结果：{trade['result']} | PnL: {trade['pnl_percent']:+.2f}%")
        print(f"  理由：{trade.get('reason', 'N/A')}")
        for signal in trade.get("impulse_signals", []):
            print(f"    - {signal['type']}: {signal['message']}")


def analyze_single_trade(args):
    trades = load_trades()
    target_trade = next((trade for trade in trades if trade["id"] == args.trade_id), None)
    if not target_trade:
        if args.json:
            print(json.dumps(build_json_response(
                "impulse_trade_analysis",
                error={"code": "trade_not_found", "message": f"Trade not found: {args.trade_id}"},
            ), indent=2, ensure_ascii=False))
            return
        print(f"未找到交易 ID: {args.trade_id}")
        return

    trade_index = trades.index(target_trade)
    signals = detect_impulse_trade(target_trade, trades[:trade_index])
    if args.json:
        output = {"trade_id": target_trade["id"], "trade": target_trade, "impulse_signals": signals}
        print(json.dumps(build_json_response("impulse_trade_analysis", data=output), indent=2, ensure_ascii=False))
        return

    print(f"\n交易分析：{target_trade['symbol']} {target_trade['direction']}")
    print(f"时间：{target_trade['timestamp']}")
    print(f"结果：{target_trade['result']} | PnL: {target_trade['pnl_percent']:+.2f}%")
    print(f"理由：{target_trade.get('reason', 'N/A')}")
    if signals:
        print(f"\n检测到 {len(signals)} 个风险信号")
        for signal in signals:
            print(f"\n  [{signal['type']}] - {signal['severity'].upper()}")
            print(f"  {signal['message']}")
            print(f"  建议：{signal['suggestion']}")
    else:
        print("\n[OK] 未检测到冲动交易信号，这是一笔相对理性的决策。")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze impulse trading patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_impulse.py
  python analyze_impulse.py --json
  python analyze_impulse.py --detail
  python analyze_impulse.py --trade-id abc123
        """,
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON for AI consumption")
    parser.add_argument("--detail", action="store_true", help="Show detailed breakdown of each impulse trade")
    parser.add_argument("--trade-id", dest="trade_id", help="Analyze a specific trade by ID")
    args = parser.parse_args()

    if args.trade_id:
        analyze_single_trade(args)
    else:
        analyze_impulse_trades(args)


if __name__ == "__main__":
    main()
