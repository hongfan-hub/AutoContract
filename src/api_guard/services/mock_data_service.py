from __future__ import annotations

from typing import Any


class MockDataService:
    def generate(self, schema: dict[str, Any] | None) -> Any:
        if not schema:
            return None

        schema_type = schema.get("type")
        if "default" in schema:
            return schema["default"]
        if "example" in schema:
            return schema["example"]
        if "enum" in schema and schema["enum"]:
            return schema["enum"][0]

        if schema_type == "object":
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            payload: dict[str, Any] = {}
            for name, child in properties.items():
                if name in required or child.get("default") is not None:
                    payload[name] = self.generate(child)
            return payload

        if schema_type == "array":
            return [self.generate(schema.get("items", {}))]
        if schema_type == "integer":
            return 1
        if schema_type == "number":
            return 1.0
        if schema_type == "boolean":
            return True
        if schema_type == "string":
            fmt = schema.get("format")
            if fmt == "email":
                return "demo@example.com"
            if fmt == "date-time":
                return "2026-01-01T00:00:00Z"
            return "demo"

        if "$ref" in schema:
            return {}
        return None
