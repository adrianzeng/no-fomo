# no-fomo

> 让每笔交易都变成学习，而不是赌博

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**no-fomo** 是一个帮助你避免冲动交易的自我复盘工具。它记录你的每笔交易，分析交易模式，识别 FOMO、报复性交易等冲动行为，并生成可执行的改进建议。

---

## 🎯 项目起源

这个项目源于创作者自身的大半年交易学习经历。在观察市场后发现：

- 大部分交易者都是**冲动型交易**
- 很多人不知道为什么要开多/开空，只是因为 K 线在上涨就 FOMO 追入
- 追多的位置往往并不合理
- 通过**复盘学习**，可以让交易道路变得更加顺畅

**no-fomo 的目的**：让新手学会复盘，知道自己每次开单是理性决策，而不是冲动消费。

---

## ✨ 核心功能

### 1. 开仓理由质量检测
记录交易时自动分析你的开仓理由质量（0-100 分），识别：
- ✅ 强理由：技术面依据、具体价格、指标信号
- ⚠️ 弱理由：感觉、试试、FOMO 追涨

```bash
python scripts/log_trade.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --exit 86000 --pnl_percent 1.18 --result WIN \
  --reason "突破 85000 阻力后回踩确认，MA5 支撑，MACD 金叉"
```

### 2. 冲动交易识别
自动检测：
- **FOMO** - 追涨杀跌
- **报复性交易** - 亏损后立即开新仓
- **情绪化交易** - 基于"感觉"而非客观依据

```bash
python scripts/analyze_impulse.py --detail
```

### 3. 开仓前检查
在开仓前强制你停下来思考，提供实时反馈：

```bash
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --reason "突破回踩确认，MA 支撑"
```

### 4. K 线形态分析
识别价格行为和均线模式：
- 价格行为：突破、回踩、反弹、回落、盘整
- 均线模式：均线支撑、均线阻力、金叉、死叉

```bash
python scripts/analyze_patterns.py
```

### 5. 周报复盘报告
自动生成包含以下内容的周报：
- 表现摘要（胜率、PnL、盈利因子）
- 最佳/最差交易
- 开仓理由质量分布
- 冲动交易分析
- 本周学到的教训
- 下周改进目标

```bash
python scripts/weekly_review.py --days 7
```

---

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Windows / macOS / Linux

### 安装

```bash
# 克隆仓库
git clone https://github.com/adrianzeng/no-fomo.git
cd no-fomo

# 测试安装（无需额外依赖）
python scripts/log_trade.py --help
```

### 记录第一笔交易

```bash
python scripts/log_trade.py \
  --symbol BTCUSDT \
  --direction LONG \
  --entry 85000 \
  --exit 86000 \
  --pnl_percent 1.18 \
  --result WIN \
  --reason "突破 85000 阻力后回踩确认，MA5 支撑" \
  --timeframe 1h
```

### 查看分析

```bash
# 查看交易统计
python scripts/log_trade.py --stats

# 分析冲动交易
python scripts/analyze_impulse.py

# 生成周报
python scripts/weekly_review.py
```

---

## 📁 项目结构

```
no-fomo/
├── scripts/
│   ├── log_trade.py              # 记录交易（含理由分析）
│   ├── pre_trade_check.py        # 开仓前检查
│   ├── analyze.py                # 交易分析
│   ├── analyze_impulse.py        # 冲动交易分析
│   ├── analyze_patterns.py       # K 线形态分析
│   ├── weekly_review.py          # 周报复盘
│   ├── generate_rules.py         # 规则生成
│   ├── update_memory.py          # 记忆更新
│   ├── trade_analysis_utils.py   # 分析工具库
│   └── [Binance 集成脚本...]
├── data/
│   ├── trades.json               # 交易数据
│   └── learned_rules.json        # 生成的规则
├── SKILL.md                      # OpenClaw Skill 文档
├── README.md                     # 本项目文档
├── LICENSE                       # MIT License
└── _meta.json                    # 元数据
```

---

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| 数据存储 | JSON |
| 分析引擎 | 自研规则引擎 |
| 兼容性 | Windows / macOS / Linux |

### 技术标准

本项目遵循以下技术原则：

1. **零外部依赖** - 核心功能仅使用 Python 标准库
2. **JSON 优先** - 所有数据以 JSON 格式存储，便于扩展
3. **CLI 优先** - 命令行界面，易于集成和自动化
4. **ASCII 输出** - 兼容 Windows 默认终端编码
5. **模块化设计** - 每个脚本独立运行，可组合使用

---

## 📖 使用示例

### 完整的交易复盘流程

```bash
# 1. 开仓前检查
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --reason "1h 突破回踩，MA20 支撑"

# 2. 平仓后记录
python scripts/log_trade.py --symbol BTCUSDT --direction LONG \
  --entry 85000 --exit 86000 --pnl_percent 1.18 --result WIN \
  --reason "1h 突破回踩确认，MA5 支撑" --timeframe 1h

# 3. 分析冲动交易
python scripts/analyze_impulse.py

# 4. 分析 K 线形态
python scripts/analyze_patterns.py

# 5. 生成周报
python scripts/weekly_review.py --save
```

---

## 🔌 Binance 集成（可选）

如果你使用 Binance Futures，可以自动导入交易记录：

```bash
# 配置 Binance API
python scripts/setup_binance_config.py

# 同步交易
python scripts/binance_sync.py --symbol BTCUSDT

# 自动学习
python scripts/binance_auto_learn.py --symbol BTCUSDT
```

---

## 📝 文档

- [SKILL.md](SKILL.md) - OpenClaw Skill 完整文档
- [PREPUBLISH_REPORT.md](PREPUBLISH_REPORT.md) - 发布报告

---

## 🤝 贡献

欢迎贡献！请参考以下步骤：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

---

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件。

---

## ⚠️ 免责声明

**重要提示**：

- 本工具仅供学习和研究使用
- 不构成任何投资建议或交易建议
- 加密货币交易存在高风险，可能导致本金损失
- 请自行承担交易风险
- 过往表现不代表未来结果

---

## 📬 联系方式

- 项目地址：https://github.com/adrianzeng/no-fomo
- 问题反馈：https://github.com/adrianzeng/no-fomo/issues

---

## 🙏 致谢

感谢所有为开源社区做出贡献的开发者。

如果这个项目对你有帮助，请给一个 ⭐️ Star！
