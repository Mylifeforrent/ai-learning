# 消息流转示例：从飞书消息到 AgentFn 参数

本文用 mock 数据说明：用户在飞书聊天框输入消息后，项目如何一步步把它转换成 `InboundMessage`、`session_id`、`history`，最后传给 `AgentFn`。

相关核心代码位置：

| 位置 | 作用 |
|---|---|
| `xiaopaw/feishu/listener.py:52` | WebSocket 事件处理入口 `do_without_validation()` |
| `xiaopaw/feishu/listener.py:98` | 生成 `routing_key` |
| `xiaopaw/feishu/listener.py:105` | 提取文本内容 |
| `xiaopaw/feishu/listener.py:110` | 提取附件信息 |
| `xiaopaw/feishu/listener.py:115` | 提取 `msg_id` |
| `xiaopaw/feishu/listener.py:116` | 提取 `root_id`，没有则用 `msg_id` |
| `xiaopaw/feishu/listener.py:123` | 构造 `InboundMessage` |
| `xiaopaw/feishu/listener.py:137` | 调用 `on_message(inbound)` |
| `xiaopaw/main.py:152` | `on_message=runner.dispatch` |
| `xiaopaw/runner.py:80` | `Runner.dispatch()` 入队 |
| `xiaopaw/runner.py:149` | `Runner._handle()` 处理单条消息 |
| `xiaopaw/runner.py:159` | 通过 `SessionManager.get_or_create()` 获取 session |
| `xiaopaw/runner.py:180` | 通过 `SessionManager.load_history()` 读取历史 |
| `xiaopaw/runner.py:187` | 调用 `AgentFn` |
| `xiaopaw/runner.py:192` | 通过 `SessionManager.append()` 写入历史 |
| `xiaopaw/session/manager.py:32` | `get_or_create()` |
| `xiaopaw/session/manager.py:88` | `load_history()` |
| `xiaopaw/session/manager.py:116` | `append()` |
| `xiaopaw/agents/main_crew.py:227` | 真正的 `agent_fn(...)` 闭包 |
| `xiaopaw/agents/main_crew.py:246` | `crew.akickoff()` 把 `user_message` 和 `history` 传给 LLM |

## 基础概念

`AgentFn` 的类型定义在 `xiaopaw/runner.py:32`：

```python
AgentFn = Callable[[str, list[MessageEntry], str, str, str, bool], Awaitable[str]]
# 参数依次: user_message, history, session_id, routing_key, root_id, verbose
```

也就是实际 Agent 函数大致长这样：

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

这 6 个参数不是飞书原始事件里直接都有的。它们是在 `FeishuListener`、`Runner`、`SessionManager` 三层共同处理后拼出来的。

## 存储路径

配置文件里默认：

```yaml
data_dir: "./data"
```

读取位置是 `xiaopaw/main.py:72`：

```python
data_dir = Path(cfg.get("data_dir", "./data")).resolve()
```

如果项目从仓库根目录启动，那么默认数据目录可以理解为：

```text
{repo}/data
```

在当前项目中，也就是类似：

```text
/Users/macbookair/vscode-workspace/ai-learning/geek_enterprise_grade_multi_agents_design/17.Project2-Xiaopaw-feishu-assistant/xiaopaw/data
```

Session 相关文件：

```text
{data_dir}/sessions/index.json
{data_dir}/sessions/{session_id}.jsonl
```

附件本地存储路径：

```text
{data_dir}/workspace/sessions/{session_id}/uploads/{filename}
```

附件在沙盒内给 Agent 看的路径：

```text
/workspace/sessions/{session_id}/uploads/{filename}
```

## routing_key 规则

规则定义在 `xiaopaw/feishu/session_key.py:12`：

```python
def resolve_routing_key(
    chat_type: str,
    sender_id: str,
    chat_id: str,
    thread_id: str | None,
) -> str:
    if chat_type == "p2p":
        return f"p2p:{sender_id}"
    if thread_id:
        return f"thread:{chat_id}:{thread_id}"
    return f"group:{chat_id}"
```

也就是：

```text
单聊      p2p:{open_id}
普通群聊  group:{chat_id}
话题群    thread:{chat_id}:{thread_id}
```

`routing_key` 不是飞书原始字段，而是项目为了统一处理单聊、群聊、话题而生成的内部 key。

它主要有两个作用：

1. `Runner` 用它做队列维度，同一个 `routing_key` 的消息串行处理。
2. `SessionManager` 用它找到当前 active session。

## 场景一：单聊文本消息，第一次对话

用户在飞书单聊里输入：

```text
帮我总结一下今天的待办
```

飞书推来的 mock 原始事件可以简化成：

```json
{
  "header": {
    "event_type": "im.message.receive_v1"
  },
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_user_001"
      }
    },
    "message": {
      "chat_type": "p2p",
      "chat_id": "oc_unused_for_p2p",
      "thread_id": null,
      "message_type": "text",
      "content": "{\"text\":\"帮我总结一下今天的待办\"}",
      "message_id": "om_msg_001",
      "root_id": "",
      "create_time": "1736500000000"
    }
  }
}
```

### 第一步：FeishuListener 解析飞书事件

代码位置：`xiaopaw/feishu/listener.py:86` 到 `xiaopaw/feishu/listener.py:121`。

解析出来的关键变量：

```python
sender_open_id = "ou_user_001"
chat_type = "p2p"
chat_id = "oc_unused_for_p2p"
thread_id = None
msg_id = "om_msg_001"
root_id = "om_msg_001"  # 因为原始 root_id 为空，所以使用 msg_id
ts = 1736500000000
```

生成 `routing_key`：

```python
routing_key = resolve_routing_key(
    chat_type="p2p",
    sender_id="ou_user_001",
    chat_id="oc_unused_for_p2p",
    thread_id=None,
)
```

结果：

```text
routing_key = "p2p:ou_user_001"
```

提取文本：

```python
content = "帮我总结一下今天的待办"
```

提取附件：

```python
attachment = None
```

### 第二步：构造 InboundMessage

代码位置：`xiaopaw/feishu/listener.py:123`。

得到的对象等价于：

```python
InboundMessage(
    routing_key="p2p:ou_user_001",
    content="帮我总结一下今天的待办",
    msg_id="om_msg_001",
    root_id="om_msg_001",
    sender_id="ou_user_001",
    ts=1736500000000,
    is_cron=False,
    attachment=None,
)
```

然后 `FeishuListener` 调用：

```python
asyncio.run_coroutine_threadsafe(self._on_message(inbound), self._loop)
```

代码位置：`xiaopaw/feishu/listener.py:137`。

在主程序中，`on_message` 实际就是：

```python
on_message=runner.dispatch
```

代码位置：`xiaopaw/main.py:152`。

所以实际进入：

```python
await runner.dispatch(inbound)
```

### 第三步：Runner.dispatch 按 routing_key 入队

代码位置：`xiaopaw/runner.py:80`。

`Runner` 会用：

```python
key = inbound.routing_key
```

此时：

```text
key = "p2p:ou_user_001"
```

内部队列大致变成：

```python
self._queues = {
    "p2p:ou_user_001": Queue([
        InboundMessage(...)
    ])
}
```

如果这个 `routing_key` 还没有 worker，会创建一个 worker：

```python
self._workers = {
    "p2p:ou_user_001": Task(...)
}
```

含义：同一个单聊用户的消息一条一条处理，避免多条消息同时修改同一个 session 历史。

### 第四步：Runner._handle 获取 session

代码位置：`xiaopaw/runner.py:149` 到 `xiaopaw/runner.py:160`。

```python
key = inbound.routing_key
session = await self._session_mgr.get_or_create(key)
```

此时传入 `SessionManager.get_or_create()` 的参数：

```text
routing_key = "p2p:ou_user_001"
```

如果这是这个用户第一次聊天，`{data_dir}/sessions/index.json` 可能还不存在，或者里面没有这个 key。

`SessionManager` 会创建新 session，假设生成：

```text
session_id = "s-a1b2c3d4e5f6"
```

创建后，`index.json` 会变成：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-a1b2c3d4e5f6",
    "sessions": [
      {
        "id": "s-a1b2c3d4e5f6",
        "created_at": "2026-05-30T10:00:00+00:00",
        "verbose": false,
        "message_count": 0
      }
    ]
  }
}
```

文件路径：

```text
{data_dir}/sessions/index.json
```

同时会创建一个 JSONL 历史文件：

```text
{data_dir}/sessions/s-a1b2c3d4e5f6.jsonl
```

初始内容只有 meta 行：

```jsonl
{"type":"meta","session_id":"s-a1b2c3d4e5f6","routing_key":"p2p:ou_user_001","created_at":"2026-05-30T10:00:00+00:00"}
```

### 第五步：Runner 加载 history

代码位置：`xiaopaw/runner.py:180`。

```python
history = await self._session_mgr.load_history(session.id)
```

此时：

```text
session.id = "s-a1b2c3d4e5f6"
```

读取文件：

```text
{data_dir}/sessions/s-a1b2c3d4e5f6.jsonl
```

因为这是第一次对话，文件里只有 meta 行，没有 message 行，所以：

```python
history = []
```

### 第六步：Runner 调用 AgentFn

代码位置：`xiaopaw/runner.py:187`。

实际调用等价于：

```python
reply = await self._agent_fn(
    "帮我总结一下今天的待办",
    [],
    "s-a1b2c3d4e5f6",
    "p2p:ou_user_001",
    "om_msg_001",
    False,
)
```

也就是：

```text
user_message = "帮我总结一下今天的待办"
history = []
session_id = "s-a1b2c3d4e5f6"
routing_key = "p2p:ou_user_001"
root_id = "om_msg_001"
verbose = false
```

### 第七步：真实 agent_fn 如何使用这些参数

真实 `agent_fn` 在 `xiaopaw/agents/main_crew.py:227`。

它会构建 Crew：

```python
crew = _build_crew(
    session_id=session_id,
    routing_key=routing_key,
    history_all=history,
    step_callback=step_cb,
    sandbox_url=sandbox_url,
)
```

代码位置：`xiaopaw/agents/main_crew.py:238`。

然后调用 CrewAI：

```python
result = await crew.akickoff(
    inputs={
        "user_message": user_message,
        "history": _format_history(history, max_turns=max_history_turns),
    }
)
```

代码位置：`xiaopaw/agents/main_crew.py:246`。

对于第一次对话，传给 LLM 的 mock inputs 大致是：

```python
{
    "user_message": "帮我总结一下今天的待办",
    "history": "（无历史记录）"
}
```

注意：`session_id` 和 `routing_key` 主要注入到工具层，例如 `SkillLoaderTool`，不是作为 `crew.akickoff()` 的普通输入直接给 LLM。

### 第八步：Agent 返回后写入 history

假设 Agent 返回：

```text
当然可以，请把今天的待办发给我，或者上传相关文件。
```

`Runner` 调用：

```python
await self._session_mgr.append(
    session.id,
    user=user_content,
    feishu_msg_id=inbound.msg_id,
    assistant=reply,
)
```

代码位置：`xiaopaw/runner.py:192`。

写入文件：

```text
{data_dir}/sessions/s-a1b2c3d4e5f6.jsonl
```

写入后内容类似：

```jsonl
{"type":"meta","session_id":"s-a1b2c3d4e5f6","routing_key":"p2p:ou_user_001","created_at":"2026-05-30T10:00:00+00:00"}
{"type":"message","role":"user","content":"帮我总结一下今天的待办","ts":1780125601000,"feishu_msg_id":"om_msg_001"}
{"type":"message","role":"assistant","content":"当然可以，请把今天的待办发给我，或者上传相关文件。","ts":1780125601000}
```

同时 `index.json` 里的 `message_count` 会从 `0` 变成 `2`。

## 场景二：同一个单聊用户发第二条消息

用户继续输入：

```text
上午要写周报，下午要开项目会
```

飞书事件里的 `message_id` 变成：

```text
msg_id = "om_msg_002"
```

`routing_key` 仍然是：

```text
p2p:ou_user_001
```

`SessionManager.get_or_create("p2p:ou_user_001")` 会从 `index.json` 找到：

```text
active_session_id = "s-a1b2c3d4e5f6"
```

所以这次不会创建新 session。

`load_history("s-a1b2c3d4e5f6")` 会读取上一轮写入的两条 message，得到：

```python
history = [
    MessageEntry(
        role="user",
        content="帮我总结一下今天的待办",
        ts=1780125601000,
        feishu_msg_id="om_msg_001",
    ),
    MessageEntry(
        role="assistant",
        content="当然可以，请把今天的待办发给我，或者上传相关文件。",
        ts=1780125601000,
        feishu_msg_id=None,
    ),
]
```

调用 `AgentFn` 时变成：

```python
reply = await self._agent_fn(
    "上午要写周报，下午要开项目会",
    history,
    "s-a1b2c3d4e5f6",
    "p2p:ou_user_001",
    "om_msg_002",
    False,
)
```

传给 LLM 的 inputs 大致是：

```python
{
    "user_message": "上午要写周报，下午要开项目会",
    "history": "用户: 帮我总结一下今天的待办\n助手: 当然可以，请把今天的待办发给我，或者上传相关文件。"
}
```

这就是 `history` 的作用：让 Agent 知道“上午要写周报...”是在承接上一句“帮我总结待办”。

## 场景三：普通群聊消息

群里用户输入：

```text
@小爪 生成一份本周项目进展摘要
```

飞书事件简化如下：

```json
{
  "header": {
    "event_type": "im.message.receive_v1"
  },
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_alice"
      }
    },
    "message": {
      "chat_type": "group",
      "chat_id": "oc_group_001",
      "thread_id": null,
      "message_type": "text",
      "content": "{\"text\":\"@小爪 生成一份本周项目进展摘要\"}",
      "message_id": "om_group_msg_001",
      "root_id": "",
      "create_time": "1736500100000"
    }
  }
}
```

解析结果：

```text
sender_open_id = "ou_alice"
chat_type = "group"
chat_id = "oc_group_001"
thread_id = None
msg_id = "om_group_msg_001"
root_id = "om_group_msg_001"
```

生成：

```text
routing_key = "group:oc_group_001"
```

构造 `InboundMessage`：

```python
InboundMessage(
    routing_key="group:oc_group_001",
    content="@小爪 生成一份本周项目进展摘要",
    msg_id="om_group_msg_001",
    root_id="om_group_msg_001",
    sender_id="ou_alice",
    ts=1736500100000,
    is_cron=False,
    attachment=None,
)
```

如果这是这个群第一次使用机器人，`SessionManager` 创建：

```text
session_id = "s-g001aabbccdd"
```

`index.json`：

```json
{
  "group:oc_group_001": {
    "active_session_id": "s-g001aabbccdd",
    "sessions": [
      {
        "id": "s-g001aabbccdd",
        "created_at": "2026-05-30T10:03:00+00:00",
        "verbose": false,
        "message_count": 0
      }
    ]
  }
}
```

对应历史文件：

```text
{data_dir}/sessions/s-g001aabbccdd.jsonl
```

调用 `AgentFn`：

```python
reply = await self._agent_fn(
    "@小爪 生成一份本周项目进展摘要",
    [],
    "s-g001aabbccdd",
    "group:oc_group_001",
    "om_group_msg_001",
    False,
)
```

群聊需要特别注意：

```text
routing_key = group:{chat_id}
```

不是：

```text
group:{sender_open_id}
```

所以同一个群里的不同用户，只要都在普通群聊里触发机器人，会共享这个群的 active session。

例如群里另一个用户 `ou_bob` 接着发消息，仍然会进入：

```text
routing_key = "group:oc_group_001"
session_id = "s-g001aabbccdd"
```

## 场景四：话题群消息

用户在群话题里输入：

```text
继续补充：风险点是供应商延期
```

飞书事件简化如下：

```json
{
  "header": {
    "event_type": "im.message.receive_v1"
  },
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_alice"
      }
    },
    "message": {
      "chat_type": "group",
      "chat_id": "oc_group_001",
      "thread_id": "omt_thread_001",
      "message_type": "text",
      "content": "{\"text\":\"继续补充：风险点是供应商延期\"}",
      "message_id": "om_thread_msg_002",
      "root_id": "om_thread_root_001",
      "create_time": "1736500200000"
    }
  }
}
```

解析结果：

```text
chat_type = "group"
chat_id = "oc_group_001"
thread_id = "omt_thread_001"
msg_id = "om_thread_msg_002"
root_id = "om_thread_root_001"
```

生成：

```text
routing_key = "thread:oc_group_001:omt_thread_001"
```

构造 `InboundMessage`：

```python
InboundMessage(
    routing_key="thread:oc_group_001:omt_thread_001",
    content="继续补充：风险点是供应商延期",
    msg_id="om_thread_msg_002",
    root_id="om_thread_root_001",
    sender_id="ou_alice",
    ts=1736500200000,
    is_cron=False,
    attachment=None,
)
```

如果这是该话题第一次触发机器人，会创建独立 session：

```text
session_id = "s-t001aabbccdd"
```

`index.json` 中会出现：

```json
{
  "thread:oc_group_001:omt_thread_001": {
    "active_session_id": "s-t001aabbccdd",
    "sessions": [
      {
        "id": "s-t001aabbccdd",
        "created_at": "2026-05-30T10:05:00+00:00",
        "verbose": false,
        "message_count": 0
      }
    ]
  }
}
```

调用 `AgentFn`：

```python
reply = await self._agent_fn(
    "继续补充：风险点是供应商延期",
    [],
    "s-t001aabbccdd",
    "thread:oc_group_001:omt_thread_001",
    "om_thread_root_001",
    False,
)
```

这里 `root_id` 很重要。

发送回复时，`FeishuSender` 会根据 `routing_key` 判断这是话题：

```python
elif routing_key.startswith("thread:"):
    await self._send_thread(root_id, msg_type, msg_content, root_id)
```

代码位置：`xiaopaw/feishu/sender.py:46`。

真正回复话题时会使用：

```python
ReplyMessageRequest.builder().message_id(root_id)
```

代码位置：`xiaopaw/feishu/sender.py:240`。

所以：

```text
root_id = "om_thread_root_001"
```

决定了机器人回复到哪个话题根消息下面。

## 场景五：用户上传文件

用户在单聊里上传文件，并备注：

```text
请分析这个 Excel
```

飞书事件简化如下：

```json
{
  "header": {
    "event_type": "im.message.receive_v1"
  },
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_user_001"
      }
    },
    "message": {
      "chat_type": "p2p",
      "chat_id": "oc_unused_for_p2p",
      "thread_id": null,
      "message_type": "file",
      "content": "{\"file_key\":\"file_v3_abc\",\"file_name\":\"sales.xlsx\"}",
      "message_id": "om_file_msg_001",
      "root_id": "",
      "create_time": "1736500300000"
    }
  }
}
```

`FeishuListener` 提取文本时：

```python
content = ""
```

因为 `_extract_content()` 只处理 `text` 和 `post`。

附件会被解析成：

```python
Attachment(
    msg_type="file",
    file_key="file_v3_abc",
    file_name="sales.xlsx",
)
```

构造 `InboundMessage`：

```python
InboundMessage(
    routing_key="p2p:ou_user_001",
    content="",
    msg_id="om_file_msg_001",
    root_id="om_file_msg_001",
    sender_id="ou_user_001",
    ts=1736500300000,
    is_cron=False,
    attachment=Attachment(
        msg_type="file",
        file_key="file_v3_abc",
        file_name="sales.xlsx",
    ),
)
```

进入 `Runner._handle()` 后，先获取 session：

```python
session = await self._session_mgr.get_or_create(key)
```

假设：

```text
session.id = "s-a1b2c3d4e5f6"
```

然后附件下载逻辑在 `xiaopaw/runner.py:162` 到 `xiaopaw/runner.py:178`。

下载到本地：

```text
{data_dir}/workspace/sessions/s-a1b2c3d4e5f6/uploads/sales.xlsx
```

代码位置：`xiaopaw/feishu/downloader.py:37`。

Agent 看到的是沙盒路径：

```text
/workspace/sessions/s-a1b2c3d4e5f6/uploads/sales.xlsx
```

`Runner` 会把 `user_content` 改写成：

```text
用户发来了文件，已自动保存至沙盒路径：
`/workspace/sessions/s-a1b2c3d4e5f6/uploads/sales.xlsx`
请根据文件内容和用户意图完成相应处理。
```

如果用户原始文本不为空，还会追加：

```text
用户备注：请分析这个 Excel
```

当前 Feishu file 事件本身在这份代码里没有从 content 提取备注；如果备注来自测试 API 或其他入口，才会被拼到 `original_text`。

最终调用 `AgentFn` 的 `user_message` 不是空字符串，而是改写后的文件提示：

```python
reply = await self._agent_fn(
    "用户发来了文件，已自动保存至沙盒路径：\n`/workspace/sessions/s-a1b2c3d4e5f6/uploads/sales.xlsx`\n请根据文件内容和用户意图完成相应处理。",
    history,
    "s-a1b2c3d4e5f6",
    "p2p:ou_user_001",
    "om_file_msg_001",
    False,
)
```

写入 JSONL 时，保存的也是改写后的 `user_content`。

## 场景六：用户发送 /new

用户输入：

```text
/new
```

这仍然会被 `FeishuListener` 构造成普通 `InboundMessage`：

```python
InboundMessage(
    routing_key="p2p:ou_user_001",
    content="/new",
    msg_id="om_cmd_msg_001",
    root_id="om_cmd_msg_001",
    sender_id="ou_user_001",
    ts=1736500400000,
    is_cron=False,
    attachment=None,
)
```

但在 `Runner._handle()` 中会先进入 slash command 拦截：

```python
slash_reply = await self._handle_slash(inbound)
if slash_reply is not None:
    await self._sender.send_text(key, slash_reply, inbound.root_id)
    return
```

代码位置：`xiaopaw/runner.py:153`。

`/new` 的逻辑：

```python
new_session = await self._session_mgr.create_new_session(key)
```

代码位置：`xiaopaw/runner.py:223`。

假设原来：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-a1b2c3d4e5f6",
    "sessions": [
      {
        "id": "s-a1b2c3d4e5f6",
        "created_at": "2026-05-30T10:00:00+00:00",
        "verbose": false,
        "message_count": 4
      }
    ]
  }
}
```

执行 `/new` 后：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-new12345678",
    "sessions": [
      {
        "id": "s-a1b2c3d4e5f6",
        "created_at": "2026-05-30T10:00:00+00:00",
        "verbose": false,
        "message_count": 4
      },
      {
        "id": "s-new12345678",
        "created_at": "2026-05-30T10:20:00+00:00",
        "verbose": false,
        "message_count": 0
      }
    ]
  }
}
```

新建文件：

```text
{data_dir}/sessions/s-new12345678.jsonl
```

内容：

```jsonl
{"type":"meta","session_id":"s-new12345678","routing_key":"p2p:ou_user_001","created_at":"2026-05-30T10:20:00+00:00"}
```

注意：`/new` 不会调用 `AgentFn`，也不会把 `/new` 写入聊天历史。它只是切换 active session，然后用 `send_text()` 回复用户。

下一条普通消息会进入新 session：

```text
session_id = "s-new12345678"
history = []
```

## 场景七：用户发送 /verbose on

用户输入：

```text
/verbose on
```

`Runner._handle_slash()` 会执行：

```python
await self._session_mgr.get_or_create(key)
await self._session_mgr.update_verbose(key, True)
```

代码位置：`xiaopaw/runner.py:227` 到 `xiaopaw/runner.py:231`。

`index.json` 中当前 active session 的 `verbose` 会变成：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-new12345678",
    "sessions": [
      {
        "id": "s-new12345678",
        "created_at": "2026-05-30T10:20:00+00:00",
        "verbose": true,
        "message_count": 0
      }
    ]
  }
}
```

注意：`/verbose on` 也不会调用 `AgentFn`，不会写入聊天历史。

下一条普通消息进入 `Runner._handle()` 时：

```python
session = await self._session_mgr.get_or_create(key)
```

拿到的：

```text
session.verbose = true
```

于是调用 `AgentFn` 时：

```python
reply = await self._agent_fn(
    user_content,
    history,
    session.id,
    inbound.routing_key,
    inbound.root_id,
    True,
)
```

在 `build_agent_fn()` 中，`verbose=True` 会创建 step callback：

```python
step_cb = (
    _make_step_callback(sender, routing_key, root_id) if verbose else None
)
```

代码位置：`xiaopaw/agents/main_crew.py:235`。

这个 callback 会把 Agent 的中间推理步骤发回飞书。

## 场景八：Test API 模拟消息

项目测试接口也会构造 `InboundMessage`。

代码位置：`xiaopaw/api/test_server.py:94`。

假设请求：

```json
{
  "routing_key": "p2p:ou_test_user",
  "sender_id": "ou_test_user",
  "content": "测试一下本地接口",
  "msg_id": "test_msg_001"
}
```

会构造：

```python
InboundMessage(
    routing_key="p2p:ou_test_user",
    content="测试一下本地接口",
    msg_id="test_msg_001",
    root_id="test_msg_001",
    sender_id="ou_test_user",
    ts=1780125600000,
)
```

注意这里没有经过飞书事件解析，所以 `routing_key` 是请求体里直接传进来的。

后续仍然进入：

```python
await runner.dispatch(inbound)
```

也就是说，从 `Runner` 往后的 session、history、AgentFn 参数组装逻辑和真实飞书消息一致。

## 完整状态变化总览

以单聊第一条文本消息为例，状态变化如下。

### 飞书原始事件

```json
{
  "chat_type": "p2p",
  "sender.open_id": "ou_user_001",
  "message.content": "{\"text\":\"帮我总结一下今天的待办\"}",
  "message.message_id": "om_msg_001",
  "message.root_id": ""
}
```

### FeishuListener 中间变量

```python
sender_open_id = "ou_user_001"
routing_key = "p2p:ou_user_001"
content = "帮我总结一下今天的待办"
msg_id = "om_msg_001"
root_id = "om_msg_001"
attachment = None
```

### InboundMessage

```python
InboundMessage(
    routing_key="p2p:ou_user_001",
    content="帮我总结一下今天的待办",
    msg_id="om_msg_001",
    root_id="om_msg_001",
    sender_id="ou_user_001",
    ts=1736500000000,
    is_cron=False,
    attachment=None,
)
```

### SessionManager 生成或读取 session

```python
session = SessionEntry(
    id="s-a1b2c3d4e5f6",
    created_at="2026-05-30T10:00:00+00:00",
    verbose=False,
    message_count=0,
)
```

### history

第一次消息：

```python
history = []
```

第二次消息可能是：

```python
history = [
    MessageEntry(role="user", content="上一轮用户消息", ts=1780125601000, feishu_msg_id="om_msg_001"),
    MessageEntry(role="assistant", content="上一轮助手回复", ts=1780125601000, feishu_msg_id=None),
]
```

### AgentFn 调用

```python
reply = await self._agent_fn(
    "帮我总结一下今天的待办",
    [],
    "s-a1b2c3d4e5f6",
    "p2p:ou_user_001",
    "om_msg_001",
    False,
)
```

### 写入 JSONL 后

```jsonl
{"type":"meta","session_id":"s-a1b2c3d4e5f6","routing_key":"p2p:ou_user_001","created_at":"2026-05-30T10:00:00+00:00"}
{"type":"message","role":"user","content":"帮我总结一下今天的待办","ts":1780125601000,"feishu_msg_id":"om_msg_001"}
{"type":"message","role":"assistant","content":"当然可以，请把今天的待办发给我，或者上传相关文件。","ts":1780125601000}
```

## 最核心的一句话

用户消息不是直接传给 Agent。

它先被 `FeishuListener` 标准化成 `InboundMessage`，再由 `Runner` 根据 `routing_key` 找到当前 `session_id`，通过 `session_id` 读取 history，最后组装成：

```python
user_message, history, session_id, routing_key, root_id, verbose
```

这 6 个参数一起传给 `AgentFn`。

## 补充：同一个用户隔天发消息会创建新 session 吗

不会。

按当前项目代码，同一个用户过一天再发消息，默认仍然会使用同一个 active `session_id`，不会因为跨天自动创建新 session。

原因是 `SessionManager.get_or_create(routing_key)` 只看这个 `routing_key` 是否已经存在，以及它当前的 `active_session_id` 是谁。它没有判断日期、超时时间、最后活跃时间之类的逻辑。

代码位置：`xiaopaw/session/manager.py:32`。

例如单聊用户第一天发消息：

```text
routing_key = p2p:ou_user_001
```

第一次出现时，`SessionManager` 创建：

```text
active_session_id = s-a1b2c3d4e5f6
```

`index.json` 中类似：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-a1b2c3d4e5f6",
    "sessions": [
      {
        "id": "s-a1b2c3d4e5f6",
        "created_at": "2026-05-29T10:00:00+00:00",
        "verbose": false,
        "message_count": 2
      }
    ]
  }
}
```

第二天同一个用户再发消息，`routing_key` 仍然是：

```text
p2p:ou_user_001
```

所以 `SessionManager.get_or_create("p2p:ou_user_001")` 会继续返回：

```text
session_id = s-a1b2c3d4e5f6
```

读取的历史文件仍然是：

```text
{data_dir}/sessions/s-a1b2c3d4e5f6.jsonl
```

也就是说，跨天不会自动清空上下文。

### idle_timeout 不等于 session 超时

`Runner` 中有一个 `idle_timeout`，默认配置是：

```yaml
runner:
  queue_idle_timeout_s: 300
```

它对应 `Runner.__init__()` 的：

```python
idle_timeout: float = 300.0
```

代码位置：`xiaopaw/runner.py:66`。

这个超时只影响 `Runner` 内存里的 worker：

```python
inbound = await asyncio.wait_for(
    queue.get(), timeout=self._idle_timeout
)
```

代码位置：`xiaopaw/runner.py:118`。

含义是：某个 `routing_key` 的队列空闲 300 秒后，这个 worker 会退出，释放内存。

它不会删除：

```text
{data_dir}/sessions/index.json
{data_dir}/sessions/{session_id}.jsonl
```

也不会创建新 session。

下一次同一个用户再发消息时，`Runner` 会重新创建 worker，但 `SessionManager` 仍然会从 `index.json` 找回原来的 active `session_id`。

## 当前项目什么时候会产生新的 session_id

当前代码里，新的 `session_id` 主要在以下情况产生。

### 情况一：某个 routing_key 第一次出现

代码位置：`xiaopaw/session/manager.py:36`。

如果 `index.json` 里没有这个 `routing_key`：

```python
if routing_key not in index:
    entry = self._make_new_session()
```

例如第一次收到：

```text
routing_key = p2p:ou_new_user
```

会创建：

```text
session_id = s-newuser001
```

并写入：

```text
{data_dir}/sessions/index.json
{data_dir}/sessions/s-newuser001.jsonl
```

### 情况二：用户发送 /new

代码位置：`xiaopaw/runner.py:223`。

```python
if cmd == "/new":
    new_session = await self._session_mgr.create_new_session(key)
```

`create_new_session()` 会为同一个 `routing_key` 新建 session，并切换为 active。

代码位置：`xiaopaw/session/manager.py:55`。

例如原来：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-old001",
    "sessions": [
      {
        "id": "s-old001",
        "created_at": "2026-05-29T10:00:00+00:00",
        "verbose": false,
        "message_count": 20
      }
    ]
  }
}
```

用户发送 `/new` 后：

```json
{
  "p2p:ou_user_001": {
    "active_session_id": "s-new002",
    "sessions": [
      {
        "id": "s-old001",
        "created_at": "2026-05-29T10:00:00+00:00",
        "verbose": false,
        "message_count": 20
      },
      {
        "id": "s-new002",
        "created_at": "2026-05-30T09:00:00+00:00",
        "verbose": false,
        "message_count": 0
      }
    ]
  }
}
```

后续消息会进入：

```text
session_id = s-new002
history = []
```

### 情况三：session 数据被清空后再次发消息

测试 API 支持清空 session。

代码位置：`xiaopaw/session/manager.py:165`。

```python
async def clear_all(self) -> None:
    ...
```

它会删除 session JSONL 文件，并清空 `index.json`。

清空后，同一个用户再发消息时，因为 `routing_key` 已经不在 `index.json` 中，所以会重新创建新 session。

### 情况四：未来代码新增自动切 session 规则

当前没有这类逻辑。

如果以后要实现“隔天自动新建 session”，通常需要在 `SessionManager.get_or_create()` 或 `Runner._handle()` 附近增加判断，例如：

```text
如果 active session 的 created_at 或 last_active_at 距离现在超过阈值，则 create_new_session(routing_key)
```

但当前 `SessionEntry` 只有：

```python
id
created_at
verbose
message_count
```

没有 `last_active_at` 字段。因此若要实现更自然的超时切 session，最好先扩展 session 元数据。

## 主流 session 管理思路

不同产品会根据交互方式选择不同的 session 策略。下面是常见几类。

### 思路一：显式新建 session

代表方式：

```text
用户点击“新对话”
用户发送 /new
```

当前项目就是这种思路。

优点：

```text
行为可预测，不会突然丢上下文。
```

缺点：

```text
如果用户忘记 /new，旧上下文可能一直影响后续对话。
```

适合：

```text
工作助手、命令型 Bot、需要稳定上下文的企业工具。
```

### 思路二：按空闲时间自动过期

例如：

```text
用户 30 分钟或 2 小时没有说话，下次消息自动进入新 session。
```

需要记录：

```text
last_active_at
```

判断逻辑类似：

```text
now - last_active_at > session_timeout
```

优点：

```text
比较符合“聊完一阵就结束”的自然体验。
```

缺点：

```text
用户隔一段时间回来想继续上文，可能发现上下文没了。
```

适合：

```text
客服机器人、问答助手、短任务 Bot。
```

### 思路三：按自然日切 session

例如：

```text
每天 0 点后，同一个用户第一条消息自动创建新 session。
```

判断逻辑类似：

```text
session.created_at 的日期 != 当前日期
```

优点：

```text
实现简单，方便按天归档。
```

缺点：

```text
跨天工作的任务可能被切断，比如晚上 23:50 开始，00:10 继续。
```

适合：

```text
日报、打卡、每日任务型助手。
```

### 思路四：按主题或任务切 session

例如：

```text
用户说“开始一个新任务”
用户上传新文件
用户切换项目
系统识别意图变化很大
```

优点：

```text
上下文更贴合任务，不只是贴合时间。
```

缺点：

```text
需要更复杂的意图识别，容易误切或漏切。
```

适合：

```text
多项目工作台、知识库问答、复杂 Agent 系统。
```

### 思路五：短期窗口 + 长期记忆

常见做法：

```text
当前 session 只保留最近 N 轮消息。
更早内容做摘要、向量检索或长期记忆。
```

当前项目已经有一点类似思路：

```text
load_history() 默认读取最近 max_turns 条消息。
main_crew 中 _format_history() 只注入最近 max_history_turns 条。
完整历史可通过 history_reader Skill 分页读取。
```

相关代码：

```text
xiaopaw/session/manager.py:88
xiaopaw/agents/main_crew.py:46
xiaopaw/tools/skill_loader.py:304
```

优点：

```text
减少上下文长度，降低成本，同时保留查历史能力。
```

缺点：

```text
需要设计好摘要、检索或历史读取策略。
```

适合：

```text
长期个人助手、企业知识助手、多轮复杂任务助手。
```

### 当前项目最接近哪种

当前项目最接近：

```text
显式新建 session + 最近历史窗口 + 可分页读完整历史
```

也就是：

```text
用户不主动 /new，就继续沿用 active session。
Agent 默认看到最近若干条历史。
更早历史需要通过 history_reader Skill 查询。
```

如果你希望“同一个用户隔天自动新 session”，需要额外实现“按自然日切 session”或“按空闲时间切 session”的策略。
