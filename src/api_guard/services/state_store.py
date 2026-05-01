from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from api_guard.models import PipelineRun
from api_guard.utils.fs import ensure_dir
from api_guard.utils.time_utils import now_iso


class StateStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        ensure_dir(self.database_path.parent)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS repo_state (
                    repo_name TEXT PRIMARY KEY,
                    last_commit_sha TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_name TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    openapi_path TEXT,
                    report_path TEXT,
                    notes TEXT
                )
                """
            )

    def get_last_commit(self, repo_name: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT last_commit_sha FROM repo_state WHERE repo_name = ?",
                (repo_name,),
            ).fetchone()
        return row[0] if row else None

    def set_last_commit(self, repo_name: str, sha: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO repo_state (repo_name, last_commit_sha, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(repo_name) DO UPDATE SET
                    last_commit_sha = excluded.last_commit_sha,
                    updated_at = excluded.updated_at
                """,
                (repo_name, sha, now_iso()),
            )

    def create_run(self, run: PipelineRun) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO pipeline_runs (
                    repo_name, commit_sha, status, started_at, finished_at, openapi_path, report_path, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.repo,
                    run.commit_sha,
                    run.status,
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.openapi_path,
                    run.report_path,
                    run.notes,
                ),
            )
            return int(cursor.lastrowid)

    def finish_run(
        self,
        run_id: int,
        status: str,
        openapi_path: str = "",
        report_path: str = "",
        notes: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE pipeline_runs
                SET status = ?, finished_at = ?, openapi_path = ?, report_path = ?, notes = ?
                WHERE id = ?
                """,
                (status, now_iso(), openapi_path, report_path, notes, run_id),
            )

    def recent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, repo_name, commit_sha, status, started_at, finished_at, openapi_path, report_path, notes
                FROM pipeline_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "id": row[0],
                "repo_name": row[1],
                "commit_sha": row[2],
                "status": row[3],
                "started_at": row[4],
                "finished_at": row[5],
                "openapi_path": row[6],
                "report_path": row[7],
                "notes": row[8],
            }
            for row in rows
        ]
