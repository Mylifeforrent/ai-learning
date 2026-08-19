from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.local import LocalDocumentationRepository
from loop_engineering.schemas import CheckResult


MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SKIPPED_LINK_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#")
PLACEHOLDERS = re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE)


class DeterministicVerifier:
    """Fast, explainable checks that do not require another model call."""

    def __init__(
        self,
        repository: LocalDocumentationRepository,
        git: GitRepository,
    ) -> None:
        self.repository = repository
        self.git = git

    def run(self) -> list[CheckResult]:
        changed_files = self.git.status_paths()
        checks = [self._has_changes(changed_files), self._scope_is_docs_only(changed_files)]
        checks.append(self._git_diff_is_clean())
        checks.extend(self._check_changed_documents(changed_files))
        return checks

    @staticmethod
    def _has_changes(changed_files: list[str]) -> CheckResult:
        return CheckResult(
            code="changes_present",
            passed=bool(changed_files),
            message=(
                f"Found {len(changed_files)} changed file(s)."
                if changed_files
                else "The agent did not change any files."
            ),
        )

    def _scope_is_docs_only(self, changed_files: list[str]) -> CheckResult:
        invalid = [
            path
            for path in changed_files
            if Path(path).suffix.lower() not in self.repository.allowed_extensions
        ]
        return CheckResult(
            code="docs_only_scope",
            passed=not invalid,
            message=(
                "All changed files are documentation files."
                if not invalid
                else "Non-documentation files were changed: " + ", ".join(invalid)
            ),
        )

    def _git_diff_is_clean(self) -> CheckResult:
        passed, output = self.git.diff_check()
        return CheckResult(
            code="git_diff_check",
            passed=passed,
            message=(
                "Git found no whitespace errors."
                if passed
                else f"Git diff check failed: {output}"
            ),
        )

    def _check_changed_documents(self, changed_files: list[str]) -> list[CheckResult]:
        checks: list[CheckResult] = []
        for relative_path in changed_files:
            if Path(relative_path).suffix.lower() not in self.repository.allowed_extensions:
                continue
            path = self.repository.resolve(relative_path)
            if not path.exists():
                checks.append(
                    CheckResult(
                        code="document_exists",
                        passed=False,
                        path=relative_path,
                        message=f"Changed document was deleted: {relative_path}",
                    )
                )
                continue
            content = path.read_text(encoding="utf-8")
            checks.append(self._no_placeholders(relative_path, content))
            checks.extend(self._internal_links_resolve(relative_path, content))
        return checks

    @staticmethod
    def _no_placeholders(relative_path: str, content: str) -> CheckResult:
        placeholders = sorted(set(match.group(0).upper() for match in PLACEHOLDERS.finditer(content)))
        return CheckResult(
            code="no_placeholders",
            passed=not placeholders,
            path=relative_path,
            message=(
                f"No placeholder markers in {relative_path}."
                if not placeholders
                else f"Placeholder markers in {relative_path}: {', '.join(placeholders)}"
            ),
        )

    def _internal_links_resolve(self, relative_path: str, content: str) -> list[CheckResult]:
        source = self.repository.resolve(relative_path)
        checks: list[CheckResult] = []
        for raw_target in MARKDOWN_LINK.findall(content):
            target = raw_target.strip().strip("<>")
            if not target or target.startswith(SKIPPED_LINK_PREFIXES):
                continue

            path_only = unquote(target.split("#", maxsplit=1)[0].split("?", maxsplit=1)[0])
            if not path_only:
                continue
            candidate = (
                self.repository.resolve(path_only.lstrip("/"))
                if path_only.startswith("/")
                else (source.parent / path_only).resolve()
            )
            inside_workspace = candidate == self.repository.root or self.repository.root in candidate.parents
            passed = inside_workspace and candidate.exists()
            checks.append(
                CheckResult(
                    code="internal_link_resolves",
                    passed=passed,
                    path=relative_path,
                    message=(
                        f"Internal link resolves: {relative_path} -> {target}"
                        if passed
                        else f"Broken or unsafe internal link in {relative_path}: {target}"
                    ),
                )
            )
        return checks
