from fastapi import FastAPI

from app.database import create_db_and_tables

app = FastAPI(title="Karyam API")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Karyam backend is running"}