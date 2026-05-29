# FastAPI await、事件循环与 worker 请求处理说明

## 先看这段代码

项目里的小红书笔记流程中有这样的代码：

```python
# Step 1：全部图片视觉分析（并发）
visual_by_id, visual_summary = await _run_visual_analysis_phase(idea_request)

# Step 2：全部图片编辑方案（并发）
edit_by_id, edit_summary = await _run_image_edit_phase(idea_request, visual_by_id)
```

这两行都有 `await`，但这不表示它们会并行执行。

实际执行顺序是：

```text
先执行 Step 1
等待 Step 1 完成，拿到 visual_by_id 和 visual_summary
再执行 Step 2
等待 Step 2 完成，拿到 edit_by_id 和 edit_summary
```

原因是 Step 2 依赖 Step 1 的结果：

```python
_run_image_edit_phase(idea_request, visual_by_id)
```

如果 Step 1 没有先完成，Step 2 就拿不到 `visual_by_id`。

所以这两行之间是串行关系，不是并行关系。

## await 不等于并行

`await` 的核心含义不是“让下一行一起跑”，而是：

```text
当前协程执行到这里，需要等待一个异步操作完成；
等待期间，当前协程暂停；
事件循环可以去调度其他已经就绪的任务；
等被 await 的操作完成后，再回到这里继续往下执行。
```

也就是说，`await` 表达的是“异步等待”，不是“自动并行”。

如果没有 `await`：

```python
visual_result = _run_visual_analysis_phase(idea_request)
```

拿到的通常不是真正的结果，而是一个 coroutine 对象：

```text
<coroutine object ...>
```

此时 `_run_visual_analysis_phase()` 里的异步逻辑还没有被完整等待执行，后续代码也拿不到 `visual_by_id`。

写上 `await` 后：

```python
visual_by_id, visual_summary = await _run_visual_analysis_phase(idea_request)
```

含义是：

```text
我要等待这个异步函数完成；
完成后把返回值解包成 visual_by_id 和 visual_summary；
然后继续执行下一行代码。
```

## await 真正起到的作用

`await` 至少有两个重要作用。

第一，等待异步任务完成并拿到结果。

例如：

```python
visual_by_id, visual_summary = await _run_visual_analysis_phase(idea_request)
```

这行会等 `_run_visual_analysis_phase()` 执行完成，然后拿到它返回的结果。

第二，等待期间让出事件循环的执行权。

当代码执行到某个真正的异步等待点，比如：

```python
result = await asyncio.wait_for(crew.akickoff(), timeout=timeout)
```

当前协程会暂停。它不会一直占着事件循环空等。

这时事件循环可以先去处理别的任务，例如：

```text
其他 HTTP 请求
其他数据库查询
其他外部 API 调用
其他已经就绪的 coroutine
```

等 `crew.akickoff()` 返回结果后，事件循环再恢复当前协程，从 `await` 后面继续执行。

所以可以把 `await` 理解成：

```text
我在这里等一个结果；
但我等待时，不独占事件循环；
你可以先去执行别的任务；
结果回来后，再叫我继续往下跑。
```

## 什么时候才是并行或并发执行

如果希望两个没有依赖关系的异步任务并发执行，通常需要显式创建任务，例如：

```python
task1 = asyncio.create_task(func1())
task2 = asyncio.create_task(func2())

result1 = await task1
result2 = await task2
```

或者使用：

```python
result1, result2 = await asyncio.gather(
    func1(),
    func2(),
)
```

这类写法才表示：

```text
func1 和 func2 可以一起开始；
两个都完成后，再继续往下执行。
```

但在当前小红书流程里，Step 2 需要 Step 1 的 `visual_by_id`，所以不适合直接这样并发：

```python
await asyncio.gather(
    _run_visual_analysis_phase(idea_request),
    _run_image_edit_phase(idea_request, visual_by_id),
)
```

因为 `visual_by_id` 还没有产生。

## 当前代码里的“并发”指什么

这两行外层是串行：

```text
Step 1 完成后，才进入 Step 2
```

但每个 phase 内部可能有多张图片任务并发。

在当前项目中，单张图片的视觉分析任务是这样构造的：

```python
return Task(
    description=description,
    expected_output=expected_output,
    agent=get_xhs_visual_analyst(),
    output_pydantic=XhsImageVisualAnalysis,
    async_execution=True,
)
```

单张图片的编辑方案任务也是：

```python
return Task(
    description=description,
    expected_output=expected_output,
    agent=get_xhs_image_editor(),
    output_pydantic=XhsImageEditPlan,
    async_execution=True,
)
```

所以更准确的理解是：

```text
Step 1 和 Step 2 之间：串行
Step 1 内部多张图片视觉分析：并发
Step 2 内部多张图片编辑方案：并发
```

也就是：

```text
先并发分析所有图片
等所有视觉分析结果完成
再并发生成所有图片编辑方案
等所有编辑方案完成
再进入后续内容生成流程
```

## FastAPI 如何同时处理多个请求

FastAPI 运行在 ASGI 服务器上，常见服务器是 Uvicorn。

当两个请求进入 FastAPI 时，可以理解为：

```text
请求 A 进来
请求 B 进来

ASGI 服务器把它们包装成可调度的协程任务
事件循环统一管理这些任务
哪个任务遇到 await 暂停了
事件循环就切去执行其他已经就绪的任务
```

例如接口中有：

```python
@app.get("/demo")
async def demo():
    result = await call_llm_api()
    return result
```

请求 A 执行到：

```python
await call_llm_api()
```

它需要等待外部 LLM 接口返回。这段时间 CPU 没必要一直空等。

于是请求 A 对应的协程暂停，把控制权还给事件循环。

这时请求 B 也来了，事件循环就可以先处理请求 B。

等请求 A 的 LLM 结果返回后，事件循环再恢复请求 A，从 `await` 后面继续执行，并最终返回响应。

所以异步模型不是：

```text
一个请求固定占用一个线程，从头等到尾
```

而更像：

```text
一个事件循环管理很多请求协程；
哪个请求在等 IO，就先挂起；
事件循环去处理其他已经就绪的请求；
结果回来后再恢复原来的请求。
```

这就是 FastAPI 适合处理大量 IO 型任务的原因，例如：

```text
调用数据库
调用 Redis
调用外部 HTTP API
调用大模型接口
等待文件上传读取
```

## 和传统一个请求一个线程的区别

传统同步 Web 模型常见理解是：

```text
请求 A 进来 -> 分配一个线程处理 A
请求 B 进来 -> 分配另一个线程处理 B

A 如果在等待数据库，这个线程也被 A 占着
B 如果在等待外部 API，这个线程也被 B 占着
```

这种模型简单直观，但当大量请求都在等待 IO 时，会占用很多线程。

FastAPI 的异步模型则更像：

```text
请求 A 进来 -> 创建协程任务 A
请求 B 进来 -> 创建协程任务 B

A 等 IO 时让出事件循环
事件循环处理 B
B 等 IO 时也让出事件循环
事件循环处理其他任务
A 的 IO 完成后，恢复 A
B 的 IO 完成后，恢复 B
```

它的优势在于：

```text
大量请求都在等待 IO 时，不需要为每个等待中的请求都占住一个线程。
```

## Uvicorn worker 和事件循环的关系

如果启动 Uvicorn 时使用多个 worker：

```bash
uvicorn app.main:app --workers 4
```

可以大致理解为：

```text
主进程
  -> worker 1 进程：一个主事件循环
  -> worker 2 进程：一个主事件循环
  -> worker 3 进程：一个主事件循环
  -> worker 4 进程：一个主事件循环
```

每个 worker 通常是一个独立进程。

每个 worker 通常有一个主线程运行事件循环。

这个事件循环负责调度该 worker 接收到的多个异步请求任务。

所以可以这样理解：

```text
一个 Uvicorn worker 主要靠一个事件循环线程管理很多 async request。
```

但要注意，这不等于 worker 进程里绝对只有一个线程。

更准确的说法是：

```text
每个 worker 通常有一个主事件循环线程；
但 worker 内部可能还会有线程池、后台线程，或者第三方库自己创建的线程。
```

例如 FastAPI 中如果写同步接口：

```python
@app.get("/sync")
def sync_api():
    return {"ok": True}
```

这类普通 `def` 接口通常会被 Starlette/FastAPI 放到线程池里执行，避免阻塞主事件循环。

再比如某些数据库驱动、日志库、监控库、AI SDK，也可能内部使用线程。

所以准确总结是：

```text
每个 Uvicorn worker 通常是一个进程；
每个 worker 通常有一个主线程运行事件循环；
这个事件循环管理多个异步请求任务；
但 worker 进程里不一定只有一个线程。
```

## 什么情况会破坏异步优势

异步的前提是：等待点真的会让出事件循环。

适合 `await` 的通常是 IO 型操作：

```text
await 数据库查询
await Redis 访问
await HTTP 请求
await LLM 调用
await 文件上传读取
await asyncio.sleep()
```

但如果在 `async def` 里写阻塞代码：

```python
time.sleep(10)
```

它会阻塞当前线程，也就是阻塞事件循环。

这 10 秒里，事件循环没法正常调度其他协程。

正确写法应该是：

```python
await asyncio.sleep(10)
```

如果是 CPU 密集计算，例如大规模图片处理、大量数学计算、复杂加密压缩等，也不应该长时间占用事件循环。通常需要放到线程池、进程池，或者交给后台任务系统处理。

## 一句话总结

```text
await 的意思不是自动并行，而是异步等待；
当前协程等待结果时会让出事件循环；
事件循环可以调度其他请求或任务；
结果回来后，再恢复当前协程继续往下执行。
```

对当前小红书流程来说：

```text
Step 1 和 Step 2 是顺序 await；
Step 2 依赖 Step 1 的 visual_by_id；
每个 Step 内部可以通过 CrewAI 的 async_execution=True 并发处理多张图片；
FastAPI/Uvicorn 则可以在请求等待 IO 时，用同一个事件循环线程调度其他请求。
```
