"""
skill-creator 启发式 review：对所有 SKILL.md 做静态质量检查。
规则：
1. frontmatter 完整（name/description/type）
2. description 含 3 要素（触发源 + 能力 + 产出）——用启发式关键词
3. description 含"pushy"语（'一定'/'必须'/'都走此 skill'/'whenever'）
4. type ∈ {reference, task}
5. name 与目录名一致
6. body ≥ 10 行、≤ 500 行
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

WORKSPACE = Path(__file__).resolve().parents[2] / "workspace"

VALID_TYPES = {"reference", "task"}
# 触发源关键词（覆盖所有 skill）
TRIGGER_WORDS = [
    "触发", "收到", "当", "人类", "每次", "kickoff",
    "用户", "message", "邮件", "event", "feishu",
    "trigger", "触",
]
# 能力关键词
CAPABILITY_WORDS = [
    "读", "写", "发", "分析", "评估", "产出", "生成", "判断", "扫", "加载",
    "推断", "检查", "打分", "评审", "澄清", "起草", "框架", "思考",
    "按", "从", "评",
]
# "pushy"措辞
PUSHY_WORDS = [
    "一定", "必须", "都走此", "无条件", "whenever", "总是", "任何", "所有",
    "每次被", "每次都", "都用", "every time",
]


def _iter_skills() -> list[Path]:
    return sorted(WORKSPACE.glob("**/skills/*/SKILL.md"))


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    try:
        return yaml.safe_load(parts[1]) or {}, parts[2]
    except yaml.YAMLError:
        return {}, content


@pytest.mark.parametrize("skill_path", _iter_skills(), ids=lambda p: p.parent.name)
def test_skill_quality(skill_path: Path) -> None:
    """单条 SKILL.md 质量检查."""
    assert skill_path.exists(), f"missing {skill_path}"
    content = skill_path.read_text(encoding="utf-8")

    # frontmatter
    fm, body = _parse_frontmatter(content)
    assert fm, f"no frontmatter in {skill_path}"
    for key in ("name", "description", "type"):
        assert key in fm, f"missing {key} in {skill_path}"
    assert fm["type"] in VALID_TYPES, f"invalid type in {skill_path}: {fm['type']!r}"
    # name 与目录名一致
    assert fm["name"] == skill_path.parent.name, (
        f"name mismatch in {skill_path}: frontmatter={fm['name']!r}, dir={skill_path.parent.name!r}"
    )

    desc: str = fm["description"]
    assert 40 <= len(desc) <= 600, f"description length {len(desc)} out of range in {skill_path}"

    # description 3 要素启发式：触发源 + 能力（中文内容对英文关键词放宽）
    has_trigger = any(w in desc for w in TRIGGER_WORDS)
    has_capability = any(w in desc for w in CAPABILITY_WORDS)
    assert has_trigger, f"description lacks trigger cues in {skill_path.parent.name}"
    assert has_capability, f"description lacks capability cues in {skill_path.parent.name}"

    # pushy 措辞（鼓励强触发）
    is_pushy = any(w in desc for w in PUSHY_WORDS)
    assert is_pushy, (
        f"description not pushy enough in {skill_path.parent.name}: "
        f"expected words like 一定/必须/whenever, got: {desc[:80]}..."
    )

    # body 长度
    non_empty_lines = [l for l in body.splitlines() if l.strip()]
    assert 10 <= len(non_empty_lines) <= 500, (
        f"body line count {len(non_empty_lines)} out of [10,500] in {skill_path.parent.name}"
    )


def test_skill_count_by_role() -> None:
    """确认每角色 skill 数量与 DESIGN.md v1.5 §16 预期匹配（至少齐备）."""
    counts: dict[str, int] = {}
    for p in _iter_skills():
        role = p.parent.parent.parent.name  # workspace/{role}/skills/{skill}/SKILL.md
        counts[role] = counts.get(role, 0) + 1
    # manager ≥ 10 / pm ≥ 3 / rd ≥ 5 / qa ≥ 6 / shared ≥ 2
    assert counts.get("manager", 0) >= 10, counts
    assert counts.get("pm", 0) >= 3, counts
    assert counts.get("rd", 0) >= 5, counts
    assert counts.get("qa", 0) >= 6, counts
    assert counts.get("shared", 0) >= 2, counts
