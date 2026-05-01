from __future__ import annotations

import time
from typing import Any

import httpx

from api_guard.models import RepoConfig, TestCase, TestResult, VerificationBundle


class HttpTestService:
    def __init__(self, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds

    async def execute(self, repo: RepoConfig, commit_sha: str, cases: list[TestCase]) -> VerificationBundle:
        results: list[TestResult] = []
        headers = {}
        if repo.auth_header_name and repo.auth_header_value:
            headers[repo.auth_header_name] = repo.auth_header_value

        async with httpx.AsyncClient(
            base_url=repo.test_base_url,
            timeout=self.timeout_seconds,
        ) as client:
            for case in cases:
                url = f"{repo.test_base_url}{case.path}"
                body: Any = case.payload
                request_headers = dict(headers)
                if body is not None:
                    request_headers["Content-Type"] = "application/json"

                started = time.perf_counter()
                try:
                    response = await client.request(
                        case.method,
                        case.path,
                        json=body if body is not None else None,
                        headers=request_headers,
                    )
                    latency_ms = (time.perf_counter() - started) * 1000
                    try:
                        response_body: Any = response.json()
                    except Exception:
                        response_body = response.text
                    results.append(
                        TestResult(
                            case=case,
                            url=url,
                            request_headers=request_headers,
                            request_body=body,
                            response_status=response.status_code,
                            response_body=response_body,
                            passed=response.status_code == case.expected_status,
                            latency_ms=latency_ms,
                        )
                    )
                except Exception as exc:
                    latency_ms = (time.perf_counter() - started) * 1000
                    results.append(
                        TestResult(
                            case=case,
                            url=url,
                            request_headers=request_headers,
                            request_body=body,
                            response_status=0,
                            response_body=None,
                            passed=False,
                            latency_ms=latency_ms,
                            error=str(exc),
                        )
                    )

        return VerificationBundle(repo=repo.name, commit_sha=commit_sha, results=results)
