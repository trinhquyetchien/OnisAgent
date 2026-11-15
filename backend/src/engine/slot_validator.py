"""Slot Validator and Clarification Engine for OnisAgent.

Validates required and optional slots across Finance and Task domains,
injects safe fallback defaults, and builds clarification payloads when
critical information is missing.
"""

from typing import Any
from pydantic import ValidationError

from src.schemas.base import ActionResponse, ClarificationPayload, DomainType, ExecutionStatus
from src.schemas.finance import (
    BalanceQuerySlot,
    ExpenseCreateSlot,
    IncomeCreateSlot,
    LoanCalculateSlot,
    SavingsCreateSlot,
)
from src.schemas.task import (
    TaskCompleteSlot,
    TaskCreateSlot,
    TaskDeleteSlot,
    TaskQuerySlot,
)


def _get_domain(intent: str) -> DomainType:
    if intent.startswith("finance."):
        return DomainType.FINANCE
    if intent.startswith("task."):
        return DomainType.TASK
    return DomainType.SYSTEM


class SlotValidator:
    """Validates slots against schema rules and produces ActionResponse."""

    @classmethod
    def validate(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        domain = _get_domain(intent)

        # Normalize intent name (support both raw intent and namespaced intent)
        normalized_intent = intent
        if intent in {"expense.create", "income.create", "balance.query", "loan.calculate", "savings.create"}:
            normalized_intent = f"finance.{intent}"
            domain = DomainType.FINANCE

        # Map new 32-intent naming to validation handlers
        if normalized_intent in {"finance.expense.create", "finance.add_expense"}:
            return cls._validate_expense_create(normalized_intent, slots)

        if normalized_intent in {"finance.income.create", "finance.add_income"}:
            return cls._validate_income_create(normalized_intent, slots)

        if normalized_intent in {"finance.balance.query", "finance.get_balance"}:
            return cls._validate_balance_query(normalized_intent, slots)

        if normalized_intent in {"finance.loan.calculate", "finance.loan_installment_plan"}:
            return cls._validate_loan_calculate(normalized_intent, slots)

        if normalized_intent in {"finance.savings.create", "finance.savings_goal"}:
            return cls._validate_savings_create(normalized_intent, slots)

        # ----------------- TASK DOMAIN -----------------
        if normalized_intent == "task.create":
            return cls._validate_task_create(normalized_intent, slots)

        if normalized_intent == "task.complete":
            return cls._validate_task_complete(normalized_intent, slots)

        if normalized_intent == "task.query":
            return cls._validate_task_query(normalized_intent, slots)

        if normalized_intent == "task.delete":
            return cls._validate_task_delete(normalized_intent, slots)

        # ----------------- FALLBACK / SYSTEM -----------------
        return ActionResponse(
            status=ExecutionStatus.READY,
            domain=domain,
            intent=normalized_intent,
            slots=slots,
        )

    @classmethod
    def _validate_expense_create(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        amount = slots.get("amount")
        category = slots.get("category")
        note = slots.get("note")

        if amount is None or str(amount).strip() == "":
            target_desc = note or category or "khoản này"
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="amount",
                    message=f"Bạn đã chi bao nhiêu tiền cho '{target_desc}' vậy?",
                    expected_type="currency",
                    quick_replies=["30.000₫", "45.000₫", "100.000₫", "200.000₫"],
                ),
            )

        if not category and not note:
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="category",
                    message="Khoản chi này cho nội dung hoặc danh mục gì vậy bạn?",
                    expected_type="string",
                    quick_replies=["Ăn uống", "Nhà ở", "Di chuyển", "Mua sắm", "Hóa đơn"],
                ),
            )

        try:
            validated = ExpenseCreateSlot(**slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_income_create(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        amount = slots.get("amount")
        if amount is None or str(amount).strip() == "":
            source = slots.get("source") or "khoản thu"
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="amount",
                    message=f"Bạn đã nhận được bao nhiêu tiền từ '{source}'?",
                    expected_type="currency",
                    quick_replies=["1.000.000₫", "2.000.000₫", "5.000.000₫", "10.000.000₫"],
                ),
            )

        try:
            validated = IncomeCreateSlot(**slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_balance_query(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        validated = BalanceQuerySlot(**slots)
        return ActionResponse(
            status=ExecutionStatus.READY,
            domain=DomainType.FINANCE,
            intent=intent,
            slots=validated.model_dump(),
        )

    @classmethod
    def _validate_loan_calculate(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        principal = slots.get("principal")
        term_months = slots.get("term_months")
        annual_rate = slots.get("annual_rate")

        if principal is None or str(principal).strip() == "":
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="principal",
                    message="Số tiền bạn dự định vay là bao nhiêu?",
                    expected_type="currency",
                    quick_replies=["20.000.000₫", "50.000.000₫", "100.000.000₫", "500.000.000₫"],
                ),
            )

        if term_months is None or str(term_months).strip() == "":
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="term_months",
                    message="Bạn dự định trả góp trong thời hạn bao nhiêu tháng?",
                    expected_type="integer",
                    quick_replies=["6 tháng", "12 tháng", "24 tháng", "36 tháng"],
                ),
            )

        if annual_rate is None or str(annual_rate).strip() == "":
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="annual_rate",
                    message="Lãi suất khoản vay là bao nhiêu % một năm?",
                    expected_type="percentage",
                    quick_replies=["8%/năm", "10%/năm", "12%/năm", "14%/năm"],
                ),
            )

        try:
            validated = LoanCalculateSlot(**slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_savings_create(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        goal_name = slots.get("goal_name")
        target_amount = slots.get("target_amount")

        if not goal_name or not str(goal_name).strip():
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="goal_name",
                    message="Mục tiêu hoặc tên quỹ tiết kiệm của bạn là gì?",
                    expected_type="string",
                    quick_replies=["Quỹ khẩn cấp", "Mua laptop", "Du lịch", "Mua xe"],
                ),
            )

        if target_amount is None or str(target_amount).strip() == "":
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="target_amount",
                    message=f"Mục tiêu '{goal_name}' cần đạt số tiền là bao nhiêu?",
                    expected_type="currency",
                    quick_replies=["10.000.000₫", "20.000.000₫", "50.000.000₫", "100.000.000₫"],
                ),
            )

        try:
            validated = SavingsCreateSlot(**slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.FINANCE,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_task_create(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        title = slots.get("title")
        if not title or not str(title).strip():
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="title",
                    message="Nội dung công việc hoặc việc cần nhắc nhở là gì bạn nhỉ?",
                    expected_type="string",
                    quick_replies=["Nộp báo cáo", "Họp nhóm", "Đóng tiền điện", "Gặp khách hàng"],
                ),
            )

        try:
            validated = TaskCreateSlot(**slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.TASK,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_task_complete(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        task_id = slots.get("task_id")
        title = slots.get("title") or slots.get("task_name")

        if not task_id and not title:
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="title",
                    message="Bạn muốn đánh dấu hoàn thành công việc cụ thể nào?",
                    expected_type="string",
                ),
            )

        normalized_slots = dict(slots)
        if not normalized_slots.get("title") and title:
            normalized_slots["title"] = title

        try:
            validated = TaskCompleteSlot(**normalized_slots)
            return ActionResponse(
                status=ExecutionStatus.READY,
                domain=DomainType.TASK,
                intent=intent,
                slots=validated.model_dump(),
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                message=str(err),
            )

    @classmethod
    def _validate_task_query(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        validated = TaskQuerySlot(**slots)
        return ActionResponse(
            status=ExecutionStatus.READY,
            domain=DomainType.TASK,
            intent=intent,
            slots=validated.model_dump(),
        )

    @classmethod
    def _validate_task_delete(cls, intent: str, slots: dict[str, Any]) -> ActionResponse:
        task_id = slots.get("task_id")
        title = slots.get("title") or slots.get("task_name")

        if not task_id and not title:
            return ActionResponse(
                status=ExecutionStatus.NEED_CLARIFICATION,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                clarification=ClarificationPayload(
                    intent=intent,
                    missing_slot="title",
                    message="Bạn muốn xóa công việc nào?",
                    expected_type="string",
                ),
            )

        normalized_slots = dict(slots)
        if not normalized_slots.get("title") and title:
            normalized_slots["title"] = title

        try:
            validated = TaskDeleteSlot(**normalized_slots)
            return ActionResponse(
                status=ExecutionStatus.BLOCKED,  # Requires HITL confirmation before delete
                domain=DomainType.TASK,
                intent=intent,
                slots=validated.model_dump(),
                requires_hitl=True,
                message=f"Xác nhận xóa công việc '{validated.title or validated.task_id}'?",
            )
        except (ValidationError, ValueError) as err:
            return ActionResponse(
                status=ExecutionStatus.FAILED,
                domain=DomainType.TASK,
                intent=intent,
                slots=slots,
                message=str(err),
            )
