import streamlit as st
import pandas as pd

from auth import require_role
from database import get_session
from models import AuditLog

st.set_page_config(page_title="سجل النشاط", page_icon="📜", layout="wide")
require_role("owner", "manager")

st.title("📜 سجل النشاط (Audit Log)")

with get_session() as s:
    logs = s.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()
    rows = [{
        "الوقت": l.created_at, "الفاعل": l.actor_email, "الإجراء": l.action,
        "النوع": l.entity_type, "المعرف": l.entity_id,
    } for l in logs]

df = pd.DataFrame(rows)

c1, c2 = st.columns(2)
actor_filter = c1.text_input("تصفية حسب البريد الإلكتروني")
entity_filter = c2.text_input("تصفية حسب نوع الكيان (مثال: audit, branch, user)")

if not df.empty:
    if actor_filter:
        df = df[df["الفاعل"].str.contains(actor_filter, case=False, na=False)]
    if entity_filter:
        df = df[df["النوع"].str.contains(entity_filter, case=False, na=False)]

st.dataframe(df, use_container_width=True, hide_index=True)
st.caption(f"آخر {len(rows)} حدث معروض من أصل السجل الكامل")
