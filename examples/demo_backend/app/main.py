from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr


app = FastAPI(title="Demo Backend")


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    age: int = 18


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str


FAKE_DB: dict[int, dict] = {}


@app.get("/health", response_model=HealthResponse, tags=["system"], summary="Health check")
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/users", response_model=UserResponse, tags=["users"], summary="Create user")
def create_user(payload: CreateUserRequest) -> UserResponse:
    user_id = len(FAKE_DB) + 1
    record = {
        "id": user_id,
        "name": payload.name,
        "email": payload.email,
        "created_at": datetime.now(timezone.utc),
    }
    FAKE_DB[user_id] = record
    return UserResponse(**record)


@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"], summary="Get user")
def get_user(user_id: int) -> UserResponse:
    if user_id not in FAKE_DB:
        raise HTTPException(status_code=404, detail="user not found")
    return UserResponse(**FAKE_DB[user_id])
