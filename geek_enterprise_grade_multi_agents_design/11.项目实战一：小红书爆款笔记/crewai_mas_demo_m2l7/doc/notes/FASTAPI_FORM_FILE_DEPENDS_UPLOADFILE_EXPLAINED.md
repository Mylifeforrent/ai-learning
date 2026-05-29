# FastAPI Form、File、UploadFile、Depends 参数说明

## 项目里的代码

`src/app/api/v1/xhs_note.py` 中的接口参数如下：

```python
async def create_xhs_note_report(
    idea_text: str = Form(..., description="笔记创作意图 / 思路"),
    images: List[UploadFile] = File(
        ..., description="多张图片，同一字段名 images 下上传多文件"
    ),
    request_id: str = Depends(get_request_id),
    _api_key: str = Depends(require_api_key),
) -> ApiResponse[XhsNoteReportResponse]:
```

这段代码是 FastAPI 的接口参数声明。它不只是普通的 Python 函数参数，还告诉 FastAPI：

```text
idea_text 从表单字段里取
images 从上传文件里取
request_id 通过依赖函数 get_request_id 生成或读取
_api_key 通过依赖函数 require_api_key 校验
返回值结构是 ApiResponse[XhsNoteReportResponse]
```

这个接口接收的是 `multipart/form-data` 请求，适合同时上传普通文本字段和文件。

## 它们都是 class 吗

不是。

在当前项目环境的 FastAPI 版本中：

```text
Form       是函数，调用 Form(...) 后返回 fastapi.params.Form 对象
File       是函数，调用 File(...) 后返回 fastapi.params.File 对象
Depends    是函数，调用 Depends(...) 后返回 fastapi.params.Depends 对象
UploadFile 是类，用来表示上传文件
```

所以更准确的理解是：

```text
Form / File / Depends 是 FastAPI 提供的参数声明函数
UploadFile 是上传文件对象的类型
```

它们放在函数签名里，FastAPI 启动时会读取这些声明，然后自动完成请求解析、校验、依赖执行和接口文档生成。

## idea_text: str = Form(...)

```python
idea_text: str = Form(..., description="笔记创作意图 / 思路")
```

这行的含义是：

```text
参数名：idea_text
参数类型：str
数据来源：表单字段
是否必填：必填
接口文档描述：笔记创作意图 / 思路
```

`Form(...)` 表示这个参数不是从 JSON 请求体里取，也不是从 URL query 参数里取，而是从表单数据里取。

例如调用接口时，表单里要有：

```text
idea_text=想写一篇关于咖啡店探店的小红书笔记
```

`Form(...)` 里的 `...` 是 Python 的 `Ellipsis`。在 FastAPI 里，它通常表示：

```text
这个字段是必填字段
```

如果请求里没有传 `idea_text`，FastAPI 会在进入业务函数之前直接返回参数校验错误。

## images: List[UploadFile] = File(...)

```python
images: List[UploadFile] = File(
    ..., description="多张图片，同一字段名 images 下上传多文件"
)
```

这行的含义是：

```text
参数名：images
参数类型：List[UploadFile]
数据来源：上传文件字段
是否必填：必填
字段名：images
允许数量：多个文件
```

`File(...)` 表示这个参数来自文件上传字段。

`UploadFile` 是 FastAPI 用来表示上传文件的类。每个上传文件都会被包装成一个 `UploadFile` 对象，常用属性和方法包括：

```python
file.filename      # 原始文件名
file.content_type  # 文件 MIME 类型，例如 image/jpeg
await file.read()  # 异步读取文件内容
```

因为这里写的是：

```python
List[UploadFile]
```

所以 `images` 不是单个文件，而是多个文件组成的列表。

请求方需要用同一个字段名 `images` 上传多张图片，例如表单结构类似：

```text
idea_text: 一篇关于咖啡店探店的小红书笔记
images: 1.jpg
images: 2.jpg
images: 3.jpg
```

也就是说，多文件上传不是写成 `images1`、`images2`、`images3`，而是同一个字段名重复多次。

## request_id: str = Depends(get_request_id)

```python
request_id: str = Depends(get_request_id)
```

这行的含义是：

```text
参数名：request_id
参数类型：str
数据来源：依赖函数 get_request_id 的返回值
```

`Depends(...)` 是 FastAPI 的依赖注入机制。

它告诉 FastAPI：

```text
在执行 create_xhs_note_report 之前，
先执行 get_request_id，
然后把 get_request_id 的返回值传给 request_id。
```

项目里的 `get_request_id` 定义在 `src/app/api/dependencies.py`：

```python
async def get_request_id(request: Request) -> str:
    """从请求头获取或生成 request_id，并注入上下文。"""
    rid = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(rid)
    return rid
```

它的逻辑是：

```text
如果请求头里有 X-Request-ID，就使用它
如果没有，就生成一个新的 UUID
把 request_id 写入日志上下文
最后返回 request_id
```

所以在业务函数里可以直接使用：

```python
logger.exception("xhs_note_api_failed", error=str(exc), request_id=request_id)
```

不用在每个接口里重复写“从请求头取 request id”的代码。

## _api_key: str = Depends(require_api_key)

```python
_api_key: str = Depends(require_api_key)
```

这行也是依赖注入。

它告诉 FastAPI：

```text
在进入业务函数之前，先执行 require_api_key。
```

项目里的 `require_api_key` 实际上来自：

```python
require_api_key = verify_api_key
```

也就是说，它复用了 `src/app/core/security.py` 里的 API Key 校验逻辑。

这个参数名前面有下划线：

```python
_api_key
```

通常表示：

```text
这个值主要是为了触发依赖执行，业务代码里不会直接使用它。
```

也就是说，这个接口关心的不是 `_api_key` 这个字符串本身，而是：

```text
如果 API Key 不合法，就不要继续执行接口逻辑。
```

如果校验失败，`require_api_key` 会提前抛出异常，业务函数 `create_xhs_note_report` 不会继续执行。

## 为什么不用普通参数

如果写成普通参数：

```python
async def create_xhs_note_report(
    idea_text: str,
    images: List[UploadFile],
):
```

FastAPI 不一定能准确知道：

```text
idea_text 应该来自 form-data
images 应该来自文件上传
这个接口需要鉴权
这个接口需要 request_id
```

所以这里通过 `Form`、`File`、`Depends` 明确告诉 FastAPI 参数来源和处理方式。

## 整体执行过程

当请求进入这个接口时，大致流程是：

```text
1. FastAPI 解析 multipart/form-data 请求。
2. 从表单字段中读取 idea_text。
3. 从文件字段 images 中读取多张图片，包装成 List[UploadFile]。
4. 执行 get_request_id，得到 request_id。
5. 执行 require_api_key，完成 API Key 校验。
6. 参数都准备好后，调用 create_xhs_note_report。
7. 函数内部调用 generate_xhs_note_report 生成报告。
8. 最后返回 ApiResponse[XhsNoteReportResponse]。
```

## 一个类比

可以把函数签名看成接口的“入参说明书”：

```python
idea_text: str = Form(...)
```

表示：

```text
请从表单里拿一个必填文本字段，名字叫 idea_text。
```

```python
images: List[UploadFile] = File(...)
```

表示：

```text
请从上传文件里拿一组必填文件，字段名叫 images。
```

```python
request_id: str = Depends(get_request_id)
```

表示：

```text
请先运行 get_request_id，把结果放到 request_id。
```

```python
_api_key: str = Depends(require_api_key)
```

表示：

```text
请先运行 require_api_key，确保请求有权限。
```

## 小结

这几个参数的核心作用如下：

| 写法 | 它是什么 | 作用 |
| --- | --- | --- |
| `Form(...)` | 参数声明函数 | 声明字段来自表单数据 |
| `File(...)` | 参数声明函数 | 声明字段来自上传文件 |
| `UploadFile` | 类 | 表示一个上传文件对象 |
| `Depends(...)` | 参数声明函数 | 声明这个参数来自依赖函数的返回值 |
| `...` | Python 的 Ellipsis | 在 FastAPI 参数里通常表示必填 |
| `description=...` | 文档描述 | 用于生成 OpenAPI / Swagger 接口文档 |

这段接口代码的重点是：

```text
它通过函数签名同时声明了请求格式、文件上传、依赖注入、鉴权和响应类型。
```
