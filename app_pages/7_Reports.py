import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_login, current_user, render_logout_sidebar
from database import get_session
from models import Audit, AuditAnswer, AuditQuestion
from utils import export_audit_report_pdf, export_audits_to_excel
from data_cache import get_branches_by_id_cached
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("reports_title"))

branches_by_id = get_branches_by_id_cached()

with get_session() as s:
    audits = s.query(Audit).filter(Audit.status.in_(["submitted", "reviewed", "closed"])).order_by(Audit.created_at.desc()).all()
    # نستخرج البيانات المطلوبة كقيم بسيطة وإحنا لسا داخل الجلسة، لتفادي الوصول
    # لأعمدة الكائنات بعد إغلاق الجلسة (DetachedInstanceError).
    audits_data = [{"id": a.id, "reference": a.reference, "branch_id": a.branch_id} for a in audits]

if not audits_data:
    st.info(t("no_submitted_audits"))
else:
    options = {f"{a['reference']} - {branches_by_id[a['branch_id']]['name_ar'] if a['branch_id'] in branches_by_id else ''}": a["id"] for a in audits_data}
    choice = st.selectbox(t("select_audit_report"), list(options.keys()))
    audit_id = options[choice]

    with get_session() as s:
        audit = s.query(Audit).get(audit_id)
        answers = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()
        questions = {q.id: q for q in s.query(AuditQuestion).all()}

        answers_rows = [{
            "question": questions[a.question_id].question_ar if a.question_id in questions else "—",
            "answer": a.answer, "weight": questions[a.question_id].weight if a.question_id in questions else 0,
            "note": a.note,
        } for a in answers]

        branch_info = branches_by_id.get(audit.branch_id)
        audit_info = {
            "reference": audit.reference, "branch_name": branch_info["name_ar"] if branch_info else "—",
            "auditor_email": audit.auditor_email, "status": audit.status, "score": audit.score,
        }

    st.write(t("report_summary_line", ref=audit_info["reference"], branch=audit_info["branch_name"], score=audit_info["score"]))
    st.table(pd.DataFrame(answers_rows))

    pdf_bytes = export_audit_report_pdf(audit_info, answers_rows)
    st.download_button(t("download_pdf_btn"), data=pdf_bytes,
                        file_name=f"{audit_info['reference']}.pdf", mime="application/pdf")

st.divider()
st.subheader(t("export_all_title"))
with get_session() as s:
    all_audits = s.query(Audit).all()
    df_all = pd.DataFrame([{
        t("reference_col"): a.reference,
        t("branch_col"): branches_by_id[a.branch_id]["name_ar"] if a.branch_id in branches_by_id else "—",
        t("auditor_col"): a.auditor_email, t("status_col"): a.status, t("score_col"): a.score,
        t("created_at_col"): a.created_at,
    } for a in all_audits])

if not df_all.empty:
    excel_bytes = export_audits_to_excel(df_all)
    st.download_button(t("export_all_excel_btn"), data=excel_bytes, file_name="all_audits.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

