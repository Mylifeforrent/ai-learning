# FastAPI lifespan 中 yield 的底层原理

## 项目里的代码

项目入口中有这样一段代码：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化日志与配置，关闭时清理。"""
    settings = get_settings()
    from app.observability.logging import configure_logging

    configure_logging(settings.log_level, settings.log_dir)
    logger.info("application_started", env=settings.env, port=settings.port)
    yield
    logger.info("application_shutdown")
```

这里的 `yield` 不是为了返回多个值，而是为了把应用生命周期函数切成两段：

```text
yield 前面：应用启动时执行
yield 位置：应用运行中，FastAPI/Uvicorn 开始接收请求
yield 后面：应用关闭时执行
```

## 第一层：yield 让函数变成 async generator

普通的 `async def` 通常是协程函数：

```python
async def foo():
    return 1
```

但如果 `async def` 里面出现了 `yield`：

```python
async def foo():
    yield 1
```

它就不再是普通 coroutine，而是异步生成器 async generator。

异步生成器的特点是：执行到 `yield` 时会暂停，后面还可以从暂停的位置继续执行。

可以粗略理解为：

```text
调用 lifespan(app)
  -> 得到一个 async generator 对象
  -> 第一次推进它时，执行 yield 前面的代码
  -> 执行到 yield，暂停
  -> 后续再次推进时，从 yield 后面继续执行
```

## 第二层：asynccontextmanager 把它变成异步上下文管理器

`@asynccontextmanager` 来自 Python 标准库：

```python
from contextlib import asynccontextmanager
```

它的作用是把一个“只 yield 一次”的 async generator 包装成异步上下文管理器。

也就是可以参与这种结构：

```python
async with lifespan(app):
    ...
```

它底层大致等价于一个拥有 `__aenter__` 和 `__aexit__` 的对象：

```python
class LifespanContextManager:
    async def __aenter__(self):
        # 执行 yield 前面的代码
        # 在 yield 处暂停
        return yielded_value

    async def __aexit__(self, exc_type, exc, tb):
        # 从 yield 后面继续执行
        # 执行关闭、清理逻辑
```

所以：

```text
进入 async with
  -> 执行 yield 前面的启动逻辑

到达 yield
  -> lifespan 暂停
  -> 控制权交给 async with 内部代码

退出 async with
  -> 从 yield 后面继续执行
  -> 执行关闭逻辑
```

## 第三层：FastAPI/Starlette 调用 lifespan

在项目中，FastAPI 应用是这样创建的：

```python
app = FastAPI(
    title="Enterprise AI App",
    lifespan=lifespan,
)
```

这表示把 `lifespan` 函数交给 FastAPI/Starlette 作为应用生命周期管理器。

Uvicorn 启动应用时，会通过 ASGI lifespan 协议通知应用启动；FastAPI/Starlette 收到启动事件后，会进入这个 lifespan 上下文。

可以粗略理解成底层类似：

```python
async with lifespan(app):
    await server.serve_requests()
```

真实实现更复杂一些，要处理 ASGI 协议消息、异常、关闭信号等，但核心流程就是这个。

## 完整执行顺序

项目代码的执行顺序可以理解为：

```text
1. Uvicorn 启动 FastAPI 应用
   |
2. FastAPI/Starlette 进入 lifespan
   |
3. 执行 yield 前面的代码
   |
4. get_settings()
   |
5. configure_logging(settings.log_level, settings.log_dir)
   |
6. logger.info("application_started", ...)
   |
7. 执行到 yield，lifespan 暂停
   |
8. FastAPI 应用正式运行，开始处理请求
   |
9. 收到关闭信号，例如 Ctrl+C、进程退出、容器停止
   |
10. FastAPI/Starlette 退出 lifespan
    |
11. 从 yield 后面继续执行
    |
12. logger.info("application_shutdown")
```

## 和普通 try/finally 的类比

可以把它类比成：

```python
try:
    configure_logging(...)
    logger.info("application_started")

    await server.serve_requests()
finally:
    logger.info("application_shutdown")
```

`yield` 前面的代码类似 `try` 里正式运行前的初始化逻辑。

`yield` 后面的代码类似 `finally` 里的清理逻辑。

区别是 FastAPI 通过 `@asynccontextmanager` 和 ASGI lifespan 协议，把这套流程封装成了应用生命周期。

## 为什么这里适合用 yield

应用生命周期天然就是“两段式”的：

```text
启动阶段：初始化资源
运行阶段：处理请求
关闭阶段：释放资源
```

例如更复杂的项目里，可能会这样写：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await create_db_pool()
    app.state.db = db
    logger.info("application_started")

    yield

    await db.close()
    logger.info("application_shutdown")
```

这样数据库连接池在启动时创建，应用运行期间可用，应用关闭时释放。

## 最后总结

这里的 `yield` 可以理解成 FastAPI 应用生命周期的分界线：

```text
yield 前：startup
yield 中：application running
yield 后：shutdown
```

底层机制是：

```text
async def + yield
  -> 形成 async generator
  -> @asynccontextmanager 包装成异步上下文管理器
  -> FastAPI/Starlette 在 ASGI lifespan 阶段进入和退出这个上下文
```

所以这段代码的实际语义是：

> 启动时配置日志并打印 application_started；应用运行期间停在 yield；关闭时从 yield 后继续执行并打印 application_shutdown。
