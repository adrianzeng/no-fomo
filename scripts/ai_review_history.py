#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browse stored AI review history for No-FOMO.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

DATA_DIR = Path(__file__).parent.parent / "data"
AI_REVIEWS_FILE = DATA_DIR / "ai_reviews.json"


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


def load_ai_reviews() -> dict[str, Any]:
    if not AI_REVIEWS_FILE.exists():
        return {"reviews": [], "metadata": {}}
    with open(AI_REVIEWS_FILE, "r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_subject(review: dict[str, Any]) -> str:
    request = review.get("request", {})
    trade_plan = request.get("trade_plan")
    if isinstance(trade_plan, dict):
        symbol = trade_plan.get("symbol", "UNKNOWN")
        direction = trade_plan.get("direction", "UNKNOWN")
        return f"{symbol} {direction}"

    trade = request.get("trade")
    if isinstance(trade, dict):
        symbol = trade.get("symbol", "UNKNOWN")
        direction = trade.get("direction", "UNKNOWN")
        return f"{symbol} {direction}"

    return "UNKNOWN"


def infer_review_type(review: dict[str, Any]) -> str:
    review_type = review.get("review_type")
    if review_type:
        return str(review_type)
    request = review.get("request", {})
    if "trade_plan" in request:
        return "pre_trade"
    if "trade" in request:
        return "post_trade"
    return "unknown"


def filter_reviews(
    reviews: list[dict[str, Any]],
    review_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    filtered = []
    for review in reviews:
        current_type = infer_review_type(review)
        current_success = bool(review.get("success"))

        if review_type and current_type != review_type:
            continue
        if status == "success" and not current_success:
            continue
        if status == "failed" and current_success:
            continue
        filtered.append(review)
    return filtered


def summarize_reviews(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total_reviews": len(reviews),
        "success_count": 0,
        "failed_count": 0,
        "by_type": {},
    }

    for review in reviews:
        review_type = infer_review_type(review)
        success = bool(review.get("success"))
        summary["by_type"].setdefault(review_type, {"total": 0, "success": 0, "failed": 0})
        summary["by_type"][review_type]["total"] += 1
        if success:
            summary["success_count"] += 1
            summary["by_type"][review_type]["success"] += 1
        else:
            summary["failed_count"] += 1
            summary["by_type"][review_type]["failed"] += 1

    return summary


def format_review_row(review: dict[str, Any]) -> str:
    timestamp = review.get("timestamp", "N/A")
    review_type = infer_review_type(review)
    subject = infer_subject(review)
    status = "OK" if review.get("success") else "FAIL"

    ai_review = review.get("ai_review", {})
    if review.get("success"):
        result = ai_review.get("review", {})
        verdict = result.get("verdict", "N/A")
        score = result.get("score", "N/A")
        tail = f"{verdict} | score={score}"
    else:
        error = ai_review.get("error", {}) or review.get("error", {})
        tail = error.get("code", "unknown_error")

    return f"[{status}] {timestamp} | {review_type} | {subject} | {tail}"


def print_review_detail(review: dict[str, Any]) -> None:
    print("=" * 60)
    print(f"时间：{review.get('timestamp', 'N/A')}")
    print(f"类型：{infer_review_type(review)}")
    print(f"对象：{infer_subject(review)}")
    print(f"状态：{'成功' if review.get('success') else '失败'}")

    ai_review = review.get("ai_review", {})
    if review.get("success"):
        result = ai_review.get("review", {})
        print(f"评分：{result.get('score', 'N/A')}")
        print(f"结论：{result.get('verdict', 'N/A')}")
        if result.get("strengths"):
            print("优点：")
            for item in result["strengths"]:
                print(f"  - {item}")
        if result.get("risks"):
            print("风险：")
            for item in result["risks"]:
                print(f"  - {item}")
        print(f"行动建议：{result.get('action', 'N/A')}")
        print(f"正向反馈：{result.get('encouragement', 'N/A')}")
    else:
        error = ai_review.get("error", {}) or review.get("error", {})
        print(f"错误码：{error.get('code', 'N/A')}")
        print(f"错误信息：{error.get('message', 'N/A')}")
    print("=" * 60)


def print_report(reviews: list[dict[str, Any]], summary: dict[str, Any], args: argparse.Namespace) -> None:
    print("=" * 60)
    print("AI Review History")
    print("=" * 60)
    print(f"总记录：{summary['total_reviews']} | 成功：{summary['success_count']} | 失败：{summary['failed_count']}")

    if summary["by_type"]:
        print("\n[类型统计]")
        print("-" * 40)
        for review_type, stats in sorted(summary["by_type"].items()):
            print(f"  {review_type}: total={stats['total']} success={stats['success']} failed={stats['failed']}")

    if not reviews:
        print("\n暂无符合条件的 AI 记录。")
        print("=" * 60)
        return

    print("\n[最近记录]")
    print("-" * 40)
    for review in reviews:
        print(format_review_row(review))

    if args.detail:
        print("\n[详细记录]")
        for review in reviews:
            print_review_detail(review)

    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Browse stored AI review history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_review_history.py
  python ai_review_history.py --type pre_trade
  python ai_review_history.py --status success --last 5
  python ai_review_history.py --detail --last 2
  python ai_review_history.py --json
        """,
    )
    parser.add_argument("--type", dest="review_type", choices=["pre_trade", "post_trade"], help="Filter by review type")
    parser.add_argument("--status", choices=["success", "failed"], help="Filter by review status")
    parser.add_argument("--last", type=int, default=10, help="Show the last N matching reviews (default: 10)")
    parser.add_argument("--detail", action="store_true", help="Show detailed review content")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    data = load_ai_reviews()
    reviews = data.get("reviews", [])
    if not reviews:
        if args.json:
            print(json.dumps(build_json_response(
                "ai_review_history",
                error={"code": "no_ai_reviews", "message": "No AI review history found."},
            ), indent=2, ensure_ascii=False))
            return
        print("暂无 AI review 历史记录。")
        return

    filtered = filter_reviews(reviews, review_type=args.review_type, status=args.status)
    filtered = list(reversed(filtered))[: max(args.last, 0)]
    summary = summarize_reviews(filtered)

    if args.json:
        output = {
            "summary": summary,
            "reviews": filtered,
        }
        print(json.dumps(build_json_response("ai_review_history", data=output), indent=2, ensure_ascii=False))
        return

    print_report(filtered, summary, args)


if __name__ == "__main__":
    main()
