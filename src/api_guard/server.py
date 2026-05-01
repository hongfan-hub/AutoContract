from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api_guard.config import load_config, to_public_dict
from api_guard.orchestrator import PipelineOrchestrator
from api_guard.scheduler import PollingScheduler


class RunRequest(BaseModel):
    repo_name: str
    force: bool = False


def create_app(config_path: str | Path) -> FastAPI:
    config = load_config(config_path)
    orchestrator = PipelineOrchestrator(config)
    scheduler = PollingScheduler(orchestrator)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if config.scheduler_enabled:
            await scheduler.start()
        try:
            yield
        finally:
            await scheduler.stop()

    app = FastAPI(
        title="API Guard",
        version="0.1.0",
        lifespan=lifespan,
        description="Automatic API diffing, contract reconstruction, and verification service.",
    )

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"ok": True}

    @app.get("/config")
    async def get_config() -> dict:
        return to_public_dict(config)

    @app.get("/dashboard")
    async def dashboard() -> dict:
        return orchestrator.dashboard()

    @app.post("/runs")
    async def run_pipeline(request: RunRequest) -> dict:
        if request.repo_name not in orchestrator.repo_map():
            raise HTTPException(status_code=404, detail="repo not found")
        return await orchestrator.run_for_repo(request.repo_name, force=request.force)

    @app.post("/runs/all")
    async def run_all(force: bool = False) -> dict:
        return {"results": await orchestrator.run_all(force=force)}

    return app
