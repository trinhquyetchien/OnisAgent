"""Unit tests for multi-turn session context and slot merging."""

from decimal import Decimal
from src.engine.context_manager import ContextManager
from src.schemas.common import ExecutionState


def test_multiturn_clarification_merge_amount():
    manager = ContextManager()
    session_id = "test_session_1"

    # Turn 1: User says "Vừa mua trà sữa" -> Missing amount
    turn1_res = manager.process_turn(
        session_id=session_id,
        intent="finance.expense.create",
        slots={"note": "trà sữa", "category": "đồ uống"},
    )

    assert turn1_res.state == ExecutionState.NEED_CLARIFICATION
    assert turn1_res.clarification.missing_slot == "amount"

    # Turn 2: User supplements amount "45000"
    turn2_res = manager.process_turn(
        session_id=session_id,
        slots={"amount": 45000},
    )

    assert turn2_res.state == ExecutionState.READY
    assert turn2_res.slots["amount"] == Decimal("45000")
    assert turn2_res.slots["note"] == "trà sữa"
    assert turn2_res.slots["category"] == "đồ uống"
    assert turn2_res.slots["account"] == "default_account"


def test_multiturn_task_clarification_merge():
    manager = ContextManager()
    session_id = "test_session_2"

    # Turn 1: Task create without title
    turn1_res = manager.process_turn(
        session_id=session_id,
        intent="task.create",
        slots={},
    )
    assert turn1_res.state == ExecutionState.NEED_CLARIFICATION
    assert turn1_res.clarification.missing_slot == "title"

    # Turn 2: User provides title
    turn2_res = manager.process_turn(
        session_id=session_id,
        slots={"title": "Họp nhóm OnisAgent"},
    )
    assert turn2_res.state == ExecutionState.READY
    assert turn2_res.slots["title"] == "Họp nhóm OnisAgent"
    assert turn2_res.slots["category"] == "Chung"


def test_multiturn_intent_switch_clears_previous_slots():
    manager = ContextManager()
    session_id = "test_session_3"

    # Turn 1: Expense missing amount
    manager.process_turn(
        session_id=session_id,
        intent="finance.expense.create",
        slots={"note": "cà phê"},
    )

    # Turn 2: User decides to switch intent to check balance
    turn2_res = manager.process_turn(
        session_id=session_id,
        intent="finance.balance.query",
        slots={},
    )
    assert turn2_res.state == ExecutionState.READY
    assert turn2_res.slots["account"] == "all"
