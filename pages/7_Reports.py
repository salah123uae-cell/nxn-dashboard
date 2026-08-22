import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_login, render_logout_sidebar
from database import get_session
from models import Audit, AuditAnswer, AuditQuestion
from utils import export_audit_report_pdf, export_audits_to_excel
from data_cache import get_branches_cached
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Reports | التقارير", page_icon="📈", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_login()
render_logout_sidebar()

st.title(t("reports_title"))
branches_by_id = {branch["id"]: branch for branch in get_branches_cached()}

with get_session() as session:
    audits = session.query(
        Audit.id, Audit.reference, Audit.branch_id,
    ).filter(
        Audit.status.in_(["submitted", "reviewed", "closed"])
    ).order_by(Audit.created_at.desc()).limit(500).all()

if not audits:
    st.info(t("no_submitted_audits"))
else:
    options = {
        f"{audit.reference} - {branches_by_id.get(audit.branch_id, {}).get('name_ar', '')}": audit.id
        for audit in audits
    }
    choice = st.selectbox(t("select_audit_report"), list(options))
    audit_id = options[choice]

    with get_session() as session:
        audit = session.get(Audit, audit_id)
        answers = session.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()
        question_ids = [answer.question_id for answer in answers]
        questions = {
            question.id: question for question in session.query(AuditQuestion).filter(
                AuditQuestion.id.in_(question_ids)
            ).all()
        } if question_ids else {}

        answers_rows = [{
            "question": questions[answer.question_id].question_ar if answer.question_id in questions else "—",
            "answer": answer.answer,
            "weight": questions[answer.question_id].weight if answer.question_id in questions else 0,
            "note": answer.note,
        } for answer in answers]

        branch_info = branches_by_id.get(audit.branch_id)
        audit_info = {
            "reference": audit.reference,
            "branch_name": branch_info["name_ar"] if branch_info else "—",
            "auditor_email": audit.auditor_email,
            "status": audit.status,
            "score": audit.score,
            "updated_at": audit.updated_at.isoformat() if audit.updated_at else "",
        }

    st.write(t(
        "report_summary_line",
        ref=audit_info["reference"],
        branch=audit_info["branch_name"],
        score=audit_info["score"],
    ))
    st.dataframe(pd.DataFrame(answers_rows), use_container_width=True, hide_index=True)

    pdf_key = f"_report_pdf_{audit_id}_{audit_info['updated_at']}"
    if st.button(t("download_pdf_btn"), key=f"prepare_pdf_{audit_id}"):
        st.session_state[pdf_key] = export_audit_report_pdf(audit_info, answers_rows)
    if pdf_key in st.session_state:
        st.download_button(
            t("download_pdf_btn"),
            data=st.session_state[pdf_key],
            file_name=f"{audit_info['reference']}.pdf",
            mime="application/pdf",
            key=f"download_pdf_{audit_id}",
        )

st.divider()
st.subheader(t("export_all_title"))
if st.button(t("export_all_excel_btn"), key="prepare_all_audits_excel"):
    with get_session() as session:
        all_audits = session.query(
            Audit.reference, Audit.branch_id, Audit.auditor_email,
            Audit.status, Audit.score, Audit.created_at,
        ).order_by(Audit.created_at.desc()).all()
    export_df = pd.DataFrame([{
        t("reference_col"): audit.reference,
        t("branch_col"): branches_by_id.get(audit.branch_id, {}).get("name_ar", "—"),
        t("auditor_col"): audit.auditor_email,
        t("status_col"): audit.status,
        t("score_col"): audit.score,
        t("created_at_col"): audit.created_at,
    } for audit in all_audits])
    st.session_state["_all_audits_excel"] = export_audits_to_excel(export_df)

if "_all_audits_excel" in st.session_state:
    st.download_button(
        t("export_all_excel_btn"),
        data=st.session_state["_all_audits_excel"],
        file_name="all_audits.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_all_audits_excel",
    )
