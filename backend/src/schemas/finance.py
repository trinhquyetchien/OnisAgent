"""Pydantic V2 Schemas for Finance Domain."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


class ExpenseCreateSchema(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Số tiền chi tiêu (> 0)")
    category: str | None = Field(default=None, description="Danh mục chi")
    note: str | None = Field(default=None, description="Ghi chú chi")
    account: str = Field(default="default_account", description="Tài khoản/ví chi")
    date: datetime = Field(default_factory=datetime.now, description="Thời điểm chi")
    payment_method: str | None = Field(default=None, description="Phương thức thanh toán")

    @model_validator(mode="after")
    def validate_category_or_note(self) -> "ExpenseCreateSchema":
        if not (self.category and self.category.strip()) and not (self.note and self.note.strip()):
            raise ValueError("Phải có ít nhất 'category' hoặc 'note' cho khoản chi.")
        if not self.category and self.note:
            self.category = "Khác"
        return self


class IncomeCreateSchema(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Số tiền thu nhập (> 0)")
    source: str = Field(default="Thu nhập khác", description="Nguồn thu nhập")
    account: str = Field(default="default_account", description="Tài khoản nhận")
    date: datetime = Field(default_factory=datetime.now, description="Thời điểm nhận")


class BalanceQuerySchema(BaseModel):
    account: str = Field(default="all", description="Tài khoản cần tra cứu (mặc định 'all')")


class LoanCalculateSchema(BaseModel):
    principal: Decimal = Field(..., gt=0, description="Số tiền gốc vay (> 0)")
    term_months: int = Field(..., gt=0, description="Thời hạn vay (tháng)")
    annual_rate: Decimal = Field(..., gt=0, description="Lãi suất năm (thập phân hoặc %, vd: 0.12 hoặc 12)")
    method: str = Field(default="reducing_balance", description="Phương thức tính lãi: reducing_balance / straight_line")
    purpose: str | None = Field(default=None, description="Mục đích vay")

    @field_validator("annual_rate", mode="before")
    @classmethod
    def normalize_rate(cls, v: Any) -> Decimal:
        raw_str = str(v).strip().rstrip("%").strip()
        rate = Decimal(raw_str)
        if rate > 1:
            rate = rate / Decimal("100")
        return rate


class SavingsCreateSchema(BaseModel):
    goal_name: str = Field(..., min_length=1, description="Tên mục tiêu tiết kiệm")
    target_amount: Decimal = Field(..., gt=0, description="Số tiền mục tiêu (> 0)")
    deadline: datetime | None = Field(default=None, description="Hạn chót hoàn thành")
    monthly_contribution: Decimal | None = Field(default=None, gt=0, description="Đóng góp hàng tháng dự kiến")
