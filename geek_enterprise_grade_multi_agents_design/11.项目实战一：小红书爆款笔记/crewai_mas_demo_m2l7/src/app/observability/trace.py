"""OpenTracing 兼容的 Trace 上下文：trace_id、span_id、W3C traceparent 解析与注入。"""

import secrets
from contextvars import ContextVar

# W3C Trace Context 要求 trace_id 是 32 个十六进制字符，span_id 是 16 个十六进制字符。
# 这里的 *_BYTES 表示传给 secrets.token_hex(num_bytes) 的“字节数”：
# 1 byte = 8 bit，可表示 0~255；十六进制 1 位只能表示 0~15，
# 因此需要 2 位十六进制字符才能完整表示 1 byte，例如 255 会表示为 ff。
# 所以 16 bytes -> 32 hex chars，8 bytes -> 16 hex chars。
TRACE_ID_BYTES = 16  # 生成 32 个十六进制字符的 trace_id
SPAN_ID_BYTES = 8    # 生成 16 个十六进制字符的 span_id

# ContextVar 用于保存“当前异步上下文”的变量值，适合 FastAPI 这类并发请求场景。
# 原理详见 doc/notes/CONTEXTVAR_EXPLAINED.md。
# 每个请求都会拥有自己独立的 trace_id/span_id，上下游函数可以通过 get_* 方法读取，
# 但不同请求之间不会因为共用全局变量而互相串值。
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")

# 当前服务为本次请求/操作生成的 span_id，用来标识 trace 链路中的当前节点。
span_id_ctx: ContextVar[str] = ContextVar("span_id", default="")

# 上游服务传来的 span_id，会作为当前 span 的 parent_span_id，便于还原父子调用关系。
parent_span_id_ctx: ContextVar[str] = ContextVar("parent_span_id", default="")


def _random_hex(num_bytes: int) -> str:
    return secrets.token_hex(num_bytes)


def generate_trace_id() -> str:
    """生成符合 W3C 的 32 位十六进制 trace_id。"""
    return _random_hex(TRACE_ID_BYTES)


def generate_span_id() -> str:
    """生成符合 W3C 的 16 位十六进制 span_id。"""
    return _random_hex(SPAN_ID_BYTES)


def set_trace_context(
    trace_id: str | None = None,
    span_id: str | None = None,
    parent_span_id: str | None = None,
) -> tuple[str, str]:
    """
    设置当前上下文的 trace_id、span_id。
    若未传入则自动生成，返回 (trace_id, span_id)。
    """
    tid = trace_id or generate_trace_id()
    sid = span_id or generate_span_id()
    trace_id_ctx.set(tid)
    span_id_ctx.set(sid)
    if parent_span_id is not None:
        parent_span_id_ctx.set(parent_span_id)
    return tid, sid


def get_trace_id() -> str:
    return trace_id_ctx.get() or ""


def get_span_id() -> str:
    return span_id_ctx.get() or ""


def get_parent_span_id() -> str:
    return parent_span_id_ctx.get() or ""


def get_trace_context() -> dict[str, str]:
    """返回 OpenTracing 风格的上下文字典，便于写入日志。"""
    return {
        "trace_id": get_trace_id(),
        "span_id": get_span_id(),
        "parent_span_id": get_parent_span_id(),
    }


def parse_traceparent(header_value: str | None) -> tuple[str | None, str | None]:
    """
    解析 W3C traceparent 头：version-trace_id-span_id-flags。
    返回 (trace_id, parent_span_id)，解析失败返回 (None, None)。
    """
    if not header_value or not header_value.strip():
        return None, None
    parts = header_value.strip().split("-")
    if len(parts) != 4:
        return None, None
    _version, tid, parent_sid, _flags = parts
    if len(tid) != 32 or len(parent_sid) != 16:
        return None, None
    try:
        int(tid, 16)
        int(parent_sid, 16)
    except ValueError:
        return None, None
    return tid, parent_sid


def build_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
    """构造 W3C traceparent 头：00-{trace_id}-{span_id}-{flags}。"""
    flags = "01" if sampled else "00"
    return f"00-{trace_id}-{span_id}-{flags}"
