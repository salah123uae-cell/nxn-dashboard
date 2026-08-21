import streamlit as st
import pandas as pd
from datetime import datetime

from auth import require_login, current_user, log_action
from database import get_session
from models import CorrectiveAction, Audit

st.set_page_config(page_title="الإجراءات التصحيحية", page_icon="🛠️", layout="wide")
require_login()
user = current_user()

st.title("🛠️ الإجراءات التصحيحية")

with get_session() as s:
    actions = s.query(CorrectiveAction).order_by(CorrectiveAction.created_at.desc()).all()
    audits = {a.id: a for a in s.query(Audit).all()}

    if user["role"] in ("auditor", "branch"):
        actions = [a for a in actions if a.owner_email == user["email"]]

    rows = [{
        "id": a.id, "المرجع": audits[a.audit_id].reference if a.audit_id in audits else "—",
        "العنوان": a.title, "المسؤول": a.owner_email, "الأولوية": a.priority,
        "الحالة": a.status, "الاستحقاق": a.due_at,
    } for a in actions]

df = pd.DataFrame(rows)
st.dataframe(df.drop(columns=["id"]) if not df.empty else df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("📝 تحديث حالة إجراء تصحيحي")

if not df.empty:
    options = {f"#{r['id']} - {r['العنوان']}": r["id"] for r in rows}
    choice = st.selectbox("اختر الإجراء", list(options.keys()))
    action_id = options[choice]

    with get_session() as s:
        action = s.query(CorrectiveAction).get(action_id)

    can_update = user["role"] in ("owner", "manager") or user["email"] == action.owner_email

    if can_update:
        new_status = st.selectbox("الحالة الجديدة", ["open", "in_progress", "pending_review", "closed", "rejected"],
                                   index=["open", "in_progress", "pending_review", "closed", "rejected"].index(action.status))
        response_note = st.text_area("ملاحظة الرد", value=action.response_note or "")
        if st.button("تحديث"):
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
            st.success("تم التحديث ✅")
            st.rerun()
    else:
        st.info("ليس لديك صلاحية تحديث هذا الإجراء")
else:
    st.success("لا توجد إجراءات تصحيحية 🎉")
