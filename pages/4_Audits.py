import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
from datetime import datetime

from auth import require_login, current_user, log_action, can_manage_branch, render_logout_sidebar
from database import get_session
from models import Audit, AuditAnswer, AuditQuestion, Branch, CorrectiveAction
from utils import generate_reference, calculate_audit_score, score_badge, export_audits_to_excel
from data_cache import get_branches_cached, get_active_branches_cached, get_questions_for_version_cached, get_sections_cached, clear_reference_cache
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Audits | التدقيقات", page_icon="🔍", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("audits_title"))

tab_list, tab_new, tab_conduct = st.tabs([t("tab_audit_list"), t("tab_new_audit"), t("tab_conduct")])

# ---------- تبويب: قائمة التدقيقات ----------
with tab_list:
    branches_by_id = {b["id"]: b for b in get_branches_cached()}
    with get_session() as s:
        audits = s.query(Audit).order_by(Audit.created_at.desc()).all()
        rows = []
        for a in audits:
            rows.append({
                t("reference_col"): a.reference,
                t("branch_col"): branches_by_id[a.branch_id]["name_ar"] if a.branch_id in branches_by_id else "—",
                t("auditor_col"): a.auditor_email,
                t("status_col"): a.status,
                t("score_col"): score_badge(a.score),
                t("created_at_col"): a.created_at,
            })
    df = pd.DataFrame(rows)
    status_filter = st.multiselect(t("filter_by_status"), options=["scheduled", "draft", "submitted", "reviewed", "closed", "cancelled"])
    if status_filter and not df.empty:
        df = df[df[t("status_col")].isin(status_filter)]
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        excel_bytes = export_audits_to_excel(df)
        st.download_button(t("export_excel"), data=excel_bytes, file_name="audits.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---------- تبويب: تدقيق جديد ----------
with tab_new:
    if user["role"] not in ("owner", "manager", "auditor"):
        st.info(t("no_create_permission"))
    else:
        active_branches = get_active_branches_cached()
        if not active_branches:
            st.warning(t("no_active_branches"))
        else:
            with st.form("new_audit"):
                branch_options = {f"{b['code']} - {b['name_ar']}": b["id"] for b in active_branches}
                branch_choice = st.selectbox(t("branch_col"), list(branch_options.keys()))
                auditor_email = st.text_input(t("auditor_email_label"), value=user["email"])
                scheduled_at = st.date_input(t("schedule_date_label"), value=datetime.utcnow())
                checklist_version = st.text_input(t("checklist_version_label"), value="QV1")
                if st.form_submit_button(t("create_audit_btn")):
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
                        st.success(t("audit_created", ref=audit.reference))
                        st.rerun()

# ---------- تبويب: تنفيذ / مراجعة تدقيق ----------
with tab_conduct:
    with get_session() as s:
        audits = s.query(Audit).filter(Audit.status.in_(["scheduled", "draft", "submitted", "reviewed"])).all()
        audit_options = {f"{a.reference} ({a.status})": a.id for a in audits}

    if not audit_options:
        st.info(t("no_audits_available"))
    else:
        choice = st.selectbox(t("select_audit"), list(audit_options.keys()))
        audit_id = audit_options[choice]

        with get_session() as s:
            audit = s.query(Audit).get(audit_id)
            branch = s.query(Branch).get(audit.branch_id)
            existing_answers = {a.question_id: a for a in s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()}

            audit_data = {"reference": audit.reference, "status": audit.status, "score": audit.score}
            branch_name = branch.name_ar if branch else "—"
            checklist_version = audit.checklist_version

        # الأسئلة والأقسام بيانات مرجعية نادرًا ما تتغيّر — تُقرأ من الذاكرة المؤقتة (أسرع بكثير)
        questions = get_questions_for_version_cached(checklist_version)
        sections = get_sections_cached()

        st.write(t("audit_summary_line", branch=branch_name, status=audit_data["status"], score=score_badge(audit_data["score"])))

        editable = audit_data["status"] in ("scheduled", "draft")

        # ملاحظة أداء: كل حقول الإجابة والملاحظات داخل نموذج (st.form) واحد، فلا تُعاد
        # قراءة قاعدة البيانات وإعادة رسم كل الأسئلة مع كل حرف يُكتب — فقط عند الحفظ/الإرسال.
        with st.form(key=f"audit_form_{audit_id}"):
            answers_input = {}
            current_section = None
            for q in questions:
                sec = sections.get(q["section_id"])
                if sec and sec["id"] != current_section:
                    st.subheader(f"📂 {sec['name_ar']}")
                    current_section = sec["id"]

                existing = existing_answers.get(q["id"])
                default_answer = existing.answer if existing else None
                default_note = existing.note if existing else ""

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{q['code']}** — {q['question_ar']}  _(وزن: {q['weight']})_")
                    note = st.text_input(t("note_label"), value=default_note, key=f"note_{audit_id}_{q['id']}", disabled=not editable, label_visibility="collapsed", placeholder=t("note_placeholder"))
                with col2:
                    options = ["-- بدون --", "compliant", "non_compliant", "not_applicable"]
                    ans = st.selectbox(
                        t("answer_label"), options,
                        index=(options.index(default_answer) if default_answer in options else 0),
                        key=f"ans_{audit_id}_{q['id']}", disabled=not editable, label_visibility="collapsed",
                    )
                answers_input[q["id"]] = {"answer": None if ans == "-- بدون --" else ans, "note": note, "weight": q["weight"]}
                st.divider()

            if editable:
                c1, c2 = st.columns(2)
                save_draft = c1.form_submit_button(t("save_draft_btn"))
                submit_final = c2.form_submit_button(t("submit_final_btn"))
            else:
                save_draft = False
                submit_final = False
                st.info(t("already_submitted_info"))

        # ---------- معالجة الحفظ كمسودة (خارج النموذج، بعد التقديم) ----------
        if editable and save_draft:
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
            st.success(t("saved_draft_msg"))
            st.rerun()

        # ---------- معالجة الإرسال النهائي (خارج النموذج، بعد التقديم) ----------
        if editable and submit_final:
            unanswered = [qid for qid, d in answers_input.items() if d["answer"] is None]
            if unanswered:
                st.error(t("unanswered_error", n=len(unanswered)))
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
                st.success(t("audit_submitted_msg", score=score))
                st.rerun()

        if not editable and user["role"] in ("owner", "manager") and audit_data["status"] == "submitted":
            if st.button(t("close_audit_btn")):
                with get_session() as s:
                    a = s.query(Audit).get(audit_id)
                    a.status = "closed"
                    a.closed_at = datetime.utcnow()
                    log_action(user["email"], "close", "audit", audit_id)
                st.success(t("audit_closed_msg"))
                st.rerun()
