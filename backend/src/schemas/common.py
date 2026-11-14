"""Common schemas and execution states for OnisAgent."""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ExecutionState(str, Enum):
    READY = "READY"
    NEED_CLARIFICATION = "NEED_CLARIFICATION"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


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


class ActionResponse(BaseModel):
    state: ExecutionState
    domain: DomainType
    intent: str
    slots: dict[str, Any] = Field(default_factory=dict)
    clarification: ClarificationPayload | None = None
    requires_hitl: bool = False
    message: str | None = None
