# asyncio 事件循环与 run_in_executor 说明

本文说明 `xiaopaw/feishu/listener.py` 中这段代码的含义：

```python
loop = asyncio.get_running_loop()
# lark-oapi ws.Client.start() 为阻塞同步方法，内部自管事件循环，
# 这里通过线程池隔离，避免嵌套事件循环错误。
await loop.run_in_executor(None, self._ws_client.start)
```

## loop 不是无限循环

这里的 `loop` 不是 `while True` 那种无限循环，也不是一个线程。

`asyncio.get_running_loop()` 返回的是当前正在运行的 **asyncio 事件循环对象**。可以把事件循环理解为异步程序里的调度器：它负责安排 coroutine、定时器、IO 回调等什么时候运行。

几个概念要分开看：

```text
线程 Thread
  是操作系统用来执行代码的“工人”。

事件循环 Event Loop
  是 asyncio 里的“调度器”，负责安排 async 任务什么时候继续执行。

协程 Coroutine
  是 async def 创建出来的异步任务代码。
```

所以：

```python
loop = asyncio.get_running_loop()
```

意思是：

```text
获取当前这个线程里正在运行的 asyncio 调度器。
```

它不是新建线程，也不是返回线程。

## 事件循环是否会一直运行

事件循环通常由外层代码启动，例如：

```python
asyncio.run(main())
```

背后大致可以理解为：

```text
1. 创建一个事件循环 loop
2. 在这个 loop 里运行 main()
3. main() 没结束，loop 就持续调度任务
4. main() 结束，loop 关闭
```

因此，事件循环本身不是线程，但它会运行在某个线程里。最常见的是主线程。

只要主异步任务没有结束，事件循环就会继续调度任务。

## self 的含义

`self.xxx` 表示当前实例上的属性或方法。

例如类初始化时创建了：

```python
self._ws_client = WSClient(...)
```

那么：

```python
self._ws_client
```

表示当前 `FeishuListener` 实例持有的飞书 WebSocket 客户端。

而：

```python
self._ws_client.start
```

表示这个客户端对象的 `start` 方法。

注意这里没有写括号：

```python
self._ws_client.start
```

不是：

```python
self._ws_client.start()
```

因为这里不是立刻调用它，而是把这个函数对象交给线程池去调用。

## 为什么使用 run_in_executor

`lark-oapi` 的 `ws.Client.start()` 是一个同步阻塞方法。它很可能会持续运行，用来维护 WebSocket 长连接并监听飞书消息。

如果直接写：

```python
self._ws_client.start()
```

它会阻塞当前 asyncio 事件循环，导致其他异步任务无法继续运行。

因此项目使用：

```python
await loop.run_in_executor(None, self._ws_client.start)
```

意思是：

```text
把 self._ws_client.start 这个同步阻塞函数放到另一个线程里运行，
当前 async 函数等待它执行。
```

这样主 asyncio 事件循环仍然可以继续调度其他异步任务。

## None 参数表示什么

`run_in_executor` 的形式大致是：

```python
loop.run_in_executor(executor, func, *args)
```

第一个参数：

```python
None
```

表示使用 asyncio 默认的线程池执行器。

如果需要自定义线程池，也可以传入一个 `ThreadPoolExecutor`：

```python
executor = ThreadPoolExecutor(max_workers=1)
await loop.run_in_executor(executor, self._ws_client.start)
```

但这里传 `None` 表示“用默认线程池”，对当前场景已经足够。

第二个参数：

```python
self._ws_client.start
```

表示要在线程池里执行的函数。

如果这个函数需要参数，可以继续往后传：

```python
await loop.run_in_executor(None, some_func, arg1, arg2)
```

等价于在线程池中执行：

```python
some_func(arg1, arg2)
```

当前代码里的 `start` 不需要额外参数，所以只传函数本身。

## 整体理解

这段代码可以口语化理解为：

```text
当前程序是 asyncio 异步程序，但飞书 SDK 的 WebSocket start() 是同步阻塞的。
为了不堵住主事件循环，把它放到默认线程池里运行，并在这里等待它。
```

调用关系大致是：

```text
当前线程里有一个 asyncio 事件循环 loop
        |
        | 调用 run_in_executor
        v
默认线程池里开/复用一个工作线程
        |
        v
执行 self._ws_client.start()
```

真正持续监听飞书消息的，是线程池里的工作线程在执行 `self._ws_client.start()`。

`loop = asyncio.get_running_loop()` 这一句只是拿到当前 asyncio 调度器，方便后面调用 `run_in_executor` 把阻塞函数安排到线程池里执行。
