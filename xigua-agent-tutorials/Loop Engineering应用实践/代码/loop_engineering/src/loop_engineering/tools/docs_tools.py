from __future__ import annotations

from langchain.tools import tool

from loop_engineering.repository.git import GitRepository
from loop_engineering.repository.local import LocalDocumentationRepository


def build_documentation_tools(
    repository: LocalDocumentationRepository,
    git: GitRepository,
) -> list:
    """Build tool closures bound to a single isolated workspace."""

    @tool
    def list_documentation_files(pattern: str = "**/*") -> str:
        """List documentation files. The glob pattern is relative to the repository root."""
        files = repository.list_documents(pattern)
        return "\n".join(files) if files else "No documentation files matched."

    @tool
    def read_document(path: str) -> str:
        """Read one documentation file using a repository-relative path."""
        return repository.read_text(path)

    @tool
    def search_documentation(query: str) -> str:
        """Search all documentation files for a literal phrase, returning path and line number."""
        matches = repository.search_documents(query)
        return "\n".join(matches) if matches else f"No matches found for: {query}"

    @tool
    def write_document(path: str, content: str) -> str:
        """Create or replace a Markdown/MDX document with complete file content."""
        repository.write_document(path, content)
        return f"Wrote {path} ({len(content)} characters)."

    @tool
    def inspect_current_diff() -> str:
        """Inspect all uncommitted documentation changes before finishing the task."""
        diff = git.diff()
        return diff if diff else "There are no uncommitted changes."

    return [
        list_documentation_files,
        read_document,
        search_documentation,
        write_document,
        inspect_current_diff,
    ]
