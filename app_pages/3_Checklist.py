import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_login, current_user, log_action, render_logout_sidebar
from database import get_session
from models import ChecklistVersion, AuditSection, AuditQuestion
from data_cache import clear_reference_cache
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()
can_edit = user["role"] in ("owner", "manager")


st.title(t("checklist_title"))

tab1, tab2, tab3 = st.tabs([t("tab_versions"), t("tab_sections"), t("tab_questions")])

with tab1:
    with get_session() as s:
        versions = s.query(ChecklistVersion).all()
        vdf = pd.DataFrame([{
            t("code_col"): v.code, t("name_ar_col"): v.name_ar, t("status_col"): v.status,
            t("created_by_col"): v.created_by,
        } for v in versions])
    st.dataframe(vdf, use_container_width=True, hide_index=True)

    if can_edit:
        with st.form("add_version"):
            st.write(t("add_version_title"))
            code = st.text_input(t("version_code_label"))
            name_ar = st.text_input(t("name_ar_label").replace(" *", ""))
            name_en = st.text_input(t("name_en_label").replace(" *", ""))
            status = st.selectbox(t("status_col"), ["draft", "active", "retired"])
            if st.form_submit_button(t("save")):
                with get_session() as s:
                    s.add(ChecklistVersion(code=code, name_ar=name_ar, name_en=name_en,
                                           status=status, created_by=user["email"]))
                    log_action(user["email"], "create", "checklist_version", code)
                st.success(t("updated_msg"))
                st.rerun()

with tab2:
    with get_session() as s:
        sections = s.query(AuditSection).order_by(AuditSection.sort_order).all()
        sdf = pd.DataFrame([{
            t("code_col"): sec.code, t("name_ar_col"): sec.name_ar, t("weight_col"): sec.weight,
            t("sort_order_col"): sec.sort_order, t("active_col"): sec.active,
        } for sec in sections])
    st.dataframe(sdf, use_container_width=True, hide_index=True)

    if can_edit:
        with st.form("add_section"):
            st.write(t("add_section_title"))
            code = st.text_input(t("section_code_label"))
            name_ar = st.text_input(t("name_ar_label").replace(" *", ""), key="sec_ar")
            name_en = st.text_input(t("name_en_label").replace(" *", ""), key="sec_en")
            weight = st.number_input(t("weight_label"), min_value=0, max_value=100, value=10)
            sort_order = st.number_input(t("sort_order_label"), min_value=0, value=1)
            if st.form_submit_button(t("save_section_btn")):
                with get_session() as s:
                    s.add(AuditSection(code=code, name_ar=name_ar, name_en=name_en,
                                       weight=weight, sort_order=sort_order, active=True))
                    log_action(user["email"], "create", "audit_section", code)
                clear_reference_cache()
                st.success(t("updated_msg"))
                st.rerun()

with tab3:
    with get_session() as s:
        sections_raw = {sec.id: sec for sec in s.query(AuditSection).all()}
        questions = s.query(AuditQuestion).order_by(AuditQuestion.sort_order).all()
        qdf = pd.DataFrame([{
            t("code_col"): q.code,
            t("section_col"): sections_raw[q.section_id].name_ar if q.section_id in sections_raw else "—",
            t("question_col"): q.question_ar, t("weight_col"): q.weight,
            t("checklist_version_col"): q.checklist_version, t("active_col"): q.active,
        } for q in questions])
        sections = {sec_id: {"id": sec.id, "name_ar": sec.name_ar, "code": sec.code} for sec_id, sec in sections_raw.items()}
    st.dataframe(qdf, use_container_width=True, hide_index=True)

    if can_edit and sections:
        with st.form("add_question"):
            st.write(t("add_question_title"))
            code = st.text_input(t("question_code_label"))
            sec_options = {f"{sec['name_ar']} ({sec['code']})": sec["id"] for sec in sections.values()}
            sec_choice = st.selectbox(t("section_col"), list(sec_options.keys()))
            question_ar = st.text_area(t("question_ar_label"))
            question_en = st.text_area(t("question_en_label"))
            weight = st.number_input(t("question_weight_label"), min_value=0.0, value=10.0)
            version = st.text_input(t("checklist_version_col"), value="QV1")
            if st.form_submit_button(t("save_question_btn")):
                with get_session() as s:
                    s.add(AuditQuestion(
                        section_id=sec_options[sec_choice], code=code,
                        question_ar=question_ar, question_en=question_en,
                        weight=weight, checklist_version=version, sort_order=0,
                    ))
                    log_action(user["email"], "create", "audit_question", code)
                clear_reference_cache()
                st.success(t("updated_msg"))
                st.rerun()

