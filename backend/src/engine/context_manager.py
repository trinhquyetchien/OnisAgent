"""Multi-turn Session Context Manager for OnisAgent.

Maintains pending clarification requests per session, merges subsequent
user inputs into pending slots, and transitions states seamlessly.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.engine.validator import SlotValidator
from src.schemas.common import ActionResponse, ExecutionState


@dataclass
class SessionContext:
    session_id: str
    user_id: str
    current_intent: str | None = None
    accumulated_slots: dict[str, Any] = field(default_factory=dict)
    waiting_for_slot: str | None = None
    last_updated: datetime = field(default_factory=datetime.now)


class ContextManager:
    """In-memory multi-turn session storage and slot merger."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def get_session(self, session_id: str, user_id: str = "default_user") -> SessionContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(
                session_id=session_id,
                user_id=user_id,
            )
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def process_turn(
        self,
        session_id: str,
        user_id: str = "default_user",
        intent: str | None = None,
        slots: dict[str, Any] | None = None,
    ) -> ActionResponse:
        """Process a turn within a session context.

        If a session is waiting for a slot (NEED_CLARIFICATION), merges new slot
        values with previously accumulated slots.
        """
        session = self.get_session(session_id, user_id)
        new_slots = dict(slots or {})

        # If session was waiting for clarification and no new intent is provided (or same intent)
        if session.waiting_for_slot and (intent is None or intent == session.current_intent):
            active_intent = session.current_intent
            merged_slots = dict(session.accumulated_slots)
            merged_slots.update(new_slots)
        else:
            # New conversation turn or explicit intent change
            active_intent = intent or session.current_intent
            if not active_intent:
                return ActionResponse(
                    state=ExecutionState.FAILED,
                    domain=_get_domain_fallback(active_intent),
                    intent="unknown",
                    message="Không thể xác định intent cho lượt hội thoại.",
                )
            merged_slots = new_slots

        # Validate with SlotValidator
        response = SlotValidator.validate(active_intent, merged_slots)

        if response.state == ExecutionState.NEED_CLARIFICATION:
            session.current_intent = active_intent
            session.accumulated_slots = merged_slots
            session.waiting_for_slot = response.clarification.missing_slot if response.clarification else None
            session.last_updated = datetime.now()
        else:
            # READY, BLOCKED, or FAILED: Reset pending slot wait
            session.waiting_for_slot = None
            session.accumulated_slots.clear()
            session.current_intent = None
            session.last_updated = datetime.now()

        return response


def _get_domain_fallback(intent: str | None) -> Any:
    from src.schemas.common import DomainType
    if intent and intent.startswith("finance."):
        return DomainType.FINANCE
    if intent and intent.startswith("task."):
        return DomainType.TASK
    return DomainType.SYSTEM
