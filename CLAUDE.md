# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**no-fomo** is a trading discipline tool that helps traders avoid impulsive decisions (FOMO, revenge trading, emotional trades) through structured review and analysis. It's designed as both a standalone CLI tool and an OpenClaw Skill.

## Quick Commands

```bash
# Test/installation check (no dependencies required)
python scripts/log_trade.py --help

# Log a trade
python scripts/log_trade.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --exit 86000 --pnl_percent 1.18 --result WIN \
  --reason "突破回踩确认，MA5 支撑" --timeframe 1h

# Pre-trade check
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --reason "1h 突破回踩，MA20 支撑"

# Analysis commands
python scripts/analyze.py              # Basic stats
python scripts/analyze_impulse.py      # Impulse trading analysis
python scripts/analyze_patterns.py     # Price action & MA patterns
python scripts/weekly_review.py        # Weekly review report

# Syntax check before commit
python -m py_compile scripts/*.py
```

## Architecture

### Core Modules

```
scripts/
├── trade_analysis_utils.py    # Shared utilities (reason analysis, impulse detection)
├── log_trade.py               # Trade logging with reason quality analysis
├── pre_trade_check.py         # Pre-trade checklist
├── analyze_impulse.py         # FOMO/revenge/emotion detection
├── analyze_patterns.py        # Price action & MA pattern analysis
├── weekly_review.py           # Weekly review reports
├── analyze.py                 # Basic win rate & PnL analysis
├── generate_rules.py          # Rule generation from historical data
└── binance_*.py               # Binance Futures integration (optional)
```

### Data Flow

1. **Trade Logging** → `data/trades.json` (with reason_quality, impulse_signals, timeframe)
2. **Analysis Scripts** → Read trades, output reports/insights
3. **Rule Generation** → `data/learned_rules.json`

### Key Design Principles

1. **Zero external dependencies** - Core uses only Python standard library
2. **JSON-first storage** - All data in JSON format
3. **CLI-first design** - Easy to integrate and automate
4. **ASCII output** - Compatible with Windows default terminal encoding
5. **Modular scripts** - Each script runs independently, composable

## Technical Notes

- **Python 3.11+** required (uses `str | None` union syntax)
- **UTF-8 encoding** for all file I/O (Windows compatibility via `sys.stdout` wrapper)
- **No database** - Uses JSON files for simplicity

## OpenClaw Skill

This is also an OpenClaw Skill (`SKILL.md`, `_meta.json`). The skill:
- Runs via `python3 {baseDir}/scripts/xxx`
- Requires Python 3.11+
- Emoji: 🧠

## Common Development Tasks

### Adding a new analysis script

1. Create `scripts/new_feature.py`
2. Import utilities: `from trade_analysis_utils import ...`
3. Use `DATA_DIR = Path(__file__).parent.parent / "data"` for data paths
4. Add UTF-8 encoding wrapper for Windows
5. Support `--json` flag for AI consumption

### Testing changes

```bash
# Syntax check
python -m py_compile scripts/your_script.py

# Run with test data
python scripts/your_script.py --json
```

### Documentation

- User-facing: `README.md` (Chinese + English)
- OpenClaw Skill: `SKILL.md`
- Release notes: `PREPUBLISH_REPORT.md`
