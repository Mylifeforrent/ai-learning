# Agent 机制疑问解答 (Q&A)

针对你在 `note.md` 中提出的三个关键问题，这里为你进行详细解答：

## 1. CrewAI 的 Tools 和 MCP 提供的 Tools 本质上是不是都是 Function Calls？

**是的，本质上它们都是基于 Function Calling / Tool Calling 机制设计出来的，只是封装层级和生态应用范围有所不同。**

- **本质一致**：无论是 CrewAI、LangChain 的 Tools 还是 MCP (Model Context Protocol) 的 Tools，底层思想都是“让大模型知道有哪些外部能力可用”。它们都会把可用工具的名称、描述、参数类型（Schema）翻译成大模型能看懂的结构（通常是特定格式的 JSON Schema 或提示词），并告诉大模型：“如果你需要某种信息或要执行某个动作，请按照指定格式输出工具的调用请求”。
- **差异点**：
  - **框架层 Tool (CrewAI/LangChain)**：主要是代码级别的封装。你编写一个 Python 函数，用 `@tool` 装饰器包裹，框架在运行时读取它的签名并生成 Schema 发给 OpenAI 等大模型。
  - **协议层 Tool (MCP)**：MCP 是一种标准化协议。它的目标是打破具体框架的绑定，让任何符合协议标准的数据源或工具服务，都可以通过这套协议无缝接入到任意的大模型工具平台（如 Cursor、Claude Desktop 等）。它是跨进程、跨边界的。

## 2. 为什么提示词里存在 `stop: [Observation]`？它的设计目的及举例

**目的：强制 AI 停止文本生成，防止 AI 产生“幻觉”从而自己编造外部工具的执行结果。**这正是著名的 ReAct (Reason + Act) 模式的核心实现手段。

### 详细解释：
在系统提示词中，我们通常告诉 AI，解决问题的标准步骤如下：
1. **Thought**：思考你应该怎么做
2. **Action**：决定使用什么工具以及参数
3. **Observation**：这是工具实际返回的客观结果

如果你不加 `stop: [Observation]`，AI 在生成完 `Thought` 和 `Action` 后，因为它的天性是“续写文本”，它会顺着之前的语境**直接猜**或者**捏造**一个工具执行的结果。这是极度危险的（例如它根本没查数据库，却直接编造了一个库存数据）。

### 举例说明：
假设 AI 需要通过天气 API 查询天气。

**没有 `stop: ["Observation"]` 时发生的灾难：**
```text
(AI 生成开始)
Thought: 我需要查一下北京当前的天气。
Action: get_weather("Beijing")
Observation: 北京今天是晴天，气温25度。 ( <- 这里是 AI 凭空瞎编的，根本没有发起网络请求 )
Thought: 好的，我现在知道天气了。
(AI 生成结束，全过程一气呵成，但拿到的是假数据)
```

**加了 `stop: ["Observation"]` 后正确的流程：**
```text
(AI 生成开始)
Thought: 我需要查一下北京当前的天气。
Action: get_weather("Beijing")
(AI 遇到了 stop 词，立刻中断并停止生成，控制权交还给 Python 框架代码)
```
**这时候 Python 框架接管**：提取出 `get_weather("Beijing")`，真正在本地发起 HTTP 请求，得到真实结果“大雨，15度”。
**Python 框架**把带真实结果的文本拼接上去，再次发送给 AI 进行下一轮对话（这就是所谓的循环 Loop）：
```text
(User / System 补充代码执行结果继续请求模型)
Observation: 北京今天是中到大雨，气温 15 度。
(AI 接着上面的结果继续生成)
Thought: 原来下雨了，我需要提醒用户出门带伞。
```

## 3. 是否可以用 LangGraph + LangChain 实现类似机制？(附示例代码)

**完全可以。LangGraph 就是为了实现这种循环状态机（State Machine）和复杂的 Workflow / Agentic 机制而生的。** CrewAI 本质上也是一层封装好的特定执行流。使用 LangGraph 你能获得更强大的定制性和流控能力（比如设置超时、增加人工审批节点、回退处理等）。

### 设计思路：
在一个 LangGraph 中，用来实现类似的 ReAct Agent，主要需要两个核心节点（Nodes）：
1. **Agent Node（大脑节点）**：负责接收当前状态的对话历史，调用 LLM 进行思考。如果 LLM 决定调用工具，则输出 Tool Call。如果任务完成，则输出最终回答。
2. **Tool Node（手脚节点）**：当 Agent 决定使用工具时，图的状体会路由到这个工具执行节点。它执行对应的本地 Python 函数，并将执行返回的结果添加到对话历史中（作为 ToolMessage/Observation），然后把连线（Edge）重新指回 Agent Node 触发继续思考。

### 简化版 LangGraph 示例代码：

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from typing import Annotated, TypedDict
import operator

# 1. 定义我们自己的工具 (相当于 CrewAI 里的 Tool)
@tool
def search_weather(city: str) -> str:
    """查询给定城市的天气"""
    # 这里应该发起真实的网络请求，暂用模拟数据代替
    if "北京" in city:
         return "北京今天中雨，建议随身带伞，气温15度"
    return "未知城市天气"

tools = [search_weather]

# 2. 定义图中流转的 State (状态)
class AgentState(TypedDict):
    # 自动合并每次产生的消息历史，形成完整的上下文记忆
    messages: Annotated[list, operator.add]

# 3. 初始化 LLM 和绑定 Tools 
llm = ChatOpenAI(model="gpt-4o")
# bind_tools 将 Python 签名转成 OpenAI function calling 格式
llm_with_tools = llm.bind_tools(tools)

# 4. 定义处理节点
def chatbot_node(state: AgentState):
    """思考节点：调用 LLM 进行推断"""
    messages = state["messages"]
    
    # 我们可以在请求的最开始插入 System Prompt，定义它的能力与限制
    if not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content="你是一个智能助手。回答问题前，请总是使用适当的工具来获取准确的外部信息。")
        messages = [sys_msg] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 利用 langgraph 已经预制的 ToolNode，能直接解析执行 LLM 返回的 Tool Call
tool_node = ToolNode(tools)

# 5. 构建图数据结构并编译
builder = StateGraph(AgentState)
builder.add_node("agent", chatbot_node)
builder.add_node("tools", tool_node)

# 定义图的连线逻辑（Edges）
builder.add_edge(START, "agent")
# tools_condition 是官方提供的一个快捷路由函数，
# 会检查 agent 节点最新输出中是否包含 tool calls。
# 若有，则走向 "tools" 节点；若无，则表示任务结束，走向 END。
builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})

# 工具执行完后，一定要有一条边指回 agent，让它基于工具执行结果(Observation)继续推断下一步
builder.add_edge("tools", "agent")

graph = builder.compile()

# 6. 测试运行我们的 LangGraph Agent
initial_state = {"messages": [HumanMessage(content="北京今天天气怎样？我出门需要注意什么？")]}
for event in graph.stream(initial_state, stream_mode="values"):
    # 打印图流转时的每次新产生的状态信息
    message = event["messages"][-1]
    message.pretty_print()
```

*以上代码就是一个完整的 ReAct 状态循环流。这就是 LangGraph 的优势所在，它把复杂的 Thought-Action-Observation 抽象成一个个具体的图节点和边进行流转，逻辑完全透明，你可以明确地知道它的下一步走向并在其间加入各种复杂的业务逻辑。*

---

## 4. CrewAI 中 System Prompt、User Prompt、Assistant Prompt 三种提示词模版各自的作用与协作机制

### 4.1 核心结论：这是 LLM 的底层要求，框架只是填充者

> **这三种提示词（`system`、`user`、`assistant`）本质上是 LLM Chat Completion API 定义的三种消息角色，是大模型层面的规范，不是某个框架独创的。** CrewAI、LangChain、AutoGen、Dify、以及任何 Agent 框架，最终都是在往这三种角色的"壳"里填充内容，然后发给 LLM API。

换言之：
- **LLM API 提供了"信封的格式"**（system / user / assistant 三种角色）
- **框架负责"往信封里装信"**（将你定义的 Agent 参数、Task 描述、历史对话自动填入对应角色的消息中）

---

### 4.2 三种提示词角色的职责分类

| 角色 | 谁写入的 | 核心职责 | 在 CrewAI 中对应什么 | 一句话比喻 |
| :--- | :--- | :--- | :--- | :--- |
| **`system`** | 开发者/框架 | 定义 AI 的**身份、能力边界、行为规则** | Agent 的 `role` + `goal` + `backstory` + 可用工具列表 + ReAct 格式指令 | 📋 **岗位说明书** |
| **`user`** | 用户/框架 | 提出**具体任务、问题、期望输出格式** | Task 的 `description` + `expected_output` | 📝 **甲方需求文档** |
| **`assistant`** | LLM 生成 | AI 的**思考过程、行动决策、最终回答** | 模型输出的 Thought / Action / Final Answer | 🤖 **员工的工作汇报** |

---

### 4.3 用一个完整例子说明三者如何协作

**场景**：你用 CrewAI 创建了一个"市场调研分析师"Agent，给它分配了一个"分析某公司竞品"的任务。

#### 第一步：CrewAI 读取你的配置，自动组装消息

你写的 CrewAI 代码：
```python
from crewai import Agent, Task, Crew
from langchain.tools import tool

@tool("search_web")
def search_web(query: str) -> str:
    """在互联网上搜索信息"""
    return "搜索结果: Tesla 2024年Q3营收251亿美元, 同比增长8%..."

analyst = Agent(
    role="资深市场调研分析师",
    goal="通过数据和工具，为用户提供精准的竞品分析报告",
    backstory="你有10年市场分析经验，擅长数据挖掘和趋势预测。你始终用数据说话，绝不编造信息。",
    tools=[search_web],
    verbose=True
)

task = Task(
    description="请调研 Tesla 最新一个季度的财务表现，并与 BYD 进行对比分析。",
    expected_output="一份简洁的对比分析报告，包含营收、毛利率、交付量三个关键维度。",
    agent=analyst
)

crew = Crew(agents=[analyst], tasks=[task])
result = crew.kickoff()
```

#### 第二步：底层实际发给 LLM API 的消息内容

CrewAI 框架读取你的代码后，会自动组装以下 HTTP 请求发给大模型 API：

```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "你是 资深市场调研分析师。\n你的目标是：通过数据和工具，为用户提供精准的竞品分析报告。\n\n背景故事：你有10年市场分析经验，擅长数据挖掘和趋势预测。你始终用数据说话，绝不编造信息。\n\n你可以使用以下工具：\n- search_web：在互联网上搜索信息。参数：query (string)\n\n处理任务时请严格遵循以下格式：\nThought: 仔细思考你应该怎么做\nAction: 选择一个工具\nAction Input: 工具的参数\nObservation: 工具返回的结果\n...(可以重复多次)\nThought: 我现在已经知道了最终答案\nFinal Answer: 最终回复"
    },
    {
      "role": "user",
      "content": "请调研 Tesla 最新一个季度的财务表现，并与 BYD 进行对比分析。\n\n期望输出格式：一份简洁的对比分析报告，包含营收、毛利率、交付量三个关键维度。"
    }
  ],
  "stop": ["Observation"]
}
```

> ⚡ **请注意**：你在 CrewAI 代码中写的那些参数（`role`, `goal`, `backstory`, `tools`, `description`, `expected_output`），全部被框架自动拼接成了标准的 `system` 和 `user` 消息！**这就是框架的核心价值——帮你组装提示词。**

#### 第三步：LLM 返回 Assistant 消息（第一轮 —— 思考 + 行动）

```json
{
  "role": "assistant",
  "content": "Thought: 用户需要 Tesla 和 BYD 的最新季度财务对比。我首先需要搜索 Tesla 的最新财务数据。\nAction: search_web\nAction Input: {\"query\": \"Tesla 2024 Q3 财务报告 营收 毛利率 交付量\"}"
}
```

> 模型在生成到 `Observation` 之前就被 `stop` 词截停了。控制权交还给 CrewAI 框架。

#### 第四步：框架执行工具，以 User 角色注入真实结果（伪 Observation）

```json
{
  "role": "user",
  "content": "Observation: 搜索结果: Tesla 2024年Q3营收251亿美元, 同比增长8%..."
}
```

> ⚠️ 在 ReAct 模式中，工具结果被伪装成 `user` 角色注入。在原生 Tool Calling 模式中则使用独立的 `tool` 角色（见本文件 Q3 的 LangGraph 示例）。

#### 第五步：LLM 再次返回 Assistant 消息（循环继续或给出最终回答）

```json
{
  "role": "assistant",
  "content": "Thought: 我已经拿到了 Tesla 的数据，现在需要搜索 BYD 的对应数据进行对比。\nAction: search_web\nAction Input: {\"query\": \"比亚迪 BYD 2024 Q3 营收 毛利率 交付量\"}"
}
```

...*（框架再次执行工具、注入结果、循环往复）*...

最终，当模型认为信息足够时：
```json
{
  "role": "assistant",
  "content": "Thought: 我现在已经有了 Tesla 和 BYD 的完整数据，可以给出最终分析报告了。\nFinal Answer: \n## Tesla vs BYD 2024Q3 对比分析报告\n| 维度 | Tesla | BYD |\n|------|-------|-----|\n| 营收 | 251亿美元 | 282亿美元 |\n| 毛利率 | 19.8% | 22.1% |\n| 交付量 | 46.3万辆 | 82.6万辆 |\n\n关键洞察：BYD 在本季度的营收和交付量均超过 Tesla..."
}
```

---

### 4.4 三种角色在完整对话循环中的协作时序图

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  SYSTEM 角色  │      │  USER 角色    │      │ ASSISTANT 角色│
│  (岗位说明书)  │      │  (甲方需求)   │      │ (员工汇报)    │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                      │                      │
       │ ① 框架组装：          │                      │
       │ role + goal +        │                      │
       │ backstory + tools +  │                      │
       │ ReAct格式指令         │                      │
       │─────────────────────>│                      │
       │                      │ ② 框架组装：          │
       │                      │ task description +   │
       │                      │ expected_output      │
       │                      │─────────────────────>│
       │                      │                      │ ③ LLM 生成:
       │                      │                      │ Thought + Action
       │                      │                      │（被 stop 词截停）
       │                      │                      │<─────────────────
       │                      │ ④ 框架执行工具后      │
       │                      │ 注入 Observation      │
       │                      │─────────────────────>│
       │                      │                      │ ⑤ LLM 继续生成:
       │                      │                      │ Thought + Action
       │                      │                      │ 或 Final Answer
       │                      │                      │<─────────────────
       │                      │                      │
       │         ↺ 重复 ④⑤ 直到输出 Final Answer       │
```

---

### 4.5 各角色的详细功能拆解

#### 🔷 System Prompt —— "你是谁 + 你能做什么 + 你必须怎么做"

System Prompt 在 CrewAI 中由以下部分自动拼接而成：

| 来源参数 | 填充到 System Prompt 中的职能 | 示例 |
| :--- | :--- | :--- |
| `Agent.role` | 定义身份角色 | "你是资深市场调研分析师" |
| `Agent.goal` | 定义工作目标 | "通过数据和工具提供精准的竞品分析报告" |
| `Agent.backstory` | 注入专业背景和行为准则 | "你有10年市场分析经验，始终用数据说话" |
| `Agent.tools` | 列出可用工具的名称、描述、参数 | "你可以使用: search_web(query)" |
| 框架硬编码 | 注入 ReAct 格式规范（Thought/Action/Observation） | "处理任务时请严格遵循以下格式..." |

> **核心作用**：奠定整场对话的"基调"和"铁律"。System Prompt 只在对话最开始出现一次，但它的影响力贯穿所有后续回合。就像一个员工入职第一天收到的《员工手册》，之后做的所有工作都要遵守手册里的规章制度。

#### 🔷 User Prompt —— "这次具体要你做什么"

User Prompt 在 CrewAI 中由以下部分自动拼接：

| 来源参数 | 填充到 User Prompt 中的职能 | 示例 |
| :--- | :--- | :--- |
| `Task.description` | 具体的任务指令 | "调研 Tesla 最新季度财务表现，与 BYD 对比" |
| `Task.expected_output` | 期望的输出格式和内容要求 | "简洁对比报告，包含营收、毛利率、交付量" |
| 框架自动注入 | Observation（工具执行结果以 user 角色注入） | "Observation: Tesla Q3 营收 251 亿美元..." |

> **核心作用**：驱动每一轮对话的"具体指令"。如果说 System Prompt 是战略方向，那 User Prompt 就是战术命令。每次对话循环中模型都要响应最新的 User 消息。

#### 🔷 Assistant Prompt —— "我是这样思考和行动的"

Assistant 消息不是开发者填写的，而是大模型自己生成的：

| 生成内容 | 含义 | 示例 |
| :--- | :--- | :--- |
| `Thought: ...` | 模型的推理过程（受 System Prompt 中 ReAct 格式约束） | "Thought: 我需要先搜索 Tesla 的财务数据" |
| `Action: ...` | 决定调用哪个工具 | "Action: search_web" |
| `Action Input: ...` | 工具的参数 | "Action Input: {\"query\": \"Tesla Q3 财报\"}" |
| `Final Answer: ...` | 最终输出给用户的回答 | "Final Answer: ## Tesla vs BYD 对比报告..." |

> **核心作用**：作为"上下文记忆"累积在消息列表中。每一轮模型的历史输出（assistant 消息）都会被保留并在下一轮请求中一起发送给 LLM，让模型知道"我之前做了什么、想了什么"，从而保持多轮推理的连贯性。

---

### 4.6 这是 LLM 的要求还是框架的设计？—— 层级关系分析

这个问题的答案是**两者兼有，但根源在 LLM 层**：

```
┌──────────────────────────────────────────────────────────────────┐
│                        第一层：LLM API 规范                       │
│                                                                    │
│  OpenAI / Anthropic / Google 等模型厂商定义了 Chat API 的消息格式：  │
│  - role: "system"  → 模型预训练/微调时被教会：这是"规则设定"        │
│  - role: "user"    → 模型被教会：这是"用户的问题/指令"              │
│  - role: "assistant" → 模型被教会：这是"我之前说过的话"             │
│  - role: "tool"    → 模型被教会：这是"工具返回的真实数据"           │
│                                                                    │
│  ✅ 这是模型层面的规范，所有框架都必须遵守                          │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                    框架在此基础上做"内容填充"
                                │
┌───────────────────────────────▼──────────────────────────────────┐
│                    第二层：Agent 框架的封装逻辑                     │
│                                                                    │
│  CrewAI / LangChain / AutoGen 等框架的工作是：                     │
│  - 把 Agent 的 role/goal/backstory → 填入 system 消息              │
│  - 把 Task 的 description/expected_output → 填入 user 消息         │
│  - 把 LLM 的历史输出 → 维护在 assistant 消息列表中                 │
│  - 把工具的执行结果 → 注入到 user 或 tool 消息中                   │
│                                                                    │
│  ✅ 这是框架层面的封装策略，不同框架填充方式有差异                   │
└─────────────────────────────────────────────────────────────────┘
```

#### 所有类似 CrewAI 的框架是否都遵循这个设计逻辑？

**是的，几乎所有主流 Agent 框架的设计逻辑都是一致的**，因为它们面对的是同一个底层 API 规范。差异只在"往信封里装什么内容"：

| 框架 | System Prompt 里装什么 | User Prompt 里装什么 | Assistant 如何生成 |
| :--- | :--- | :--- | :--- |
| **CrewAI** | role + goal + backstory + 工具描述 + ReAct 格式 | task description + expected_output | Thought/Action/Final Answer 文本 |
| **LangChain/LangGraph** | 开发者自定义的系统指令 | 用户输入 | 纯文本或结构化 tool_calls |
| **AutoGen** | Agent 的 system_message | 用户输入 + 其他 Agent 的发言 | 自由文本回复 |
| **Dify** | 应用模板中的"系统提示词" | 用户在对话框中的输入 | 模型自由回复 |
| **Coze (扣子)** | Bot 的"人设与回复逻辑" | 用户消息 | 模型自由回复 |

> 🔑 **最终结论**：`system` / `user` / `assistant` 这三种角色是**大模型 Chat API 的底层规范**（源头是 OpenAI 在 2023 年推出 `gpt-3.5-turbo` 时定义的 Chat Completion API 格式，后来成为行业标准）。所有Agent 框架都只是在这个标准格式之上做"内容编排"。就好比 HTTP 协议定义了 GET/POST/PUT 等方法，而 Spring MVC、Django、Express 等 Web 框架都是在这些方法上做业务封装——原理完全一致。
