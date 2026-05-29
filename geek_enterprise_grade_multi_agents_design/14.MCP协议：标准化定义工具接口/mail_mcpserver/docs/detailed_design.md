# 邮件 MCP 服务 — 详细设计文档

> 基于 `docs/design.md` 框架设计规范，面向邮件收发业务的完整实现设计。

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构总览](#2-系统架构总览)
3. [请求处理全链路](#3-请求处理全链路)
4. [新增模块详细设计](#4-新增模块详细设计)
5. [现有模块改动设计](#5-现有模块改动设计)
6. [删除清单](#6-删除清单)
7. [配置与依赖变更](#7-配置与依赖变更)
8. [安全设计](#8-安全设计)
9. [异常处理设计](#9-异常处理设计)
10. [测试设计](#10-测试设计)
11. [实施计划](#11-实施计划)
12. [API 接口规范](#12-api-接口规范)

---

## 1. 项目概述

### 1.1 业务目标

将现有的 MCP 框架 demo 改造为**邮件收发 MCP 服务**，通过 IMAP 协议读取邮件、SMTP 协议发送邮件，为 AI Agent 提供标准化的邮件操作能力。

### 1.2 核心能力

| MCP 工具 | 协议 | 功能 |
|----------|------|------|
| `get_mail_list` | IMAP | 获取邮箱邮件列表（支持文件夹、分页、搜索） |
| `get_mail_detail` | IMAP | 获取指定邮件的完整内容（含附件列表） |
| `send_email` | SMTP | 发送邮件（支持纯文本和 HTML Multipart） |

### 1.3 支持的邮箱提供商

| 提供商 | 域名后缀 | IMAP 服务器 | SMTP 服务器 |
|--------|---------|------------|------------|
| QQ 邮箱 | `qq.com` | imap.qq.com:993 | smtp.qq.com:465 |
| 新浪邮箱 | `sina.com` / `sina.cn` | imap.sina.com:993 | smtp.sina.com:465 |
| 网易邮箱 | `163.com` | imap.163.com:993 | smtp.163.com:465 |

### 1.4 用户模型

- 用户需**预先注册**，提交 `user_id`、`email`、`passkey`（邮箱授权码）
- 一个用户可注册多个邮箱
- 用户配置保存在 **Fernet 加密的本地文件**中
- 所有 MCP 工具调用必须携带 `X-User-Id` 请求头，服务端校验 user_id 与邮箱的归属关系

### 1.5 技术栈变更

在框架原有技术栈基础上，新增：

| 组件 | 技术选型 | 版本 | 用途 |
|------|----------|------|------|
| IMAP 客户端 | imap-tools | >= 1.7.0 | 邮件读取（同步库，asyncio.to_thread 包装） |
| SMTP 客户端 | aiosmtplib | >= 3.0.0 | 异步邮件发送 |
| 加密 | cryptography (Fernet) | >= 42.0.0 | 用户配置加密存储 |

---

## 2. 系统架构总览

### 2.1 改造后的文件结构

```
app/
├── __init__.py
├── main.py                          # 修改：挂载注册路由、lifespan 初始化 user_store
├── core/
│   ├── config.py                   # 修改：新增邮件服务配置项
│   ├── security.py                 # 不变
│   ├── logging.py                  # 不变
│   ├── exceptions.py               # 修改：新增邮件相关异常类
│   └── context.py                  # ★ 新增：user_id ContextVar
├── mcp_server/
│   ├── app.py                      # 修改：服务名、导入 mail 模块
│   └── transport.py                # 修改：提取 X-User-Id 头
├── services/                        # ★ 新增：业务服务层
│   ├── __init__.py
│   ├── email_providers.py          # 邮箱提供商配置映射
│   ├── user_store.py               # 加密用户配置存储
│   ├── imap_service.py             # IMAP 邮件读取服务
│   └── smtp_service.py             # SMTP 邮件发送服务
├── tools/
│   ├── __init__.py                 # 修改：更新文档
│   ├── base.py                     # 不变
│   └── mail.py                     # ★ 新增：三个 MCP 工具
├── routers/                         # ★ 新增：FastAPI 路由
│   ├── __init__.py
│   └── registration.py             # 用户邮箱注册 HTTP 端点
└── utils/
    ├── __init__.py                 # 不变
    ├── http_client.py              # 不变（保留，其他工具可能用到）
    └── metrics.py                  # 不变
```

**删除的文件**：`app/tools/demo.py`、`app/tools/system.py`、`app/tools/resources.py`、`app/tools/prompts.py`

### 2.2 分层架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│  Client (AI Agent / curl / MCP Inspector)                            │
│  Headers: X-API-Key + X-User-Id                                     │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────────────┐
│  接口接入层 (Interface Layer)                    [app/main.py]        │
│                                                                       │
│  ├─ CORSMiddleware                                                   │
│  ├─ add_request_id_middleware (UUID v4 + 耗时)                       │
│  ├─ origin_verification_middleware (跳过 /mcp、/api/)                │
│  ├─ Prometheus Instrumentator                                        │
│  ├─ GET  /health                                                     │
│  ├─ GET  /metrics                                                    │
│  ├─ POST /api/v1/register  → registration_router  ← 新增            │
│  └─ Mount /mcp → protected_mcp_app                                   │
├──────────────────────────────────────────────────────────────────────┤
│  协议适配层 (Protocol Layer)               [app/mcp_server/]         │
│                                                                       │
│  transport.py:                                                        │
│  ├─ verify_api_key_asgi()              ← 已有                        │
│  ├─ 提取 X-User-Id → set_user_id()    ← 新增                        │
│  └─ 委托给 FastMCP Streamable HTTP                                   │
│                                                                       │
│  app.py:                                                              │
│  └─ FastMCP("Mail-MCP-Server") + import mail                        │
├──────────────────────────────────────────────────────────────────────┤
│  业务逻辑层 (Service Layer)                [app/tools/ + services/]   │
│                                                                       │
│  tools/mail.py:                                                       │
│  ├─ @mcp_tool get_mail_list(email, folder, limit, offset, query)     │
│  ├─ @mcp_tool get_mail_detail(email, mail_id)                        │
│  └─ @mcp_tool send_email(send_email, to_email, subject, body)        │
│      每个工具: require_user_id() → validate_access() → 调用服务层     │
│                                                                       │
│  services/:                                                           │
│  ├─ user_store.py      验证 user_id ↔ email 归属，提供 passkey      │
│  ├─ imap_service.py    IMAP 读取（imap_tools + asyncio.to_thread）   │
│  └─ smtp_service.py    SMTP 发送（aiosmtplib 原生异步）              │
├──────────────────────────────────────────────────────────────────────┤
│  基础设施层 (Infrastructure)         [app/core/ + app/utils/]         │
│                                                                       │
│  ├─ context.py         user_id ContextVar 传播    ← 新增             │
│  ├─ config.py          Settings + 邮件配置项      ← 修改             │
│  ├─ exceptions.py      邮件异常类                 ← 修改             │
│  ├─ email_providers.py 域名→服务器映射            ← 新增             │
│  ├─ logging.py / security.py / http_client.py / metrics.py  不变     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. 请求处理全链路

### 3.1 MCP 工具调用完整流程

以 `get_mail_list` 为例：

```
Client POST /mcp/
  │  Headers:
  │    Authorization: Bearer <api-key>
  │    X-User-Id: user01
  │    Content-Type: application/json
  │    Accept: application/json, text/event-stream
  │  Body:
  │    {"jsonrpc":"2.0","method":"tools/call",
  │     "params":{"name":"get_mail_list",
  │               "arguments":{"email":"alice@qq.com","limit":10}},
  │     "id":1}
  │
  ▼
┌─ FastAPI 中间件栈 ─────────────────────────────────────────────────┐
│ ① add_request_id_middleware                                         │
│    request_id = UUID v4                                             │
│    structlog.contextvars.bind_contextvars(request_id=...)           │
│    可选: 提取 X-User-Id 写入日志上下文                               │
│ ② origin_verification_middleware                                    │
│    path.startswith("/mcp") → 跳过                                   │
│ ③ CORSMiddleware                                                    │
│ ④ Prometheus Instrumentator                                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─ Starlette Mount /mcp ──────────────────────────────────────────────┐
│ path 剥离前缀: "/mcp/" → "/"                                        │
│ 进入 protected_mcp_app(scope, receive, send)                        │
│                                                                      │
│ ⑤ API Key 鉴权                                                      │
│    headers[b"authorization"] → "Bearer <key>"                        │
│    secrets.compare_digest(key, settings.MCP_API_KEY)                 │
│                                                                      │
│ ⑥ 提取 user_id  ← 新增                                              │
│    headers[b"x-user-id"] → "user01"                                  │
│    set_user_id("user01")          # 写入 ContextVar                  │
│    structlog.contextvars.bind_contextvars(user_id="user01")          │
│                                                                      │
│ ⑦ 委托 MCP SDK (FastMCP Streamable HTTP handler)                    │
│    解析 JSON-RPC: method="tools/call", name="get_mail_list"         │
│    分发到 get_mail_list 工具函数                                      │
│                                                                      │
│ ⑧ 工具函数执行 (app/tools/mail.py)                                   │
│    8a. user_id = require_user_id()      # 从 ContextVar 读取        │
│        → "user01"                                                    │
│    8b. account = user_store.validate_access("user01", "alice@qq.com")│
│        → EmailAccount(email="alice@qq.com", passkey="xxx")           │
│    8c. track_tool_execution 开始计时  (Prometheus 装饰器)             │
│    8d. mails = await imap_service.fetch_mail_list(                   │
│            email="alice@qq.com",                                     │
│            passkey="xxx",                                            │
│            folder="INBOX",                                           │
│            limit=10, offset=0, query=None                            │
│        )                                                             │
│        → asyncio.to_thread(_fetch_mail_list, ...)                    │
│          → imap_tools: MailBox("imap.qq.com", 993)                   │
│                         .login("alice@qq.com", "xxx")                │
│                         .fetch(headers_only=True, reverse=True)      │
│    8e. track_tool_execution 记录指标                                  │
│        TOOL_DURATION.observe(duration)                                │
│        TOOL_EXECUTION_TOTAL.labels(status="success").inc()           │
│    8f. return {"email":"alice@qq.com","folder":"INBOX","mails":[...]}│
│                                                                      │
│ ⑨ FastMCP 封装 JSON-RPC 响应                                        │
│    {"jsonrpc":"2.0","id":1,"result":{"content":[...]}}               │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─ 中间件返回阶段 ────────────────────────────────────────────────────┐
│ ④ Prometheus: 记录 http_request_duration_seconds                    │
│ ① Request-ID: 记录 latency_ms, 设置 X-Request-ID 响应头             │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 用户注册流程

```
Client POST /api/v1/register
  │  Headers: Authorization: Bearer <api-key>
  │  Body: {"user_id":"user01","email":"alice@qq.com","passkey":"xxx"}
  │
  ▼
┌─ FastAPI 路由 ──────────────────────────────────────────────────────┐
│ ① Depends(verify_api_key)  ← 复用 security.py 中已有的 FastAPI 版本 │
│ ② 校验邮箱域名: get_provider_config("alice@qq.com")                 │
│    → EmailProviderConfig(imap_host="imap.qq.com", ...)              │
│ ③ user_store.register_account("user01", "alice@qq.com", "xxx")      │
│    → asyncio.Lock 加锁                                              │
│    → 内存更新 _users dict                                            │
│    → Fernet 加密 → 写入 data/users.enc                               │
│ ④ 返回 {"success":true, "message":"...", "user_id":"user01", ...}   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. 新增模块详细设计

### 4.1 `app/core/context.py` — user_id 上下文传播

**职责**：通过 Python `contextvars.ContextVar` 在 ASGI 请求链路中传播 user_id，从 transport 层到 tool 函数。

**接口**：

| 函数 | 签名 | 调用方 | 说明 |
|------|------|--------|------|
| `set_user_id` | `(user_id: str) -> Token` | transport.py | 鉴权通过后设置 |
| `get_user_id` | `() -> Optional[str]` | 任意位置 | 可选读取，不抛异常 |
| `require_user_id` | `() -> str` | tools/mail.py | 必须存在，缺失抛 ValueError |

**原理**：Python `contextvars` 在 async 协程链中天然传播。`protected_mcp_app` 中 `await mcp_asgi_app(scope, receive, send)` 与后续 MCP SDK 调用工具函数处于同一异步上下文，因此 transport 层设置的 ContextVar 在工具函数中可读。这与现有 `request_id` 通过 `structlog.contextvars` 传播的机制一致。

**设计决策**：使用独立的 `contextvars.ContextVar` 而非 `structlog.contextvars`，因为 user_id 用于业务鉴权逻辑，需要类型安全的访问接口。同时在 transport 层额外调用 `structlog.contextvars.bind_contextvars(user_id=uid)`，使所有日志自动携带 user_id 字段。

### 4.2 `app/services/email_providers.py` — 邮箱提供商配置

**职责**：维护邮箱域名后缀到 IMAP/SMTP 服务器的映射关系。

**数据结构**：

```python
@dataclass(frozen=True)
class EmailProviderConfig:
    imap_host: str          # IMAP 服务器地址
    imap_port: int          # IMAP 端口，通常 993 (SSL)
    smtp_host: str          # SMTP 服务器地址
    smtp_port: int          # SMTP 端口，通常 465 (SSL) 或 587 (STARTTLS)
    smtp_use_tls: bool      # True=直接 TLS (465), False=STARTTLS (587)
```

**映射表**：

```python
PROVIDER_MAP: dict[str, EmailProviderConfig] = {
    "qq.com":   EmailProviderConfig("imap.qq.com",  993, "smtp.qq.com",  465, True),
    "sina.com": EmailProviderConfig("imap.sina.com", 993, "smtp.sina.com", 465, True),
    "sina.cn":  EmailProviderConfig("imap.sina.com", 993, "smtp.sina.com", 465, True),
    "163.com":  EmailProviderConfig("imap.163.com",  993, "smtp.163.com",  465, True),
}
```

**核心函数**：

```python
def get_provider_config(email: str) -> EmailProviderConfig:
    """
    根据邮箱地址的域名后缀查找提供商配置。

    提取逻辑：email.rsplit("@", 1)[-1].lower()
    不支持的域名抛出 ValueError，错误信息包含所有支持的域名列表。
    """
```

**扩展性**：新增邮箱提供商只需在 `PROVIDER_MAP` 中添加一行映射。未来可改为从配置文件加载。

### 4.3 `app/services/user_store.py` — 加密用户配置存储

**职责**：管理用户邮箱注册信息的加密存储、内存缓存和权限校验。

#### 4.3.1 数据模型

```python
@dataclass
class EmailAccount:
    email: str      # 邮箱地址
    passkey: str    # 邮箱授权码（非登录密码）

@dataclass
class UserConfig:
    user_id: str
    accounts: list[EmailAccount]
```

#### 4.3.2 磁盘存储格式

文件路径由 `USER_STORE_PATH` 配置项指定（默认 `data/users.enc`）。

加密前的 JSON 结构：
```json
{
  "user_001": {
    "accounts": [
      {"email": "alice@qq.com", "passkey": "abcdef123456"},
      {"email": "alice@163.com", "passkey": "ghijkl789012"}
    ]
  },
  "user_002": {
    "accounts": [
      {"email": "bob@sina.com", "passkey": "mnopqr345678"}
    ]
  }
}
```

使用 `cryptography.fernet.Fernet` 加密后存储为二进制文件。Fernet 提供 AES-128-CBC 加密 + HMAC-SHA256 认证，保证数据的机密性和完整性。

#### 4.3.3 类设计

```python
class UserStore:
    _users: dict[str, UserConfig]       # 内存缓存（user_id → UserConfig）
    _fernet: Fernet                      # 加密/解密器
    _file_path: Path                     # 加密文件路径
    _lock: asyncio.Lock                  # 写操作互斥锁
```

#### 4.3.4 方法接口

| 方法 | 类型 | 签名 | 说明 |
|------|------|------|------|
| `initialize` | async | `() -> None` | lifespan 中调用，加载加密密钥和磁盘数据 |
| `register_account` | async | `(user_id, email, passkey) -> None` | 注册或更新邮箱，加锁写入 |
| `remove_account` | async | `(user_id, email) -> bool` | 移除邮箱，返回是否成功 |
| `get_account` | sync | `(user_id, email) -> Optional[EmailAccount]` | 查询账号，无锁 |
| `validate_access` | sync | `(user_id, email) -> EmailAccount` | **核心方法**：校验权限，失败抛异常 |
| `list_accounts` | sync | `(user_id) -> list[str]` | 列出用户所有邮箱 |

#### 4.3.5 并发安全

- **写操作**（register_account、remove_account）：使用 `asyncio.Lock` 串行化，确保内存更新和磁盘持久化的原子性
- **读操作**（get_account、validate_access、list_accounts）：不加锁。Python dict 的读取在 CPython GIL 下是线程安全的，且写操作在 Lock 内完成后 dict 才会被更新
- **单进程限制**：当前设计假设单 Uvicorn worker。多 worker 部署需引入文件锁或迁移到数据库

#### 4.3.6 validate_access 异常行为

```
validate_access("user01", "alice@qq.com")
  → user01 不存在     → raise LookupError("User 'user01' is not registered")
  → user01 存在但无此邮箱 → raise PermissionError("User 'user01' does not have access to email 'alice@qq.com'")
  → 匹配成功          → return EmailAccount(email="alice@qq.com", passkey="xxx")
```

#### 4.3.7 全局单例

```python
user_store = UserStore()  # 模块级单例，在 app/main.py 的 lifespan 中初始化
```

### 4.4 `app/services/imap_service.py` — IMAP 邮件读取

**职责**：封装 `imap_tools` 库，提供异步的邮件列表和详情读取能力。

#### 4.4.1 同步到异步包装策略

`imap_tools` 底层使用 Python 标准库 `imaplib`，是纯同步的。所有 IMAP 操作通过 `asyncio.to_thread()` 在线程池中执行，避免阻塞事件循环。

```
async fetch_mail_list(...)
  └─ await asyncio.to_thread(_fetch_mail_list, ...)
       └─ imap_tools.MailBox(...).login(...).fetch(...)
```

#### 4.4.2 连接管理策略

**每次请求新建连接**，原因：
- IMAP 连接是有状态的（已登录用户、已选择文件夹），不同请求的用户/文件夹不同
- 国内邮箱提供商对单用户并发连接数有限制
- `with MailBox(host, port).login(email, passkey)` 上下文管理器确保连接释放
- 避免连接池复杂度（keepalive、过期淘汰、不同凭据的隔离）

#### 4.4.3 邮件列表接口

```python
async def fetch_mail_list(
    email: str,
    passkey: str,
    folder: str = "INBOX",
    limit: int = 20,
    offset: int = 0,
    query: Optional[str] = None,
) -> list[dict]
```

**内部实现要点**：

| 特性 | 实现 |
|------|------|
| 分页 | `mailbox.fetch(..., limit=slice(offset, offset + limit))` |
| 排序 | `reverse=True`，最新邮件在前 |
| 性能 | `headers_only=True`，不下载正文，仅获取信封信息 |
| 搜索 | `imap_tools.OR(subject=query, from_=query, body=query)` |
| 无搜索 | `imap_tools.AND(all=True)` |

**返回数据结构**（每封邮件）：

```python
{
    "uid": "12345",              # 邮件 UID（IMAP 唯一标识）
    "subject": "会议通知",        # 主题
    "from": "sender@qq.com",     # 发件人
    "date": "2026-02-17 10:30",  # 日期字符串
    "seen": True,                # 是否已读
}
```

#### 4.4.4 邮件详情接口

```python
async def fetch_mail_detail(
    email: str,
    passkey: str,
    mail_id: str,
    folder: str = "INBOX",
) -> dict
```

**返回数据结构**：

```python
{
    "uid": "12345",
    "subject": "会议通知",
    "from": "sender@qq.com",
    "to": ["alice@qq.com"],
    "cc": ["bob@163.com"],
    "date": "2026-02-17 10:30",
    "text_body": "纯文本正文...",
    "html_body": "<html>HTML 正文...</html>",
    "attachments": [
        {"filename": "report.pdf", "content_type": "application/pdf", "size": 102400}
    ]
}
```

**注意**：附件仅返回元信息（文件名、类型、大小），不返回内容。下载附件功能留待后续迭代。

### 4.5 `app/services/smtp_service.py` — SMTP 邮件发送

**职责**：封装 `aiosmtplib` 库，提供异步邮件发送能力。

#### 4.5.1 异步特性

`aiosmtplib` 是原生异步库，直接 `await` 调用，无需 `asyncio.to_thread()`。

#### 4.5.2 发送接口

```python
async def send_email(
    from_email: str,
    passkey: str,
    to_email: str,
    subject: str,
    body: str,
    content_type: str = "plain",    # "plain" 或 "html"
) -> dict
```

#### 4.5.3 邮件构建

使用 Python 标准库 `email.mime` 构建 MIME 消息：

```python
message = MIMEMultipart("alternative")
message["From"] = from_email
message["To"] = to_email
message["Subject"] = subject
message.attach(MIMEText(body, content_type, "utf-8"))
```

使用 `MIMEMultipart("alternative")` 即使当前只有单一内容类型，也保留 Multipart 结构，便于未来扩展（如同时包含纯文本和 HTML 版本）。

#### 4.5.4 TLS 连接策略

根据 `EmailProviderConfig.smtp_use_tls` 决定连接方式：

| 模式 | 端口 | aiosmtplib 参数 | 说明 |
|------|------|-----------------|------|
| 直接 TLS | 465 | `use_tls=True` | 连接即加密（QQ/Sina/163 默认） |
| STARTTLS | 587 | `start_tls=True` | 先明文连接再升级 |

#### 4.5.5 返回数据结构

```python
{
    "success": True,
    "message": "Email sent successfully to alice@qq.com",
    "from": "bob@163.com",
    "to": "alice@qq.com",
    "subject": "会议通知"
}
```

### 4.6 `app/tools/mail.py` — MCP 工具定义

**职责**：定义三个 MCP 工具函数，作为 AI Agent 的调用入口。每个工具遵循统一的三步模式。

#### 4.6.1 统一调用模式

```python
@mcp_tool(name="<tool_name>", description="<描述>")
async def tool_func(...) -> dict:
    # Step 1: 获取 user_id（从请求头通过 ContextVar 传递）
    user_id = require_user_id()

    # Step 2: 校验权限（user_id 是否拥有该邮箱）
    account = user_store.validate_access(user_id, email)

    # Step 3: 调用服务层（使用 account.passkey 作为凭据）
    result = await service_function(email=account.email, passkey=account.passkey, ...)
    return result
```

#### 4.6.2 工具一：get_mail_list

```python
@mcp_tool(
    name="get_mail_list",
    description="获取邮箱中的邮件列表。需要提供邮箱地址，可选指定文件夹、数量限制、偏移量和搜索关键词。",
)
async def get_mail_list(
    email: str,                          # 必填：邮箱地址
    folder: str = "INBOX",               # 可选：文件夹名，默认收件箱
    limit: int = 20,                     # 可选：返回数量，默认 20
    offset: int = 0,                     # 可选：偏移量，默认 0
    query: Optional[str] = None,         # 可选：搜索关键词
) -> dict
```

**返回**：
```python
{
    "email": "alice@qq.com",
    "folder": "INBOX",
    "total_fetched": 10,
    "offset": 0,
    "limit": 20,
    "mails": [...]       # MailSummary 列表
}
```

#### 4.6.3 工具二：get_mail_detail

```python
@mcp_tool(
    name="get_mail_detail",
    description="获取指定邮件的详细内容，包括正文、附件列表等。需要提供邮箱地址和邮件ID。",
)
async def get_mail_detail(
    email: str,                          # 必填：邮箱地址
    mail_id: str,                        # 必填：邮件 UID
) -> dict
```

#### 4.6.4 工具三：send_email

```python
@mcp_tool(
    name="send_email",
    description="发送邮件。支持纯文本和HTML格式正文（Multipart）。需要提供发件邮箱、收件邮箱、主题和正文。",
)
async def send_email(
    send_email: str,                     # 必填：发件人邮箱
    to_email: str,                       # 必填：收件人邮箱
    subject: str,                        # 必填：邮件主题
    body: str,                           # 必填：邮件正文（纯文本或 HTML）
) -> dict
```

**正文类型自动检测**：如果 `body` 中包含 `<html` 或 `<body` 标签，自动以 `text/html` 发送；否则以 `text/plain` 发送。

### 4.7 `app/routers/registration.py` — 用户注册端点

**职责**：提供 FastAPI HTTP 端点，用于管理用户邮箱注册。

#### 4.7.1 端点列表

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/v1/register` | API Key (Depends) | 注册或更新邮箱账号 |
| DELETE | `/api/v1/register` | API Key (Depends) | 移除邮箱账号 |
| GET | `/api/v1/accounts/{user_id}` | API Key (Depends) | 列出用户已注册邮箱 |

#### 4.7.2 注册请求体

```python
class RegisterEmailRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="用户标识")
    email: str = Field(..., description="邮箱地址")
    passkey: str = Field(..., min_length=1, description="邮箱授权码")
```

#### 4.7.3 注册流程

```
POST /api/v1/register
  → Depends(verify_api_key)                       # API Key 鉴权
  → get_provider_config(request.email)             # 校验域名是否支持
  → user_store.register_account(user_id, email, passkey)
  → 200 {"success": true, "message": "...", ...}
```

**鉴权方式**：使用 `app/core/security.py:22-76` 中已有的 `verify_api_key` FastAPI 依赖注入函数。这个函数此前是预留的（文档注释："保留用于未来非 MCP 的 FastAPI 路由鉴权"），现在正式启用。

---

## 5. 现有模块改动设计

### 5.1 `app/core/config.py` — 新增配置项

在 `Settings` 类中新增：

```python
# 用户存储配置
USER_STORE_PATH: str = Field(
    default="data/users.enc",
    description="加密用户配置文件路径",
)
USER_STORE_ENCRYPTION_KEY: str = Field(
    ...,                    # 必填，无默认值
    description="Fernet 加密密钥",
)

# IMAP/SMTP 超时
IMAP_TIMEOUT: int = Field(default=30, description="IMAP 连接超时秒数")
SMTP_TIMEOUT: int = Field(default=30, description="SMTP 连接超时秒数")
```

`USER_STORE_ENCRYPTION_KEY` 设为必填（`Field(...)`），与 `MCP_API_KEY` 一致，确保加密总是被正确配置。

### 5.2 `app/core/exceptions.py` — 新增异常类

```python
class EmailServiceError(MCPException):
    """邮件服务操作异常（IMAP/SMTP 连接或操作失败）"""
    def __init__(self, message: str = "邮件服务异常"):
        super().__init__(message, status_code=502)     # Bad Gateway

class UserNotFoundError(MCPException):
    """用户未注册"""
    def __init__(self, message: str = "用户未注册"):
        super().__init__(message, status_code=404)

class EmailAuthorizationError(MCPException):
    """用户无权操作该邮箱"""
    def __init__(self, message: str = "邮箱访问被拒绝"):
        super().__init__(message, status_code=403)
```

### 5.3 `app/mcp_server/app.py` — 工具注册切换

**变更前**：
```python
mcp = FastMCP("Enterprise-Demo-MCP", ...)
from app.tools import demo, system, resources, prompts
```

**变更后**：
```python
mcp = FastMCP("Mail-MCP-Server", ...)
from app.tools import mail
```

### 5.4 `app/mcp_server/transport.py` — 提取 user_id

在 `protected_mcp_app` 函数中，API Key 鉴权通过后，新增 user_id 提取逻辑：

```python
# 在 verify_api_key_asgi 通过后、委托 mcp_asgi_app 之前：
from app.core.context import set_user_id

user_id_header = headers.get(b"x-user-id")
if user_id_header:
    user_id = user_id_header.decode("utf-8")
    set_user_id(user_id)
    structlog.contextvars.bind_contextvars(user_id=user_id)
    logger.info("mcp_request_user_identified", user_id=user_id, **summary)
else:
    logger.warning("mcp_request_no_user_id", **summary)
```

**设计决策**：不在 transport 层拒绝缺少 `X-User-Id` 的请求。原因：
1. 保持 transport 层只负责 API Key 鉴权，职责单一
2. `tools/list` 等不涉及邮箱操作的 MCP 方法不需要 user_id
3. 工具函数通过 `require_user_id()` 自行校验，给出更精确的错误信息

### 5.5 `app/main.py` — 生命周期和路由

#### 5.5.1 lifespan 修改

```python
from app.services.user_store import user_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        await user_store.initialize()       # ← 新增：加载加密用户数据
        await http_client.start()
        yield
        await asyncio.sleep(5)
        await http_client.stop()
```

#### 5.5.2 挂载注册路由

```python
from app.routers.registration import router as registration_router
app.include_router(registration_router)
```

#### 5.5.3 Origin 中间件跳过 /api/ 路径

```python
# 在 origin_verification_middleware 中：
if request.url.path in ["/", "/health", ...] \
   or request.url.path.startswith("/mcp") \
   or request.url.path.startswith("/api/"):     # ← 新增
    return await call_next(request)
```

---

## 6. 删除清单

| 文件 | 原内容 | 删除原因 |
|------|--------|---------|
| `app/tools/demo.py` | hello_world, echo 工具 | 框架 demo，业务不需要 |
| `app/tools/system.py` | get_server_info, fetch_external_data | 框架 demo，业务不需要 |
| `app/tools/resources.py` | server-info, server-status 资源 | 框架 demo，业务不需要 |
| `app/tools/prompts.py` | code_review, data_analysis 提示词 | 框架 demo，业务不需要 |
| `tests/unit/tools/test_basic.py` | hello_world, echo 测试 | 对应工具已删除 |
| `tests/unit/tools/test_business.py` | get_server_info 测试 | 对应工具已删除 |
| `tests/test_tools.py` | 旧工具测试 | 需重写为邮件工具测试 |

---

## 7. 配置与依赖变更

### 7.1 新增依赖

添加到 `requirements.txt` 和 `pyproject.toml [project.dependencies]`：

```
imap-tools>=1.7.0
aiosmtplib>=3.0.0
cryptography>=42.0.0
```

### 7.2 新增环境变量

| 变量 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `USER_STORE_ENCRYPTION_KEY` | str | **是** | 无 | Fernet 加密密钥（32 字节 base64 编码） |
| `USER_STORE_PATH` | str | 否 | `data/users.enc` | 加密用户配置文件路径 |
| `IMAP_TIMEOUT` | int | 否 | 30 | IMAP 连接超时秒数 |
| `SMTP_TIMEOUT` | int | 否 | 30 | SMTP 连接超时秒数 |

### 7.3 `.env.example` 更新

```env
# ─── 邮件服务配置 ───
# Fernet 加密密钥（必填）
# 生成方式: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
USER_STORE_ENCRYPTION_KEY=

# 加密用户配置文件路径
USER_STORE_PATH=data/users.enc

# IMAP/SMTP 超时（秒）
IMAP_TIMEOUT=30
SMTP_TIMEOUT=30
```

### 7.4 `.gitignore` 更新

```
# User data (encrypted)
data/
```

---

## 8. 安全设计

### 8.1 双层鉴权模型

```
┌──────────────────────────────────────┐
│  第一层：API Key (MCP 端点 + 注册端点)│
│  transport.py / Depends(verify_api_key) │
│  → 验证调用方身份（机器对机器鉴权）    │
├──────────────────────────────────────┤
│  第二层：user_id + email 归属校验      │
│  tools/mail.py → user_store.validate_access() │
│  → 验证用户对邮箱的操作权限            │
└──────────────────────────────────────┘
```

- **API Key** 验证调用方是否为合法客户端（如内部 Agent 平台）
- **user_id + email** 验证具体用户是否拥有该邮箱的操作权限
- 两层独立，缺一不可

### 8.2 凭据保护

| 保护点 | 措施 |
|--------|------|
| 磁盘存储 | Fernet 加密（AES-128-CBC + HMAC-SHA256） |
| 内存中 | passkey 明文存在于 `_users` dict 中，进程退出后清除 |
| 传输中 | HTTPS（由反向代理/网关提供） |
| 日志中 | passkey **不**记录到日志中，仅记录 email |
| API 响应 | 注册端点不回传 passkey |

### 8.3 加密密钥管理

- `USER_STORE_ENCRYPTION_KEY` 通过环境变量注入，不写入代码或配置文件
- 生产环境建议通过 K8s Secret 或 Vault 管理
- 密钥轮换需手动解密旧文件、用新密钥重新加密（未来可自动化）

---

## 9. 异常处理设计

### 9.1 工具函数异常链路

```
MCP 工具函数
  ├─ require_user_id() 失败
  │   → ValueError("user_id not found in request context")
  │   → MCP SDK 捕获，返回 JSON-RPC error response
  │
  ├─ user_store.validate_access() 失败
  │   ├─ LookupError("User 'xxx' is not registered")
  │   └─ PermissionError("User 'xxx' does not have access to email 'yyy'")
  │   → MCP SDK 捕获，返回 JSON-RPC error response
  │
  ├─ imap_service 异常
  │   ├─ imap_tools.MailboxLoginError  → IMAP 登录失败（授权码错误）
  │   ├─ imap_tools.MailboxFolderSelectError → 文件夹不存在
  │   ├─ ConnectionError / TimeoutError → 网络问题
  │   └─ LookupError → 邮件不存在
  │   → MCP SDK 捕获，返回 JSON-RPC error response
  │
  └─ smtp_service 异常
      ├─ aiosmtplib.SMTPAuthenticationError → 认证失败
      ├─ aiosmtplib.SMTPRecipientsRefused → 收件人被拒绝
      └─ aiosmtplib.SMTPException → 其他 SMTP 错误
      → MCP SDK 捕获，返回 JSON-RPC error response
```

### 9.2 ASGI 层异常兜底

`transport.py` 中已有的 try/except 块继续作为最后兜底，捕获所有未处理的异常并返回 500。

### 9.3 注册端点异常

| 异常场景 | HTTP 状态码 | 响应 |
|----------|------------|------|
| 缺少 API Key | 403 | `{"detail": "缺少API Key..."}` |
| 无效 API Key | 403 | `{"detail": "API Key无效"}` |
| 不支持的邮箱域名 | 400 | `{"detail": "Unsupported email domain 'xxx'..."}` |
| 请求体校验失败 | 422 | Pydantic 验证错误列表 |
| 账号不存在（删除时） | 404 | `{"detail": "Account not found"}` |

---

## 10. 测试设计

### 10.1 测试文件结构

```
tests/
├── conftest.py                            # 修改：新增加密密钥、user_store fixtures
├── test_main.py                           # 修改：更新端点断言
├── test_security.py                       # 保留不变
├── test_config.py                         # 修改：测试新配置字段
├── unit/
│   ├── core/
│   │   ├── test_logging.py               # 保留不变
│   │   └── test_context.py               # 新增：user_id ContextVar 测试
│   ├── services/
│   │   ├── __init__.py
│   │   ├── test_email_providers.py       # 新增：提供商配置测试
│   │   ├── test_user_store.py            # 新增：加密存储测试
│   │   ├── test_imap_service.py          # 新增：IMAP 服务测试（mock）
│   │   └── test_smtp_service.py          # 新增：SMTP 服务测试（mock）
│   ├── tools/
│   │   └── test_mail.py                  # 新增：MCP 工具测试（mock 服务层）
│   └── infrastructure/
│       └── test_http_client.py           # 保留不变
└── integration/
    ├── test_api_endpoints.py             # 修改：更新断言
    └── test_registration.py              # 新增：注册端点集成测试
```

### 10.2 测试 Fixtures 变更

`tests/conftest.py` 新增：

```python
import tempfile
from cryptography.fernet import Fernet

TEST_FERNET_KEY = Fernet.generate_key().decode()
os.environ.setdefault("USER_STORE_ENCRYPTION_KEY", TEST_FERNET_KEY)
os.environ.setdefault("USER_STORE_PATH", os.path.join(tempfile.gettempdir(), "test_users.enc"))
```

### 10.3 关键测试用例

#### user_store 测试
- 加密/解密往返：写入后重新加载，数据一致
- 注册新用户、注册新邮箱、更新 passkey
- validate_access 成功/用户不存在/邮箱不匹配
- 多用户并发写入（`asyncio.gather`）
- 空文件启动（首次初始化）

#### email_providers 测试
- 每个支持的域名返回正确配置
- 不支持的域名抛出 ValueError
- 邮箱地址大小写不敏感

#### imap_service 测试（mock imap_tools）
- 正常获取邮件列表
- 带搜索词获取
- 获取邮件详情
- 邮件不存在时抛异常
- 登录失败时抛异常

#### smtp_service 测试（mock aiosmtplib）
- 纯文本邮件发送
- HTML 邮件发送
- SMTP 认证失败
- MIME 消息构建正确性

#### tools/mail 测试
- 工具函数完整调用链（mock user_store + 服务层）
- 缺少 user_id 时抛 ValueError
- 用户无权限时抛异常
- 参数默认值正确

#### registration 端点测试
- 完整注册流程
- 需要 API Key
- 不支持的域名返回 400
- 重复注册更新 passkey
- 删除和列出端点

---

## 11. 实施计划

### Phase 1 — 基础设施（无破坏性变更）

1. 新增 `imap-tools`、`aiosmtplib`、`cryptography` 到 `requirements.txt` 和 `pyproject.toml`
2. 创建 `app/core/context.py`（user_id ContextVar）
3. 创建 `app/services/__init__.py`
4. 创建 `app/services/email_providers.py`（提供商配置）
5. 创建 `app/services/user_store.py`（加密用户存储）
6. 修改 `app/core/config.py`（新增配置项）
7. 修改 `app/core/exceptions.py`（新增异常类）
8. 编写 Phase 1 相关单元测试

### Phase 2 — 服务层

1. 创建 `app/services/imap_service.py`
2. 创建 `app/services/smtp_service.py`
3. 编写 IMAP/SMTP 服务单元测试

### Phase 3 — 切换（一次性替换）

1. 创建 `app/tools/mail.py`（三个 MCP 工具）
2. 创建 `app/routers/__init__.py` 和 `app/routers/registration.py`
3. 修改 `app/mcp_server/transport.py`（提取 user_id）
4. 修改 `app/mcp_server/app.py`（切换导入）
5. 修改 `app/main.py`（lifespan + 注册路由 + 中间件）
6. 删除旧工具文件：demo.py、system.py、resources.py、prompts.py
7. 删除旧测试文件并编写新测试

### Phase 4 — 收尾

1. 更新 `.env.example`
2. 更新 `app/tools/__init__.py` 文档
3. 更新 `tests/conftest.py`
4. 更新 `examples/list_tools.py`
5. 更新 `.gitignore`（加入 `data/`）
6. 全量测试运行
7. 手动端到端验证

---

## 12. API 接口规范

### 12.1 MCP 工具调用

#### 列出工具

```
POST /mcp/
Authorization: Bearer <api-key>
X-User-Id: <user-id>
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}

Response 200:
{
  "jsonrpc": "2.0", "id": 1,
  "result": {
    "tools": [
      {"name": "get_mail_list", "description": "获取邮箱中的邮件列表...", "inputSchema": {...}},
      {"name": "get_mail_detail", "description": "获取指定邮件的详细内容...", "inputSchema": {...}},
      {"name": "send_email", "description": "发送邮件...", "inputSchema": {...}}
    ]
  }
}
```

#### 获取邮件列表

```
POST /mcp/
Authorization: Bearer <api-key>
X-User-Id: user01
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","method":"tools/call",
 "params":{"name":"get_mail_list","arguments":{
   "email":"alice@qq.com","folder":"INBOX","limit":10,"offset":0,"query":"会议"
 }},"id":2}

Response 200:
{
  "jsonrpc": "2.0", "id": 2,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"email\":\"alice@qq.com\",\"folder\":\"INBOX\",\"total_fetched\":3,\"offset\":0,\"limit\":10,\"mails\":[{\"uid\":\"123\",\"subject\":\"会议通知\",\"from\":\"boss@qq.com\",\"date\":\"2026-02-17\",\"seen\":true},...]}"
    }]
  }
}
```

#### 获取邮件详情

```
POST /mcp/
Authorization: Bearer <api-key>
X-User-Id: user01
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","method":"tools/call",
 "params":{"name":"get_mail_detail","arguments":{
   "email":"alice@qq.com","mail_id":"123"
 }},"id":3}
```

#### 发送邮件

```
POST /mcp/
Authorization: Bearer <api-key>
X-User-Id: user01
Content-Type: application/json
Accept: application/json, text/event-stream

{"jsonrpc":"2.0","method":"tools/call",
 "params":{"name":"send_email","arguments":{
   "send_email":"alice@qq.com",
   "to_email":"bob@163.com",
   "subject":"会议提醒",
   "body":"明天上午10点开会，请准时参加。"
 }},"id":4}
```

### 12.2 用户注册端点

#### 注册邮箱

```
POST /api/v1/register
Authorization: Bearer <api-key>
Content-Type: application/json

{"user_id": "user01", "email": "alice@qq.com", "passkey": "abcdef123456"}

Response 200:
{
  "success": true,
  "message": "Email 'alice@qq.com' registered for user 'user01'",
  "user_id": "user01",
  "email": "alice@qq.com"
}
```

#### 移除邮箱

```
DELETE /api/v1/register
Authorization: Bearer <api-key>
Content-Type: application/json

{"user_id": "user01", "email": "alice@qq.com"}

Response 200:
{"success": true, "message": "Account removed"}
```

#### 列出用户邮箱

```
GET /api/v1/accounts/user01
Authorization: Bearer <api-key>

Response 200:
{"user_id": "user01", "accounts": ["alice@qq.com", "alice@163.com"]}
```

### 12.3 错误响应

#### MCP 端点 — 缺少 user_id

```
(MCP JSON-RPC error response, 包含 ValueError 信息)
```

#### MCP 端点 — 用户无权限

```
(MCP JSON-RPC error response, 包含 PermissionError 信息)
```

#### 注册端点 — 不支持的域名

```
HTTP 400
{"detail": "Unsupported email domain 'outlook.com'. Supported: 163.com, qq.com, sina.cn, sina.com"}
```
