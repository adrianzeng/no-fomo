# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project Overview

**no-fomo** is an AI-assisted trading discipline tool for discretionary traders.

It is designed around a simple idea:

- review the trade thesis before entry
- review execution after exit
- reduce FOMO, revenge trading, and low-quality decisions
- build a repeatable decision process rather than chasing signals

This project is intentionally:

- not a market prediction product
- not an auto-trading bot
- not a quant platform

It is both:

1. a standalone local CLI tool
2. a skill-oriented project that can be used through OpenClaw / Claude Code style workflows

## Current Product Shape

The current MVP already supports a full review loop:

1. `pre_trade_check.py`
2. optional AI pre-trade review via `--ai`
3. manual trade execution outside the tool
4. `log_trade.py`
5. optional AI post-trade review via `--ai`
6. history lookup through `ai_review_history.py`
7. periodic analysis through impulse / pattern / weekly review scripts

This means the repository should be treated as an **AI trading discipline MVP**, not just a collection of utility scripts.

## Important Principles

When editing or extending this project, preserve these boundaries:

### What No-FOMO should do

- help users clarify their thesis before entry
- help users review execution quality after exit
- reinforce discipline, not excitement
- identify impulse behavior and repeated decision patterns
- work well in CLI-first or skill-style workflows

### What No-FOMO should not do

- tell users which direction the market will go
- automatically place or manage trades
- optimize for hype, token incentives, or gamified speculation
- reward raw profit over decision quality

## Current Core Scripts

### Core decision flow

- `scripts/pre_trade_check.py`
- `scripts/log_trade.py`
- `scripts/ai_review_history.py`

### Analysis layer

- `scripts/analyze_impulse.py`
- `scripts/analyze_patterns.py`
- `scripts/weekly_review.py`

### Shared AI / utility layer

- `scripts/ai_client.py`
- `scripts/trade_analysis_utils.py`

### Exchange integration

- `scripts/binance_client.py`
- `scripts/binance_sync.py`
- `scripts/setup_binance_config.py`

## Data Files

Primary local data files:

- `data/trades.json`
- `data/ai_reviews.json`
- `data/learned_rules.json`

Guidance:

- `trades.json` is the trade journal
- `ai_reviews.json` stores AI review history separately
- avoid mixing AI review records directly into unrelated structures unless necessary

## AI Configuration

AI review uses a separate local `.ai.env` file.

Expected keys:

- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`

The project currently uses an **OpenAI-compatible `/chat/completions`** interface.

That means Claude Code should preserve this design unless there is a strong reason to change it.
Do not add provider-specific SDK complexity by default.

## Binance Configuration

Binance integration uses local `.binance.env`.

Expected use:

- import completed Binance Futures trades
- not manage open positions as first-class records yet

Important:

- local proxy behavior matters
- browser access and Python access are not equivalent
- avoid assuming system proxy is automatically inherited by CLI tools

## Development Priorities

If asked what should be built next, the priority order is:

1. strengthen the current AI review loop
2. add active trade intervention (`active_trade_review.py`)
3. add AI-powered periodic coaching / summaries
4. improve structured input ergonomics
5. only then consider UI or broader exchange support

Avoid jumping to:

- multi-exchange support too early
- token / points systems
- dashboard-first work before the decision loop is solid

## Editing Guidance

When making changes:

- prefer extending existing scripts over creating unnecessary new entrypoints
- keep outputs UTF-8 safe
- preserve machine-readable JSON envelopes where they already exist
- keep AI feedback focused on discipline, clarity, and execution quality
- do not let AI wording drift into market prediction or overconfidence

If adding a new AI review step, it should usually output:

- `score`
- `verdict`
- `strengths`
- `risks`
- `action`
- `encouragement`

And `encouragement` must reward process quality, not profit outcome.

## Quick Commands

### Basic validation

```bash
python scripts/pre_trade_check.py --help
python scripts/log_trade.py --help
python scripts/ai_review_history.py --help
python scripts/weekly_review.py --json
```

### Pre-trade review

```bash
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --stop-loss 84200 --target 87000 \
  --reason "1h breakout retest confirmation, MA20 support, invalidation below 84200" \
  --ai
```

### Post-trade review

```bash
python scripts/log_trade.py --symbol ETHUSDT --direction SHORT \
  --entry 2480 --exit 2445 --pnl_percent 1.41 --result WIN \
  --reason "1h resistance rejection, EMA20 pressure, failed retest" \
  --timeframe 1h --ai
```

### AI review history

```bash
python scripts/ai_review_history.py
python scripts/ai_review_history.py --status success --last 5
python scripts/ai_review_history.py --type post_trade --detail --last 2
```

### Analysis scripts

```bash
python scripts/analyze_impulse.py --json
python scripts/analyze_patterns.py --json
python scripts/weekly_review.py --json
```

### Syntax check

```bash
python -m py_compile scripts/*.py
```

## Skill / Agent Use

This repository may be used as a skill-like project in OpenClaw or Claude Code contexts.

That means good changes should preserve:

- clear CLI entrypoints
- composable JSON outputs
- local-file configuration
- low dependency overhead
- deterministic behavior suitable for agent workflows

Do not redesign it around a heavy framework unless the user explicitly asks for that shift.

## Documentation Alignment

Keep these files aligned with the actual implementation:

- `README.md`
- `ROADMAP.md`
- `CLAUDE.md`
- `SKILL.md`

If implementation meaningfully changes the product shape, update the docs in the same pass.
