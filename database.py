"""
إعداد الاتصال بقاعدة البيانات وإنشاء الجلسات (Sessions).
افتراضيًا يستخدم SQLite (ملف واحد بسيط، بدون أي تثبيت أو إعداد) — مناسب للتشغيل
المحلي المباشر بدون تعقيد. إذا احتجت PostgreSQL لاحقًا (مثلاً عند النشر أونلاين)،
يكفي تضبط DATABASE_URL في ملف .env أو st.secrets.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from models import Base

load_dotenv()


def _get_setting(key: str, default: str = "") -> str:
    """يقرأ الإعداد من متغيرات البيئة أولًا، ثم من st.secrets إن وُجد (نشر سحابي)."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


# افتراضيًا: ملف SQLite محلي باسم nxn_quality.db بجانب المشروع (صفر إعدادات)
DATABASE_URL = _get_setting("DATABASE_URL", "sqlite:///nxn_quality.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """ينشئ كل الجداول في قاعدة البيانات إن لم تكن موجودة."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session():
    """مدير سياق (context manager) لإدارة جلسة قاعدة البيانات بأمان."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
