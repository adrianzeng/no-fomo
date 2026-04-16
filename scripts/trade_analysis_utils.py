#!/usr/bin/env python3
"""
Trading analysis utilities for detecting impulse trades and evaluating reason quality.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List


WEAK_REASON_PATTERNS = {
    "fomo": [
        r"追涨",
        r"拉升",
        r"冲高",
        r"追",
        r"fast.*up",
        r"pump",
        r"moon",
        r"surge",
        r"spike",
    ],
    "emotion": [
        r"感觉",
        r"觉得",
        r"试试",
        r"猜",
        r"feel",
        r"guess",
        r"try",
        r"hope",
    ],
    "revenge": [
        r"回本",
        r"翻本",
        r"报复",
        r"recover",
        r"revenge",
        r"make back",
    ],
    "boredom": [
        r"无聊",
        r"手痒",
        r"闲着",
        r"bored",
        r"just.*trade",
    ],
}

STRONG_REASON_PATTERNS = [
    r"突破.*回踩",
    r"突破.*确认",
    r"支撑.*反弹",
    r"阻力.*回落",
    r"均线.*支撑",
    r"均线.*阻力",
    r"背离",
    r"breakout.*retest",
    r"support.*bounce",
    r"resistance.*reject",
    r"ma.*support",
    r"ma.*resistance",
    r"divergence",
    r"consolidation",
]

INDICATOR_KEYWORDS = {
    "rsi": ["rsi", "相对强弱"],
    "macd": ["macd", "异同移动平均线"],
    "ma": ["ma", "均线", "移动平均线", "ema", "sma"],
    "bollinger": ["bollinger", "布林"],
    "fibonacci": ["fibonacci", "斐波那契", "黄金分割"],
    "volume": ["volume", "成交量", "量能"],
}


def analyze_reason_quality(reason: str) -> Dict:
    """Analyze the quality of a trade reason."""
    if not reason or len(reason.strip()) < 5:
        return {
            "score": 0,
            "level": "MISSING",
            "feedback": "开仓理由为空或过短，请写清楚具体的入场依据。",
            "signals": ["empty_reason"],
            "positive_signals": [],
        }

    reason_lower = reason.lower()
    signals = []
    positive_signals = []

    for category, patterns in WEAK_REASON_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, reason_lower):
                signals.append(f"weak_{category}")
                break

    for pattern in STRONG_REASON_PATTERNS:
        if re.search(pattern, reason_lower):
            positive_signals.append("technical_basis")
            break

    if re.search(r"\d{4,}", reason):
        positive_signals.append("specific_price")

    detected_indicators = []
    for indicator_name, keywords in INDICATOR_KEYWORDS.items():
        if any(keyword in reason_lower for keyword in keywords):
            detected_indicators.append(indicator_name)

    if detected_indicators:
        positive_signals.append("indicator_based")

    base_score = 50
    base_score -= len(signals) * 20
    base_score += len(positive_signals) * 15
    score = max(0, min(100, base_score))

    if score >= 80:
        level = "EXCELLENT"
        feedback = "理由充分，基于明确的技术面依据。"
    elif score >= 60:
        level = "GOOD"
        feedback = "理由较为充分，但还可以进一步具体化。"
    elif score >= 40:
        level = "WARNING"
        feedback = "理由不够充分，可能存在冲动交易风险。"
    elif score >= 20:
        level = "POOR"
        feedback = "理由质量较差，建议重新审视交易动机。"
    else:
        level = "IMPULSIVE"
        feedback = "高度疑似冲动交易，请先停下来复核计划。"

    return {
        "score": score,
        "level": level,
        "feedback": feedback,
        "signals": signals,
        "positive_signals": positive_signals,
        "detected_indicators": detected_indicators,
    }


def detect_impulse_trade(
    trade: Dict,
    recent_trades: List[Dict],
    price_data: Dict | None = None,
) -> List[Dict]:
    """Detect potential impulse trading patterns."""
    del price_data

    signals = []
    reason_analysis = analyze_reason_quality(trade.get("reason", ""))

    if "weak_fomo" in reason_analysis.get("signals", []):
        signals.append({
            "type": "FOMO",
            "severity": "high",
            "message": "开仓理由显示你可能在追涨杀跌。",
            "suggestion": "等待回踩或反抽确认后再入场，不要在快速波动里追单。",
        })

    if recent_trades:
        last_trade = recent_trades[-1]
        if last_trade.get("result") == "LOSS":
            try:
                last_time = datetime.fromisoformat(last_trade["timestamp"])
                current_time = datetime.fromisoformat(trade.get("timestamp", datetime.now().isoformat()))
                time_gap = (current_time - last_time).total_seconds() / 60
                if time_gap < 60:
                    signals.append({
                        "type": "REVENGE",
                        "severity": "high",
                        "message": f"亏损后 {int(time_gap)} 分钟内再次开仓，疑似报复性交易。",
                        "suggestion": "建议至少休息 1 小时，等情绪恢复后再重新评估。",
                    })
            except (KeyError, ValueError):
                pass

    if "weak_emotion" in reason_analysis.get("signals", []):
        signals.append({
            "type": "EMOTION",
            "severity": "medium",
            "message": "开仓理由更多来自感觉，而不是客观依据。",
            "suggestion": "把感觉改写成可验证的技术条件，例如关键位置、指标或结构变化。",
        })

    if reason_analysis.get("level") in ["POOR", "IMPULSIVE", "MISSING"]:
        signals.append({
            "type": "WEAK_REASON",
            "severity": "medium",
            "message": reason_analysis.get("feedback"),
            "suggestion": "先写清楚入场前提、失效条件和风险收益，再决定是否交易。",
        })

    return signals


def get_impulse_statistics(trades: List[Dict]) -> Dict:
    """Calculate impulse trading statistics across all trades."""
    if not trades:
        return {}

    impulse_count = 0
    impulse_types = {}
    impulse_trades = []
    normal_trades = []

    for index, trade in enumerate(trades):
        signals = detect_impulse_trade(trade, trades[:index])
        if signals:
            impulse_count += 1
            impulse_trades.append(trade)
            for signal in signals:
                signal_type = signal["type"]
                impulse_types[signal_type] = impulse_types.get(signal_type, 0) + 1
        else:
            normal_trades.append(trade)

    impulse_wins = len([trade for trade in impulse_trades if trade.get("result") == "WIN"])
    normal_wins = len([trade for trade in normal_trades if trade.get("result") == "WIN"])
    impulse_win_rate = (impulse_wins / len(impulse_trades) * 100) if impulse_trades else 0
    normal_win_rate = (normal_wins / len(normal_trades) * 100) if normal_trades else 0

    return {
        "total_trades": len(trades),
        "impulse_count": impulse_count,
        "impulse_percentage": (impulse_count / len(trades) * 100) if trades else 0,
        "impulse_types": impulse_types,
        "impulse_win_rate": impulse_win_rate,
        "normal_win_rate": normal_win_rate,
        "impulse_trades": impulse_trades,
        "normal_trades": normal_trades,
    }


PRICE_ACTION_PATTERNS = {
    "breakout": {
        "keywords": ["突破", "breakout", "冲破"],
        "description": "价格突破关键位置",
    },
    "retest": {
        "keywords": ["回踩", "回测", "确认", "retest", "pullback"],
        "description": "突破后的回踩确认",
    },
    "bounce": {
        "keywords": ["反弹", "支撑", "bounce", "support"],
        "description": "支撑位反弹",
    },
    "rejection": {
        "keywords": ["阻力", "回落", "reject", "resistance"],
        "description": "阻力位回落",
    },
    "consolidation": {
        "keywords": ["盘整", "区间", "consolidation", "range"],
        "description": "区间盘整",
    },
}

MA_PATTERNS = {
    "ma_support": {
        "keywords": ["均线支撑", "MA 支撑", "EMA 支撑", "ma support"],
        "description": "均线作为支撑",
    },
    "ma_resistance": {
        "keywords": ["均线阻力", "MA 阻力", "EMA 阻力", "ma resistance"],
        "description": "均线作为阻力",
    },
    "golden_cross": {
        "keywords": ["金叉", "golden cross"],
        "description": "均线金叉",
    },
    "death_cross": {
        "keywords": ["死叉", "death cross"],
        "description": "均线死叉",
    },
}


def detect_price_action_pattern(reason: str) -> List[Dict]:
    """Detect price action and moving average patterns mentioned in the reason."""
    patterns = []
    reason_lower = reason.lower()

    for pattern_name, pattern_info in PRICE_ACTION_PATTERNS.items():
        for keyword in pattern_info["keywords"]:
            if keyword.lower() in reason_lower:
                patterns.append({
                    "type": "price_action",
                    "pattern": pattern_name,
                    "description": pattern_info["description"],
                })
                break

    for pattern_name, pattern_info in MA_PATTERNS.items():
        for keyword in pattern_info["keywords"]:
            if keyword.lower() in reason_lower:
                patterns.append({
                    "type": "ma_pattern",
                    "pattern": pattern_name,
                    "description": pattern_info["description"],
                })
                break

    return patterns


def format_impulse_report(stats: Dict) -> str:
    """Format impulse trading statistics into a readable report."""
    if not stats:
        return "暂无数据"

    lines = [
        "=" * 50,
        "冲动交易分析报告",
        "=" * 50,
        "",
        f"总交易数：{stats['total_trades']}",
        f"冲动交易：{stats['impulse_count']} ({stats['impulse_percentage']:.1f}%)",
        "",
        "冲动类型分布：",
    ]

    for impulse_type, count in stats.get("impulse_types", {}).items():
        lines.append(f"  - {impulse_type}: {count} 次")

    lines.extend([
        "",
        "胜率对比：",
        f"  - 冲动交易胜率：{stats['impulse_win_rate']:.1f}%",
        f"  - 理性交易胜率：{stats['normal_win_rate']:.1f}%",
        "",
    ])

    if stats["impulse_win_rate"] < stats["normal_win_rate"]:
        diff = stats["normal_win_rate"] - stats["impulse_win_rate"]
        lines.append(f"洞察：减少冲动交易，理论上可提升胜率约 {diff:.1f}%")

    lines.append("=" * 50)
    return "\n".join(lines)
