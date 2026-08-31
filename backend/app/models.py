from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class EmployeeStatus(str, Enum):
    active = "active"
    on_leave = "on_leave"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str  # e.g. "Manager", "Developer", "Designer"
    team: str
    status: EmployeeStatus = EmployeeStatus.active
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    priority: TaskPriority = TaskPriority.medium
    status: TaskStatus = TaskStatus.todo
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TimesheetEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    task_id: Optional[int] = Field(default=None, foreign_key="task.id")
    entry_date: date
    hours: float
    approved: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)