from __future__ import annotations

from api_guard.models import CommitInfo, FileDiff, RepoConfig
from api_guard.services.git_service import GitService
from api_guard.services.state_store import StateStore


class SnifferAgent:
    def __init__(self, state_store: StateStore) -> None:
        self.state_store = state_store

    def sniff(self, repo: RepoConfig) -> tuple[CommitInfo, list[FileDiff], bool]:
        git = GitService(repo.path)
        current = git.head_commit()
        previous_sha = self.state_store.get_last_commit(repo.name)
        has_changed = current.sha != previous_sha
        changed_files = git.changed_files_since(previous_sha) if has_changed else []
        return current, changed_files, has_changed
