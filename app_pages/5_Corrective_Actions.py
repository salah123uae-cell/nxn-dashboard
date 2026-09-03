import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
from datetime import datetime

from auth import (
    require_login, current_user, log_action, render_logout_sidebar,
    can_manage_branch, can_view_audit, can_respond_to_corrective_action,
    can_approve_corrective_action,
)
from database import get_session
from models import CorrectiveAction, Audit
from utils import style_status_badges, CORRECTIVE_STATUS_COLORS, PRIORITY_COLORS
from i18n import t, get_lang
from audit_workflow import respond_to_corrective_action, review_corrective_action

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("corrective_actions_title"))

with get_session() as s:
    actions = s.query(CorrectiveAction).order_by(CorrectiveAction.created_at.desc()).all()
    audits = {a.id: a for a in s.query(Audit).all()}

    actions = [a for a in actions if a.audit_id in audits and can_view_audit(user, audits[a.audit_id])]

    rows = [{
        "id": a.id, t("reference_col"): audits[a.audit_id].reference if a.audit_id in audits else "—",
        t("title_col"): a.title, t("owner_col"): a.owner_email, t("priority_col"): a.priority,
        t("status_col"): a.status, t("due_col"): a.due_at,
    } for a in actions]

df = pd.DataFrame(rows)
if not df.empty:
    display_df = df.drop(columns=["id"])
    styled = style_status_badges(display_df, {
        t("status_col"): CORRECTIVE_STATUS_COLORS,
        t("priority_col"): PRIORITY_COLORS,
    })
    st.dataframe(styled, use_container_width=True, hide_index=True)
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

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
        action_audit = s.query(Audit).get(action.audit_id) if action.audit_id else None
        action_branch_id = action_audit.branch_id if action_audit else None

    can_respond = action_branch_id is not None and can_respond_to_corrective_action(user, action_branch_id)
    can_approve = can_approve_corrective_action(user) and action_status == "pending_review"

    if can_respond:
        # ملاحظة أداء: الحقول داخل نموذج (st.form) فلا تُعاد قراءة قاعدة البيانات
        # وإعادة رسم الصفحة مع كل حرف يُكتب بملاحظة الرد — فقط عند الضغط على "تحديث".
        with st.form(key=f"update_action_{action_id}"):
            response_note = st.text_area(t("response_note_label"), value=action_response_note)
            submitted = st.form_submit_button(t("update"))

        if submitted:
            with get_session() as s:
                respond_to_corrective_action(s, action_id, response_note, user["email"])
            log_action(user["email"], "respond", "corrective_action", action_id,
                       before={"status": action_status}, after={"status": "pending_review"})
            st.success(t("updated_msg"))
            st.rerun()
    elif can_approve:
        c1, c2 = st.columns(2)
        approve = c1.button("اعتماد وإغلاق", key=f"approve_action_{action_id}")
        reject = c2.button("رفض وإعادته للفرع", key=f"reject_action_{action_id}")
        if approve or reject:
            with get_session() as s:
                review_corrective_action(s, action_id, approve=approve, actor_email=user["email"])
            final_status = "closed" if approve else "rejected"
            log_action(user["email"], "approve" if approve else "reject", "corrective_action",
                       action_id, before={"status": action_status}, after={"status": final_status})
            st.success(t("updated_msg"))
            st.rerun()
    else:
        st.info(t("no_action_update_permission"))
else:
    st.success(t("no_actions"))
