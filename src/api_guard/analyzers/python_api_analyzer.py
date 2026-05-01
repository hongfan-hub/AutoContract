from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from api_guard.models import RouteContract


HTTP_DECORATORS = {"get", "post", "put", "patch", "delete"}
MODEL_BASES = {"BaseModel"}


class PythonApiAnalyzer:
    def analyze_repo(self, repo_path: str | Path) -> list[RouteContract]:
        root = Path(repo_path)
        routes: list[RouteContract] = []
        for file_path in root.rglob("*.py"):
            if ".venv" in file_path.parts or "__pycache__" in file_path.parts:
                continue
            routes.extend(self._analyze_file(file_path))
        return routes

    def _analyze_file(self, file_path: Path) -> list[RouteContract]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        models = _collect_models(tree)
        routes: list[RouteContract] = []

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            routes.extend(_extract_routes(node, file_path, models))
        return routes


def _collect_models(tree: ast.Module) -> dict[str, dict[str, Any]]:
    models: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_expr_name(base) in MODEL_BASES for base in node.bases):
            continue

        properties: dict[str, Any] = {}
        required: list[str] = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                field_name = item.target.id
                properties[field_name] = _schema_from_annotation(item.annotation)
                if item.value is None:
                    required.append(field_name)
                elif isinstance(item.value, ast.Constant):
                    properties[field_name]["default"] = item.value.value
            elif isinstance(item, ast.Assign) and len(item.targets) == 1 and isinstance(
                item.targets[0], ast.Name
            ):
                field_name = item.targets[0].id
                properties[field_name] = {"type": "string"}
                required.append(field_name)

        models[node.name] = {
            "type": "object",
            "properties": properties,
            "required": required,
        }
    return models


def _extract_routes(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    file_path: Path,
    models: dict[str, dict[str, Any]],
) -> list[RouteContract]:
    contracts: list[RouteContract] = []
    for decorator in func.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if not isinstance(decorator.func, ast.Attribute):
            continue

        method = decorator.func.attr.lower()
        if method not in HTTP_DECORATORS:
            continue

        path_value = _literal_string(decorator.args[0]) if decorator.args else ""
        tags = _keyword_list(decorator, "tags")
        summary = _keyword_string(decorator, "summary") or ast.get_docstring(func) or ""
        response_model = _keyword_name(decorator, "response_model")
        request_model = _infer_request_model(func, models)
        response_schema = models.get(response_model) if response_model else _schema_from_annotation(
            func.returns
        )
        request_schema = models.get(request_model) if request_model else None
        path_params = _extract_path_params(func, path_value)
        contracts.append(
            RouteContract(
                path=path_value,
                methods=[method.upper()],
                handler=func.name,
                request_model=request_model,
                response_model=response_model,
                tags=tags,
                summary=summary,
                source_file=str(file_path),
                line_number=func.lineno,
                request_schema=request_schema,
                response_schema=response_schema,
                path_params=path_params,
            )
        )
    return contracts


def _infer_request_model(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    models: dict[str, dict[str, Any]],
) -> str | None:
    for arg in func.args.args:
        if arg.arg in {"self", "request"}:
            continue
        name = _annotation_name(arg.annotation)
        if name and name in models:
            return name
    return None


def _extract_path_params(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
    path_value: str,
) -> list[dict[str, Any]]:
    path_params: list[dict[str, Any]] = []
    expected_names = {segment[1:-1] for segment in path_value.split("/") if segment.startswith("{") and segment.endswith("}")}
    for arg in func.args.args:
        if arg.arg in expected_names:
            path_params.append(
                {
                    "name": arg.arg,
                    "schema": _schema_from_annotation(arg.annotation),
                    "required": True,
                }
            )
    return path_params


def _schema_from_annotation(annotation: ast.expr | None) -> dict[str, Any]:
    if annotation is None:
        return {"type": "string"}

    name = _annotation_name(annotation)
    if name in {"str", "EmailStr"}:
        schema = {"type": "string"}
        if name == "EmailStr":
            schema["format"] = "email"
        return schema
    if name in {"int"}:
        return {"type": "integer"}
    if name in {"float", "Decimal"}:
        return {"type": "number"}
    if name in {"bool"}:
        return {"type": "boolean"}
    if name in {"datetime"}:
        return {"type": "string", "format": "date-time"}
    if name in {"dict", "Dict"}:
        return {"type": "object"}
    if name in {"list", "List"}:
        if isinstance(annotation, ast.Subscript):
            return {"type": "array", "items": _schema_from_annotation(annotation.slice)}
        return {"type": "array", "items": {"type": "string"}}

    if isinstance(annotation, ast.Subscript):
        base_name = _annotation_name(annotation.value)
        if base_name in {"list", "List"}:
            return {"type": "array", "items": _schema_from_annotation(annotation.slice)}
        if base_name in {"Optional"}:
            return _schema_from_annotation(annotation.slice)

    if name:
        return {"$ref": f"#/components/schemas/{name}"}
    return {"type": "string"}


def _annotation_name(node: ast.expr | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _annotation_name(node.value)
    if isinstance(node, ast.Tuple) and node.elts:
        return _annotation_name(node.elts[0])
    return None


def _expr_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _literal_string(node: ast.expr) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _keyword_list(call: ast.Call, name: str) -> list[str]:
    for keyword in call.keywords:
        if keyword.arg != name:
            continue
        if isinstance(keyword.value, ast.List):
            values: list[str] = []
            for item in keyword.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    values.append(item.value)
            return values
    return []


def _keyword_string(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def _keyword_name(call: ast.Call, name: str) -> str | None:
    for keyword in call.keywords:
        if keyword.arg != name:
            continue
        return _annotation_name(keyword.value)
    return None
