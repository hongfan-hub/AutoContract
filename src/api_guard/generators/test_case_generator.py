from __future__ import annotations

import re
from typing import Any

from api_guard.models import TestCase
from api_guard.services.mock_data_service import MockDataService


class TestCaseGenerator:
    def __init__(self) -> None:
        self.mock_data = MockDataService()

    def from_openapi(self, document: dict[str, Any], limit: int = 20) -> list[TestCase]:
        cases: list[TestCase] = []
        paths: dict[str, Any] = document.get("paths", {})
        for path, operations in paths.items():
            for method, operation in operations.items():
                rendered_path = _render_path(path, operation.get("parameters", []), self.mock_data)
                request_schema = (
                    operation.get("requestBody", {})
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema")
                )
                payload = self.mock_data.generate(request_schema)
                expected_status = _expected_status(operation.get("responses", {}))
                cases.append(
                    TestCase(
                        name=operation.get("operationId", f"{method}_{path}"),
                        method=method.upper(),
                        path=rendered_path,
                        payload=payload,
                        expected_status=expected_status,
                        tags=operation.get("tags", []),
                    )
                )
                if len(cases) >= limit:
                    return cases
        return cases


def _expected_status(responses: dict[str, Any]) -> int:
    for key in responses:
        if key.isdigit():
            return int(key)
    return 200


def _render_path(path: str, parameters: list[dict[str, Any]], mock_data: MockDataService) -> str:
    rendered = path
    for item in parameters:
        if item.get("in") != "path":
            continue
        name = item["name"]
        schema = item.get("schema", {})
        value = mock_data.generate(schema)
        if value is None:
            value = "demo"
        rendered = rendered.replace(f"{{{name}}}", str(value))
    return re.sub(r"{[^}]+}", "demo", rendered)
