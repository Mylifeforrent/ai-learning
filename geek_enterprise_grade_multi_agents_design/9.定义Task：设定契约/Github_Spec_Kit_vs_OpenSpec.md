# 规范驱动开发 (SDD)：GitHub Spec Kit vs OpenSpec

在 AI 辅助编程时代，从口头指令（Vibe Coding）转向明确的契约和规范（Spec-Driven Development, SDD）已经成为开发复杂应用的核心范式。你提供的第三方总结非常精准：**未来的最佳实践不是 SDD+TDD 的简单叠加，而是 SDD 作为唯一真理源（Single Source of Truth）。**

目前在规范驱动开发领域，**GitHub Spec Kit** 和 **OpenSpec** 是两个最具代表性的开源框架/工具。

## 1. GitHub Spec Kit 与 OpenSpec 的核心区别

| 维度 | OpenSpec (openspec.dev) | GitHub Spec Kit |
| --- | --- | --- |
| **核心定位** | 轻量级的、基于 Markdown 的规范文档标准和工作流框架。 | 一套开源的工具链、模板库和 CLI，旨在将 SDD 流程化。 |
| **实现方式** | 在项目中建立 `openspec/` 目录存放 `specs/` (规范) 和 `changes/` (变更)。主张极简的 Markdown 格式。 | 提供 CLI 工具创建工作空间，自带大量的 Prompt 模板和宪章（Constitution）设置。 |
| **工作流阶段** | **Proposal (提议)** -> **Apply (应用)** -> **Archive (归档)**。支持通过 Spec Deltas 追踪需求变更。 | 四阶段门控：**Specify (定义)** -> **Plan (计划)** -> **Tasks (任务拆解)** -> **Implement (实现)**。 |
| **工具集成** | 极具包容性，深入集成主流 Agent IDE（如 Cursor, Windsurf, Claude Code），常常可以直接作为 Slash Command 调用。 | 偏向于 GitHub 生态（如 Copilot），但也声明是 Agent-Agnostic（代理无关）的。提供更强的模板化支持。 |
| **适用场景** | 敏捷开发、中小型团队、甚至现有旧代码仓库（Brownfield）的轻量级迭代。 | 企业级开发、需要严格流程控制和架构评审的大型项目。 |

## 2. 目前主流方式是哪种？

**结论：** 严格意义上说，**OpenSpec 的“思想与范式”更加主流且更受一线开发者欢迎**。

由于当前开发者高度依赖 Cursor、Windsurf 等 Agentic IDE，OpenSpec 所提倡的 **“轻量级 Markdown 规范 + Agent 直接读取执行”** 完美契合了当下的开发习惯。GitHub Spec Kit 则略显重度，更适合有严格工程生命周期标准的大型组织。

无论是使用哪个工具，**主流的核心思想只有一个**：**彻底摒弃将需求写在对话框里（Vibe Coding），要求所有设计转化为结构化 Markdown 文件，将其作为 Task 的刚性契约，让 AI 严格按照契约去实现、测试和交付。**

---

## 3. 具体操作步骤与实践案例（基于 Agentic IDE 的 SDD 范式）

以下是一个基于目前主流 Agent IDE (如 Cursor / Windsurf / CodeFlicker) 的 SDD 实施标准操作流程（SOP）。

### 步骤 1：建立规范文档 (Proposal) - 明确契约
停止直接在 AI 聊天框里下达开发指令。
改为在项目目录下创建一个规范文档（例如 `docs/specs/user_auth_feature.md`），明确你的核心要求。

```markdown
# 规范：用户登录与鉴权模块

## 1. 目标
实现一个基于 JWT 的用户登录模块，包括用户无感知的登录态保持机制。

## 2. 验收标准 (Acceptance Criteria) - *非常重要：交给 AI 的核对单*
- [ ] 必须复用现有的基础组件库 `@/components/ui/button`。
- [ ] 密码必须使用 `bcrypt` 依赖包进行加密存储。
- [ ] 登录失败需返回清晰的 401 状态码，并附带错误字典中的 "ERR_INVALID_CREDENTIALS"。
- [ ] 成功登录后，Token 需存储在 HttpOnly Cookie 中，且前端不得直接操作。

## 3. 测试策略
- Agent 需使用 Jest 编写自动化测试，验证 “密码错误机制” 和 “Token 存储安全性”。
- 在提交 PR 前，要求测试通过率达到 100%。
```

### 步骤 2：引入 Agent 工作流，执行契约 (Apply)
在 IDE 的 Agent 对话框（如 Cursor Composer 模式）中，将刚写好的规范文档作为唯一输入源喂给大模型：

**Agent Prompt 实践建议:**
> 引用文件：`@docs/specs/user_auth_feature.md`
> 
> "请读取上方的规范文档。这是我们此次 Task 的契约。
> 1. 请严格按照文档中的 `验收标准` 进行“规划”和“编码”。
> 2. 第一步：先向我输出你的 Technical Plan（涉及修改哪些文件），等我回复“OK”再开始写代码。
> 3. 第二步：编码完成并自查后，根据 `测试策略` 自动生成由于测试用例，并执行 `npm run test`。
> 4. 如果遇到测试报错，请自行修复，直到满足契约的验收标准。"

### 步骤 3：AI 自我修复与验收闭环
Agent 生成代码 -> 自动跑测试 -> 测试终端报警 -> **Agent 自我审查并修复代码** -> 重新测试直到绿灯。
此时，AI 不再是一个“高级代码补全器”，而是一个**能够遵守契约独立完成交付的协作者**。

### 步骤 4：规范一致性检查 (CI/CD 防腐)
在企业级流水线中，接入轻量级大模型（如 GPT-4o-mini 或 Claude-3-Haiku）作为 CI Reviewer。在提交代码合入主干前，系统自动将 `PR 变更代码` 和对应的 `user_auth_feature.md` 结合进行一致性打分：
> “根据 Spec 的契约要求，该段代码是否有使用纯文本存储密码等违背契约的行为？如果有，直接 Block 合并申请。”
此举能彻底防范 AI 产生的代码“架构飘移”。

---

## 4. 落地到你的项目架构中

在《企业级多智能体设计》的【9.定义Task：设定契约】环节中，你可以总结出三大原则：
1. **口头不接单：** 任何多 Agent 协作工作流中的 Task，不接受口语化的自然语言调度，所有的上下文必须封装成具备约束力的 Markdown（如 `xxx_spec.md`）。
2. **测试转标准：** 将手动编写繁琐的单元测试的时间，转化为编写精准语义的 `Acceptance Criteria (AC)`，让执行端 Agent 基于 AC 倒推用例去自动防御问题。
3. **架构防腐与对齐：** 将全局技术宪章（Technology Constitution）加入 Agent 的系统提示词中，充当所有 Task 契约的基础底色，实现代码在微观（功能）与宏观（规范）上的一致。
