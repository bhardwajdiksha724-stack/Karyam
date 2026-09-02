from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_current_employee
from app.auth_routes import router as auth_router
from app.database import create_db_and_tables
from app.employee_routes import router as employee_router
from app.models import Employee
from app.schemas import EmployeeRead
from app.task_routes import router as task_router
from app.timesheet_routes import router as timesheet_router

app = FastAPI(title="Karyam API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(task_router)
app.include_router(timesheet_router)
app.include_router(employee_router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Karyam backend is running"}


@app.get("/auth/me", response_model=EmployeeRead)
def read_current_employee(current_employee: Employee = Depends(get_current_employee)):
    """Proves the token-based auth works — returns whoever's token you send."""
    return current_employee