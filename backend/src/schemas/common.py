"""Common schemas and execution states for OnisAgent."""

from src.schemas.base import (
    ActionResponse,
    ClarificationPayload,
    DomainType,
    ExecutionStatus,
    SessionContext,
)

# Backwards compatibility alias
ExecutionState = ExecutionStatus

__all__ = [
    "ExecutionStatus",
    "ExecutionState",
    "DomainType",
    "ClarificationPayload",
    "SessionContext",
    "ActionResponse",
]
