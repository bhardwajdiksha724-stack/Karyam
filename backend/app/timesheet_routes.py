from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import get_current_employee
from app.database import get_session
from app.models import AccessRole, Employee, Task, TimesheetEntry
from app.schemas import TimesheetCreate, TimesheetRead, TimesheetUpdate

router = APIRouter(prefix="/timesheets", tags=["timesheets"])


def _to_timesheet_read(entry: TimesheetEntry, session: Session) -> TimesheetRead:
    employee = session.get(Employee, entry.employee_id)
    task = session.get(Task, entry.task_id) if entry.task_id else None
    return TimesheetRead(
        id=entry.id,
        employee_id=entry.employee_id,
        employee_name=employee.name if employee else None,
        task_id=entry.task_id,
        task_title=task.title if task else None,
        entry_date=entry.entry_date,
        hours=entry.hours,
        approved=entry.approved,
        created_at=entry.created_at,
    )


@router.post("", response_model=TimesheetRead)
def create_entry(
    data: TimesheetCreate,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Managers can log an entry for anyone. Regular employees can only log
    entries for themselves."""
    if current_employee.access_role != AccessRole.manager and data.employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="You can only log timesheet entries for yourself")

    entry = TimesheetEntry(**data.dict())
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _to_timesheet_read(entry, session)


@router.get("", response_model=List[TimesheetRead])
def list_entries(
    employee_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    approved: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    query = select(TimesheetEntry)
    if employee_id:
        query = query.where(TimesheetEntry.employee_id == employee_id)
    if start_date:
        query = query.where(TimesheetEntry.entry_date >= start_date)
    if end_date:
        query = query.where(TimesheetEntry.entry_date <= end_date)
    if approved is not None:
        query = query.where(TimesheetEntry.approved == approved)
    entries = session.exec(query).all()
    return [_to_timesheet_read(e, session) for e in entries]


@router.patch("/{entry_id}", response_model=TimesheetRead)
def update_entry(
    entry_id: int,
    data: TimesheetUpdate,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Approving/rejecting a timesheet requires manager access. A regular
    employee may only correct the `hours` on their OWN entry — they can
    never approve their own (or anyone's) timesheet."""
    entry = session.get(TimesheetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")

    update_data = data.dict(exclude_unset=True)
    is_manager = current_employee.access_role == AccessRole.manager

    if "approved" in update_data and not is_manager:
        raise HTTPException(status_code=403, detail="Only a manager can approve or reject timesheets")

    if not is_manager and entry.employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="You can only edit your own timesheet entries")

    for key, value in update_data.items():
        setattr(entry, key, value)

    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _to_timesheet_read(entry, session)


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: int,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Managers can delete any entry. Employees can only delete their own."""
    entry = session.get(TimesheetEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Timesheet entry not found")

    if current_employee.access_role != AccessRole.manager and entry.employee_id != current_employee.id:
        raise HTTPException(status_code=403, detail="You can only delete your own timesheet entries")

    session.delete(entry)
    session.commit()
    return {"detail": "Timesheet entry deleted"}
