"""Comprehensive unit tests for SlotValidator and Schemas."""

from decimal import Decimal
from src.engine.validator import SlotValidator
from src.schemas.common import DomainType, ExecutionState
from src.schemas.task import TaskPriority


def test_expense_create_success_with_defaults():
    slots = {"amount": 45000, "note": "trà sữa"}
    res = SlotValidator.validate("finance.expense.create", slots)

    assert res.state == ExecutionState.READY
    assert res.domain == DomainType.FINANCE
    assert res.slots["amount"] == Decimal("45000")
    assert res.slots["category"] == "Khác"
    assert res.slots["account"] == "default_account"
    assert "date" in res.slots


def test_expense_create_missing_amount_triggers_clarification():
    slots = {"note": "trà sữa"}
    res = SlotValidator.validate("finance.expense.create", slots)

    assert res.state == ExecutionState.NEED_CLARIFICATION
    assert res.clarification is not None
    assert res.clarification.missing_slot == "amount"
    assert "bao nhiêu tiền" in res.clarification.message
    assert len(res.clarification.quick_replies) > 0


def test_expense_create_missing_category_and_note():
    slots = {"amount": 50000}
    res = SlotValidator.validate("finance.expense.create", slots)

    assert res.state == ExecutionState.NEED_CLARIFICATION
    assert res.clarification is not None
    assert res.clarification.missing_slot == "category"


def test_income_create_success_and_missing_amount():
    # Success
    res = SlotValidator.validate("finance.income.create", {"amount": 15000000, "source": "lương"})
    assert res.state == ExecutionState.READY
    assert res.slots["amount"] == Decimal("15000000")
    assert res.slots["account"] == "default_account"

    # Missing amount
    res_missing = SlotValidator.validate("finance.income.create", {"source": "tiền thưởng"})
    assert res_missing.state == ExecutionState.NEED_CLARIFICATION
    assert res_missing.clarification.missing_slot == "amount"


def test_balance_query_default_all():
    res = SlotValidator.validate("finance.balance.query", {})
    assert res.state == ExecutionState.READY
    assert res.slots["account"] == "all"


def test_loan_calculate_success_and_missing_slots():
    # Success
    res = SlotValidator.validate(
        "finance.loan.calculate",
        {"principal": 50000000, "term_months": 12, "annual_rate": "10%"},
    )
    assert res.state == ExecutionState.READY
    assert res.slots["principal"] == Decimal("50000000")
    assert res.slots["term_months"] == 12
    assert res.slots["annual_rate"] == Decimal("0.10")
    assert res.slots["method"] == "reducing_balance"

    # Missing term_months
    res_missing = SlotValidator.validate(
        "finance.loan.calculate",
        {"principal": 50000000, "annual_rate": 0.1},
    )
    assert res_missing.state == ExecutionState.NEED_CLARIFICATION
    assert res_missing.clarification.missing_slot == "term_months"


def test_savings_create_success_and_missing_goal():
    # Success
    res = SlotValidator.validate(
        "finance.savings.create",
        {"goal_name": "Quỹ mua laptop", "target_amount": 25000000},
    )
    assert res.state == ExecutionState.READY
    assert res.slots["goal_name"] == "Quỹ mua laptop"
    assert res.slots["target_amount"] == Decimal("25000000")
    assert res.slots["deadline"] is None

    # Missing goal_name
    res_missing = SlotValidator.validate("finance.savings.create", {"target_amount": 25000000})
    assert res_missing.state == ExecutionState.NEED_CLARIFICATION
    assert res_missing.clarification.missing_slot == "goal_name"


def test_task_create_success_with_defaults():
    slots = {"title": "Nộp slide đồ án AI4Life"}
    res = SlotValidator.validate("task.create", slots)

    assert res.state == ExecutionState.READY
    assert res.domain == DomainType.TASK
    assert res.slots["title"] == "Nộp slide đồ án AI4Life"
    assert res.slots["priority"] == TaskPriority.MEDIUM
    assert res.slots["category"] == "Chung"
    assert res.slots["deadline"] is None


def test_task_create_missing_title():
    res = SlotValidator.validate("task.create", {})
    assert res.state == ExecutionState.NEED_CLARIFICATION
    assert res.clarification.missing_slot == "title"


def test_task_complete_and_delete_with_hitl():
    # Complete
    res_comp = SlotValidator.validate("task.complete", {"title": "Báo cáo"})
    assert res_comp.state == ExecutionState.READY

    # Delete (HITL gate)
    res_del = SlotValidator.validate("task.delete", {"title": "Báo cáo"})
    assert res_del.state == ExecutionState.BLOCKED
    assert res_del.requires_hitl is True
