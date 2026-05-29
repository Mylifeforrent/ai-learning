# structlog processors 原理说明

## 这段代码在做什么

项目中的日志格式化代码如下：

```python
formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.KeyValueRenderer(
        key_order=["timestamp", "level", "event", "request_id", "trace_id", "span_id"]
    ),
    foreign_pre_chain=_shared_processors(),
)
```

它的作用是：把 structlog 产生的结构化日志事件，最终渲染成一行人类可读的 `key=value` 文本。

例如业务代码写：

```python
logger.info("http_request_start", method="POST", path="/api/demo")
```

经过 processor 链处理后，最终日志可能变成：

```text
timestamp='2026-05-27T10:00:00.000000Z' level='info' event='http_request_start' request_id='...' trace_id='...' span_id='...' method='POST' path='/api/demo'
```

## structlog 的 event_dict 是什么

structlog 的核心思想是：日志不是一开始就拼成字符串，而是先表示成一个字典。

这个字典通常叫 `event_dict`。

例如：

```python
logger.info("user_login", user_id=123)
```

可以粗略理解成：

```python
{
    "event": "user_login",
    "user_id": 123,
}
```

processor 就是一组函数，依次接收并修改这个 `event_dict`：

```text
event_dict
  -> processor 1 增加 request_id
  -> processor 2 增加 trace_id/span_id
  -> processor 3 增加 level
  -> processor 4 增加 timestamp
  -> renderer 渲染成最终文本
```

## _shared_processors() 有什么用

项目里定义了：

```python
def _shared_processors() -> list:
    return [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        add_trace_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
```

`_shared_processors()` 的作用是复用一组公共日志处理步骤，保证不同来源的日志都尽量拥有一致的字段。

这里它被用了两次：

```python
foreign_pre_chain=_shared_processors()
```

以及：

```python
structlog.configure(
    processors=[
        *_shared_processors(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
)
```

第一处用于处理普通 `logging` 体系来的日志，第二处用于处理 structlog 自己产生的日志。

这样做的目的就是：无论日志是通过 `structlog.get_logger()` 打出来的，还是某些第三方库通过标准库 `logging` 打出来的，都尽量经过同一批公共 processor，补齐时间、级别、request_id、trace_id 等字段。

## ProcessorFormatter 是什么

`structlog.stdlib.ProcessorFormatter` 是 structlog 提供的一个桥接器，用来把 structlog 和 Python 标准库 `logging` 接起来。

Python 标准库 `logging` 的 Handler 需要一个 Formatter：

```text
Logger -> Handler -> Formatter -> 输出到文件/控制台
```

而 structlog 的日志通常要经过 processor 链处理。

`ProcessorFormatter` 的作用就是：在标准库 Formatter 这个位置，继续执行 structlog processor，并把最终事件渲染成字符串。

在本项目里：

```python
all_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)
```

表示 `app.log` 和 `error.log` 两个文件 handler 都使用同一个 structlog formatter。

## processor=KeyValueRenderer(...) 的作用

这里的 `processor` 是最终渲染器：

```python
processor=structlog.processors.KeyValueRenderer(
    key_order=["timestamp", "level", "event", "request_id", "trace_id", "span_id"]
)
```

`KeyValueRenderer` 会把 `event_dict` 转成单行 `key=value` 字符串。

`key_order` 用来指定关键字段的输出顺序。比如希望时间、日志级别、事件名、请求 ID、Trace 信息优先出现在日志前面：

```text
timestamp=... level=... event=... request_id=... trace_id=... span_id=...
```

这样日志在终端或文件里更容易扫读，也方便 `grep`。

## foreign_pre_chain 的作用

`foreign_pre_chain` 用于处理“非 structlog 原生”的日志事件。

这里的 foreign 可以理解成：不是通过 structlog 的 BoundLogger 打出来的日志，而是来自 Python 标准库 `logging` 或第三方库。

例如第三方库里可能写的是：

```python
logging.getLogger("some_lib").info("something happened")
```

这类日志没有经过 structlog.configure 里的 processor 链。`foreign_pre_chain=_shared_processors()` 就是在它们进入最终渲染前，先补跑一遍公共 processor，让它们也能带上 level、timestamp、request_id、trace_id 等字段。

## 每个 processor 的作用

### structlog.contextvars.merge_contextvars

作用：把绑定在 structlog contextvars 里的上下文字段合并到当前日志事件里。

如果某处代码使用过：

```python
structlog.contextvars.bind_contextvars(user_id="u1")
```

后续日志经过 `merge_contextvars` 时，`event_dict` 里就会自动带上：

```python
{"user_id": "u1"}
```

这个项目当前主要自己用 `ContextVar` 保存 `request_id`、`trace_id`，但保留 `merge_contextvars` 可以兼容后续使用 structlog 官方 contextvars 绑定上下文的写法。

### add_request_id

作用：把当前请求的 `request_id` 注入日志。

代码如下：

```python
def add_request_id(logger: logging.Logger, method_name: str, event_dict: dict) -> dict:
    rid = get_request_id()
    if rid:
        event_dict["request_id"] = rid
    return event_dict
```

`get_request_id()` 从 `request_id_ctx` 这个 `ContextVar` 中读取当前请求的 request id。

这样业务代码不需要每次手动传：

```python
logger.info("some_event", request_id=request_id)
```

只要请求入口设置过 request id，后面的日志都会自动带上。

### add_trace_context

作用：把当前请求的 `trace_id` 和 `span_id` 注入日志。

代码会从 `app.observability.trace` 里读取：

```python
tid = get_trace_id()
sid = get_span_id()
```

然后写入：

```python
event_dict["trace_id"] = tid
event_dict["span_id"] = sid
```

这样同一个请求链路里的日志可以通过 `trace_id` 串起来，也可以通过 `span_id` 定位当前服务节点。

### structlog.processors.add_log_level

作用：把日志级别加入 `event_dict`。

例如：

```python
logger.info("hello")
```

经过这个 processor 后，事件中会多出：

```python
{"level": "info"}
```

最终日志就可以输出：

```text
level='info'
```

### structlog.processors.TimeStamper(fmt="iso")

作用：给日志增加时间戳字段。

`fmt="iso"` 表示使用 ISO 格式时间，通常类似：

```text
2026-05-27T10:00:00.000000Z
```

经过这个 processor 后，事件中会多出：

```python
{"timestamp": "..."}
```

时间字段对排查线上问题很重要，尤其是结合 request id 和 trace id 看一段请求链路时。

### structlog.processors.StackInfoRenderer()

作用：当日志调用时带了 `stack_info=True`，把当前调用栈信息渲染进日志。

例如：

```python
logger.info("debug_stack", stack_info=True)
```

这个 processor 会把调用栈转换成文本，加入到 `event_dict` 中。

它不是每条日志都会输出栈，只有日志事件要求输出 stack info 时才会生效。

### structlog.processors.format_exc_info

作用：格式化异常信息。

当日志调用带有异常信息时，例如：

```python
logger.exception("unhandled_exception")
```

或者：

```python
logger.error("failed", exc_info=True)
```

`format_exc_info` 会把异常类型、异常消息、堆栈信息格式化成适合输出的文本字段。

这样最终日志里可以看到完整 traceback，而不是只看到一个异常对象。

## wrap_for_formatter 的作用

在 `structlog.configure()` 中，最后一个 processor 是：

```python
structlog.stdlib.ProcessorFormatter.wrap_for_formatter
```

它不是普通的字段补充 processor，而是 structlog 和 `ProcessorFormatter` 配合时需要的桥接步骤。

它会把已经处理过的 `event_dict` 包装成标准库 logging 能携带的形式，然后交给 handler 上配置的 `ProcessorFormatter` 做最终渲染。

可以理解成：

```text
structlog processor 链
  -> wrap_for_formatter
  -> logging Handler
  -> ProcessorFormatter
  -> KeyValueRenderer
  -> 最终日志文本
```

## 一条日志的完整处理路径

以项目自己的 structlog 日志为例：

```python
logger.info("http_request_start", method="POST", path="/api/demo")
```

大致处理路径是：

```text
1. 生成初始 event_dict：
   {"event": "http_request_start", "method": "POST", "path": "/api/demo"}

2. merge_contextvars 合并 structlog contextvars。

3. add_request_id 注入 request_id。

4. add_trace_context 注入 trace_id/span_id。

5. add_log_level 注入 level。

6. TimeStamper 注入 timestamp。

7. StackInfoRenderer 处理 stack_info。

8. format_exc_info 处理异常信息。

9. wrap_for_formatter 交给标准库 logging handler。

10. ProcessorFormatter 调用 KeyValueRenderer。

11. 输出 key=value 文本到 app.log 或 error.log。
```

## 最后总结

这段日志配置的核心目的不是简单“格式化字符串”，而是搭建一条结构化日志处理流水线：

```text
业务日志事件
  -> 补充上下文 request_id/trace_id/span_id
  -> 补充 level/timestamp/异常栈
  -> 渲染成 key=value 文本
  -> 写入日志文件
```

`_shared_processors()` 是这条流水线里可复用的公共处理步骤；`ProcessorFormatter` 是 structlog 和 Python 标准 logging handler 之间的桥；`KeyValueRenderer` 是最终把结构化字典变成可读文本的渲染器。
