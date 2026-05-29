# HTTP Request Body 流式读取原理说明

## 为什么请求体会像“一次性流”

HTTP 请求从客户端发到服务端时，本质上是一串网络字节：

```text
客户端
  -> TCP 连接
  -> HTTP 请求行、请求头、请求体
  -> 服务端 socket
```

请求行和请求头通常比较小，服务端会较早解析出来，比如方法、路径、Header 等。

请求体 body 不一定小。它可能是一个 JSON，也可能是一个大文件上传、表单提交、流式传输内容。如果框架在请求一进来时就把 body 全部读进内存，会有几个问题：

- 大请求会占用很多内存。
- 文件上传场景不适合一次性全部加载。
- 分块传输时，body 可能本来就是边到达边读取。
- 服务端需要背压能力，不能无限制吞数据。

所以底层通常把 body 暴露成一个“向前读取”的输入流。这个流读过的数据就被消费了，后面再次读取时，底层不会自动把已经读过的网络字节倒回去。

可以类比成：

```text
body 流：part1 -> part2 -> part3 -> EOF

第一次读取：读到 part1、part2、part3
第二次读取：已经到 EOF，没有新数据
```

如果应用希望多次读取 body，就需要自己或框架把第一次读到的内容缓存下来，再用缓存内容构造一个“新的可读入口”。

## ASGI/FastAPI 里 body 是怎么来的

FastAPI 底层基于 Starlette，运行在 ASGI 服务器上，常见组合是：

```text
Uvicorn
  -> ASGI
  -> Starlette
  -> FastAPI
  -> 路由函数
```

ASGI 把一个 HTTP 请求拆成三类核心信息：

```text
scope   : 请求元信息，例如 method、path、headers
receive : 异步函数，用来接收请求体等事件
send    : 异步函数，用来发送响应事件
```

其中请求体不是直接放在 `scope` 里，而是通过 `receive()` 一次或多次读取：

```python
message = await receive()
```

可能读到：

```python
{
    "type": "http.request",
    "body": b'{"name":"Tom"}',
    "more_body": False,
}
```

如果 body 较大，也可能分多次到达：

```python
{"type": "http.request", "body": b"part1", "more_body": True}
{"type": "http.request", "body": b"part2", "more_body": True}
{"type": "http.request", "body": b"part3", "more_body": False}
```

Starlette 的 `Request` 对象把这些底层细节包装起来，让业务代码可以写：

```python
body_bytes = await request.body()
data = await request.json()
```

但底层仍然是从 ASGI `receive()` 流里读取 body。

## 项目里的 new_request 是在做什么

项目中的代码：

```python
body_bytes = await request.body()

async def receive():
    return {"type": "http.request", "body": body_bytes}

new_request = StarletteRequest(request.scope, receive)
```

作用是：

```text
1. 中间件先读取原始 request 的 body，用于日志打印。
2. 把读取到的 body_bytes 缓存在内存里。
3. 构造一个新的 receive()，后续读取 body 时从缓存返回。
4. 用原来的 scope + 新的 receive() 构造 new_request。
5. 把 new_request 传给后续路由，避免路由读不到请求体。
```

这和 Java 里常见的 `HttpServletRequestWrapper` 思路很像：先把原始 body 读出来缓存成 byte array，然后重写读取入口，让后续代码还能再读。

需要注意一个细节：Starlette 的同一个 `Request` 实例内部可能会缓存 `request.body()` 的结果，所以在“同一个 Request 对象上重复调用 `await request.body()`”通常能拿到缓存值。但中间件把请求继续交给后续应用时，后续链路不一定复用同一个 `Request` 实例，所以这里显式构造 `new_request` 更稳妥。

## Tomcat 到 Spring Boot 的请求处理路径

Java Web 项目里，常见路径是：

```text
客户端
  -> TCP 连接
  -> Tomcat Connector
  -> 解析 HTTP 请求
  -> 构造 ServletRequest / HttpServletRequest
  -> Filter 链
  -> Spring MVC DispatcherServlet
  -> HandlerMapping 找到 Controller
  -> HandlerAdapter 调用 Controller
  -> HttpMessageConverter 读取 @RequestBody
```

Tomcat 作为 Servlet 容器，负责接收 socket 数据、解析 HTTP 协议，并把请求包装成 Servlet API 里的对象，例如 `HttpServletRequest`。

在 Servlet API 中，请求体主要通过这两个入口读取：

```java
ServletInputStream inputStream = request.getInputStream();
BufferedReader reader = request.getReader();
```

它们背后面对的仍然是请求体输入流。这个输入流和 ASGI 的 `receive()` 思路类似：它代表客户端发送过来的 body 数据，读取会推进流的位置。

## Spring Boot 的 @RequestBody 是怎么读取 body 的

在 Spring MVC 中，如果 Controller 写了：

```java
@PostMapping("/users")
public User createUser(@RequestBody UserRequest request) {
    ...
}
```

Spring 会在调用 Controller 方法之前，使用 `HttpMessageConverter` 读取 `HttpServletRequest` 的 body。

典型流程是：

```text
1. 请求进入 DispatcherServlet。
2. Spring 找到目标 Controller 方法。
3. 发现参数上有 @RequestBody。
4. 选择合适的 HttpMessageConverter，例如 MappingJackson2HttpMessageConverter。
5. 从 request.getInputStream() 读取 body。
6. 使用 Jackson 把 JSON 反序列化成 Java 对象。
7. 把 Java 对象作为参数传给 Controller 方法。
```

所以 `@RequestBody` 并不是凭空拿到 body，它底层仍然要读取 `request.getInputStream()`。

## Java 中 body 能不能被多个地方读取

原始 `HttpServletRequest` 的 body 不能天然无限重复读取。

如果 Filter 里先读了：

```java
ServletInputStream inputStream = request.getInputStream();
byte[] bytes = inputStream.readAllBytes();
```

后面的 Controller 再用：

```java
@RequestBody UserRequest request
```

就可能读不到 body，因为原始输入流已经被 Filter 消费完了。

很多 Java 项目里感觉“body 可以在多个地方拿到”，常见原因是：

- 实际上只有 Controller 读取了一次 body。
- 读取的是 query/form parameter，不是原始 body 流。
- 使用了缓存型 request wrapper。
- 日志组件、安全组件或框架扩展已经帮忙包装过 request。
- 读取的是 Spring 已经反序列化好的 Java 对象，而不是重新读原始流。

## getInputStream 和 getReader 的关系

在 Servlet API 里，`getInputStream()` 和 `getReader()` 都是读取请求体的入口，但通常不能混用。

例如：

```java
request.getInputStream();
request.getReader();
```

或者：

```java
request.getReader();
request.getInputStream();
```

这类混用通常会抛出 `IllegalStateException`，因为一个按字节流读，一个按字符流读，容器不允许同一个 request body 同时用两种方式读取。

## 同一个 Controller 里读两次 body 会怎样

Java Servlet 标准的 `HttpServletRequest` 没有 `getBody()` 这个通用方法，常见的是 `getInputStream()`、`getReader()`，或者 Spring 的 `@RequestBody`。

如果在同一个 Controller 里直接读两次原始输入流：

```java
@PostMapping("/demo")
public String demo(HttpServletRequest request) throws IOException {
    byte[] first = request.getInputStream().readAllBytes();
    byte[] second = request.getInputStream().readAllBytes();
    return "first=" + first.length + ", second=" + second.length;
}
```

常见表现是：

```text
第一次：能读到 body 内容。
第二次：读到空内容，因为流已经到 EOF。
```

具体表现可能受 Servlet 容器和 wrapper 影响，但“原始流不能自动重放”这个原则不变。

如果使用 `@RequestBody`：

```java
@PostMapping("/demo")
public String demo(@RequestBody UserRequest body, HttpServletRequest request) throws IOException {
    byte[] second = request.getInputStream().readAllBytes();
    return "...";
}
```

`@RequestBody` 已经在 Controller 方法调用前被 Spring 读取并反序列化了，所以方法里再读 `request.getInputStream()`，通常也读不到原始 body。

如果尝试定义多个 `@RequestBody` 参数：

```java
public String demo(@RequestBody A a, @RequestBody B b) {
    ...
}
```

这通常不是一个合理用法。HTTP 请求只有一个 body，Spring 读取一次后，第二个参数没有独立的 body 可读。实际项目中应定义一个组合 DTO 来承载整个请求体。

## ContentCachingRequestWrapper 能解决什么

Spring 提供了 `ContentCachingRequestWrapper`，它可以在请求体被读取时，把内容缓存起来，之后通过：

```java
byte[] cached = wrapper.getContentAsByteArray();
```

拿到已经读取过的内容。

但要注意：`ContentCachingRequestWrapper` 更常用于“读取后查看缓存内容”，例如日志记录。它不是万能的“让原始 `getInputStream()` 可以无限重读”的方案。

它的典型特点是：

- body 只有在被实际读取后才会进入缓存。
- `getContentAsByteArray()` 可以拿到缓存内容。
- 如果要让后续业务代码重新从头读取 body，很多项目会自定义 `HttpServletRequestWrapper`，把 body 缓存成 byte array，并在每次 `getInputStream()` 时返回一个新的 `ByteArrayInputStream` 包装。

这种自定义 wrapper 的思路和 FastAPI 里的 `new_request + 自定义 receive()` 非常接近。

## Java wrapper 和 FastAPI new_request 的类比

Java 中可重复读取 body 的 wrapper 思路：

```text
原始 HttpServletRequest
  -> Filter 读取 InputStream
  -> 缓存 body bytes
  -> 包装成 CachedBodyHttpServletRequest
  -> 后续 Filter/Controller 从缓存中读取 body
```

FastAPI 当前项目中的思路：

```text
原始 Request
  -> 中间件 await request.body()
  -> 缓存 body_bytes
  -> 构造新的 receive()
  -> StarletteRequest(request.scope, receive)
  -> 后续路由从缓存 receive() 读取 body
```

两者本质一样：

> 原始 body 是一次性流；如果要让多个地方读取，就必须缓存并重新包装读取入口。

## 最后总结

请求体 body 底层通常不是一个可以天然无限重复读取的字段，而是来自网络连接的输入流。

Java Servlet 里的 `getInputStream()`、`getReader()` 是流式读取；ASGI/FastAPI 里的 `receive()` 也是流式读取。

区别只是不同框架包装得不一样：

```text
Java Servlet:
HttpServletRequest -> getInputStream()/getReader()

Spring MVC:
@RequestBody -> HttpMessageConverter -> request.getInputStream()

ASGI/FastAPI:
Request.body()/Request.json() -> ASGI receive()
```

如果没有缓存和 wrapper，谁先把 body 读完，后面的人就很可能读不到。项目里的 `StarletteRequest(request.scope, receive)` 就是在中间件读完 body 后，重新提供一个基于缓存的 body 读取入口。
