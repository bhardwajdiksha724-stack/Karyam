from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_session
from app.models import Employee
from app.schemas import EmployeeRead, LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=EmployeeRead)
def signup(data: SignupRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(Employee).where(Employee.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = Employee(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        team=data.team,
    )
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    employee = session.exec(select(Employee).where(Employee.email == data.email)).first()
    if not employee or not verify_password(data.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(employee.id), "email": employee.email})
    return TokenResponse(access_token=token)