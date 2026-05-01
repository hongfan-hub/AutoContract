from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from api_guard.agents.contract_agent import ContractAgent
from api_guard.agents.load_agent import LoadAgent
from api_guard.agents.sniffer_agent import SnifferAgent
from api_guard.config import AppConfig
from api_guard.generators.replay_script_generator import ReplayScriptGenerator
from api_guard.models import PipelineRun, RepoConfig
from api_guard.publishers.api_management import ApiManagementPublisher
from api_guard.services.artifact_store import ArtifactStore
from api_guard.services.evidence_service import EvidenceService
from api_guard.services.state_store import StateStore


class PipelineOrchestrator:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state_store = StateStore(config.database_path)
        self.artifacts = ArtifactStore(config.artifact_dir)
        self.evidence = EvidenceService(self.artifacts)
        self.sniffer = SnifferAgent(self.state_store)
        self.contract = ContractAgent()
        self.load = LoadAgent(config.request_timeout_seconds, config.max_cases_per_run)
        self.publisher = ApiManagementPublisher()
        self.replay = ReplayScriptGenerator()

    def repo_map(self) -> dict[str, RepoConfig]:
        return {repo.name: repo for repo in self.config.repos}

    async def run_for_repo(self, repo_name: str, force: bool = False) -> dict:
        repo = self.repo_map()[repo_name]
        commit, changed_files, has_changed = self.sniffer.sniff(repo)
        if not has_changed and not force:
            return {
                "repo": repo.name,
                "commit_sha": commit.sha,
                "status": "skipped",
                "reason": "no_new_commit",
            }

        run_id = self.state_store.create_run(
            PipelineRun(repo=repo.name, commit_sha=commit.sha, status="running")
        )
        try:
            contract_bundle = self.contract.build(repo, commit, changed_files)
            contract_bundle_path = self.evidence.store_contract_bundle(contract_bundle)
            openapi_path = self.evidence.store_openapi(contract_bundle)
            publish_status = await self.publisher.publish(repo, contract_bundle.openapi)

            verification_bundle = await self.load.verify(repo, commit.sha, contract_bundle.openapi)
            verification_path = self.evidence.store_verification(verification_bundle)
            replay_script = self.replay.build(repo.test_base_url, verification_bundle.results)
            replay_path = self.artifacts.save_text(repo.name, commit.sha, "replay_requests.py", replay_script)

            report_markdown = self.evidence.build_markdown_report(
                contract_bundle,
                verification_bundle,
                str(openapi_path),
            )
            report_path = self.evidence.store_human_report(repo.name, commit.sha, report_markdown)

            self.state_store.set_last_commit(repo.name, commit.sha)
            final_status = "passed" if verification_bundle.passed else "failed"
            notes = (
                f"publish={publish_status}; contract={contract_bundle_path.name}; "
                f"verification={verification_path.name}; replay={replay_path.name}"
            )
            self.state_store.finish_run(
                run_id,
                final_status,
                openapi_path=str(openapi_path),
                report_path=str(report_path),
                notes=notes,
            )
            return {
                "repo": repo.name,
                "commit_sha": commit.sha,
                "status": final_status,
                "publish_status": publish_status,
                "artifacts": {
                    "contract_bundle": str(contract_bundle_path),
                    "openapi": str(openapi_path),
                    "verification": str(verification_path),
                    "report": str(report_path),
                    "replay_script": str(replay_path),
                },
                "summary": {
                    "route_count": len(contract_bundle.routes),
                    "changed_file_count": len(contract_bundle.changed_files),
                    "test_count": len(verification_bundle.results),
                    "failed_count": verification_bundle.failed_count,
                },
            }
        except Exception as exc:
            self.state_store.finish_run(run_id, "error", notes=str(exc))
            raise

    async def run_all(self, force: bool = False) -> list[dict]:
        results = []
        for repo in self.config.repos:
            results.append(await self.run_for_repo(repo.name, force=force))
        return results

    def dashboard(self) -> dict:
        return {
            "repos": [_repo_dict(repo) for repo in self.config.repos],
            "recent_runs": self.state_store.recent_runs(),
        }


def _repo_dict(repo: RepoConfig) -> dict:
    data = asdict(repo)
    for key, value in list(data.items()):
        if isinstance(value, Path):
            data[key] = str(value)
    return data
