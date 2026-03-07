# AI Agent 框架提示词工程技巧与底层原理全景对比分析

在当今的大模型（LLM）驱动的 Agent 开发中，不同的框架为了让大模型更好地遵循指令、完成指定的任务流、以及精准地调用外部工具，演化出了多种不同的提示词（Prompt）工程流派和技巧。

本文将为您详细展开讲解 CrewAI 中的 `Thought:`、`stop: [Observation]`，AutoGPT 和 OpenAI 的 JSON 格式约束，并扩展介绍如 Anthropic Claude 推荐的 XML 标签等其他优秀框架的提示词技巧，帮助您全面了解其背后的技术原理。

---

## 1. CrewAI (基于 ReAct 模式) 的提示词技巧

CrewAI 等强调过程推理的框架，很大程度上受 ReAct (Reason + Act) 论文的启发。大模型被要求在执行任何外部操作之前，先“大声思考”。

### 1.1 `Thought:` 前缀的原理
**现象**：如果你查看 CrewAI 的底层发给大模型的提示词模板，总是能在末尾或者每个步骤的开头看到它强制要求或者强提示大模型输出 `Thought: `（思考：）。

**原理解析**：
*   **引导思维链 (Chain-of-Thought, CoT)**：大模型本质上是“概率性的文本接龙”。如果直接让大模型给出“行动（Action）”，它往往会跳过中间推理过程，导致它选错工具或传错参数。通过在提示词模板中预置 `Thought:`，强制大模型必须先生成一段自我推理的文字（例如：“用户让我查天气，我需要先调用 `get_weather` 工具，参数应该是 `Beijing`”）。
*   **格式对齐**：在 ReAct 循环中，解析器极度依赖固定的文本格式来提取信息。常见的格式约定为：
    *   `Thought:` (思考过程)
    *   `Action:` (调用的工具名称)
    *   `Action Input:` (给工具的参数格式)
    强制大模型生成 `Thought:` 是整个状态机顺利流转的锚点。

### 1.2 `stop: [Observation]` 的防幻觉机制
**现象**：在向 OpenAI / 本地大模型发起 API 请求时，传入的参数中往往会设置 `stop=["Observation"]`（或 `Observation:`）。

**原理解析**：
*   **强制让出控制权**：大模型的本能是**续写文本**。当它输出了 `Action:` 和 `Action Input:` 告诉系统它想用什么工具后，如果不加以阻止，它会根据常识“自己编造”一个结果接着往下写。例如它查天气，会自己接着写 `Observation: 今天天气晴朗`。
*   **截断与接管**：通过设置 stop 词，大模型在生成到 `Observation` 这个词的一瞬间，API 生成就会立即终止停止计费。本地框架（如 CrewAI 的解析器）接管程序控制权，从生成的文本中提取出 `Action`，在本地运行 Python 代码（如实际发起 HTTP 天气请求），得到真实结果后，**由 Python 代码将结果拼接在 `Observation: [真实降雨15度]` 后面**，再把整段对话历史重新发给大模型。
*   **这就是 Agent “循环执行”的实质**。

---

## 2. OpenAI Function Calling 与 AutoGPT 的 JSON 规范流派

早期的 ReAct 模式（像 LangChain 早期的 zero-shot-react-description 和 CrewAI 的默认模式）需要大模型输出特定的文本格式，然后用正则表达式去匹配提取动作。这种方式极其脆弱，大模型稍微多输出一个空格或换行，正则匹配就会失败导致 Agent 崩溃。

为了解决这个问题，以 AutoGPT 和后来的 OpenAI 官方 API 为代表，掀起了 **JSON 化** 的浪潮。

### 2.1 AutoGPT 定义 JSON 格式的原理
**原理**：在 OpenAI 官方推出 Function Calling 前，AutoGPT 就在提示词中硬性规定大模型**必须且只能**输出高强度的结构化 JSON 对象。

**内部提示词结构**：AutoGPT 给大模型的 System Prompt 中包含了类似以下的 Schema 要求：
```json
{
  "thoughts": {
    "text": "我对当前任务的理解...",
    "reasoning": "为什么我要这么做...",
    "plan": "- 第一步\n- 第二步",
    "criticism": "我这样做的缺点是...",
    "speak": "给用户展示的一段语音/文本"
  },
  "command": {
    "name": "search_internet",
    "args": { "query": "极客时间 深度学习" }
  }
}
```
**为什么这样做更加规范？**
*   **规避正则解析难题**：Python 的 `json.loads()` 远比复杂的正则表达式稳健。
*   **强制结构化反思**：通过把 `reasoning`、`plan`、`criticism` 固定在 JSON Schema 里，AutoGPT 强制大模型在每一步必须进行深度反思（类似强制写八股文）。

### 2.2 OpenAI 原生 Function Calling 原理
**原理**：OpenAI 后期在 API 甚至模型底层训练层面（微调），直接原生支持了 JSON 格式的工具调用。这被称为 Function Calling (现在的 Tool Calling)。

*   **Schema 注入**：你在 API 请求的 `tools` 参数里，按 JSON Schema 格式传入你有哪些 Python 函数，以及它们的参数名为啥、类型是啥。
*   **底层指令隔离**：与以前把工具列表生硬拼接到 System Prompt 末尾不同，Tool Calling 在模型底层对工具的抽象进行了专门处理。大模型能够更精准地理解“这是一个工具箱，我不在日常聊天中，我要输出一个 JSON 格式的工具请求”。
*   **无需 `stop` 词的巧技**：在开启了 Tool Calling 后，模型返回的 `finish_reason` 不再是常规的 `stop`，而是特殊的 `tool_calls`。此时框架就知道大模型在请求挂起，等待你返回工具结果给她。这就优雅地替代了 `stop: [Observation]` 的“Hack”技巧。

---

## 3. 其他优秀框架及生态的提示词技巧

在整个生态中，为了更好地调度大模型，还衍生出了诸多其他流派的技巧。

### 3.1 Anthropic Claude 的 XML Tags 技巧 
**背景与原理**：如果你使用 Claude 作为 Agent 的底层驱动器（比如使用 LangGraph 中的 XML Agent），你会发现它的提示词里充满了 `<thought>`、`<tool_use>`、`<result>` 等 XML 标签。

**为何推荐 XML？**
*   **Claude 数据集的偏好**：Anthropic 官方极度推荐使用 XML 格式，因为 Claude 系列在预训练时接触了大量 XML 和 HTML 数据，它对闭合标签 (`<tag>内容</tag>`) 的结构理解远胜于 Markdown 或 JSON。
*   **容错率更高**：JSON 漏一个引号或者右括号整个解析就会崩溃；而 XML 即便有些细微缺陷，使用流式正则获取 `xml` 标签内的内容也非常稳定。
*   **Prompt 隔离**：利用 `<context>`、`<instructions>` 标签，可以清晰地为大模型划分哪些是背景，哪些是核心指令，减少指令污染。

### 3.2 BabyAGI 的任务驱动拆解 (Task-Driven) 技巧
**原理**：BabyAGI 框架弱化了单一 Agent 的复杂内部反思，而是通过专门的 Prompt 聚焦于“任务列表的维护”。

**它其实有三个不同的 Agent（实则为三个不同提示词驱动的调用）：**
1.  **Execution Agent**：拿到当前的第一优先级任务，执行它。
2.  **Task Creation Agent**：带着刚才执行的结果，和总体目标，生成接下来还能做哪些新任务。
3.  **Prioritization Agent**：对任务列表重新排序去重。

**启示**：把一个需要写 1000 字超大 Prompt 的全能大 Agent，拆成了 3 个各只有 100 字 Prompt 的专职 Agent。通过外部向量数据库或者内存数组进行联动，极大降低了对单次大模型上下文理解的压力。

---

## 4. 总结对比

| 框架/技术流派 | 核心提示词技术 | 优点 | 缺点 |
| :--- | :--- | :--- | :--- |
| **CrewAI / 裸 ReAct** | `Thought:` 强制发散思维<br>`stop:[Observation]` 截断 | 兼容性最佳，即便是开源小模型也能通过文本跟读的方式运行。 | 解析脆弱，容易被特殊符号打乱正则提取。容易触发“幻觉”无视 stop 词。 |
| **AutoGPT** | 完全基于 JSON Schema 约定结构和 Command 输出 | 极度严谨，内部状态高度透明化（可见 Plan, Criticism）。 | 严重消耗 Token；较差/较小的模型极易输出格式错误的 JSON（如引号未转义）。 |
| **OpenAI Tool Call** | API 底层 JSON 协议支持，`finish_reason=tool_calls` | 最具现代感，无需手写复杂的提取逻辑，调用成功率极最高。 | 必须依赖支持 Tool Calling 功能的前沿大模型（如 GPT-4 / Claude 3）。 |
| **Anthropic Claude** | 使用 `<XML>` 标签包裹指令及规划 | 对于指令分治和防御提示词注入极强，流式提取友好。 | 具有平台特异性（主要适用于 Claude，GPT 并不绝对偏好此格式）。 |
| **BabyAGI** | 目标与任务拆分的动态 Prompt 队列 | 降低了单次 Prompt 的压力，可跑无限时任务。 | 流程固定，不适合需要快速单次强推理的动作。 |

无论是利用 `stop` 截断、JSON 约束 还是 XML 封装，其**底层哲学都是一致的**：**在自然语言的模糊性中，建立一套可以被传统编程语言（Python/Java）解析和操控的“确定性契约”。**企业级多智能体设计应当根据底层大模型的能力组合使用这些技术。
