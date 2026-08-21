import streamlit as st
import pandas as pd

from auth import require_login, current_user
from database import get_session
from models import Audit, AuditAnswer, AuditQuestion, Branch
from utils import export_audit_report_pdf, export_audits_to_excel

st.set_page_config(page_title="التقارير", page_icon="📈", layout="wide")
require_login()
user = current_user()

st.title("📈 التقارير")

with get_session() as s:
    audits = s.query(Audit).filter(Audit.status.in_(["submitted", "reviewed", "closed"])).order_by(Audit.created_at.desc()).all()
    branches = {b.id: b for b in s.query(Branch).all()}

if not audits:
    st.info("لا توجد تدقيقات مُرسلة بعد لتوليد تقرير عنها")
else:
    options = {f"{a.reference} - {branches[a.branch_id].name_ar if a.branch_id in branches else ''}": a.id for a in audits}
    choice = st.selectbox("اختر تدقيقًا لعرض تقريره", list(options.keys()))
    audit_id = options[choice]

    with get_session() as s:
        audit = s.query(Audit).get(audit_id)
        branch = s.query(Branch).get(audit.branch_id)
        answers = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()
        questions = {q.id: q for q in s.query(AuditQuestion).all()}

        answers_rows = [{
            "question": questions[a.question_id].question_ar if a.question_id in questions else "—",
            "answer": a.answer, "weight": questions[a.question_id].weight if a.question_id in questions else 0,
            "note": a.note,
        } for a in answers]

        audit_info = {
            "reference": audit.reference, "branch_name": branch.name_ar if branch else "—",
            "auditor_email": audit.auditor_email, "status": audit.status, "score": audit.score,
        }

    st.write(f"**المرجع:** {audit_info['reference']} | **الفرع:** {audit_info['branch_name']} | **النتيجة:** {audit_info['score']}%")
    st.table(pd.DataFrame(answers_rows))

    pdf_bytes = export_audit_report_pdf(audit_info, answers_rows)
    st.download_button("⬇️ تحميل تقرير PDF", data=pdf_bytes,
                        file_name=f"{audit_info['reference']}.pdf", mime="application/pdf")

st.divider()
st.subheader("📊 تصدير كل التدقيقات")
with get_session() as s:
    all_audits = s.query(Audit).all()
    all_branches = {b.id: b for b in s.query(Branch).all()}
    df_all = pd.DataFrame([{
        "المرجع": a.reference,
        "الفرع": all_branches[a.branch_id].name_ar if a.branch_id in all_branches else "—",
        "المدقق": a.auditor_email, "الحالة": a.status, "النتيجة": a.score,
        "تاريخ الإنشاء": a.created_at,
    } for a in all_audits])

if not df_all.empty:
    excel_bytes = export_audits_to_excel(df_all)
    st.download_button("⬇️ تصدير الكل Excel", data=excel_bytes, file_name="all_audits.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
