import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
from datetime import datetime

from auth import require_login, current_user, log_action, render_logout_sidebar
from database import get_session
from models import CorrectiveAction, Audit
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Corrective Actions | الإجراءات التصحيحية", page_icon="🛠️", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()

language_switcher()

st.title(t("corrective_actions_title"))

with get_session() as s:
    actions = s.query(CorrectiveAction).order_by(CorrectiveAction.created_at.desc()).all()
    audits = {a.id: a for a in s.query(Audit).all()}

    if user["role"] in ("auditor", "branch"):
        actions = [a for a in actions if a.owner_email == user["email"]]

    rows = [{
        "id": a.id, t("reference_col"): audits[a.audit_id].reference if a.audit_id in audits else "—",
        t("title_col"): a.title, t("owner_col"): a.owner_email, t("priority_col"): a.priority,
        t("status_col"): a.status, t("due_col"): a.due_at,
    } for a in actions]

df = pd.DataFrame(rows)
st.dataframe(df.drop(columns=["id"]) if not df.empty else df, use_container_width=True, hide_index=True)

st.divider()
st.subheader(t("update_action_title"))

if not df.empty:
    options = {f"#{r['id']} - {r[t('title_col')]}": r["id"] for r in rows}
    choice = st.selectbox(t("select_action"), list(options.keys()))
    action_id = options[choice]

    with get_session() as s:
        action = s.query(CorrectiveAction).get(action_id)
        action_status = action.status
        action_response_note = action.response_note or ""
        action_owner_email = action.owner_email

    can_update = user["role"] in ("owner", "manager") or user["email"] == action_owner_email

    if can_update:
        # ملاحظة أداء: الحقول داخل نموذج (st.form) فلا تُعاد قراءة قاعدة البيانات
        # وإعادة رسم الصفحة مع كل حرف يُكتب بملاحظة الرد — فقط عند الضغط على "تحديث".
        with st.form(key=f"update_action_{action_id}"):
            statuses = ["open", "in_progress", "pending_review", "closed", "rejected"]
            new_status = st.selectbox(t("new_status_action_label"), statuses, index=statuses.index(action_status))
            response_note = st.text_area(t("response_note_label"), value=action_response_note)
            submitted = st.form_submit_button(t("update"))

        if submitted:
            with get_session() as s:
                a = s.query(CorrectiveAction).get(action_id)
                before = {"status": a.status}
                a.status = new_status
                a.response_note = response_note
                a.responded_by = user["email"]
                a.responded_at = datetime.utcnow()
                if new_status == "closed":
                    a.completed_at = datetime.utcnow()
                    a.closed_by = user["email"]
                log_action(user["email"], "update", "corrective_action", action_id, before=before, after={"status": new_status})
            st.success(t("updated_msg"))
            st.rerun()
    else:
        st.info(t("no_action_update_permission"))
else:
    st.success(t("no_actions"))
