from __future__ import annotations

from api_guard.generators.test_case_generator import TestCaseGenerator
from api_guard.models import RepoConfig, VerificationBundle
from api_guard.services.http_test_service import HttpTestService


class LoadAgent:
    def __init__(self, timeout_seconds: int, max_cases: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_cases = max_cases
        self.case_generator = TestCaseGenerator()
        self.http = HttpTestService(timeout_seconds)

    async def verify(self, repo: RepoConfig, commit_sha: str, openapi_document: dict) -> VerificationBundle:
        cases = self.case_generator.from_openapi(openapi_document, limit=self.max_cases)
        return await self.http.execute(repo, commit_sha, cases)
