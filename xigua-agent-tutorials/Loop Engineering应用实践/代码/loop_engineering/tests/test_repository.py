from pathlib import Path

import pytest

from loop_engineering.repository.local import (
    LocalDocumentationRepository,
    UnsafePathError,
)


def test_repository_blocks_path_traversal(tmp_path: Path) -> None:
    repository = LocalDocumentationRepository(tmp_path, allowed_extensions=[".md"])

    with pytest.raises(UnsafePathError):
        repository.resolve("../secrets.txt")


def test_repository_writes_only_documentation(tmp_path: Path) -> None:
    repository = LocalDocumentationRepository(tmp_path, allowed_extensions=[".md", ".mdx"])
    repository.write_document("docs/page.md", "# Page\n")

    assert repository.read_text("docs/page.md") == "# Page\n"
    with pytest.raises(ValueError):
        repository.write_document("src/app.py", "print('no')")
