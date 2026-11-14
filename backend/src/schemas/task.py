"""Pydantic V2 Schemas for Task Domain Slots."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCreateSlot(BaseModel):
    title: str = Field(..., min_length=1, description="Tiêu đề công việc")
    deadline: datetime | None = Field(default=None, description="Hạn chót công việc")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Mức độ ưu tiên")
    category: str = Field(default="Chung", description="Danh mục/dự án của task")
    reminder: bool = Field(default=False, description="Có bật chuông nhắc nhở không")


class TaskCompleteSlot(BaseModel):
    task_id: str | None = Field(default=None, description="ID của task cần hoàn thành")
    title: str | None = Field(default=None, description="Tên/tiêu đề task cần hoàn thành")
    completion_date: datetime = Field(default_factory=datetime.now, description="Ngày giờ hoàn thành")

    @model_validator(mode="after")
    def validate_task_identifier(self) -> "TaskCompleteSlot":
        if not (self.task_id and self.task_id.strip()) and not (self.title and self.title.strip()):
            raise ValueError("Phải cung cấp ít nhất 'task_id' hoặc 'title' để hoàn thành công việc.")
        return self


class TaskQuerySlot(BaseModel):
    time_range: str = Field(default="today", description="Khoảng thời gian: today, tomorrow, this_week, all")
    status: str = Field(default="pending", description="Trạng thái: pending, completed, all")
    priority: TaskPriority | None = Field(default=None, description="Lọc theo độ ưu tiên")


class TaskDeleteSlot(BaseModel):
    task_id: str | None = Field(default=None, description="ID của task cần xóa")
    title: str | None = Field(default=None, description="Tên/tiêu đề task cần xóa")
    requires_hitl: bool = Field(default=True, description="Thao tác xóa task luôn yêu cầu xác nhận HITL")

    @model_validator(mode="after")
    def validate_task_identifier(self) -> "TaskDeleteSlot":
        if not (self.task_id and self.task_id.strip()) and not (self.title and self.title.strip()):
            raise ValueError("Phải cung cấp ít nhất 'task_id' hoặc 'title' để xóa công việc.")
        return self


# Backwards compatibility aliases
TaskCreateSchema = TaskCreateSlot
TaskCompleteSchema = TaskCompleteSlot
TaskQuerySchema = TaskQuerySlot
TaskDeleteSchema = TaskDeleteSlot
