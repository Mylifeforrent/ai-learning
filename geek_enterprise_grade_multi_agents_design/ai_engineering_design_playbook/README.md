# AI Engineering Design Playbook

这套文档从 `geek_enterprise_grade_multi_agents_design` 课程目录与阶段项目中提炼一套可迁移、可复用的 AI 工程设计方法论。它不是课程笔记的复制，而是把课程小节、demo、综合项目和工程化加固实践整理成未来做企业级 AI 项目时可直接参考的设计框架。

## 适用场景

适合以下类型的项目：

| 场景 | 适用方式 |
| --- | --- |
| 从 0 到 1 搭建 AI 应用 | 按 `03_ai_engineering_design_methodology.md` 逐层设计需求、Agent、工具、工作流和测试 |
| 把 demo 推进到工程项目 | 参考 `02_project_evolution_path.md` 中 Project 1 到 Project 5 的能力演进 |
| 设计 Multi-Agent 或 Agent Team | 参考 `04_reusable_project_template.md` 与 `06_agent_long_term_reference.md` 中的角色、协议、工作区模板 |
| 引入长期记忆与 Harness | 参考 `05_harness_engineering_practices.md` 中的 Bootstrap、上下文生命周期、文件记忆和搜索记忆 |
| 做生产级加固 | 参考 Hook、Guardrails、Observability、Eval、CI/CD、Monitoring、Data Flywheel 的分层实践 |

## 文档结构

| 文档 | 解决的问题 |
| --- | --- |
| `01_knowledge_map.md` | 课程小节、demo、核心知识点、阶段项目之间如何对应 |
| `02_project_evolution_path.md` | 五个阶段性综合项目如何逐步演进 |
| `03_ai_engineering_design_methodology.md` | 企业级 AI 项目的通用设计方法论 |
| `04_reusable_project_template.md` | 可复用的项目目录、模块职责、命名和配置模板 |
| `05_harness_engineering_practices.md` | Harness 工程化实践，包含上下文、记忆、Hook、测试、CI/CD、监控 |
| `06_agent_long_term_reference.md` | 给未来 AI Agent 长期参考的规则、模板和检查清单 |
| `07_reference_selection_guide.md` | 告诉未来 AI 不同项目应追加参考哪些综合项目和 demo，避免实现风格跑偏 |

## 推荐阅读顺序

1. 先读 `01_knowledge_map.md`，理解课程知识体系和 demo 对应关系。
2. 再读 `02_project_evolution_path.md`，理解从小红书项目到 XiaoPaw v2 的工程演进。
3. 如果要启动新项目，读 `03_ai_engineering_design_methodology.md` 和 `04_reusable_project_template.md`。
4. 如果要提升已有项目的稳定性，读 `05_harness_engineering_practices.md`。
5. 如果要让 AI Agent 复用这套经验，读 `06_agent_long_term_reference.md`，并把其中的规则作为项目初始化参考。
6. 如果要让实现更贴近课程体系，读 `07_reference_selection_guide.md`，按项目类型追加 Project 1-5 或对应 `crewai_mas_demo` 小节作为 canonical reference。

## 方法论总览

这套课程背后存在一条清晰路径：

```text
范式选择
  -> Agent / Task / Process 基础建模
  -> Tool / MCP / Skills 能力扩展
  -> Harness 管理上下文、工作区和执行环境
  -> Memory / RAG / Skill 沉淀长期经验
  -> Orchestrator / Agent Teams 扩展协作复杂度
  -> Hook / Guardrails / Observability 做生产加固
  -> Eval / CI/CD / Monitoring / Data Flywheel 做持续演进
```

其中最重要的工程判断是：

| 判断 | 含义 |
| --- | --- |
| 先契约，后智能 | 用 Pydantic、Task expected output、测试用例约束 AI 输出 |
| 先工作流，后自治 | 先跑通可解释流程，再把不确定部分交给 Agent |
| 先工具边界，后工具数量 | 工具语义要完整、I/O 要瘦、错误要可恢复 |
| 先上下文治理，后长期记忆 | 没有 prune、compress、Bootstrap 的系统不适合盲目上 RAG |
| 先单 Agent，后团队 | 有明确瓶颈和收益后再拆角色、邮箱、共享区和事件流 |
| 先 Hook 骨架，后策略叠加 | 观测、可靠性、安全都应挂在统一事件体系上 |
| 先评测闭环，后规模化 | 没有 Eval、监控和数据飞轮，系统只会停留在上线当天 |

## 主要证据来源

本 playbook 主要依据以下内容整理：

| 类型 | 代表路径 |
| --- | --- |
| 全局课程大纲 | `README.md` |
| 课程笔记 | `1.intoduction/notes.md` 到 `40.Organizational Evolution.../note.md` |
| 横向 demo | `crewai_mas_demo/README.md`、`crewai_mas_demo/m*/README.md`、核心 `.py` |
| Project 1 | `11.项目实战一：小红书爆款笔记/crewai_mas_demo_m2l7/` |
| Project 2 | `17.Project2-Xiaopaw-feishu-assistant/xiaopaw/` |
| Project 3 | `22.Project3-Xiaopaw-with-memory/xiaopaw-with-memory/` |
| Project 4 | `29.Project4-Agent teams/xiaopaw-team/` |
| Project 5 | `33.Project5-xiaopaw with security enhancement/xiaopaw-v2/` |

## 使用方式

未来启动一个新的企业级 AI 项目时，可以按下面顺序复用：

1. 用 `03` 的场景评估方法判断是否值得做 AI。
2. 用 `04` 的目录模板初始化项目骨架。
3. 用 `06` 的 Agent 参考规则写 `agents.yaml`、`tasks.yaml`、`workspace-init/*.md`。
4. 用 `05` 的 Harness 实践接入 Session、Workspace、Memory、Hook、Eval 和 CI/CD。
5. 用 `02` 的演进路径判断当前项目处于哪个阶段，以及下一阶段该增强什么能力。
6. 用 `07` 选择 1-3 个综合项目或少量 demo 作为实现风格参考。
