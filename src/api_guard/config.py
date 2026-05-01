from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib

from .models import AppConfig, RepoConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser().resolve()
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    app = data["app"]
    root = config_path.parent

    repos = [
        RepoConfig(
            name=item["name"],
            path=(root / item["path"]).resolve(),
            test_base_url=item["test_base_url"].rstrip("/"),
            openapi_title=item.get("openapi_title", item["name"]),
            api_management_url=item.get("api_management_url", ""),
            api_management_method=item.get("api_management_method", "PUT").upper(),
            poll_interval_seconds=int(
                item.get("poll_interval_seconds", app["default_poll_interval_seconds"])
            ),
            auth_header_name=item.get("auth_header_name", ""),
            auth_header_value=item.get("auth_header_value", ""),
        )
        for item in data.get("repos", [])
    ]

    return AppConfig(
        bind_host=app.get("bind_host", "127.0.0.1"),
        bind_port=int(app.get("bind_port", 8099)),
        artifact_dir=(root / app.get("artifact_dir", "./artifacts")).resolve(),
        database_path=(root / app.get("database_path", "./data/api_guard.db")).resolve(),
        scheduler_enabled=bool(app.get("scheduler_enabled", True)),
        default_poll_interval_seconds=int(app.get("default_poll_interval_seconds", 60)),
        max_cases_per_run=int(app.get("max_cases_per_run", 20)),
        request_timeout_seconds=int(app.get("request_timeout_seconds", 15)),
        repos=repos,
    )


def to_public_dict(config: AppConfig) -> dict[str, Any]:
    return {
        "bind_host": config.bind_host,
        "bind_port": config.bind_port,
        "artifact_dir": str(config.artifact_dir),
        "database_path": str(config.database_path),
        "scheduler_enabled": config.scheduler_enabled,
        "default_poll_interval_seconds": config.default_poll_interval_seconds,
        "max_cases_per_run": config.max_cases_per_run,
        "request_timeout_seconds": config.request_timeout_seconds,
        "repos": [
            {
                "name": repo.name,
                "path": str(repo.path),
                "test_base_url": repo.test_base_url,
                "openapi_title": repo.openapi_title,
                "api_management_url": repo.api_management_url,
                "api_management_method": repo.api_management_method,
                "poll_interval_seconds": repo.poll_interval_seconds,
                "auth_header_name": repo.auth_header_name,
                "auth_header_value": "***" if repo.auth_header_value else "",
            }
            for repo in config.repos
        ],
    }
