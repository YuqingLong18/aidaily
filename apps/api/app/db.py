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


def _migrate_sqlite_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return
    import sqlite3

    # Ensure new optional bilingual columns exist without requiring a destructive migration.
    db_path = DATABASE_URL.replace("sqlite:///", "", 1)
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA table_info(item)")
        existing = {row[1] for row in cur.fetchall()}

        desired = {
            "title_zh": "TEXT",
            "tags_zh_csv": "TEXT NOT NULL DEFAULT ''",
            "summary_bullets_zh_md": "TEXT NOT NULL DEFAULT ''",
            "why_it_matters_zh_md": "TEXT NOT NULL DEFAULT ''",
            "market_impact_zh_md": "TEXT NOT NULL DEFAULT ''",
        }

        for col, ddl in desired.items():
            if col in existing:
                continue
            cur.execute(f"ALTER TABLE item ADD COLUMN {col} {ddl}")
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate_sqlite_schema()


@contextmanager
def session_scope() -> Session:
    with Session(engine) as session:
        yield session
