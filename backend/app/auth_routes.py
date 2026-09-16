import os
import secrets

from fastapi import APIRouter, Depends, HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlmodel import Session, select

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_session
from app.models import AccessRole, Employee
from app.schemas import EmployeeRead, GoogleAuthRequest, LoginRequest, SignupRequest, TokenResponse

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
    """Verifies the ID token Google's Sign-In button hands back to the
    frontend, then either logs the matching account in or creates a new one
    automatically — no separate signup step needed for Google users."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not set on the server.")

    try:
        # This call verifies the token's signature, expiry, and that it was
        # really issued for OUR app (the audience check) — this is what
        # stops someone from forging a fake "Google" login.
        id_info = id_token.verify_oauth2_token(
            data.credential, google_requests.Request(), client_id
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google credential")
    except Exception as e:
        # Covers network issues reaching Google's servers, not just a bad token.
        raise HTTPException(status_code=500, detail=f"Could not verify Google credential: {e}")

    email = id_info.get("email")
    name = id_info.get("name", email)

    employee = session.exec(select(Employee).where(Employee.email == email)).first()

    if not employee:
        # First time signing in with this Google account — create an
        # account automatically. They can never log in with a password
        # since nobody (including them) knows this random one.
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