"""
وحدة النسخ الاحتياطي الكامل — تصدّر كل جداول النظام إلى ملف JSON واحد،
وتقدر تستعيدها لاحقًا (مثلاً عند الانتقال من SQLite إلى PostgreSQL دائمة،
أو عند الحاجة لاستعادة النظام بعد أي مشكلة).
"""
import json
import base64
from datetime import datetime, date

from sqlalchemy import DateTime, Date

from database import get_session
from models import (
    User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion,
    Audit, AuditAnswer, EvidenceFile, CorrectiveAction, ReportChangeRequest,
    Notification, AuditLog,
)

# ترتيب الجداول يهم بسبب المفاتيح الخارجية — الجداول "الأب" أولًا دائمًا
EXPORT_ORDER = [
    ("users", User),
    ("credentials", Credential),
    ("branches", Branch),
    ("checklist_versions", ChecklistVersion),
    ("audit_sections", AuditSection),
    ("audit_questions", AuditQuestion),
    ("audits", Audit),
    ("audit_answers", AuditAnswer),
    ("evidence_files", EvidenceFile),
    ("corrective_actions", CorrectiveAction),
    ("report_change_requests", ReportChangeRequest),
    ("notifications", Notification),
    ("audit_log", AuditLog),
]


def _serialize_value(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, bytes):
        return {"__bytes_b64__": base64.b64encode(v).decode("ascii")}
    return v


def export_all_data() -> bytes:
    """يصدّر كل الجداول كملف JSON واحد (نسخة احتياطية كاملة). يرجع bytes جاهزة للتنزيل."""
    data = {}
    with get_session() as s:
        for name, model in EXPORT_ORDER:
            rows = s.query(model).all()
            cols = [c.name for c in model.__table__.columns]
            data[name] = [
                {c: _serialize_value(getattr(row, c)) for c in cols}
                for row in rows
            ]
    meta = {"_exported_at": datetime.utcnow().isoformat(), "_version": 1}
    payload = {"_meta": meta, **data}
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def import_all_data(json_bytes: bytes) -> dict:
    """يستعيد نسخة احتياطية كاملة. يستبدل أي صفوف بنفس المعرّفات (merge)، ويرجع عدد الصفوف المستعادة لكل جدول."""
    data = json.loads(json_bytes.decode("utf-8"))
    counts = {}
    with get_session() as s:
        for name, model in EXPORT_ORDER:
            rows = data.get(name, [])
            col_types = {c.name: c.type for c in model.__table__.columns}
            for row in rows:
                clean_row = {}
                for k, v in row.items():
                    if k not in col_types:
                        continue
                    col_type = col_types[k]
                    if isinstance(v, dict) and "__bytes_b64__" in v:
                        v = base64.b64decode(v["__bytes_b64__"])
                    elif isinstance(v, str) and isinstance(col_type, (DateTime, Date)):
                        try:
                            v = datetime.fromisoformat(v)
                        except Exception:
                            pass
                    clean_row[k] = v
                obj = model(**clean_row)
                s.merge(obj)
            counts[name] = len(rows)
    return counts
