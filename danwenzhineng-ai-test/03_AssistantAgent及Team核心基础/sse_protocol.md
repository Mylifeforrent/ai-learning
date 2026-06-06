是的，**`\n\n`（双换行）是 SSE (Server-Sent Events) 协议的标准强制要求**，不是可选的格式偏好。

### 1. 为什么必须是 `\n\n`？

根据 [W3C SSE 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation)，SSE 的数据流是由一个个**事件（Event）** 组成的，而每个事件的结束标志就是：

> **一个空行（即连续两个换行符 `\n\n`）**

解析规则如下：

```
data: {"type":"chunk","content":"Hello"}\n    ← 字段行，以 \n 结尾
\n                                            ← 空行，表示这个事件到此结束
                                              ↑ 这两个 \n 合起来就是 \n\n
data: {"type":"chunk","content":" World"}\n   ← 下一个事件开始
\n                                            ← 下一个事件结束
```

-   **第一个 `\n`**：是当前 `data:` 这一行的行尾换行符。
-   **第二个 `\n`**：是一个**空行**，作为事件之间的分隔符/终止符。

### 2. 如果少写一个 `\n` 会怎样？

| 写法 | 结果 |
| :--- | :--- |
| `yield f"data: {json}\n\n"` ✅ | 浏览器/客户端正确识别为一个完整事件，立即触发 `onmessage` |
| `yield f"data: {json}\n"` ❌ | 客户端认为事件还没结束，继续等待下一行数据，直到收到 `\n` 或连接关闭才触发。**表现为消息延迟、粘连、丢失** |
| `yield f"data: {json}"` ❌❌ | 完全没有行终止符，多个事件会被拼接成一行，客户端无法解析，全部丢弃或报错 |

### 3. 多行数据的特殊情况

如果你的 `data` 内容本身包含换行符，SSE 规范要求**每一行都必须以 `data:` 开头**，最后仍然以 `\n\n` 结束：

```python
# ✅ 正确的多行 SSE 数据
yield "data: line1\n"
yield "data: line2\n"
yield "\n"  # 空行，结束事件

# ❌ 错误写法：data 值中直接嵌入换行
yield f"data: line1\nline2\n\n"  # "line2" 会被当作未知字段名，被忽略
```

不过在你的场景中，`json.dumps()` 默认输出单行 JSON，所以 `f"data: {json.dumps(...)}\n\n"` 是完全正确的标准写法。

### 4. 补充：其他合法的事件字段

除了 `data:`，SSE 还支持以下字段，它们同样遵循 `\n\n` 结束规则：

```
event: custom_event\n       ← 自定义事件类型（前端用 addEventListener('custom_event', ...) 监听）
id: 42\n                    ← 事件ID（用于断线重连时的 Last-Event-ID）
retry: 3000\n               ← 重连间隔（毫秒）
data: {"msg":"hello"}\n     ← 数据
\n                          ← 事件结束
```

> **总结**：`\n\n` 之于 SSE，就像 `{}` 之于 JSON、`</tag>` 之于 HTML——它是协议的语法组成部分，不是排版习惯。你的代码写法完全符合标准。