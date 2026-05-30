# m3l21 代码实践数据治理链路详解

> 本文基于上层目录 `../crewai_mas_demo/m3l21` 中的代码、执行日志，以及共享 Skill 目录 `../crewai_mas_demo/skills/search_memory` 进行分析。主要参考文件包括：
>
> - `../crewai_mas_demo/m3l21/m3l21_search_memory.py`
> - `../crewai_mas_demo/m3l21/indexer.py`
> - `../crewai_mas_demo/m3l21/schema.sql`
> - `../crewai_mas_demo/m3l21/test_m3l21.py`
> - `../crewai_mas_demo/m3l21/agent.log`
> - `../crewai_mas_demo/m3l21/agent.log.wf`
> - `../crewai_mas_demo/skills/search_memory/SKILL.md`
> - `../crewai_mas_demo/skills/search_memory/scripts/search.py`

## 1. 代码实践对应笔记里的哪几个工程思想

当前 `notes.md` 的核心思想是：文件系统记忆解决了“小规模可维护”的问题，但长期记忆一旦增长，就必须从“全量加载”转成“按需检索”。`m3l21` 的代码实践把这件事拆成两条链路：

1. **写入链路**：每轮对话结束后，把用户输入和助手回复治理成结构化记忆，写入 PostgreSQL + pgvector。
2. **读取链路**：当用户问“上次那个”“之前聊过的”这类历史问题时，通过 `search_memory` Skill 执行向量、全文、标量过滤混合检索，再把召回结果交给 Agent 使用。

对应关系如下：

| 笔记中的工程思想 | 代码实现位置 | 实现方式 |
| --- | --- | --- |
| Bootstrap 只加载小索引 | `m3l21_search_memory.py` 的 `build_bootstrap_prompt()` | 只读取 `soul.md`、`user.md`、`agent.md` 和 `memory.md` 前 200 行 |
| 文件索引不再承载完整长期记忆 | `WORKSPACE_DIR` 复用 m3l20 workspace，新增 pgvector 表 | 文件保留短索引，完整对话记忆进入 `memories` 表 |
| 一问一答为最小 chunk | `indexer.py` 的 `parse_turns()` 和 `_index_single_turn()` | 把 `user_message + assistant_reply` 作为一条可检索记忆 |
| 摘要 + 标签结构化治理 | `extract_summary_and_tags()` | LLM 把原始对话提炼为 `summary` 和 `tags` |
| 向量只是普通列 | `schema.sql` | `summary_vec`、`message_vec` 与标量字段在同一张表 |
| 混合检索 | `search.py` | `0.7 * vector_score + 0.3 * fulltext_score` |
| 生产可重跑 | `ON CONFLICT DO NOTHING` | 稳定 ID + 幂等插入 |
| 后台索引不阻塞用户 | `run_and_index()` + `async_index_turn()` | `asyncio.create_task()` 后台触发 |

## 2. 总体处理链路

完整链路可以分成 8 个阶段：

```text
用户消息
  -> Crew 主流程执行
  -> before_llm_call 恢复历史上下文、剪枝、压缩
  -> LLM / 工具生成助手回复
  -> 保存 session 原始记录和上下文快照
  -> 后台触发 async_index_turn
  -> 提取 summary/tags + embedding + 写入 memories 表
  -> 用户后续查询时 search_memory 调用 search.py 检索 memories
  -> Agent 利用召回结果组织最终回答
```

这个设计把“对话服务”和“长期记忆治理”解耦：

- 用户对话先返回，索引后台做。
- 原始对话保存在 session 文件里，便于审计和恢复。
- 检索型长期记忆保存在 pgvector 表里，便于按需召回。
- `SKILL.md` 负责教 Agent 什么时候查、怎么查、查不到怎么降级。

## 3. 入口：`m3l21_search_memory.py`

### 3.1 演示输入数据

入口文件里定义了三轮演示：

```python
SESSION_ID   = "demo_m3l21"
ROUTING_KEY  = "p2p:ou_demo"

DEMO_ROUNDS = [
    (
        "普通任务（建索引）",
        "帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。",
    ),
    (
        "普通任务（建索引）",
        "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
    ),
    (
        "语义搜索（跨 session 召回）",
        "我之前让你查过一个向量数据库的对比，帮我找一下那次的结论。不要只凭当前对话上下文回忆，必须调用 search_memory Skill，从 pgvector 历史记忆中检索并给出结果。",
    ),
]
```

这里已经把用户数据分成两类：

| 数据 | 作用 | 后续去向 |
| --- | --- | --- |
| `session_id = demo_m3l21` | 标识同一次连续会话 | session 文件、数据库 `session_id` |
| `routing_key = p2p:ou_demo` | 标识用户或聊天通道 | 数据库 `routing_key`，检索时可做用户隔离 |
| `user_message` | 当前用户请求 | 进入 Crew、session、索引器、数据库 |
| `assistant_reply` | 运行后才产生 | 进入 session、索引器、数据库 |

### 3.2 初始化阶段的数据状态

每轮都会构造一个新的 `XiaoPawCrew`：

```python
def __init__(self, session_id: str, user_message: str, routing_key: str = "p2p:demo") -> None:
    self.session_id      = session_id
    self.user_message    = user_message
    self.routing_key     = routing_key
    self._session_loaded = False
    self._last_msgs: list[dict] = []
    self._history_len    = 0
    self._turn_start_ts  = int(time.time() * 1000)
```

进入 Crew 前，单轮用户数据大概是：

```json
{
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "turn_start_ts": 1773925080000,
  "assistant_reply": null,
  "session_loaded": false,
  "last_msgs": []
}
```

这里的 `turn_start_ts` 是治理长期记忆的关键字段之一。后续生成稳定 ID 时，它会和 `session_id`、`user_message[:32]` 一起参与哈希，避免重复写入。

## 4. Bootstrap：把文件系统记忆作为轻量入口

`build_bootstrap_prompt()` 读取 m3l20 的 workspace：

```python
WORKSPACE_DIR = _M3L21_DIR.parent / "m3l20" / "workspace"
SESSIONS_DIR  = WORKSPACE_DIR / "sessions"
```

实际加载逻辑：

```python
def build_bootstrap_prompt(workspace_dir: Path) -> str:
    parts: list[str] = []
    for fname, tag in [
        ("soul.md",  "soul"),
        ("user.md",  "user_profile"),
        ("agent.md", "agent_rules"),
    ]:
        path = workspace_dir / fname
        if path.exists():
            parts.append(f"<{tag}>\n{path.read_text(encoding='utf-8').strip()}\n</{tag}>")

    memory_path = workspace_dir / "memory.md"
    if memory_path.exists():
        lines = memory_path.read_text(encoding="utf-8").splitlines()[:200]
        parts.append(f"<memory_index>\n{chr(10).join(lines)}\n</memory_index>")

    return "\n\n".join(parts)
```

### 数据状态

文件数据进入 LLM 前变成一个系统提示片段：

```text
<soul>
XiaoPaw 身份设定...
</soul>

<user_profile>
用户档案：晓寒...
</user_profile>

<agent_rules>
Agent 工作规范...
</agent_rules>

<memory_index>
memory.md 前 200 行...
</memory_index>
```

执行日志 `agent.log.wf` 也验证了这一点：LLM 收到的第一条 system message 包含 `<soul>`、`<user_profile>`、`<agent_rules>` 和 `<memory_index>`。这说明 m3l21 没有抛弃 m3l20 的文件系统记忆，而是把它降级为“启动提示 + 指针索引”，长期细节交给搜索系统。

## 5. before_llm_call：上下文恢复、剪枝与压缩

每次 LLM 调用前都会进入 hook：

```python
@before_llm_call
def before_llm_hook(self, context: LLMCallHookContext) -> bool | None:
    if not self._session_loaded:
        self._restore_session(context)
        self._session_loaded = True
    self._last_msgs = context.messages
    prune_tool_results(context.messages)
    maybe_compress(context.messages, context)
    return None
```

### 5.1 情况 A：新 session，没有历史上下文

`load_session_ctx()` 找不到 `demo_m3l21_ctx.json` 时返回空列表：

```python
def load_session_ctx(session_id: str, sessions_dir: Path = SESSIONS_DIR) -> list[dict]:
    p = sessions_dir / f"{session_id}_ctx.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))
```

此时上下文只包含：

```json
[
  {
    "role": "system",
    "content": "<soul>...</soul>\n\n<user_profile>...</user_profile>..."
  },
  {
    "role": "user",
    "content": "Current Task: 帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。..."
  }
]
```

治理动作：

- 不恢复历史。
- 不剪枝，因为轮次少。
- 不压缩，因为 token 占用低于阈值。

### 5.2 情况 B：已有 session，需要恢复历史

如果 `demo_m3l21_ctx.json` 存在，`_restore_session()` 会先加载历史，再把当前用户消息接在末尾：

```python
def _restore_session(self, context: LLMCallHookContext) -> None:
    history = load_session_ctx(self.session_id)
    self._history_len = len(history)
    if not history:
        return
    current_user_msg = next(
        (m for m in reversed(context.messages) if m.get("role") == "user"), {}
    )
    context.messages.clear()
    context.messages.extend(history)
    if current_user_msg:
        context.messages.append(current_user_msg)
```

恢复后数据状态：

```json
[
  {"role": "system", "content": "历史 system/bootstrap"},
  {"role": "user", "content": "上一轮任务"},
  {"role": "assistant", "content": "上一轮回答"},
  {"role": "user", "content": "当前任务"}
]
```

这解决的是短期连续对话，而不是长期搜索。长期记忆仍然靠 pgvector 检索。

### 5.3 情况 C：工具结果过多，需要剪枝

`prune_tool_results()` 只保留最近 10 轮用户上下文里的工具结果，旧工具结果内容被替换成 `[已剪枝]`：

```python
def prune_tool_results(messages: list[dict], keep_turns: int = PRUNE_KEEP_TURNS) -> None:
    user_indices = [i for i, m in enumerate(messages) if m.get("role") == "user"]
    if len(user_indices) <= keep_turns:
        return
    cutoff_idx = user_indices[-keep_turns]
    for i in range(cutoff_idx):
        if messages[i].get("role") == "tool":
            messages[i]["content"] = "[已剪枝]"
```

执行日志中可以看到大量工具结果已经变成：

```json
{
  "role": "tool",
  "name": "search_web",
  "content": "[已剪枝]"
}
```

治理目的：

- 工具原始结果可能很长，不适合永久占用 LLM 上下文。
- 旧工具结果如果已经沉淀成助手结论，继续保留原始工具输出收益不大。
- 长期可检索信息由后台索引保存，不靠上下文硬塞。

### 5.4 情况 D：上下文太长，需要压缩

`maybe_compress()` 通过粗略 token 估算决定是否压缩：

```python
model_limit   = getattr(context.llm, "context_window_size", MODEL_CTX_LIMIT)
approx_tokens = sum(len(str(m.get("content", ""))) // 2 for m in messages)
if approx_tokens / model_limit < compress_threshold:
    return
```

超过阈值后，它把旧消息切 chunk、摘要化，只保留最近 10 轮原文：

```python
summary_msgs = [
    {"role": "system", "content": f"<context_summary>\n{_summarize_chunk(chunk)}\n</context_summary>"}
    for chunk in chunks
]
messages.clear()
messages.extend(system_msgs + summary_msgs + fresh_msgs)
```

压缩后的上下文状态：

```json
[
  {"role": "system", "content": "<soul>...</soul>"},
  {"role": "system", "content": "<context_summary>旧对话摘要...</context_summary>"},
  {"role": "user", "content": "最近第 1 轮"},
  {"role": "assistant", "content": "最近第 1 轮回答"},
  {"role": "user", "content": "当前任务"}
]
```

这对应笔记里的“Bootstrap 注意力预算”思想：上下文只服务当前推理，不承担完整历史仓库职责。

## 6. 主流程执行：用户请求如何变成助手回复

核心方法是 `run_and_index()`：

```python
async def run_and_index(self) -> str:
    result = self.crew().kickoff(inputs={"user_request": self.user_message})

    if self._last_msgs:
        new_msgs = list(self._last_msgs)[self._history_len:]
        append_session_raw(self.session_id, new_msgs)
        save_session_ctx(self.session_id, list(self._last_msgs))

    assistant_reply = result.raw
    asyncio.create_task(
        async_index_turn(
            session_id      = self.session_id,
            routing_key     = self.routing_key,
            user_message    = self.user_message,
            assistant_reply = assistant_reply,
            turn_ts         = self._turn_start_ts,
        )
    )

    return assistant_reply
```

这个函数做了三件事：

1. 执行 Crew，得到 `assistant_reply`。
2. 保存短期 session 文件。
3. 后台触发长期记忆索引。

### 6.1 Round 1：普通任务，产生可索引记忆

用户输入：

```text
帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。
```

日志 `agent.log` 中显示 Agent 使用搜索工具后生成回答，核心内容是 Qwen3 更新摘要。

此时主流程产出的数据状态：

```json
{
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。",
  "assistant_reply": "✅ **Qwen3 模型近期更新动态完整摘要如下**：...",
  "turn_ts": 1773925080000
}
```

### 6.2 Round 2：普通任务，产生第二条可索引记忆

用户输入：

```text
我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。
```

助手回复是 pgvector 与 Qdrant 的对比表格和选型建议。这个回复后续应该被索引成一条“向量数据库对比”的长期记忆。

主流程产出的数据状态：

```json
{
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
  "turn_ts": 1773925090000
}
```

### 6.3 Round 3：历史查询，应该触发 search_memory

用户输入：

```text
我之前让你查过一个向量数据库的对比，帮我找一下那次的结论。
不要只凭当前对话上下文回忆，必须调用 search_memory Skill，从 pgvector 历史记忆中检索并给出结果。
```

理想情况下，Agent 应该调用 `search_memory`，通过 query `"向量数据库 对比 pgvector Qdrant"` 检索第二轮写入的记忆。

日志中的实际情况更有教学价值：`agent.log.wf` 显示 Agent 先尝试了 memory 相关 Skill，随后尝试调用 `search_memory`，但沙盒可用 Skill 列表里没有它，最终回复“无法调用 search_memory Skill”。这说明代码设计和当前执行环境之间存在部署偏差：

- 代码的 `M3L21_SANDBOX_MOUNT_DESC` 明确告诉 Agent：`../skills:/mnt/skills:ro` 包含 `search_memory`。
- 共享目录确实存在 `../crewai_mas_demo/skills/search_memory/SKILL.md`。
- 但日志里的 SkillLoader 实际可用列表只有 `pdf`、`docx`、`memory-save`、`skill-creator`、`memory-governance`。

所以实践链路里有两个分支：

| 分支 | 条件 | 结果 |
| --- | --- | --- |
| 理想分支 | 沙盒正确挂载 `../skills` 且 `MEMORY_DB_DSN` 可访问 | 调用 `search_memory`，从 pgvector 召回历史 |
| 日志实际分支 | 当前沙盒 SkillLoader 未暴露 `search_memory` | 无法执行检索，只能说明环境未部署 |

这不是工程思想失败，而是“能力文档存在，但运行时挂载/注册不一致”的环境治理问题。

## 7. session 文件：短期历史如何保存

`run_and_index()` 中的这段代码负责保存 session：

```python
if self._last_msgs:
    new_msgs = list(self._last_msgs)[self._history_len:]
    append_session_raw(self.session_id, new_msgs)
    save_session_ctx(self.session_id, list(self._last_msgs))
```

### 7.1 `append_session_raw()`：追加原始消息

```python
def append_session_raw(session_id: str, messages: list[dict], sessions_dir: Path = SESSIONS_DIR) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(sessions_dir / f"{session_id}_raw.jsonl", "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps({**msg, "ts": ts}, ensure_ascii=False) + "\n")
```

文件形态：

```jsonl
{"role":"user","content":"Current Task: ...","ts":"2026-03-19T20:58:02.123456"}
{"role":"assistant","content":"✅ **Qwen3 模型近期更新动态完整摘要如下**：...","ts":"2026-03-19T20:58:02.123456"}
```

治理作用：

- 只追加新增消息，不覆盖旧记录。
- 适合审计和离线重建索引。
- 但这里写入的是 CrewAI 上下文消息，不一定带 `type = message`，所以它和 `indexer.parse_turns()` 预期的 JSONL 格式不是完全同一种格式。

### 7.2 `save_session_ctx()`：保存上下文快照

```python
def save_session_ctx(session_id: str, messages: list[dict], sessions_dir: Path = SESSIONS_DIR) -> None:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / f"{session_id}_ctx.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
```

文件形态：

```json
[
  {"role": "system", "content": "<soul>...</soul>"},
  {"role": "user", "content": "Current Task: 帮我搜索一下最近 Qwen3 模型..."},
  {"role": "assistant", "content": "✅ **Qwen3 模型近期更新动态完整摘要如下**：..."}
]
```

治理作用：

- 用于下次同 session 恢复短期上下文。
- 保存的是“可直接喂回 LLM 的 message list”。
- 和 `raw.jsonl` 相比，它不是追加日志，而是当前上下文快照。

## 8. 长期记忆写入：`async_index_turn()` 到 `_index_single_turn()`

主流程返回前会创建后台任务：

```python
asyncio.create_task(
    async_index_turn(
        session_id      = self.session_id,
        routing_key     = self.routing_key,
        user_message    = self.user_message,
        assistant_reply = assistant_reply,
        turn_ts         = self._turn_start_ts,
    )
)
```

异步包装：

```python
async def async_index_turn(...):
    await asyncio.get_running_loop().run_in_executor(
        None,
        _index_single_turn,
        session_id, routing_key, user_message, assistant_reply, turn_ts,
    )
```

这里有一个很重要的工程细节：索引操作内部是同步数据库连接和同步 API 调用，所以不能直接写成普通 `await`。`run_in_executor()` 把同步阻塞工作丢到线程池，避免卡住事件循环。

### 8.1 输入状态

后台索引收到的是一条完整对话 turn：

```json
{
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
  "turn_ts": 1773925090000
}
```

### 8.2 稳定 ID：解决重复写入

`_index_single_turn()` 先生成稳定 ID：

```python
raw_id  = f"{session_id}_{turn_ts}_{user_message[:32]}"
turn_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
```

数据状态变成：

```json
{
  "raw_id": "demo_m3l21_1773925090000_我想了解一下 pgvector 和 Qdrant 的主要区别，",
  "id": "sha256(raw_id)[:16]"
}
```

然后检查数据库是否已有：

```python
cur.execute("SELECT 1 FROM memories WHERE id = %s", (turn_id,))
if cur.fetchone():
    return
```

这对应两种情况：

| 情况 | 数据状态 | 代码行为 |
| --- | --- | --- |
| 首次写入 | `memories` 不存在该 ID | 继续摘要、向量化、插入 |
| 重复运行 | `memories` 已存在该 ID | 直接返回，不重复写 |

这就是笔记里说的“幂等写入”。它让服务重启、网络抖动、手动重跑都不会污染长期记忆库。

### 8.3 摘要和标签：从原始对话到结构化元数据

提取函数：

```python
summary, tags = extract_summary_and_tags(user_message, assistant_reply)
```

Prompt 约束输出 JSON：

```python
_EXTRACT_PROMPT = """\
分析以下一轮对话，提取结构化信息，以 JSON 格式返回：

{{
  "summary": "一句话摘要，描述这轮对话做了什么（20字以内）",
  "tags": ["标签1", "标签2"]  // 2-4个领域标签，如：工作、文件处理、日程、搜索、代码等
}}

只返回 JSON，不要其他内容。

用户：{user_message}
助手：{assistant_reply}
"""
```

对于第二轮 pgvector/Qdrant 对比，理想提取结果可能是：

```json
{
  "summary": "对比 pgvector 和 Qdrant",
  "tags": ["代码", "向量数据库", "技术选型"]
}
```

此时数据状态：

```json
{
  "id": "稳定哈希",
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
  "summary": "对比 pgvector 和 Qdrant",
  "tags": ["代码", "向量数据库", "技术选型"],
  "turn_ts": 1773925090000
}
```

#### 异常情况：LLM 返回 Markdown 代码块

测试用例覆盖了 LLM 返回：

```text
<markdown fence: json>
{"summary": "PDF转换", "tags": ["文件处理"]}
<markdown fence end>
```

代码会去掉围栏：

```python
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
    raw = raw.strip()
```

治理结果：模型输出格式轻微不稳定时，仍能拿到结构化数据。

#### 异常情况：LLM 返回非法 JSON

代码兜底：

```python
except json.JSONDecodeError:
    return user_message[:50], []
```

数据状态：

```json
{
  "summary": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "tags": []
}
```

治理结果：

- 这条记忆仍会被写入。
- 向量搜索仍可用，因为 summary 至少是用户原文前 50 字。
- 标签过滤失效，因为 tags 为空。

## 9. 向量化：同一轮对话产生两个语义入口

代码：

```python
message_text  = f"用户：{user_message}\n助手：{assistant_reply}"
vecs          = embed_texts([summary, message_text])
search_text   = user_message + " " + " ".join(tags)
```

`embed_texts()`：

```python
resp = _embed_client.embeddings.create(
    model      = EMBED_MODEL,
    input      = texts,
    dimensions = EMBED_DIM,
)
return [item.embedding for item in resp.data]
```

输入：

```json
[
  "对比 pgvector 和 Qdrant",
  "用户：我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。\n助手：✅ **pgvector 与 Qdrant 主要区别完整对比如下**：..."
]
```

输出：

```json
[
  [0.0123, -0.0456, "... 共 1024 维"],
  [0.0311, 0.0098, "... 共 1024 维"]
]
```

两个向量的职责不同：

| 字段 | 来源 | 适合召回什么 |
| --- | --- | --- |
| `summary_vec` | 一句话摘要 | “上次那个向量数据库对比”这种概括性语义 |
| `message_vec` | 用户原话 + 助手完整回复 | 更细粒度的信息匹配，例如某个结论、文件路径、操作结果 |

当前 `search.py` 的排序主要使用 `summary_vec`。`schema.sql` 同时为 `message_vec` 建了 HNSW 索引，说明工程上预留了“摘要召回 + 原文召回”双通道。

## 10. 数据库写入：一条记忆在 `memories` 表中的最终状态

Schema：

```sql
CREATE TABLE IF NOT EXISTS memories (
    id              TEXT        PRIMARY KEY,
    session_id      TEXT        NOT NULL,
    routing_key     TEXT        NOT NULL,
    user_message    TEXT        NOT NULL,
    assistant_reply TEXT        NOT NULL,
    summary         TEXT        NOT NULL,
    tags            TEXT[]      NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    turn_ts         BIGINT      NOT NULL,
    summary_vec     vector(1024),
    message_vec     vector(1024),
    search_text     TEXT        NOT NULL DEFAULT '',
    search_tsv      TSVECTOR    GENERATED ALWAYS AS (to_tsvector('simple', search_text)) STORED
);
```

写入代码：

```python
cur.execute(
    """
    INSERT INTO memories (
        id, session_id, routing_key,
        user_message, assistant_reply,
        summary, tags,
        turn_ts,
        summary_vec, message_vec,
        search_text
    ) VALUES (
        %(id)s, %(session_id)s, %(routing_key)s,
        %(user_message)s, %(assistant_reply)s,
        %(summary)s, %(tags)s,
        %(turn_ts)s,
        %(summary_vec)s::vector, %(message_vec)s::vector,
        %(search_text)s
    )
    ON CONFLICT (id) DO NOTHING
    """,
    {
        **record,
        "summary_vec": str(record["summary_vec"]),
        "message_vec": str(record["message_vec"]),
    },
)
```

最终入库记录可以理解为：

```json
{
  "id": "e4b7a8c19d20f31a",
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
  "summary": "对比 pgvector 和 Qdrant",
  "tags": ["代码", "向量数据库", "技术选型"],
  "created_at": "数据库写入时间",
  "turn_ts": 1773925090000,
  "summary_vec": "[1024 维向量]",
  "message_vec": "[1024 维向量]",
  "search_text": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。 代码 向量数据库 技术选型",
  "search_tsv": "PostgreSQL 自动生成"
}
```

### `search_text` 和 `search_tsv` 的治理意义

应用层只写：

```text
search_text = user_message + " " + " ".join(tags)
```

数据库自动维护：

```sql
search_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('simple', search_text)) STORED
```

这就避免了两个常见问题：

- 应用层忘记更新全文索引列。
- 原始文本和索引文本不一致。

笔记里说“向量只是普通列，不是独立向量数据库”，在这里落到了最具体的工程形态：向量列、标签列、全文索引列、用户隔离字段都在同一张表。

## 11. 批量重建索引：`index_session()`

除了每轮后台索引，`indexer.py` 还提供了同步批量入口：

```python
def index_session(jsonl_path: Path) -> int:
    turns = parse_turns(jsonl_path)
    if not turns:
        return 0

    conn = psycopg2.connect(DB_DSN)
    written = 0

    try:
        for turn in turns:
            raw_id = f"{turn['session_id']}_{turn['turn_ts']}_{turn['user_message'][:32]}"
            turn_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
            ...
```

它面向的是“已有 session JSONL 离线重建索引”场景。

### 11.1 JSONL 输入格式

`parse_turns()` 期望的格式是：

```jsonl
{"type": "meta", "session_id": "s001", "routing_key": "p2p:ou_abc"}
{"type": "message", "role": "user", "content": "帮我查航班", "ts": 1000}
{"type": "message", "role": "assistant", "content": "已查到航班信息", "ts": 1001}
{"type": "message", "role": "user", "content": "帮我转PDF", "ts": 2000}
{"type": "message", "role": "assistant", "content": "转换完成", "ts": 2001}
```

输出 turns：

```json
[
  {
    "session_id": "s001",
    "routing_key": "p2p:ou_abc",
    "user_message": "帮我查航班",
    "assistant_reply": "已查到航班信息",
    "turn_ts": 1000
  },
  {
    "session_id": "s001",
    "routing_key": "p2p:ou_abc",
    "user_message": "帮我转PDF",
    "assistant_reply": "转换完成",
    "turn_ts": 2000
  }
]
```

### 11.2 不同数据情况

测试文件覆盖了四种输入情况：

| 情况 | 输入特征 | 输出 |
| --- | --- | --- |
| 正常两轮对话 | meta + user/assistant/user/assistant | 2 个 turn |
| 没有 meta | 只有 message | `routing_key = unknown`，`session_id = 文件名 stem` |
| 最后一条 user 没有 assistant | 尾部悬空问题 | 忽略未完成 turn |
| 空文件 | 无内容 | 返回 `[]` |

这体现了“数据治理不是只管 happy path”：索引器不会把未完成对话、空数据、缺 meta 的异常情况直接搞崩。

## 12. 检索利用：`search_memory` Skill 如何把记忆取回来

`SKILL.md` 给 Agent 的使用说明包括：

```bash
python /mnt/skills/search_memory/scripts/search.py \
  --query "用户的搜索意图" \
  --tags "工作,文件处理" \
  --days 7 \
  --limit 5 \
  --mode hybrid
```

它定义了三种场景：

| 用户问题 | 推荐模式 | 原因 |
| --- | --- | --- |
| “上次那个航班” | `vector` | 关键词不明确，靠语义相似度 |
| “PDF转换” | `fulltext` | 精确 token 明确 |
| “上周的工作文件” | `hybrid + days + tags` | 同时需要语义、时间、标签过滤 |
| “之前那个向量数据库对比” | `hybrid` 或 `vector` | “那个”是语义模糊，“向量数据库”又有关键词 |

### 12.1 查询参数进入 CLI

`search.py` CLI 解析：

```python
parser.add_argument("--query",       required=True,  help="搜索意图（自然语言）")
parser.add_argument("--tags",        default=None,   help="标签过滤，逗号分隔（如 工作,文件处理）")
parser.add_argument("--days",        type=int, default=None, help="时间范围，最近N天")
parser.add_argument("--routing_key", default=None,   help="限定用户")
parser.add_argument("--limit",       type=int, default=5, help="返回条数")
parser.add_argument("--mode",        default="hybrid", choices=["hybrid", "vector", "fulltext"])
```

例如用户问：

```text
我之前让你查过一个向量数据库的对比，帮我找一下那次的结论。
```

可以形成检索调用：

```bash
python /mnt/skills/search_memory/scripts/search.py \
  --query "向量数据库 pgvector Qdrant 对比" \
  --routing_key "p2p:ou_demo" \
  --limit 5 \
  --mode hybrid
```

进入 `search()` 后的数据：

```json
{
  "query": "向量数据库 pgvector Qdrant 对比",
  "tags": null,
  "days": null,
  "routing_key": "p2p:ou_demo",
  "limit": 5,
  "mode": "hybrid"
}
```

### 12.2 标量过滤：先缩小候选范围

代码：

```python
where_clauses = []
params: dict = {}

if tags:
    where_clauses.append("tags && %(tags)s")
    params["tags"] = tags

if days:
    where_clauses.append("created_at > NOW() - make_interval(days => %(days)s)")
    params["days"] = days

if routing_key:
    where_clauses.append("routing_key = %(routing_key)s")
    params["routing_key"] = routing_key
```

不同情况：

| 查询情况 | SQL 过滤 |
| --- | --- |
| 指定用户 | `routing_key = %(routing_key)s` |
| 指定最近 N 天 | `created_at > NOW() - make_interval(days => %(days)s)` |
| 指定标签 | `tags && %(tags)s` |
| 都不指定 | 全表按相关性排序 |

`tags && %(tags)s` 的含义是数组有交集。例如数据库 tags 是 `["代码", "向量数据库"]`，查询 tags 是 `["向量数据库", "工作"]`，这条记录会命中。

### 12.3 vector 模式：语义模糊召回

代码：

```sql
SELECT
    id, summary, user_message, assistant_reply, tags,
    created_at, turn_ts,
    1 - (summary_vec <=> %(query_vec)s::vector) AS score
FROM memories
{where_sql}
ORDER BY summary_vec <=> %(query_vec)s::vector
LIMIT %(limit)s
```

输入状态：

```json
{
  "query": "上次那个向量数据库对比",
  "query_vec": "[1024 维向量]",
  "mode": "vector"
}
```

输出状态：

```json
[
  {
    "id": "e4b7a8c19d20f31a",
    "summary": "对比 pgvector 和 Qdrant",
    "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
    "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
    "tags": ["代码", "向量数据库", "技术选型"],
    "created_at": "2026-03-19T20:58:20",
    "turn_ts": 1773925090000,
    "score": 0.89
  }
]
```

适合“上次那个”“之前聊过的”“那份材料”这类语义模糊问题。

### 12.4 fulltext 模式：精确关键词召回

代码：

```sql
SELECT
    id, summary, user_message, assistant_reply, tags,
    created_at, turn_ts,
    ts_rank(search_tsv, plainto_tsquery('simple', %(tsquery)s)) AS score
FROM memories
{where_sql}
{"AND" if where_clauses else "WHERE"} search_tsv @@ plainto_tsquery('simple', %(tsquery)s)
ORDER BY score DESC
LIMIT %(limit)s
```

输入状态：

```json
{
  "query": "PDF转换",
  "mode": "fulltext"
}
```

特点：

- 必须命中 `search_tsv @@ plainto_tsquery(...)`。
- 适合错误码、函数名、文件名、产品名等精确 token。
- 如果用户说“那个工具”“上次那个”，全文搜索可能失败，因为关键词不明确。

### 12.5 hybrid 模式：生产默认路径

代码：

```sql
SELECT
    id, summary, user_message, assistant_reply, tags,
    created_at, turn_ts,
    (
        0.7 * (1 - (summary_vec <=> %(query_vec)s::vector))
        + 0.3 * ts_rank(search_tsv, plainto_tsquery('simple', %(tsquery)s))
    ) AS score
FROM memories
{where_sql}
ORDER BY score DESC
LIMIT %(limit)s
```

输入：

```json
{
  "query": "向量数据库 pgvector Qdrant 对比",
  "mode": "hybrid",
  "query_vec": "[1024 维向量]",
  "tsquery": "向量数据库 pgvector Qdrant 对比"
}
```

打分含义：

```text
score = 0.7 * 摘要语义相似度 + 0.3 * 全文关键词得分
```

它实现了笔记中“向量 + 标量 + 全文，一条 SQL 搞定”的设计。查询结果不是先查向量库、再回查数据库，而是在 `memories` 表里一次取出完整可用数据。

### 12.6 输出序列化：给 Agent 可读 JSON

搜索完成后：

```python
for r in results:
    if r.get("created_at"):
        r["created_at"] = r["created_at"].isoformat()
    if r.get("score") is not None:
        r["score"] = round(float(r["score"]), 4)
```

最终打印：

```python
print(json.dumps(results, ensure_ascii=False, indent=2))
```

输出形态：

```json
[
  {
    "id": "e4b7a8c19d20f31a",
    "summary": "对比 pgvector 和 Qdrant",
    "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
    "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
    "tags": ["代码", "向量数据库", "技术选型"],
    "created_at": "2026-03-19T20:58:20.123456+08:00",
    "turn_ts": 1773925090000,
    "score": 0.9132
  }
]
```

Agent 重点使用：

- `summary`：判断哪条结果最相关。
- `assistant_reply`：恢复当时完整结论。
- `user_message`：确认用户当时问的是什么。
- `score`：辅助排序和置信度判断。
- `tags` / `created_at`：解释来源和范围。

## 13. 空结果与降级策略

`SKILL.md` 明确写了搜索为空时的放宽顺序：

```text
1. 先去掉 --days 限制（时间范围可能太窄）
2. 再去掉 --tags 限制（标签可能不匹配）
3. 最后切换到 --mode vector 纯语义搜索（关键字可能不准）
```

这是一个典型的数据治理策略：不是一次查不到就结束，而是按“约束强度”逐步放松。

### 情况 A：时间范围太窄

第一次：

```bash
python search.py --query "向量数据库对比" --days 7 --mode hybrid
```

结果为空，说明可能不是最近 7 天。

第二次：

```bash
python search.py --query "向量数据库对比" --mode hybrid
```

治理含义：时间过滤是硬约束，先去掉它扩大候选集。

### 情况 B：标签不匹配

第一次：

```bash
python search.py --query "pgvector Qdrant" --tags "数据库" --mode hybrid
```

如果索引时标签被提取成 `["代码", "技术选型"]`，就会因为 `tags &&` 不相交而查不到。

第二次：

```bash
python search.py --query "pgvector Qdrant" --mode hybrid
```

治理含义：标签是 LLM 提取结果，有概率不稳定，所以不能作为最后兜底。

### 情况 C：关键词不准

第一次：

```bash
python search.py --query "之前那个数据库方案" --mode fulltext
```

如果 `search_text` 里没有“方案”，全文模式可能无结果。

第二次：

```bash
python search.py --query "之前那个数据库方案" --mode vector
```

治理含义：当用户表达模糊时，语义向量比关键词更可靠。

## 14. 日志里的实际执行分支：代码设计和环境状态的差异

执行日志展示了一个重要事实：第三轮用户明确要求调用 `search_memory`，但实际环境没有成功暴露该 Skill。

日志片段的关键结论：

```text
错误：未找到 Skill 'search_memory'，可用：['pdf', 'docx', 'memory-save', 'skill-creator', 'memory-governance']
```

最后 LLM 回复：

```text
无法调用 search_memory Skill，因其未在可用技能列表中...
工作区中不存在持久化的 pgvector 对比历史记录...
此前提供的对比内容仅来自当前对话上下文，未被保存至记忆系统。
```

这说明当前日志走的是“环境未完整部署”的分支：

| 阶段 | 代码预期 | 日志实际 |
| --- | --- | --- |
| Skill 发现 | `/mnt/skills/search_memory/SKILL.md` 可读并可执行 | 文件描述被读到，但 SkillLoader 可用列表不含 `search_memory` |
| 检索执行 | 调用 `scripts/search.py` 查询 pgvector | 未执行 search.py |
| 结果利用 | 用 `assistant_reply` 恢复 pgvector/Qdrant 对比 | 只能说明无法检索 |

这对工程实践有一个很现实的提醒：长期记忆系统不只要写代码，还要治理运行环境。

需要同时满足：

1. pgvector 容器启动。
2. `schema.sql` 已执行。
3. `MEMORY_DB_DSN` 在主进程和沙盒中都可用。
4. `QWEN_API_KEY` 在主进程和沙盒中都可用。
5. `../skills` 正确挂载到 `/mnt/skills`。
6. SkillLoader 的可用 Skill 列表包含 `search_memory`。

## 15. 不同用户数据在链路中的状态总表

### 15.1 普通新任务

以 Qwen3 更新查询为例：

| 阶段 | 数据形态 | 示例 |
| --- | --- | --- |
| 用户输入 | 自然语言 | `帮我搜索一下最近 Qwen3 模型的更新动态，整理成摘要。` |
| Crew task | `Current Task: ...` | 被包装成任务描述 |
| LLM 上下文 | system + user + tool | Bootstrap + 当前任务 + 搜索工具结果 |
| 助手回复 | Markdown 结论 | Qwen3 更新摘要 |
| session raw | JSONL 追加 | user / assistant / tool messages |
| session ctx | JSON 快照 | 当前完整 message list |
| 索引输入 | turn dict | `user_message + assistant_reply` |
| 结构化治理 | summary + tags | `总结 Qwen3 更新`，`["搜索", "模型"]` |
| 向量治理 | 2 个 1024 维向量 | `summary_vec`、`message_vec` |
| 数据库 | `memories` 一行 | 可被后续语义或全文召回 |

### 15.2 技术对比任务

以 pgvector/Qdrant 对比为例：

| 阶段 | 数据形态 | 示例 |
| --- | --- | --- |
| 用户输入 | 自然语言 | `我想了解一下 pgvector 和 Qdrant 的主要区别...` |
| 助手回复 | 对比表格 | pgvector vs Qdrant |
| summary | 概括语义 | `对比 pgvector 和 Qdrant` |
| tags | 领域过滤 | `["向量数据库", "技术选型", "代码"]` |
| search_text | 全文索引源 | `我想了解... pgvector Qdrant ... 向量数据库 技术选型` |
| summary_vec | 语义入口 | 召回“上次那个向量数据库对比” |
| assistant_reply | 结果复用 | 直接恢复完整表格和建议 |

### 15.3 历史模糊查询

用户输入：

```text
我之前让你查过一个向量数据库的对比，帮我找一下那次的结论。
```

理想检索过程：

| 阶段 | 数据形态 | 示例 |
| --- | --- | --- |
| 用户意图 | 模糊历史查询 | `之前`、`一个向量数据库的对比` |
| Skill 选择 | `search_memory` | 因为用户问过去发生的事 |
| 查询词 | 自然语言 query | `向量数据库 pgvector Qdrant 对比` |
| 检索模式 | hybrid 或 vector | 语义 + 关键词 |
| 召回记录 | JSON 数组 | 包含第二轮 `assistant_reply` |
| 回答生成 | 复用历史结论 | 给出当时 pgvector/Qdrant 对比表 |

### 15.4 重复索引

| 阶段 | 数据状态 | 代码处理 |
| --- | --- | --- |
| 输入 | 相同 `session_id + turn_ts + user_message[:32]` | 生成相同 `turn_id` |
| DB 检查 | `SELECT 1 FROM memories WHERE id = %s` 命中 | 直接 return |
| 插入保护 | 即使并发走到 INSERT | `ON CONFLICT DO NOTHING` 二次保护 |

### 15.5 不完整 session JSONL

| 情况 | 输入 | 输出 |
| --- | --- | --- |
| 缺 meta | 无 `type=meta` 行 | `routing_key = unknown` |
| 尾部 user 未回答 | 最后一条只有 user | 不生成 turn |
| 空文件 | 无 JSONL | `[]` |
| 非数字 ts | ISO 字符串 | `turn_ts = 0` |

这里有一个代码层面的细节：`parse_turns()` 对非数字 `ts` 直接转成 0。这能保证不崩，但会降低 ID 唯一性。因为 m3l21 的在线索引用 `_turn_start_ts`，不受这个问题影响；离线重建 m3l20 风格 JSONL 时，需要注意 ISO 时间戳可能都变成 0。

## 16. 测试如何证明数据治理规则

`test_m3l21.py` 覆盖了主要治理规则：

| 测试 | 证明的规则 |
| --- | --- |
| `test_parse_turns_basic` | user + assistant 被配对成 turn |
| `test_parse_turns_no_meta` | 缺 meta 时可降级 |
| `test_parse_turns_trailing_user` | 未完成问题不入索引 |
| `test_parse_turns_empty` | 空输入返回空 |
| `test_extract_summary_and_tags_normal` | 正常 JSON 可解析 |
| `test_extract_summary_and_tags_markdown_wrapped` | Markdown 包裹 JSON 可清理 |
| `test_extract_summary_and_tags_invalid_json` | 非法 JSON 有兜底 |
| `test_embed_texts_returns_correct_shape` | embedding 维度固定 1024 |
| `test_upsert_memory_calls_execute` | 写入会执行 SQL 并 commit |
| `test_search_modes` | 三种模式都返回标准结果 |
| `test_async_index_turn_calls_single_turn` | 异步包装确实调用同步索引函数 |

测试里构造的 mock record 很清楚地展示了一条被治理后的记忆：

```python
record = {
    "id":              "test_id",
    "session_id":      "s001",
    "routing_key":     "p2p:ou_abc",
    "user_message":    "帮我查航班",
    "assistant_reply": "已查到",
    "summary":         "查航班",
    "tags":            ["出行"],
    "turn_ts":         1000,
    "summary_vec":     [0.1] * EMBED_DIM,
    "message_vec":     [0.2] * EMBED_DIM,
    "search_text":     "帮我查航班 出行",
}
```

这就是 m3l21 数据治理后的标准单元。

## 17. 这套代码如何真正实现“治理和利用”

### 治理

治理发生在写入链路：

1. **身份治理**：`routing_key` 把不同用户/会话通道隔离开。
2. **时间治理**：`turn_ts` 记录原始对话时间，`created_at` 记录入库时间。
3. **粒度治理**：一问一答为一个 chunk，避免只存用户问题导致语义缺失。
4. **结构化治理**：LLM 提取 `summary`、`tags`，把非结构化对话变成可过滤数据。
5. **语义治理**：`summary_vec`、`message_vec` 把文本变成可相似度计算的向量。
6. **全文治理**：`search_text` 和自动生成的 `search_tsv` 支持关键词检索。
7. **幂等治理**：稳定 ID + `ON CONFLICT DO NOTHING` 保证重复执行无副作用。
8. **上下文治理**：剪枝、压缩避免 LLM 上下文被旧工具结果拖垮。

### 利用

利用发生在读取链路：

1. 用户提出历史问题。
2. Agent 根据 `SKILL.md` 选择搜索模式。
3. `search.py` 将 query 向量化。
4. SQL 同时使用向量得分、全文得分、标量过滤。
5. 返回 `summary + user_message + assistant_reply + tags + score`。
6. Agent 用 `assistant_reply` 恢复历史结论，用 `summary` 和 `score` 判断相关性。

换句话说，m3l21 不是“把历史塞回 prompt”，而是把历史治理成一个可查询的数据资产。

## 18. 当前代码实践中的注意点

### 18.1 在线索引和离线 JSONL 解析的格式不完全一致

在线链路用：

```python
async_index_turn(session_id, routing_key, user_message, assistant_reply, turn_ts)
```

它直接拿当前轮次的干净数据建索引。

离线链路 `parse_turns()` 期待：

```json
{"type": "message", "role": "user", "content": "..."}
```

但 `append_session_raw()` 写的是 CrewAI 的 message dict，不一定有 `type = message`。所以生产里如果希望用 `index_session()` 重建 `append_session_raw()` 的文件，需要统一 JSONL 格式，或者增强 `parse_turns()` 兼容 CrewAI 原生消息。

### 18.2 `message_vec` 已建索引，但检索脚本目前主要用 `summary_vec`

`schema.sql` 建了：

```sql
CREATE INDEX IF NOT EXISTS memories_message_vec_idx
    ON memories USING hnsw (message_vec vector_cosine_ops);
```

但 `search.py` 的 vector 和 hybrid 排序都用 `summary_vec`。这说明当前实现偏向“摘要语义召回”，后续可以扩展为：

```text
score = 0.5 * summary_score + 0.2 * message_score + 0.3 * fulltext_score
```

### 18.3 日志显示 search_memory 部署没有打通

代码描述里 `search_memory` 应该在 `/mnt/skills/search_memory`。日志也读到了 Skill 文档内容，但 SkillLoader 的可用 Skill 列表不包含它。要让第三轮真正走 pgvector 检索，需要修正沙盒挂载或 SkillLoader 注册逻辑。

## 19. 用一条数据串起完整生命周期

以第二轮“pgvector vs Qdrant”为例，完整生命周期如下：

### Stage 1：用户输入

```json
{
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。"
}
```

### Stage 2：Crew 生成回复

```json
{
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：\n\n| 维度 | **pgvector** | **Qdrant** |..."
}
```

### Stage 3：session 持久化

```json
{
  "raw_jsonl": "追加 user/assistant/tool 消息",
  "ctx_json": "保存完整 message list 快照"
}
```

### Stage 4：后台索引输入

```json
{
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "user_message": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。",
  "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
  "turn_ts": 1773925090000
}
```

### Stage 5：结构化治理

```json
{
  "summary": "对比 pgvector 和 Qdrant",
  "tags": ["向量数据库", "技术选型", "代码"]
}
```

### Stage 6：向量和全文索引源

```json
{
  "summary_vec": "[1024 维]",
  "message_vec": "[1024 维]",
  "search_text": "我想了解一下 pgvector 和 Qdrant 的主要区别，帮我对比一下。 向量数据库 技术选型 代码"
}
```

### Stage 7：数据库行

```json
{
  "id": "稳定哈希",
  "session_id": "demo_m3l21",
  "routing_key": "p2p:ou_demo",
  "summary": "对比 pgvector 和 Qdrant",
  "tags": ["向量数据库", "技术选型", "代码"],
  "search_tsv": "由 PostgreSQL 自动生成",
  "assistant_reply": "完整历史结论"
}
```

### Stage 8：历史查询

```json
{
  "query": "之前那个向量数据库对比",
  "mode": "hybrid",
  "routing_key": "p2p:ou_demo"
}
```

### Stage 9：召回结果

```json
[
  {
    "summary": "对比 pgvector 和 Qdrant",
    "assistant_reply": "✅ **pgvector 与 Qdrant 主要区别完整对比如下**：...",
    "score": 0.9132
  }
]
```

### Stage 10：Agent 利用

最终回答不是“我猜之前聊过”，而是：

```text
我从历史记忆中找到了你之前的 pgvector 与 Qdrant 对比，结论如下：
...
```

这就是搜索驱动长期记忆的闭环。

## 20. 总结

`m3l21` 的代码实践把当前笔记里的工程思想落成了一个可执行的系统雏形：

- 用 m3l20 的文件系统继续承载 Bootstrap、用户画像、Agent 规则和轻量索引。
- 用 session 文件承载短期连续对话恢复和审计。
- 用后台索引把每轮对话治理成结构化、向量化、可全文检索的长期记忆。
- 用 pgvector 把标量过滤、全文索引、向量搜索放在同一张表里，避免两套系统同步。
- 用 `search_memory` Skill 把检索策略交给 Agent，让模型在任务层面自主选择搜索模式和降级策略。

当前执行日志也暴露了一个非常真实的工程问题：代码和文档已经准备好了 `search_memory`，但运行时 SkillLoader 没有把它暴露为可用 Skill。要让第三轮演示真正命中 pgvector，需要补齐沙盒挂载、环境变量和 Skill 注册。这个问题本身也说明，企业级记忆系统的治理对象不只是“用户数据”，还包括“工具可用性、运行时环境、索引任务、检索策略”这些工程状态。
