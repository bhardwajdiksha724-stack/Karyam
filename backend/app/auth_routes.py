import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlmodel import Session, select

from app.auth import create_access_token, get_current_employee, hash_password, verify_password
from app.database import get_session
from app.models import AccessRole, Employee
from app.schemas import (
    EmployeeRead,
    GoogleAuthRequest,
    LoginRequest,
    PasswordChangeRequest,
    ProfileUpdate,
    SignupRequest,
    TokenResponse,
)

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
        access_role=data.access_role,
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


@router.post("/google", response_model=TokenResponse)
def google_login(data: GoogleAuthRequest, session: Session = Depends(get_session)):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not set on the server.")

    try:
        id_info = id_token.verify_oauth2_token(
            data.credential, google_requests.Request(), client_id
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google credential")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not verify Google credential: {e}")

    email = id_info.get("email")
    name = id_info.get("name", email)

    employee = session.exec(select(Employee).where(Employee.email == email)).first()

    if not employee:
        employee = Employee(
            name=name,
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            role="Employee",
            team="General",
            access_role=AccessRole.employee,
        )
        session.add(employee)
        session.commit()
        session.refresh(employee)

    token = create_access_token({"sub": str(employee.id), "email": employee.email})
    return TokenResponse(access_token=token)


@router.patch("/me", response_model=EmployeeRead)
def update_profile(
    data: ProfileUpdate,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Lets a user edit their own name, job title, or team. Email and
    access_role are deliberately not editable here — they're not
    self-service fields."""
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_employee, key, value)

    session.add(current_employee)
    session.commit()
    session.refresh(current_employee)
    return current_employee


@router.post("/change-password")
def change_password(
    data: PasswordChangeRequest,
    session: Session = Depends(get_session),
    current_employee: Employee = Depends(get_current_employee),
):
    """Requires the CURRENT password to change it — this stops someone who
    briefly gets access to an already-logged-in session from locking the
    real owner out by changing their password."""
    if not verify_password(data.current_password, current_employee.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    current_employee.hashed_password = hash_password(data.new_password)
    session.add(current_employee)
    session.commit()
    return {"detail": "Password updated successfully"}