# pyproject.toml、.env.example、alembic.ini 与 egg-info 关系说明

这份笔记解释这几个文件/目录分别做什么：

- `src/enterprise_ai_app.egg-info/`
- `.env.example`
- `alembic.ini`
- `pyproject.toml`

以及为什么这个项目没有常见的 `requirements.txt`。

## 一句话结论

`enterprise_ai_app.egg-info` 是 Python 打包工具根据 `pyproject.toml` 自动生成的包元数据目录。

`.env.example` 和 `alembic.ini` 不是用来生成 `egg-info` 的，它们分别服务于运行时配置和数据库迁移。

这个项目没有 `requirements.txt`，是因为它采用了现代 Python 项目更推荐的 `pyproject.toml` 来声明依赖。

## 这几个文件的关系图

```mermaid
flowchart TD
    A["pyproject.toml"] --> B["pip install -e . / build / egg_info"]
    B --> C["src/enterprise_ai_app.egg-info/"]
    A --> D["依赖声明 dependencies"]
    D --> E["egg-info/requires.txt"]
    A --> F["项目元信息 name/version/readme"]
    F --> G["egg-info/PKG-INFO"]
    H[".env.example"] --> I["复制成 .env"]
    I --> J["app.core.config.Settings 运行时读取"]
    K["alembic.ini"] --> L["alembic 命令读取迁移配置"]
    J --> L
```

图里最关键的是：

- `pyproject.toml -> egg-info` 是直接生成关系。
- `.env.example -> .env -> Settings` 是运行时配置关系。
- `alembic.ini -> Alembic` 是数据库迁移工具配置关系。
- `.env.example` 和 `alembic.ini` 不会直接生成 `enterprise_ai_app.egg-info`。

## enterprise_ai_app.egg-info 是什么

目录位置：

```text
src/enterprise_ai_app.egg-info/
```

它是 Python 打包工具自动生成的元数据目录。常见触发命令包括：

```bash
pip install -e .
pip install .
python -m build
python setup.py egg_info
```

这个项目的包名在 `pyproject.toml` 中是：

```toml
[project]
name = "enterprise-ai-app"
```

生成目录时，打包工具会把项目名规范化：连字符 `-` 变成下划线 `_`，所以生成：

```text
enterprise_ai_app.egg-info
```

这个目录里当前有：

```text
PKG-INFO
SOURCES.txt
requires.txt
top_level.txt
dependency_links.txt
```

它们的含义是：

| 文件 | 作用 | 主要来自哪里 |
| --- | --- | --- |
| `PKG-INFO` | 包元信息，比如名称、版本、作者、依赖、README 内容 | `pyproject.toml` + `README.md` |
| `requires.txt` | 安装依赖列表 | `pyproject.toml` 的 `dependencies` 和 `optional-dependencies` |
| `SOURCES.txt` | 打包时发现的源文件列表 | setuptools 扫描结果 |
| `top_level.txt` | 顶层 Python 包名，这里是 `app` | `src/app` |
| `dependency_links.txt` | 旧式依赖链接字段，通常为空 | setuptools 兼容产物 |

所以 `egg-info` 不是业务代码，也不是配置源头。它更像是“打包工具生成出来的说明书和清单”。

## pyproject.toml 的作用

文件位置：

```text
pyproject.toml
```

它是这个项目最核心的 Python 项目配置文件，主要有四类作用。

### 1. 声明构建系统

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"
```

这告诉 `pip`：构建/安装这个项目时，用 `setuptools` 作为构建后端。

当你执行：

```bash
pip install -e .
```

`pip` 会读 `pyproject.toml`，知道应该调用 `setuptools` 来生成包元数据，于是产生 `src/enterprise_ai_app.egg-info/`。

### 2. 声明项目元信息

```toml
[project]
name = "enterprise-ai-app"
version = "0.1.0"
description = "企业级生成式AI应用Web服务框架"
readme = "README.md"
requires-python = ">=3.11"
```

这些内容会进入 `egg-info/PKG-INFO`。

比如你当前的 `PKG-INFO` 里能看到：

```text
Name: enterprise-ai-app
Version: 0.1.0
Summary: 企业级生成式AI应用Web服务框架
Requires-Python: >=3.11
```

这说明 `egg-info` 确实是由 `pyproject.toml` 派生出来的。

### 3. 声明依赖

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pydantic>=2.0",
    ...
]
```

这些内容会进入：

```text
src/enterprise_ai_app.egg-info/requires.txt
```

所以这里的 `dependencies` 就承担了过去很多项目里 `requirements.txt` 的基础职责：声明项目运行需要安装哪些包。

### 4. 声明工具配置

这个文件还放了测试和 lint 配置：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-s"

[tool.ruff]
line-length = 100
target-version = "py311"
```

这些配置不会主要影响 `egg-info`，但会影响本地测试、代码检查工具怎么运行。

## .env.example 的作用

文件位置：

```text
.env.example
```

它是环境变量模板。它不会被 Python 打包工具读取，也不会生成 `egg-info`。

它的用途是告诉开发者：“你本地需要准备哪些环境变量”。通常用法是：

```bash
cp .env.example .env
```

然后在 `.env` 里填入真实值，比如：

```env
APP_LLM_API_KEY=<your-api-key>
APP_DATABASE_URL=mysql+aiomysql://user:pass@localhost:2881/your_db
APP_SECRET_KEY=<your-secret-key>
```

项目运行时，配置类会读取 `.env`：

```python
model_config = SettingsConfigDict(
    env_prefix="APP_",
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)
```

这说明：

- 代码使用 `APP_` 作为环境变量前缀。
- `.env` 是实际运行时读取的文件。
- `.env.example` 只是模板，通常不包含真实密钥。

`.env.example` 里的变量会对应到 `Settings` 类里的字段。比如：

| `.env.example` 变量 | `Settings` 字段 | 用途 |
| --- | --- | --- |
| `APP_ENV` | `env` | 运行环境 |
| `APP_LOG_LEVEL` | `log_level` | 日志级别 |
| `APP_DATABASE_URL` | `database_url` | 数据库连接串 |
| `APP_LLM_API_KEY` | `llm_api_key` | 阿里云/通义调用密钥 |
| `APP_LLM_PROVIDER` | `llm_provider` | LLM provider |
| `APP_DATA_OUTPUT_DIR` | `data_output_dir` | 文件输出目录 |
| `APP_PORT` | `port` | 服务端口 |

它和 `egg-info` 的关系很弱：`egg-info` 是安装/打包元数据，`.env.example` 是运行时配置模板。

## alembic.ini 的作用

文件位置：

```text
alembic.ini
```

它是 Alembic 数据库迁移工具的配置文件。Alembic 用来管理数据库表结构变更，比如生成迁移脚本、执行升级/回滚。

这个文件里最关键的是：

```ini
[alembic]
script_location = src/app/db/migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = driver://user:pass@localhost/dbname
```

含义是：

- `script_location`：迁移脚本目录在 `src/app/db/migrations`。
- `prepend_sys_path = .`：运行 alembic 时，把项目根目录加入 Python 路径。
- `sqlalchemy.url`：占位连接串。

注意这里的 `sqlalchemy.url` 是占位值。项目真正的数据库连接串来自 `Settings.database_url`。

在 `src/app/db/migrations/env.py` 里可以看到：

```python
def get_url() -> str:
    return get_settings().database_url
```

在线迁移时又会覆盖配置：

```python
configuration = config.get_section(config.config_ini_section, {})
configuration["sqlalchemy.url"] = get_url()
```

所以实际迁移连接串来自：

```text
APP_DATABASE_URL -> .env / 环境变量 -> Settings.database_url -> Alembic env.py
```

`alembic.ini` 负责告诉 Alembic 去哪里找迁移目录、怎么配置日志；`.env` 负责提供真实数据库 URL。

## 这三个文件和 egg-info 的关系

### pyproject.toml 和 egg-info

这是直接关系。

```text
pyproject.toml -> setuptools/pip -> src/enterprise_ai_app.egg-info/
```

比如：

- `name = "enterprise-ai-app"` 生成 `Name: enterprise-ai-app`。
- `version = "0.1.0"` 生成 `Version: 0.1.0`。
- `dependencies = [...]` 生成 `requires.txt`。
- `readme = "README.md"` 让 `PKG-INFO` 包含 README 内容。

### .env.example 和 egg-info

基本没有直接关系。

`.env.example` 不参与依赖安装，不参与包元数据生成。它只是给开发者复制成 `.env` 的模板。

### alembic.ini 和 egg-info

也基本没有直接关系。

`alembic.ini` 是数据库迁移命令运行时读的配置。它不负责 Python 包安装，也不生成 `egg-info`。

不过它和 `pyproject.toml` 有一个间接关系：`pyproject.toml` 里声明了依赖：

```toml
"alembic>=1.13"
```

所以安装项目依赖后，才会有 `alembic` 这个迁移工具可用。

## 为什么没有 requirements.txt

很多老项目会用：

```text
requirements.txt
```

来写依赖：

```text
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
pydantic>=2.0
```

但这个项目使用的是现代 Python 打包规范，也就是 `pyproject.toml`：

```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    ...
]
```

因此安装方式是：

```bash
pip install -e .
```

如果还要安装开发依赖：

```bash
pip install -e ".[dev]"
```

其中 `[dev]` 来自：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
]
```

所以没有 `requirements.txt` 并不是遗漏，而是项目把依赖统一放在了 `pyproject.toml` 里。

## pyproject.toml 里的 dependency 能不能指定具体版本

可以。`pyproject.toml` 里的 `dependencies` 完全可以指定具体版本。

我前面举的：

```toml
"fastapi>=0.115.0"
```

只是“最低版本约束”，不是说只能这么写。

Python 包版本约束常见写法包括：

| 写法 | 含义 | 示例 |
| --- | --- | --- |
| `==` | 精确固定某个版本 | `fastapi==0.115.6` |
| `>=` | 大于等于某个版本 | `fastapi>=0.115.0` |
| `<=` | 小于等于某个版本 | `pydantic<=2.10.0` |
| `<` | 小于某个版本 | `sqlalchemy<3.0` |
| `~=` | 兼容版本 | `requests~=2.31` |
| `!=` | 排除某个坏版本 | `somepkg!=1.2.3` |
| 组合约束 | 控制版本区间 | `fastapi>=0.115.0,<0.116.0` |

所以你完全可以在 `pyproject.toml` 里写：

```toml
dependencies = [
    "fastapi==0.115.6",
    "uvicorn[standard]==0.32.1",
    "pydantic>=2.8,<3.0",
]
```

区别在于策略：

- `>=` 比较灵活，安装时会选择满足条件的新版本，适合库项目或课程 demo，但可能受到上游新版本变化影响。
- `==` 更稳定，安装结果可重复性更强，适合生产部署，但也更容易和其他依赖发生版本冲突。
- `>=,<` 是常见折中，既允许补丁/小版本升级，又避免跨大版本破坏兼容。

如果要非常严格地锁定整个环境，现代项目通常还会额外使用 lock 文件，例如 `uv.lock`、`poetry.lock`、`pdm.lock`，或者通过 `pip-tools` 生成带完整传递依赖版本的 `requirements.txt`。

注意：`pyproject.toml` 里的 `dependencies` 一般只写“直接依赖”。比如项目直接用到了 FastAPI、CrewAI、SQLAlchemy，就写进去。它们内部依赖的包属于传递依赖，通常不手写，交给包管理工具解析。

## requirements.txt 和 pyproject.toml 的区别

| 文件 | 主要用途 | 是否描述项目本身 | 是否现代标准 |
| --- | --- | --- | --- |
| `requirements.txt` | 安装一组依赖包 | 不完整描述项目元信息 | 传统方式 |
| `pyproject.toml` | 描述项目、构建系统、依赖、工具配置 | 是 | 现代标准 |

`requirements.txt` 更像“环境安装清单”。

`pyproject.toml` 更像“项目身份证 + 构建说明 + 依赖声明 + 工具配置”。

## 那 requirements.txt 什么时候还会有用

即使用了 `pyproject.toml`，有些项目仍然会额外保留 `requirements.txt`。常见原因是：

- 部署平台只支持或默认寻找 `requirements.txt`。
- 想把依赖版本完全锁死，比如 `fastapi==0.115.6`。
- 想区分运行依赖、开发依赖、生产部署依赖。
- 和 Docker、CI/CD、老工具链兼容。

但如果项目已经用：

```bash
pip install -e ".[dev]"
```

安装依赖，那么不需要再单独维护 `requirements.txt`。

## 这个项目启动/安装时各文件的典型参与顺序

### 安装依赖

```bash
pip install -e ".[dev]"
```

参与文件：

```text
pyproject.toml -> 生成/更新 egg-info -> 安装 dependencies 和 dev dependencies
```

### 配置运行环境

```bash
cp .env.example .env
```

参与文件：

```text
.env.example -> .env -> app.core.config.Settings -> 应用运行配置
```

### 运行数据库迁移

```bash
alembic upgrade head
```

参与文件：

```text
alembic.ini -> src/app/db/migrations/env.py -> Settings.database_url -> 数据库
```

其中 Alembic 本身这个工具的安装，来自 `pyproject.toml` 里的：

```toml
"alembic>=1.13"
```

## 更详细的 Alembic 使用方法

Alembic 是 SQLAlchemy 生态里的数据库迁移工具。它解决的问题是：

```text
代码里的 ORM 模型变了，数据库表结构怎么有记录、有顺序、可升级、可回滚地同步变化？
```

它不是业务查询工具，也不是 ORM 本身。它只负责数据库 schema 变更，比如：

- 创建表。
- 增加字段。
- 删除字段。
- 修改索引。
- 增加唯一约束。
- 回滚上一版表结构。

### 1. Alembic 配置入口

项目根目录下的：

```text
alembic.ini
```

是命令行入口配置。执行：

```bash
alembic upgrade head
```

时，Alembic 默认会在当前目录寻找 `alembic.ini`。

这个项目的关键配置是：

```ini
[alembic]
script_location = src/app/db/migrations
prepend_sys_path = .
version_path_separator = os

sqlalchemy.url = driver://user:pass@localhost/dbname
```

其中：

- `script_location = src/app/db/migrations`：告诉 Alembic 迁移环境和迁移脚本目录在哪里。
- `prepend_sys_path = .`：把项目根目录加入 Python import 路径，方便导入 `app`。
- `sqlalchemy.url`：这里只是占位值，不是这个项目实际使用的数据库 URL。

### 2. env.py 才是真正执行迁移逻辑的地方

Alembic 找到 `script_location` 后，会加载：

```text
src/app/db/migrations/env.py
```

这个文件负责：

1. 把 `src` 加入 `sys.path`，确保能导入 `app`。
2. 导入项目配置 `get_settings()`。
3. 导入 SQLAlchemy 的 `Base.metadata`。
4. 根据 `.env` / 环境变量里的数据库连接串创建 async engine。
5. 执行迁移。

关键代码：

```python
from app.core.config import get_settings
from app.db.models.base import Base

target_metadata = Base.metadata

def get_url() -> str:
    return get_settings().database_url
```

`target_metadata = Base.metadata` 很重要。它是 Alembic 自动生成迁移时用来对比模型和数据库差异的依据。

在线迁移时，项目会覆盖 `alembic.ini` 里的占位 URL：

```python
configuration = config.get_section(config.config_ini_section, {})
configuration["sqlalchemy.url"] = get_url()
```

所以真实链路是：

```text
.env / 环境变量里的 APP_DATABASE_URL
  -> app.core.config.Settings.database_url
  -> migrations/env.py 的 get_url()
  -> Alembic async_engine_from_config()
  -> 连接数据库执行迁移
```

### 3. script.py.mako 是迁移脚本模板

目录里还有：

```text
src/app/db/migrations/script.py.mako
```

它不是一次具体迁移，而是“以后生成具体迁移文件时用的模板”。

执行类似命令：

```bash
alembic revision -m "create users table"
```

Alembic 会根据 `script.py.mako` 生成一个 revision 文件，里面通常有：

```python
revision = "xxxx"
down_revision = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

如果使用自动生成：

```bash
alembic revision --autogenerate -m "create users table"
```

Alembic 会对比：

```text
当前数据库结构 vs Base.metadata 中声明的 ORM 模型
```

然后尽量自动填充 `upgrade()` 和 `downgrade()`。

### 4. 常用命令

#### 查看当前数据库迁移版本

```bash
alembic current
```

它会连接数据库，查看当前数据库记录的 revision。

#### 查看迁移历史

```bash
alembic history
```

它会列出迁移脚本历史。

#### 生成空迁移脚本

```bash
alembic revision -m "your migration message"
```

适合手写 SQLAlchemy 操作：

```python
def upgrade() -> None:
    op.create_table(...)

def downgrade() -> None:
    op.drop_table(...)
```

#### 根据模型变更自动生成迁移

```bash
alembic revision --autogenerate -m "add report table"
```

前提是：

- 项目里有具体 SQLAlchemy model。
- model 继承自同一个 `Base`。
- `env.py` 能 import 到这些 model，让它们注册进 `Base.metadata`。
- 数据库可连接。

#### 执行升级到最新版

```bash
alembic upgrade head
```

`head` 表示最新迁移版本。

#### 回滚一个版本

```bash
alembic downgrade -1
```

#### 生成 SQL 文件但不直接执行

```bash
alembic upgrade head --sql
```

这会输出 SQL，适合生产环境由 DBA 审核后再执行。

### 5. 这个项目目前有没有迁移脚本或者 SQL

按当前仓库内容看：**没有实际数据库迁移 revision 脚本，也没有对应业务表 SQL。**

当前 `src/app/db/migrations` 目录只有：

```text
src/app/db/migrations/env.py
src/app/db/migrations/script.py.mako
```

没有常见的：

```text
src/app/db/migrations/versions/
```

也没有类似：

```text
src/app/db/migrations/versions/20260528_xxx_create_table.py
```

这说明项目现在只是搭好了 Alembic 迁移框架，还没有生成任何实际迁移版本。

再看模型层：

```text
src/app/db/models/base.py
src/app/db/models/__init__.py
```

`base.py` 里目前只有：

```python
class Base(DeclarativeBase):
    pass

class TimestampMixin:
    ...
```

也就是只有 SQLAlchemy 声明式基类和时间戳 mixin，没有具体业务表模型，例如 `Report`、`User`、`ApiKey` 之类的 ORM class。

因此目前即使运行：

```bash
alembic revision --autogenerate -m "init"
```

大概率也不会生成有意义的建表操作，因为 `Base.metadata` 里没有具体表。

### 6. 那 oceanbase_client.py 里的 init_db 是什么

项目里还有：

```python
async def init_db() -> None:
    """初始化表结构（开发/测试用；生产建议用 Alembic 迁移）。"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

这是 SQLAlchemy 的直接建表方式：

```text
Base.metadata.create_all()
```

它和 Alembic 的区别是：

| 方式 | 适合场景 | 特点 |
| --- | --- | --- |
| `Base.metadata.create_all()` | 本地开发、测试、demo | 直接按当前模型创建缺失表，不记录版本，不擅长演进 |
| Alembic migration | 生产、多人协作、可回滚发布 | 每次 schema 变化都有 revision，可升级、可回滚、可审计 |

所以代码注释说“开发/测试用；生产建议用 Alembic 迁移”是合理的。

不过由于当前项目没有具体 ORM 表模型，`create_all()` 目前也不会创建业务表。

### 7. 如果以后要真正加数据库表，流程应该是什么

假设要保存小红书报告，可以新增一个模型：

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base, TimestampMixin, gen_uuid


class XhsNoteReport(Base, TimestampMixin):
    __tablename__ = "xhs_note_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    idea_text: Mapped[str] = mapped_column(Text, nullable=False)
    report: Mapped[str] = mapped_column(Text, nullable=False)
```

然后确保 `env.py` 能 import 到这个模型。常见做法是在 `src/app/db/models/__init__.py` 里导入它：

```python
from app.db.models.xhs_note_report import XhsNoteReport
```

再执行：

```bash
alembic revision --autogenerate -m "create xhs note reports"
```

生成迁移脚本后，检查 `upgrade()` 和 `downgrade()`，确认没问题再执行：

```bash
alembic upgrade head
```

这样数据库里才会真正出现表。

## 最后的心智模型

可以这样记：

```text
pyproject.toml：告诉 Python 工具“这个项目是什么、怎么安装、依赖什么”。
.env.example：告诉开发者“运行这个项目需要哪些环境变量”。
alembic.ini：告诉 Alembic“数据库迁移脚本在哪里、迁移命令怎么运行”。
enterprise_ai_app.egg-info：pip/setuptools 根据 pyproject.toml 生成的安装元数据。
requirements.txt：本项目没有，因为依赖已经由 pyproject.toml 管理。
```

所以这几个文件不是同一层的东西：

- `pyproject.toml` 是项目/包层。
- `.env.example` 是运行配置层。
- `alembic.ini` 是数据库迁移工具层。
- `egg-info` 是安装后生成的元数据产物。
