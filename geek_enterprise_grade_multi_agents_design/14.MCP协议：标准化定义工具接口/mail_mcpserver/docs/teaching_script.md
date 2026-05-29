# 邮件 MCP 服务关键实现讲解 — 10 分钟逐字稿

> 时长：约 10 分钟 | 目标受众：有 Python 和 FastAPI 基础的开发者
> 教学目标：理解本项目如何将 MCP 协议与邮件收发业务结合，掌握核心设计决策

---

## 开场（1 分钟）

大家好，今天用 10 分钟时间，带大家快速过一遍这个邮件 MCP 服务的关键实现。

先说一下这个项目是做什么的。它是一个基于 FastAPI 的 MCP Server，MCP 就是 Model Context Protocol，是 AI Agent 调用外部工具的标准协议。我们这个服务通过 MCP 协议，给 AI Agent 提供了三个邮件操作能力：查看邮件列表、查看邮件详情、发送邮件。支持 QQ、新浪、163 邮箱。

整个项目的架构是四层结构：最上面是 FastAPI 接口层，负责中间件和路由；第二层是 MCP 协议层，处理 JSON-RPC 和鉴权；第三层是业务服务层，包括邮件工具和 IMAP/SMTP 服务；最底层是基础设施，配置、日志、安全这些。

接下来我按请求处理的顺序，从外到内讲解关键实现。

---

## 第一部分：双层鉴权与用户身份传递（2.5 分钟）

这个项目有一个核心设计问题：MCP 子应用是通过 Starlette 的 `app.mount()` 挂载的，这意味着 FastAPI 的依赖注入在 `/mcp/` 路径下是不可用的。所以鉴权必须在 ASGI 层面自己做。

打开 `app/mcp_server/transport.py`，看 `create_protected_mcp_app` 这个函数。它做了三件事：

第一，API Key 鉴权。从 ASGI 的 headers 字典里取出 `authorization` 或 `x-api-key`，调用 `verify_api_key_asgi` 做恒定时间比较。这是传输层的第一道门。

第二，提取用户身份。鉴权通过后，从 headers 里取 `x-user-id`，调用 `set_user_id()` 写入 Python 的 `contextvars`。这是关键——

打开 `app/core/context.py`，这个文件只有三个函数，非常简单：

```python
_user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)

def set_user_id(uid: str) -> None:
    _user_id_var.set(uid)

def require_user_id() -> str:
    uid = _user_id_var.get()
    if not uid:
        raise ValueError("缺少 X-User-Id 请求头，无法识别用户身份")
    return uid
```

为什么用 `contextvars`？因为在 ASGI 异步调用链中，`ContextVar` 天然跟随协程传播。transport 层设置了 user_id，后面工具函数里直接 `require_user_id()` 就能拿到，不需要通过参数一层层传递。这和项目里已有的 `request_id` 通过 `structlog.contextvars` 传播是同一个模式。

第三件事，把请求转发给 FastMCP SDK 处理。

所以整个鉴权是两层的：transport 层验 API Key，工具函数层验 user_id 和邮箱的归属关系。关注点分离，transport 不关心业务逻辑，工具函数不关心传输协议。

---

## 第二部分：MCP 工具注册机制（1.5 分钟）

打开 `app/mcp_server/app.py`，这是 MCP 服务的核心入口：

```python
mcp = FastMCP("Mail-MCP-Server", streamable_http_path="/", stateless_http=True)
mcp_tool = create_mcp_tool_decorator(mcp)
from app.tools import mail  # 触发装饰器注册
```

三行代码，三件事。创建 FastMCP 实例，`stateless_http=True` 表示无状态模式，每次请求独立处理。然后创建装饰器工厂。最后导入 mail 模块，触发装饰器执行，完成工具注册。

装饰器工厂在 `app/tools/base.py` 里，它做了一个巧妙的链式包装：先套 Prometheus 监控装饰器 `track_tool_execution`，再套 MCP 的 `@mcp.tool` 装饰器。这样每个工具自动就有了耗时、调用次数、错误率的指标采集，业务代码完全不用关心。

打开 `app/tools/mail.py`，看工具函数的写法。每个工具都是同一个三步模式：

```python
@mcp_tool(name="get_mail_list", description="获取邮箱中的邮件列表...")
async def get_mail_list(email: str, folder: str = "INBOX", ...) -> dict:
    user_id = require_user_id()                          # ① 从 contextvars 拿 user_id
    account = user_store.validate_access(user_id, email)  # ② 校验权限，拿到 passkey
    mails = await imap_service.fetch_mail_list(...)       # ③ 调用服务层
    return {"total": len(mails), "offset": offset, "mails": mails}
```

三个工具，`get_mail_list`、`get_mail_detail`、`send_email`，全部遵循这个模式。工具函数本身非常薄，只做身份校验和参数转发，真正的业务逻辑在服务层。

---

## 第三部分：加密用户存储（2 分钟）

用户的邮箱授权码是敏感信息，不能明文存储。打开 `app/services/user_store.py`。

`UserStore` 类用 Fernet 对称加密。Fernet 底层是 AES-128-CBC 加 HMAC，加密和完整性校验都有了。

存储结构很直观：内存里是 `dict[str, list[EmailAccount]]`，key 是 user_id，value 是这个用户注册的邮箱列表。每个 `EmailAccount` 就是 email 加 passkey。

关键设计点有三个：

第一，启动时从磁盘加载。`initialize()` 方法在 `app/main.py` 的 lifespan 里调用，读取加密文件、解密、反序列化到内存。

第二，写操作用 `asyncio.Lock` 保护。注册和删除都要先拿锁，改完内存后立即加密写回磁盘。读操作不加锁，因为 Python dict 的读取本身是线程安全的。

第三，`validate_access` 方法是工具函数调用的入口。它检查 user_id 下是否注册了这个 email，有就返回 `EmailAccount`（包含 passkey），没有就抛 `PermissionError`。这样 passkey 永远不会暴露给工具函数的调用方，只在服务层内部使用。

注册入口是 `app/routers/registration.py`，这是一个标准的 FastAPI 路由，用 `Depends(verify_api_key)` 做鉴权。注意这里能用 FastAPI 依赖注入，因为注册端点是直接挂在 FastAPI app 上的，不是 MCP 子应用。

---

## 第四部分：IMAP 和 SMTP 服务（2 分钟）

邮件读取用的是 `imap_tools` 库，打开 `app/services/imap_service.py`。

这里有一个重要的技术决策：`imap_tools` 是同步库，但我们的服务是异步的。解决方案是用 `asyncio.to_thread()` 把同步操作丢到线程池里执行。

```python
async def fetch_mail_list(...) -> list[dict]:
    return await asyncio.to_thread(_connect_and_fetch_list, ...)
```

为什么不用连接池？因为 IMAP 是有状态协议，不同用户、不同文件夹的连接不能复用，而且邮箱提供商对并发连接数有限制。所以每次请求新建连接，用 `with MailBox(...).login(...)` 上下文管理器保证连接一定会被关闭。

邮件列表查询用了 `headers_only=True`，只下载邮件头，不下载正文，这对大邮箱的性能很关键。`reverse=True` 保证最新邮件在前。分页是在内存里做的，先取 `offset + limit` 条，再切片。

邮件发送用的是 `aiosmtplib`，打开 `app/services/smtp_service.py`。这个库是原生异步的，不需要 `to_thread` 包装。

一个小细节：`_detect_content_type` 函数会自动检测正文是否包含 HTML 标签，决定用 `text/plain` 还是 `text/html`。这样调用方不需要手动指定格式。

邮箱服务器地址的配置在 `app/services/email_providers.py`，用一个 `PROVIDER_MAP` 字典，按域名后缀映射到 IMAP/SMTP 服务器地址和端口。要新增邮箱提供商，只需要在这个字典里加一行。

---

## 第五部分：生命周期与整体串联（1 分钟）

最后看 `app/main.py` 的 lifespan，把所有组件串起来：

```python
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        await user_store.initialize()   # 加载加密用户配置
        await http_client.start()       # 启动 HTTP 连接池
        yield
        await asyncio.sleep(5)          # 优雅关闭：等待进行中的请求
        await http_client.stop()
```

启动时：MCP session manager 先启动，然后加载用户存储，最后启动 HTTP 客户端。关闭时反过来，先等 5 秒让进行中的请求完成，再清理资源。

中间件栈的顺序也值得注意：CORS → Request-ID → Origin 验证 → Prometheus。Origin 验证跳过了 `/mcp` 和 `/api/` 路径，因为这些端点用 API Key 鉴权，不依赖浏览器 Origin。

注册路由通过 `app.include_router(registration_router)` 挂载，MCP 子应用通过 `app.mount("/mcp", protected_mcp_app)` 挂载。两种挂载方式，对应两种鉴权模式。

---

## 总结（30 秒）

回顾一下关键设计决策：

一，双层鉴权加 contextvars 传递用户身份，解决了 MCP 子应用无法使用 FastAPI 依赖注入的问题。

二，装饰器工厂链式包装，让工具自动获得监控能力，业务代码保持干净。

三，Fernet 加密用户配置，passkey 只在服务层内部流转，不暴露给外部。

四，同步 IMAP 库用 `asyncio.to_thread` 包装，异步 SMTP 库原生使用，两种策略应对不同的库生态。

整个项目的代码量不大，但每一层的职责划分很清晰。如果要扩展，比如加新的邮箱提供商，改 `PROVIDER_MAP`；加新的工具，在 `app/tools/` 下写函数加装饰器就行。

以上就是本项目的关键实现讲解，谢谢大家。
