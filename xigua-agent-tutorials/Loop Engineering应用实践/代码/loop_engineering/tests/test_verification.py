from pathlib import Path

from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.local import LocalDocumentationRepository
from loop_engineering.verification.deterministic import DeterministicVerifier


def create_repo(tmp_path: Path) -> tuple[LocalDocumentationRepository, GitRepository]:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "# Guide\n\nSee [configuration](configuration.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "configuration.md").write_text(
        "# Configuration\n",
        encoding="utf-8",
    )
    repository = LocalDocumentationRepository(tmp_path, allowed_extensions=[".md"])
    git = GitRepository(tmp_path)
    git.ensure_initialized()
    return repository, git


def test_verifier_accepts_valid_doc_change(tmp_path: Path) -> None:
    repository, git = create_repo(tmp_path)
    repository.write_document(
        "docs/guide.md",
        "# Guide\n\nInstall with `pip install acme-sdk`.\n\n"
        "See [configuration](configuration.md).\n",
    )

    checks = DeterministicVerifier(repository, git).run()

    assert checks
    assert all(check.passed for check in checks), [check.message for check in checks]


def test_verifier_rejects_broken_internal_link(tmp_path: Path) -> None:
    repository, git = create_repo(tmp_path)
    repository.write_document(
        "docs/guide.md",
        "# Guide\n\nSee [missing](missing.md).\n",
    )

    checks = DeterministicVerifier(repository, git).run()

    failures = [check for check in checks if not check.passed]
    assert any(check.code == "internal_link_resolves" for check in failures)
