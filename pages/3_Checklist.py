import streamlit as st
import pandas as pd

from auth import require_login, current_user, log_action
from database import get_session
from models import ChecklistVersion, AuditSection, AuditQuestion

st.set_page_config(page_title="قوائم الفحص", page_icon="📋", layout="wide")
require_login()
user = current_user()
can_edit = user["role"] in ("owner", "manager")

st.title("📋 قوائم الفحص (Checklist)")

tab1, tab2, tab3 = st.tabs(["نُسخ التشيك ليست", "الأقسام", "الأسئلة"])

with tab1:
    with get_session() as s:
        versions = s.query(ChecklistVersion).all()
        vdf = pd.DataFrame([{
            "الكود": v.code, "الاسم": v.name_ar, "الحالة": v.status, "أنشأها": v.created_by,
        } for v in versions])
    st.dataframe(vdf, use_container_width=True, hide_index=True)

    if can_edit:
        with st.form("add_version"):
            st.write("➕ إضافة نسخة جديدة")
            code = st.text_input("الكود (مثال: QV2)")
            name_ar = st.text_input("الاسم بالعربي")
            name_en = st.text_input("الاسم بالإنجليزي")
            status = st.selectbox("الحالة", ["draft", "active", "retired"])
            if st.form_submit_button("حفظ"):
                with get_session() as s:
                    s.add(ChecklistVersion(code=code, name_ar=name_ar, name_en=name_en,
                                           status=status, created_by=user["email"]))
                    log_action(user["email"], "create", "checklist_version", code)
                st.success("تم الحفظ ✅")
                st.rerun()

with tab2:
    with get_session() as s:
        sections = s.query(AuditSection).order_by(AuditSection.sort_order).all()
        sdf = pd.DataFrame([{
            "الكود": sec.code, "الاسم": sec.name_ar, "الوزن": sec.weight,
            "الترتيب": sec.sort_order, "مفعّل": sec.active,
        } for sec in sections])
    st.dataframe(sdf, use_container_width=True, hide_index=True)

    if can_edit:
        with st.form("add_section"):
            st.write("➕ إضافة قسم جديد")
            code = st.text_input("كود القسم")
            name_ar = st.text_input("الاسم بالعربي", key="sec_ar")
            name_en = st.text_input("الاسم بالإنجليزي", key="sec_en")
            weight = st.number_input("الوزن", min_value=0, max_value=100, value=10)
            sort_order = st.number_input("ترتيب العرض", min_value=0, value=1)
            if st.form_submit_button("حفظ القسم"):
                with get_session() as s:
                    s.add(AuditSection(code=code, name_ar=name_ar, name_en=name_en,
                                       weight=weight, sort_order=sort_order, active=True))
                    log_action(user["email"], "create", "audit_section", code)
                st.success("تم الحفظ ✅")
                st.rerun()

with tab3:
    with get_session() as s:
        sections = {sec.id: sec for sec in s.query(AuditSection).all()}
        questions = s.query(AuditQuestion).order_by(AuditQuestion.sort_order).all()
        qdf = pd.DataFrame([{
            "الكود": q.code,
            "القسم": sections[q.section_id].name_ar if q.section_id in sections else "—",
            "السؤال": q.question_ar, "الوزن": q.weight,
            "نسخة التشيك ليست": q.checklist_version, "مفعّل": q.active,
        } for q in questions])
    st.dataframe(qdf, use_container_width=True, hide_index=True)

    if can_edit and sections:
        with st.form("add_question"):
            st.write("➕ إضافة سؤال جديد")
            code = st.text_input("كود السؤال")
            sec_options = {f"{sec.name_ar} ({sec.code})": sec.id for sec in sections.values()}
            sec_choice = st.selectbox("القسم", list(sec_options.keys()))
            question_ar = st.text_area("نص السؤال بالعربي")
            question_en = st.text_area("نص السؤال بالإنجليزي")
            weight = st.number_input("وزن السؤال", min_value=0.0, value=10.0)
            version = st.text_input("نسخة التشيك ليست", value="QV1")
            if st.form_submit_button("حفظ السؤال"):
                with get_session() as s:
                    s.add(AuditQuestion(
                        section_id=sec_options[sec_choice], code=code,
                        question_ar=question_ar, question_en=question_en,
                        weight=weight, checklist_version=version, sort_order=0,
                    ))
                    log_action(user["email"], "create", "audit_question", code)
                st.success("تم الحفظ ✅")
                st.rerun()
