from __future__ import annotations

from collections import defaultdict
from typing import Any

from api_guard.models import CommitInfo, RouteContract


class OpenApiGenerator:
    def build(
        self,
        title: str,
        repo_name: str,
        commit: CommitInfo,
        routes: list[RouteContract],
    ) -> dict[str, Any]:
        paths: dict[str, Any] = defaultdict(dict)
        components: dict[str, Any] = {"schemas": {}}

        for route in routes:
            operation = {
                "summary": route.summary or f"{route.methods[0]} {route.path}",
                "operationId": route.handler,
                "tags": route.tags or ["default"],
                "x-source-file": route.source_file,
                "x-source-line": route.line_number,
                "parameters": [
                    {
                        "name": item["name"],
                        "in": "path",
                        "required": item["required"],
                        "schema": _materialize_schema(item["schema"], components),
                    }
                    for item in route.path_params
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": _materialize_schema(route.response_schema, components)
                            }
                        },
                    }
                },
            }
            if route.request_schema:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": _materialize_schema(route.request_schema, components)
                        }
                    },
                }
            paths[route.path][route.methods[0].lower()] = operation

        return {
            "openapi": "3.1.0",
            "info": {
                "title": title,
                "version": commit.sha[:12],
                "description": (
                    f"Auto-reconstructed spec for repo {repo_name} from commit {commit.sha}."
                ),
            },
            "servers": [],
            "paths": dict(paths),
            "components": components,
            "x-generated-from": {
                "repo": repo_name,
                "commit_sha": commit.sha,
                "commit_author": commit.author,
                "commit_subject": commit.subject,
                "authored_at": commit.authored_at,
            },
        }


def _materialize_schema(schema: dict[str, Any] | None, components: dict[str, Any]) -> dict[str, Any]:
    if not schema:
        return {"type": "object"}
    if "$ref" in schema:
        return schema

    result: dict[str, Any] = dict(schema)
    properties = result.get("properties")
    if isinstance(properties, dict):
        mapped: dict[str, Any] = {}
        for name, child in properties.items():
            child_schema = _materialize_schema(child, components)
            mapped[name] = child_schema
            if "$ref" in child_schema:
                ref_name = child_schema["$ref"].split("/")[-1]
                components["schemas"].setdefault(ref_name, {"type": "object"})
        result["properties"] = mapped

    if result.get("type") == "array" and isinstance(result.get("items"), dict):
        result["items"] = _materialize_schema(result["items"], components)

    return result
