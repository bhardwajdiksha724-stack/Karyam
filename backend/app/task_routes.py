from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_employee, require_manager
from app.database import get_session
from app.models import AccessRole, Employee, Task, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_task_read(task: Task, session: Session) -> TaskRead:
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
    current_employee: Employee = Depends(require_manager),
):
    """Only managers can create tasks."""
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
    """Everyone can see the full board — visibility isn't restricted, only
    who can create/edit/delete is."""
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
    """Managers can update any field on any task. A regular employee can
    ONLY change the status of a task assigned to them (e.g. dragging their
    own card between columns) — nothing else, and not other people's tasks."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.dict(exclude_unset=True)

    if current_employee.access_role != AccessRole.manager:
        if task.assignee_id != current_employee.id:
            raise HTTPException(
                status_code=403,
                detail="You can only update the status of tasks assigned to you",
            )
        if set(update_data.keys()) - {"status"}:
            raise HTTPException(
                status_code=403,
                detail="You can only change a task's status, not its other fields",
            )

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
    current_employee: Employee = Depends(require_manager),
):
    """Only managers can delete tasks."""
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"detail": "Task deleted"}