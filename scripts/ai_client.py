#!/usr/bin/env python3
"""
Minimal OpenAI-compatible client for No-FOMO AI reviews.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).parent.parent
LOCAL_ENV_FILES = [
    BASE_DIR / ".ai.env",
    BASE_DIR / ".env",
]

PRE_TRADE_VERDICTS = {"可执行", "需补充", "不建议"}
POST_TRADE_VERDICTS = {"执行良好", "执行一般", "需要反思"}


class AIReviewError(RuntimeError):
    """Raised when AI review configuration or request fails."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def load_local_env() -> None:
    """Load simple KEY=VALUE pairs from local env files."""
    for path in LOCAL_ENV_FILES:
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key:
                    os.environ[key] = value


def load_ai_config() -> dict[str, str]:
    """Load and validate OpenAI-compatible config."""
    load_local_env()
    config = {
        "api_key": os.getenv("AI_API_KEY", "").strip(),
        "base_url": os.getenv("AI_BASE_URL", "").strip(),
        "model": os.getenv("AI_MODEL", "").strip(),
    }

    missing = [name for name, value in config.items() if not value]
    if missing:
        pretty = {
            "api_key": "AI_API_KEY",
            "base_url": "AI_BASE_URL",
            "model": "AI_MODEL",
        }
        missing_labels = ", ".join(pretty[name] for name in missing)
        raise AIReviewError("missing_config", f"AI 配置缺失：{missing_labels}。请检查 .ai.env。")

    return config


def build_system_prompt(review_type: str) -> str:
    review_scope = "before a trade" if review_type == "pre_trade" else "after a trade is closed"
    return (
        "You are No-FOMO's bilingual trade-discipline reviewer.\n"
        "You are not a signal caller, not a market predictor, and not an auto-trading assistant.\n"
        f"Your job is to review decision quality {review_scope}.\n\n"
        "Core rules:\n"
        "1. Focus on process quality, not profit potential.\n"
        "2. Penalize FOMO, revenge trading, unclear thesis, missing stop loss, poor risk/reward, and emotional language.\n"
        "3. Do not encourage adding size, chasing, or gambling behavior.\n"
        "4. Output in Simplified Chinese as the default, with concise mixed English terms only when useful.\n"
        "5. The encouragement field must reward discipline, clarity, restraint, and review habit. Never reward profit expectation.\n"
        "6. Return valid JSON only.\n"
    )


def build_pre_trade_user_prompt(payload: dict[str, Any]) -> str:
    return (
        "请基于以下开仓前信息，审查这笔交易决策质量。\n"
        "请不要预测涨跌，只评估这次决策是否清晰、克制、具备风控意识。\n"
        "请返回 JSON，字段固定为：score, verdict, strengths, risks, action, encouragement。\n\n"
        "字段要求：\n"
        "- score: 0-100 的整数\n"
        "- verdict: 只允许使用 可执行 / 需补充 / 不建议\n"
        "- strengths: 字符串数组，列出本次计划的优点\n"
        "- risks: 字符串数组，列出主要风险点\n"
        "- action: 一句明确、可执行的下一步建议\n"
        "- encouragement: 一句正向反馈，只能奖励纪律与过程，不能奖励盈利预期\n\n"
        f"输入数据：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def build_post_trade_user_prompt(payload: dict[str, Any]) -> str:
    return (
        "请基于以下已结束交易信息，做一次交易后复盘。\n"
        "请不要把盈亏结果本身当作唯一标准，而是评估这笔交易的执行质量、纪律性与可复用经验。\n"
        "请返回 JSON，字段固定为：score, verdict, strengths, risks, action, encouragement。\n\n"
        "字段要求：\n"
        "- score: 0-100 的整数\n"
        "- verdict: 只允许使用 执行良好 / 执行一般 / 需要反思\n"
        "- strengths: 字符串数组，列出本次交易中做得对的地方\n"
        "- risks: 字符串数组，列出本次交易暴露的问题\n"
        "- action: 一句明确、可执行的下次改进建议\n"
        "- encouragement: 一句正向反馈，只能奖励纪律、复盘与执行，不奖励盈利预期\n\n"
        f"输入数据：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def build_user_prompt(payload: dict[str, Any], review_type: str) -> str:
    if review_type == "post_trade":
        return build_post_trade_user_prompt(payload)
    return build_pre_trade_user_prompt(payload)


def normalize_review(payload: dict[str, Any], review_type: str) -> dict[str, Any]:
    """Normalize model output into the required schema."""
    verdict = str(payload.get("verdict", "")).strip()
    allowed_verdicts = POST_TRADE_VERDICTS if review_type == "post_trade" else PRE_TRADE_VERDICTS
    default_verdict = "执行一般" if review_type == "post_trade" else "需补充"
    if verdict not in allowed_verdicts:
        verdict = default_verdict

    try:
        score = int(payload.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    strengths = payload.get("strengths")
    if not isinstance(strengths, list):
        strengths = []
    strengths = [str(item).strip() for item in strengths if str(item).strip()]

    risks = payload.get("risks")
    if not isinstance(risks, list):
        risks = []
    risks = [str(item).strip() for item in risks if str(item).strip()]

    if review_type == "post_trade":
        default_action = "把这次交易的得失写成一条明确规则，下一次按规则执行。"
        default_encouragement = "你愿意在交易结束后认真复盘，这就是建立稳定系统的关键动作。"
    else:
        default_action = "先补全关键信息，再决定是否入场。"
        default_encouragement = "你愿意在开仓前停下来审查计划，这本身就是正确的交易动作。"

    action = str(payload.get("action", "")).strip() or default_action
    encouragement = str(payload.get("encouragement", "")).strip() or default_encouragement

    return {
        "score": score,
        "verdict": verdict,
        "strengths": strengths,
        "risks": risks,
        "action": action,
        "encouragement": encouragement,
    }


def request_ai_review(payload: dict[str, Any], review_type: str = "pre_trade") -> dict[str, Any]:
    """Request a structured AI review from an OpenAI-compatible API."""
    config = load_ai_config()
    endpoint = config["base_url"].rstrip("/") + "/chat/completions"
    body = {
        "model": config["model"],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": build_system_prompt(review_type)},
            {"role": "user", "content": build_user_prompt(payload, review_type)},
        ],
    }

    request = Request(
        url=endpoint,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        },
    )

    raw_text = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                raw_text = response.read().decode("utf-8")
            break
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and attempt < 2:
                retry_after = exc.headers.get("Retry-After")
                try:
                    delay = max(1, int(retry_after)) if retry_after else (attempt + 1) * 5
                except ValueError:
                    delay = (attempt + 1) * 5
                time.sleep(delay)
                continue
            raise AIReviewError("http_error", f"AI 接口返回 HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AIReviewError("connection_error", f"AI 接口连接失败: {exc}") from exc

    if raw_text is None:
        raise AIReviewError("empty_response", "AI 接口未返回有效内容。")

    try:
        response_payload = json.loads(raw_text)
        content = response_payload["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise AIReviewError("bad_response", "AI 接口返回格式无法解析。") from exc

    try:
        review = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AIReviewError("bad_content", "AI 返回内容不是有效 JSON。") from exc

    return normalize_review(review, review_type)
