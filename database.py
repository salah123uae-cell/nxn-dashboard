"""
إعداد الاتصال بقاعدة البيانات وإنشاء الجلسات (Sessions).
افتراضيًا يستخدم SQLite (ملف واحد بسيط، بدون أي تثبيت أو إعداد) — مناسب للتشغيل
المحلي المباشر بدون تعقيد. إذا احتجت PostgreSQL لاحقًا (مثلاً عند النشر أونلاين)،
يكفي تضبط DATABASE_URL في ملف .env أو st.secrets.
"""
import os
import tempfile
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


def _default_sqlite_path() -> str:
    """
    يبحث عن أول مجلد قابل للكتابة فعليًا (مجلد المشروع، ثم المجلد الشخصي،
    ثم المجلد المؤقت للنظام). هذا ضروري لأن بعض بيئات الاستضافة السحابية
    (مثل Streamlit Cloud) تكون فيها مجلد المشروع نفسه للقراءة فقط.
    """
    candidates = [os.getcwd(), os.path.expanduser("~"), tempfile.gettempdir()]
    for d in candidates:
        try:
            test_file = os.path.join(d, ".write_test_tmp")
            with open(test_file, "w") as f:
                f.write("x")
            os.remove(test_file)
            return os.path.join(d, "nxn_quality.db").replace("\\", "/")
        except Exception:
            continue
    return os.path.join(tempfile.gettempdir(), "nxn_quality.db").replace("\\", "/")


# افتراضيًا: ملف SQLite في أول مجلد قابل للكتابة (صفر إعدادات، ويعمل محليًا وسحابيًا)
DATABASE_URL = _get_setting("DATABASE_URL", f"sqlite:///{_default_sqlite_path()}")

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
