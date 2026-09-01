from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_employee
from app.database import get_session
from app.models import Employee, Task, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_task_read(task: Task, session: Session) -> TaskRead:
    """Attaches the assignee's name to a task so the frontend doesn't have to
    make a separate lookup for every task it displays."""
    assignee_name = None
    if task.assignee_id:
        assignee = session.get(Employee, task.assignee_id)
        assignee_name = assignee.name if assignee else None
    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        priority=task.priority,
        status=task.status,
        due_date=task.due_date,
        created_at=task.created_at,
    )


@router.post("", response_model=TaskRead)
def create_task(
    data: TaskCreate,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    task = Task(**data.dict())
    session.add(task)
    session.commit()
    session.refresh(task)
    return _to_task_read(task, session)


@router.get("", response_model=List[TaskRead])
def list_tasks(
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Any logged-in manager can see all tasks. Optional filters via query
    params, e.g. GET /tasks?status=todo or GET /tasks?assignee_id=3"""
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    if assignee_id:
        query = query.where(Task.assignee_id == assignee_id)
    tasks = session.exec(query).all()
    return [_to_task_read(t, session) for t in tasks]


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _to_task_read(task, session)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return _to_task_read(task, session)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"detail": "Task deleted"}