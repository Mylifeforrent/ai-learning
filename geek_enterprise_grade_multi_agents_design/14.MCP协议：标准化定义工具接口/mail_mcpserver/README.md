# Mail MCP Server

基于 FastAPI 构建的邮件收发 MCP (Model Context Protocol) 服务器，通过 IMAP 协议读取邮件、SMTP 协议发送邮件，为 AI Agent 提供标准化的邮件操作能力。采用 2025 Streamable HTTP 传输协议规范。

## 核心特性

- **邮件收发** - 支持 QQ、新浪、163 邮箱的 IMAP 读取和 SMTP 发送
- **Streamable HTTP 传输** - 遵循 MCP 2025-06-18 规范，单端点 (`/mcp/`) 双向通信
- **双层鉴权** - API Key 传输层鉴权 + user_id/email 业务层权限校验
- **加密存储** - 用户邮箱授权码使用 Fernet 对称加密持久化
- **异步优先** - 基于 FastAPI ASGI，SMTP 原生异步，IMAP 通过 `asyncio.to_thread` 包装
- **可观测性** - Structlog 结构化 JSON 日志 + Prometheus 指标（工具粒度耗时/计数/错误率）
- **弹性设计** - httpx 连接池 + Tenacity 指数退避重试 + 优雅关闭

---

## MCP 工具

| 工具 | 协议 | 功能 |
|------|------|------|
| `get_mail_list` | IMAP | 获取邮件列表（支持文件夹、分页、按主题搜索） |
| `get_mail_detail` | IMAP | 获取邮件详情（完整正文、附件列表） |
| `send_email` | SMTP | 发送邮件（自动检测纯文本/HTML） |

### 支持的邮箱

| 提供商 | 域名 | IMAP | SMTP |
|--------|------|------|------|
| QQ 邮箱 | `qq.com` | imap.qq.com:993 | smtp.qq.com:465 |
| 新浪邮箱 | `sina.com` / `sina.cn` | imap.sina.com:993 | smtp.sina.com:465 |
| 网易邮箱 | `163.com` | imap.163.com:993 | smtp.163.com:465 |

---

## 快速开始

### 1. 环境要求

- Python 3.11+

### 2. 安装

```bash
git clone <your-repo-url>
cd mail_mcpserver

python -m venv venv
source venv/bin/activate

pip install -e ".[dev]"
```

### 3. 配置

```bash
cp .env.example .env
```

编辑 `.env`，**必须设置以下两项**：

```env
MCP_API_KEY=your-secret-api-key          # MCP 端点鉴权密钥
USER_STORE_ENCRYPTION_KEY=your-fernet-key # Fernet 加密密钥
```

生成 Fernet 密钥：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

完整配置项见 [.env.example](.env.example)。

### 4. 启动服务

```bash
# 方式一：直接运行
python -m app.main

# 方式二：uvicorn（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8007
```

### 5. 注册邮箱账号

使用前必须先注册用户邮箱：

```bash
curl -X POST http://localhost:8007/api/v1/register \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user01","email":"yourname@qq.com","passkey":"你的邮箱授权码"}'
```

### 6. 使用 MCP 工具

```bash
# 列出所有工具
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'

# 查看邮件列表
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_mail_list","arguments":{"email":"yourname@qq.com","limit":5}},"id":2}'

# 查看邮件详情
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_mail_detail","arguments":{"email":"yourname@qq.com","mail_uid":"123"}},"id":3}'

# 发送邮件
curl -X POST http://localhost:8007/mcp/ \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "X-User-Id: user01" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"send_email","arguments":{"from_email":"yourname@qq.com","to_email":"receiver@163.com","subject":"测试邮件","body":"这是一封测试邮件"}},"id":4}'
```

### 7. Docker 部署

```bash
docker build -t mail-mcp-server .
docker run -p 8007:8000 \
  -e MCP_API_KEY=your-secret-api-key \
  -e USER_STORE_ENCRYPTION_KEY=your-fernet-key \
  -v $(pwd)/data:/app/data \
  mail-mcp-server
```

---

## 服务端点一览

| 端点 | 方法 | 鉴权 | 说明 |
|------|------|------|------|
| `/` | GET | 否 | API 基本信息 |
| `/health` | GET | 否 | 健康检查（K8s liveness/readiness） |
| `/docs` | GET | 否 | Swagger UI 文档 |
| `/metrics` | GET | 否 | Prometheus 指标 |
| `/api/v1/register` | POST | API Key | 注册/更新用户邮箱账号 |
| `/api/v1/register` | DELETE | API Key | 移除用户邮箱账号 |
| `/api/v1/accounts/{user_id}` | GET | API Key | 列出用户已注册邮箱 |
| `/mcp/` | POST | API Key + X-User-Id | MCP JSON-RPC 端点（**必须带末尾 `/`**） |

鉴权方式：`Authorization: Bearer <key>` 或 `X-API-Key: <key>`

---

## 项目结构

```
mail_mcpserver/
├── app/
│   ├── main.py                   # FastAPI 入口：中间件、生命周期、路由挂载
│   ├── core/
│   │   ├── config.py             # Pydantic Settings 配置管理
│   │   ├── context.py            # user_id ContextVar 上下文传递
│   │   ├── security.py           # API Key 鉴权 + Origin 校验
│   │   ├── logging.py            # Structlog 日志配置
│   │   └── exceptions.py         # 全局异常类 + 异常处理器
│   ├── mcp_server/
│   │   ├── app.py                # FastMCP 实例 + 工具注册
│   │   └── transport.py          # ASGI 鉴权 + X-User-Id 提取
│   ├── services/
│   │   ├── email_providers.py    # 邮箱提供商配置（域名→服务器映射）
│   │   ├── user_store.py         # Fernet 加密用户配置存储
│   │   ├── imap_service.py       # IMAP 邮件读取（imap_tools + to_thread）
│   │   └── smtp_service.py       # SMTP 邮件发送（aiosmtplib）
│   ├── tools/
│   │   ├── base.py               # @mcp_tool 装饰器工厂
│   │   └── mail.py               # 三个 MCP 邮件工具
│   ├── routers/
│   │   └── registration.py       # 用户邮箱注册 HTTP 端点
│   └── utils/
│       ├── http_client.py        # 异步 HTTP 客户端
│       └── metrics.py            # Prometheus 指标
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── core/test_context.py
│   │   ├── services/test_email_providers.py
│   │   ├── services/test_user_store.py
│   │   └── tools/test_mail.py
│   └── integration/
│       └── test_api_endpoints.py
├── docs/
│   ├── design.md                 # 需求设计
│   └── detailed_design.md        # 详细设计文档
├── examples/
│   └── list_tools.py             # 示例：HTTP 调用 MCP 工具
├── .env.example
├── Dockerfile
└── pyproject.toml
```

---

## 架构设计

### 分层架构

```
┌─────────────────────────────────────────────────────┐
│  Client (AI Agent / curl / MCP Inspector / ...)      │
└────────────────────────┬────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────┐
│  Interface Layer   (app/main.py)                     │
│  ├─ CORS Middleware                                  │
│  ├─ Request-ID + Latency Middleware                  │
│  ├─ Origin Verification Middleware                   │
│  └─ Prometheus Instrumentator                        │
├──────────────────────────────────────────────────────┤
│  Protocol Layer    (app/mcp_server/)                 │
│  ├─ transport.py   ASGI Auth + X-User-Id 提取        │
│  └─ app.py         FastMCP (Streamable HTTP)         │
├──────────────────────────────────────────────────────┤
│  Service Layer     (app/services/ + app/tools/)      │
│  ├─ mail.py        MCP 工具 (get_mail_list, ...)     │
│  ├─ imap_service   IMAP 邮件读取                     │
│  ├─ smtp_service   SMTP 邮件发送                     │
│  └─ user_store     加密用户配置管理                   │
├──────────────────────────────────────────────────────┤
│  Infrastructure    (app/core/ + app/utils/)           │
│  ├─ config.py      Pydantic Settings                 │
│  ├─ context.py     user_id ContextVar                │
│  ├─ security.py    Auth & Origin Verification        │
│  ├─ logging.py     Structlog + File Rotation         │
│  └─ metrics.py     Prometheus Counters/Histograms    │
└──────────────────────────────────────────────────────┘
```

### 请求处理流程

```
Client POST /mcp/ (Bearer token + X-User-Id)
  → CORS Middleware
  → Request-ID Middleware (生成/透传 X-Request-ID, 绑定 contextvars)
  → Origin Middleware (跳过 /mcp 和 /api/ 路径)
  → Starlette Mount → ASGI transport.py
    → verify_api_key_asgi() → 403 或继续
    → 提取 X-User-Id → set_user_id() 写入 contextvars
    → FastMCP Streamable HTTP handler
      → JSON-RPC dispatch → tools/call
      → mail.py → require_user_id() → user_store.validate_access()
      → imap_service / smtp_service
    → JSON 响应
  → Latency 记录 + X-Request-ID 响应头
```

---

## 测试

```bash
# 运行所有测试（排除需要运行服务的集成测试）
pytest tests/ -v --ignore=tests/test_crewai.py --ignore=tests/test_mcp_direct.py

# 带覆盖率
pytest tests/ --cov=app --cov-report=html
```

---

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| Web 框架 | FastAPI | ASGI 异步框架 |
| MCP SDK | mcp (FastMCP) | MCP 协议实现 |
| IMAP | imap_tools | 邮件读取 |
| SMTP | aiosmtplib | 异步邮件发送 |
| 加密 | cryptography (Fernet) | 用户配置加密 |
| 日志 | structlog | 结构化 JSON 日志 |
| 配置 | pydantic-settings | 环境变量管理 |
| 监控 | prometheus-client | 指标采集 |
| HTTP 客户端 | httpx + tenacity | 外部调用 + 重试 |

---

## 许可证

MIT License

## 参考文档

- [MCP 规范 (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [FastMCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [需求设计](./docs/design.md)
- [详细设计](./docs/detailed_design.md)
