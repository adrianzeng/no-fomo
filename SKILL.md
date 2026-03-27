---
name: no-fomo
description: Trade without FOMO. A self-learning system that detects impulsive trades, analyzes your patterns, and helps you build disciplined trading habits through deliberate review.
metadata: {"openclaw":{"emoji":"🧠","requires":{"bins":["python3"]}}}
---

# no-fomo - No FOMO Trading

> 让每笔交易都变成学习，而不是赌博

AI-powered trading discipline coach. This skill stores every trade with full context, detects impulse patterns (FOMO, revenge trading, emotional decisions), analyzes price action and MA patterns, and generates actionable improvement goals through weekly reviews.

## The Problem

Most traders lose money because they:
- Enter trades impulsively without clear rationale
- Chase price movements (FOMO)
- Trade revenge after losses
- Never review and learn from their mistakes

## The Solution

**no-fomo** helps you build disciplined trading habits through:
1. **Pre-trade checks** - Pause and think before entering
2. **Reason quality analysis** - Score your entry rationale (0-100)
3. **Impulse detection** - Identify FOMO, revenge, emotional trades
4. **Pattern analysis** - Learn which setups work for YOU
5. **Weekly reviews** - Structured reflection with improvement goals

## Quick Start

### 1. Log Your First Trade

```bash
python3 {baseDir}/scripts/log_trade.py \
  --symbol BTCUSDT \
  --direction LONG \
  --entry 85000 \
  --exit 86000 \
  --pnl_percent 1.18 \
  --result WIN \
  --reason "突破 85000 阻力后回踩确认，MA5 支撑，MACD 金叉" \
  --timeframe 1h
```

The script will automatically:
- Analyze your reason quality (score 0-100)
- Detect impulse signals (FOMO, emotion, weak reason)
- Provide immediate feedback

### 2. Pre-Trade Check (Before Opening)

```bash
python3 {baseDir}/scripts/pre_trade_check.py \
  --symbol BTCUSDT \
  --direction LONG \
  --entry 85000 \
  --reason "1h 突破回踩，MA20 支撑"
```

### 3. Review Your Patterns

```bash
# Analyze impulse trades
python3 {baseDir}/scripts/analyze_impulse.py

# Analyze price action patterns
python3 {baseDir}/scripts/analyze_patterns.py

# Generate weekly review
python3 {baseDir}/scripts/weekly_review.py
```

## Scripts Reference

| Script | Purpose |
|---|---|
| `log_trade.py` | Log trades with reason quality analysis |
| `pre_trade_check.py` | Pre-trade checklist to avoid impulses |
| `analyze_impulse.py` | Detect FOMO, revenge, emotional trades |
| `analyze_patterns.py` | Price action & MA pattern analysis |
| `weekly_review.py` | Weekly review with improvement goals |
| `analyze.py` | Basic win rate & PnL analysis |
| `generate_rules.py` | Generate data-backed rules |
| `binance_sync.py` | Import Binance Futures trades |
| `binance_auto_learn.py` | Auto-sync + analyze + learn |

## Data Files

| File | Purpose |
|---|---|
| `data/trades.json` | Trade history with reason quality |
| `data/learned_rules.json` | Generated trading rules |
| `.binance.env` | Binance API configuration |

## Binance Integration (Optional)

For automatic trade import from Binance USDT-M Futures:

```bash
# One-time setup
python3 {baseDir}/scripts/setup_binance_config.py

# Sync trades
python3 {baseDir}/scripts/binance_sync.py --symbol BTCUSDT

# Auto-learn (sync + analyze + generate rules)
python3 {baseDir}/scripts/binance_auto_learn.py --symbol BTCUSDT
```

Config modes:
- `BINANCE_MODE=live` - Live trading
- `BINANCE_MODE=testnet` - Testnet trading

See full Binance documentation in README.md.

## Trade Data Format

Trades stored in `data/trades.json`:

```json
{
  "trades": [{
    "id": "abc123",
    "timestamp": "2026-03-28T10:00:00",
    "symbol": "BTCUSDT",
    "direction": "LONG",
    "entry": 85000,
    "exit": 86000,
    "pnl_percent": 1.18,
    "result": "WIN",
    "timeframe": "1h",
    "reason": "突破回踩确认，MA5 支撑",
    "reason_quality": {"score": 80, "level": "EXCELLENT"},
    "impulse_signals": []
  }]
}
```

## Best Practices

1. **Log every trade** - Including losses, especially losses
2. **Write detailed reasons** - This is how you learn
3. **Use pre-trade check** - Before opening, not after
4. **Review weekly** - Run `weekly_review.py` every weekend
5. **Trust data, not feelings** - Let your history speak

## Limitations

- No real-time data collection
- No automatic indicator integration
- No mobile/web UI (CLI only)

## Contributing

Contributions welcome! Please read README.md for guidelines.

## License

MIT License - See LICENSE file.

