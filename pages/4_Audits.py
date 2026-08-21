import streamlit as st
import pandas as pd
from datetime import datetime

from auth import require_login, current_user, log_action, can_manage_branch
from database import get_session
from models import Audit, AuditAnswer, AuditQuestion, AuditSection, Branch, CorrectiveAction
from utils import generate_reference, calculate_audit_score, score_badge, export_audits_to_excel

st.set_page_config(page_title="التدقيقات", page_icon="🔍", layout="wide")
require_login()
user = current_user()

st.title("🔍 التدقيقات")

tab_list, tab_new, tab_conduct = st.tabs(["📄 قائمة التدقيقات", "➕ تدقيق جديد", "📝 تنفيذ / مراجعة تدقيق"])

# ---------- تبويب: قائمة التدقيقات ----------
with tab_list:
    with get_session() as s:
        audits = s.query(Audit).order_by(Audit.created_at.desc()).all()
        branches = {b.id: b for b in s.query(Branch).all()}
        rows = []
        for a in audits:
            rows.append({
                "المرجع": a.reference,
                "الفرع": branches[a.branch_id].name_ar if a.branch_id in branches else "—",
                "المدقق": a.auditor_email,
                "الحالة": a.status,
                "النتيجة": score_badge(a.score),
                "تاريخ الإنشاء": a.created_at,
            })
    df = pd.DataFrame(rows)
    status_filter = st.multiselect("تصفية حسب الحالة", options=["scheduled", "draft", "submitted", "reviewed", "closed", "cancelled"])
    if status_filter and not df.empty:
        df = df[df["الحالة"].isin(status_filter)]
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        excel_bytes = export_audits_to_excel(df)
        st.download_button("⬇️ تصدير Excel", data=excel_bytes, file_name="audits.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- تبويب: تدقيق جديد ----------
with tab_new:
    if user["role"] not in ("owner", "manager", "auditor"):
        st.info("ليس لديك صلاحية إنشاء تدقيقات جديدة")
    else:
        with get_session() as s:
            branches = s.query(Branch).filter(Branch.status == "active").all()
        if not branches:
            st.warning("لا توجد فروع نشطة. أضف فرعًا أولًا من صفحة الفروع.")
        else:
            with st.form("new_audit"):
                branch_options = {f"{b.code} - {b.name_ar}": b.id for b in branches}
                branch_choice = st.selectbox("الفرع", list(branch_options.keys()))
                auditor_email = st.text_input("بريد المدقق", value=user["email"])
                scheduled_at = st.date_input("تاريخ الجدولة", value=datetime.utcnow())
                checklist_version = st.text_input("نسخة التشيك ليست", value="QV1")
                if st.form_submit_button("إنشاء التدقيق"):
                    with get_session() as s:
                        audit = Audit(
                            reference=generate_reference(),
                            branch_id=branch_options[branch_choice],
                            auditor_email=auditor_email,
                            scheduled_at=datetime.combine(scheduled_at, datetime.min.time()),
                            status="scheduled",
                            checklist_version=checklist_version,
                        )
                        s.add(audit)
                        s.flush()
                        log_action(user["email"], "create", "audit", audit.id, after={"reference": audit.reference})
                        st.success(f"تم إنشاء التدقيق: {audit.reference} ✅")
                        st.rerun()

# ---------- تبويب: تنفيذ / مراجعة تدقيق ----------
with tab_conduct:
    with get_session() as s:
        audits = s.query(Audit).filter(Audit.status.in_(["scheduled", "draft", "submitted", "reviewed"])).all()
        audit_options = {f"{a.reference} ({a.status})": a.id for a in audits}

    if not audit_options:
        st.info("لا توجد تدقيقات متاحة للتنفيذ حاليًا")
    else:
        choice = st.selectbox("اختر التدقيق", list(audit_options.keys()))
        audit_id = audit_options[choice]

        with get_session() as s:
            audit = s.query(Audit).get(audit_id)
            branch = s.query(Branch).get(audit.branch_id)
            questions = s.query(AuditQuestion).filter(
                AuditQuestion.checklist_version == audit.checklist_version,
                AuditQuestion.active == True,  # noqa: E712
            ).order_by(AuditQuestion.sort_order).all()
            sections = {sec.id: sec for sec in s.query(AuditSection).all()}
            existing_answers = {a.question_id: a for a in s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()}

            audit_data = {"reference": audit.reference, "status": audit.status, "score": audit.score}
            branch_name = branch.name_ar if branch else "—"

        st.write(f"**الفرع:** {branch_name} | **الحالة:** {audit_data['status']} | **النتيجة الحالية:** {score_badge(audit_data['score'])}")

        editable = audit_data["status"] in ("scheduled", "draft")

        answers_input = {}
        current_section = None
        for q in questions:
            sec = sections.get(q.section_id)
            if sec and sec.id != current_section:
                st.subheader(f"📂 {sec.name_ar}")
                current_section = sec.id

            existing = existing_answers.get(q.id)
            default_answer = existing.answer if existing else None
            default_note = existing.note if existing else ""

            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{q.code}** — {q.question_ar}  _(وزن: {q.weight})_")
                note = st.text_input("ملاحظة", value=default_note, key=f"note_{q.id}", disabled=not editable, label_visibility="collapsed", placeholder="ملاحظة (اختياري)")
            with col2:
                ans = st.selectbox(
                    "الإجابة", ["-- بدون --", "compliant", "non_compliant", "not_applicable"],
                    index=(["-- بدون --", "compliant", "non_compliant", "not_applicable"].index(default_answer) if default_answer in ["compliant", "non_compliant", "not_applicable"] else 0),
                    key=f"ans_{q.id}", disabled=not editable, label_visibility="collapsed",
                )
            answers_input[q.id] = {"answer": None if ans == "-- بدون --" else ans, "note": note, "weight": q.weight}
            st.divider()

        if editable:
            c1, c2 = st.columns(2)
            if c1.button("💾 حفظ كمسودة"):
                with get_session() as s:
                    for qid, data in answers_input.items():
                        existing = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id, AuditAnswer.question_id == qid).first()
                        if existing:
                            existing.answer = data["answer"]
                            existing.note = data["note"]
                            existing.answered_by = user["email"]
                            existing.answered_at = datetime.utcnow()
                        else:
                            s.add(AuditAnswer(audit_id=audit_id, question_id=qid, answer=data["answer"],
                                               note=data["note"], answered_by=user["email"], answered_at=datetime.utcnow()))
                    a = s.query(Audit).get(audit_id)
                    if a.status == "scheduled":
                        a.status = "draft"
                        a.started_at = datetime.utcnow()
                st.success("تم الحفظ كمسودة ✅")
                st.rerun()

            if c2.button("📤 إرسال التدقيق النهائي"):
                unanswered = [qid for qid, d in answers_input.items() if d["answer"] is None]
                if unanswered:
                    st.error(f"يوجد {len(unanswered)} سؤال بدون إجابة. أكمل الإجابات قبل الإرسال.")
                else:
                    with get_session() as s:
                        for qid, data in answers_input.items():
                            existing = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id, AuditAnswer.question_id == qid).first()
                            score_awarded = data["weight"] if data["answer"] == "compliant" else 0
                            if existing:
                                existing.answer = data["answer"]
                                existing.note = data["note"]
                                existing.score_awarded = score_awarded
                                existing.answered_by = user["email"]
                                existing.answered_at = datetime.utcnow()
                            else:
                                s.add(AuditAnswer(audit_id=audit_id, question_id=qid, answer=data["answer"],
                                                   score_awarded=score_awarded, note=data["note"],
                                                   answered_by=user["email"], answered_at=datetime.utcnow()))
                        s.flush()
                        all_answers = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()
                        qmap = {q.id: q for q in s.query(AuditQuestion).all()}
                        score = calculate_audit_score(
                            [{"question_id": a.question_id, "answer": a.answer} for a in all_answers], qmap
                        )
                        a = s.query(Audit).get(audit_id)
                        a.status = "submitted"
                        a.submitted_at = datetime.utcnow()
                        a.score = score

                        # إنشاء إجراء تصحيحي تلقائي لكل إجابة غير متوافقة
                        for ans in all_answers:
                            if ans.answer == "non_compliant":
                                q = qmap.get(ans.question_id)
                                s.add(CorrectiveAction(
                                    audit_id=audit_id, answer_id=ans.id,
                                    title=f"معالجة عدم توافق: {q.code if q else ans.question_id}",
                                    description=q.question_ar if q else "",
                                    owner_email=audit.auditor_email,
                                    due_at=datetime.utcnow(),
                                    priority="high", status="open",
                                ))
                        log_action(user["email"], "submit", "audit", audit_id, after={"score": score})
                    st.success(f"تم إرسال التدقيق ✅ النتيجة: {score}%")
                    st.rerun()
        else:
            st.info("هذا التدقيق مُرسل بالفعل — يمكن للمدير مراجعته وإغلاقه من قسم المراجعة أدناه")
            if user["role"] in ("owner", "manager") and audit_data["status"] == "submitted":
                if st.button("✅ اعتماد وإغلاق التدقيق"):
                    with get_session() as s:
                        a = s.query(Audit).get(audit_id)
                        a.status = "closed"
                        a.closed_at = datetime.utcnow()
                        log_action(user["email"], "close", "audit", audit_id)
                    st.success("تم إغلاق التدقيق ✅")
                    st.rerun()
