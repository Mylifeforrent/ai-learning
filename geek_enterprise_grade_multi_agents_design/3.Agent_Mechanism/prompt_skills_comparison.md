# AI Agent 框架提示词工程技巧与底层原理全景对比分析 (含实战代码范例)

在当今的大模型（LLM）驱动的 Agent 开发中，不同的框架为了让大模型更好地遵循指令、完成指定的任务流、以及精准地调用外部工具，演化出了多种不同的提示词（Prompt）工程流派和技巧。

本文将为您详细展开讲解 CrewAI 中的 `Thought:`、`stop: [Observation]`，AutoGPT 和 OpenAI 的 JSON 格式约束，并扩展介绍如 Anthropic Claude 推荐的 XML 标签等其他优秀框架的提示词技巧，帮助您全面了解其背后的技术原理及**实际代码应用**。

---

## 📊 技术演进时间线

理解这些流派的关键在于：它们并非孤立产物，而是一条清晰的**技术演进链条**：

```
2022 年底                    2023 年初               2023 年中              2024 年至今
   │                          │                      │                       │
   ▼                          ▼                      ▼                       ▼
[ReAct 论文]  ──→  [LangChain/CrewAI   ──→  [AutoGPT JSON   ──→  [OpenAI/Anthropic/Google
 Thought/Act/        采用纯文本              硬规范约束]         原生 Tool Calling API]
 Observation]        + stop 词]
                                                              (当前工业标准 ✅)
```

简而言之：**纯文本 Hack → JSON Prompt 约束 → 原生 API 协议**，一步比一步稳健。

---

## 1. CrewAI (基于 ReAct 模式) 的提示词技巧

CrewAI 等强调过程推理的框架，很大程度上受 ReAct (Reason + Act) 论文的启发。大模型被要求在执行任何外部操作之前，先"大声思考"。

### 1.1 原理解析
*   **引导思维链 (Chain-of-Thought, CoT)**：大模型本质上是"概率性的文本接龙"。如果直接让大模型给出"行动（Action）"，它往往会跳过中间推理过程，导致它选错工具或传错参数。通过在提示词模板中预置 `Thought:`，强制大模型必须先生成一段自我推理的文字。
*   **`stop: [Observation]` 防幻觉机制**：大模型的本能是续写文本。当它输出行动指令后，如果不加阻止，它会自己编造一个结果接着往下写。通过设置 stop 词为 `Observation`，API 生成会立即终止。本地框架接管控制权，真实调用工具后，将结果拼接成 `Observation: [真实结果]` 再次发给大模型。

### 1.2 实际案例演示

**📝 框架预置的系统提示词 (System Prompt) 长什么样？**
```text
你在解决问题时，必须严格遵循以下格式：
Question: 需要你回答的问题或完成的任务
Thought: 思考你应该怎么做
Action: 选择使用下面工具中的一个：[get_weather, calculator]
Action Input: 传入工具的参数
Observation: 工具执行返回的内容
... (Thought/Action/Action Input/Observation 可以重复多次)
Thought: 我现在知道了最终答案
Final Answer: 最终回复给用户的完整内容
```

**🤖 大模型输出的结果长什么样？（中间挂起状态）**
```text
Thought: 用户问我今天北京的天气，我需要调用天气查询工具。
Action: get_weather
Action Input: {"city": "Beijing"}
```
*(注意：到这里因为触发了 stop_word: "Observation"，大模型停止输出。Python 代码拿到上述文本，解析出 `get_weather` 并实际运行，得到结果 "多云，20度" 后，将 `Observation: 多云，20度\n` 附在后面再发回给大模型进行下一轮推断)*

**💻 CrewAI 框架使用代码示例**
```python
from crewai import Agent, Task, Crew
from langchain.tools import tool

@tool("get_weather")
def get_weather(city: str) -> str:
    """查询指定城市的天气"""
    return "多云，20度" # 模拟外部 API 返回

# 创建基于 ReAct 模式的 Agent
researcher = Agent(
    role='天气预报员',
    goal='准确地查出当地天气',
    backstory='你是一个严谨的气象专家。',
    verbose=True, # 开启后终端会打印 Thought/Action/Observation 的过程
    allow_delegation=False,
    tools=[get_weather] # CrewAI 底层会将这个工具的描述转化为 Prompt 注入给模型
)

task = Task(description='查一下今天北京的天气', expected_output='简短的天气报告', agent=researcher)
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
print(result)
```

---

## 2. OpenAI Function Calling 与 AutoGPT 的 JSON 规范流派

早期的 ReAct 模式因为用正则表达式去匹配提取纯文本的动作，在生产环境中极其脆弱。为了解决这个问题，以 AutoGPT 为代表掀起了 **JSON 化** 的浪潮，而后 OpenAI 官方通过 API 层面对其进行了原生支持。

### 2.1 AutoGPT 纯 JSON 约束案例

**📝 提示词长什么样？(由于没有 API 原生层面的支持，只能硬写在 Prompt 里)**
```text
你是一个全自动 AI 助手。你必须并且只能用以下 JSON 格式进行回复，绝对不能输出任何其他非 JSON 文本：
{
  "thoughts": {
    "text": "你对当前状况的思考",
    "reasoning": "为什么你要选这个动作",
    "plan": "- 你的短期排期计划\n- 下一步操作",
    "criticism": "对你刚才行为的自省，指出可能的缺点"
  },
  "command": {
    "name": "命令名称，必须从 [search_internet, read_file] 中选择",
    "args": { "参数键": "参数值" }
  }
}
```

**🤖 大模型输出的结果长什么样？**
```json
{
  "thoughts": {
    "text": "用户想了解极客时间的课程，我需要先搜索一下相关信息。",
    "reasoning": "由于我没有实时的极客时间课程数据，使用互联网搜索是最快的方法。",
    "plan": "- 搜索最新热门课程\n- 提取有用信息\n- 总结返回给用户",
    "criticism": "我需要确保搜索关键词精确，避免搜出无关广告信息。"
  },
  "command": {
    "name": "search_internet",
    "args": {
      "query": "极客时间 最新热门课程清单"
    }
  }
}
```

**💻 AutoGPT 风格的 Python 解析代码**
```python
import json
from openai import OpenAI

client = OpenAI()

# AutoGPT 风格：把 JSON Schema 约束硬写进 System Prompt
system_prompt = """你是一个全自动 AI 助手。回复时必须严格使用以下 JSON 格式，
不允许输出任何其他非 JSON 文本：
{
  "thoughts": { "text": "...", "reasoning": "...", "plan": "...", "criticism": "..." },
  "command": { "name": "命令名", "args": { "参数键": "参数值" } }
}
可用命令: search_internet(query), read_file(filename)
"""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "帮我调研极客时间的AI课程"}
    ]
)

raw_text = response.choices[0].message.content  # 纯文本字符串

# ⚠️ 关键！AutoGPT 时代需要自行解析 JSON，如果模型在前后多输出了一句话就会崩溃
try:
    parsed = json.loads(raw_text)
    command_name = parsed["command"]["name"]
    command_args = parsed["command"]["args"]
    print(f"将执行命令: {command_name}，参数: {command_args}")
except json.JSONDecodeError as e:
    print(f"❌ 模型输出了无法解析的 JSON: {e}")
    # AutoGPT 常常在这里需要写大量的容错/重试逻辑
```

### 2.2 OpenAI 原生 Function Call (Tool Calling) 案例

> **🌟 行业现状说明**：**Tool Calling（即 Function Calling）毫无疑问是当前 Agent 开发绝对的主流和工业标准。** 
> *   现在几乎所有的头部闭源模型（GPT-4o, Claude 3.5, Gemini 1.5）和优秀的开源模型（Qwen 2.5, Llama 3, DeepSeek）都在预训练或指令微调（SFT）阶段，原生加入了对 Tool Calling 结构的理解。
> *   LangChain 的最新架构 `LangGraph`、以及 CrewAI 等专门的 Agent 框架，底层的默认调度器都已经从原始的文本 ReAct 切换为了原生的 `bind_tools()` / Tool Calling 支持。

**原理**：OpenAI 在模型底层直接支持了结构化的工具分发。底层训练教会了模型区分"普通对话"和"工具调用"。开发者不再需要把复杂的 JSON 样例塞进系统提示词，而是在请求参数的 `tools` 字段中传入 JSON Schema。大模型会自动识别，而在它判断需要调用工具时，会返回一个要求工具调用的独特状态。

**💻 OpenAI API 完整往返代码（含工具结果回传）**
```python
import json
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

# ──────────────────────────────────────────
# 第一步：定义工具 Schema（不再需要塞进 System Prompt！）
# ──────────────────────────────────────────
tools = [
  {
    "type": "function",
    "function": {
      "name": "get_weather",
      "description": "查询给定地点的天气",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "城市名称，例如北京、上海"
          }
        },
        "required": ["location"]
      }
    }
  }
]

# ──────────────────────────────────────────
# 第二步：发起第一轮请求
# ──────────────────────────────────────────
messages = [{"role": "user", "content": "北京天气如何？"}]

response = client.chat.completions.create(
  model="gpt-4o",
  messages=messages,
  tools=tools,
  tool_choice="auto"
)

assistant_message = response.choices[0].message

# 🔍 关键！此时 finish_reason == "tool_calls"，而不是 "stop"
# 说明模型没有直接回答，而是要求框架去执行工具
print(assistant_message.tool_calls)
# 输出: [ToolCall(id='call_xyz', function=Function(arguments='{"location":"Beijing"}', name='get_weather'))]

# ──────────────────────────────────────────
# 第三步：框架执行真实工具，并把结果回传给模型（完成 Round-Trip）
# ──────────────────────────────────────────
tool_call = assistant_message.tool_calls[0]
args = json.loads(tool_call.function.arguments)

# 真实运行本地函数（替代了 ReAct 中 stop 词截断后的本地代码执行）
weather_result = f"{args['location']}今天多云，气温20度，建议穿薄外套" # 模拟

# 将 assistant 的工具请求消息 + 工具执行结果一起追加到消息历史
messages.append(assistant_message)                        # 模型的工具请求
messages.append({                                         # 工具的真实返回
    "role":         "tool",
    "tool_call_id": tool_call.id,
    "content":      weather_result
})

# ──────────────────────────────────────────
# 第四步：把带有真实结果的上下文再次发给模型，此时它才正式回答用户
# ──────────────────────────────────────────
final_response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools
)

# 🎉 此时 finish_reason == "stop"，模型给出了最终自然语言回答
print(final_response.choices[0].message.content)
# 输出: "北京今天多云，气温20度。建议您出门穿一件薄外套，注意保暖。"
```

> **🔑 与 ReAct 模式对比的核心差异**：
> - ReAct 模式靠 `stop: ["Observation"]` **截断文本生成** 来让出控制权 → 然后用正则提取 Action → 本地执行 → 手动拼接 Observation 文本。
> - Tool Calling 靠 `finish_reason="tool_calls"` **原生 API 信号** 来让出控制权 → SDK 直接返回结构化对象 → 本地执行 → 以 `role: "tool"` 消息回传结果。
> - 后者完全消灭了人工正则解析和文本格式脆弱性，是 ReAct 的工业化升级版。

---

## 3. Anthropic Claude 的 XML Tags 流派

Anthropic (Claude 的开发商) 明确推荐使用 XML 标签来包裹提示词和工具调用，这得益于其预训练数据集对 XML 的高敏锐度。这在 LangChain 的 XML Agent 中也有大量应用。

> **⚠️ 重要补充**：虽然 Claude 以 XML 闻名，但 Anthropic 现在也已原生支持了类似 OpenAI 的结构化 Tool Calling API。XML 标签在今天更多用于**提示词内部的信息隔离与结构分治**（例如划分 `<context>`、`<instructions>`、`<examples>` 等区域），而非工具调用本身。这两者可以同时使用。

### 3.1 实际案例演示

**📝 提示词长什么样 (XML System Prompt)？**
```xml
<system_instructions>
你是一个智能助手。你有以下工具可用：
<tools>
<tool_description>
<tool_name>calculator</tool_name>
<description>执行数学计算</description>
<parameters>
  <parameter><name>expression</name><type>string</type></parameter>
</parameters>
</tool_description>
</tools>

当你需要调用工具时，请使用严格的 XML 格式响应：
<tool_use>
  <tool_name>工具名称</tool_name>
  <tool_input>
    <参数名>参数值</参数名>
  </tool_input>
</tool_use>
</system_instructions>

<user_input>
234 乘以 564 等于多少？
</user_input>
```

**🤖 大模型输出的结果长什么样？**
```xml
<thought>用户要求计算 234 * 564 的结果，这是一个纯数学表达式，我应该调用 calculator 工具来得到准确的机器计算结果。</thought>
<tool_use>
  <tool_name>calculator</tool_name>
  <tool_input>
    <expression>234 * 564</expression>
  </tool_input>
</tool_use>
```
*(这种结构对流式解析极为友好：一旦 Python 代码在使用流式(Stream)监听回答时匹配到了 `</tool_use>` 的闭合标签，即可立即拦截流并执行工具)*

**💻 LangChain XML Agent 代码示例**
```python
from langchain.agents import create_xml_agent, AgentExecutor
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain import hub

@tool
def calculator(expression: str) -> str:
    """执行数学计算并返回结果"""
    return str(eval(expression))

# Claude 模型天然擅长 XML 格式的理解
llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")

# 拉取官方预制的 XML Agent 模版（内含 XML 格式的 Thought/Action 分隔结构）
prompt = hub.pull("hwchase17/xml-agent-convo")

# 创建 XML Agent
agent = create_xml_agent(llm, tools=[calculator], prompt=prompt)
executor = AgentExecutor(agent=agent, tools=[calculator], verbose=True)

result = executor.invoke({"input": "234 乘以 564 等于多少？"})
print(result["output"])
```

---

## 4. BabyAGI 的任务驱动编排 (Task-Driven)

相比于让一个庞大的 Agent 用复杂的 Prompt（如包含了 Thought, Plan, Action, JSON 等）去独挑大梁，BabyAGI 选择弱化单一大模型的压力。它通过**动态分离提示词**，用 3 个不同的 Agent (执行者、任务创造者、排序优化者) 短小精悍的 Prompt 相互配合达成总目标。

### 4.1 实际案例演示

**📝 提示词：生成新任务的 Agent (Task Creation Agent)**
```text
你是一个任务创造AI。你的最高指挥目标是: 搭建一个极客时间的学习助手。
上一次完成的任务是: 搜索所有的最新课程列表，完成的结果是: [课程A, 课程B]
当前未完成的剩余任务清单有: [建立本地数据库, 开发交互前端]

请仔细阅读上述结果，并基于总指挥目标，判断是否需要创建新的后续衍生任务。
你需要以 JSON 数组返回。切记！绝对不要生成与现有清单重复的任务。
```

**🤖 大模型输出的结果长什么样？**
```json
[
  "分析上一次搜索返回的极客时间网页DOM结构，找出翻页规则",
  "编写Python Scrapy爬虫脚本批量提取最新课程标题与价格信息"
]
```

**💻 BabyAGI 的核心 Python 操作循环**
```python
# 核心业务逻辑架构，展现了分布式拆分 Prompt 在代码层面的威力
objective = "写出一份完整的 AI 前沿课程调研报告"
task_list = ["任务1: 搜索AI课程", "任务2: 查阅官方文档汇总"]

while task_list:
    # 1. 拿出第一个任务执行
    current_task = task_list.pop(0)

    # 【这里内部是一个专门做事的提示词，不关心排期】
    result = execute_agent(objective, current_task)  
    
    # 2. 存入内存或向量数据库 (长期记忆)
    vector_db.store(result)
    
    # 3. 创造新任务
    # 【这里的提示词如上面例子所示，专门反向发散思维】
    new_tasks = task_creation_agent(objective, result, task_list) 
    
    # 4. 追加到队尾
    task_list.extend(new_tasks)
    
    # 5. 重新排优先级并去重
    # 【这里的提示词专门做统筹与裁切工作】
    task_list = prioritization_agent(objective, task_list) 
```
*(通过这三个角色的环环相扣，虽然放弃了类似于 ChatGPT 对话框那样的连贯上下文，却极大降低了单次调用的 Token 消耗，使系统有能力处理极其复杂、需耗时数周才能完成的长周期战略目标。)*

---

## 5. 总结对比全景图

| 框架/流派 | 核心通信格式 | 代表技术/标记 | 对系统代码的要求 | 适用场景 |
| :--- | :--- | :--- | :--- | :--- |
| **CrewAI/裸ReAct** | 结构化文本 | `Thought:`、`stop=["Observation"]` | 需编写正则表达式提取器，易碎。 | 兼容无法输出标准 JSON 的开源小模型。 |
| **AutoGPT** | 深层 JSON 对象 | 强约束格式 (`thoughts`, `command`) | `json.loads()`，偶尔需处理转义异常。 | 需要模型强反思的全自动脱机操作。 |
| **OpenAI 工具调用** | 原生 API 对象 | `finish_reason="tool_calls"` | SDK 直接返回结构化对象，无需解析文本。 | **当前工业标准**，成功率最高。 |
| **Anthropic Claude** | XML + 原生 Tool Call | `<tag>` 闭合标签做信息分治 | 可用 XML Parser 或正则拦截流式响应。 | 需要信息隔离和防提示词注入的场景。 |
| **BabyAGI** | 分布式微提示词队列 | 多阶段 Agent (执行→生成→排序) | 强依赖外部持久内存（向量数据库）。 | 独立静默执行的长周期目标导向系统。 |

---

## 6. 底层哲学总结

无论采用哪种流派，其**底层哲学本质是一致的**：

> **在自然语言极其模糊、不确定的输出中，建立一套能被传统编程语言（Python/Java）精确解析和操控的"确定性契约"。**

这个"契约"的形式从最初的纯文本标记（`Thought:/Action:`）→ JSON 结构约束 → API 原生协议，经历了不断演进。企业级多智能体系统设计应当优先采用原生 Tool Calling 协议，仅在模型不支持时降级到文本 ReAct 方案。
