from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth import get_current_employee
from app.database import get_session
from app.models import Employee
from app.schemas import EmployeeRead

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=List[EmployeeRead])
def list_employees(
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    employees = session.exec(select(Employee)).all()
    return employees