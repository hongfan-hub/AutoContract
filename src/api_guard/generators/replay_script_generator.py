from __future__ import annotations

import json
from typing import Iterable

from api_guard.models import TestResult


class ReplayScriptGenerator:
    def build(self, base_url: str, results: Iterable[TestResult]) -> str:
        lines = [
            "import json",
            "import requests",
            "",
            f'BASE_URL = "{base_url}"',
            "",
        ]
        for index, result in enumerate(results, start=1):
            variable = f"payload_{index}"
            payload_json = json.dumps(result.request_body, ensure_ascii=False)
            lines.extend(
                [
                    f"{variable} = {payload_json}",
                    (
                        f'response = requests.request("{result.case.method}", '
                        f'BASE_URL + "{result.case.path}", '
                        f"json={variable}, headers={json.dumps(result.request_headers, ensure_ascii=False)})"
                    ),
                    f'print("{result.case.method} {result.case.path}", response.status_code, response.text)',
                    "",
                ]
            )
        return "\n".join(lines)
