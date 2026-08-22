"""
دوال مخزّنة مؤقتًا (Cached) لتسريع التطبيق. Streamlit يعيد تشغيل الصفحة كاملة مع
كل تفاعل من المستخدم، فبدون تخزين مؤقت تُعاد نفس استعلامات قاعدة البيانات مرارًا.
هذه الدوال تحفظ نتائج البيانات المرجعية (الفروع، الأقسام، الأسئلة) لفترة قصيرة
لتقليل عدد مرات الوصول لقاعدة البيانات دون التأثير على حداثة البيانات بشكل ملحوظ.
"""
import streamlit as st
from database import get_session
from models import Branch, AuditSection, AuditQuestion


@st.cache_data(ttl=300, show_spinner=False)
def get_branches_cached():
    """كل الفروع (نشطة وغير نشطة) كقواميس بسيطة — تُستخدم للعرض والبحث بالاسم."""
    with get_session() as s:
        branches = s.query(Branch).order_by(Branch.id).all()
        return [{
            "id": b.id, "code": b.code, "name_ar": b.name_ar, "name_en": b.name_en,
            "region": b.region, "city": b.city, "status": b.status,
            "manager_email": b.manager_email,
        } for b in branches]


@st.cache_data(ttl=300, show_spinner=False)
def get_branches_by_id_cached():
    """قاموس {معرف الفرع: بياناته} — يلغي تكرار بناء نفس القاموس بعدة صفحات."""
    return {b["id"]: b for b in get_branches_cached()}


@st.cache_data(ttl=300, show_spinner=False)
def get_active_branches_cached():
    """الفروع النشطة فقط — تُشتق من القائمة الكاملة المخزّنة مؤقتًا (بدون استعلام قاعدة بيانات إضافي)."""
    return [{"id": b["id"], "code": b["code"], "name_ar": b["name_ar"]}
            for b in get_branches_cached() if b["status"] == "active"]


@st.cache_data(ttl=300, show_spinner=False)
def get_questions_for_version_cached(checklist_version: str):
    """أسئلة نسخة تشيك ليست معيّنة، مرتبة — بيانات مرجعية نادرًا ما تتغيّر."""
    with get_session() as s:
        questions = s.query(AuditQuestion).filter(
            AuditQuestion.checklist_version == checklist_version,
            AuditQuestion.active == True,  # noqa: E712
        ).order_by(AuditQuestion.sort_order).all()
        return [{
            "id": q.id, "section_id": q.section_id, "code": q.code,
            "question_ar": q.question_ar, "weight": q.weight, "sort_order": q.sort_order,
        } for q in questions]


@st.cache_data(ttl=300, show_spinner=False)
def get_sections_cached():
    """كل أقسام التدقيق كقاموس {id: بيانات القسم}."""
    with get_session() as s:
        sections = s.query(AuditSection).order_by(AuditSection.sort_order).all()
        return {sec.id: {"id": sec.id, "name_ar": sec.name_ar, "code": sec.code} for sec in sections}


def clear_reference_cache():
    """يمسح الكاش يدويًا فورًا بعد أي تعديل إداري (إضافة فرع/سؤال) لتجنّب عرض بيانات قديمة."""
    get_branches_cached.clear()
    get_branches_by_id_cached.clear()
    get_active_branches_cached.clear()
    get_questions_for_version_cached.clear()
    get_sections_cached.clear()
