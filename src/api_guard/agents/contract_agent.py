from __future__ import annotations

from api_guard.analyzers.python_api_analyzer import PythonApiAnalyzer
from api_guard.models import CommitInfo, ContractBundle, FileDiff, RepoConfig
from api_guard.openapi.generator import OpenApiGenerator


class ContractAgent:
    def __init__(self) -> None:
        self.analyzer = PythonApiAnalyzer()
        self.openapi = OpenApiGenerator()

    def build(
        self,
        repo: RepoConfig,
        commit: CommitInfo,
        changed_files: list[FileDiff],
    ) -> ContractBundle:
        routes = self.analyzer.analyze_repo(repo.path)
        document = self.openapi.build(repo.openapi_title, repo.name, commit, routes)
        return ContractBundle(
            repo=repo.name,
            commit=commit,
            changed_files=changed_files,
            routes=routes,
            openapi=document,
        )
