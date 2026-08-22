import streamlit as st
from branding import render_logo, apply_theme

from auth import require_login, current_user
from database import get_session
from models import Audit, Branch, CorrectiveAction, AuditAnswer, AuditQuestion
from ai_agent import is_ai_configured, summarize_audit, chat_with_assistant

st.set_page_config(page_title="المساعد الذكي", page_icon="🤖", layout="wide")
apply_theme()
render_logo(size="small")
require_login()
user = current_user()

st.title("🤖 المساعد الذكي والوكيل الذكي")
st.caption("مدعوم بنموذج Claude من Anthropic")

if not is_ai_configured():
    st.warning(
        "⚠️ **المساعد الذكي غير مفعّل بعد.** لتفعيله:\n\n"
        "1. احصل على مفتاح API من https://console.anthropic.com\n"
        "2. في Streamlit Cloud: **Manage app → Settings → Secrets**، أضف السطر:\n"
        "```\nANTHROPIC_API_KEY = \"sk-ant-...\"\n```\n"
        "3. أعد تشغيل التطبيق (**Reboot app**)"
    )
    st.stop()

tab_chat, tab_insights = st.tabs(["💬 محادثة مع المساعد", "📊 ملخصات ذكية للتدقيقات"])

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

    prompt = st.chat_input("اسأل المساعد الذكي عن أي شيء يخص جودة الفروع...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("جارٍ التفكير..."):
                try:
                    reply = chat_with_assistant(prompt, context_summary, st.session_state.chat_history)
                except Exception as e:
                    reply = f"حدث خطأ أثناء الاتصال بالمساعد الذكي: {e}"
                st.write(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.session_state.chat_history:
        if st.button("🗑️ مسح المحادثة"):
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
        st.info("لا توجد تدقيقات مُرسلة بعد لتوليد ملخص ذكي عنها")
    else:
        options = {
            f"{a.reference} - {branches[a.branch_id].name_ar if a.branch_id in branches else ''}": a.id
            for a in audits
        }
        choice = st.selectbox("اختر تدقيقًا لتحليله بالذكاء الاصطناعي", list(options.keys()))
        audit_id = options[choice]

        if st.button("🧠 توليد ملخص ذكي"):
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

            with st.spinner("المساعد الذكي يحلل بيانات التدقيق..."):
                try:
                    summary = summarize_audit(audit_info, answers_rows)
                    st.markdown(summary)
                except Exception as e:
                    st.error(f"حدث خطأ أثناء توليد الملخص: {e}")
