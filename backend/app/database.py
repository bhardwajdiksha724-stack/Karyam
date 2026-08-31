import os

from sqlmodel import SQLModel, Session, create_engine

# In production you'd set this via a real environment variable / secret.
# For local dev it defaults to the Postgres instance you create below.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://karyam_user:karyam_dev_pass@localhost:5432/karyam",
)

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    """Creates all tables defined by our SQLModel models, if they don't exist yet."""
    from app import models  # noqa: F401 — import registers tables with metadata

    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — gives each request its own DB session."""
    with Session(engine) as session:
        yield session