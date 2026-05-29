# 项目整体架构说明

这份文档用于从全局到局部理解当前项目的代码结构、运行入口、业务链路、模块职责和配置文件作用。文中的文件路径都写成 Markdown 链接，可以直接点击进入对应源码查看细节。

## 1. 项目定位

当前项目是一个“小红书爆款笔记生成 Agent 实战项目”，核心能力是：

> 用户上传多张图片 + 一句话创作意图，系统通过 FastAPI 接收请求，再由 CrewAI 多 Agent 流程完成图片视觉分析、图片编辑方案、内容策略、文案撰写和 SEO 优化，最终返回一份小红书笔记撰写报告。

技术栈大致是：

- Web 服务：[FastAPI](../../src/app/main.py) + Uvicorn
- 多 Agent 编排：[CrewAI Flow/Agent/Task](../../src/app/crews/xhs_note/flows.py)
- LLM 适配：[阿里云通义千问兼容 OpenAI Chat Completions API](../../src/app/crews/llm/aliyun_llm.py)
- 数据模型：[Pydantic v2](../../src/app/schemas/xhs_note.py)
- 配置管理：[pydantic-settings](../../src/app/core/config.py)
- 日志与监控：[structlog](../../src/app/observability/logging.py) + [Prometheus](../../src/app/observability/metrics.py)
- 数据库预留：[SQLAlchemy Async](../../src/app/db/clients/oceanbase_client.py) + [Alembic](../../src/app/db/migrations/env.py)

## 2. 顶层目录结构

```text
.
├── src/app/                    # 应用源码，采用 src layout
│   ├── main.py                 # FastAPI 应用入口
│   ├── __main__.py             # python -m app 本地启动入口
│   ├── api/                    # API 路由和依赖
│   ├── core/                   # 配置、安全、图片处理等基础能力
│   ├── crews/                  # CrewAI Agent/Task/Flow/LLM/Tools
│   ├── db/                     # 数据库客户端、模型基类、迁移
│   ├── observability/          # 日志、trace、metrics
│   ├── schemas/                # Pydantic 请求/响应/领域模型
│   └── services/               # 业务服务层
├── tests/                      # 单元测试和集成测试
├── deploy/                     # Docker、K8s、Grafana 部署配置
├── doc/                        # 课程资料和已有设计文档
├── pyproject.toml              # 项目元数据、依赖、pytest/ruff 配置
├── alembic.ini                 # Alembic 命令行配置
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略规则
└── README.md                   # 项目说明和快速开始
```

## 3. 运行入口

### 3.1 ASGI 应用入口

真正被 Uvicorn 加载的是 [src/app/main.py](../../src/app/main.py) 里的：

- `create_application()`：创建 FastAPI app，注册中间件、异常处理、路由和 Prometheus 指标。
- `app = create_application()`：Uvicorn 使用的 ASGI 应用对象。

典型启动方式：

```bash
uvicorn app.main:app --reload --app-dir src
```

也可以在安装好项目后用：

```bash
python -m uvicorn app.main:app --reload --app-dir src
```

### 3.2 本地模块启动入口

[src/app/__main__.py](../../src/app/__main__.py) 支持：

```bash
PYTHONPATH=src python -m app
```

它会读取 [src/app/core/config.py](../../src/app/core/config.py) 中的 `APP_PORT` 配置，默认监听 `8072`，并以 reload 模式启动 `app.main:app`。

### 3.3 应用创建时做了什么

[src/app/main.py](../../src/app/main.py) 的主要职责：

- 读取全局配置：[get_settings()](../../src/app/core/config.py)
- 初始化生命周期 `lifespan`，启动时配置日志
- 注册限流中间件：`SlowAPIMiddleware`
- 注册 `request_id` 中间件：生成或透传 `X-Request-ID`
- 注册 trace 中间件：[http_trace_middleware](../../src/app/observability/http_trace.py)
- 注册全局异常处理器和 HTTP 异常处理器
- 挂载健康检查路由：[src/app/api/v1/health.py](../../src/app/api/v1/health.py)
- 挂载业务 API 聚合路由：[src/app/api/v1/__init__.py](../../src/app/api/v1/__init__.py)
- 暴露 Prometheus 指标端点：`/metrics`

## 4. 请求链路总览

核心接口是：

```text
POST /api/v1/xhs/notes/report
```

请求字段：

- `idea_text`：表单字段，用户的一句话创作意图
- `images`：multipart 多文件字段，上传多张图片
- `X-API-Key`：可选/必选取决于环境与配置

整体链路：

```mermaid
sequenceDiagram
    participant User as 用户
    participant API as FastAPI API
    participant Service as xhs_note_service
    participant Flow as xhs_note Flow
    participant Crew as CrewAI Agents
    participant LLM as AliyunLLM

    User->>API: POST /api/v1/xhs/notes/report<br/>idea_text + images
    API->>API: 表单解析 + API Key 校验
    API->>Service: generate_xhs_note_report()
    Service->>Service: 校验图片数量
    Service->>Service: 保存图片到临时目录
    Service->>Service: 压缩图片
    Service->>Flow: run_xhs_note_flow()
    Flow->>Crew: 视觉分析任务
    Crew->>LLM: 多模态图片分析
    Flow->>Crew: 图片编辑方案任务
    Crew->>LLM: 多模态编辑建议
    Flow->>Crew: 策略 -> 文案 -> SEO
    Crew->>LLM: 文本模型调用
    Flow->>Service: final_report
    Service->>Service: 清理临时目录
    Service->>API: report / error
    API->>User: ApiResponse
```

对应代码：

| 层级 | 文件 | 作用 |
| --- | --- | --- |
| API 路由 | [src/app/api/v1/xhs_note.py](../../src/app/api/v1/xhs_note.py) | 定义 `POST /api/v1/xhs/notes/report` |
| API 聚合 | [src/app/api/v1/__init__.py](../../src/app/api/v1/__init__.py) | 把小红书路由挂到 `/api/v1/xhs` |
| 依赖注入 | [src/app/api/dependencies.py](../../src/app/api/dependencies.py) | 提供 request_id 和 API Key 依赖 |
| 鉴权 | [src/app/core/security.py](../../src/app/core/security.py) | 校验 `X-API-Key` |
| 服务层 | [src/app/services/xhs_note_service.py](../../src/app/services/xhs_note_service.py) | 图片保存、压缩、组装领域请求、调用 Flow、清理目录 |
| Flow 编排 | [src/app/crews/xhs_note/flows.py](../../src/app/crews/xhs_note/flows.py) | 三阶段多 Agent 编排 |
| Agent 工厂 | [src/app/crews/xhs_note/agents.py](../../src/app/crews/xhs_note/agents.py) | 创建 CrewAI Agent |
| Task 工厂 | [src/app/crews/xhs_note/tasks.py](../../src/app/crews/xhs_note/tasks.py) | 创建 CrewAI Task |
| 数据模型 | [src/app/schemas/xhs_note.py](../../src/app/schemas/xhs_note.py) | 定义输入、输出、中间结构 |

## 5. API 层

API 入口文件是 [src/app/api/v1/xhs_note.py](../../src/app/api/v1/xhs_note.py)。

核心函数：

```python
async def create_xhs_note_report(...)
```

它做的事情很薄：

1. 从 `multipart/form-data` 读取 `idea_text` 和 `images`。
2. 通过 `Depends(get_request_id)` 获取请求 ID。
3. 通过 `Depends(require_api_key)` 做 API Key 校验。
4. 调用服务层 [generate_xhs_note_report()](../../src/app/services/xhs_note_service.py)。
5. 把结果包装成统一响应 [ApiResponse](../../src/app/schemas/common.py)。

API 层不直接处理图片、不直接调用 LLM，也不编排 Agent，这样职责比较清晰。

健康检查在 [src/app/api/v1/health.py](../../src/app/api/v1/health.py)：

- `GET /health/live`：只表示进程存活。
- `GET /health/ready`：当前返回应用环境信息，后续可以扩展 DB/Redis 探测。

## 6. Service 层

服务层文件是 [src/app/services/xhs_note_service.py](../../src/app/services/xhs_note_service.py)。

核心函数：

```python
async def generate_xhs_note_report(
    idea_text: str,
    files: List[UploadFile],
) -> Tuple[Optional[str], str]
```

它是业务入口，负责把 HTTP 上传文件转换成 CrewAI Flow 能处理的领域模型。

主要步骤：

1. 校验至少上传一张图片。
2. 读取全局配置 [Settings](../../src/app/core/config.py)，尤其是：
   - `data_output_dir`
   - `xhs_image_max_size`
   - `xhs_image_quality`
   - `xhs_max_images`
3. 校验图片数量不超过 `APP_XHS_MAX_IMAGES`。
4. 生成本次运行的 `run_id`。
5. 创建临时目录：

   ```text
   <APP_DATA_OUTPUT_DIR>/xhs_note/<run_id>
   ```

6. 调用 `_save_uploaded_images()` 保存并压缩图片。
7. 组装 [XhsNoteIdeaRequest](../../src/app/schemas/xhs_note.py)。
8. 调用 [run_xhs_note_flow()](../../src/app/crews/xhs_note/flows.py)。
9. 成功或异常后都清理临时目录。

文件名安全处理由 `_sanitize_filename()` 完成，避免路径穿越和常见危险字符。

图片压缩实际调用 [compress_image_to_standard()](../../src/app/core/image_utils.py)，统一控制图片长边尺寸和 JPEG/WebP 质量。

## 7. CrewAI 编排层

CrewAI 相关代码集中在 [src/app/crews](../../src/app/crews)。

### 7.1 编排中心

[src/app/crews/xhs_note/flows.py](../../src/app/crews/xhs_note/flows.py) 是整个 AI 工作流的中心。

对外入口：

```python
async def run_xhs_note_flow(
    idea_request: XhsNoteIdeaRequest,
) -> Tuple[str | None, str]
```

内部分三阶段：

| 阶段 | 函数 | 输入 | 输出 |
| --- | --- | --- | --- |
| 视觉分析 | `_run_visual_analysis_phase()` | 用户意图 + 图片列表 | `visual_by_id` + `visual_summary` |
| 图片编辑方案 | `_run_image_edit_phase()` | 用户意图 + 图片 + 视觉分析结果 | `edit_by_id` + `edit_summary` |
| 内容创作 | `_run_content_phase()` | 用户意图 + 视觉批次报告 + 编辑批次报告 | 策略 brief + 文案 + SEO 笔记 |

最后由 `_generate_final_report()` 把 SEO 结果和图片编辑方案拼成字符串报告。

注意当前 API 最终返回的是字符串报告：

- 响应模型：[XhsNoteReportResponse.report](../../src/app/schemas/xhs_note.py)
- 项目中也定义了结构化的 [XhsNoteFinalReport](../../src/app/schemas/xhs_note.py)，但当前主链路没有直接返回这个结构化模型。

### 7.2 Agent 定义

Agent 工厂在 [src/app/crews/xhs_note/agents.py](../../src/app/crews/xhs_note/agents.py)。

当前有 5 个 Agent：

| Agent 工厂函数 | 配置名 | 职责 | 模型形态 |
| --- | --- | --- | --- |
| `get_xhs_visual_analyst()` | `xhs_visual_analyst` | 视觉分析 | 多模态 |
| `get_xhs_image_editor()` | `xhs_image_editor` | 图片编辑方案 | 多模态 |
| `get_xhs_growth_strategist()` | `xhs_growth_strategist` | 内容增长策略 | 文本 |
| `get_xhs_content_writer()` | `xhs_content_writer` | 小红书文案撰写 | 文本 |
| `get_xhs_seo_expert()` | `xhs_seo_expert` | SEO 优化 | 文本 |

Agent 的角色、目标、背景等大段提示词不写死在 Python 里，而是在 [src/app/crews/config/agents.yaml](../../src/app/crews/config/agents.yaml)。

Python 代码主要负责：

- 读取 YAML 配置。
- 绑定 LLM。
- 绑定工具。
- 设置 `multimodal=True`。

这里每次调用工厂函数都会创建新的 Agent 实例，可以减少并发请求下共享 Agent 状态的风险。

### 7.3 Task 定义

Task 工厂在 [src/app/crews/xhs_note/tasks.py](../../src/app/crews/xhs_note/tasks.py)。

Task 的描述模板在 [src/app/crews/config/tasks.yaml](../../src/app/crews/config/tasks.yaml)。

主要 Task：

| Task 构造函数 | 作用 | 结构化输出 |
| --- | --- | --- |
| `build_visual_analysis_task()` | 单张图片视觉分析 | `XhsImageVisualAnalysis` |
| `build_visual_analysis_summary_task()` | 汇总所有图片视觉分析 | 字符串 |
| `build_image_edit_task()` | 单张图片编辑方案 | `XhsImageEditPlan` |
| `build_image_edit_plan_summary_task()` | 汇总所有图片编辑方案 | 字符串 |
| `get_task_content_strategy()` | 内容策略简报 | `XhsContentStrategyBrief` |
| `get_task_copywriting()` | 小红书文案 | `XhsCopywritingOutput` |
| `get_task_seo_optimization()` | SEO 优化结果 | `XhsSEOOptimizedNote` |

视觉分析和图片编辑单图任务设置了 `async_execution=True`。Flow 中 Crew 使用 `Process.sequential` 和 `akickoff()`，实际并发/异步行为会受 CrewAI 版本和上下文任务依赖影响；从代码设计意图看，它是在尽量让多图任务以异步方式执行，并在最后用 summary task 汇总。

### 7.4 LLM 适配

LLM 入口在 [src/app/crews/llm/__init__.py](../../src/app/crews/llm/__init__.py)：

```python
get_llm(...)
```

当前只支持 `aliyun` provider，实际实现是 [AliyunLLM](../../src/app/crews/llm/aliyun_llm.py)。

[src/app/crews/llm/aliyun_llm.py](../../src/app/crews/llm/aliyun_llm.py) 的关键职责：

- 继承 CrewAI 的 `BaseLLM`。
- 读取 `APP_LLM_API_KEY`、`APP_LLM_REGION`、`APP_LLM_TIMEOUT`、`APP_LLM_RETRY_COUNT` 等配置。
- 根据 region 选择阿里云 DashScope endpoint。
- 调用兼容 OpenAI Chat Completions 格式的接口。
- 支持多模态消息，把本地图片工具返回的 base64 data URL 转换成模型可读的 `image_url` 消息。
- 实现同步 `call()` 和异步 `acall()`。
- 对 5xx、429、超时和网络错误做有限重试。

一个重要设计点：

```python
def supports_function_calling(self) -> bool:
    return False
```

这表示项目让 CrewAI 走 ReAct 文本解析路径，而不是依赖阿里云接口原生 function calling。

### 7.5 Tools

工具在 [src/app/crews/tools](../../src/app/crews/tools)。

| 文件 | 工具 | 作用 |
| --- | --- | --- |
| [add_image_tool_local.py](../../src/app/crews/tools/add_image_tool_local.py) | `AddImageToolLocal` | 读取本地图片，编码为 base64 data URL，供多模态模型使用 |
| [intermediate_tool.py](../../src/app/crews/tools/intermediate_tool.py) | `IntermediateTool` | 让 Agent 保存中间思考产物 |

注意：图片压缩已经在 Service 层通过 [image_utils.py](../../src/app/core/image_utils.py) 完成；`AddImageToolLocal` 当前有效行为是读取传入路径并编码成 base64 data URL。

## 8. 数据模型层

领域模型集中在 [src/app/schemas/xhs_note.py](../../src/app/schemas/xhs_note.py)。

可以按生命周期理解：

### 8.1 上传图片内部表示

- `XhsImageInput`：服务端为每张图生成 `image_id`、保留文件名和本地临时路径。
- `XhsNoteIdeaRequest`：用户意图 + 图片列表，是进入 Flow 的领域请求。

### 8.2 视觉与编辑中间结果

- `XhsImageVisualAnalysis`：单张图的视觉分析。
- `XhsImageEditPlan`：单张图的编辑方案。
- `XhsVisualBatchReport`：多图视觉分析汇总。
- `XhsImageEditBatchReport`：多图编辑方案汇总。

### 8.3 内容创作结果

- `XhsContentStrategyBrief`：增长策略 Agent 输出。
- `XhsCopywritingOutput`：内容撰写 Agent 输出。
- `XhsSEOOptimizedNote`：SEO Agent 输出。

### 8.4 API 响应模型

- `XhsNoteReportResponse`：当前 API 直接返回 `report: str`。
- [src/app/schemas/common.py](../../src/app/schemas/common.py) 中的 `ApiResponse[T]` 是统一响应壳：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "..."
}
```

## 9. Core 基础模块

### 9.1 配置

全局配置在 [src/app/core/config.py](../../src/app/core/config.py)。

核心类：

```python
class Settings(BaseSettings)
```

配置读取规则：

```text
环境变量 > .env 文件 > 代码默认值
```

并且所有项目配置默认使用 `APP_` 前缀，例如：

- `APP_ENV`
- `APP_PORT`
- `APP_LLM_API_KEY`
- `APP_DATABASE_URL`
- `APP_XHS_IMAGE_MAX_SIZE`

特殊兼容：

- 如果没有配置 `APP_LLM_API_KEY`，会尝试读取 `QWEN_API_KEY`。
- 如果没有配置 `APP_BAIDU_API_KEY`，会尝试读取 `BAIDU_API_KEY`。

`get_settings()` 使用 `@lru_cache` 缓存配置对象，避免每次请求重复解析配置。

### 9.2 API Key 鉴权

鉴权逻辑在 [src/app/core/security.py](../../src/app/core/security.py)。

规则：

- 如果配置了 `APP_API_KEYS`，请求必须携带匹配的 `X-API-Key`。
- 如果没配置 `APP_API_KEYS`：
  - development/staging 下允许无 key，返回 `"dev-no-key"`。
  - production 下直接报 500，提示服务端未正确配置 key。

### 9.3 图片处理

图片处理在 [src/app/core/image_utils.py](../../src/app/core/image_utils.py)。

`compress_image_to_standard()` 会：

- 校验文件存在。
- 使用 Pillow 打开图片。
- 按长边 `max_size` 等比缩放。
- 有透明通道时保存为 PNG。
- 无透明通道时保存为 JPEG，并使用配置中的质量参数。
- 覆盖原图时先写临时文件再替换，降低写坏原文件的风险。

## 10. 可观测性模块

可观测性代码集中在 [src/app/observability](../../src/app/observability)。

| 文件 | 作用 |
| --- | --- |
| [logging.py](../../src/app/observability/logging.py) | structlog 配置，request_id/trace_id 注入，日志文件按小时轮转 |
| [trace.py](../../src/app/observability/trace.py) | W3C traceparent 解析、生成 trace_id/span_id |
| [http_trace.py](../../src/app/observability/http_trace.py) | HTTP 请求/响应日志、脱敏、截断、traceparent 响应头 |
| [metrics.py](../../src/app/observability/metrics.py) | AI 专用 Prometheus 指标 |

日志输出位置由 `APP_LOG_DIR` 控制，默认 `./logs`。

主要日志文件：

- `app.log`：全部应用日志
- `error.log`：错误日志
- `crewai_<date>.txt`：CrewAI 执行日志

Prometheus 指标：

- HTTP 通用指标由 `prometheus-fastapi-instrumentator` 自动暴露到 `/metrics`。
- AI 相关指标在 [metrics.py](../../src/app/observability/metrics.py) 中定义，例如 `crew_execution_seconds`、`ai_agent_error_total`。

## 11. 数据库模块

数据库相关代码已经搭好基础设施，但当前小红书主链路没有把报告写入数据库。

| 文件 | 作用 |
| --- | --- |
| [src/app/db/clients/oceanbase_client.py](../../src/app/db/clients/oceanbase_client.py) | SQLAlchemy 异步 engine/session 工厂，兼容 OceanBase/MySQL |
| [src/app/db/clients/file_client.py](../../src/app/db/clients/file_client.py) | 本地文件读写客户端，带根目录隔离，防目录穿越 |
| [src/app/db/models/base.py](../../src/app/db/models/base.py) | SQLAlchemy `Base`、UUID 生成、时间戳 mixin |
| [src/app/db/migrations/env.py](../../src/app/db/migrations/env.py) | Alembic 异步迁移环境 |
| [src/app/db/migrations/script.py.mako](../../src/app/db/migrations/script.py.mako) | Alembic 迁移脚本模板 |

数据库连接串配置项：

```text
APP_DATABASE_URL
```

默认值在代码中是：

```text
sqlite+aiosqlite:///./app.db
```

`.env.example` 中示例是 MySQL/OceanBase 风格：

```text
mysql+aiomysql://user:pass@localhost:2881/your_db
```

## 12. 测试结构

测试目录是 [tests](../../tests)。

| 文件/目录 | 作用 |
| --- | --- |
| [tests/conftest.py](../../tests/conftest.py) | 测试数据工厂、Mock CrewAI 输出、settings fixture |
| [tests/unit](../../tests/unit) | 单元测试 |
| [tests/integration](../../tests/integration) | 接口级集成测试和 curl 脚本 |
| [tests/integration/test_xhs_note.py](../../tests/integration/test_xhs_note.py) | 小红书接口集成测试，mock LLM 调用 |
| [tests/integration/xhs_note_curl.sh](../../tests/integration/xhs_note_curl.sh) | 真实服务的 curl 调用脚本 |
| [tests/result_report.md](../../tests/result_report.md) | 测试结果报告 |
| [tests/result.json](../../tests/result.json) | 测试结果 JSON |

测试配置在 [pyproject.toml](../../pyproject.toml)：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-s"
```

其中 `pythonpath = ["src"]` 很关键，它让测试中可以直接 `import app...`。

运行测试：

```bash
pytest tests/ -v
```

## 13. 配置文件说明

### 13.1 pyproject.toml

[pyproject.toml](../../pyproject.toml) 是当前 Python 项目的核心配置文件。

它包含：

- `[build-system]`：告诉 pip/build 使用 `setuptools` 构建项目。
- `[project]`：项目名、版本、描述、Python 版本、依赖列表。
- `[project.optional-dependencies]`：开发依赖，例如 `pytest`、`httpx`。
- `[tool.setuptools.packages.find]`：声明源码包在 `src` 下。
- `[tool.pytest.ini_options]`：pytest 配置。
- `[tool.ruff]` 和 `[tool.ruff.lint]`：ruff 代码检查配置。

安装依赖的推荐方式：

```bash
pip install -e ".[dev]"
```

其中：

- `-e` 表示 editable install，本地改源码后不需要重新安装。
- `.[dev]` 表示安装主依赖和 `dev` 可选依赖。

### 13.2 为什么没有 requirements.txt

以前很多 Python 项目会用 `requirements.txt` 管依赖；这个项目没有它，是因为依赖已经写在现代标准配置 [pyproject.toml](../../pyproject.toml) 里了。

两者区别可以这么理解：

| 文件 | 更适合做什么 |
| --- | --- |
| `requirements.txt` | 传统 pip 安装清单，常用于“部署时锁定安装哪些包” |
| `pyproject.toml` | 现代 Python 项目标准配置，能同时管理项目元数据、依赖、构建系统、测试工具、格式化工具 |

当前项目采用的是 `pyproject.toml` 的方式，所以不需要单独的 `requirements.txt`。

如果你只是想安装运行依赖：

```bash
pip install -e .
```

如果你还要跑测试：

```bash
pip install -e ".[dev]"
```

如果未来生产部署需要完全锁定依赖版本，可以额外生成：

```bash
pip freeze > requirements.txt
```

但这不是当前项目必须的文件。

### 13.3 .env.example

[.env.example](../../.env.example) 是环境变量模板。

[src/app/core/config.py](../../src/app/core/config.py) 中的 `Settings` 会自动读取 `.env` 文件，但 `.env` 通常包含密钥，所以被 [.gitignore](../../.gitignore) 忽略，不提交到 Git。

使用方式：

```bash
cp .env.example .env
```

然后按需填写：

| 配置项 | 作用 |
| --- | --- |
| `APP_ENV` | 环境：development / staging / production |
| `APP_PORT` | 本地启动端口，默认 8072 |
| `APP_LOG_LEVEL` | 日志级别 |
| `APP_LOG_DIR` | 日志目录 |
| `APP_DATABASE_URL` | 数据库连接串 |
| `APP_REDIS_URL` | Redis 地址，当前主链路暂未用到 |
| `APP_LLM_API_KEY` | 阿里云 LLM API Key，真实调用 Agent 时必需 |
| `APP_LLM_PROVIDER` | 当前只实现 aliyun |
| `APP_LLM_MODEL` | 默认文本模型 |
| `APP_LLM_REGION` | 阿里云 endpoint 区域 |
| `APP_LLM_TIMEOUT` | LLM 请求超时时间 |
| `APP_LLM_RETRY_COUNT` | LLM 请求失败重试次数 |
| `APP_SECRET_KEY` | 生产环境签名/会话密钥 |
| `APP_API_KEYS` | API Key 白名单，逗号分隔 |
| `APP_BAIDU_API_KEY` | 百度千帆搜索 API Key，当前小红书主链路暂未看到直接使用 |
| `APP_DATA_OUTPUT_DIR` | 上传图片临时输出目录 |
| `APP_XHS_IMAGE_MAX_SIZE` | 小红书图片压缩长边最大像素 |
| `APP_XHS_IMAGE_QUALITY` | 小红书图片压缩质量 |

### 13.4 CrewAI YAML 配置

Agent 配置：

- [src/app/crews/config/agents.yaml](../../src/app/crews/config/agents.yaml)

Task 配置：

- [src/app/crews/config/tasks.yaml](../../src/app/crews/config/tasks.yaml)

这两个文件把大段 prompt 从 Python 代码中拆出去，优点是：

- Python 保持结构清晰。
- prompt 可单独维护。
- Agent 和 Task 的职责边界更明显。

代码读取位置：

- Agent YAML 读取：[src/app/crews/xhs_note/agents.py](../../src/app/crews/xhs_note/agents.py)
- Task YAML 读取：[src/app/crews/xhs_note/tasks.py](../../src/app/crews/xhs_note/tasks.py)

### 13.5 alembic.ini

[alembic.ini](../../alembic.ini) 是 Alembic 命令行配置。

关键项：

```ini
script_location = src/app/db/migrations
```

表示迁移脚本目录在 [src/app/db/migrations](../../src/app/db/migrations)。

`sqlalchemy.url` 在 `alembic.ini` 中只是占位值，真实运行时 [src/app/db/migrations/env.py](../../src/app/db/migrations/env.py) 会通过 `get_settings().database_url` 读取 `APP_DATABASE_URL`。

### 13.6 Dockerfile

Docker 配置在 [deploy/docker/Dockerfile](../../deploy/docker/Dockerfile)。

特点：

- 多阶段构建。
- 使用 `python:3.11-slim`。
- 先根据 [pyproject.toml](../../pyproject.toml) 构建 wheel。
- 运行阶段安装 wheel。
- 设置 `PYTHONPATH=/app/src`。
- 默认 `APP_ENV=production`。
- 创建非 root 用户 `app`。
- 容器内监听端口 `8000`。
- 启动命令是：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

注意：本地默认端口是 `8072`，Docker/K8s 默认端口是 `8000`。

### 13.7 K8s 配置

K8s Deployment 在 [deploy/k8s/deployment.yaml](../../deploy/k8s/deployment.yaml)。

它定义：

- Deployment：`ai-service`
- 副本数：3
- 容器镜像：`enterprise-ai-app:latest`
- 环境变量来源：
  - ConfigMap：`ai-app-config`
  - Secret：`ai-app-secrets`
- livenessProbe：`/health/live`
- readinessProbe：`/health/ready`
- Service：ClusterIP 暴露 8000

ConfigMap 示例在 [deploy/k8s/configmap.example.yaml](../../deploy/k8s/configmap.example.yaml)，只放非敏感配置。真实密钥应该放到 Kubernetes Secret，不要写进 ConfigMap。

### 13.8 Grafana Dashboard

[deploy/grafana/dashboard.json](../../deploy/grafana/dashboard.json) 是 Grafana 仪表盘配置，用于配合 Prometheus 展示服务指标。

### 13.9 .gitignore

[.gitignore](../../.gitignore) 主要忽略：

- `.env`、虚拟环境、Python 缓存
- 构建产物
- 测试缓存和覆盖率
- IDE 配置
- 数据目录、日志目录、临时文件

这解释了为什么你本地可能有 `.env`、`.venv`、`logs/`、`data/`，但它们不会进入 Git。

### 13.10 README.md

[README.md](../../README.md) 是面向使用者的快速说明，包含项目介绍、技术栈、快速开始、接口测试和部署说明。

它提到 `.vscode/launch.json`，但当前仓库中没有跟踪 `.vscode` 目录，并且 [.gitignore](../../.gitignore) 会忽略 `.vscode/`。所以以当前目录为准，IDE 调试配置不属于已提交代码的一部分。

## 14. 主业务模块细节

### 14.1 小红书接口如何返回

[src/app/api/v1/xhs_note.py](../../src/app/api/v1/xhs_note.py) 中：

- 成功时：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "report": "最终报告字符串"
  },
  "request_id": "..."
}
```

- Flow 返回错误但没有抛异常时：

```json
{
  "code": 1,
  "message": "小红书笔记生成失败: ...",
  "data": null,
  "request_id": "..."
}
```

- 代码异常时：抛 `HTTPException(500)`，由全局异常处理返回错误响应。

### 14.2 图片生命周期

图片从上传到清理的过程：

```text
UploadFile
  -> _sanitize_filename()
  -> <data_output_dir>/xhs_note/<run_id>/<safe_filename>
  -> compress_image_to_standard()
  -> XhsImageInput(local_path=...)
  -> AddImageToolLocal 读取 local_path
  -> base64 data URL 进入多模态 LLM
  -> Flow 结束
  -> _cleanup_temp_directory()
```

相关代码：

- 上传处理：[src/app/services/xhs_note_service.py](../../src/app/services/xhs_note_service.py)
- 图片压缩：[src/app/core/image_utils.py](../../src/app/core/image_utils.py)
- 图片转 base64：[src/app/crews/tools/add_image_tool_local.py](../../src/app/crews/tools/add_image_tool_local.py)

### 14.3 多 Agent 工作流

可以把 [flows.py](../../src/app/crews/xhs_note/flows.py) 里的流程理解成：

```text
XhsNoteIdeaRequest
    |
    v
视觉分析阶段
    - 每张图片生成 XhsImageVisualAnalysis
    - 生成 visual_summary
    |
    v
图片编辑阶段
    - 只处理视觉分析成功的图片
    - 每张图片生成 XhsImageEditPlan
    - 生成 edit_summary
    |
    v
内容创作阶段
    - 内容策略 XhsContentStrategyBrief
    - 文案 XhsCopywritingOutput
    - SEO XhsSEOOptimizedNote
    |
    v
字符串 final_report
```

中间结果通过 Pydantic 模型约束，CrewAI Task 使用 `output_pydantic=...` 尽量让 LLM 输出可解析结构。

## 15. 依赖和安装方式

当前项目的依赖都在 [pyproject.toml](../../pyproject.toml) 的：

```toml
dependencies = [
    ...
]
```

主要依赖类别：

| 类别 | 依赖 |
| --- | --- |
| Web | `fastapi`, `uvicorn[standard]`, `python-multipart` |
| 配置与模型 | `pydantic`, `pydantic-settings` |
| 日志监控 | `structlog`, `prometheus-fastapi-instrumentator` |
| 安全限流 | `slowapi` |
| 数据库 | `sqlalchemy[asyncio]`, `aiosqlite`, `aiomysql`, `alembic`, `redis` |
| AI 编排 | `crewai`, `crewai-tools` |
| HTTP/YAML/图片 | `requests`, `pyyaml`, `Pillow`, `aiofiles` |
| 测试可选依赖 | `pytest`, `pytest-asyncio`, `httpx` |

本地开发推荐：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## 16. 阅读代码建议顺序

如果你想快速理解项目，不建议从所有文件平铺阅读。推荐按这个顺序：

1. [README.md](../../README.md)：先知道项目目标和接口形态。
2. [src/app/main.py](../../src/app/main.py)：理解 FastAPI 应用如何被创建。
3. [src/app/api/v1/xhs_note.py](../../src/app/api/v1/xhs_note.py)：看 HTTP 请求怎么进入业务。
4. [src/app/services/xhs_note_service.py](../../src/app/services/xhs_note_service.py)：看上传图片如何变成领域请求。
5. [src/app/schemas/xhs_note.py](../../src/app/schemas/xhs_note.py)：理解所有中间数据结构。
6. [src/app/crews/xhs_note/flows.py](../../src/app/crews/xhs_note/flows.py)：重点阅读三阶段 Agent 编排。
7. [src/app/crews/xhs_note/agents.py](../../src/app/crews/xhs_note/agents.py) 和 [src/app/crews/config/agents.yaml](../../src/app/crews/config/agents.yaml)：理解 Agent 角色。
8. [src/app/crews/xhs_note/tasks.py](../../src/app/crews/xhs_note/tasks.py) 和 [src/app/crews/config/tasks.yaml](../../src/app/crews/config/tasks.yaml)：理解 Task 模板和结构化输出。
9. [src/app/crews/llm/aliyun_llm.py](../../src/app/crews/llm/aliyun_llm.py)：理解模型调用、重试、多模态消息适配。
10. [src/app/core/config.py](../../src/app/core/config.py) 和 [.env.example](../../.env.example)：理解所有环境变量。
11. [tests/unit/test_flows.py](../../tests/unit/test_flows.py)、[tests/unit/test_service.py](../../tests/unit/test_service.py)、[tests/unit/test_api.py](../../tests/unit/test_api.py)：用测试反向确认预期行为。

## 17. 当前架构的几个关键观察

- 当前主业务是小红书笔记生成，数据库模块更多是框架预留，主链路暂未持久化报告。
- `pyproject.toml` 已经承担依赖声明职责，所以没有 `requirements.txt` 是正常的。
- API 返回的是字符串报告，而不是完整结构化 `XhsNoteFinalReport`，如果后续要做前端展示或持久化，可能会考虑改成结构化返回。
- `.env.example` 中有百度搜索配置，但当前小红书主链路未看到直接调用百度搜索工具。
- 本地端口默认 `8072`，Docker/K8s 配置默认 `8000`，排查启动问题时要注意端口来源。
- README 中提到 `.vscode/launch.json`，但当前仓库没有提交这个目录。

