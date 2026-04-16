# No-FOMO Roadmap

## 一、项目定位

`No-FOMO` 是一个面向主观交易者的 **AI trading discipline system**。

它不做：

- market prediction
- auto-trading
- quant platform
- “告诉你现在该买还是该卖”的喊单产品

它要做的是另一件更实际的事：

- 在开仓前帮助用户把交易逻辑说清楚
- 在持仓中帮助用户识别情绪化操作
- 在平仓后帮助用户完成结构化复盘
- 长期减少 FOMO、revenge trading 和低质量决策

## 二、当前版本已经收敛的能力

这一部分代表：**已经实现、已经跑通、已经做过手动验证**。

### 1. Pre-trade check

脚本：

- [scripts/pre_trade_check.py](/C:/Users/10041/Desktop/no-fomo/scripts/pre_trade_check.py)

当前能力：

- 输入 `symbol / direction / entry / reason / timeframe / stop-loss / target`
- 输出 reason quality
- 输出 impulse signals
- 输出历史样本提示
- 输出 risk / reward
- 输出综合建议

状态：

- 已收敛

### 2. Pre-trade AI review

入口：

- `pre_trade_check.py --ai`

当前能力：

- 基于 OpenAI-compatible API 做结构化 AI 审核
- 输出 `score / verdict / strengths / risks / action / encouragement`
- `encouragement` 只奖励纪律和过程，不奖励盈利预期

状态：

- 已收敛

说明：

- 原 roadmap 里设想是独立 `pre_trade_ai_review.py`
- 当前实现并入 `pre_trade_check.py`
- 能力已经落地，形式做了简化

### 3. Trade logging

脚本：

- [scripts/log_trade.py](/C:/Users/10041/Desktop/no-fomo/scripts/log_trade.py)

当前能力：

- 记录平仓交易
- 保存 reason / notes / indicators / market context
- 自动附带 reason quality analysis
- 自动附带 impulse signal detection

状态：

- 已收敛

### 4. Post-trade AI review

入口：

- `log_trade.py --ai`

当前能力：

- 对已结束交易做结构化 AI 复盘
- 强调执行质量、纪律性、可复用经验
- 输出 `score / verdict / strengths / risks / action / encouragement`

状态：

- 已收敛

### 5. AI review history

脚本：

- [scripts/ai_review_history.py](/C:/Users/10041/Desktop/no-fomo/scripts/ai_review_history.py)

当前能力：

- 查看最近 AI 记录
- 按 `pre_trade / post_trade` 过滤
- 按 `success / failed` 过滤
- 查看详细内容
- 支持 `--json`

状态：

- 已收敛

### 6. 冲动交易分析

脚本：

- [scripts/analyze_impulse.py](/C:/Users/10041/Desktop/no-fomo/scripts/analyze_impulse.py)

当前能力：

- 输出冲动交易数量
- 输出 EMOTION / WEAK_REASON 等信号
- 对比冲动交易与非冲动交易表现

状态：

- 已收敛

### 7. 模式分析

脚本：

- [scripts/analyze_patterns.py](/C:/Users/10041/Desktop/no-fomo/scripts/analyze_patterns.py)

当前能力：

- 分析 price action / MA pattern
- 输出样本数与胜率摘要
- 输出模式洞察

状态：

- 已收敛

### 8. 周期复盘

脚本：

- [scripts/weekly_review.py](/C:/Users/10041/Desktop/no-fomo/scripts/weekly_review.py)

当前能力：

- performance summary
- best / worst trade
- reason quality distribution
- impulse review
- lessons learned
- next goals

状态：

- 已收敛

### 9. Binance 已平仓交易导入

脚本：

- [scripts/binance_client.py](/C:/Users/10041/Desktop/no-fomo/scripts/binance_client.py)
- [scripts/binance_sync.py](/C:/Users/10041/Desktop/no-fomo/scripts/binance_sync.py)

当前能力：

- 导入已完成的 Binance Futures round-trip
- 不会把 open position 直接写入 `trades.json`
- 支持本地代理配置

状态：

- 已收敛

当前边界：

- Python 侧可能需要显式 proxy 配置
- 多日持仓可能需要 `--start-time`
- 当前只重建 closed trades

### 10. OpenAI-compatible AI provider config

当前能力：

- `.ai.env`
- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`

已验证：

- 智谱 BigModel 可用
- 真实 API 已跑通

状态：

- 已收敛

### 11. 标准化 JSON 输出

当前能力：

- 关键脚本统一返回 JSON envelope
- 支持自动化与后续集成

状态：

- 已收敛

### 12. README 与 MVP 主路径

当前能力：

- README 已按当前 MVP 重写
- pre-trade -> post-trade -> history -> review 主链路已手动验证

状态：

- 已收敛

## 三、当前版本部分收敛，但后面还能增强的能力

这些功能已经有最小实现，但还没有到“完全不动”的程度。

### 1. AI review abstraction

当前状态：

- 已有 [scripts/ai_client.py](/C:/Users/10041/Desktop/no-fomo/scripts/ai_client.py)
- 已同时支持 pre-trade / post-trade review

还可以继续补：

- 更统一的 review schema
- 更清晰的 prompt 管理
- 更强的 provider error handling

状态：

- 部分收敛

### 2. 奖励机制

当前状态：

- 已收敛到 `encouragement` 一句话
- 已明确只奖励纪律与过程

还可以继续补：

- `discipline_progress`
- `behavior_risk_note`
- 周报中的纪律反馈层

状态：

- 部分收敛

## 四、还没有开始或还没有收敛的能力

这些功能仍然是 roadmap 上的后续方向，不属于当前已完成的 MVP。

### 1. Active trade review

目标：

- 在用户已经持仓时介入
- 帮助用户识别加仓、扛单、反手、恐慌操作是否是情绪驱动

建议脚本：

- `active_trade_review.py`

状态：

- 未开始

这是当前最值得补的下一核心功能。

### 2. AI 周期总结

目标：

- 在 `weekly_review` 之上增加 AI coach 层
- 把统计结果变成行为层面的建议

状态：

- 未开始

### 3. Open position 手动录入

目标：

- 让未平仓仓位也能进入 review 流程

状态：

- 未开始

### 4. Binance open position sync

目标：

- 自动拉取当前 open positions

状态：

- 未开始

### 5. 结构化 thesis 输入模板

目标：

- 提高用户输入质量
- 提高 AI 审核质量

状态：

- 未开始

### 6. 轻量 UI

候选形式：

- TUI
- 小型 web form
- 轻量 dashboard

状态：

- 未开始

### 7. 多交易所输入源

候选：

- OKX
- HTX
- Gate
- Hyperliquid

当前判断：

- 现在不作为优先项
- 先把 Binance 路径打磨稳定
- 再抽象统一 exchange import interface

状态：

- 战略上已收敛优先级
- 实施上未开始

## 五、当前推荐的开发顺序

### Phase 1：当前 MVP 收口

目标：

- 形成可运行、可验证、可发布的 CLI MVP

当前状态：

- 已完成

### Phase 2：AI 核心层

目标：

- 把项目从规则工具升级为 AI 决策辅助系统

当前状态：

- 基本完成

已完成项：

- `ai_client.py`
- pre-trade AI review
- post-trade AI review
- AI provider config
- AI history

未完成项：

- active trade review

### Phase 3：行为教练层

目标：

- 从单次判断升级为长期行为改进系统

当前状态：

- 未开始

### Phase 4：易用性与展示层

目标：

- 降低 CLI 使用门槛
- 提高展示效果

当前状态：

- 未开始

## 六、当前最值得做的下一步

如果只选一个下一步，我建议：

### `active_trade_review.py`

原因：

- 这最符合 No-FOMO 的产品定位
- 也是当前闭环里唯一明显缺失的一段
- 它能把项目从“开仓前 + 平仓后”补成真正的“交易中介入”

## 七、当前版本的最终判断

现在的 `No-FOMO` 可以被清晰定义为：

**一个已经跑通、并完成手动验证的 AI trading discipline MVP。**

它已经具备：

- 开仓前 AI 审核
- 平仓后 AI 复盘
- AI 历史回看
- 冲动交易分析
- 周期复盘
- Binance 已结束交易导入

它还不具备：

- 持仓中即时介入
- open position sync
- 轻量 UI
- 多交易所统一输入层
- 长期 AI coach 层

## 八、奖励机制原则

当前已经确认的原则：

- 奖励高质量决策
- 奖励纪律执行
- 奖励及时止损
- 奖励完整复盘
- 不奖励单笔盈利本身

当前最小实现：

- `encouragement`

后续可扩展方向：

- `discipline_progress`
- `behavior_risk_note`
- AI weekly coach feedback
