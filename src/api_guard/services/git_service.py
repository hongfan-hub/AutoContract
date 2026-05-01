from __future__ import annotations

import subprocess
from pathlib import Path

from api_guard.models import CommitInfo, FileDiff


class GitService:
    def __init__(self, repo_path: str | Path) -> None:
        self.repo_path = Path(repo_path)

    def _run(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout.strip()

    def head_commit(self) -> CommitInfo:
        output = self._run("log", "-1", "--pretty=format:%H%x1f%an%x1f%aI%x1f%s")
        sha, author, authored_at, subject = output.split("\x1f", maxsplit=3)
        return CommitInfo(sha=sha, author=author, authored_at=authored_at, subject=subject)

    def changed_files_since(self, previous_sha: str | None) -> list[FileDiff]:
        if previous_sha:
            range_spec = f"{previous_sha}..HEAD"
        else:
            range_spec = "HEAD~1..HEAD"

        try:
            numstat = self._run("diff", "--numstat", range_spec)
            name_status = self._run("diff", "--name-status", range_spec)
            patch_text = self._run("diff", "--unified=3", range_spec)
        except subprocess.CalledProcessError:
            numstat = self._run("show", "--numstat", "--format=", "HEAD")
            name_status = self._run("show", "--name-status", "--format=", "HEAD")
            patch_text = self._run("show", "--unified=3", "--format=", "HEAD")

        patch_by_file = _split_patch_by_file(patch_text)
        lines = [line for line in name_status.splitlines() if line.strip()]
        diffs: list[FileDiff] = []
        pending_numstat: dict[str, tuple[int, int]] = {}

        for line in numstat.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0].isdigit():
                additions, deletions, path = parts
                pending_numstat[path] = (int(additions), int(deletions))

        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 2:
                status, path = parts[0], parts[-1]
                additions, deletions = pending_numstat.get(path, (0, 0))
                diffs.append(
                    FileDiff(
                        path=path,
                        status=status,
                        additions=additions,
                        deletions=deletions,
                        patch=patch_by_file.get(path, ""),
                    )
                )

        if not diffs and patch_by_file:
            for path, patch in patch_by_file.items():
                additions, deletions = pending_numstat.get(path, (0, 0))
                diffs.append(
                    FileDiff(
                        path=path,
                        status="M",
                        additions=additions,
                        deletions=deletions,
                        patch=patch,
                    )
                )

        return diffs


def _split_patch_by_file(patch_text: str) -> dict[str, str]:
    patches: dict[str, list[str]] = {}
    current: str | None = None
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/", maxsplit=1)
            current = parts[1] if len(parts) == 2 else None
            if current:
                patches[current] = [line]
            continue
        if current:
            patches[current].append(line)
    return {path: "\n".join(lines) for path, lines in patches.items()}
