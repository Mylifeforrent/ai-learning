# 交互架构设计

## 课件信息
- 课程：Agent 上下文管理系统 -- Context Engineering 完整指南
- 总页数：31
- 交互分布：绿色 5 页 / 黄色 24 页 / 红色 2 页

## 交互级别定义
- 绿色（static）：纯展示，无需用户交互，CSS 入场动画即可
- 黄色（light）：卡片展开、hover 效果、tab 切换、简单 GSAP 动画
- 红色（heavy）：状态机驱动的复杂交互，多步展开，需要 hookFn

## 逐页交互设计

### 第一章：认知升维（7页）

| Slide | 文件名 | 标题 | 级别 | 交互类型 | 说明 |
|-------|--------|------|------|---------|------|
| S001 | S001-cover.html | 封面 | 绿色 | fade-in | 标题+副标题+课程信息渐入，背景柔和渐变 |
| S002 | S002-supply-demand.html | 供需模型升维 | 黄色 | flip-cards | 供给侧/消费侧双卡片翻转对比，底部三层递进模型横向排列 |
| S003 | S003-context-rot.html | Context Rot 现象 | 黄色 | progressive-reveal | 渐显动画：先展示"窗口越大越好？"，点击后揭示腐化数据 |
| S004 | S004-effective-window.html | 有效窗口 vs 宣传窗口 | 黄色 | data-highlight | RULER 数据表，hover 行高亮，关键数据（50-65%）脉冲强调 |
| S005 | S005-model-comparison.html | 模型有效窗口对比 | 黄色 | bar-chart-anim | 四个模型柱状图从 0 动画增长，宣传窗口 vs 有效窗口双柱对比 |
| S006 | S006-compression-trigger.html | 压缩启动点 | 黄色 | water-level | 鱼缸水位动画：水位从 0% 升到 100%，80% 处红线闪烁提示"启动压缩" |
| S007 | S007-ch1-summary.html | 第一章小结 | 绿色 | fade-in | 三个要点卡片依次入场，过渡到第二章预告 |

### 第二章：六大功能模块（10页）

| Slide | 文件名 | 标题 | 级别 | 交互类型 | 说明 |
|-------|--------|------|------|---------|------|
| S008 | S008-six-modules.html | 六模块全景图 | 红色 | module-explorer | 中心鱼缸图 + 六根管道，点击任意管道展开对应模块卡片（名称/隐喻/核心问题/token占比），已展开模块高亮保持，全部展开后显示完整占比饼图 |
| S009 | S009-system-prompt.html | 系统提示层 | 黄色 | layer-stack | 6层拼接可视化：垂直堆叠的6个色块，点击每层展开详情（文件名+内容概述+token估算） |
| S010 | S010-conversation-history.html | 对话历史管理层 | 黄色 | strategy-tabs | 三个策略tab（截断/压缩/摘要），切换展示机制+代码片段+优缺点 |
| S011 | S011-memory-injection.html | 记忆检索注入层 | 黄色 | type-cards | 四类型分组卡片（user/feedback/project/reference），点击展开示例内容和检索流程 |
| S012 | S012-tool-context.html | 工具上下文管理层 | 黄色 | density-scale | 工具密集度分级滑块：拖动或点击切换 <10 / 10-30 / 30-100 / 100+ 四档，展示对应管理策略 |
| S013 | S013-task-state.html | 任务状态层 | 黄色 | before-after | Scratchpad 前后对比：左侧"无 Scratchpad 压缩后断片"，右侧"有 Scratchpad 完整回忆"，hover 高亮差异 |
| S014 | S014-external-knowledge.html | 外部知识层 | 黄色 | compare-table | RAG vs 全上下文对比表，hover 行高亮，底部结论卡片 |
| S015 | S015-token-budget.html | Token 预算分配 | 黄色 | donut-chart | 环形图展示六模块 token 占比，hover 各段弹出详情tooltip |
| S016 | S016-module-interaction.html | 模块间协作与冲突 | 黄色 | connection-anim | 六模块节点图，依次高亮协作连线和冲突连线（四种失败模式标注） |
| S017 | S017-ch2-summary.html | 第二章小结 | 绿色 | fade-in | 六模块快速回顾卡片 + 过渡到第三章 |

### 第三章：五策略框架（8页）

| Slide | 文件名 | 标题 | 级别 | 交互类型 | 说明 |
|-------|--------|------|------|---------|------|
| S018 | S018-five-strategies.html | 五策略全景图 | 红色 | strategy-explorer | 五个策略圆形/五边形布局，点击展开每个策略卡片（机制/实现/场景/优先级），已展开保持高亮，全部展开后显示决策优先级排序动画 |
| S019 | S019-write.html | Write 策略 | 黄色 | expand-card | Scratchpad/文件系统/数据库三种实现，点击展开代码示例和适用场景 |
| S020 | S020-select.html | Select 策略 | 黄色 | flow-diagram | RAG 检索流程动画：query → embedding → 向量搜索 → top-k → 注入，逐步高亮 |
| S021 | S021-compress.html | Compress 策略 | 黄色 | triple-compare | 三种压缩技术并排对比（工具清除/观察遮蔽/LLM摘要），hover 高亮差异维度 |
| S022 | S022-isolate.html | Isolate 策略 | 黄色 | arch-diagram | 子 Agent 架构图：主 Agent 分发任务到子 Agent，各自维护独立窗口 |
| S023 | S023-cache.html | Cache 策略 | 黄色 | cost-anim | Prompt Caching 成本对比动画：无缓存 vs 有缓存的月度成本柱状图，差额高亮 |
| S024 | S024-strategy-combo.html | 策略组合实战 | 黄色 | matrix-hover | 五策略×六模块交叉矩阵表，hover 单元格高亮行列+弹出详情 tooltip |
| S025 | S025-ch3-summary.html | 第三章小结 | 绿色 | fade-in | 五策略优先级排序回顾 + 过渡到第四章 |

### 第四章：决策内化（6页）

| Slide | 文件名 | 标题 | 级别 | 交互类型 | 说明 |
|-------|--------|------|------|---------|------|
| S026 | S026-rag-vs-long.html | RAG vs 长上下文选型 | 黄色 | decision-table | 七类场景策略匹配表，hover 行高亮，底部快速选型提示 |
| S027 | S027-token-economics.html | Token 经济学 | 黄色 | cost-highlight | 成本对比表（1万/10万/100万对话），关键数据脉冲强调，hover 显示节省百分比 |
| S028 | S028-caching-cost.html | Prompt Caching 成本优化 | 黄色 | stage-progress | 六阶段递进条：从 Stage 0 到 Stage 5 逐步点亮，每步展示策略+节省比例 |
| S029 | S029-checklist.html | 生产级 Checklist | 黄色 | checkbox-list | 可勾选清单，勾选后进度条更新，全部勾选触发完成动画 |
| S030 | S030-knowledge-map.html | 全课知识图谱 | 黄色 | knowledge-graph | 概念节点图（Context Rot → 六模块 → 五策略），hover 节点高亮关联边，点击节点弹出概念摘要 |
| S031 | S031-ending.html | 结束页 | 绿色 | fade-in | 能力自检清单 + 下节预告 + 感谢 |

## 红色页面详细状态机

### S008 六模块全景图

```
状态机：
  idle → module_1_open → module_2_open → ... → all_open → summary

交互逻辑：
  1. 初始展示鱼缸中心图 + 六根管道标签
  2. 点击任意管道 → 展开对应模块详情卡片（从管道方向滑入）
  3. 卡片内容：模块名 / 隐喻 / 核心问题 / 典型 token 占比
  4. 已展开模块管道保持高亮色
  5. 全部六个模块展开后 → 底部出现 token 占比饼图 + 总结文案
  6. 支持折叠已展开模块（再次点击）

元素清单：
  - 中心鱼缸 SVG（简化示意，不需要精细绘制）
  - 6个管道标签按钮
  - 6个详情卡片（毛玻璃卡片样式）
  - 1个饼图（CSS 或简单 SVG）
  - 总结文案区
```

### S018 五策略全景图

```
状态机：
  idle → strategy_1_open → ... → all_open → priority_reveal

交互逻辑：
  1. 初始展示五个策略圆形/卡片环形排列
  2. 点击策略 → 展开详情卡片（机制 / 典型实现 / 适用场景）
  3. 已展开策略保持高亮
  4. 全部五个策略展开后 → 中心区域出现决策优先级排序
     Cache(1) → Compress工具清除(2) → Compress遮蔽/trim(3) → Isolate(4) → Write+Select(5)
  5. 优先级排序有动画（从1到5逐步点亮）

元素清单：
  - 5个策略卡片（环形布局）
  - 5个详情展开区域
  - 中心优先级排序图
  - 动画序列
```

## hookFn 需求

仅红色页面需要 hookFn：
- S008: hookFn 管理六模块展开状态，绑定点击事件，控制饼图出现时机
- S018: hookFn 管理五策略展开状态，绑定点击事件，控制优先级动画触发

黄色页面的交互通过 CSS :hover / :active + 简单 JS（data-* 属性驱动的 tab 切换、GSAP ScrollTrigger 入场动画）实现，不需要复杂 hookFn。
