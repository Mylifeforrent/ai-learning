# config.py 中 model_config 与 .env/default 配置关系

## 先给结论

`src/app/core/config.py` 里的这段不是无效代码：

```python
model_config = SettingsConfigDict(
    env_prefix="APP_",
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)
```

它不会被项目业务代码显式调用，所以用 `rg model_config` 看起来像“没人引用”。但 `Settings` 继承自 `pydantic_settings.BaseSettings`，在执行 `Settings()` 时，Pydantic Settings 会自动读取这个类属性，用它决定环境变量前缀、`.env` 文件位置、编码、以及多余字段怎么处理。

本项目真正的入口是：

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

业务代码通常调用 `get_settings()`，然后才拿到配置值。

## 加载链路

运行时大致是这样：

```text
业务代码调用 get_settings()
  -> get_settings() 第一次执行 Settings()
  -> BaseSettings 读取 Settings.model_config
  -> 按配置加载环境变量、.env、字段默认值
  -> 执行 validators
  -> 返回 Settings 实例
  -> lru_cache 缓存这个实例
```

所以 `model_config` 是“框架约定式配置”，不是普通业务函数调用。

## 到底用 .env 还是 config.py 默认值

两者都会用，但优先级不同。

在本项目正常运行方式下，`get_settings()` 没有传构造参数，所以主要优先级是：

```text
系统环境变量 APP_* > 项目根目录 .env > config.py 字段默认值
```

例如：

```python
port: int = 8072
```

因为配置了：

```python
env_prefix="APP_"
```

所以它对应的环境变量是：

```env
APP_PORT=8072
```

如果你的 `.env` 中写了：

```env
APP_PORT=9000
```

那么 `settings.port` 会是 `9000`，不是 `8072`。

如果系统环境变量里又写了：

```bash
APP_PORT=8000
```

那么 `settings.port` 会是 `8000`，系统环境变量优先于 `.env`。

如果 `.env` 和系统环境变量都没有配置 `APP_PORT`，才会使用 `config.py` 里的默认值 `8072`。

补充：如果代码里手动写 `Settings(port=1234)`，构造参数优先级比环境变量还高。测试代码里经常这样写，是为了绕开真实 `.env`。

## .env.example、.env、config.py 的角色

当前仓库里能看到 `.env.example`，但没有实际 `.env` 文件。

它们的职责不同：

| 文件 | 职责 |
| --- | --- |
| `.env.example` | 配置模板，告诉你有哪些变量可以填，不会自动生效 |
| `.env` | 本地真实配置文件，会被 `Settings` 自动读取 |
| `config.py` | 定义配置字段、类型、默认值、校验规则、加载规则 |

也就是说，`.env.example` 需要复制成 `.env` 后才会参与运行时配置：

```bash
cp .env.example .env
```

然后编辑 `.env` 里的值。

另外，`env_file=".env"` 是相对于进程当前工作目录读取的。通常从项目根目录启动服务时没有问题；如果从别的目录启动，可能读不到这个 `.env`。

## 为什么 config.py 里还要定义很多默认配置

这些字段不是为了和 `.env` 二选一，而是为了给整个应用定义一套统一的配置模型：

1. 字段名：代码里统一用 `settings.llm_model`、`settings.port`。
2. 类型：比如 `port: int`、`database_echo: bool`、`llm_timeout: int`。
3. 默认值：本地开发或未配置时仍可启动。
4. 校验：比如 `log_level` 只能是 `DEBUG/INFO/WARNING/ERROR`，`xhs_image_quality` 必须在 `1-100`。
5. 文档化：看 `Settings` 类就能知道项目支持哪些配置项。

所以默认值不是“覆盖 .env”，而是“没有外部配置时的 fallback”。

## 字段与环境变量如何对应

规则是：

```text
字段名 -> 大写 -> 加 APP_ 前缀
```

示例：

| Settings 字段 | 环境变量 |
| --- | --- |
| `env` | `APP_ENV` |
| `port` | `APP_PORT` |
| `log_level` | `APP_LOG_LEVEL` |
| `database_url` | `APP_DATABASE_URL` |
| `llm_api_key` | `APP_LLM_API_KEY` |
| `llm_retry_count` | `APP_LLM_RETRY_COUNT` |
| `xhs_image_max_size` | `APP_XHS_IMAGE_MAX_SIZE` |
| `xhs_max_images` | `APP_XHS_MAX_IMAGES` |
| `crew_execution_timeout` | `APP_CREW_EXECUTION_TIMEOUT` |

因为配置了 `extra="ignore"`，所以 `.env` 里多出来、且没有映射到 `Settings` 字段的配置，会被忽略，不会报错。

## QWEN_API_KEY 和 BAIDU_API_KEY 的特殊 fallback

`config.py` 里还有一个 `model_validator(mode="before")`：

```python
if not (out.get("llm_api_key") or "").strip():
    out["llm_api_key"] = os.environ.get("QWEN_API_KEY", "").strip()
if not (out.get("baidu_api_key") or "").strip():
    out["baidu_api_key"] = os.environ.get("BAIDU_API_KEY", "").strip()
```

意思是：

1. 优先读取 `APP_LLM_API_KEY`。
2. 如果没配 `APP_LLM_API_KEY`，再尝试从系统环境变量 `QWEN_API_KEY` 兜底。
3. 优先读取 `APP_BAIDU_API_KEY`。
4. 如果没配 `APP_BAIDU_API_KEY`，再尝试从系统环境变量 `BAIDU_API_KEY` 兜底。

注意这里用的是 `os.environ.get(...)`，所以这个 fallback 更准确地说是读取“系统环境变量”。如果只是把 `QWEN_API_KEY` 写进 `.env`，但没有写 `APP_LLM_API_KEY`，不建议依赖它一定生效。最稳妥的写法还是：

```env
APP_LLM_API_KEY=你的key
APP_BAIDU_API_KEY=你的key
```

## 当前项目中哪些配置被实际使用

下面是从当前代码引用关系梳理出来的情况。

| 配置字段 | 当前用途 |
| --- | --- |
| `env` | 控制 FastAPI docs/redoc 是否开放；健康检查返回环境；安全逻辑判断生产环境 |
| `port` | `python -m app` 本地启动时传给 uvicorn |
| `log_level` | 应用启动时配置日志级别 |
| `log_dir` | 应用日志和 CrewAI 执行日志输出目录 |
| `database_url` | SQLAlchemy 连接池和 Alembic 迁移读取 |
| `database_echo` | SQLAlchemy engine 是否打印 SQL |
| `llm_api_key` | 阿里云 LLM 调用密钥 |
| `llm_provider` | `get_llm()` 选择 LLM provider，目前只支持 `aliyun` |
| `llm_model` | 默认文本模型 |
| `llm_image_model` | 默认多模态图片模型 |
| `llm_region` | 阿里云 endpoint 区域 |
| `llm_timeout` | LLM 请求超时时间 |
| `llm_retry_count` | LLM 请求失败重试次数 |
| `api_keys` | API 鉴权白名单，逗号分隔 |
| `data_output_dir` | 小红书笔记上传图片的临时输出根目录 |
| `xhs_image_max_size` | 小红书图片压缩长边限制 |
| `xhs_image_quality` | 小红书图片压缩质量 |
| `xhs_max_images` | 单次小红书请求最大图片数量 |
| `crew_execution_timeout` | CrewAI 每阶段执行超时时间 |

下面这些字段目前在 `src` 业务代码中没有看到实际读取，更多像是框架预留或后续扩展项：

| 配置字段 | 备注 |
| --- | --- |
| `redis_url` | 可能为后续队列/缓存预留 |
| `llm_base_url` | 可能为后续自定义 LLM endpoint 预留 |
| `secret_key` | 生产密钥字段已定义，但当前安全逻辑主要使用 `api_keys` |
| `baidu_api_key` | 已定义并支持 fallback，但当前 `src` 中没看到实际搜索工具调用 |
| `baidu_search_timeout` | 同上，当前未看到实际读取 |
| `tools_directory_read_root` | 目录读取工具的安全配置预留，当前未看到实际读取 |

## 一句话判断

`model_config` 有效，它由 `BaseSettings` 自动消费。

`config.py` 里的默认配置也有效，但只在没有对应 `APP_*` 环境变量、也没有 `.env` 配置时才兜底。

实际运行时不是“.env 和 config.py 二选一”，而是：

```text
config.py 定义配置模型和默认值
.env/系统环境变量按 APP_ 前缀覆盖这些默认值
业务代码统一通过 get_settings() 读取最终合并后的结果
```
