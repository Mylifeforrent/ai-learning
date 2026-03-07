# ReAct 模式消息累积机制深度剖析 —— 以 CrewAI 为例

## 1. 三种 Role（角色）的定义与原理

OpenAI Chat Completions API 的核心设计就是一个**多轮对话消息列表** `messages: [...]`。列表中每条消息都必须携带一个 `role` 字段，用来区分"这句话是谁说的"。

| Role | 谁写入的？ | 作用 | 什么时候使用？ |
| :--- | :--- | :--- | :--- |
| `system` | **开发者/框架** 硬编码写入 | 设定大模型的"人格"和"规则"。相当于对大模型下达的"最高指令"，优先级最高。 | 始终且仅放在消息列表的**首位**，只需一条。整个对话过程中保持不变。 |
| `user` | **最终用户** 或 **框架代替用户** 写入 | 代表"人类的声音"。大模型会把这个角色的消息当做需要回应的输入请求。 | 每一轮对话中，代替人类发问或向大模型注入新信息（如 Observation 结果）。 |
| `assistant` | **大模型自身** 生成，被框架捕获后存入 | 代表"AI 的声音"。大模型的每一次输出都是 assistant 消息。框架将其记录下来并追加到下一轮请求中，使大模型"记住自己之前说了什么"。 | 框架代码每次收到大模型的回复后，原封不动地追加到 messages 列表。 |
| `tool` | **框架代码** 执行完工具后写入 | （仅限 Tool Calling 模式）代表"工具的真实返回结果"。 | 当模型通过原生 Tool Calling 请求调用工具后，框架执行完毕将结果以此角色回传。 |

> **核心要点**：`assistant` 就是大模型每一次的输出结果，没错！框架把它"录像"下来塞回到下一轮请求的消息列表中，大模型才能"回忆"起自己之前做了什么。**大模型本身没有记忆**，它的"记忆"完全是由框架代码在每一轮请求时，不断累积地把历史消息全部重新发送给它来实现的。

---

## 2. 你的理解完全正确！完整 API 日志模拟

下面用一个具体的例子来模拟 CrewAI 在 ReAct 模式下的**完整 API 调用日志**。

**任务**：查询北京天气，并给出穿衣建议。  
**可用工具**：`get_weather(city)`

---

### 🔄 第 1 轮 API 请求

框架组装的 `messages` 列表：
```json
{
  "model": "gpt-4o",
  "stop": ["Observation:"],
  "messages": [
    {
      "role": "system",
      "content": "你是一个天气预报专家。你每次必须使用下面的格式来输出：\nThought: 你的思考\nAction: 工具名称，只能从 [get_weather] 中选\nAction Input: 传入的 JSON 参数\nObservation: 工具返回的结果（不要自己编写！）\n...\n当你准备好最终答案时，输出：\nThought: I now know the final answer\nFinal Answer: 最终答案"
    },
    {
      "role": "user",
      "content": "请帮我查一下北京今天天气，并给出穿衣建议。"
    }
  ]
}
```
> 📌 **此时只有 2 条消息**：1 条 system + 1 条 user。

**大模型返回（被 `stop: ["Observation:"]` 截断）**：
```text
Thought: 用户需要北京的天气信息，我应该调用 get_weather 工具来获取真实数据。
Action: get_weather
Action Input: {"city": "Beijing"}

```
> 📌 模型生成到即将输出 `Observation:` 时被强制停止。这段输出被框架以 **`assistant`** 角色记录。

**框架代码在后台的操作**：
```python
# 1. 正则提取出 Action 和 Action Input
action = "get_weather"
action_input = {"city": "Beijing"}

# 2. 真实执行工具（发起 HTTP 请求）
result = get_weather("Beijing")  # 返回: "北京今天阴转小雨，气温8-14度，北风3级"

# 3. 把大模型的输出 + 工具结果一起追加到消息列表
```

---

### 🔄 第 2 轮 API 请求

框架组装的 `messages` 列表（注意：**累积追加了上一轮的内容**）：
```json
{
  "model": "gpt-4o",
  "stop": ["Observation:"],
  "messages": [
    {
      "role": "system",
      "content": "（与第 1 轮完全相同的系统提示词，省略...）"
    },
    {
      "role": "user",
      "content": "请帮我查一下北京今天天气，并给出穿衣建议。"
    },
    {
      "role": "assistant",
      "content": "Thought: 用户需要北京的天气信息，我应该调用 get_weather 工具来获取真实数据。\nAction: get_weather\nAction Input: {\"city\": \"Beijing\"}\n"
    },
    {
      "role": "user",
      "content": "Observation: 北京今天阴转小雨，气温8-14度，北风3级"
    }
  ]
}
```
> 📌 **此时有 4 条消息**：
> 1. system（不变）
> 2. user（原始提问，不变）
> 3. **assistant**（第 1 轮大模型的输出，被框架原样记录追加）
> 4. **user**（框架把真实的工具结果以 `Observation: ...` 的形式，冒充 user 角色注入！）

> ⚠️ **为什么 Observation 是 user 角色？** 因为在 ReAct 的纯文本模式下，API 只有 system/user/assistant 三种角色可选（没有 `tool` 角色）。Observation 不是大模型自己说的（它被截断了），而是外部框架注入的客观事实 —— 所以只能以 `user` 角色塞入。大模型会把它当做"人类补充的新信息"来消化。

**大模型返回**：
```text
Thought: I now know the final answer. 北京今天阴转小雨，我应该建议用户带伞并适当添衣。
Final Answer: 北京今天天气为阴转小雨，气温8-14度，北风3级。建议您：
1. 外出请携带雨伞
2. 建议穿着薄款羽绒服或厚外套
3. 体感偏冷，注意防风保暖
```
> 📌 模型判断信息已足够，输出 `Final Answer`，**跳出循环**。框架检测到 `Final Answer` 关键词，提取其后内容作为最终结果返回给真正的用户。

---

### 🔄 假如需要第 3 轮（即工具需多次调用的场景）

如果模型在第 2 轮没有给出 Final Answer，而是继续请求调用另一个工具（如 `get_uv_index`），那第 3 轮的 messages 会是：

```json
{
  "messages": [
    { "role": "system",    "content": "（系统提示词）" },
    { "role": "user",      "content": "请帮我查一下北京今天天气，并给出穿衣建议。" },
    { "role": "assistant", "content": "Thought: ...第1轮思考...\nAction: get_weather\nAction Input: ..." },
    { "role": "user",      "content": "Observation: 北京今天阴转小雨，气温8-14度" },
    { "role": "assistant", "content": "Thought: 我还需要查紫外线指数...\nAction: get_uv_index\nAction Input: ..." },
    { "role": "user",      "content": "Observation: 紫外线指数2，较弱" }
  ]
}
```
> 📌 **此时有 6 条消息**：每一轮都追加一对 `assistant + user(Observation)`，像"千层饼"一样不断累积。大模型通过阅读自己之前说的所有 assistant 消息来"回忆"已完成的工作。

---

## 3. 消息累积的可视化全景图

```
┌──────────────────────────── 第 1 轮请求 ────────────────────────────┐
│  [system] 系统人设提示词（含 ReAct 格式要求 + 工具列表）            │
│  [user]   "请帮我查一下北京今天天气并给出穿衣建议"                  │
│                            ↓                                       │
│                    大模型生成 → 被 stop 词截断                      │
│                            ↓                                       │
│  [assistant] "Thought:...  Action: get_weather  Action Input:..."  │ ← 被框架捕获
└────────────────────────────────────────────────────────────────────┘
                             ↓  框架运行 get_weather() → "阴转小雨8-14度"
┌──────────────────────────── 第 2 轮请求 ────────────────────────────┐
│  [system]    （与上轮相同）                                         │
│  [user]      （与上轮相同）                                         │
│  [assistant] （第1轮大模型的完整输出，原样追加）                     │ ← 累积！
│  [user]      "Observation: 阴转小雨，8-14度，北风3级"               │ ← 工具结果注入
│                            ↓                                       │
│                    大模型生成                                       │
│                            ↓                                       │
│  [assistant] "Thought: I now know the final answer\n               │
│               Final Answer: 建议穿厚外套带伞..."                   │ ← 跳出循环！
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. 为什么必须这样做？—— 大模型没有记忆

最关键的一点：

> **大模型（如 GPT-4、Claude）本身不具备任何跨请求的记忆能力。** 每次 API 调用对大模型来说都是一次"全新的对话"。它不记得上一次你问了什么、它回答了什么。

所以框架的唯一办法就是：**每一轮都把从头到尾的完整对话历史重新发给它**。不断累积的历史消息就是大模型的"外挂记忆条"。

这也解释了为什么 Agent 跑多轮之后 Token 消耗会飞速上涨 —— 因为每一轮请求的 Token 数 ≈ system 长度 + 前面所有轮次的 assistant+user 长度之和。这就是为什么：
- **CrewAI 设置了最大迭代次数**（默认 25 次），防止无限循环导致天价账单。
- **BabyAGI 选择拆分 Prompt**，让每一个子 Agent 只关注当前任务，不携带完整历史；而把历史存入向量数据库，按需检索（RAG），从而压缩每一次发送的 Token 量。

---

## 5. ReAct 文本模式 vs Tool Calling 模式的消息对比

| 对比维度 | ReAct 纯文本模式（CrewAI 默认） | 原生 Tool Calling 模式 |
| :--- | :--- | :--- |
| 工具结果用什么 role？ | `user`（冒充用户注入 Observation） | `tool`（专属角色，含 `tool_call_id`） |
| 如何停止生成？ | `stop: ["Observation:"]` 截断 | `finish_reason: "tool_calls"` 原生信号 |
| assistant 消息包含什么？ | 纯文本混杂 Thought/Action | 结构化 `tool_calls` 对象 |
| 解析方式 | 正则匹配 `Action:` 和 `Action Input:` | SDK 直接 `.tool_calls[0].function` |
| 消息累积结构 | `[sys, user, asst, user, asst, user, ...]` | `[sys, user, asst, tool, asst, tool, ...]` |

> 💡 Tool Calling 模式中，工具结果拥有专属的 `tool` 角色，不再需要冒充 `user`。这让大模型能更清晰地区分"人说的话"和"工具返回的数据"。
