# FastAPI asynccontextmanager 与类型注解说明

## 项目里的代码

在 FastAPI 应用启动逻辑里，常见到这样的写法：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    ...
```

这里其实有两个概念：

```text
@asynccontextmanager 是装饰器
app: FastAPI 里的 : FastAPI 是类型注解
```

它们不是同一个东西。

## @asynccontextmanager 是什么

```python
@asynccontextmanager
```

这是一个装饰器，不是类型注解。

它来自 Python 标准库：

```python
from contextlib import asynccontextmanager
```

它的作用是：

```text
把一个带 yield 的异步函数，包装成一个异步上下文管理器。
```

也就是说，原本普通的异步函数：

```python
async def lifespan(app: FastAPI):
    # 启动时执行
    yield
    # 关闭时执行
```

加上 `@asynccontextmanager` 之后，FastAPI 就可以把它当成生命周期管理器使用。

## yield 前后分别什么时候执行

在 FastAPI 的 lifespan 函数中：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # yield 之前
    yield
    # yield 之后
```

执行时机可以理解为：

```text
yield 之前：应用启动时执行
yield 位置：应用运行期间停在这里
yield 之后：应用关闭时执行
```

例如：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("应用启动")
    yield
    print("应用关闭")
```

大致效果是：

```text
服务启动时打印：应用启动
服务运行期间停在 yield
服务关闭时打印：应用关闭
```

## FastAPI 为什么需要它

FastAPI 支持通过 `lifespan` 参数注册应用生命周期逻辑：

```python
app = FastAPI(lifespan=lifespan)
```

这表示：

```text
应用启动时，执行 lifespan 中 yield 之前的初始化逻辑；
应用运行时，保持在 yield；
应用关闭时，执行 yield 之后的清理逻辑。
```

常见用途包括：

```text
启动时初始化数据库连接
启动时加载模型或配置
启动时注册监控组件
关闭时释放连接池
关闭时清理后台任务
```

所以 `@asynccontextmanager` 的重点不是“标注类型”，而是把这个函数变成 FastAPI 能识别的生命周期上下文。

## app: FastAPI 是什么

```python
async def lifespan(app: FastAPI):
```

这里的：

```python
app: FastAPI
```

才是类型注解。

它表示：

```text
app 这个参数预期是 FastAPI 类型。
```

类型注解主要给这些工具和场景使用：

```text
编辑器代码提示
静态类型检查
代码可读性
团队协作时理解参数含义
```

例如编辑器看到 `app: FastAPI` 后，就更容易提示：

```python
app.include_router(...)
app.add_middleware(...)
app.state
```

## 类型注解会强制检查类型吗

通常不会。

Python 的类型注解默认不会在运行时强制校验类型。

也就是说：

```python
async def lifespan(app: FastAPI):
    ...
```

这行并不等于：

```text
运行时必须检查 app 一定是 FastAPI，否则立刻报错。
```

它更像是给人和工具看的说明：

```text
这个参数应该传 FastAPI 应用对象。
```

真正是否传入正确对象，通常由调用方和框架逻辑保证。

## 一个简单类比

这行代码：

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```

可以拆开理解：

```text
@asynccontextmanager
把函数改造成“异步上下文管理器”

async def lifespan(...)
定义一个异步函数

app: FastAPI
说明 app 参数预期是 FastAPI 应用对象
```

所以它整体表达的是：

```text
定义一个 FastAPI 应用生命周期函数，
这个函数可以在应用启动和关闭时分别执行不同逻辑。
```

## 小结

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
```

可以总结为：

```text
@asynccontextmanager：装饰器，把带 yield 的异步函数变成异步上下文管理器。
async def：定义异步函数。
app: FastAPI：类型注解，说明 app 参数是 FastAPI 应用对象。
yield 之前：应用启动时执行。
yield 之后：应用关闭时执行。
```

其中：

```text
@asynccontextmanager 影响函数运行方式。
app: FastAPI 主要影响代码提示、静态检查和可读性。
```
