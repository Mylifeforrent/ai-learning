# AI Agent 框架提示词工程技巧与底层原理全景对比分析 (含实战代码范例)

在当今的大模型（LLM）驱动的 Agent 开发中，不同的框架为了让大模型更好地遵循指令、完成指定的任务流、以及精准地调用外部工具，演化出了多种不同的提示词（Prompt）工程流派和技巧。

本文将为您详细展开讲解 CrewAI 中的 `Thought:`、`stop: [Observation]`，AutoGPT 和 OpenAI 的 JSON 格式约束，并扩展介绍如 Anthropic Claude 推荐的 XML 标签等其他优秀框架的提示词技巧，帮助您全面了解其背后的技术原理及**实际代码应用**。

---

## 1. CrewAI (基于 ReAct 模式) 的提示词技巧

CrewAI 等强调过程推理的框架，很大程度上受 ReAct (Reason + Act) 论文的启发。大模型被要求在执行任何外部操作之前，先“大声思考”。

### 1.1 原理解析
*   **引导思维链 (Chain-of-Thought, CoT)**：大模型本质上是“概率性的文本接龙”。如果直接让大模型给出“行动（Action）”，它往往会跳过中间推理过程，导致它选错工具或传错参数。通过在提示词模板中预置 `Thought:`，强制大模型必须先生成一段自我推理的文字。
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
*(Python 代码层面直接 `parsed_data = json.loads(response)` 即可，稳健性比正则高了数百倍)*

### 2.2 OpenAI 原生 Function Call (Tool Calling) 案例

**原理**：OpenAI 在模型底层直接支持了结构化的工具分发。底层训练教会了模型区分“普通对话”和“工具调用”。开发者不再需要把复杂的 JSON 样例塞进系统提示词，而是在请求参数的 `tools` 字段中传入 JSON Schema。大模型会自动识别，而在它判断需要调用工具时，会返回一个要求工具调用的独特状态。

**💻 OpenAI API 代码示例与抓包结果**
```python
import json
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

# 1. 告诉大模型你有什么工具 (按照格式定义 JSON Schema)
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

# 2. 发起请求
response = client.chat.completions.create(
  model="gpt-4o",
  messages=[{"role": "user", "content": "北京天气如何？"}],
  tools=tools,
  tool_choice="auto" 
)

# 3. 查看大模型输出: 它没有返回常规对话文本，而是返回了特殊挂起状态 tool_calls！
message = response.choices[0].message
print(message.tool_calls)
# 输出结构类似: 
# [ToolCall(id='call_xyz123', function=Function(arguments='{"location":"Beijing"}', name='get_weather'), type='function')]

# 框架层接下来会自动提取 json.loads(message.tool_calls[0].function.arguments) 来运行本地代码
```

---

## 3. Anthropic Claude 的 XML Tags 流派

Anthropic (Claude 的开发商) 明确推荐使用 XML 标签来包裹提示词和工具调用，这得益于其预训练数据集对 XML 的高敏锐度。这在 LangChain 的 XML Agent 中也有大量应用。

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
task_list = ["任务1: 搜索AI课程", "任务2: 查阅官方文档汇总之"]

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
| **CrewAI/裸ReAct** | 结构化文本 | `Thought:`<br>`stop=["Observation"]` | 需编写庞大复杂的正则表达式提取器，易碎。 | 兼容各种无法输出标准 JSON 的开源小模型。 |
| **AutoGPT** | 深层 JSON 对象 | 强约束格式 (`thoughts`, `command` 字段) | `json.loads()`，偶尔需要单独处理转义字符导致的系统崩溃。 | 需要模型强反思 (`criticism`/`plan`) 的全自动脱机操作。 |
| **OpenAI 工具调用** | 原生 API 对象 | `finish_reason="tool_calls"` | 无需解析原始文本，SDK 方法直接返回 Python dict/object 对象。 | 现代化商业应用首选套件，最为稳定且成功率极高。 |
| **Anthropic Claude** | XML 变体 | `<tool_use>`, `<thought>` 等闭合标签 | 需要利用 XML Parser 或正则寻找结束符拦截流式响应。 | Claude 平台上的应用，以及防御“提示词注入攻击”要求极高的安全场景。 |
| **BabyAGI** | 分布式微提示词队列 | 多阶段 Agent (执行->生成任务->排序打分) | 放弃上下文，强依赖外部持久内存组件（如 Pinecone 向量数据库）。 | 适合不需要随时跟人工交流对话、能够独立静默执行数天的目标导向型系统。 |
