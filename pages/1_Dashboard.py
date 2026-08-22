import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
import plotly.express as px

from auth import require_login, current_user, render_logout_sidebar
from database import get_session
from models import Audit, CorrectiveAction
from data_cache import get_branches_cached
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Dashboard | الداشبورد", page_icon="📊", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("dashboard_title"))


@st.cache_data(ttl=15, show_spinner=False)
def load_dashboard_data():
    """يحمّل كل بيانات الداشبورد دفعة واحدة ويخزّنها 15 ثانية لتسريع التنقّل."""
    branches_by_id = {b["id"]: b for b in get_branches_cached()}
    with get_session() as s:
        audits = s.query(Audit).all()
        actions = s.query(CorrectiveAction).all()

        audits_data = [{
            "id": a.id, "reference": a.reference,
            "branch": branches_by_id[a.branch_id]["name_ar"] if a.branch_id in branches_by_id else "—",
            "status": a.status, "score": a.score,
            "auditor": a.auditor_email, "created_at": a.created_at,
        } for a in audits]

        actions_data = [{
            "title": a.title, "owner_email": a.owner_email,
            "priority": a.priority, "status": a.status, "due_at": a.due_at,
        } for a in actions]

    return audits_data, actions_data


audits_data, actions_data = load_dashboard_data()
df = pd.DataFrame(audits_data)

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("total_audits"), len(df))
col2.metric(t("closed_audits"), int((df["status"] == "closed").sum()) if not df.empty else 0)
col3.metric(t("in_progress"), int(df["status"].isin(["draft", "submitted", "reviewed"]).sum()) if not df.empty else 0)
avg_score = round(df["score"].dropna().mean(), 1) if not df.empty and df["score"].notna().any() else 0
col4.metric(t("avg_score"), f"{avg_score}%")

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader(t("status_distribution"))
    if not df.empty:
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = [t("status_col"), t("count_col")]
        fig = px.pie(status_counts, names=t("status_col"), values=t("count_col"), hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_audit_data"))

with c2:
    st.subheader(t("score_by_branch"))
    if not df.empty and df["score"].notna().any():
        by_branch = df.dropna(subset=["score"]).groupby("branch")["score"].mean().reset_index()
        fig2 = px.bar(by_branch, x="branch", y="score", labels={"branch": t("branch_col"), "score": t("score_col")})
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(t("no_score_data"))

st.divider()
st.subheader(t("open_corrective_actions"))
open_actions = [a for a in actions_data if a["status"] in ("open", "in_progress", "pending_review")]
if open_actions:
    adf = pd.DataFrame([{
        t("title_col"): a["title"], t("owner_col"): a["owner_email"],
        t("priority_col"): a["priority"], t("status_col"): a["status"], t("due_col"): a["due_at"],
    } for a in open_actions])
    st.dataframe(adf, use_container_width=True, hide_index=True)
else:
    st.success(t("no_open_actions"))
