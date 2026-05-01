# API Guard Report - demo-backend

- Commit: `3a40c082f8f6f577e9c2928abc8fc6c5a8f8066a`
- Author: `Codex Demo`
- Subject: chore: ignore pycache
- OpenAPI: `C:\Users\Eldridge\Documents\Codex\2026-05-02\api-agent-agent-agent-commit-agent\artifacts\demo-backend\3a40c082f8f6\openapi.json`
- Verification Passed: `True`
- Failed Count: `0`

## Changed Files
- `A` `.gitignore` +2/-0
- `D` `app/__pycache__/__init__.cpython-314.pyc` +0/-0
- `D` `app/__pycache__/main.cpython-314.pyc` +0/-0

## Reconstructed Routes
- `GET` `/health` -> `health`
- `POST` `/users` -> `create_user`
- `GET` `/users/{user_id}` -> `get_user`

## Verification Results
- [PASS] `GET` `/health` status=200 latency=8.66ms
- [PASS] `POST` `/users` status=200 latency=6.74ms
- [PASS] `GET` `/users/1` status=200 latency=3.66ms

## Anti Finger-Pointing Evidence
- The generated OpenAPI document is archived with the triggering commit hash.
- Every request/response payload is captured in `verification_report.json` for replay.
- The exact changed files and patches are archived in `contract_bundle.json`.