"""
self_score.py — 从 task_output 解析 self_score 5 维自评 + 计算加权总分

对齐 DESIGN.md §16.5 + §25.2 L2 `result_quality_estimate` 字段来源。

Agent 在 task_done 前调用 self_score SKILL，按 5 维打分并输出 JSON：

```json
{
  "self_score": 0.82,
  "breakdown": {
    "completeness": 1.0,
    "self_review": 0.9,
    "hard_constraints": 1.0,
    "clarity": 0.7,
    "timeliness": 0.8
  },
  "rationale": "..."
}
```

task_callback 从 task_output 解析这段 JSON 写入 L2 entry。
"""
from __future__ import annotations

import json
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

DEFAULT_WEIGHTS: dict[str, float] = {
    "completeness": 0.20,
    "self_review": 0.30,
    "hard_constraints": 0.20,
    "clarity": 0.15,
    "timeliness": 0.15,
}

REQUIRED_DIMS = set(DEFAULT_WEIGHTS.keys())

# 简单 JSON 块提取：匹配 {...self_score...} 的最外层对象
_JSON_BLOCK = re.compile(r"\{[\s\S]*?\"self_score\"[\s\S]*?\}", re.DOTALL)


def compute_self_score(
    breakdown: dict[str, float],
    *,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> float:
    """按 5 维加权计算总分，返回 0.0-1.0（round 到 2 位）."""
    missing = REQUIRED_DIMS - breakdown.keys()
    if missing:
        raise ValueError(f"missing dimensions: {missing}")
    for k, v in breakdown.items():
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"dim {k}={v} out of range [0, 1]")
    total = sum(breakdown[k] * weights[k] for k in REQUIRED_DIMS)
    # Decimal + ROUND_HALF_UP 保证 0.895 → 0.90 而非 0.89（浮点 rounding 陷阱）
    return float(Decimal(str(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _try_parse_json_obj(text: str) -> dict | None:
    """从文本里尽力提取一个含 self_score 字段的 JSON 对象."""
    if not text:
        return None
    # 先直接整体 json 试一次
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "self_score" in obj:
            return obj
    except (json.JSONDecodeError, TypeError):
        pass
    # 再做区块匹配（最小匹配）
    for m in _JSON_BLOCK.finditer(text):
        # 扩展匹配直到 JSON 平衡
        start = m.start()
        balanced = _extract_balanced_braces(text, start)
        if balanced is None:
            continue
        try:
            obj = json.loads(balanced)
            if isinstance(obj, dict) and "self_score" in obj:
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _extract_balanced_braces(text: str, start: int) -> str | None:
    """从 text[start]（必为 '{'）开始找到配对的 '}'，返回含括号的子串."""
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def extract_self_score_from_task_output(task_output: Any) -> tuple[float | None, dict | None]:
    """
    从 CrewAI TaskOutput 里解析 self_score + breakdown。
    找不到合法结构 → 返回 (None, None)（task_callback 写 L2 时字段记为 null）.
    """
    obj: dict | None = None

    # json_output 优先（CrewAI Pydantic 输出模型的情况）
    jo = getattr(task_output, "json_output", None)
    if isinstance(jo, dict) and "self_score" in jo:
        obj = jo

    if obj is None:
        raw = getattr(task_output, "raw", None)
        obj = _try_parse_json_obj(raw)

    if obj is None:
        return None, None

    try:
        score = float(obj["self_score"])
    except (KeyError, TypeError, ValueError):
        return None, None

    breakdown = obj.get("breakdown")
    if not isinstance(breakdown, dict):
        breakdown = None

    return score, breakdown
