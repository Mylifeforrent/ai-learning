"""
self_score.py 单元测试（T-SS-*）

对齐 DESIGN.md §16.5 + §25.2 L2 schema 的 self_score 字段来源。
"""
from __future__ import annotations

import pytest

from xiaopaw_team.tools.self_score import (
    compute_self_score,
    extract_self_score_from_task_output,
    DEFAULT_WEIGHTS,
)


def test_compute_self_score_5_dim_weighted() -> None:
    """T-SS-01: 5 维加权计算正确."""
    breakdown = {
        "completeness": 1.0,
        "self_review": 0.9,
        "hard_constraints": 1.0,
        "clarity": 0.7,
        "timeliness": 0.8,
    }
    # 0.2*1.0 + 0.3*0.9 + 0.2*1.0 + 0.15*0.7 + 0.15*0.8
    # = 0.2 + 0.27 + 0.2 + 0.105 + 0.12 = 0.895
    # Decimal ROUND_HALF_UP → 0.90
    actual = compute_self_score(breakdown)
    assert actual == 0.90


def test_compute_self_score_weights_sum_to_1() -> None:
    assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9


def test_compute_self_score_rejects_missing_dim() -> None:
    with pytest.raises(ValueError, match="missing"):
        compute_self_score({"completeness": 1.0})  # 缺其他 4 维


def test_compute_self_score_rejects_out_of_range() -> None:
    with pytest.raises(ValueError, match="range"):
        compute_self_score({
            "completeness": 1.5, "self_review": 1.0, "hard_constraints": 1.0,
            "clarity": 1.0, "timeliness": 1.0,
        })


def test_compute_self_score_rounds_to_2_decimals() -> None:
    """精度约定：小数点后 2 位."""
    breakdown = {
        "completeness": 1.0, "self_review": 1.0, "hard_constraints": 1.0,
        "clarity": 1.0, "timeliness": 1.0,
    }
    assert compute_self_score(breakdown) == 1.0


# ---------- T-SS-02: extract from task_output ----------


class _FakeTaskOutput:
    def __init__(self, raw: str):
        self.raw = raw
        self.json_output = None
        self.task_id = "tab01234"


def test_extract_from_raw_json_block() -> None:
    raw = """产品设计完成。产出摘要：

{
  "self_score": 0.85,
  "breakdown": {
    "completeness": 1.0,
    "self_review": 0.9,
    "hard_constraints": 1.0,
    "clarity": 0.6,
    "timeliness": 0.8
  },
  "rationale": "..."
}
"""
    score, breakdown = extract_self_score_from_task_output(_FakeTaskOutput(raw))
    assert score == 0.85
    assert breakdown["completeness"] == 1.0


def test_extract_missing_returns_none() -> None:
    """T-SS-02: Agent 漏调 self_score → 返回 (None, None)."""
    raw = "产品设计完成，已写入 design/product_spec.md"
    score, breakdown = extract_self_score_from_task_output(_FakeTaskOutput(raw))
    assert score is None
    assert breakdown is None


def test_extract_from_dict_task_output() -> None:
    class _DictOutput:
        raw = None
        json_output = {"self_score": 0.6, "breakdown": {
            "completeness": 0.5, "self_review": 0.5, "hard_constraints": 0.8,
            "clarity": 0.7, "timeliness": 0.7,
        }}
        task_id = "t"
    score, breakdown = extract_self_score_from_task_output(_DictOutput())
    assert score == 0.6
    assert breakdown["self_review"] == 0.5
