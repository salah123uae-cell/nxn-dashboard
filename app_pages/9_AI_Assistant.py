import streamlit as st
from branding import render_logo, apply_theme

from auth import require_login, current_user, render_logout_sidebar
from database import get_session
from models import Audit, Branch, CorrectiveAction, AuditAnswer, AuditQuestion
from ai_agent import is_ai_configured, summarize_audit, chat_with_assistant, MAX_CHAT_MESSAGES_PER_SESSION
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("ai_title"))
st.caption(t("ai_caption"))

if not is_ai_configured():
    if user["role"] == "owner":
        st.warning(
            t("ai_not_configured") + "\n\n"
            + t("ai_setup_step1") + "\n"
            + t("ai_setup_step2") + "\n"
            "```\nAI_API_KEY = \"...\"\n```\n"
            + t("ai_setup_step3") + "\n\n"
            + t("ai_setup_cost_note")
        )
    else:
        st.info(t("ai_not_ready_generic"))
    st.stop()

tab_chat, tab_insights = st.tabs([t("tab_chat"), t("tab_insights")])

# ---------- تبويب: محادثة عامة ----------
with tab_chat:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    with get_session() as s:
        total_audits = s.query(Audit).count()
        open_actions = s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(["open", "in_progress"])
        ).count()
        total_branches = s.query(Branch).count()

    context_summary = (
        f"عدد الفروع: {total_branches} | إجمالي التدقيقات: {total_audits} | "
        f"إجراءات تصحيحية مفتوحة: {open_actions} | دور المستخدم الحالي: {user['role']}"
    )

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_msg_count = sum(1 for m in st.session_state.chat_history if m["role"] == "user")

    if user_msg_count >= MAX_CHAT_MESSAGES_PER_SESSION:
        st.warning(t("chat_limit_reached", n=MAX_CHAT_MESSAGES_PER_SESSION))
    else:
        prompt = st.chat_input(t("chat_placeholder"))
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner(t("ai_thinking")):
                    try:
                        reply = chat_with_assistant(prompt, context_summary, st.session_state.chat_history)
                    except Exception as e:
                        reply = f"حدث خطأ أثناء الاتصال بالمساعد الذكي: {e}"
                    st.write(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.session_state.chat_history:
        if st.button(t("clear_chat_btn")):
            st.session_state.chat_history = []
            st.rerun()

# ---------- تبويب: ملخصات ذكية للتدقيقات ----------
with tab_insights:
    with get_session() as s:
        audits = s.query(Audit).filter(
            Audit.status.in_(["submitted", "reviewed", "closed"])
        ).order_by(Audit.created_at.desc()).all()
        branches = {b.id: b for b in s.query(Branch).all()}

    if not audits:
        st.info(t("no_submitted_for_ai"))
    else:
        options = {
            f"{a.reference} - {branches[a.branch_id].name_ar if a.branch_id in branches else ''}": a.id
            for a in audits
        }
        choice = st.selectbox(t("select_audit_ai"), list(options.keys()))
        audit_id = options[choice]

        if st.button(t("generate_summary_btn")):
            with get_session() as s:
                audit = s.query(Audit).get(audit_id)
                branch = s.query(Branch).get(audit.branch_id)
                answers = s.query(AuditAnswer).filter(AuditAnswer.audit_id == audit_id).all()
                questions = {q.id: q for q in s.query(AuditQuestion).all()}

                answers_rows = [{
                    "question": questions[a.question_id].question_ar if a.question_id in questions else "—",
                    "answer": a.answer,
                    "weight": questions[a.question_id].weight if a.question_id in questions else 0,
                    "note": a.note,
                } for a in answers]

                audit_info = {
                    "reference": audit.reference,
                    "branch_name": branch.name_ar if branch else "—",
                    "score": audit.score,
                }

            with st.spinner(t("ai_analyzing")):
                try:
                    summary = summarize_audit(audit_info, answers_rows)
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"حدث خطأ أثناء توليد الملخص: {e}")

