from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models import TaskPriority, TaskStatus


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "Manager"
    team: str = "General"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    team: str

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.medium
    status: TaskStatus = TaskStatus.todo
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[date] = None


class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TimesheetCreate(BaseModel):
    employee_id: int
    task_id: Optional[int] = None
    entry_date: date
    hours: float


class TimesheetUpdate(BaseModel):
    """Used both for correcting hours and for the manager's approve/reject action."""
    hours: Optional[float] = None
    approved: Optional[bool] = None


class TimesheetRead(BaseModel):
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None
    entry_date: date
    hours: float
    approved: bool
    created_at: datetime

    class Config:
        from_attributes = True