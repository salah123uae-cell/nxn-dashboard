"""
إعداد الاتصال بقاعدة البيانات وإنشاء الجلسات (Sessions).
افتراضيًا يستخدم SQLite (ملف واحد بسيط، بدون أي تثبيت أو إعداد) — مناسب للتشغيل
المحلي المباشر بدون تعقيد. إذا احتجت PostgreSQL لاحقًا (مثلاً عند النشر أونلاين)،
يكفي تضبط DATABASE_URL في ملف .env أو st.secrets.

مهم جدًا: لو تشغّل النظام على استضافة سحابية (مثل Streamlit Cloud) بدون DATABASE_URL
مضبوط بشكل صحيح، يرجع تلقائيًا لملف SQLite محلي — وهذا الملف يُمسح بالكامل مع كل
إعادة تشغيل للخادم (نشر تحديث جديد مثلًا)، فتضيع كل البيانات! لذا هذا الملف يتتبّع
صراحة هل الاتصال الفعلي ناجح بقاعدة البيانات الدائمة المضبوطة، ويعرض تحذيرًا واضحًا
لو رجع للوضع المؤقت غير الآمن — بدل ما يفشل بصمت.
"""
import os
import tempfile
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from models import Base

load_dotenv()

# تصبح True فقط لو DATABASE_URL انقرأ فعليًا من البيئة أو الأسرار (يعني قاعدة بيانات
# دائمة مضبوطة عمدًا)، و False لو رجعنا تلقائيًا لملف SQLite المؤقت الافتراضي.
IS_PERSISTENT_DB_CONFIGURED = False


def _get_setting(key: str) -> str | None:
    """يقرأ الإعداد من متغيرات البيئة أولًا، ثم من st.secrets إن وُجد (نشر سحابي).
    يرجع None صراحة لو الإعداد غير موجود بأي مصدر — لا نُخفي هذا كخطأ صامت."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # لو فشلت قراءة st.secrets لأي سبب (غير موجودة أصلًا محليًا مثلًا)، هذا متوقّع
        # فقط عند التشغيل المحلي بدون secrets.toml — لا نعتبره خطأ حقيقي هنا.
        pass
    return None


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


_configured_url = _get_setting("DATABASE_URL")
if _configured_url:
    DATABASE_URL = _configured_url
    IS_PERSISTENT_DB_CONFIGURED = True
else:
    # لا يوجد DATABASE_URL مضبوط بأي مصدر — نرجع لملف SQLite مؤقت (غير آمن على
    # الاستضافة السحابية، البيانات تُمسح مع كل إعادة تشغيل). هذا الوضع يُعرض
    # كتحذير واضح بالواجهة عبر is_persistent_db_configured() بدل ما يمر بصمت.
    DATABASE_URL = f"sqlite:///{_default_sqlite_path()}"
    IS_PERSISTENT_DB_CONFIGURED = False

# بعض مزوّدي الاستضافة (مثل Neon, Heroku, Railway) يعطون رابطًا يبدأ بـ postgres://
# لكن SQLAlchemy الحديث (2.x) يشترط postgresql:// — نصحّح الصيغة تلقائيًا هنا.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# نستخدم مكتبة psycopg (الإصدار 3) بدل psycopg2 القديمة، لأنها تدعم أحدث إصدارات
# بايثون (مثل 3.13/3.14) بعجلات (wheels) جاهزة بدون الحاجة لبناء من المصدر.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def is_persistent_db_configured() -> bool:
    """يرجع True لو قاعدة البيانات الفعلية المستخدمة هي القاعدة الدائمة المضبوطة
    (Postgres مثلًا)، و False لو النظام يعمل حاليًا على SQLite المؤقت الافتراضي
    (يعني البيانات معرّضة للضياع مع كل إعادة تشغيل للخادم)."""
    return IS_PERSISTENT_DB_CONFIGURED


def init_db():
    """ينشئ كل الجداول في قاعدة البيانات إن لم تكن موجودة، ويضيف أي أعمدة جديدة لجداول موجودة مسبقًا."""
    Base.metadata.create_all(bind=engine)
    _migrate_add_missing_columns()


def _migrate_add_missing_columns():
    """ترحيل بسيط وآمن: يضيف أعمدة جديدة لجداول قديمة إن لم تكن موجودة
    (بدون حذف أو تعديل أي بيانات حالية). يعمل مع SQLite و PostgreSQL."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    table_columns_to_add = {
        "users": [("employee_number", "VARCHAR")],
        "corrective_actions": [("overdue_notified_at", "TIMESTAMP")],
    }
    for table_name, columns in table_columns_to_add.items():
        if table_name not in inspector.get_table_names():
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for col_name, col_type in columns:
            if col_name not in existing_cols:
                try:
                    with engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                except Exception:
                    pass


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

