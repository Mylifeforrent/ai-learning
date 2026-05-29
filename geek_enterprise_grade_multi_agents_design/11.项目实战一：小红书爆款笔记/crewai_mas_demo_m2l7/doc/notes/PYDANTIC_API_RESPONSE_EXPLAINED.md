# Pydantic 通用 API 响应模型说明

## 项目里的代码

`src/app/schemas/common.py` 中定义了统一响应模型：

```python
T = TypeVar("T")


class ErrorDetail(BaseModel):
    """统一错误响应体。"""

    code: int = Field(..., description="业务/HTTP 错误码")
    message: str = Field(..., description="可展示给用户的信息")
    request_id: str = Field("", description="便于日志关联的请求 ID")


class ApiResponse(BaseModel, Generic[T]):
    """统一成功响应体。"""

    code: int = Field(0, description="0 表示成功")
    message: str = Field("ok", description="提示信息")
    data: T | None = Field(None, description="业务数据")
    request_id: str = Field("", description="请求 ID")
```

这段代码的作用是定义项目统一的 API 响应格式：

```text
成功响应：ApiResponse[T]
错误响应：ErrorDetail
```

这样不同接口不会各自返回不同结构，前端、调用方和测试代码都可以按统一格式处理。

## T = TypeVar("T")

```python
T = TypeVar("T")
```

`TypeVar` 来自 Python 的 `typing` 模块，用来定义泛型类型变量。

这里的 `T` 表示：

> 具体业务数据的类型先不固定，等使用 `ApiResponse` 时再指定。

例如：

```python
ApiResponse[dict]
ApiResponse[list[str]]
ApiResponse[XhsNoteReportResponse]
```

这样 `ApiResponse` 的 `data` 字段就可以根据不同接口变化。

如果不用泛型，也可以写成：

```python
data: Any | None
```

但这样类型信息会比较弱，编辑器、类型检查器和接口文档都不容易知道 `data` 里面到底是什么。

## class ErrorDetail(BaseModel)

```python
class ErrorDetail(BaseModel):
```

这行定义错误响应模型。

`BaseModel` 来自 Pydantic。继承 `BaseModel` 后，这个类就具备了几个能力：

```text
字段类型声明
数据校验
默认值处理
序列化为 dict/json
生成 OpenAPI/Swagger 文档 schema
```

这个模型通常用于异常处理器，例如全局异常返回：

```json
{
  "code": 500,
  "message": "Internal server error",
  "request_id": "abc-123"
}
```

## ErrorDetail.code

```python
code: int = Field(..., description="业务/HTTP 错误码")
```

含义：

```text
字段名：code
字段类型：int
是否必填：必填
文档描述：业务/HTTP 错误码
```

`Field(...)` 里的 `...` 是 Python 的 Ellipsis，在 Pydantic 里表示这个字段没有默认值，创建对象时必须传。

例如下面这样可以：

```python
ErrorDetail(code=500, message="Internal server error")
```

但下面这样不可以，因为缺少必填字段：

```python
ErrorDetail(message="Internal server error")
```

## ErrorDetail.message

```python
message: str = Field(..., description="可展示给用户的信息")
```

含义：

```text
字段名：message
字段类型：str
是否必填：必填
作用：返回错误说明
```

例如：

```json
{
  "message": "API key is invalid"
}
```

这个字段通常可以展示给调用方或前端，用来说明失败原因。

## ErrorDetail.request_id

```python
request_id: str = Field("", description="便于日志关联的请求 ID")
```

含义：

```text
字段名：request_id
字段类型：str
默认值：""
作用：关联服务端日志
```

当接口报错时，客户端可以把 `request_id` 发给后端排查。后端就可以在日志里搜索同一个 `request_id`，找到对应请求的完整日志链路。

## class ApiResponse(BaseModel, Generic[T])

```python
class ApiResponse(BaseModel, Generic[T]):
```

这行定义统一成功响应模型。

它同时继承：

```text
BaseModel  -> 获得 Pydantic 数据模型能力。
Generic[T] -> 表示这是一个泛型模型，里面会用到类型变量 T。
```

所以 `ApiResponse` 可以表达不同业务接口的响应：

```python
ApiResponse[dict]
ApiResponse[XhsNoteReportResponse]
ApiResponse[list[UserInfo]]
```

## ApiResponse.code

```python
code: int = Field(0, description="0 表示成功")
```

含义：

```text
字段名：code
字段类型：int
默认值：0
作用：表示业务处理结果
```

项目里约定：

```text
code = 0   表示成功
code != 0 可能表示业务失败
```

注意：这个 `code` 是响应体里的业务码，不一定等同于 HTTP 状态码。

例如 HTTP 状态码可能是 `200`，但响应体里：

```json
{
  "code": 1,
  "message": "小红书笔记生成失败"
}
```

表示 HTTP 请求成功到达服务，但业务处理失败。

## ApiResponse.message

```python
message: str = Field("ok", description="提示信息")
```

含义：

```text
字段名：message
字段类型：str
默认值："ok"
作用：返回提示信息
```

成功时一般是：

```json
{
  "message": "ok"
}
```

业务失败时也可以放具体原因。

## ApiResponse.data

```python
data: T | None = Field(None, description="业务数据")
```

含义：

```text
字段名：data
字段类型：T 或 None
默认值：None
作用：承载具体业务结果
```

这里的 `T` 就是前面定义的泛型变量。

例如接口声明：

```python
response_model=ApiResponse[XhsNoteReportResponse]
```

那么可以理解为：

```python
data: XhsNoteReportResponse | None
```

如果接口声明：

```python
response_model=ApiResponse[dict]
```

那么可以理解为：

```python
data: dict | None
```

`| None` 表示业务数据可以为空。比如创建失败、暂无数据、或者某些只返回状态的接口，可以让 `data` 为 `null`。

## ApiResponse.request_id

```python
request_id: str = Field("", description="请求 ID")
```

含义：

```text
字段名：request_id
字段类型：str
默认值：""
作用：关联请求日志
```

它和 `ErrorDetail.request_id` 的作用类似：让调用方能用响应里的 `request_id` 去服务端日志中定位这次请求。

## Field 的作用

`Field` 来自 Pydantic：

```python
from pydantic import Field
```

它不是用来表示“字段值本身”的普通变量，而是用来给 Pydantic 模型字段声明额外配置。

在 Pydantic v2 中，`Field` 可以理解成一个工厂函数。它本身不是我们直接继承使用的普通 class；调用 `Field(...)` 后，会返回一个字段信息对象，Pydantic 在创建 `BaseModel` 子类时会读取这个对象，知道这个字段的默认值、是否必填、文档描述、校验规则等信息。

也就是说：

```python
message: str = Field("ok", description="提示信息")
```

不要理解成：

```text
message 这个字段的值是 Field 对象
```

而应该理解成：

```text
message 是一个 str 类型字段；
默认值是 "ok"；
OpenAPI/Swagger 文档里的字段说明是 "提示信息"。
```

Pydantic 会在类定义阶段读取 `Field("ok", description="提示信息")` 里的元信息，然后把 `message` 注册成模型字段。真正创建模型实例时，`message` 的值会是字符串 `"ok"`，不是 `Field` 对象。

例如：

```python
resp = ApiResponse()
print(resp.message)
```

输出会是：

```text
ok
```

而不是：

```text
Field(...)
```

`Field` 常用于给模型字段添加这些信息：

```text
默认值
是否必填
描述信息
校验规则
示例
别名
```

当前代码主要用了两类：

```python
Field(...)
```

表示必填。这里的 `...` 是 Python 的 Ellipsis，Pydantic 会把它理解为“没有默认值，创建对象时必须传入”。

```python
Field("ok", description="提示信息")
```

表示默认值是 `"ok"`，并给 OpenAPI 文档添加字段描述。

也可以把它和普通默认值对比：

```python
message: str = "ok"
```

这也能表示默认值是 `"ok"`，但不能额外提供 Swagger 文档描述、校验规则、示例、别名等信息。

使用 `Field` 后可以写成：

```python
message: str = Field(
    "ok",
    description="提示信息",
)
```

如果需要更多约束，也可以继续扩展，比如：

```python
name: str = Field(
    ...,
    min_length=1,
    max_length=50,
    description="用户名",
)
```

这表示：

```text
name 是必填字符串；
长度至少 1；
长度最多 50；
Swagger 文档说明是“用户名”。
```

这些 `description` 会出现在 FastAPI 自动生成的 Swagger 文档里。

## 成功响应示例

以小红书报告接口为例，成功时可能返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "report": "..."
  },
  "request_id": "8f0b8a0b-7e9a-4f0d-9c72-123456789abc"
}
```

这里的 `data` 类型由接口的 `response_model` 决定。

## 错误响应示例

发生未处理异常时，项目里的全局异常处理器会返回类似：

```json
{
  "code": 500,
  "message": "Internal server error",
  "request_id": "8f0b8a0b-7e9a-4f0d-9c72-123456789abc"
}
```

这个结构对应 `ErrorDetail`。

## 为什么要统一响应体

统一响应体的好处是：

```text
前端处理更简单：固定读 code/message/data/request_id。
接口文档更稳定：所有接口结构一致。
排查问题更方便：每个响应都带 request_id。
业务错误和 HTTP 错误可以有清晰区分。
测试断言更统一：测试代码可以按同一结构校验。
```

## 最后总结

这段代码的核心作用是定义项目 API 的统一返回契约：

```text
ErrorDetail
  -> 用于错误响应，包含 code、message、request_id。

ApiResponse[T]
  -> 用于成功或业务响应，包含 code、message、data、request_id。

T
  -> 表示 data 的泛型类型，让不同接口可以返回不同业务数据。

Field
  -> 定义默认值、必填规则和 Swagger 文档描述。
```

一句话理解：

> `ApiResponse[T]` 负责统一“成功响应长什么样”，`ErrorDetail` 负责统一“错误响应长什么样”，`T` 让 `data` 可以跟随不同接口变成不同类型。
