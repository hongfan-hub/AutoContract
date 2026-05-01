from __future__ import annotations

from typing import Any

import httpx

from api_guard.models import RepoConfig


class ApiManagementPublisher:
    async def publish(self, repo: RepoConfig, openapi_document: dict[str, Any]) -> str:
        if not repo.api_management_url:
            return "skipped:no_api_management_url"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(
                repo.api_management_method,
                repo.api_management_url,
                json=openapi_document,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
        return f"published:{response.status_code}"
