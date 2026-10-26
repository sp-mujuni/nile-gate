"""Typed API and domain models for Nile Gate."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MissionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class MissionCreate(BaseModel):
    name: str = Field(min_length=3, max_length=120)
    objective: str = Field(min_length=10, max_length=2000)
    environment: str = Field(default="simulation", min_length=3, max_length=80)
    waypoints: list[str] = Field(default_factory=list, max_length=30)
    constraints: list[str] = Field(default_factory=list, max_length=30)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name", "objective", "environment")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value


class AgentReport(BaseModel):
    agent_id: str
    agent_name: str
    status: str
    summary: str
    findings: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)


class MissionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    objective: str
    environment: str
    waypoints: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: MissionStatus = MissionStatus.DRAFT
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    reports: list[AgentReport] = Field(default_factory=list)
    plan: dict[str, Any] = Field(default_factory=dict)


class EventRecord(BaseModel):
    id: int
    mission_id: str | None = None
    event_type: str
    actor: str
    payload: dict[str, Any]
    created_at: datetime
