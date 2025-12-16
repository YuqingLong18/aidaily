from __future__ import annotations

import os
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine


def _default_sqlite_url() -> str:
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "nexus.db"))
    return f"sqlite:///{db_path}"


DATABASE_URL = os.getenv("DATABASE_URL", _default_sqlite_url())

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Session:
    with Session(engine) as session:
        yield session
