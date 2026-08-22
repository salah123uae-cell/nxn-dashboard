"""Database connection and transactional session management."""
import os
import tempfile
from contextlib import contextmanager
from functools import lru_cache

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base

load_dotenv()


def _get_setting(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value:
        return value
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def _default_sqlite_path() -> str:
    candidates = [os.getcwd(), os.path.expanduser("~"), tempfile.gettempdir()]
    for directory in candidates:
        try:
            test_file = os.path.join(directory, ".write_test_tmp")
            with open(test_file, "w", encoding="utf-8") as handle:
                handle.write("x")
            os.remove(test_file)
            return os.path.join(directory, "nxn_quality.db").replace("\\", "/")
        except Exception:
            continue
    return os.path.join(tempfile.gettempdir(), "nxn_quality.db").replace("\\", "/")


APP_ENV = _get_setting("APP_ENV", "development").strip().lower()
configured_database_url = _get_setting("DATABASE_URL")

if APP_ENV in {"production", "prod"}:
    if not configured_database_url:
        raise RuntimeError("DATABASE_URL is required in production; refusing SQLite fallback")
    if not configured_database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")):
        raise RuntimeError("Production DATABASE_URL must use PostgreSQL")

DATABASE_URL = configured_database_url or f"sqlite:///{_default_sqlite_path()}"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql+psycopg2://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_options = {"pool_pre_ping": True, "connect_args": connect_args}
if DATABASE_URL.startswith("postgresql"):
    engine_options.update(pool_size=5, max_overflow=10, pool_timeout=10, pool_recycle=300)
engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@lru_cache(maxsize=1)
def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
