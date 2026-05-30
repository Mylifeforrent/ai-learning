# m3l20 文件系统记忆工程化链路追踪

> 本文基于 `../crewai_mas_demo/m3l20/m3l20_file_memory.py`、`../crewai_mas_demo/m3l20/agent.log`、`../crewai_mas_demo/m3l20/agent.log.wf`、`../crewai_mas_demo/m3l20/workspace/` 与 `../crewai_mas_demo/skills/` 当前文件状态整理。
> 目标是把 `notes.md` 中讲到的“文件 memory 记忆、写通道、Skill 固化、记忆治理”对应到真实代码、日志输入输出、沙盒目录、文件名和文件内容，方便后续追踪审查。

## 1. 总览：notes 里的设计如何落到代码

`notes.md` 讲的是一个闭环：Bootstrap 读记忆、`memory-save` 写偏好/事实、`skill-creator` 写可复用 SOP、`memory-governance` 做治理。`m3l20_file_memory.py` 的工程实现把这个闭环拆成四层：

| 设计点 | 代码位置 | 工程效果 |
| --- | --- | --- |
| Bootstrap 读通道 | `build_bootstrap_prompt(WORKSPACE_DIR)` | 启动时读取 `soul.md`、`user.md`、`agent.md`、`memory.md` 前 200 行，拼进 Agent backstory |
| 写权限隔离 | `SkillLoaderTool(sandbox_mount_desc=M3L20_SANDBOX_MOUNT_DESC)` | 主 Agent 不拿 `FileWriterTool` / `FileReadTool`，所有写文件都交给 Sub-Crew 在沙盒里做 |
| 沙盒目录映射 | `sandbox-docker-compose.yaml` + `M3L20_SANDBOX_MOUNT_DESC` | 本地 `m3l20/workspace` 映射为沙盒 `/workspace:rw`；本地 `../skills` 映射为沙盒 `/mnt/skills:rw` |
| 渐进式披露 | `tools/skill_loader_tool.py` | 主 Agent 只看到 Skill 的 `name + description`；触发后才加载完整 `SKILL.md` 并启动 Sub-Crew |
| Session 持久化 | `save_session_ctx()` / `append_session_raw()` | 压缩上下文写 `workspace/sessions/demo_m3l20_ctx.json`，原始历史追加到 `demo_m3l20_raw.jsonl` |

整体链路可以这样看：

```text
用户输入
  ↓
XiaoPawCrew.main() 三轮 DEMO_ROUNDS
  ↓
Crew.kickoff(inputs={"user_request": message})
  ↓
assistant_agent.backstory = build_bootstrap_prompt(workspace)
  ↓
主 Agent 只持有 skill_loader + search_web
  ↓
主 Agent 选择 skill_loader(skill_name, task_context)
  ↓
SkillLoaderTool 读取对应 SKILL.md 全文
  ↓
build_skill_crew(...) 创建 Sub-Crew
  ↓
Sub-Crew 通过 AIO-Sandbox MCP 读写 /workspace 或 /mnt/skills
  ↓
结果返回主 Agent
  ↓
上下文写入 workspace/sessions/
```

## 2. 文件系统目录：本地路径与沙盒路径的对应关系

### 2.1 本地真实目录

当前代码与日志位于：

```text
../crewai_mas_demo/m3l20/
├── m3l20_file_memory.py
├── sandbox-docker-compose.yaml
├── agent.log
├── agent.log.wf
└── workspace/
    ├── soul.md
    ├── user.md
    ├── agent.md
    ├── memory.md
    └── sessions/
        ├── demo_m3l20_ctx.json
        └── demo_m3l20_raw.jsonl
```

共享 Skills 目录位于：

```text
../crewai_mas_demo/skills/
├── load_skills.yaml
├── memory-save/SKILL.md
├── skill-creator/SKILL.md
├── memory-governance/SKILL.md
└── software-dev-sop/SKILL.md
```

### 2.2 沙盒挂载目录

`m3l20/sandbox-docker-compose.yaml` 把本地目录映射进 AIO-Sandbox：

```yaml
volumes:
  - ./workspace:/workspace:rw
  - ../skills:/mnt/skills:rw
```

所以日志里看到的沙盒路径，对应本地路径如下：

| 沙盒路径 | 本地路径 | 用途 |
| --- | --- | --- |
| `/workspace/user.md` | `../crewai_mas_demo/m3l20/workspace/user.md` | 用户档案和偏好，`memory-save` 的主要写入目标 |
| `/workspace/agent.md` | `../crewai_mas_demo/m3l20/workspace/agent.md` | Agent 行为规范和治理触发规则 |
| `/workspace/memory.md` | `../crewai_mas_demo/m3l20/workspace/memory.md` | 记忆索引，只放指针，Bootstrap 读前 200 行 |
| `/workspace/sessions/demo_m3l20_ctx.json` | `../crewai_mas_demo/m3l20/workspace/sessions/demo_m3l20_ctx.json` | 压缩后的可恢复上下文 |
| `/workspace/sessions/demo_m3l20_raw.jsonl` | `../crewai_mas_demo/m3l20/workspace/sessions/demo_m3l20_raw.jsonl` | 原始 append-only 对话历史 |
| `/mnt/skills/load_skills.yaml` | `../crewai_mas_demo/skills/load_skills.yaml` | Skill 注册清单 |
| `/mnt/skills/<skill-name>/SKILL.md` | `../crewai_mas_demo/skills/<skill-name>/SKILL.md` | 可复用 Skill 的规范文件 |

### 2.3 当前核心记忆文件内容

`/workspace/memory.md` 当前只有 6 行，是一个非常薄的索引：

```md
# XiaoPaw 记忆索引

> 200 行上限。各主题详见对应 topic 文件，此处只写指针。

## 用户偏好
→ 详见 user.md（Bootstrap 直接注入，此处不重复）
```

`/workspace/user.md` 当前已经包含日志里要保存的偏好：

```md
# 用户档案：晓寒

- **职业**：互联网 AI 技术架构师，极客时间签约讲师
- **当前项目**：《企业级多智能体设计实战》（极客时间专栏）
- **技术偏好**：Python / CrewAI / FastAPI，不喜欢废话，AI 回复控制在 200 字以内，Python 代码注释尽量使用中文
- **工作内容**：准备课程材料、调研行业动态、输出技术文章、录制视频
- **语言**：中文回复
- **代码注释**：Python 代码注释尽量使用中文
```

`/workspace/agent.md` 明确约束主 Agent 不直接读写文件：

```md
本课（m3l20）主 Agent **不使用**文件读写工具（FileReadTool / FileWriterTool）。
所有文件操作通过 skill_loader 调用对应 Skill，由 Sub-Crew 在沙盒中执行。

- memory.md 超过 150 行时主动提示用户触发 memory-governance
- 有死链（主题文件不存在但 memory.md 里有索引）时触发治理
- skills/ 有功能重叠的 Skill 时建议合并
```

## 3. 代码链路：Agent 如何收到信息、装配上下文、调用 Skill

### 3.1 三轮演示输入长什么样

`m3l20_file_memory.py` 里定义了三轮演示：

```python
DEMO_ROUNDS = [
    (
        "记忆保存",
        "我以后写 Python 代码，注释尽量用中文，回复也控制在 200 字以内。把这两条偏好记录下来。",
    ),
    (
        "技能固化",
        (
            "我发现每次分析港股都要做同样几步：查实时行情 → 看近期新闻 → 写估值分析。"
            "把这个 SOP 保存为一个叫 analyze-hk-stock 的 Skill，以后直接调用。"
        ),
    ),
    (
        "记忆治理",
        "帮我审计一下 workspace/ 和 skills/ 目录，有没有需要清理的内容，生成治理报告。",
    ),
]
```

每一轮都会传给 CrewAI：

```python
result = crew_instance.crew().kickoff(
    inputs={"user_request": message}
)
```

Task 的 `description` 是：

```python
description = "{user_request}"
expected_output = "针对用户请求的完整回复，文件操作已通过 Skill 在沙盒中完成"
```

所以主 Agent 收到的不是文件路径 API，而是一段自然语言任务。它要自己决定是否调用 `skill_loader`。

### 3.2 Bootstrap 注入的系统上下文长什么样

`build_bootstrap_prompt()` 会读取：

```python
for fname, tag in [
    ("soul.md",   "soul"),
    ("user.md",   "user_profile"),
    ("agent.md",  "agent_rules"),
]:
    ...

memory_path = workspace_dir / "memory.md"
lines = memory_path.read_text(encoding="utf-8").splitlines()[:200]
```

日志 `agent.log.wf` 里可以看到真实注入后的系统消息结构：

```text
You are XiaoPaw 个人助手.
<soul>
... soul.md 内容 ...
</soul>

<user_profile>
... user.md 内容 ...
</user_profile>

<agent_rules>
... agent.md 内容 ...
</agent_rules>

<memory_index>
... memory.md 前 200 行 ...
</memory_index>
```

这对应 `notes.md` 里的“读通道”：启动时只读固定骨架和薄索引，不把所有历史 topic 文件一次性塞进上下文。

### 3.3 主 Agent 拿到哪些工具

`assistant_agent()` 里只给了两个工具：

```python
tools = [
    SkillLoaderTool(sandbox_mount_desc=M3L20_SANDBOX_MOUNT_DESC),
    BaiduSearchTool(),
    # 没有 FileWriterTool / FileReadTool
]
```

关键点是：主 Agent 没有直接写文件的工具。它能做的是：

1. 判断任务属于哪个 Skill；
2. 调用 `skill_loader(skill_name, task_context)`；
3. 由 `SkillLoaderTool` 创建 Sub-Crew；
4. Sub-Crew 在沙盒里读写 `/workspace` 或 `/mnt/skills`。

### 3.4 `SkillLoaderTool` 做了什么

`SkillLoaderTool.__init__()` 会读取 `../crewai_mas_demo/skills/load_skills.yaml`，只提取每个 `SKILL.md` 的 frontmatter description，生成轻量 XML：

```xml
<available_skills>
  <skill>
    <name>memory-save</name>
    <type>task</type>
    <description>Use this skill to persist important information...</description>
  </skill>
  <skill>
    <name>skill-creator</name>
    <type>task</type>
    <description>Create new skills and save them...</description>
  </skill>
  <skill>
    <name>memory-governance</name>
    <type>task</type>
    <description>Use this skill to audit and clean up...</description>
  </skill>
</available_skills>
```

真正调用时，`_get_skill_instructions(skill_name)` 才读取完整 `SKILL.md`，再拼上沙盒强约束：

```text
IMPORTANT:【强制约束】所有脚本和文件操作必须在 AIO-Sandbox 中执行，禁止直接操作本地文件系统。
此 Skill 资源已挂载至沙盒绝对路径：/mnt/skills/<skill-name>/

可用沙盒工具：
1. sandbox_file_operations
2. sandbox_execute_bash
3. sandbox_execute_code
4. sandbox_str_replace_editor
```

随后 `_execute_skill_async()` 走任务型 Skill 路径：

```python
crew = build_skill_crew(
    skill_name=skill_name,
    skill_instructions=instructions,
    mount_desc=self.sandbox_mount_desc,
    mcp_url=self.sandbox_mcp_url,
)
result = await crew.akickoff(inputs=base_inputs)
```

这就是 `notes.md` 里说的“主 Agent 不碰文件系统，写操作全部通过 Sub-Crew + 沙盒完成”。

## 4. Round 1：memory-save 如何保存用户偏好

### 4.1 用户输入

日志 `agent.log` 记录：

```text
Round 1/3  [记忆保存]
用户消息   : 我以后写 Python 代码，注释尽量用中文，回复也控制在 200 字以内。把这两条偏好记录下来。
```

### 4.2 主 Agent 发起的 Skill 调用

`workspace/sessions/demo_m3l20_ctx.json` 中记录的调用是：

```text
Thought: 需要将用户的两条偏好（Python 注释用中文、回复控制在 200 字以内）持久化保存。根据 Agent 规范，应调用 memory-save 技能。
Action: skill_loader
Action Input: {
  "skill_name": "memory-save",
  "task_context": "记录用户偏好：1. Python 代码注释尽量使用中文；2. AI 回复严格控制在 200 字以内。"
}
```

`task_context` 本质上就是 Sub-Crew 收到的任务说明。它没有直接告诉 Sub-Crew “怎么写文件”，具体写入规则来自 `memory-save/SKILL.md` 和 `M3L20_SANDBOX_MOUNT_DESC`。

### 4.3 Sub-Crew 读写的目标文件

目标文件是：

```text
沙盒路径：/workspace/user.md
本地路径：../crewai_mas_demo/m3l20/workspace/user.md
```

`agent.log` 里能看到 Sub-Crew 的关键动作：

```text
Tool Args: {'action': 'read', 'path': '/workspace/user.md'}
...
Tool Args: {'command': 'str_replace', 'path': '/workspace/user.md', ...}
...
Tool Args: {'action': 'write', 'path': '/workspace/user.md', 'content': '# 用户档案：晓寒\n\n- ...'}
...
Tool Args: {'action': 'read', 'path': '/workspace/user.md'}
```

也就是说，实际执行是：

1. 先读取 `/workspace/user.md`；
2. 判断偏好是否重复；
3. 尝试用 `str_replace` 精准更新；
4. 后续又用 `sandbox_file_operations(action="write")` 写入完整内容；
5. 最后 read-back 验证。

这和 `notes.md` 中“写前先读、更新优于追加、写后 read-back 验证”的方向一致。

### 4.4 返回结果和最终效果

日志里的最终 Observation：

```json
{
  "status": "completed",
  "details": {
    "file_path": "/workspace/user.md",
    "preferences_recorded": [
      "Python 代码注释尽量使用中文",
      "AI 回复严格控制在 200 字以内"
    ],
    "verification_status": "verified"
  }
}
```

最终用户可见回复：

```text
已记录您的两条偏好：1. Python 代码注释尽量使用中文；2. AI 回复严格控制在 200 字以内。信息已保存至 user.md 文件并通过验证。
```

当前 `user.md` 的效果是：

```md
- **技术偏好**：Python / CrewAI / FastAPI，不喜欢废话，AI 回复控制在 200 字以内，Python 代码注释尽量使用中文
- **代码注释**：Python 代码注释尽量使用中文
```

审查结论：

- ✅ 偏好确实进入了文件系统；
- ✅ 下次 `build_bootstrap_prompt()` 会把 `user.md` 注入 `<user_profile>`；
- ⚠️ 当前 `user.md` 有轻微冗余：`技术偏好` 和 `代码注释` 都记录了 Python 中文注释偏好。

## 5. Round 2：skill-creator 如何把 SOP 固化成 Skill

### 5.1 用户输入

日志 `agent.log` 记录：

```text
Round 2/3  [技能固化]
用户消息   : 我发现每次分析港股都要做同样几步：查实时行情 → 看近期新闻 → 写估值分析。把这个 SOP 保存为一个叫 analyze-hk-stock 的 Skill，以后直接调用。
```

### 5.2 主 Agent 发起的 Skill 调用

Session 文件中的调用：

```text
Thought: 用户希望将港股分析的 SOP（查实时行情 → 看近期新闻 → 写估值分析）封装为可复用 Skill，应调用 skill-creator。
Action: skill_loader
Action Input: {
  "skill_name": "skill-creator",
  "task_context": "创建名为 analyze-hk-stock 的 Skill，SOP 包含三步：1. 查询港股实时行情；2. 检索近期相关新闻；3. 输出估值分析报告。"
}
```

### 5.3 预期文件写入位置

根据 `skill-creator/SKILL.md` 和 m3l20 的沙盒挂载，预期应该写入：

```text
沙盒 Skill 文件：/mnt/skills/analyze-hk-stock/SKILL.md
本地 Skill 文件：../crewai_mas_demo/skills/analyze-hk-stock/SKILL.md

沙盒注册文件：/mnt/skills/load_skills.yaml
本地注册文件：../crewai_mas_demo/skills/load_skills.yaml
```

`skill-creator/SKILL.md` 要求执行四步：

```text
1. Read /mnt/skills/load_skills.yaml，检查是否已有同名 Skill
2. Write /mnt/skills/<skill-name>/SKILL.md
3. 更新 /mnt/skills/load_skills.yaml
4. Read-back 验证 SKILL.md 和 load_skills.yaml
```

### 5.4 日志返回结果

日志里的 Observation：

```json
{
  "errcode": 0,
  "errmsg": "success",
  "skill_name": "analyze-hk-stock",
  "path": "/mnt/skills/analyze-hk-stock/SKILL.md",
  "trigger": "Use this skill when the user asks to analyze Hong Kong stocks, research HK companies, or evaluate HK investment opportunities. Activate whenever 港股 or HK stock analysis is needed."
}
```

最终用户可见回复：

```text
✅ 已创建 Skill：analyze-hk-stock
路径：/mnt/skills/analyze-hk-stock/SKILL.md
触发条件：当用户请求分析港股、研究香港上市公司或评估港股投资机会时自动激活。
SOP 步骤：1. 查询实时行情；2. 检索近期新闻；3. 输出估值分析报告。
```

### 5.5 当前文件状态审查

当前文件系统复查结果：

```text
../crewai_mas_demo/skills/analyze-hk-stock/ 不存在
../crewai_mas_demo/skills/load_skills.yaml 中没有 analyze-hk-stock 条目
```

因此这里要区分两件事：

| 维度 | 结论 |
| --- | --- |
| 日志证据 | `agent.log` / `demo_m3l20_ctx.json` 记录 Sub-Crew 返回了创建成功 |
| 当前文件证据 | 当前 checkout 下没有 `analyze-hk-stock/SKILL.md`，也没有注册条目 |
| 审查判断 | 该 Skill 的“日志返回”存在，但当前文件落盘状态不可验证；可能是后续被清理、日志来自不同运行状态，或 demo 中 Sub-Crew 返回了成功但未真正持久化 |

这是一个值得修正的工程点：`skill-creator` 的成功条件应该以 **文件存在 + `load_skills.yaml` 包含条目 + read-back 内容正确** 三者同时满足为准，而不是只相信模型返回 JSON。

## 6. Round 3：memory-governance 如何做记忆治理

### 6.1 用户输入

日志 `agent.log` 记录：

```text
Round 3/3  [记忆治理]
用户消息   : 帮我审计一下 workspace/ 和 skills/ 目录，有没有需要清理的内容，生成治理报告。
```

### 6.2 主 Agent 发起的 Skill 调用

Session 文件中的调用：

```text
Thought: 用户要求审计 workspace/ 和 skills/ 目录并生成治理报告，应调用 memory-governance 技能。
Action: skill_loader
Action Input: {
  "skill_name": "memory-governance",
  "task_context": "审计 workspace/ 和 skills/ 目录，检查 memory.md 行数、死链、重复或冗余 Skill，并生成治理报告。"
}
```

### 6.3 Sub-Crew 扫描了哪些对象

根据 `memory-governance/SKILL.md` 和日志，治理扫描范围包括：

```text
/workspace/memory.md
/workspace/*.md
/mnt/skills/load_skills.yaml
/mnt/skills/*/SKILL.md
```

日志里可见它执行了这类扫描逻辑：

```python
workspace_files = ['agent.md', 'memory.md', 'user.md', 'soul.md']
referenced = ...
orphan_files = []
for ws_file in workspace_files:
    if ws_file not in referenced:
        orphan_files.append(ws_file)
```

又扫描了 Skill 的 `allowed-tools`：

```python
legal_tools = ['Read', 'Write', 'Bash', 'Browser']
illegal_tools = [t for t in allowed_tools if t not in legal_tools]
if illegal_tools:
    skill_issues.append({
        'type': 'illegal_tool',
        'skill': skill_name,
        'illegal_tools': illegal_tools
    })
```

### 6.4 治理报告 Observation

日志里的结构化结果：

```json
{
  "memory_status": {
    "current_lines": 6,
    "limit": 200,
    "level": "normal"
  },
  "dead_links": [],
  "orphan_files": [
    {"file": "agent.md", "reason": "未被 memory.md 任何条目引用"},
    {"file": "user.md", "reason": "未被 memory.md 任何条目引用"},
    {"file": "soul.md", "reason": "未被 memory.md 任何条目引用"}
  ],
  "misplaced_files": [],
  "routing_mismatches": [],
  "stale_files": [],
  "conflicts": [],
  "redundancies": [
    {
      "topic": "语言偏好",
      "files": ["user.md", "soul.md"],
      "description": "两处均记录了相同的中文回复偏好"
    }
  ],
  "skill_issues": [
    {
      "type": "illegal_tool",
      "skill": "software-dev-sop",
      "illegal_tools": ["FileReadTool", "FileWriterTool", "BashTool"]
    }
  ],
  "security_issues": [
    {
      "file": "agent.md",
      "entry": "References FileReadTool/FileWriterTool",
      "reason": "These should be handled by skills, not directly referenced"
    }
  ]
}
```

最终用户可见回复：

```text
✅ 治理报告生成完毕：

- Memory 状态：6/200 行，正常
- 孤立文件：agent.md、user.md、soul.md（未被 memory.md 引用）
- 冗余内容：user.md 与 soul.md 重复记录“中文回复”偏好
- Skill 问题：software-dev-sop 使用了禁止的 FileReadTool/FileWriterTool/BashTool
- 安全风险：agent.md 直接引用文件工具，应改由 Skill 封装

建议：合并偏好至 user.md，移除 agent.md/soul.md；修复或移除违规 Skill。
```

### 6.5 每个治理结果代表什么

| 检查项 | 日志结果 | 含义 | 当前判断 |
| --- | --- | --- | --- |
| `memory_status` | 6/200，normal | `memory.md` 很薄，没有接近 150 行预警线 | ✅ 正常 |
| `dead_links` | `[]` | `memory.md` 没有指向不存在的 topic 文件 | ✅ 正常 |
| `orphan_files` | `agent.md`、`user.md`、`soul.md` | 扫描器认为这些文件没有被 `memory.md` 引用 | ⚠️ 规则需调优 |
| `redundancies` | `user.md` + `soul.md` 都有中文回复偏好 | 多处记录相似偏好，未来可能一处更新另一处没更新 | ⚠️ 可优化 |
| `skill_issues` | `software-dev-sop` 使用 `FileReadTool` / `FileWriterTool` / `BashTool` | 这些不是 AIO-Sandbox 允许的基础工具名 | ✅ 发现真实问题 |
| `security_issues` | `agent.md` 提到文件工具 | 治理器认为直接引用文件工具有安全风险 | ⚠️ 需要人工判定 |

这里最重要的审查结论是：`memory-governance` 的方向正确，但规则还比较“粗”。`soul.md`、`user.md`、`agent.md` 是 Bootstrap 固定加载文件，不是 topic 文件；它们不应该因为没出现在 `memory.md` 里就被视为普通孤立文件。更合理的治理规则是：

```text
核心文件白名单：
  soul.md
  user.md
  agent.md
  memory.md

野文档检查只扫描：
  memory_*.md
  或约定的 topic 文件
```

## 7. Session 文件记录了什么

`m3l20_file_memory.py` 在每一轮结束后执行：

```python
new_msgs = list(crew_instance._last_msgs)[crew_instance._history_len:]
append_session_raw(SESSION_ID, new_msgs)
save_session_ctx(SESSION_ID, list(crew_instance._last_msgs))
```

对应两个文件：

| 文件 | 类型 | 作用 |
| --- | --- | --- |
| `workspace/sessions/demo_m3l20_ctx.json` | 覆盖写入 | 保存当前可恢复上下文，下次同 session 启动时 `_restore_session()` 会加载 |
| `workspace/sessions/demo_m3l20_raw.jsonl` | 追加写入 | 保存原始历史，每条消息带 `ts` 时间戳，适合审计 |

`demo_m3l20_ctx.json` 中能看到三类关键内容：

```text
1. system：Bootstrap 后的 soul/user/agent/memory_index + SkillLoaderTool 可用技能 XML
2. user：每一轮 Current Task
3. assistant：Thought / Action / Action Input / Observation / Final Answer
```

这说明 m3l20 不只是把“长期记忆”写入 `workspace/*.md`，还把“本 session 发生过什么”写入 `sessions/`。两者分工不同：

| 类型 | 文件 | 生命周期 | 用途 |
| --- | --- | --- | --- |
| 长期记忆 | `user.md`、`agent.md`、`memory.md`、topic 文件 | 跨 session 长期有效 | Bootstrap 注入和按需读取 |
| 会话历史 | `sessions/demo_m3l20_ctx.json`、`demo_m3l20_raw.jsonl` | 当前 session 或审计历史 | 恢复上下文、排查执行链路 |

## 8. 与 notes.md 的对齐度和差异点

### 8.1 对齐的地方

- ✅ **Bootstrap 读通道已落地**：`soul.md`、`user.md`、`agent.md`、`memory.md` 被拼进 backstory。
- ✅ **主 Agent 无直接写权限**：代码中没有给主 Agent 配 `FileReadTool` / `FileWriterTool`。
- ✅ **写操作走 Sub-Crew + 沙盒**：`SkillLoaderTool` 把任务派给 AIO-Sandbox MCP。
- ✅ **沙盒挂载支持写记忆和写 Skill**：`/workspace:rw`、`/mnt/skills:rw`。
- ✅ **Session 恢复、剪枝、压缩沿用 m3l19**：`before_llm_hook()` 负责恢复历史、剪枝 tool result、必要时压缩。
- ✅ **治理链路有真实日志**：`memory-governance` 确实输出了 memory 状态、死链、冗余、Skill 问题、安全问题。

### 8.2 需要注意的差异

| 差异点 | 当前状态 | 影响 |
| --- | --- | --- |
| `memory-save/SKILL.md` 与 notes 的四门控不完全一致 | 当前 `memory-save` 更强调 `sandbox_file_operations write` 和 read-back，未完整写出 Utility / Confidence / Novelty / Type 四门控 | 需要把 notes 中的准入控制补进实际 Skill，减少误写 |
| `skill-creator` 日志成功但当前文件缺失 | 没有 `../skills/analyze-hk-stock/SKILL.md` | 说明成功返回和真实落盘之间缺少强验证，或当前 checkout 与日志运行状态不一致 |
| `memory-governance` 把核心文件算作 orphan | `soul.md` / `user.md` / `agent.md` 被列为孤立文件 | 治理规则要增加核心文件白名单，避免误建议删除 |
| `software-dev-sop` 的 `allowed-tools` 是旧工具名 | `FileReadTool` / `FileWriterTool` / `BashTool` | 对 m3l20 的沙盒 Skill 体系来说确实不合法，应迁移成 `Read` / `Write` / `Bash` 或脚本调用说明 |

## 9. 记忆治理的整体步骤和链路

结合代码和日志，`memory-governance` 的完整治理链路是：

```text
用户请求治理
  ↓
主 Agent 根据 Skill XML 选择 memory-governance
  ↓
Action Input:
  skill_name = "memory-governance"
  task_context = "审计 workspace/ 和 skills/ 目录..."
  ↓
SkillLoaderTool 读取 /mnt/skills/memory-governance/SKILL.md
  ↓
Sub-Crew 获得治理规范 + m3l20 沙盒挂载说明
  ↓
Sub-Crew 扫描：
  /workspace/memory.md
  /workspace/*.md
  /mnt/skills/load_skills.yaml
  /mnt/skills/*/SKILL.md
  ↓
生成结构化 JSON：
  memory_status
  dead_links
  orphan_files
  routing_mismatches
  stale_files
  conflicts
  redundancies
  skill_issues
  security_issues
  ↓
主 Agent 转成用户可读治理报告
  ↓
等待用户确认后，才应执行清理
```

当前日志中只执行到“生成治理报告”，没有执行删除或归档。这符合 `memory-governance/SKILL.md` 的关键原则：

```text
CRITICAL：不得在用户确认前执行任何删除或修改操作。
```

## 10. 每一步做了什么、效果是什么

| 步骤 | 收到的信息 | 操作目录/文件 | 做的事 | 效果 |
| --- | --- | --- | --- | --- |
| Bootstrap | 无用户输入，启动时自动执行 | `workspace/soul.md`、`user.md`、`agent.md`、`memory.md` | 拼成 `<soul>`、`<user_profile>`、`<agent_rules>`、`<memory_index>` | Agent 一启动就知道身份、用户偏好、行为规则和记忆索引 |
| 记忆保存 | “Python 注释用中文，回复 200 字以内” | `/workspace/user.md` | 读取、更新、写入、read-back | 偏好进入 `user.md`，下次 session 自动生效 |
| 技能固化 | “港股分析 SOP 保存成 analyze-hk-stock Skill” | 预期 `/mnt/skills/analyze-hk-stock/SKILL.md` + `/mnt/skills/load_skills.yaml` | 日志返回创建成功 | 当前文件缺失，需进一步修复验证链路 |
| 记忆治理 | “审计 workspace/ 和 skills/” | `/workspace/*.md` + `/mnt/skills/*/SKILL.md` | 扫描 memory 行数、死链、孤立文件、冗余、非法工具、安全问题 | 生成治理结果：memory 正常、发现冗余和 Skill 工具名问题 |
| Session 保存 | 每轮 Agent 消息 | `workspace/sessions/demo_m3l20_ctx.json`、`demo_m3l20_raw.jsonl` | 覆盖保存压缩上下文，追加原始历史 | 后续可恢复 session，也可审计完整调用链 |

## 11. 建议的后续工程修正

1. **把核心文件加入治理白名单**
   - `soul.md`、`user.md`、`agent.md`、`memory.md` 是 Bootstrap 骨架，不应作为普通 orphan 文件。

2. **强化 `skill-creator` 的 read-back 验证**
   - 返回成功前必须确认：
     - `/mnt/skills/<skill-name>/SKILL.md` 存在；
     - `/mnt/skills/load_skills.yaml` 包含对应条目；
     - YAML 可解析；
     - 重新初始化 `SkillLoaderTool` 能看到新 Skill。

3. **把 notes 中的四门控补进 `memory-save/SKILL.md`**
   - Utility：三个月后是否仍有价值；
   - Confidence：是否来自用户明确表达；
   - Novelty：目标文件是否已有重复内容；
   - Type：是否为稳定偏好/规则/决策。

4. **把旧式 `allowed-tools` 迁移为沙盒基础工具**
   - `software-dev-sop` 当前使用 `FileReadTool` / `FileWriterTool` / `BashTool`；
   - m3l20 的 Skill 体系更适合用 `Read` / `Write` / `Bash`，复杂业务动作放进 `scripts/`，再通过 Bash 执行。

5. **治理报告落盘路径要统一**
   - `memory-governance/SKILL.md` 写的是 `/workspace/memory_governance_report.md`；
   - 早期日志里出现过 `/workspace/output/governance_report.md`；
   - 建议统一为 `/workspace/memory_governance_report.md`，便于 Bootstrap 或用户查找。

## 12. 一句话总结

m3l20 的文件系统记忆工程化，本质是：**主 Agent 只负责判断和派单，长期记忆和技能文件都由专用 Skill 在沙盒挂载目录中读写，并用 session 文件保留执行轨迹；治理 Skill 定期扫描这些文件，报告过期、重复、死链和安全问题，但必须等用户确认后才清理。**
