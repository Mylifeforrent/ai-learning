# m2l8 代码与当前笔记的对应学习指南

这份指南用来回答一个问题：**`m2l8` 代码到底在实践 `notes.md` 里的哪些工具设计思想？**

简短结论：`m2l8` 不是单纯演示“模型会调用文件工具”，而是在演示 Agent-Native Tool 的企业级关键点：**模型负责表达意图，工具负责执行动作，Hook 负责在工具执行前接管安全、上下文和路径治理。**

---

## 1. 代码目录和学习目标

当前示例主要包含三个部分：

| 文件 | 作用 | 对应笔记主题 |
| --- | --- | --- |
| `m2l8/m2l8_context.py` | 定义请求级上下文变量，如 `user_id` | 身份不能通过 prompt 传递 |
| `m2l8/m2l8_tools_call.py` | 定义 Agent、Task、Crew 和 `@before_tool_call` Hook | 工具调用拦截、路径重写、多租户隔离 |
| `m2l8/workspace/1234567890/CRONTAB.md` | Agent 通过文件工具写入的结果 | 工具让 AI 应用真正完成任务 |

学习时不要只看 Agent 配置，更要重点看 Hook，因为 Hook 是这节课从“能调用工具”走向“安全调用工具”的关键。

---

## 2. 从 Function Calling/ReAct 到 m2l8

`notes.md` 里讲到：

```text
Function Calling 解决的是：怎么把一次工具调用写对。
ReAct 解决的是：什么时候调用哪个工具，以及调用完之后下一步怎么办。
```

`m2l8` 示例中，Agent 面对用户的自然语言请求，会决定是否调用：

- `FileWriterTool`
- `FileReadTool`

这一步可以理解为 Function Calling 或 ReAct 中的 `Action`：模型把“帮我创建/查询/修改定时任务”转换成文件读写工具调用。

但是仅靠模型生成工具参数是不够的。比如模型可能传入：

```text
CRONTAB.md
../../etc/passwd
/tmp/other_user_file.md
```

这些路径对普通文件 API 来说都是字符串，但对企业系统来说代表完全不同的安全风险。于是 `m2l8` 在工具真正执行前加入了 Hook：

```text
Agent 决定调用工具
        |
        v
@before_tool_call 拦截
        |
        v
检查 user_id、重写路径、阻断非法路径
        |
        v
FileWriterTool / FileReadTool 执行
```

这就是 Agent-Native Tool 和传统 API 的区别：**工具调用不是裸奔执行，中间要有工程治理层。**

---

## 3. 阅读顺序

### 第一步：先读 `m2l8_context.py`

重点看：

```python
user_id = ContextVar[Optional[str]]("user_id", default=None)
request_id = ContextVar[Optional[str]]("request_id", default=None)
task_id = ContextVar[Optional[str]]("task_id", default=None)
```

它对应 `notes.md` 的这一点：

> 权限必须通过系统安全链路传递，不能通过 prompt 传递。

也就是说，`user_id` 不应该由模型生成，不应该作为工具参数暴露给模型，而应该由后端系统在请求进入时写入上下文。

在真实 Web 服务中，这个值通常来自：

- JWT token
- Session
- API Gateway
- 后端认证中间件
- 企业身份系统

课堂示例里用固定值模拟：

```python
user_id.set("1234567890")
```

这不是生产写法，只是为了让你看到多租户隔离的效果。

### 第二步：再读 `file_path_hook`

`m2l8/m2l8_tools_call.py` 中最重要的是：

```python
@before_tool_call
def file_path_hook(context: Any):
```

它做了四件事：

| 步骤 | 代码行为 | 学习重点 |
| --- | --- | --- |
| 识别工具 | 只处理文件读写工具 | Hook 不一定拦截所有工具 |
| 读取身份 | 从 `ContextVar` 读取 `user_id` | 身份来自系统，不来自模型 |
| 重写路径 | 把模型给出的文件名放进用户工作空间 | 模型只表达意图，不掌控真实路径 |
| 安全校验 | 用 `Path.relative_to()` 防路径穿越 | 权限由工程层硬校验 |

这段代码体现了一个很重要的原则：

> Agent 可以决定“我要写 CRONTAB.md”，但不能决定“我写到系统哪个真实目录”。

真实目录应该由系统根据当前用户身份计算出来。

### 第三步：看 Agent 的工具配置

`crontab_manager_agent` 只暴露了两个工具：

```python
tools = [FileWriterTool(), FileReadTool()]
```

这和 `notes.md` 的“工具语义完整、不要做 God Tool”有关。

这个示例没有暴露一个超级工具：

```text
FileManager(action_type="read/write/delete/list/...")
```

而是把读和写分成明确工具。这样模型更容易选择，也更容易做安全拦截。

### 第四步：看三轮 `crew.kickoff`

最后三轮请求分别是：

```python
crew.kickoff(inputs={"user_input": "帮我创建一个周一到周五每天早上9点的任务..."})
crew.kickoff(inputs={"user_input": "查一下我现在的定时任务"})
crew.kickoff(inputs={"user_input": "帮我把查询阿里股价的任务改到9点半"})
```

这三轮对应：

| 用户意图 | Agent 可能动作 | Hook 作用 |
| --- | --- | --- |
| 创建定时任务 | 写 `CRONTAB.md` | 重定向到 `workspace/1234567890/CRONTAB.md` |
| 查询定时任务 | 读 `CRONTAB.md` | 只允许读取当前用户工作空间 |
| 修改定时任务 | 先读再写 | 每次工具调用都重新校验路径 |

最终落盘结果在：

```text
m2l8/workspace/1234567890/CRONTAB.md
```

这就是第一张图“工具让 AI 应用真正完成任务”的具体体现：模型不是只回答“我会帮你创建”，而是真的通过工具把任务记录写进了文件。

---

## 4. 路径安全为什么要这样写？

危险路径示例：

```text
../../etc/passwd
../other_user/CRONTAB.md
/tmp/sensitive.txt
```

如果直接把这些路径交给文件工具，就可能越权读写。`m2l8` 用两阶段处理：

### 阶段一：如果模型已经给了工作空间内的绝对路径，就放行

```python
original_file_path_abs = Path(original_file_path).resolve()
original_file_path_abs.relative_to(base_path_abs)
```

如果 `original_file_path_abs` 确实在当前用户工作空间里，`relative_to()` 会成功。

### 阶段二：如果模型只给了普通文件名，就拼到用户工作空间下

```python
new_file_path = base_path / original_file_path
new_file_path_abs = new_file_path.resolve()
new_file_path_abs.relative_to(base_path_abs)
```

例如模型传入：

```text
CRONTAB.md
```

会被重写为：

```text
m2l8/workspace/1234567890/CRONTAB.md
```

如果模型传入：

```text
../../etc/passwd
```

拼接和 `resolve()` 之后会逃出工作空间，`relative_to()` 会抛出 `ValueError`，Hook 返回 `False`，工具不会执行。

这比字符串判断更稳，因为下面这种路径用字符串前缀很容易判断错：

```text
/workspace/123
/workspace/123_evil
```

---

## 5. 当前我已顺手优化的地方

这次我对 `m2l8/m2l8_tools_call.py` 做了几个低风险改动，让它更适合学习：

| 改动 | 原因 |
| --- | --- |
| `WORKSPACE_BASE_PATH` 改为基于脚本目录 | 避免从不同 cwd 启动时写到不同 workspace |
| 增加 `FILE_TOOL_PATH_FIELDS` 映射 | 避免在 Hook 里散落多处 `if/elif` |
| 去掉未使用的 `ScrapeWebsiteTool`、`after_tool_call`、`task_id` 导入 | 降低阅读噪音 |
| 给 Hook 参数加了 `Any` 类型标注 | 让示例更接近可维护 Python 代码 |
| `mkdir(parents=True, exist_ok=True)` 直接调用 | 简化目录创建逻辑 |

这些改动不改变课程主线，只是让代码更清楚。

---

## 6. 代码仍然可以继续改进的地方

这个示例用于教学已经足够，但如果要走向生产，还可以继续补强。

### 6.1 增加审计日志

现在 Hook 用 `print()` 输出：

```python
print(f"工具调用：{context.tool_name}")
print(f"工具输入：{context.tool_input}")
```

生产系统应该记录结构化日志：

- `user_id`
- `request_id`
- `tool_name`
- 原始路径
- 重写后路径
- 是否阻断
- 阻断原因

这样才能审计“谁在什么时候尝试访问了什么”。

### 6.2 增加测试用例

建议至少测试这些路径：

| 输入路径 | 期望结果 |
| --- | --- |
| `CRONTAB.md` | 放行并重写到当前用户 workspace |
| `workspace/1234567890/CRONTAB.md` | 放行 |
| `../../etc/passwd` | 阻断 |
| `/tmp/x.md` | 阻断或按策略重定向 |
| 空字符串 | 阻断并返回建设性错误 |

### 6.3 区分“重定向”和“拒绝绝对路径”

当前代码允许两种输入：

- 已经在工作空间内的路径。
- 普通相对路径，自动拼接到工作空间。

如果生产安全策略更严格，可以直接拒绝所有绝对路径，只允许模型传文件名或相对路径。

### 6.4 把 Hook 逻辑封装成可复用模块

当前 Hook 直接写在演示脚本里，适合课堂讲解。生产中可以拆成：

```text
security/
  workspace_policy.py
  tool_hooks.py
  audit_logger.py
```

这样多个 Agent、多个工具都能复用同一套安全策略。

---

## 7. 推荐学习路线

按这个顺序学，会比较顺：

1. 先读 `notes.md` 的第 2 节，理解 Function Calling 和 ReAct 的工具调用差异。
2. 再读 `notes.md` 的第 3 节，理解 Agent Tool 为什么不能照搬传统 API 设计。
3. 读 `m2l8_context.py`，理解为什么 `user_id` 不能由模型传。
4. 读 `m2l8_tools_call.py` 的 `file_path_hook`，理解工具调用前如何做安全接管。
5. 看 `workspace/1234567890/CRONTAB.md`，确认 Agent 的工具调用产生了真实副作用。
6. 回到 `notes.md` 的第 6 节，用反模式检查当前代码还能怎么增强。

记住这句话就抓住了这节课的骨架：

> 模型负责“想做什么”，工具负责“真的去做”，Hook 负责“能不能这样做、应该在哪个安全边界内做”。

