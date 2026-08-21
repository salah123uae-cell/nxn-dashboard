import streamlit as st
import pandas as pd
import plotly.express as px

from auth import require_login, current_user
from database import get_session
from models import Audit, Branch, CorrectiveAction

st.set_page_config(page_title="الداشبورد", page_icon="📊", layout="wide")
require_login()
user = current_user()

st.title("📊 لوحة المعلومات")

with get_session() as s:
    audits = s.query(Audit).all()
    branches = {b.id: b for b in s.query(Branch).all()}
    actions = s.query(CorrectiveAction).all()

    audits_data = [{
        "id": a.id, "reference": a.reference,
        "branch": branches[a.branch_id].name_ar if a.branch_id in branches else "—",
        "status": a.status, "score": a.score,
        "auditor": a.auditor_email, "created_at": a.created_at,
    } for a in audits]

df = pd.DataFrame(audits_data)

col1, col2, col3, col4 = st.columns(4)
col1.metric("إجمالي التدقيقات", len(df))
col2.metric("مكتملة (مغلقة)", int((df["status"] == "closed").sum()) if not df.empty else 0)
col3.metric("قيد التنفيذ", int(df["status"].isin(["draft", "submitted", "reviewed"]).sum()) if not df.empty else 0)
avg_score = round(df["score"].dropna().mean(), 1) if not df.empty and df["score"].notna().any() else 0
col4.metric("متوسط النتيجة", f"{avg_score}%")

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("توزيع حالات التدقيق")
    if not df.empty:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["الحالة", "العدد"]
        fig = px.pie(status_counts, names="الحالة", values="العدد", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("لا توجد بيانات تدقيق بعد")

with c2:
    st.subheader("متوسط النتيجة حسب الفرع")
    if not df.empty and df["score"].notna().any():
        by_branch = df.dropna(subset=["score"]).groupby("branch")["score"].mean().reset_index()
        fig2 = px.bar(by_branch, x="branch", y="score", labels={"branch": "الفرع", "score": "النتيجة"})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("لا توجد نتائج محسوبة بعد")

st.divider()
st.subheader("🛠️ الإجراءات التصحيحية المفتوحة")
open_actions = [a for a in actions if a.status in ("open", "in_progress", "pending_review")]
if open_actions:
    adf = pd.DataFrame([{
        "العنوان": a.title, "المسؤول": a.owner_email,
        "الأولوية": a.priority, "الحالة": a.status, "الاستحقاق": a.due_at,
    } for a in open_actions])
    st.dataframe(adf, use_container_width=True, hide_index=True)
else:
    st.success("لا توجد إجراءات تصحيحية مفتوحة 🎉")
