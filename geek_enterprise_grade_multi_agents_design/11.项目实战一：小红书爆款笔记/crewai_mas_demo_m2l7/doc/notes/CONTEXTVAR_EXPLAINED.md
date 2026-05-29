# Python ContextVar 原理说明

## 这行代码在做什么

```python
span_id_ctx: ContextVar[str] = ContextVar("span_id", default="")
```

这行代码定义了一个名为 `span_id` 的上下文变量，用来保存“当前请求/当前异步任务”的 `span_id`。

它看起来像一个全局变量，但它不是普通全局变量。普通全局变量在整个进程里只有一份值，多个并发请求同时修改时容易互相覆盖；`ContextVar` 会根据当前执行上下文保存不同的值，所以每个请求可以拿到自己的 `span_id`。

## ContextVar 的核心原理

`ContextVar` 来自 Python 标准库 `contextvars`，用于管理上下文局部变量。

可以把它理解成：

> 同一个变量名，在不同执行上下文里有不同的值。

在 FastAPI、Starlette、asyncio 这类异步程序中，很多请求可能运行在同一个线程里。它们通过事件循环不断切换执行：

```text
请求 A 执行一会儿 -> await 等待 I/O
请求 B 开始执行 -> await 等待 I/O
请求 A 恢复执行
请求 C 开始执行
```

## 为什么不是一个请求对应一个线程

“一个请求对应一个线程”是传统同步 Web 服务里很常见的模型。比如一些基于阻塞 I/O 的服务会为每个请求分配一个线程，或者从线程池里拿一个线程来处理这个请求。请求处理过程中，如果代码在等数据库、HTTP 接口、文件读取等 I/O，这个线程也会跟着阻塞在那里。

FastAPI/Starlette 属于 ASGI 异步框架，常见运行方式是 Uvicorn + asyncio。它的核心模型不是“每个请求一个线程”，而是：

> 一个事件循环线程里运行很多协程任务，每个请求通常对应一个 asyncio Task。

当请求 A 执行到 `await`，比如等待数据库或外部 HTTP 接口时，请求 A 会主动把执行权交还给事件循环。事件循环发现请求 A 正在等 I/O，就可以先去执行请求 B、请求 C。等请求 A 等待的 I/O 完成后，事件循环再恢复请求 A。

所以，在异步模型里，一个线程中可能同时管理很多请求。它们不是同一时刻真的在 CPU 上并行执行，而是在遇到 `await` 时快速切换，看起来像很多请求同时推进。

可以粗略对比为：

```text
传统同步模型：
请求 A -> 线程 1 -> 阻塞等待 I/O
请求 B -> 线程 2 -> 阻塞等待 I/O
请求 C -> 线程 3 -> 阻塞等待 I/O

asyncio 异步模型：
请求 A -> Task A \
请求 B -> Task B  -> 同一个事件循环线程调度
请求 C -> Task C /
```

这也是为什么 `ThreadLocal` 在异步服务里不够精确：如果多个请求都在同一个线程里切换执行，那么按线程保存变量，可能会把多个请求的值放到同一个线程槽位里。`ContextVar` 则是按执行上下文保存值，更适合这种 “一个线程 + 多个 Task” 的模型。

补充一点：FastAPI 也可能使用多个进程、多个 worker，或者在执行普通同步函数时使用线程池。但在一个典型的 async 请求处理链路里，隔离请求上下文时仍然应该优先使用 `ContextVar`，而不是依赖“一个请求一个线程”的假设。

## 从请求接收到 asyncio Task 的处理过程

可以先纠正一个容易混淆的理解：

> ASGI/asyncio 的典型模型，不是“一个专门线程接收请求，再交给很多线程处理请求”。

这种“接收线程 + 工作线程池”的理解更接近传统同步服务器。ASGI 服务器，比如 Uvicorn，通常是：

```text
一个 worker 进程
  -> 一个事件循环 event loop
    -> 监听 socket
    -> 接收连接
    -> 解析 HTTP 请求
    -> 为请求创建/调度 asyncio Task
    -> 在同一个事件循环中推进多个请求 Task
```

如果配置了多个 worker，那么是多个进程各自拥有自己的事件循环：

```text
worker 进程 1 -> event loop 1 -> 管理一批请求 Task
worker 进程 2 -> event loop 2 -> 管理一批请求 Task
worker 进程 3 -> event loop 3 -> 管理一批请求 Task
```

每个 worker 内部仍然主要是事件循环调度协程，而不是给每个请求分配一个独立线程。

一个典型 async 请求的处理流程可以理解为：

```text
1. 客户端发起 HTTP 请求
   |
2. Uvicorn worker 的 socket 收到连接和数据
   |
3. 事件循环发现 socket 可读，读取请求数据
   |
4. HTTP 协议层解析请求，构造 ASGI scope
   |
5. ASGI 服务器调用 FastAPI/Starlette 应用
   |
6. 当前请求进入中间件链，例如 http_trace_middleware
   |
7. 中间件调用 set_trace_context()，把 trace_id/span_id 写入 ContextVar
   |
8. FastAPI 执行路由函数，当前请求作为一个 asyncio Task 被事件循环调度
   |
9. 如果路由里 await 数据库、HTTP 接口、Redis 等 I/O，请求 Task 暂停，让出事件循环
   |
10. 事件循环继续推进其他已经就绪的请求 Task
   |
11. 等 I/O 完成后，事件循环恢复原来的请求 Task
   |
12. 返回响应，响应头里写入 traceparent
```

这里的高性能来自两个点：

- 等 I/O 时不占着线程空转。请求 A 在等数据库时，事件循环可以去处理请求 B、请求 C。
- 大量连接和请求可以由少量事件循环线程管理，不需要为每个请求都创建一个操作系统线程。

但这并不表示 CPU 计算也会自动并行。asyncio 适合 I/O 密集型场景，比如网络请求、数据库查询、消息队列等。如果某个请求里有很重的 CPU 计算，而且没有 `await`，它会长时间占用事件循环，导致其他请求也被卡住。这类任务通常要放到进程池、任务队列，或者专门的后台计算服务中处理。

也有一个例外需要注意：FastAPI 支持普通同步路由函数，比如：

```python
def sync_route():
    ...
```

这类同步函数可能会被 Starlette 放到线程池里执行，避免阻塞事件循环。但如果路由是：

```python
async def async_route():
    ...
```

那它通常就是作为事件循环里的协程 Task 被调度。

所以，更准确的理解是：

```text
不是：一个接收线程 + 很多请求处理线程 + 每个请求一个线程

而是：每个 worker 有自己的事件循环，事件循环把很多请求作为 asyncio Task 来调度；
     只有同步阻塞代码、线程池配置或特殊场景，才会额外使用线程。
```

这也解释了为什么 `ContextVar` 很重要：多个请求 Task 可能在同一个线程和同一个事件循环里交替执行，所以不能只依赖线程级别的变量隔离。

如果用普通全局变量保存 `span_id`，请求 A 设置的值可能被请求 B 覆盖。等请求 A 恢复执行时，读到的就可能是请求 B 的 `span_id`。

`ContextVar` 解决的就是这个问题：它把变量值绑定到当前的 `Context`，而不是绑定到整个进程的全局状态。

## 它像 Java 的 ThreadLocal 吗

概念上很像，但隔离粒度不同。

Java `ThreadLocal` 的典型含义是：

> 同一个变量名，在不同线程里有不同的值。

Python `ContextVar` 的典型含义是：

> 同一个变量名，在不同执行上下文里有不同的值。

在同步多线程程序里，可以粗略地把 `ContextVar` 类比成 `ThreadLocal`。但在异步程序里，`ContextVar` 比 `ThreadLocal` 更适合。

原因是：异步框架里的多个请求可能在同一个线程中交替执行。如果只按线程隔离，那么同一个线程上的多个请求仍然可能共享到同一份值；而 `ContextVar` 可以按 asyncio Task/上下文隔离，避免请求之间串值。

## 为什么 FastAPI Trace 适合用 ContextVar

这个项目里，`trace.py` 保存了三个上下文变量：

```python
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
span_id_ctx: ContextVar[str] = ContextVar("span_id", default="")
parent_span_id_ctx: ContextVar[str] = ContextVar("parent_span_id", default="")
```

请求进入 `http_trace_middleware` 后，会调用：

```python
trace_id, span_id = set_trace_context(trace_id=tid, parent_span_id=parent_sid or None)
```

`set_trace_context()` 内部会执行：

```python
trace_id_ctx.set(tid)
span_id_ctx.set(sid)
parent_span_id_ctx.set(parent_span_id)
```

这样，在同一个请求链路后续的函数里，就不需要层层传递 `trace_id` 和 `span_id` 参数，可以直接调用：

```python
get_trace_id()
get_span_id()
get_parent_span_id()
```

日志模块、异常处理、业务函数都能拿到当前请求自己的 trace 信息。

## 一个简单对比

普通全局变量的问题：

```python
current_span_id = ""

async def handle_request_a():
    global current_span_id
    current_span_id = "span-a"
    await some_io()
    print(current_span_id)  # 这里可能已经被请求 B 改成 span-b

async def handle_request_b():
    global current_span_id
    current_span_id = "span-b"
```

`ContextVar` 的效果：

```python
span_id_ctx = ContextVar("span_id", default="")

async def handle_request_a():
    span_id_ctx.set("span-a")
    await some_io()
    print(span_id_ctx.get())  # 仍然是 span-a

async def handle_request_b():
    span_id_ctx.set("span-b")
    print(span_id_ctx.get())  # 是 span-b
```

两个请求即使在同一个线程里交替执行，也会读取各自上下文里的值。

## set/get/reset 的工作方式

`ContextVar` 常用方法有三个：

```python
token = span_id_ctx.set("abc123")
value = span_id_ctx.get()
span_id_ctx.reset(token)
```

- `set(value)`：在当前上下文中设置值，并返回一个 `token`。
- `get()`：读取当前上下文中的值；如果没有设置过，就返回 `default`。
- `reset(token)`：恢复到 `set()` 之前的状态。

当前项目没有显式调用 `reset()`，因为每个请求进入中间件时都会重新设置 trace 上下文，请求处理过程也比较短。更复杂的场景中，比如临时覆盖上下文值，使用 `token/reset` 会更严谨。

## 和这个项目的关系

在本项目里，`ContextVar` 的价值是让 Trace 信息成为“当前请求的隐式上下文”：

- 请求入口负责解析或生成 `trace_id/span_id`。
- 中间件把它们写入 `ContextVar`。
- 日志或下游函数通过 `get_trace_id()`、`get_span_id()` 读取。
- 并发请求之间不会互相污染。

所以，`span_id_ctx: ContextVar[str] = ContextVar("span_id", default="")` 可以理解为：

> 定义一个可在当前异步请求上下文中读取和写入的 `span_id` 容器，作用类似 Java `ThreadLocal`，但更适合 Python asyncio/FastAPI 的并发模型。
