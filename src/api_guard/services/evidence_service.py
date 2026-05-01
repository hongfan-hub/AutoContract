from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from api_guard.models import ContractBundle, VerificationBundle
from api_guard.services.artifact_store import ArtifactStore


class EvidenceService:
    def __init__(self, artifacts: ArtifactStore) -> None:
        self.artifacts = artifacts

    def store_contract_bundle(self, bundle: ContractBundle) -> Path:
        return self.artifacts.save_json(
            bundle.repo,
            bundle.commit.sha,
            "contract_bundle.json",
            asdict(bundle),
        )

    def store_openapi(self, bundle: ContractBundle) -> Path:
        return self.artifacts.save_json(bundle.repo, bundle.commit.sha, "openapi.json", bundle.openapi)

    def store_verification(self, bundle: VerificationBundle) -> Path:
        return self.artifacts.save_json(
            bundle.repo,
            bundle.commit_sha,
            "verification_report.json",
            asdict(bundle),
        )

    def store_human_report(
        self,
        repo: str,
        commit_sha: str,
        markdown: str,
    ) -> Path:
        return self.artifacts.save_text(repo, commit_sha, "report.md", markdown)

    def build_markdown_report(
        self,
        contract: ContractBundle,
        verification: VerificationBundle,
        openapi_path: str,
    ) -> str:
        route_lines = "\n".join(
            f"- `{','.join(route.methods)}` `{route.path}` -> `{route.handler}`"
            for route in contract.routes
        )
        result_lines = "\n".join(
            f"- [{'PASS' if result.passed else 'FAIL'}] `{result.case.method}` `{result.case.path}` "
            f"status={result.response_status} latency={result.latency_ms:.2f}ms"
            + (f" error={result.error}" if result.error else "")
            for result in verification.results
        )
        changed_files = "\n".join(
            f"- `{item.status}` `{item.path}` +{item.additions}/-{item.deletions}"
            for item in contract.changed_files
        )

        return "\n".join(
            [
                f"# API Guard Report - {contract.repo}",
                "",
                f"- Commit: `{contract.commit.sha}`",
                f"- Author: `{contract.commit.author}`",
                f"- Subject: {contract.commit.subject}",
                f"- OpenAPI: `{openapi_path}`",
                f"- Verification Passed: `{verification.passed}`",
                f"- Failed Count: `{verification.failed_count}`",
                "",
                "## Changed Files",
                changed_files or "- None",
                "",
                "## Reconstructed Routes",
                route_lines or "- None",
                "",
                "## Verification Results",
                result_lines or "- None",
                "",
                "## Anti Finger-Pointing Evidence",
                "- The generated OpenAPI document is archived with the triggering commit hash.",
                "- Every request/response payload is captured in `verification_report.json` for replay.",
                "- The exact changed files and patches are archived in `contract_bundle.json`.",
            ]
        )
