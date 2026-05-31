## XiaoPaw（小爪子）

基于飞书的本地工作助手，通过 Skills 生态 + AIO-Sandbox（Docker）实现安全可扩展的工具调用。支持飞书 WebSocket 长连接，无需公网 IP，适合本地/内网部署。

> **第22课·记忆篇**：本版本新增三层记忆架构——Bootstrap 上下文注入、ctx.json 跨 session 压缩、pgvector 搜索记忆。

### 核心功能

- **飞书全场景接入**：单聊（p2p）、群聊（group）、话题群（thread）
- **Skills 生态**：9 个内置 Skill，覆盖文件处理、网页搜索/浏览、飞书操作、定时任务、历史查询
- **AIO-Sandbox 隔离**：所有代码执行在 Docker 沙盒中运行，凭证不经过 LLM
- **三层记忆架构**（第22课新增）：Bootstrap 文件注入 + ctx.json 上下文压缩 + pgvector 语义搜索
- **Verbose 详细模式**：实时推送 Agent 推理过程，可随时开关
- **定时任务**：支持一次性（at）、固定间隔（every）、Cron 表达式三种模式
- **TestAPI**：HTTP 接口本地调试，无需真实飞书环境
- **卡片消息 + Loading 效果**：发送交互式卡片，Loading 状态实时更新
- **Markdown 富文本渲染**：支持 lark_md 格式，Agent 回复支持加粗、斜体、链接等

### 内置 Skills

| Skill | 类型 | 能力 |
|-------|------|------|
| `pdf` | 任务型 | PDF 解析、文本提取、格式转换 |
| `docx` | 任务型 | Word 文档读取与处理 |
| `pptx` | 任务型 | PPT 文档读取与处理 |
| `xlsx` | 任务型 | Excel 表格读取与处理 |
| `feishu_ops` | 任务型 | 通过 `scripts/*.py` 脚本读取飞书云文档、向指定群/用户发消息 |
| `scheduler_mgr` | 任务型 | 通过 `scheduler_mgr/scripts/*.py` 创建/查看/更新/删除定时任务 |
| `baidu_search` | 任务型 | 百度千帆网络搜索，支持时间过滤与站点限定 |
| `web_browse` | 任务型 | 网页内容提取（Markdown 转换）与浏览器自动化（截图/表单/JS） |
| `history_reader` | 参考型 | 分页读取历史对话记录 |
| `memory-save` | 任务型 | 将用户偏好/事实/SOP 持久化到 workspace 文件（L20 语义记忆写通道） |
| `skill-creator` | 任务型 | 将 SOP 固化为可复用 SKILL.md（L20 程序记忆） |
| `memory-governance` | 任务型 | 审计并清理 workspace 记忆文件（去重/过期/死链） |
| `search_memory` | 任务型 | 基于 pgvector 的历史对话语义搜索（L21 搜索层） |

### 目录结构

```
xiaopaw/
├── main.py                  # 进程入口
├── models.py                # InboundMessage / Attachment / SenderProtocol
├── runner.py                # 执行引擎（per-routing_key 队列、Slash 命令、Agent 调用）
├── llm/aliyun_llm.py        # AliyunLLM 适配器（通义千问，支持多模态+Function Calling）
├── feishu/
│   ├── listener.py          # WebSocket 事件 → InboundMessage
│   ├── sender.py            # 消息发送（p2p/group/thread），含重试
│   ├── downloader.py        # 附件下载到 session workspace
│   └── session_key.py       # routing_key 解析
├── agents/
│   ├── main_crew.py         # 主 Crew（build_agent_fn 工厂）
│   └── skill_crew.py        # Sub-Crew 工厂（build_skill_crew）
├── memory/
│   ├── bootstrap.py         # 读取 workspace 4文件 → 注入 Agent backstory（L19）
│   ├── context_mgmt.py      # prune 剪枝 / compress 压缩 / ctx.json + raw.jsonl 持久化（L19）
│   └── indexer.py           # extract → embed → upsert pgvector 异步建索引（L21）
├── tools/
│   ├── skill_loader.py      # SkillLoaderTool（渐进式披露 + Sub-Crew 触发）
│   ├── add_image_tool_local.py
│   ├── baidu_search_tool.py
│   └── intermediate_tool.py
├── session/                 # SessionManager（index.json + JSONL）
├── cron/                    # CronService（asyncio 精确 timer）
├── cleanup/                 # CleanupService（按策略清理过期文件）
├── observability/           # 日志 + Prometheus Metrics
├── api/                     # TestAPI（aiohttp HTTP 服务）
└── skills/                  # SKILL.md + 执行脚本，每个 Skill 独立目录
    ├── pdf/ docx/ pptx/ xlsx/
    ├── feishu_ops/
    ├── scheduler_mgr/
    ├── baidu_search/
    ├── web_browse/
    ├── history_reader/
    ├── memory-save/
    ├── memory-governance/
    ├── skill-creator/
    └── search_memory/
```

### 环境准备

**依赖**：Python 3.11+、Docker（运行 AIO-Sandbox + pgvector）

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

**环境变量**：

```bash
export QWEN_API_KEY=<阿里云千问 API Key>       # 必填：LLM + Embedding 调用
export FEISHU_APP_ID=<飞书应用 App ID>         # 必填：飞书开放平台
export FEISHU_APP_SECRET=<飞书应用 App Secret>  # 必填：飞书开放平台
export BAIDU_API_KEY=<百度千帆 API Key>        # 可选：baidu_search Skill
export MEMORY_DB_DSN=postgresql://xiaopaw:xiaopaw123@localhost:5432/xiaopaw_memory  # 可选：pgvector 搜索记忆

# 调试时可选开启完整请求 payload 日志
export QWEN_DEBUG_PAYLOAD=1
```

### 配置 `config.yaml`

复制模板并填写飞书凭证：

```bash
cp config.yaml.template config.yaml
```

核心配置项：

```yaml
feishu:
  app_id: "${FEISHU_APP_ID}"
  app_secret: "${FEISHU_APP_SECRET}"

memory:
  workspace_dir: "./data/workspace"   # Bootstrap 读取 soul/user/agent/memory.md
  ctx_dir: "./data/ctx"              # ctx.json 跨 session 压缩快照
  db_dsn: "postgresql://xiaopaw:xiaopaw123@localhost:5432/xiaopaw_memory"

sandbox:
  url: "http://localhost:8022/mcp"

debug:
  enable_test_api: true             # 本地调试时开启
  test_api_port: 9090
```

完整配置项见 `config.yaml.template`。

### 初始化 Workspace 文件（第22课记忆篇）

`workspace-init/` 目录提供了初始模板，复制后按实际情况修改：

```bash
mkdir -p data/workspace
cp workspace-init/soul.md   data/workspace/soul.md    # XiaoPaw 性格/身份
cp workspace-init/user.md   data/workspace/user.md    # 用户档案（按需填写）
cp workspace-init/agent.md  data/workspace/agent.md   # Agent 能力边界
cp workspace-init/memory.md data/workspace/memory.md  # 长期记忆索引（初始为空）
```

Bootstrap 阶段（每轮对话开始前）XiaoPaw 会读取这四个文件构建 Agent 背景知识：
- `soul.md`：不变的性格与原则
- `user.md`：用户档案（可手动更新，也可由 XiaoPaw 自动追加）
- `agent.md`：工具清单与能力边界
- `memory.md`：跨 session 重要信息索引（200行上限，超出自动截断）

### 启动 Docker 服务

**AIO-Sandbox**（代码执行沙盒）：

```bash
docker compose -f sandbox-docker-compose.yaml up -d
```

Sandbox MCP 端点：`http://localhost:8022/mcp`

**pgvector**（搜索记忆数据库，第22课新增）：

```bash
docker compose -f pgvector-docker-compose.yaml up -d
```

pgvector 连接串：`postgresql://xiaopaw:xiaopaw123@localhost:5432/xiaopaw_memory`

> `schema.sql` 在容器首次启动时自动执行，无需手动建表。

### 启动 XiaoPaw

```bash
python3 -m xiaopaw.main
```

启动后：
- 飞书 WebSocket 开始监听消息
- Prometheus 指标：`http://127.0.0.1:9100/metrics`
- JSON 行日志：`data/logs/xiaopaw.log`
- TestAPI（如已启用）：`http://127.0.0.1:9090/api/test/message`

### 本地调试（TestAPI）

在 `config.yaml` 中设置 `debug.enable_test_api: true`，无需真实飞书环境：

```bash
# 发送消息，同步获取 Bot 回复
curl -X POST http://127.0.0.1:9090/api/test/message \
  -H "Content-Type: application/json" \
  -d '{"routing_key": "p2p:ou_test001", "content": "你好"}'

# 响应示例（Bot 回复已通过卡片消息 + update_card 完整更新）
{
  "msg_id": "test_xxx",
  "reply": "**你好！** 我是 XiaoPaw 工作助手。有什么可以帮助你的吗？",
  "session_id": "s-uuid-001",
  "duration_ms": 2345,
  "skills_called": []
}

# 清空会话数据
curl -X DELETE http://127.0.0.1:9090/api/test/sessions
```

**卡片消息流程**（从 2026-03-09 开始）：
1. 用户发送消息 → Runner 接收
2. Runner 调用 `send_thinking()` → 发送"⏳ 思考中..."加载卡片，获取 card_msg_id
3. Agent 执行（5-30s）
4. Runner 调用 `update_card(card_msg_id, 最终结果)` → 更新卡片内容为 Agent 回复
5. 若更新失败，降级调用 `send()` 重新发送整条消息

### Slash 命令

| 命令 | 功能 |
|------|------|
| `/new` | 创建新会话，之前历史不带入 |
| `/verbose on/off` | 开启/关闭推理过程实时推送 |
| `/verbose` | 查询详细模式当前状态 |
| `/status` | 查看当前会话信息 |
| `/help` | 显示命令帮助 |

### 运行测试

```bash
# 单元测试（含覆盖率）
python3 -m pytest tests/unit/ -v --cov=xiaopaw --cov-report=term-missing

# 集成测试（无 LLM，无 Sandbox）
python3 -m pytest tests/integration/ -m "not llm and not sandbox" -v

# 集成测试（含 LLM，需设置 QWEN_API_KEY）
python3 -m pytest tests/integration/test_e2e_conversation.py -m "llm and not sandbox" -v -s

# 完整集成测试（需启动 Sandbox）
python3 -m pytest tests/integration/ -v -s --timeout=180
```

**测试统计**（2026-03-24）：642 单元测试，86%+ 覆盖率 ✅

更多设计细节见 `DESIGN.md` 和 `CLAUDE.md`。

---

## 课堂代码演示学习指南

### 整体架构一览

```
┌─────────────────────────────────────────────────────┐
│  三层记忆架构                                         │
│                                                     │
│  Layer 1（L19）: 上下文生命周期                        │
│  ┌─────────────────────────────────────────────┐    │
│  │ Bootstrap        ← soul/user/agent/memory.md │    │
│  │ → Agent backstory 注入                        │    │
│  │                                              │    │
│  │ @before_llm_call Hook:                       │    │
│  │   首次: 从 ctx.json 恢复历史                   │    │
│  │   每次: prune(工具结果) → compress(超阈值)     │    │
│  │                                              │    │
│  │ Session 持久化:                               │    │
│  │   ctx.json（覆写）+ raw.jsonl（追加）          │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Layer 2（L20）: 文件系统记忆                         │
│  ┌─────────────────────────────────────────────┐    │
│  │ memory-save    → 写入偏好/事实到 workspace/    │    │
│  │ skill-creator  → 固化 SOP 为 SKILL.md         │    │
│  │ memory-governance → 审计清理（8 项健康检查）     │    │
│  │                                              │    │
│  │ memory.md 是导航索引（≤200 行）                │    │
│  │ 实际内容在 memory_{topic}.md 中               │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Layer 3（L21）: 搜索式记忆                          │
│  ┌─────────────────────────────────────────────┐    │
│  │ 写入: asyncio.create_task(async_index_turn)  │    │
│  │   parse → extract_summary → embed → upsert   │    │
│  │                                              │    │
│  │ 读取: search_memory Skill                    │    │
│  │   hybrid: 0.7×向量 + 0.3×BM25               │    │
│  │   过滤: tags / days / routing_key            │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 学习路线

---

#### 第一步：理解三层记忆的分工

| 层 | 存什么 | 什么时候写 | 什么时候读 | 时间尺度 |
|----|--------|-----------|-----------|---------|
| L1 上下文 | LLM 对话状态 | 每次 LLM 调用（剪枝/压缩）+ 每轮结束（ctx.json） | Session 恢复时 | 跨 Session |
| L2 文件 | 稳定事实（偏好、SOP、持仓） | 用户表达偏好或确认工作流时 | Bootstrap 注入（每次 Session 启动） | 永久 |
| L3 搜索 | 瞬态对话产出（分析结论、临时判断） | 每轮自动后台索引 | 按需语义检索（search_memory Skill） | 永久 |

**理解要点**：L2 存"稳定事实"（始终在 context 中），L3 存"瞬态产出"（按需检索）——这是两层的核心区别。

---

#### 第二步：看 Bootstrap 导航骨架

**阅读文件**：`xiaopaw/memory/bootstrap.py` + `workspace-init/` 四个模板文件

| 文件 | XML 标签 | 内容 |
|------|----------|------|
| `soul.md` | `<soul>` | 不可变的人格/风格 |
| `user.md` | `<user_profile>` | 用户画像（记忆写入更新） |
| `agent.md` | `<agent_rules>` | 工作规则 + Onboarding SOP |
| `memory.md` | `<memory_index>` | 导航索引（≤200 行，指向 topic 文件） |

**理解要点**：Bootstrap 只注入"骨架"——告诉 Agent 信息在哪，不全量加载。memory.md 是目录，不是内容存储。

---

#### 第三步：看 MemoryAwareCrew 的 Hook 集成

**阅读文件**：`xiaopaw/agents/main_crew.py`（搜索 `MemoryAwareCrew`）

| Hook 时机 | 行为 |
|----------|------|
| 首次 LLM 调用 | 从 ctx.json 恢复历史 + 合并 Bootstrap 系统消息 |
| 每次 LLM 调用 | 剪枝（清除旧工具结果）→ 压缩（超 45% 阈值时分块摘要） |
| 返回值 | `None`（继续执行，不阻断） |

**理解要点**：为什么用 `@before_llm_call` 而不是 `@after_llm_call`？因为 CrewAI 的 after hook 会 `str()` 返回值，破坏工具调度的类型检查。

---

#### 第四步：看文件记忆的三个 Skill

**阅读文件**：`xiaopaw/skills/memory-save/SKILL.md` + `skill-creator/SKILL.md` + `memory-governance/SKILL.md`

| Skill | 触发场景 | 写入位置 |
|-------|---------|---------|
| memory-save | 用户表达偏好（"我喜欢..."） | workspace/ 下的 md 文件 |
| skill-creator | 用户描述重复工作流 | skills/ 下的 SKILL.md |
| memory-governance | 记忆积累过多 / 定期审计 | 清理 workspace/ 和 skills/ |

**理解要点**：memory-save 有严格的四步准入协议——准入控制（三个月价值？）→ 目标选择（写哪个文件？）→ 阈值门控（memory.md < 150 行？）→ 写入执行（str_replace + 回读验证）。

---

#### 第五步：看 pgvector 搜索记忆

**阅读文件**：`xiaopaw/memory/indexer.py` + `xiaopaw/skills/search_memory/`

写入路径（每轮自动触发）：
```
对话结束 → asyncio.create_task → ThreadPoolExecutor
  → parse_turns → extract_summary_and_tags(LLM)
  → embed_texts(text-embedding-v3, 1024维)
  → upsert_memory(ON CONFLICT DO NOTHING)
```

读取路径（按需触发）：
```
用户: "之前讨论的那个方案..."
  → search_memory Skill → Sub-Crew → scripts/search.py
  → hybrid: 0.7×cosine + 0.3×BM25
  → 返回匹配记录
```

**理解要点**：search_memory 的 SKILL.md 被设计为"主动激活"——当用户消息暗示依赖历史信息时（"根据之前的讨论"），Agent 应主动调用，不需要用户明确要求。

---

#### 第六步：看 Onboarding SOP 自删除

**阅读文件**：`workspace-init/agent.md`（搜索 "onboarding"）

六步自引导流程：命名 → 用途 → 风格 → 用户信息 → 禁忌 → SOP 训练。每一步都使用 memory-save 持久化进度。全部完成后，agent.md 中的 Onboarding SOP 章节自动删除——"任务完成即自毁"。

**理解要点**：这是"自修改 Agent 规则"的演示——Agent 不仅能写记忆文件，还能修改自己的行为规则文件。Onboarding 完成后不再需要 SOP，删除它释放 context 空间。

---

#### 第七步：看集成测试设计

**阅读文件**：`docs/test-design-course22.md` + `tests/integration/test_course22_cases.py`

| 测试组 | 场景 | 验证层 |
|--------|------|--------|
| U (P2) | SOP Skill 路由 | L2: 创建投资报告 Skill → 一句话触发 |
| V (P3) | 持仓决策 | L2: Bootstrap 注入持仓 → Agent 直接知道 |
| W (P4) | Onboarding 自删除 | L2: 完成后 agent.md 中 SOP 消失 |
| X (P5) | SOP 全生命周期 | L2: 描述 → 结构化 → 确认 → 创建 → 触发 |
| Y (P6) | 历史分析召回 | L3: 自动索引 → pgvector → search_memory |

---

### 学习检查清单

- [ ] L2 文件记忆和 L3 搜索记忆的核心区别？（L2 存稳定事实始终在 context 中，L3 存瞬态产出按需检索）
- [ ] Bootstrap 为什么只注入"骨架"不注入全量？（context 是稀缺资源，骨架只占几十行 token）
- [ ] memory.md 的 200 行限制是什么？（导航索引不是内容存储，超出会浪费 context）
- [ ] 为什么不用 `@after_llm_call`？（CrewAI 框架 `str()` 返回值，破坏工具调度类型检查）
- [ ] 异步索引为什么用 `create_task` + `run_in_executor`？（create_task 不阻塞用户对话，run_in_executor 将同步 DB 操作放入线程池）
- [ ] Onboarding SOP 完成后为什么要自删除？（释放 context 空间，不再需要的指令只是噪声）
- [ ] search_memory 什么时候应该"主动激活"？（用户消息暗示依赖历史信息时，如"之前的方案"、"上次的结论"）
