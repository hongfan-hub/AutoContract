from __future__ import annotations

import asyncio
import contextlib

from api_guard.orchestrator import PipelineOrchestrator


class PollingScheduler:
    def __init__(self, orchestrator: PipelineOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._tasks: list[asyncio.Task] = []
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._tasks:
            return
        for repo in self.orchestrator.config.repos:
            task = asyncio.create_task(self._poll_repo(repo.name, repo.poll_interval_seconds))
            self._tasks.append(task)

    async def stop(self) -> None:
        self._stopping.set()
        for task in self._tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _poll_repo(self, repo_name: str, interval_seconds: int) -> None:
        while not self._stopping.is_set():
            try:
                await self.orchestrator.run_for_repo(repo_name, force=False)
            except Exception:
                pass
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=interval_seconds)
            except asyncio.TimeoutError:
                continue
