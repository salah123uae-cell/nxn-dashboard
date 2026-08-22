import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
import plotly.express as px
from sqlalchemy import func

from auth import require_login, render_logout_sidebar
from database import get_session
from models import Audit, CorrectiveAction
from data_cache import get_branches_by_id_cached
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Dashboard | الداشبورد", page_icon="📊", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_login()
render_logout_sidebar()

st.title(t("dashboard_title"))


@st.cache_data(ttl=15, show_spinner=False)
def load_dashboard_data():
    """Load aggregates in SQL instead of transferring every audit to Streamlit."""
    branches_by_id = get_branches_by_id_cached()
    with get_session() as session:
        total_audits = session.query(func.count(Audit.id)).filter(Audit.dashboard_visible.is_(True)).scalar() or 0
        closed_audits = session.query(func.count(Audit.id)).filter(
            Audit.dashboard_visible.is_(True), Audit.status == "closed"
        ).scalar() or 0
        in_progress = session.query(func.count(Audit.id)).filter(
            Audit.dashboard_visible.is_(True),
            Audit.status.in_(["draft", "submitted", "reviewed"]),
        ).scalar() or 0
        avg_score = session.query(func.avg(Audit.score)).filter(
            Audit.dashboard_visible.is_(True), Audit.score.isnot(None)
        ).scalar()

        status_rows = session.query(Audit.status, func.count(Audit.id)).filter(
            Audit.dashboard_visible.is_(True)
        ).group_by(Audit.status).all()

        branch_rows = session.query(Audit.branch_id, func.avg(Audit.score)).filter(
            Audit.dashboard_visible.is_(True), Audit.score.isnot(None)
        ).group_by(Audit.branch_id).all()

        action_rows = session.query(
            CorrectiveAction.title,
            CorrectiveAction.owner_email,
            CorrectiveAction.priority,
            CorrectiveAction.status,
            CorrectiveAction.due_at,
        ).filter(
            CorrectiveAction.status.in_(["open", "in_progress", "pending_review"])
        ).order_by(CorrectiveAction.created_at.desc()).limit(200).all()

    statuses = [{"status": status, "count": count} for status, count in status_rows]
    branches = [{
        "branch": branches_by_id.get(branch_id, {}).get("name_ar", "—"),
        "score": round(float(score), 2),
    } for branch_id, score in branch_rows]
    actions = [{
        "title": row.title, "owner_email": row.owner_email,
        "priority": row.priority, "status": row.status, "due_at": row.due_at,
    } for row in action_rows]
    metrics = {
        "total": total_audits,
        "closed": closed_audits,
        "in_progress": in_progress,
        "avg_score": round(float(avg_score), 1) if avg_score is not None else 0,
    }
    return metrics, statuses, branches, actions


metrics, status_data, branch_data, open_actions = load_dashboard_data()

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("total_audits"), metrics["total"])
col2.metric(t("closed_audits"), metrics["closed"])
col3.metric(t("in_progress"), metrics["in_progress"])
col4.metric(t("avg_score"), f"{metrics['avg_score']}%")

st.divider()
c1, c2 = st.columns(2)

with c1:
    st.subheader(t("status_distribution"))
    if status_data:
        status_df = pd.DataFrame(status_data)
        fig = px.pie(status_df, names="status", values="count", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_audit_data"))

with c2:
    st.subheader(t("score_by_branch"))
    if branch_data:
        branch_df = pd.DataFrame(branch_data)
        fig2 = px.bar(
            branch_df, x="branch", y="score",
            labels={"branch": t("branch_col"), "score": t("score_col")},
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info(t("no_score_data"))

st.divider()
st.subheader(t("open_corrective_actions"))
if open_actions:
    adf = pd.DataFrame([{
        t("title_col"): action["title"],
        t("owner_col"): action["owner_email"],
        t("priority_col"): action["priority"],
        t("status_col"): action["status"],
        t("due_col"): action["due_at"],
    } for action in open_actions])
    st.dataframe(adf, use_container_width=True, hide_index=True)
    if len(open_actions) == 200:
        st.caption("Showing the 200 most recent open actions.")
else:
    st.success(t("no_open_actions"))
