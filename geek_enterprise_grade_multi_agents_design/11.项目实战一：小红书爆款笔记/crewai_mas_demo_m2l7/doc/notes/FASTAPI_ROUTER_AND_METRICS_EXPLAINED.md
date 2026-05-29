# FastAPI 路由挂载与 metrics 暴露说明

## 项目里的三行代码

在 `src/app/main.py` 的 `create_application()` 里有这三行：

```python
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(api_router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

它们分别做三件事：

```text
1. 挂载健康检查路由。
2. 挂载业务 API 路由。
3. 给 FastAPI 应用接入 Prometheus 指标采集，并暴露 /metrics 接口。
```

## app.include_router 是什么

FastAPI 里的 `APIRouter` 可以理解成“一组路由的集合”。

小项目可以把所有接口都直接写在 `app` 上：

```python
@app.get("/hello")
async def hello():
    ...
```

但项目变大后，更常见的做法是按模块拆成多个 router：

```text
health.router   -> 健康检查接口
api_router      -> 业务接口聚合
xhs_note.router -> 小红书业务接口
```

然后在应用入口统一挂载：

```python
app.include_router(...)
```

这样 `main.py` 不需要直接写所有接口，只负责组装应用。

## 第一行：挂载健康检查路由

代码：

```python
app.include_router(health.router, prefix="/health", tags=["health"])
```

`health.router` 定义在：

```text
src/app/api/v1/health.py
```

里面有两个接口：

```python
@router.get("/live")
async def liveness():
    ...

@router.get("/ready")
async def readiness():
    ...
```

挂载时加了：

```python
prefix="/health"
```

所以最终路径会变成：

```text
GET /health/live
GET /health/ready
```

`tags=["health"]` 主要用于 OpenAPI/Swagger 文档分组。访问 `/docs` 时，这两个接口会被归到 `health` 分组下。

这两个接口通常给 Kubernetes、负载均衡器或运维监控使用：

```text
/health/live  : 进程是否还活着
/health/ready : 应用是否准备好接收流量
```

## 第二行：挂载业务 API 路由

代码：

```python
app.include_router(api_router)
```

`api_router` 定义在：

```text
src/app/api/v1/__init__.py
```

代码是：

```python
api_router = APIRouter(prefix="/api/v1", tags=["v1"])
api_router.include_router(xhs_note.router, prefix="/xhs", tags=["xhs"])
```

这里有两层路由组合。

第一层：`api_router` 自己带了统一版本前缀：

```text
/api/v1
```

第二层：它又把小红书业务路由 `xhs_note.router` 挂到：

```text
/xhs
```

而 `xhs_note.router` 里定义了：

```python
@router.post("/notes/report")
```

所以最终业务接口路径是：

```text
POST /api/v1/xhs/notes/report
```

这个拆分方式的好处是：

```text
main.py
  -> 只负责挂载 api_router

api/v1/__init__.py
  -> 负责聚合 v1 版本下的业务模块

xhs_note.py
  -> 只负责小红书业务接口
```

以后如果新增用户模块、订单模块、内容模块，可以继续在 `api_router` 里挂载：

```python
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(order.router, prefix="/orders", tags=["orders"])
```

最终就会形成：

```text
/api/v1/users/...
/api/v1/orders/...
```

## 第三行：接入 Prometheus 指标

代码：

```python
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

这里的 `Instrumentator` 来自：

```python
from prometheus_fastapi_instrumentator import Instrumentator
```

它的作用是给 FastAPI 应用自动增加 Prometheus 指标采集能力。

这行代码可以拆成三步理解：

```python
Instrumentator()
```

创建一个指标采集器对象。

```python
.instrument(app)
```

把采集器接入当前 FastAPI 应用。可以把它理解成：给应用请求处理链路加了一层监控逻辑。

这层逻辑会在请求进入、请求结束时观察本次请求的信息，例如：

```text
请求方法：GET / POST
请求路径：/health/live、/api/v1/xhs/notes/report
响应状态码：200、500
请求耗时：用了多少秒
```

然后把这些信息累加到 Prometheus client 维护的内存指标对象里，例如 counter、histogram 等。

注意：这里不是把每个请求“转换成 Prometheus 格式并写入日志”。更准确地说：

```text
请求经过应用
  -> Instrumentator 观察请求
  -> 更新内存中的 metrics 计数器/耗时桶
  -> 请求继续正常返回给客户端
```

这些指标不是普通日志文件，不在 `app.log` 或 `error.log` 里。它们通常保存在当前 Python 进程内存中的 Prometheus 指标注册表里。

```python
.expose(app, endpoint="/metrics")
```

在 FastAPI 应用上暴露一个指标接口：

```text
GET /metrics
```

Prometheus 可以定期访问这个地址，抓取应用当前的监控指标。

这里也不是应用主动把 metrics “同步到 Prometheus”。Prometheus 的常见工作方式是 pull 模型：

```text
Prometheus 定时请求应用的 /metrics
  -> 应用把当前内存中的指标序列化成 Prometheus 文本格式
  -> Prometheus 读取响应内容
  -> Prometheus 把这些时间序列数据保存到自己的数据库里
```

所以 `/metrics` 更像一个“指标快照导出接口”。应用负责暴露当前指标，Prometheus 负责定时来抓取和存储。

## Instrumentator 是否拦截了请求

可以说它“观察/包装了请求处理过程”，但不建议简单理解成“拦截后把请求变成 metrics 日志”。

更准确的过程是：

```text
1. 客户端请求业务接口，例如 POST /api/v1/xhs/notes/report。
2. 请求进入 FastAPI 应用。
3. Instrumentator 注册的监控逻辑记录请求开始时间。
4. 请求继续进入中间件、路由函数和业务代码。
5. 业务代码返回响应。
6. Instrumentator 记录响应状态码、耗时、handler 等信息。
7. 对应的 counter/histogram 指标在内存中增加。
8. 响应正常返回给客户端。
```

之后 Prometheus 再请求：

```text
GET /metrics
```

应用才会把内存中的指标对象渲染成 Prometheus 可以识别的文本格式。

也就是说：

```text
业务请求阶段：更新内存指标。
/metrics 阶段：把内存指标导出成 Prometheus 文本格式。
Prometheus 阶段：定时抓取 /metrics 并保存到 Prometheus 自己的存储中。
```

三者不是同一件事。

## 应用挂掉后 metrics 会不会丢

会有可能丢一部分。

因为 `Instrumentator` 采集到的请求数量、耗时桶等指标，通常先保存在当前 FastAPI 进程的内存里。只有 Prometheus 成功请求 `/metrics` 并把结果保存到 Prometheus 自己的存储中之后，这部分指标才算进入监控系统。

可以理解为：

```text
请求发生
  -> 应用内存 metrics 增加
  -> Prometheus 定时抓取 /metrics
  -> Prometheus 存储成功
```

如果应用在下面这个阶段突然崩溃：

```text
应用内存 metrics 已经增加
  -> 但 Prometheus 还没来得及抓取
  -> 进程挂掉
```

那么这段还没被 Prometheus 抓走的指标增量就可能丢失。

举个例子：

```text
Prometheus 每 15 秒抓取一次 /metrics。

第 0 秒：Prometheus 抓取成功。
第 10 秒：应用处理了 100 个请求，内存 metrics 已经增加。
第 12 秒：应用进程突然崩溃。
第 15 秒：Prometheus 原本准备抓取，但应用已经不可用。
```

这时，第 10 秒到第 12 秒之间那 100 个请求对应的指标，就可能没有进入 Prometheus。

但已经被 Prometheus 抓取并保存过的数据不会因为应用挂掉而丢失。

所以更准确的结论是：

```text
已经被 Prometheus 抓取的数据：不会因为应用挂掉而丢。
还只存在应用进程内存里的指标：应用挂掉后可能丢。
```

这也是 Prometheus pull 模型的常见特性。Prometheus metrics 更适合做趋势监控、性能观测和告警，不适合当作审计日志、精确计费记录，或者“每一次事件都必须 100% 不丢”的强一致数据源。

如果要降低这类影响，可以考虑：

```text
缩短 Prometheus scrape interval，例如从 15s 调到 5s。
多副本部署，减少单个实例崩溃带来的观测缺口。
对关键业务事件使用持久化日志、数据库或消息队列。
不要把 metrics 当作精确审计或计费依据。
```

## /metrics 大概会输出什么

访问 `/metrics` 时，返回的不是 JSON，而是 Prometheus 文本格式。

内容大概类似：

```text
# HELP http_requests_total Total number of requests by method, status and handler.
# TYPE http_requests_total counter
http_requests_total{handler="/health/live",method="GET",status="2xx"} 10.0

# HELP http_request_duration_seconds Request duration in seconds.
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{handler="/api/v1/xhs/notes/report",le="0.1"} 3.0
```

具体指标名称会受 `prometheus-fastapi-instrumentator` 版本和配置影响，但核心信息通常包括：

```text
请求总数
请求耗时
HTTP 状态码
请求方法
接口 handler
```

## 为什么 metrics 和业务路由都挂在 app 上

FastAPI 应用对象 `app` 是整个 Web 服务的入口。

无论是业务接口、健康检查接口，还是 metrics 指标接口，最终都要注册到 `app` 上，Uvicorn 收到请求后才能通过 `app` 找到对应处理逻辑。

可以粗略理解为：

```text
Uvicorn 收到 HTTP 请求
  -> 交给 FastAPI app
  -> app 根据路径匹配路由
  -> /health/live 匹配 health.router
  -> /api/v1/xhs/notes/report 匹配 api_router 里的业务路由
  -> /metrics 匹配 Instrumentator 暴露的指标路由
```

## 这三行执行后的结果

应用启动后，至少会多出这些路径：

```text
GET  /health/live
GET  /health/ready
POST /api/v1/xhs/notes/report
GET  /metrics
```

其中：

```text
/health/...     给存活检查、就绪检查使用。
/api/v1/...     给业务客户端调用。
/metrics        给 Prometheus 抓取监控指标使用。
```

## 最后总结

这三行代码是在完成 FastAPI 应用的最后组装：

```text
app.include_router(health.router, prefix="/health", tags=["health"])
  -> 把健康检查接口注册到 /health 下。

app.include_router(api_router)
  -> 把 v1 业务接口注册到应用上。

Instrumentator().instrument(app).expose(app, endpoint="/metrics")
  -> 接入请求指标采集，并暴露 /metrics 给 Prometheus。
```

它们不直接处理某个具体请求，而是在应用启动时把“路由表”和“监控能力”注册到 FastAPI 应用对象上。
