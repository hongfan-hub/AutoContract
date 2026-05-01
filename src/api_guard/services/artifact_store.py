from __future__ import annotations

from pathlib import Path
from typing import Any

from api_guard.utils.fs import ensure_dir
from api_guard.utils.json_utils import write_json


class ArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = ensure_dir(root)

    def run_dir(self, repo: str, commit_sha: str) -> Path:
        return ensure_dir(self.root / repo / commit_sha[:12])

    def save_json(self, repo: str, commit_sha: str, name: str, data: Any) -> Path:
        path = self.run_dir(repo, commit_sha) / name
        write_json(path, data)
        return path

    def save_text(self, repo: str, commit_sha: str, name: str, content: str) -> Path:
        path = self.run_dir(repo, commit_sha) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path
