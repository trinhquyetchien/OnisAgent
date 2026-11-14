"""Base schemas and execution statuses for OnisAgent."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    READY = "READY"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"  # For HITL gate


class DomainType(str, Enum):
    FINANCE = "FINANCE"
    TASK = "TASK"
    SYSTEM = "SYSTEM"


class ClarificationPayload(BaseModel):
    intent: str
    missing_slot: str
    message: str
    expected_type: str = "string"
    quick_replies: list[str] = Field(default_factory=list)


class SessionContext(BaseModel):
    session_id: str
    user_id: str = "default_user"
    current_intent: str | None = None
    accumulated_slots: dict[str, Any] = Field(default_factory=dict)
    waiting_for_slot: str | None = None
    last_updated: datetime = Field(default_factory=datetime.now)


class ActionResponse(BaseModel):
    status: ExecutionStatus
    domain: DomainType
    intent: str
    slots: dict[str, Any] = Field(default_factory=dict)
    clarification: ClarificationPayload | None = None
    requires_hitl: bool = False
    message: str | None = None
