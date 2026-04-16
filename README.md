# no-fomo

> 一个用 AI 帮助交易者在开仓前冷静判断、在平仓后认真复盘的交易纪律工具。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

`no-fomo` 不是喊单工具，不预测涨跌，也不自动下单。

它解决的是另一个更常见、也更实际的问题：

- 明明没有清晰计划，却因为 FOMO 临时开仓
- 刚亏完一单，又立刻报复性再开一单
- 开仓理由很模糊，事后也无法复盘
- 交易做完了，但没有沉淀成自己的决策框架

这个项目的目标，是把交易行为拆成一个可重复执行的流程：

1. 开仓前先检查
2. 写下 thesis 和风险条件
3. 用 AI 辅助审查决策质量
4. 平仓后记录结果与执行情况
5. 再用 AI 做一次 post-trade review
6. 最后通过历史分析与周期复盘，反过来修正自己的交易框架

这就是 `No-FOMO` 当前的 MVP 闭环。

## 这个项目现在已经能做什么

当前版本已经完成并手动验证过以下能力：

### 1. Pre-trade check

在开仓前运行 [scripts/pre_trade_check.py](/C:/Users/10041/Desktop/no-fomo/scripts/pre_trade_check.py)，检查：

- 开仓理由质量
- 冲动交易风险
- 最近亏损后的 revenge trade 风险
- 相同 symbol + direction 的历史模式表现
- 止损、目标位、风险回报比

可选加上 `--ai`，让模型进一步输出结构化审核结果：

- `score`
- `verdict`
- `strengths`
- `risks`
- `action`
- `encouragement`

其中 `encouragement` 只奖励**纪律和过程**，不奖励盈利预期。

示例：

```bash
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 ^
  --stop-loss 84200 --target 87000 ^
  --reason "1h 突破回踩确认，MA20 支撑，失效位 84200，若放量跌回结构内则不做" ^
  --ai
```

### 2. Post-trade logging + AI review

在平仓后运行 [scripts/log_trade.py](/C:/Users/10041/Desktop/no-fomo/scripts/log_trade.py)，记录：

- symbol / direction / entry / exit / pnl
- timeframe
- reason
- notes
- indicators
- market context

可选加上 `--ai`，让模型对这笔交易做 post-trade review，重点不是“赚没赚”，而是：

- 这笔交易是否执行得当
- 理由是否足够清晰
- 是否存在冲动或情绪化成分
- 这次交易能沉淀出什么下次可复用的规则

示例：

```bash
python scripts/log_trade.py --symbol ETHUSDT --direction SHORT ^
  --entry 2480 --exit 2445 --pnl_percent 1.41 --result WIN ^
  --reason "1h 阻力回落确认，EMA20 压制，跌破回抽失败" ^
  --timeframe 1h --notes "manual validation with ai" --ai
```

### 3. AI review history

所有 AI 审核结果都会单独写入 `data/ai_reviews.json`，不会污染原始交易日志结构。

你可以通过 [scripts/ai_review_history.py](/C:/Users/10041/Desktop/no-fomo/scripts/ai_review_history.py) 回看历史 AI 记录：

- 查看最近记录
- 按 `pre_trade` / `post_trade` 过滤
- 按 `success` / `failed` 过滤
- 查看详细内容

示例：

```bash
python scripts/ai_review_history.py
python scripts/ai_review_history.py --status success --last 5
python scripts/ai_review_history.py --type post_trade --detail --last 2
```

### 4. 历史分析与周期复盘

当前项目还包含 3 个复盘脚本：

- [scripts/analyze_impulse.py](/C:/Users/10041/Desktop/no-fomo/scripts/analyze_impulse.py)
- [scripts/analyze_patterns.py](/C:/Users/10041/Desktop/no-fomo/scripts/analyze_patterns.py)
- [scripts/weekly_review.py](/C:/Users/10041/Desktop/no-fomo/scripts/weekly_review.py)

分别用于：

- 分析冲动交易占比和特征
- 提炼常见的 price action / MA pattern
- 输出周期复盘结果和改进目标

## 为什么这个项目和普通交易记录工具不一样

普通交易 journal 更像“事后记账”。

`No-FOMO` 想做的是更靠近决策过程的东西：

- 在你准备开仓的时候介入
- 在你已经开完、但还没形成坏习惯之前介入
- 把交易行为变成一个能被 AI 和人一起审视的过程

换句话说，它不是在帮你找“下一单机会”，而是在帮你建立“下一次不冲动的能力”。

## 当前闭环流程

推荐按这个顺序使用：

```text
Pre-trade check
  -> AI pre-trade review
  -> Open / manage trade manually
  -> Close trade
  -> Log trade
  -> AI post-trade review
  -> Review history / impulse analysis / weekly review
```

对应命令示例：

```bash
python scripts/pre_trade_check.py --symbol BTCUSDT --direction LONG --entry 85000 ^
  --stop-loss 84200 --target 87000 ^
  --reason "1h 突破回踩确认，MA20 支撑，失效位 84200，若放量跌回结构内则不做" --ai

python scripts/log_trade.py --symbol BTCUSDT --direction LONG ^
  --entry 85000 --exit 86000 --pnl_percent 1.18 --result WIN ^
  --reason "1h 突破回踩确认，MA20 支撑" --timeframe 1h --ai

python scripts/ai_review_history.py --status success --last 5
python scripts/analyze_impulse.py
python scripts/weekly_review.py --days 7
```

## AI 配置

AI 部分使用单独的本地 `.ai.env` 文件，不要提交到仓库。

项目根目录下创建：

```env
AI_API_KEY=your_api_key_here
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4.1-mini
```

当前实现基于 **OpenAI-compatible `/chat/completions`** 接口。

这意味着你可以接：

- OpenAI API
- 智谱 BigModel（OpenAI-compatible 路径）
- 其他兼容 OpenAI 接口格式的模型服务

例如智谱可以这样配置：

```env
AI_API_KEY=你的智谱API_KEY
AI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
AI_MODEL=glm-4.7-flash
```

## Binance Futures 导入

Binance 集成是可选能力，主要用于把**已结束的合约交易**导入本地 journal。

相关脚本：

- [scripts/binance_client.py](/C:/Users/10041/Desktop/no-fomo/scripts/binance_client.py)
- [scripts/binance_sync.py](/C:/Users/10041/Desktop/no-fomo/scripts/binance_sync.py)
- [scripts/setup_binance_config.py](/C:/Users/10041/Desktop/no-fomo/scripts/setup_binance_config.py)

当前边界：

- 只导入 **closed futures round-trips**
- 未平仓仓位不会作为完整交易导入
- 多天持仓可能需要显式传 `--start-time`

本地配置放在 `.binance.env`：

```env
BINANCE_MODE=live
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_FUTURES_BASE_URL=https://fapi.binance.com
BINANCE_RECV_WINDOW=5000
```

如果本地通过 Clash / Clash Verge 代理访问 Binance，Python 不一定自动继承浏览器代理，需要显式写：

```env
HTTPS_PROXY=http://127.0.0.1:7897
HTTP_PROXY=http://127.0.0.1:7897
```

先 dry-run：

```bash
python scripts/binance_sync.py --dry-run --json
```

## JSON 输出

当前核心脚本都支持 JSON 输出，便于自动化和后续扩展：

- `pre_trade_check.py --json`
- `pre_trade_check.py --json --ai`
- `log_trade.py` 当前默认是文本输出
- `ai_review_history.py --json`
- `analyze_impulse.py --json`
- `analyze_patterns.py --json`
- `weekly_review.py --json`
- `binance_sync.py --json`

统一 envelope 结构：

```json
{
  "meta": {
    "report_type": "example",
    "generated_at": "2026-01-01T00:00:00",
    "status": "ok"
  },
  "data": {}
}
```

错误结构：

```json
{
  "meta": {
    "report_type": "example",
    "generated_at": "2026-01-01T00:00:00",
    "status": "error"
  },
  "error": {
    "code": "example_error",
    "message": "Something went wrong."
  }
}
```

## 当前项目边界

这个项目现在适合被理解为：

**一个已经跑通、并完成手动验证的 AI trading discipline MVP。**

它现在已经能做的：

- 支持开仓前 AI 审核
- 支持平仓后 AI 复盘
- 支持 AI 历史回看
- 支持基础冲动交易分析与周期复盘
- 支持 Binance 已结束合约交易导入

它现在还**不**做的：

- 自动交易
- 预测市场方向
- 管理未平仓仓位作为一等公民对象
- Web UI / mobile app
- token / points / 勋章系统
- 多交易所统一接入层

## 安装与验证

### 环境要求

- Python 3.11+
- Windows / macOS / Linux

### 基础检查

```bash
python scripts/pre_trade_check.py --help
python scripts/log_trade.py --help
python scripts/ai_review_history.py --help
python scripts/weekly_review.py --json
```

### 当前建议的手动验证顺序

1. 跑一次 `pre_trade_check.py`
2. 跑一次 `pre_trade_check.py --ai`
3. 跑一次 `log_trade.py`
4. 跑一次 `log_trade.py --ai`
5. 跑一次 `ai_review_history.py`
6. 跑 `analyze_impulse.py --json`
7. 跑 `analyze_patterns.py --json`
8. 跑 `weekly_review.py --json`

## 安全说明

- 不要提交 `.ai.env`
- 不要提交 `.binance.env`
- 不要在 issue、截图、聊天记录里暴露真实 key
- Binance API 尽量只开 read 权限和必要的 futures 读取权限
- 如果网络环境允许，优先加 IP 限制

## License

MIT. See [LICENSE](/C:/Users/10041/Desktop/no-fomo/LICENSE).

## Disclaimer

本项目用于交易复盘、决策审查和流程辅助。

它不是投资建议，也不会替代你的风险管理。
加密货币合约交易风险极高，可能导致本金损失。
