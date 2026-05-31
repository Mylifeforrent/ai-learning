"""
workspace.py 单元测试（T-WS-*, T-RS-*）

对齐 DESIGN.md §11.2 + §11.2.1 权限矩阵（v1.3-P2-20）。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from xiaopaw_team.tools.workspace import (
    write_shared,
    read_shared,
    check_write,
    init_project_tree,
)


@pytest.fixture
def ws_root(tmp_path: Path) -> Path:
    """创建一个完整 workspace 根（含 shared/projects/p1 子树）。"""
    init_project_tree(tmp_path, project_id="p1")
    return tmp_path


# ---------- 正向：各角色写自己 Owner 目录 ----------


@pytest.mark.parametrize("role,rel_path", [
    ("manager", "needs/requirements.md"),
    ("pm", "design/product_spec.md"),
    ("rd", "tech/tech_design.md"),
    ("rd", "code/backend/main.py"),
    ("qa", "qa/test_plan.md"),
    ("qa", "qa/defects/bug_1.md"),
])
def test_write_shared_allowed_owner(ws_root: Path, role: str, rel_path: str) -> None:
    write_shared(ws_root, project_id="p1", role=role, rel_path=rel_path, content="hello")
    full = ws_root / "shared" / "projects" / "p1" / rel_path
    assert full.exists()
    assert full.read_text() == "hello"


# ---------- 负向：角色写其他 Owner 目录被拒 ----------


@pytest.mark.parametrize("role,rel_path", [
    ("pm", "code/app.py"),
    ("rd", "design/product_spec.md"),
    ("qa", "needs/requirements.md"),
    ("manager", "code/backend/main.py"),
])
def test_write_shared_rejects_non_owner(ws_root: Path, role: str, rel_path: str) -> None:
    with pytest.raises(PermissionError):
        write_shared(ws_root, project_id="p1", role=role, rel_path=rel_path, content="x")


# ---------- reviews/ 目录规则（v1.3-P2-20 正则修复）----------


@pytest.mark.parametrize("role,rel_path,allowed", [
    ("rd", "reviews/product_design/rd_review.md", True),
    ("qa", "reviews/product_design/qa_acceptance_check.md", True),
    ("manager", "reviews/product_design/manager_note.md", True),
    # 角色与文件名 prefix 不一致 → 拒
    ("rd", "reviews/product_design/qa_review.md", False),
    ("qa", "reviews/code/rd_review.md", False),
    # 缺 topic 后缀 → 拒
    ("manager", "reviews/product_design/manager.md", False),
    # 非角色白名单 prefix → 拒
    ("pm", "reviews/product_design/stranger_review.md", False),
])
def test_reviews_path_pattern(ws_root: Path, role: str, rel_path: str, allowed: bool) -> None:
    if allowed:
        write_shared(ws_root, project_id="p1", role=role, rel_path=rel_path, content="r")
        assert (ws_root / "shared" / "projects" / "p1" / rel_path).exists()
    else:
        with pytest.raises(PermissionError):
            write_shared(ws_root, project_id="p1", role=role, rel_path=rel_path, content="r")


# ---------- mailboxes / events.jsonl 通过 Tool 层禁止直写 ----------


def test_write_shared_rejects_mailboxes(ws_root: Path) -> None:
    """邮箱必须走 SendMailTool，不能直接 WriteShared."""
    with pytest.raises(PermissionError):
        write_shared(ws_root, project_id="p1", role="manager",
                     rel_path="mailboxes/pm.json", content="[]")


def test_write_shared_rejects_events_jsonl(ws_root: Path) -> None:
    """events.jsonl 必须走 AppendEventTool."""
    with pytest.raises(PermissionError):
        write_shared(ws_root, project_id="p1", role="manager",
                     rel_path="events.jsonl", content="{}")


# ---------- 路径穿越防护 ----------


def test_write_shared_rejects_path_traversal(ws_root: Path) -> None:
    with pytest.raises(PermissionError):
        write_shared(ws_root, project_id="p1", role="manager",
                     rel_path="../../../../etc/passwd", content="x")


# ---------- read_shared: 全员可读 ----------


def test_read_shared_all_roles(ws_root: Path) -> None:
    write_shared(ws_root, project_id="p1", role="pm",
                 rel_path="design/product_spec.md", content="功能清单...")
    for role in ("manager", "pm", "rd", "qa"):
        content = read_shared(ws_root, project_id="p1", role=role,
                              rel_path="design/product_spec.md")
        assert content == "功能清单..."


def test_read_shared_nonexistent_raises(ws_root: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_shared(ws_root, project_id="p1", role="pm", rel_path="design/ghost.md")


# ---------- init_project_tree ----------


def test_init_project_tree_creates_all_dirs(ws_root: Path) -> None:
    p = ws_root / "shared" / "projects" / "p1"
    for sub in ("needs", "design", "tech", "code", "qa", "qa/defects",
                "reviews", "mailboxes", "logs/l2_task"):
        assert (p / sub).is_dir(), f"missing {sub}"
    # 4 邮箱 + events.jsonl
    for role in ("manager", "pm", "rd", "qa"):
        assert (p / "mailboxes" / f"{role}.json").exists()
    assert (p / "events.jsonl").exists()
