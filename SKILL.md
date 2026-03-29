---
name: no-fomo
description: Trade without FOMO. A self-learning system that detects impulsive trades, analyzes your patterns, and helps you build disciplined trading habits through deliberate review.
version: 1.0.0
author: 糕头
category: trading
metadata: {"openclaw":{"emoji":"🧠","requires":{"bins":["python3"]}}}
---

# no-fomo - No FOMO Trading

> 让每笔交易都变成学习，而不是赌博

**AI-powered trading discipline coach.** This skill stores every trade with full context, detects impulse patterns (FOMO, revenge trading, emotional decisions), analyzes price action and MA patterns, and generates actionable improvement goals through weekly reviews.

---

## 📋 核心功能

| 功能 | 说明 | 适用场景 |
|------|------|----------|
| **开仓前检查** | 强制冷静，检测冲动信号 | 开仓前防止手痒 |
| **理由质量评分** | 0-100 分区分理性 vs 冲动 | 评估开仓依据 |
| **冲动交易识别** | FOMO/报复/情绪化检测 | 复盘时发现问题 |
| **K 线形态分析** | 突破/回踩/均线模式识别 | 积累个人模式库 |
| **周报复盘** | 自动生成改进报告 | 持续优化交易体系 |

---

## 🚀 OpenClaw 调用方式

### 前置要求
- Python 3.11+
- 工作目录：`{baseDir}` = `C:\Users\10041\.openclaw\workspace\skills\no-fomo`

### 1. 记录交易

```bash
openclaw skill-run no-fomo log_trade \
  --symbol BTCUSDT \
  --direction LONG \
  --entry 85000 \
  --exit 86000 \
  --pnl_percent 1.18 \
  --result WIN \
  --reason "突破 85000 阻力后回踩确认，MA5 支撑，MACD 金叉" \
  --timeframe 1h
```

**自动分析：**
- ✅ 理由质量评分（0-100）
- ⚠️ 冲动信号检测（FOMO/情绪/弱理由）
- 📊 即时反馈

### 2. 开仓前检查（强烈推荐）

```bash
openclaw skill-run no-fomo pre_trade_check \
  --symbol BTCUSDT \
  --direction LONG \
  --entry 85000 \
  --reason "1h 突破回踩，MA20 支撑"
```

**输出：**
- 理由质量评分 + 反馈
- 冲动信号检测（如刚亏损）
- 历史胜率匹配
- 综合建议（开仓/观望）

### 3. 查看统计

```bash
# 交易统计
openclaw skill-run no-fomo stats

# 最近 N 笔交易
openclaw skill-run no-fomo list --last 10

# 冲动交易分析
openclaw skill-run no-fomo analyze_impulse

# K 线形态分析
openclaw skill-run no-fomo analyze_patterns

# 周报复盘
openclaw skill-run no-fomo weekly_review --days 7
```

### 4. Binance 自动同步（可选）

```bash
# 首次配置
openclaw skill-run no-fomo setup_binance_config

# 同步交易
openclaw skill-run no-fomo binance_sync --symbol BTCUSDT

# 自动学习（同步 + 分析 + 生成规则）
openclaw skill-run no-fomo binance_auto_learn --symbol BTCUSDT
```

---

## 📋 完整命令参考

| 命令 | 说明 | 示例 |
|------|------|------|
| `log_trade` | 记录交易（含理由分析） | `log_trade --symbol BTCUSDT --direction LONG ...` |
| `pre_trade_check` | 开仓前检查清单 | `pre_trade_check --symbol BTCUSDT --reason "突破回踩"` |
| `stats` | 交易统计（胜率/PnL） | `stats` |
| `list` | 列出交易记录 | `list --last 10` |
| `analyze_impulse` | 冲动交易分析 | `analyze_impulse --detail` |
| `analyze_patterns` | K 线形态分析 | `analyze_patterns` |
| `weekly_review` | 周报复盘报告 | `weekly_review --days 7` |
| `generate_rules` | 生成交易规则 | `generate_rules` |
| `binance_sync` | 同步 Binance 交易 | `binance_sync --symbol BTCUSDT` |
| `binance_auto_learn` | 自动学习流程 | `binance_auto_learn --symbol BTCUSDT` |
| `setup_binance_config` | 配置 Binance API | `setup_binance_config` |

---

## 📁 数据文件

| 文件 | 位置 | 说明 |
|------|------|------|
| `trades.json` | `data/trades.json` | 交易历史记录 |
| `learned_rules.json` | `data/learned_rules.json` | 生成的交易规则 |
| `.binance.env` | 根目录 | Binance API 配置（可选） |

---

## 📊 交易数据格式

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

---

## 🎓 使用最佳实践

### 1. 每笔交易都记录
- ✅ 盈利单要记
- ❌ **亏损单更要记**（这是学习的关键）

### 2. 理由要具体
- ✅ 好理由：`"1h 突破 85000 后回踩确认，MA5 支撑，MACD 金叉"`
- ❌ 差理由：`"感觉要涨"`、`"试试"`

### 3. 开仓前必查
- 在开仓前运行 `pre_trade_check`
- 如果检测到冲动信号 → **停下来，等 1 小时**

### 4. 每周复盘
- 周末运行 `weekly_review --days 7`
- 根据报告调整下周交易计划

### 5. 相信数据，不是感觉
- 让历史交易记录告诉你什么模式有效
- 不要因为一两笔亏损否定系统

---

## ⚠️ 注意事项

### 数据目录
- 当前数据存储在 `skills/no-fomo/data/trades.json`
- 建议定期备份此文件

### Binance 配置（可选）
- 如使用 Binance 自动同步，需配置 API Key
- **永远不要分享你的 API Secret**
- 建议只开通**只读权限**

### 局限性
- ❌ 无实时数据收集（需手动记录或 Binance 同步）
- ❌ 无自动指标集成（需手动描述）
- ❌ 无移动端/Web UI（纯 CLI）

---

## 🔧 故障排查

### Python 版本检查
```bash
python3 --version
# 需要 3.11+
```

### 测试安装
```bash
openclaw skill-run no-fomo log_trade --help
```

### 数据文件损坏
删除 `data/trades.json` 重新开始（先备份！）

---

## 📖 相关文档

- [README.md](README.md) - 完整项目文档（中英双语）
- [CLAUDE.md](CLAUDE.md) - 开发者指南
- [PREPUBLISH_REPORT.md](PREPUBLISH_REPORT.md) - 发布报告

---

## 💡 示例工作流

### 完整交易流程

```bash
# 1. 开仓前：冷静检查
openclaw skill-run no-fomo pre_trade_check \
  --symbol BTCUSDT --direction LONG --entry 85000 \
  --reason "1h 突破回踩，MA20 支撑"

# 2. 平仓后：记录交易
openclaw skill-run no-fomo log_trade \
  --symbol BTCUSDT --direction LONG \
  --entry 85000 --exit 86000 --pnl_percent 1.18 --result WIN \
  --reason "1h 突破回踩确认，MA5 支撑" --timeframe 1h

# 3. 周末：复盘分析
openclaw skill-run no-fomo weekly_review --days 7
```

### 查看当前状态

```bash
# 胜率统计
openclaw skill-run no-fomo stats

# 最近交易
openclaw skill-run no-fomo list --last 5

# 有没有冲动交易
openclaw skill-run no-fomo analyze_impulse
```

---

## 🤝 贡献

欢迎贡献！请阅读 README.md 了解指南。

## 📄 许可证

MIT License - 详见 LICENSE 文件。

## ⚠️ 免责声明

**重要提示**：
- 本工具仅供学习和研究使用
- 不构成任何投资建议或交易建议
- 加密货币交易存在高风险，可能导致本金损失
- 请自行承担交易风险
- 过往表现不代表未来结果

---

**Created by 糕头 | 让每笔交易都变成学习，而不是赌博** 🧠
