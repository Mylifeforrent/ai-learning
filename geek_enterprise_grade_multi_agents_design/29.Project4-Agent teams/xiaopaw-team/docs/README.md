# docs/

xiaopaw-team 设计文档目录。

## 主文档

- **[DESIGN.md](./DESIGN.md)** — **v1.2 综合版**（17/22 基础 + 29 团队扩展）。唯一权威设计文档，完整构建本项目所需的全部设计。
- **[test-design.md](./test-design.md)** — **测试设计文档 v1.0**（2004 行）。风险分析 / 测试点 / 可测性评估 / 自动化方案 / 功能 case / E2E Journey / 数据工厂。与 DESIGN.md 配套使用。

## 基础模块详设（继承 17/22 课，与 DESIGN.md 配合使用）

- [design-modules.md](./design-modules.md) — 基础模块内部实现（FeishuListener / Runner / Main Agent / SkillLoaderTool / Sub-Crew / CronService / CleanupService / memory 子系统）
- [design-data.md](./design-data.md) — 数据格式详设（InboundMessage / session / trace / SKILL.md / memories 表等）
- [design-api.md](./design-api.md) — 飞书接口详设（WebSocket 事件 / REST 消息接口 / 文件下载）
- [design-observability.md](./design-observability.md) — 日志规范 + Prometheus 指标

**阅读顺序**：先读 DESIGN.md 理解整体架构和团队层设计；如需 22 课基础组件的内部细节，查 design-modules.md 等子文档。

## 历史版本

- [history/v0.2-architecture.md](./history/v0.2-architecture.md) — v0.2 架构草稿
- [history/v0.3-detailed-flow.md](./history/v0.3-detailed-flow.md) — v0.3 详细流程剧本
- [history/v1.1-team-only.md](./history/v1.1-team-only.md) — v1.1 团队层专版（未含 17/22 基础，被当前 DESIGN.md 取代）

## 文档职责约定

- **DESIGN.md 是唯一需要维护的主设计文档**。任何架构 / Skill / Tool / 流程的变更都写进它
- 基础模块详设（design-*.md）继承自 xiaopaw-with-memory（22 课），保持同步即可；本课不新增详设文档
- 代码实现时如发现设计与代码不一致，**先改 DESIGN.md 达成共识**再改代码
- 每次重大版本升级，旧版本整体归 history/ 并在 DESIGN.md 附录 F 记录变更
