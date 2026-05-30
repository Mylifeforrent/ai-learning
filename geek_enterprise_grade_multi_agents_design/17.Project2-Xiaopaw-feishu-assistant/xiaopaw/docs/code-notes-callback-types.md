# 回调类型别名说明

本文说明 `xiaopaw/feishu/listener.py` 中两个回调类型别名的含义：

```python
OnMessageFn = Callable[[InboundMessage], Awaitable[None]]
OnBotAddedFn = Callable[[str, str], Awaitable[None]]
```

## 基础语法

这两行是在定义类型别名，用来描述“回调函数应该长什么样”。

`Callable[[参数类型...], 返回值类型]` 表示一个可调用对象，通常就是函数。

`Awaitable[None]` 表示这个函数调用后返回的是一个可 `await` 的对象，通常是 `async def` 定义的协程，最终结果是 `None`。

## OnMessageFn

```python
OnMessageFn = Callable[[InboundMessage], Awaitable[None]]
```

`OnMessageFn` 表示一种异步函数类型：它接收一个 `InboundMessage` 参数，不返回业务结果。

等价于要求函数长这样：

```python
async def handle_message(message: InboundMessage) -> None:
    ...
```

在项目中，它用于飞书收到消息后，把解析好的 `InboundMessage` 交给上层处理。典型场景是把它连接到 `Runner.dispatch`。

## OnBotAddedFn

```python
OnBotAddedFn = Callable[[str, str], Awaitable[None]]
```

`OnBotAddedFn` 表示一种异步函数类型：它接收两个字符串参数，不返回业务结果。

等价于要求函数长这样：

```python
async def handle_bot_added(chat_id: str, group_name: str) -> None:
    ...
```

在项目中，它用于 Bot 被拉进群时的回调。第一个 `str` 是 `chat_id`，第二个 `str` 是群名 `group_name`。

## 作用

这两个类型别名主要有三个作用：

1. 提升可读性。

   比起在构造函数里直接写：

   ```python
   on_message: Callable[[InboundMessage], Awaitable[None]]
   ```

   写成：

   ```python
   on_message: OnMessageFn
   ```

   更容易看出这是“收到消息后的处理函数”。

2. 帮助类型检查和 IDE 提示。

   如果传入的函数参数不对，或者不是异步函数，`mypy`、Pyright、IDE 等工具可以更早提示问题。

3. 解耦 `FeishuListener` 和具体业务处理。

   `FeishuListener` 只负责监听飞书事件、解析消息。它不关心消息后面怎么处理，只调用传进来的 `on_message` 或 `on_bot_added`。

   因此生产环境可以接入真实的业务处理逻辑，测试环境也可以替换成假的异步函数。

一句话总结：这两行不是创建函数，而是在给“异步回调函数的形状”起名字，让 `FeishuListener` 可以用类型清晰的方式接收外部注入的处理逻辑。
