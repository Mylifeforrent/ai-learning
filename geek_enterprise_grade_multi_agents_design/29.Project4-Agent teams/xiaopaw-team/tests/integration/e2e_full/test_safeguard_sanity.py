"""
Safeguard 机制自检（不需 LLM）：验证 Driver.start/stop 能正确备份+还原 workspace。

跑法：`pytest tests/integration/e2e_full/test_safeguard_sanity.py -v`
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tests.integration.e2e_full._driver import REAL_WORKSPACE, WorkspaceSafeguard


def _dir_hash(path: Path) -> str:
    """计算整目录内容哈希（用于断言恢复是否精确）."""
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(path))
            h.update(rel.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def test_workspace_safeguard_captures_and_restores(tmp_path: Path) -> None:
    backup = tmp_path / "backup"
    guard = WorkspaceSafeguard(backup)

    before = _dir_hash(REAL_WORKSPACE)
    guard.capture()

    # 污染 workspace：追加一个文件
    polluted = REAL_WORKSPACE / "shared" / "projects" / "TEST-POLLUTION"
    polluted.mkdir(parents=True, exist_ok=True)
    (polluted / "trash.txt").write_text("this should be gone after restore")

    # 改一个 SKILL.md
    sample_skill = REAL_WORKSPACE / "manager" / "skills" / "sop_feature_dev" / "SKILL.md"
    original_skill = sample_skill.read_text(encoding="utf-8")
    sample_skill.write_text("# POLLUTED\n", encoding="utf-8")

    mid = _dir_hash(REAL_WORKSPACE)
    assert mid != before, "污染后 hash 应不同"

    guard.restore()

    after = _dir_hash(REAL_WORKSPACE)
    assert after == before, "restore 未能完整还原 workspace"
    assert not polluted.exists(), "测试产生的 project 目录应被还原清除"
    assert sample_skill.read_text(encoding="utf-8") == original_skill, "SKILL.md 应被还原"
