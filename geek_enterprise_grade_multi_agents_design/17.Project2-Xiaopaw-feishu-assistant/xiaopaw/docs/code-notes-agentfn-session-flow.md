# AgentFn 参数来源与 SessionManager 链路

本文说明 `xiaopaw/runner.py` 中 `AgentFn` 的参数含义、来源，以及它们和 `SessionManager` 的关系。

```python
AgentFn = Callable[[str, list[MessageEntry], str, str, str, bool], Awaitable[str]]
# 参数依次: user_message, history, session_id, routing_key, root_id, verbose
```

可以把这段代码理解成：`Runner` 规定了“真正 Agent 函数”必须接收哪些上下文。

也就是实际函数长这样：

```python
async def agent_fn(
    user_message: str,
    history: list[MessageEntry],
    session_id: str,
    routing_key: str,
    root_id: str,
    verbose: bool,
) -> str:
    ...
```

## 整体链路

1. 用户在飞书聊天框发消息。
2. 飞书 WebSocket 把消息事件推给 `FeishuListener`。
3. `FeishuListener` 解析飞书事件，构造 `InboundMessage`。
4. `InboundMessage` 被交给 `Runner.dispatch()`。
5. `Runner` 按 `routing_key` 排队，进入 `_handle()`。
6. `_handle()` 通过 `SessionManager` 找到当前 session，加载 history。
7. `_handle()` 调用 `self._agent_fn(user_content, history, session.id, inbound.routing_key, inbound.root_id, session.verbose)`。
8. Agent 返回 reply。
9. `SessionManager.append()` 把本轮用户消息和助手回复写入历史。
10. `FeishuSender` 根据 `routing_key` 和 `root_id` 把回复发回飞书。

关键代码在 `xiaopaw/runner.py`：

```python
reply = await self._agent_fn(
    user_content, history, session.id,
    inbound.routing_key, inbound.root_id, session.verbose,
)
```

对应代码位置：`xiaopaw/runner.py:187`。

## 关键代码位置索引

| 位置 | 作用 |
|---|---|
| `xiaopaw/runner.py:32` | 定义 `AgentFn` 类型别名 |
| `xiaopaw/runner.py:61` | `Runner.__init__()` 接收 `session_mgr`、`sender`、`agent_fn` |
| `xiaopaw/runner.py:80` | `Runner.dispatch()` 接收 `InboundMessage` 并按 `routing_key` 入队 |
| `xiaopaw/runner.py:149` | `Runner._handle()` 开始处理单条消息 |
| `xiaopaw/runner.py:159` | 通过 `SessionManager.get_or_create()` 获取当前 active session |
| `xiaopaw/runner.py:180` | 通过 `SessionManager.load_history()` 读取历史 |
| `xiaopaw/runner.py:187` | 调用 `self._agent_fn(...)`，把 6 个参数传给 Agent |
| `xiaopaw/runner.py:192` | 通过 `SessionManager.append()` 写入本轮历史 |
| `xiaopaw/runner.py:223` | `/new` 命令创建新 session |
| `xiaopaw/runner.py:227` | `/verbose` 命令修改 verbose 状态 |
| `xiaopaw/feishu/listener.py:98` | 根据飞书事件生成 `routing_key` |
| `xiaopaw/feishu/listener.py:105` | 从飞书消息 content 中提取纯文本 |
| `xiaopaw/feishu/listener.py:115` | 提取 `msg_id` |
| `xiaopaw/feishu/listener.py:116` | 提取 `root_id`，没有则使用 `msg_id` |
| `xiaopaw/feishu/listener.py:123` | 构造 `InboundMessage` |
| `xiaopaw/feishu/listener.py:137` | 调用 `on_message(inbound)`，实际进入 `Runner.dispatch()` |
| `xiaopaw/feishu/session_key.py:12` | `resolve_routing_key()` 的生成规则 |
| `xiaopaw/session/manager.py:32` | `get_or_create()`：根据 `routing_key` 获取或创建 active session |
| `xiaopaw/session/manager.py:55` | `create_new_session()`：创建并切换 active session |
| `xiaopaw/session/manager.py:88` | `load_history()`：按 `session_id` 读取历史 |
| `xiaopaw/session/manager.py:116` | `append()`：追加用户消息和助手回复 |
| `xiaopaw/session/models.py:8` | `SessionEntry` 数据结构 |
| `xiaopaw/session/models.py:26` | `MessageEntry` 数据结构 |
| `xiaopaw/main.py:126` | `build_agent_fn()` 构建真实 Agent 函数 |
| `xiaopaw/main.py:133` | 创建 `Runner` 并注入 `session_mgr`、`agent_fn` |
| `xiaopaw/main.py:149` | 创建 `FeishuListener` |
| `xiaopaw/main.py:152` | `on_message=runner.dispatch`，把 Listener 接到 Runner |
| `xiaopaw/agents/main_crew.py:211` | `build_agent_fn()` 工厂函数定义 |
| `xiaopaw/agents/main_crew.py:227` | 真正的 `agent_fn(...)` 闭包定义 |
| `xiaopaw/agents/main_crew.py:238` | 用 `session_id`、`routing_key`、history 构建 Crew |
| `xiaopaw/agents/main_crew.py:246` | 调用 `crew.akickoff()`，把 `user_message` 和格式化 history 交给 LLM |
| `xiaopaw/tools/skill_loader.py:122` | `SkillLoaderTool` 接收 `session_id`、`routing_key`、history |
| `xiaopaw/tools/skill_loader.py:304` | `history_reader` 从完整 history 中分页读取 |

## 参数来源

| AgentFn 参数 | 来源 | 含义 |
|---|---|---|
| `user_message` | `inbound.content`，或附件消息改写后的 `user_content` | 用户这次发来的消息内容 |
| `history` | `SessionManager.load_history(session.id)` | 当前 session 之前的聊天历史 |
| `session_id` | `SessionManager.get_or_create(key)` 返回的 `session.id` | 当前对话 ID，比如 `s-xxxx` |
| `routing_key` | `FeishuListener` 根据飞书事件解析出来 | 标识“哪个用户/群/话题”的路由键 |
| `root_id` | 飞书消息里的 `root_id`，没有则用 `msg_id` | 用来回复到正确消息或话题 |
| `verbose` | 当前 `SessionEntry.verbose` | 是否把 Agent 推理过程发回飞书 |

## routing_key 是什么

`routing_key` 是项目内部统一的“会话路由键”。生成规则在 `xiaopaw/feishu/session_key.py`：

```python
p2p:{sender_id}              # 单聊
group:{chat_id}              # 普通群聊
thread:{chat_id}:{thread_id} # 话题群
```

它有两个核心作用。

第一，`Runner` 用它做队列 key，保证同一个用户、群或话题的消息串行处理。

第二，`SessionManager` 用它找到当前 active session。

## session_id 是什么

`session_id` 是一次具体对话的 ID，比如 `s-abc123...`。

`routing_key` 表示“谁在聊”，`session_id` 表示“当前是哪一轮对话上下文”。

例如同一个用户当前正在一个对话里：

```text
routing_key = p2p:ou_xxx
active_session_id = s-001
```

用户发送 `/new` 后：

```text
routing_key = p2p:ou_xxx
active_session_id = s-002
```

也就是说，还是同一个人，但换了一个新的上下文。

创建新 session 的逻辑在 `Runner._handle_slash()` 和 `SessionManager.create_new_session()`。

## history 是什么

`history` 是当前 `session_id` 对应的历史消息列表，元素类型是 `MessageEntry`。

`MessageEntry` 定义在 `xiaopaw/session/models.py`：

```python
@dataclass(frozen=True)
class MessageEntry:
    """JSONL 中的一条对话消息"""

    role: str  # "user" | "assistant"
    content: str
    ts: int  # 毫秒时间戳
    feishu_msg_id: str | None = None
```

读取位置在 `Runner._handle()`：

```python
history = await self._session_mgr.load_history(session.id)
```

它的用途主要有两个。

第一，传给 CrewAI，让 Agent 知道前面聊过什么。

在 `xiaopaw/agents/main_crew.py` 中：

```python
inputs={
    "user_message": user_message,
    "history": _format_history(history, max_turns=max_history_turns),
}
```

第二，完整 history 会注入 `SkillLoaderTool`，供 `history_reader` skill 分页读取。

## root_id 是什么

`root_id` 来自飞书消息事件。解析位置在 `xiaopaw/feishu/listener.py`：

```python
root_id = message.get("root_id") or msg_id
```

普通消息可能没有 `root_id`，项目就用当前消息的 `msg_id`。

话题消息里，`root_id` 可以帮助机器人回复到对应话题。发送时 `FeishuSender` 会用到它，例如话题回复会调用 `_send_thread(root_id, ...)`。

## verbose 是什么

`verbose` 表示当前 session 是否开启详细模式。

用户可以通过 slash command 修改：

```text
/verbose on
/verbose off
```

`Runner._handle_slash()` 会调用：

```python
await self._session_mgr.update_verbose(key, True)
```

或：

```python
await self._session_mgr.update_verbose(key, False)
```

当 `verbose=True` 时，`build_agent_fn()` 会创建 step callback，把 Agent 中间推理步骤通过 `sender.send()` 发回飞书。

## SessionManager 的角色

`SessionManager` 做两件事。

第一，维护：

```text
routing_key -> active_session_id
```

也就是“这个用户、群或话题当前正在使用哪个 session”。

第二，维护每个：

```text
session_id -> JSONL 聊天历史
```

也就是“这个 session 里之前聊过什么”。

相关方法：

```python
get_or_create(routing_key)
```

获取当前 active session，不存在就创建。

```python
create_new_session(routing_key)
```

创建新 session，并把它切换成当前 active session。

```python
load_history(session_id)
```

读取当前 session 的历史消息。

```python
append(session_id, user=..., feishu_msg_id=..., assistant=...)
```

把本轮用户消息和助手回复追加到 JSONL。

## 用户消息到 AgentFn 参数的转换

以一条普通文本消息为例。

飞书事件中有这些信息：

```text
chat_type
chat_id
thread_id
sender.open_id
message.content
message.message_id
message.root_id
message.create_time
```

`FeishuListener` 先做解析：

```python
routing_key = resolve_routing_key(
    chat_type=chat_type,
    sender_id=sender_open_id,
    chat_id=chat_id,
    thread_id=thread_id,
)
```

再提取文本：

```python
content = FeishuListener._extract_content(
    message.get("message_type") or "",
    message.get("content") or "",
)
```

再构造 `InboundMessage`：

```python
inbound = InboundMessage(
    routing_key=routing_key,
    content=content,
    msg_id=msg_id,
    root_id=root_id,
    sender_id=sender_open_id,
    ts=ts,
    attachment=attachment,
)
```

然后交给 `Runner`：

```python
asyncio.run_coroutine_threadsafe(self._on_message(inbound), self._loop)
```

在主程序中，`on_message` 实际上传入的是：

```python
on_message=runner.dispatch
```

所以这条消息进入：

```python
Runner.dispatch(inbound)
```

`Runner.dispatch()` 按 `routing_key` 入队，worker 取出后调用：

```python
await self._handle(inbound)
```

`Runner._handle()` 中开始组装 AgentFn 参数：

```python
key = inbound.routing_key
session = await self._session_mgr.get_or_create(key)
user_content = inbound.content
history = await self._session_mgr.load_history(session.id)
```

最后调用：

```python
reply = await self._agent_fn(
    user_content,
    history,
    session.id,
    inbound.routing_key,
    inbound.root_id,
    session.verbose,
)
```

一句话总结：

`routing_key` 决定“这条消息属于哪个用户、群或话题”，`SessionManager` 用它找到当前 `session_id`，再用 `session_id` 读取 history，最后 `Runner` 把 `user_message + history + session_id + routing_key + root_id + verbose` 一起交给 Agent。
