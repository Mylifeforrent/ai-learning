from __future__ import annotations

import re
from pathlib import Path


class UnsafePathError(ValueError):
    pass


class LocalDocumentationRepository:
    """Safe filesystem access restricted to one documentation workspace."""

    def __init__(
        self,
        root: Path,
        allowed_extensions: list[str],
        protected_paths: list[str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self.protected_paths = set(protected_paths or [])
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str) -> Path:
        normalized = relative_path.strip().replace("\\", "/")
        if not normalized or normalized == ".":
            return self.root

        first_segment = normalized.split("/", maxsplit=1)[0]
        if first_segment in self.protected_paths:
            raise UnsafePathError(f"Path is protected: {relative_path}")

        candidate = (self.root / normalized).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise UnsafePathError(f"Path escapes workspace: {relative_path}")
        return candidate

    def list_files(self, pattern: str = "**/*") -> list[str]:
        files = [path for path in self.root.glob(pattern) if path.is_file()]
        return sorted(path.relative_to(self.root).as_posix() for path in files if ".git" not in path.parts)

    def list_documents(self, pattern: str = "**/*") -> list[str]:
        return [
            path
            for path in self.list_files(pattern)
            if Path(path).suffix.lower() in self.allowed_extensions
        ]

    def read_text(self, relative_path: str) -> str:
        path = self.resolve(relative_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return path.read_text(encoding="utf-8")

    def write_document(self, relative_path: str, content: str) -> None:
        path = self.resolve(relative_path)
        if path.suffix.lower() not in self.allowed_extensions:
            raise ValueError(
                f"Only documentation files are writable: {sorted(self.allowed_extensions)}"
            )
        if len(content.encode("utf-8")) > 250_000:
            raise ValueError("Refusing to write a documentation file larger than 250 KB")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def search_documents(self, query: str, max_results: int = 30) -> list[str]:
        if not query.strip():
            return []
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        matches: list[str] = []
        for relative_path in self.list_documents():
            for line_number, line in enumerate(self.read_text(relative_path).splitlines(), start=1):
                if pattern.search(line):
                    matches.append(f"{relative_path}:{line_number}: {line.strip()}")
                    if len(matches) >= max_results:
                        return matches
        return matches
