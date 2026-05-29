![工具让 AI 应用真正完成任务](imgs/image.png)

![Native Function Calling vs ReAct](imgs/image1.png)

# Function Calling 和 ReAct 的对比理解

第二张图里的对比，本质上不是在比较两个“模型能力”，而是在比较两种使用工具的工程范式：

- **Native Function Calling**：让模型直接把用户意图转换成某个工具调用的结构化参数，比如 JSON。
- **ReAct**：让模型在执行过程中不断经历 `Thought -> Action -> Observation`，根据工具返回结果继续判断下一步，直到得到最终答案。

所以这些对比是从它们的**执行流程**推导出来的。

## 1. 为什么 Function Calling 更快、token 更少？

Function Calling 的路径通常很短：

```text
用户输入 -> LLM 判断要调用哪个函数 -> 输出结构化参数 -> 程序执行工具 -> 返回结果
```

它不需要把中间推理过程一轮轮展开，也不需要多次调用模型来修正策略。因此在任务明确时，它的速度和成本通常更好。

例如用户问：

> 帮我查一下北京今天的天气。

模型只需要生成一次工具调用：

```json
{
  "tool": "get_weather",
  "args": {
    "city": "北京",
    "date": "today"
  }
}
```

这里用户目标很明确，工具也很明确，参数也容易抽取。使用 ReAct 反而可能显得“绕远”。

## 2. 为什么 Function Calling 适合单一、明确场景？

因为 Function Calling 更像“意图到 API 参数”的映射。只要问题可以被稳定地归类到某个工具，并且参数边界清楚，它就很好用。

典型场景：

- 查天气：城市、日期明确。
- 查订单：订单号明确。
- 创建日程：标题、时间、参与人明确。
- 查询库存：商品 ID 或名称明确。

例如：

```text
用户：帮我把明天下午 3 点和张三开会加入日历。
```

模型可以直接生成：

```json
{
  "tool": "create_calendar_event",
  "args": {
    "title": "和张三开会",
    "date": "明天",
    "time": "15:00",
    "attendees": ["张三"]
  }
}
```

这种任务的关键不是复杂推理，而是**参数抽取准确**。

## 3. 为什么 Function Calling 的可解释性相对弱？

图里说 Function Calling 偏“黑盒”，不是说它完全不可控，而是说它通常只暴露最终工具调用：

```json
{
  "tool": "search",
  "args": {
    "query": "某个问题"
  }
}
```

你能看到它选了哪个工具、填了哪些参数，但不一定能看到它为什么这样选、有没有考虑过其他工具、是否漏掉了前置条件。

如果模型一开始就把工具选错，或者参数生成错，后面的执行结果就会被带偏。

例如：

```text
用户：查一下苹果最近一季财报，并总结 iPhone 业务表现。
```

如果模型误把“苹果”理解成水果公司，或者只搜索了 “apple revenue” 而没有限定财报季度，就会影响结果质量。Function Calling 本身不会天然提供一个“发现不够、继续修正”的循环，除非我们额外在工程里设计重试、校验和多步流程。

不过也要注意：现代大模型，尤其是具备 reasoning 能力的模型，已经可以在输出 function call 之前做更充分的内部推理。因此 Function Calling 的效果比早期好很多。它的问题更多是**默认流程偏一次性**，而不是模型完全不能思考。

## 4. 为什么 ReAct 更适合复杂、不确定场景？

ReAct 的核心是把任务拆成多轮：

```text
Thought：我需要先查什么？
Action：调用某个工具。
Observation：工具返回了什么？
Thought：结果够不够？下一步做什么？
Action：继续调用工具。
...
Final Answer：最终回答。
```

它适合那些一开始无法确定完整路径的任务。比如：

> 帮我找一个下周末从上海出发、预算 3000 以内、适合亲子游的目的地，并给出交通和住宿建议。

这个任务不是一次 API 调用能解决的。模型可能需要：

1. 判断下周末的具体日期。
2. 搜索上海出发的高铁或机票价格。
3. 筛选适合亲子游的目的地。
4. 查询天气、酒店价格、景点开放情况。
5. 如果预算超了，回退并换候选城市。
6. 最后整合成方案。

这就是 ReAct 的优势：它可以根据每一步的观察结果动态调整路线。

一个简化的 ReAct 过程可能是：

```text
Thought：用户关心预算、亲子、下周末，我需要先确定日期和候选目的地。
Action：search("上海出发 下周末 亲子游 高铁 预算 3000")
Observation：杭州、南京、常州、安吉比较常见。

Thought：需要比较交通成本和住宿成本，先查杭州和南京。
Action：search("上海 到 杭州 高铁 价格 周末")
Observation：高铁价格较低，时间短。

Thought：杭州交通便宜，但热门酒店可能贵，需要查住宿。
Action：search("杭州 亲子酒店 周末 价格")
Observation：部分酒店超预算，经济型方案仍可行。

Thought：信息足够，可以给出主推方案和备选方案。
Final Answer：推荐杭州，备选南京，并说明预算拆分。
```

这里的关键不是“能不能调用搜索工具”，而是模型能不能在搜索结果不完整、不确定、甚至互相冲突时继续迭代。

## 5. 为什么 ReAct 更耗 token、成本更高？

ReAct 需要把中间步骤表示出来，并且通常会多次调用模型和工具：

```text
Thought + Action + Observation
Thought + Action + Observation
Thought + Action + Observation
Final Answer
```

每多一轮，都会增加：

- 模型输入 token：要把历史步骤、工具结果继续塞回上下文。
- 模型输出 token：要生成下一步判断或最终回答。
- 工具调用成本：搜索、数据库、浏览器、代码执行等工具都可能有额外成本。
- 延迟：每轮都要等待模型和工具返回。

所以 ReAct 不是“永远更高级”，而是适合用在 Function Calling 一次做不稳的地方。

## 6. 两者不是互斥关系

实际工程中，常见做法是把它们组合起来：

- 简单任务：直接 Function Calling。
- 复杂任务：用 ReAct 做多步规划和观察。
- 每个 Action：底层仍然可以是一次 Native Function Calling。

也就是说，ReAct 里的 `Action` 经常就是一个 function call。

可以理解为：

```text
Function Calling 解决的是：怎么把一次工具调用写对。
ReAct 解决的是：什么时候调用哪个工具，以及调用完之后下一步怎么办。
```

## 7. 一个更具体的对比例子

假设用户问：

> 帮我查一下用户 10086 的最近一笔订单状态。

这个任务适合 Function Calling：

```json
{
  "tool": "get_latest_order",
  "args": {
    "user_id": "10086"
  }
}
```

因为目标明确、工具明确、参数明确。

但如果用户问：

> 用户 10086 说他的包裹一直没到，帮我判断问题出在哪里，并给他一个回复建议。

这个任务更适合 ReAct，因为它可能需要多步排查：

```text
Thought：先查用户最近订单。
Action：get_latest_order(user_id=10086)
Observation：订单 A，状态为已发货。

Thought：需要查物流轨迹。
Action：get_shipping_trace(order_id="A")
Observation：物流在中转站停留 3 天。

Thought：需要判断是否异常，以及是否有售后规则。
Action：get_after_sales_policy(reason="物流停滞")
Observation：超过 72 小时可建议用户申请催派或补偿券。

Final Answer：包裹问题大概率是物流中转停滞，建议客服这样回复用户……
```

这个例子里，第一次工具调用之后还不能直接回答，必须根据 Observation 决定下一步，这就是 ReAct 的典型价值。

## 8. 总结

第二张图的对比可以这样记：

| 维度 | Native Function Calling | ReAct |
| --- | --- | --- |
| 执行方式 | 一次或少数几次结构化工具调用 | 多轮思考、行动、观察 |
| 优势 | 快、便宜、输出结构稳定 | 能处理复杂任务和不确定信息 |
| 成本 | token 和延迟较低 | token、延迟和工具调用成本更高 |
| 准确性来源 | 参数抽取和工具选择要一次做对 | 可以根据观察结果迭代修正 |
| 可解释性 | 主要看到最终工具调用 | 可以看到任务推进过程和中间依据 |
| 适合场景 | 简单、边界清楚、参数明确 | 多步骤、结果不确定、需要探索 |

一句话总结：

> Function Calling 更像“把一句话翻译成一次 API 调用”；ReAct 更像“边查边想边行动的任务执行循环”。

![alt text](imgs/image2.png) 
1. 从“原子性”到“语义完整性”
传统 API：追求高内聚低耦合，极度原子化。比如获取用户信息 get_info_by_id(id)，更新状态 update_status_by_id(id, status)。

Agent Tool：大模型讨厌繁琐的多次往返组合。工具设计需要语义完整。比如直接设计一个 update_user_status_by_name(name, status)，在工具内部去完成“查 ID -> 校验 -> 更新”的闭环，而不是让大模型分三步去调三个不同的原子工具。

2. 从“强类型结构”到“可描述的简单结构”
传统 API：入参经常是复杂的强类型对象或深层嵌套的 JSON。

Agent Tool：入参越简单、越扁平越好，最好都是基础类型（String, Int），因为每个参数都会消耗 Token 且增加模型理解失败的概率。更关键的是，每个参数都必须附带详尽的自然语言描述（Description），告诉模型这个字段填什么、不能填什么。

3. 从“状态码”到“建设性报错（Constructive Error）”
传统 API：报错时返回类似 error_code=1001 或 Null。程序代码捕获到 1001 后会走特定的 catch 逻辑。

Agent Tool：如果你给大模型返回一个 1001 或者空的字符串，它会直接懵圈，然后开始胡言乱语（幻觉）或者陷入死循环。面向 Agent 的报错，必须是自然语言的“指导意见”。例如返回："操作失败：时间参数格式错误，你输入了 2026/01/01，请你修改为 YYYY-MM-DD 的格式后重新调用本工具。"大模型看到这句话，立刻就能自我纠错（Self-Correction）并重试。
![alt text](imgs/image3.png) 


![alt text](imgs/image4.png) 

![alt text](imgs/image5.png)

假设你写了一个 FileWriterTool 让 Agent 帮用户保存文件。你绝对不能在 Tool 的参数里暴露出 user_id，指望大模型在调用时乖乖地把当前用户的 user_id 传给你。大模型是极其容易被提示词注入（Prompt Injection）攻击的，它完全有可能被诱导去读写其他用户的数据！

正确的企业级解法：隐式上下文挂载与 Hook 拦截。

我们来看看项目中是如何通过优雅的代码设计解决这个问题的：

项目代码：https://github.com/kid0317/crewai_mas_demo/blob/main/m2l8/m2l8_tools_call.py

1. 使用 contextvars 管理 API 请求级上下文
在 m2l8_context.py 中，我们利用 Python 的原生库创建了线程 / 协程安全的上下文变量，确保高并发下不同用户的请求彻底隔离。

# m2l8_context.py 核心代码
from contextvars import ContextVar
from typing import Optional
 
# 用户 ID 上下文变量：标识当前请求的用户
user_id = ContextVar[Optional[str]]("user_id", default=None)
# 任务 ID 上下文变量：标识当前执行的任务
task_id = ContextVar[Optional[str]]("task_id", default=None)
2. 通过 Hook 机制透明接管工具执行路径
在 m2l8_tools_call.py 中，我们在大模型调用工具之前（@before_tool_call），拦截它的请求，从当前上下文中静默提取真实安全的 user_id，动态修改文件读写路径。大模型从头到尾都不知道底层做了路径隔离，既降低了它的认知负担，又保证了绝对的安全。

# m2l8_tools_call.py 核心代码示例
import sys
import os
from pathlib import Path
from crewai.hooks import before_tool_call
from m2l8_context import user_id
 
WORKSPACE_BASE_PATH = Path("./workspace").resolve()
 
@before_tool_call
def secure_workspace_hook(tool_call, agent):
    """
    工具调用前的安全拦截 Hook：
    确保大模型只能操作当前 User 专属的工作空间目录，防止路径穿越攻击。
    """
    # 1. 从安全的上下文中获取当前真实的租户 / 用户 ID
    current_user = user_id.get()
    if not current_user:
        raise ValueError("安全拦截：上下文中未找到有效的 user_id")
 
    # 2. 构建该用户专属的沙箱路径
    user_workspace = (WORKSPACE_BASE_PATH / current_user).resolve()
 
    # 3. 拦截并覆写工具的入参（以写入文件工具为例）
    if tool_call.tool_name == "FileWriterTool":
        raw_path = tool_call.arguments.get("file_path", "")
        # 将大模型以为的相对路径，重定向到绝对安全的沙箱内
        safe_target_path = (user_workspace / raw_path).resolve()
 
        # 安全校验：防止大模型传入 "../../../etc/passwd" 这种路径穿越
        if not str(safe_target_path).startswith(str(user_workspace)):
             raise PermissionError("安全拦截：检测到非法越权路径访问！")
 
        tool_call.arguments["file_path"] = str(safe_target_path)
这套机制是企业级 AI 中台建设中，保障多租户工具调用安全的标准方案！

四、 避坑指南：最佳实践与反模式
写工具容易，写出能让 Agent 稳定跑通全链路的工具很难。最后，我们总结一下在工具设计中最容易踩坑的“反模式”，以及对应的“最佳实践”。

🚫 严重破坏稳定性的“反模式”
全能工具（God Tool）
问题：写一个工具叫 DatabaseManager，然后让大模型通过传入一个 action_type 字符串（值为 insert, delete, query, update）来决定干什么。

后果：严重破坏单一职责原则。大模型极容易在使用时搞混不同 action 对应的必填参数，导致频频报错。

多层转义的参数（Multi-level Escaping）
问题：工具的一个参数要求传入一段 JSON 格式的字符串，而这个 JSON 字符串内部某个字段的值，又是另一段 JSON 字符串。

后果：转义符 \" 会把大模型绕晕。大模型在生成多层嵌套转义的字符串时，出错率（格式残缺）呈指数级上升。

深嵌套的入参（Deeply Nested Parameters）
问题：参数结构是 Map 里面套 List，List 里面再套 Map。

后果：增加了模型理解和生成的成本，应该极力将参数“拍平（Flatten）”。

沉默的失败（Silent Failure）
问题：工具执行报错时，生硬地返回一个空字符串 "" 或是底层的 NullPointerException 堆栈。

后果：Agent 不知道发生了什么，可能会反复重试同样的错误操作，直到把 max_iterations 耗尽卡死。

上下文炸弹（Context Bomb）
问题：读取一个文件或查询一次数据库时，不加限制地将几万行数据、数十兆的文件直接作为工具的 Observation 扔回给 Agent。

后果：瞬间撑爆大模型的 Context Window（上下文窗口），导致本次对话强制中断报错，或者模型被海量数据淹没，彻底遗忘当前的任务目标。

💡 稳健落地的“最佳实践”
建设性报错（Constructive Error Handling）：捕获工具底层的所有异常，将其转化为对大模型友好的自然语言提示。告诉它“错在哪了”以及“接下来你应该尝试怎么做”。

设计摘要或分页机制（Pagination & Summarization）：面对可能返回海量数据的工具（如读大文件、查数据库），强制在工具内部实现“分页返回”或者“关键信息摘要”。例如给工具增加一个 page_size 和 page_number 参数，并引导 Agent 如果发现内容未读完，需要翻页查询；或者在工具底层先用一个小模型将长文本压缩后，再返回给主流程的 Agent。