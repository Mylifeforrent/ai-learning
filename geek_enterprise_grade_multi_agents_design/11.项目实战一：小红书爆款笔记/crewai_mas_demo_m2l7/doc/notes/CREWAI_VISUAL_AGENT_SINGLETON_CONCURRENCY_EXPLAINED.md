# CrewAI 视觉 Agent 为什么不建议做单例

## 1. 问题背景

项目里有这样一段代码：

```python
def get_xhs_visual_analyst() -> Agent:
    """每次调用创建一个新的视觉分析 Agent 实例。因为作者说，并发场景下，如果用单例这里的上下文没清理干净，会有bug"""
    cfg_visual = _agent_cfg("xhs_visual_analyst")
    return Agent(
        config=cfg_visual,
        multimodal=True,
        llm=get_llm(image_model="qwen3-vl-plus", model="qwen3-max-2026-01-23"),
        tools=[AddImageToolLocal()],
    )
```

这个注释的意思是：视觉分析 Agent 不做全局单例，不提前创建一个全局的 `VISUAL_AGENT = Agent(...)` 反复复用，而是每次调用 `get_xhs_visual_analyst()` 时都创建一个新的 `Agent` 对象。

这不是单纯为了“保险”，而是因为 CrewAI 的 `Agent` 对象本身会保存执行过程中的运行时状态。视觉分析任务又是多图并发执行，如果多个视觉任务共享同一个 Agent，就可能出现上下文、工具消息、图片消息或 TaskOutput 串线。

## 2. 本项目里的执行链路

项目中 `get_xhs_visual_analyst()` 在 `src/app/crews/xhs_note/agents.py` 里定义：

```python
def get_xhs_visual_analyst() -> Agent:
    return Agent(
        config=cfg_visual,
        multimodal=True,
        llm=get_llm(image_model="qwen3-vl-plus", model="qwen3-max-2026-01-23"),
        tools=[AddImageToolLocal()],
    )
```

每张图片会创建一个独立的视觉分析 Task：

```python
def build_visual_analysis_task(image: XhsImageInput, idea_text: str) -> Task:
    return Task(
        description=description,
        expected_output=expected_output,
        agent=get_xhs_visual_analyst(),
        output_pydantic=XhsImageVisualAnalysis,
        async_execution=True,
    )
```

关键点有两个：

1. 每张图片一个 Task。
2. 每个图片 Task 都设置了 `async_execution=True`。

在 flow 中，项目会遍历所有图片，为每张图构建一个视觉分析 Task：

```python
tasks: List[Task] = []
for img in idea_request.images:
    tasks.append(build_visual_analysis_task(img, idea_request.idea_text))

summary_task = build_visual_analysis_summary_task(tasks)
tasks.append(summary_task)
```

也就是说，如果用户上传了 5 张图片，项目会创建 5 个视觉分析 Task，再创建 1 个汇总 Task。前 5 个 Task 是异步执行的，最后一个汇总 Task 是同步执行的，并且依赖前面这些 Task 的输出。

## 3. CrewAI 遇到 async_execution=True 时会真的并发调度

本地安装的 CrewAI 版本是 `1.14.5`。在 CrewAI 源码中，执行 task 时有这样的逻辑：

```python
if task.async_execution:
    context = self._get_context(
        task, [last_sync_output] if last_sync_output else []
    )
    async_task = asyncio.create_task(
        task.aexecute_sync(
            agent=exec_data.agent,
            context=context,
            tools=exec_data.tools,
        )
    )
    pending_tasks.append((task, async_task, task_index))
else:
    if pending_tasks:
        task_outputs.extend(
            await self._aprocess_async_tasks(pending_tasks, was_replayed)
        )
        pending_tasks.clear()
```

也就是说，CrewAI 碰到 `async_execution=True` 的 Task，不是立刻等待它结束，而是用 `asyncio.create_task(...)` 把它挂起来，让它和后续异步 Task 一起并发执行。

等遇到一个同步 Task 时，CrewAI 会先等待前面挂起的异步任务完成：

```python
if pending_tasks:
    task_outputs.extend(
        await self._aprocess_async_tasks(pending_tasks, was_replayed)
    )
    pending_tasks.clear()
```

所以在这个项目里，多张图片的视觉分析确实可能同时跑。

## 4. Agent 不是纯配置对象，而是带运行时状态的对象

从 CrewAI 的 `Agent` 源码看，Agent 内部有这些私有状态：

```python
_times_executed: int = PrivateAttr(default=0)
_mcp_resolver: MCPToolResolver | None = PrivateAttr(default=None)
_last_messages: list[LLMMessage] = PrivateAttr(default_factory=list)
```

其中最值得注意的是 `_last_messages`。CrewAI 在一次 Agent 执行完成后，会调用：

```python
save_last_messages(self)
```

而 `save_last_messages(agent)` 会从 `agent.agent_executor.messages` 中提取消息，保存到：

```python
agent._last_messages = sanitized_messages
```

TaskOutput 生成时又会读取：

```python
messages=agent.last_messages
```

而 `agent.last_messages` 返回的是：

```python
return self._last_messages
```

这说明 `Agent` 会保存“最近一次执行”的消息列表。

如果一个 Agent 只被一个 Task 使用，这没有问题。但如果多个并发 Task 共享同一个 Agent，就可能出现这样的情况：

1. 图片 A 的 Task 执行完成，写入 `agent._last_messages = A 的消息`。
2. 图片 B 的 Task 几乎同时执行完成，覆盖成 `agent._last_messages = B 的消息`。
3. 图片 A 生成 TaskOutput 时，可能读到的已经是 B 的 `last_messages`。

这就是“上下文没清理干净”的一种具体表现。

更准确地说，不一定是 CrewAI 忘记清理，而是共享对象里的运行时状态在并发场景下被互相覆盖。

## 5. 更危险的是 agent_executor 会被复用和改写

CrewAI 的 `Agent` 内部还有一个很关键的对象：`agent_executor`。

在创建 executor 时，CrewAI 的逻辑大致是：

```python
if self.agent_executor is not None:
    self._update_executor_parameters(...)
else:
    self.agent_executor = self.executor_class(...)
```

也就是说，如果这个 Agent 已经有 `agent_executor` 了，CrewAI 不会每次都创建一个全新的 executor，而是复用旧 executor，然后更新它的参数。

更新参数时会改这些字段：

```python
if task is not None:
    self.agent_executor.task = task
self.agent_executor.tools = tools
self.agent_executor.original_tools = raw_tools
self.agent_executor.prompt = prompt
self.agent_executor.tools_names = get_tool_names(tools)
self.agent_executor.tools_description = render_text_description_and_args(tools)
self.agent_executor.response_model = (
    (task.response_model or task.output_pydantic or task.output_json)
    if task
    else None
)
self.agent_executor.tools_handler = self.tools_handler
self.agent_executor.request_within_rpm_limit = rpm_limit_fn
```

这意味着如果多个 Task 共用同一个 Agent，就会共用同一个 `agent_executor`。

并发下可能出现这种交错：

1. 图片 A 的 Task 开始执行，把共享 executor 的 `task`、`prompt`、`tools`、`response_model` 设置成 A。
2. 图片 A 正在等待大模型返回。
3. 图片 B 的 Task 开始执行，把同一个 executor 的 `task`、`prompt`、`tools`、`response_model` 改成 B。
4. 图片 A 的执行流程恢复后，读到的 executor 状态可能已经变成 B 的。

可能出现的问题包括：

1. A 的 TaskOutput 拿到 B 的 messages。
2. A 的图片分析上下文里混入 B 的图片路径或图片 base64。
3. A 的结构化输出模型和 executor 当前的 `response_model` 不匹配。
4. 工具调用历史、工具描述、工具 handler 状态被覆盖。
5. 日志、token 统计、事件回调里的 task 和 agent 上下文错位。

这类 bug 通常很难稳定复现，因为它取决于异步任务的调度时机、网络耗时和模型响应耗时。

## 6. 为什么视觉 Agent 比普通文本 Agent 更敏感

视觉 Agent 使用了：

```python
multimodal=True
tools=[AddImageToolLocal()]
```

这个项目里，图片不是一开始就直接作为标准多模态消息传给 CrewAI，而是通过 `AddImageToolLocal` 这类工具把本地图片内容读出来，再让自定义的 `AliyunLLM` 处理工具结果中的图片内容。

大致链路是：

1. Task description 里包含当前图片的 `local_path`。
2. 视觉 Agent 根据任务调用 `AddImageToolLocal`。
3. `AddImageToolLocal` 读取本地图片。
4. 工具结果中包含图片信息，通常包括图片 base64 或 data URL。
5. `AliyunLLM` 在发送给阿里云大模型前，扫描 messages。
6. `_normalize_multimodal_tool_result` 从工具结果里提取图片内容。
7. `AliyunLLM` 把图片内容改造成阿里云视觉模型需要的多模态消息格式。

因此，视觉任务的 messages 里不仅有普通文本，还有图片内容。

如果共享 Agent 导致 messages 串线，后果会比普通文本任务更严重：

1. A 图分析时可能拿到 B 图的图片内容。
2. A 图的工具调用结果可能被 B 图覆盖。
3. `_normalize_multimodal_tool_result` 可能从错误 Task 的消息里提取图片。
4. 阿里云视觉模型收到的图片和当前 Task description 里的 `image_id` 不一致。
5. 最终输出看起来格式正确，但分析的是另一张图。

这类错误比直接报错更危险，因为结果可能“看起来很像真的”。

## 7. 为什么每次 new Agent 可以解决这个问题

每次调用 `get_xhs_visual_analyst()` 都创建一个新的 Agent，意味着每个视觉 Task 拥有自己的：

1. `Agent` 实例。
2. `agent_executor`。
3. `_last_messages`。
4. `tools_handler`。
5. `AddImageToolLocal` 工具实例。
6. `llm` 实例。

这样图片 A 和图片 B 即使并发执行，也不会共享同一个 executor 和 `_last_messages`。

简单说：

```text
推荐方式：

图片 A Task -> Agent A -> Executor A -> Messages A
图片 B Task -> Agent B -> Executor B -> Messages B
图片 C Task -> Agent C -> Executor C -> Messages C
```

如果做成单例，结构会变成：

```text
风险方式：

图片 A Task -> 同一个 Agent -> 同一个 Executor -> 同一个 Messages
图片 B Task -> 同一个 Agent -> 同一个 Executor -> 同一个 Messages
图片 C Task -> 同一个 Agent -> 同一个 Executor -> 同一个 Messages
```

第二种方式在并发下天然有共享状态覆盖风险。

## 8. 网上资料和源码能提供什么证据

我查到的网上资料没有直接说“CrewAI Agent 单例一定有 bug”，但有几个证据能支持这个项目的写法是合理的。

### 8.1 CrewAI 社区关于 Agent 生命周期的讨论

CrewAI 社区里有人问过：在 HTTP API 服务里，Crew、Agent、Task 应该做单例还是每次新建？方法是不是线程安全？

问题里明确提到：

1. 是否应该为这些对象创建 singleton。
2. 还是每次创建新对象。
3. 并发请求下这些方法是否 thread-safe。

社区答复倾向是：如果通过 API 使用，每次创建新实例更好、更可预测。

链接：

https://community.crewai.com/t/whats-the-lifetime-of-agent-instance/5019

### 8.2 CrewAI 社区关于 async_execution=True 的 TaskOutput 串线问题

另一个社区问题描述了使用 `async_execution=True` 时，TaskOutput 中出现其他任务输出的问题。

这个问题和本项目不是完全同一个代码路径，但现象很相似：异步 Task 执行时，不同任务的输出或上下文可能发生错位。

链接：

https://community.crewai.com/t/improper-taskoutput-when-using-async-execution-true-in-tasks/3340

### 8.3 CrewAI 官方文档确认 akickoff 是原生异步执行

CrewAI 官方文档说明，`akickoff()` 是 native async，适合高并发工作负载，会在 task execution、memory operations、knowledge retrieval 等链路中使用 async/await。

链接：

https://docs.crewai.com/en/learn/kickoff-async

这说明项目中使用 `crew.akickoff()` 加上 `async_execution=True` 的确会走异步并发链路，而不是简单顺序阻塞执行。

### 8.4 CrewAI changelog 多次出现 async/context/thread-safe 相关修复

CrewAI changelog 里出现过多次和并发上下文相关的修复，例如：

1. 传播 contextvars 到 async task threads。
2. 修复 cross-process 和 thread-safe locking。
3. 修复 context variable handling 的 race condition。
4. 增加 LLM logging callbacks 的 per-call locks，避免事件交错。

链接：

https://docs.crewai.com/en/changelog

这些 changelog 不能直接证明本项目这个视觉 Agent 单例一定出错，但能说明 CrewAI 在异步、线程、上下文隔离上确实有过真实问题和修复历史。

## 9. 和 Task 单例的关系

不仅 Agent 不建议做单例，Task 也不应该做成单例。

CrewAI 的 `Task` 对象也有运行时状态，例如：

```python
used_tools: int = 0
tools_errors: int = 0
delegations: int = 0
prompt_context: str | None = None
output: TaskOutput | None = Field(default=None)
```

执行过程中还会修改：

```python
self.prompt_context = context
self.processed_by_agents.add(agent.role)
self.output = task_output
```

所以 Task 也不是纯配置对象。

正确方式是：每次业务请求进来，根据当前输入动态创建新的 Task 对象。这个项目目前就是这样做的。

## 10. 为什么普通文本 Agent 看起来风险小一些

项目里普通文本 Agent 也都是每次函数调用创建新 Agent，例如：

```python
def get_xhs_growth_strategist() -> Agent:
    return Agent(
        config=cfg_growth,
        tools=_INTERMEDIATE_TOOLS,
        llm=get_llm(model="qwen3-max-2026-01-23"),
    )
```

这里有一个细节：`_INTERMEDIATE_TOOLS = [IntermediateTool()]` 是模块级共享工具列表。

这看起来也有共享对象，但风险比视觉 Agent 小，原因是：

1. `IntermediateTool` 如果本身是无状态工具，只是把中间内容返回或记录，那么共享风险较低。
2. 普通文本 Agent 没有图片 base64、多模态消息重写这些额外复杂度。
3. 文本任务即使串线，也通常更容易从输出内容上发现。
4. 视觉任务一旦串线，模型可能正常输出一份“看似合理”的分析，排查成本更高。

不过从更稳妥的工程角度看，如果某个工具实例内部有可变状态，也不建议在并发场景下共享同一个工具实例。

## 11. 如果强行做成单例，可能出现什么 bug

假设改成：

```python
_VISUAL_AGENT = Agent(
    config=cfg_visual,
    multimodal=True,
    llm=get_llm(image_model="qwen3-vl-plus", model="qwen3-max-2026-01-23"),
    tools=[AddImageToolLocal()],
)

def get_xhs_visual_analyst() -> Agent:
    return _VISUAL_AGENT
```

多图并发时可能出现：

1. 图片 A 的 TaskOutput.messages 是图片 B 的 messages。
2. 图片 A 的分析结果引用了图片 B 的构图、颜色、主体。
3. `_normalize_multimodal_tool_result` 从 B 的工具结果里提取图片，塞进 A 的请求。
4. `agent_executor.task` 被其他任务覆盖，日志里当前 task 与实际输出不一致。
5. 结构化输出解析偶发失败，因为 `response_model` 被另一个 Task 改写。
6. 工具调用次数、错误次数、回调事件统计错位。
7. 并发量低时不复现，并发量高或模型响应慢时偶发。

这种 bug 的典型特征是：

1. 本地单张图测试正常。
2. 两三张图偶尔正常。
3. 多张图并发、接口压力稍大时开始出现错图、漏图、输出错位。
4. 加日志后又可能因为时序变化而不稳定复现。

## 12. 这个注释可以怎么理解

原注释是：

```python
"""每次调用创建一个新的视觉分析 Agent 实例。因为作者说，并发场景下，如果用单例这里的上下文没清理干净，会有bug"""
```

可以更精确地理解成：

```text
视觉分析任务会并发执行，而 CrewAI Agent/agent_executor 会保存 messages、task、tools、
prompt、response_model 等运行时状态。若多个图片 Task 共享同一个 Agent 单例，
这些状态可能在异步执行中互相覆盖，导致图片上下文或 TaskOutput 串线。
因此每次创建新的视觉 Agent，让每个图片 Task 拥有独立上下文。
```

## 13. 最终结论

这个项目里不把 `get_xhs_visual_analyst()` 做成单例，是合理的。

核心原因不是“创建对象更优雅”，而是：

1. CrewAI 的 `Agent` 有运行时状态。
2. `agent_executor` 会被复用并改写。
3. `last_messages` 保存的是最近一次执行消息。
4. `Task` 本身也有运行时状态。
5. 项目的视觉分析是多图并发执行。
6. 多模态图片链路对 messages 的正确性要求更高。
7. 一旦共享 Agent，图片工具结果和多模态消息可能串到别的 Task。

所以更推荐的设计是：

```text
每次业务请求创建新的 Task。
每个并发视觉 Task 创建自己的视觉 Agent。
每个视觉 Agent 持有自己的 AddImageToolLocal、LLM、agent_executor、last_messages。
最后由同步 summary Task 等待并汇总前面所有视觉 Task 的输出。
```

这能用少量对象创建成本，换取更强的并发隔离和更低的排查成本。
