from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RepoConfig:
    name: str
    path: Path
    test_base_url: str
    openapi_title: str
    api_management_url: str = ""
    api_management_method: str = "PUT"
    poll_interval_seconds: int = 60
    auth_header_name: str = ""
    auth_header_value: str = ""


@dataclass(slots=True)
class AppConfig:
    bind_host: str
    bind_port: int
    artifact_dir: Path
    database_path: Path
    scheduler_enabled: bool
    default_poll_interval_seconds: int
    max_cases_per_run: int
    request_timeout_seconds: int
    repos: list[RepoConfig]


@dataclass(slots=True)
class CommitInfo:
    sha: str
    author: str
    authored_at: str
    subject: str


@dataclass(slots=True)
class FileDiff:
    path: str
    status: str
    additions: int
    deletions: int
    patch: str


@dataclass(slots=True)
class RouteContract:
    path: str
    methods: list[str]
    handler: str
    request_model: str | None
    response_model: str | None
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    source_file: str = ""
    line_number: int = 1
    request_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
    path_params: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ContractBundle:
    repo: str
    commit: CommitInfo
    changed_files: list[FileDiff]
    routes: list[RouteContract]
    openapi: dict[str, Any]
    generated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class TestCase:
    name: str
    method: str
    path: str
    payload: dict[str, Any] | list[Any] | None
    expected_status: int
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TestResult:
    case: TestCase
    url: str
    request_headers: dict[str, str]
    request_body: Any
    response_status: int
    response_body: Any
    passed: bool
    latency_ms: float
    error: str = ""


@dataclass(slots=True)
class VerificationBundle:
    repo: str
    commit_sha: str
    executed_at: datetime = field(default_factory=utc_now)
    results: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def failed_count(self) -> int:
        return sum(1 for result in self.results if not result.passed)


@dataclass(slots=True)
class PipelineRun:
    repo: str
    commit_sha: str
    status: str
    started_at: datetime = field(default_factory=utc_now)
    finished_at: datetime | None = None
    openapi_path: str = ""
    report_path: str = ""
    notes: str = ""
