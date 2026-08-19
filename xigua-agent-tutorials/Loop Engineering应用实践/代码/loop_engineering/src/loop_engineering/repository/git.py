from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GitCommandError(RuntimeError):
    pass


class GitRepository:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        process = subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=False,
            capture_output=True,
            text=True,
        )
        if check and process.returncode != 0:
            raise GitCommandError(process.stderr.strip() or process.stdout.strip())
        return process

    def ensure_initialized(self) -> None:
        if (self.root / ".git").exists():
            return
        self._run("init")
        self._run("config", "user.email", "loop-engineering@example.local")
        self._run("config", "user.name", "Loop Engineering Demo")
        self._run("add", ".")
        commit = self._run("commit", "-m", "Initial documentation baseline", check=False)
        if commit.returncode != 0 and "nothing to commit" not in commit.stdout.lower():
            raise GitCommandError(commit.stderr.strip() or commit.stdout.strip())

    def status_paths(self) -> list[str]:
        output = self._run("status", "--porcelain").stdout
        paths: list[str] = []
        for line in output.splitlines():
            if not line:
                continue
            value = line[3:]
            if " -> " in value:
                value = value.split(" -> ", maxsplit=1)[1]
            paths.append(value)
        return sorted(set(paths))

    def diff(self) -> str:
        tracked_diff = self._run("diff", "--no-ext-diff", "--", ".").stdout
        untracked_chunks: list[str] = []
        for relative_path in self.status_paths():
            path = self.root / relative_path
            status_line = self._run("status", "--porcelain", "--", relative_path).stdout
            if status_line.startswith("??") and path.is_file():
                content = path.read_text(encoding="utf-8", errors="replace")
                untracked_chunks.append(
                    f"diff --git a/{relative_path} b/{relative_path}\n"
                    f"new file mode 100644\n"
                    f"--- /dev/null\n"
                    f"+++ b/{relative_path}\n"
                    + "\n".join(f"+{line}" for line in content.splitlines())
                    + "\n"
                )
        return tracked_diff + "".join(untracked_chunks)

    def diff_check(self) -> tuple[bool, str]:
        process = self._run("diff", "--check", check=False)
        return process.returncode == 0, (process.stdout + process.stderr).strip()

    def reset_hard(self) -> None:
        self._run("reset", "--hard", "HEAD")
        self._run("clean", "-fd")

    @staticmethod
    def clone_local(source: Path, destination: Path) -> "GitRepository":
        source = source.resolve()
        destination = destination.resolve()
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(
            ["git", "clone", "--quiet", str(source), str(destination)],
            check=False,
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            raise GitCommandError(process.stderr.strip() or process.stdout.strip())
        return GitRepository(destination)
