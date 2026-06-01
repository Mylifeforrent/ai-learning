# 01. Knowledge Map

本文件把课程小节、`crewai_mas_demo` 目录、核心知识点和综合项目之间的关系整理成迁移地图。由于课程目录与 demo 命名存在少量历史编号差异，本表以实际目录名和 `crewai_mas_demo` README 中的课程说明作为依据。

## 课程主线地图

| 小节 / 目录 | 核心知识点 | 对应 demo | 被哪个综合项目使用 | 作用 |
| --- | --- | --- | --- | --- |
| `1.intoduction` | Skills 机制、渐进式上下文披露、经验复用 | 无独立 demo | Project 2-5 | 为后续 Skills 生态和长期参考奠基 |
| `2.AI_Application_Design_Pattern` | Prompt、Workflow、Single Agent、Multi-Agent 四类范式 | 无独立 demo | 全部项目 | 判断项目应该用哪种 AI 架构 |
| `3.Agent_Mechanism` | ReAct、Tool Calling、消息累积、上下文污染、框架底层交互 | `crewai_mas_demo/m1l2` | 全部项目 | 理解 Agent Loop 与工具调用本质 |
| `4.multi-agent：agent、task、process 协作美学` | Agent / Task / Process 协作、上下文隔离、文件传书 | `crewai_mas_demo/m1l3` | Project 1、Project 4 | 从单 Agent 进入 Multi-Agent 协作 |
| `5.AI应用开发工具选型` | C.U.P. 模型、复杂度、不确定性、性能约束 | 无独立 demo | 全部项目 | 判断是否用 CrewAI、Workflow 或普通代码 |
| `6.工程全景图-构建企业级施工蓝图` | Ready、MVP、Tools、Context、Collaboration、Stability 五级路线 | 无独立 demo | 全部项目 | 提供整体演进蓝图 |
| `7.基础代码环境准备` | LLM 接口、模型参数、成本与超时 | `crewai_mas_demo/m2l2`、`llm/aliyun_llm.py` | 全部项目 | 统一模型接入基础 |
| `8.定义Agent：人设设定` | Agent RGB 模型，Role / Goal / Backstory | `crewai_mas_demo/m2l3` | Project 1-5 | Agent 角色设计模板 |
| `9.定义Task：设定契约` | Task 契约、Pydantic 输出、验收标准 | `crewai_mas_demo/m2l4` | Project 1-5 | 把自然语言任务变成可验收接口 |
| `10.多模态模型` | AddImageTool、本地图片注入、多模态消息归一化 | `crewai_mas_demo/m2l6` | Project 1、Project 2-3 的文件/图片能力 | 支撑图像分析与多模态任务 |
| `11.项目实战一：小红书爆款笔记` | 5 Agent、7 Task、三阶段 Flow、FastAPI 工程化 | `crewai_mas_demo/m2l7`、项目内 `crewai_mas_demo_m2l7` | Project 1 | 第一个端到端 AI 工程样板 |
| `12.工具设计哲学: 从API到Agent-Native范式迁跃` | Function Calling vs ReAct、Agent-Native Tool、Hook 拦截 | `crewai_mas_demo/m2l8` | Project 2-5 | 工具从 API 变成 Agent 可用能力 |
| `13.自定义工具封装：构建Tools的五步标准` | 语义完整性、I/O 瘦身、错误提示、工具描述、参数描述 | `crewai_mas_demo/tools/*` | Project 1-5 | 工具设计规范 |
| `14.MCP协议：标准化定义工具接口` | FastAPI MCP Server、Streamable HTTP、工具过滤、密钥隔离 | `crewai_mas_demo/m2l9`、`fastapi_mcpserver_base` | Project 2-5 | 标准化工具生态与沙盒工具接口 |
| `15.王牌超能力：代码解释器和无头浏览器` | AIO-Sandbox、代码解释器、浏览器自动化、执行隔离 | `crewai_mas_demo/m2l10` | Project 2-5 | 让 Agent 具备真实执行能力 |
| `16.Skills生态：让Agent接入大量工具` | SKILL.md、SkillLoaderTool、reference / task skill、Sub-Crew | `crewai_mas_demo/m2l16`、`skills/*` | Project 2-5 | 构成 XiaoPaw 能力扩展核心 |
| `17.Project2-Xiaopaw-feishu-assistant` | 飞书 WebSocket、Runner、Session、Skills、Sandbox、Cron | `crewai_mas_demo/m2l17` | Project 2 | 从课程 demo 变成工作助手框架 |
| `18.从Prompt到Harness：记忆与上下文的设计范式` | Prompt Engineering、Context Engineering、Harness Engineering | 无独立 demo | Project 3-5 | 方法论从提示词转向工程外壳 |
| `19.Context Lifecysle Management-Bootstrap,cut and compress` | Bootstrap、剪枝、压缩、ctx/raw 持久化、before_llm_call | `crewai_mas_demo/m3l19` | Project 3-5 | 上下文生命周期管理 |
| `20.FilesystemMemory-Agent manage memory and learn skills` | memory-save、skill-creator、文件系统记忆、记忆 GC | `crewai_mas_demo/m3l20` | Project 3-5 | 语义记忆和程序记忆写通道 |
| `21.Memory system-enterperprise level memory management` | pgvector、混合检索、chunk、索引流水线、search_memory | `crewai_mas_demo/m3l21` | Project 3-5 | 长期可检索记忆 |
| `22.Project3-Xiaopaw-with-memory` | 三层记忆、Bootstrap 四件套、MemoryAwareCrew、异步索引 | `crewai_mas_demo/m2l22` | Project 3 | XiaoPaw 进入长记忆阶段 |
| `23.Orchestrator-Master Agent and SubAgent` | Master Agent + SubAgent、委派、独立 Crew、结果传路径 | `crewai_mas_demo/m4l23` | Project 4 | 从单助手扩展为任务小队 |
| `24.From Task List to Digital Teams` | Harness 升级、Soul + Skill + Memory、数字员工概念 | 无独立核心 demo | Project 4 | 从任务编排转向组织建模 |
| `25.Team Role: role based action institutions` | 角色制度、行为规范、role-scoped workspace | `crewai_mas_demo/m4l25` | Project 4 | 定义 Manager、PM、RD、QA 等角色 |
| `26.Information exchange between digital staff` | 共享工作区、邮箱、文件锁、三态消息状态机 | `crewai_mas_demo/m4l26` | Project 4 | Agent Team 的协作协议 |
| `27.Human as boss: How to design the checkpoint in agent teams` | HITL、人类确认节点、单一接口原则、Human CLI | `crewai_mas_demo/m4l27` | Project 4 | 让人类位于循环之上做风险控制 |
| `28.Self Evolvement` | 三层日志、复盘、proposal、分档审批、自我进化 | `crewai_mas_demo/m4l28` | Project 4 | 让团队基于运行数据改进 |
| `29.Project4-Agent teams` | Manager + PM + RD + QA、邮箱、共享区、事件流、团队复盘 | `crewai_mas_demo/m4l29`、项目 `xiaopaw-team` | Project 4 | Agent Teams 综合项目 |
| `30.Observability-Langfuse` | 5+2 事件、HookRegistry、HookLoader、Langfuse trace | `crewai_mas_demo/m5l30` | Project 5 | 统一可观测骨架 |
| `31.Reliability-retry,loop control and cost guardrails` | retry、loop detector、cost guard、dispatch_gate | `crewai_mas_demo/m5l31` | Project 5 | 可靠性策略层 |
| `32.sandbox,authentication gateway and identification` | SandboxGuard、PermissionGate、凭证注入、审计日志 | `crewai_mas_demo/m5l32` | Project 5 | 安全策略层 |
| `33.Project5-xiaopaw with security enhancement` | XiaoPaw v2/v3、Hook 加固、SSOT、E2E、生产安全 | `xiaopaw-v2` | Project 5 | 生产加固综合项目 |
| `34.How to evaluate scenario with high ROI` | 需求挖掘、AI 适用性评估、ROI 判断 | 无独立 demo | 新项目立项 | 决定是否值得做 AI 项目 |
| `35.Prototype-requirement to evaluable demo` | Who / What / How good、原型、Ground Truth | 无独立 demo | 新项目原型阶段 | 从需求变成可评测 demo |
| `36.Quality assessment-make your AI can be evaluated` | Eval case、执行、打分、汇总、bad case 分析 | 无独立 demo | Project 5、新项目 | 建立 AI 系统测试评估闭环 |
| `37.CICD-evolve continously` | AI CI/CD、版本快照、静态规则、回归、成本、安全 gate | 无独立 demo | Project 5、新项目 | 持续交付和知识库自动更新 |
| `38.Monitoring-know how your ai is working` | 六层监控、成本、Agent 执行、质量、业务、安全合规 | 无独立 demo | Project 5、新项目 | 上线后的运营监控 |
| `39.Data Flywheel-evolve your system with online data` | 显式/隐式信号、错误分析、迭代飞轮 | 无独立 demo | 新项目长期运营 | 让线上数据驱动持续改进 |
| `40.Organizational Evolution...` | AI 原生组织、试点、推广、角色能力跃迁 | 无独立 demo | 企业落地 | 把单项目经验复制到组织层 |

## demo 目录速查

| demo | 主题 | 关键文件 | 迁移价值 |
| --- | --- | --- | --- |
| `crewai_mas_demo/m1l2` | ReAct 与 CrewAI Agent 对比 | `m1l2_raw_agent.py`、`m1l2_agent.py` | 理解 Agent Loop 原理 |
| `crewai_mas_demo/m1l3` | Multi-Agent 协作 | `m1l3_multi_agent.py` | 学习 Agent、Task、Process 的协作形态 |
| `crewai_mas_demo/m2l2` | LLM 配置 | `m2l2_llm_openai.py`、`llm/aliyun_llm.py` | 建立可替换模型层 |
| `crewai_mas_demo/m2l3` | Agent 人设 | `m2l3_agent.py` | 练习 RGB 模型 |
| `crewai_mas_demo/m2l4` | Task 契约 | `m2l4_task.py` | Pydantic 输出契约 |
| `crewai_mas_demo/m2l5` | Process 编排 | `m2l5_crew.py` | Sequential Process 和 context 链 |
| `crewai_mas_demo/m2l6` | 多模态 | `m2l6_agent.py`、`tools/add_image_tool_local.py` | 图片路径注入和消息归一化 |
| `crewai_mas_demo/m2l8` | Tool Hook 与多租户上下文 | `m2l8_context.py`、`m2l8_tools_call.py` | 路径重定向、请求上下文、安全拦截 |
| `crewai_mas_demo/m2l9` | MCP 集成 | `m2l9_mcp.py` | 把 MCP Server 工具接入 Agent |
| `crewai_mas_demo/m2l10` | AIO-Sandbox | `m2l10_sandbox.py` | 代码解释器和浏览器能力 |
| `crewai_mas_demo/m2l16` | Skills 生态 | `m2l16_skills.py`、`skills/load_skills.yaml` | SkillLoaderTool + Sub-Crew 工厂 |
| `crewai_mas_demo/m2l17` | Project 2 指引 | `readme.md` | XiaoPaw 工具篇阅读路线 |
| `crewai_mas_demo/m2l22` | Project 3 指引 | `readme.md` | 三层记忆系统阅读路线 |
| `crewai_mas_demo/m3l19` | 上下文生命周期 | `m3l19_context_mgmt.py` | Bootstrap、prune、compress、session |
| `crewai_mas_demo/m3l20` | 文件记忆 | `m3l20_file_memory.py`、`workspace/*.md` | memory-save、skill-creator、memory-governance |
| `crewai_mas_demo/m3l21` | 搜索记忆 | `indexer.py`、`m3l21_search_memory.py` | pgvector、异步索引、混合检索 |
| `crewai_mas_demo/m4l23` | Orchestrator | `m4l23_orchestrator.py` | 主 Agent 委派子 Agent |
| `crewai_mas_demo/m4l25` | 团队角色 | `run_manager.py`、`run_dev.py` | 角色工作区和团队分工 |
| `crewai_mas_demo/m4l26` | 信息交换 | `tools/mailbox_ops.py`、`main.py` | 邮箱、共享工作区、任务链 |
| `crewai_mas_demo/m4l27` | Human Checkpoint | `human_cli.py`、`main.py` | 人类确认节点和单一接口 |
| `crewai_mas_demo/m4l28` | 自我进化 | `log_query.py`、`schemas.py`、`seed_logs.py` | 三层日志和复盘提案 |
| `crewai_mas_demo/m5l30` | Observability | `hook_framework/*`、`shared_hooks/*`、`demo.py` | 5+2 事件和 Langfuse |
| `crewai_mas_demo/m5l31` | Reliability | `shared_hooks/cost_guard.py`、`loop_detector.py`、`retry_tracker.py` | 策略可阻断的可靠性层 |
| `crewai_mas_demo/m5l32` | Security | `shared_hooks/sandbox_guard.py`、`permission_gate.py` | 沙箱、权限、凭证、安全审计 |

## 阶段项目吸收关系

| 阶段项目 | 吸收的前置知识 | 标志性工程形态 |
| --- | --- | --- |
| Project 1 小红书爆款笔记 | Agent RGB、Task 契约、Process、Multimodal、FastAPI、日志指标 | `agents.yaml` + `tasks.yaml` + `flows.py` + API Service |
| Project 2 XiaoPaw 飞书助手 | Tool、MCP、Skills、Sandbox、Session、Cron、Feishu 接入 | Runner + Main Agent + SkillLoaderTool + Sub-Crew |
| Project 3 XiaoPaw With Memory | Harness、Bootstrap、prune/compress、文件记忆、pgvector 搜索 | MemoryAwareCrew + `workspace-init/*.md` + `memory/*` |
| Project 4 Agent Teams | Orchestrator、角色制度、邮箱协议、HITL、自我进化 | Manager/PM/RD/QA + shared workspace + events.jsonl |
| Project 5 Security Enhancement | Observability、Reliability、Guardrails、Security、E2E、SSOT | HookRegistry + shared_hooks + docs/ssot + 15 场景 E2E |

