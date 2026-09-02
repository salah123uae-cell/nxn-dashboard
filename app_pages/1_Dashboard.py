import streamlit as st
from branding import render_logo, apply_theme, BRAND_LIME, BRAND_BLUE, BRAND_PURPLE
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from auth import require_login, current_user, render_logout_sidebar
from database import get_session
from models import Audit, CorrectiveAction
from data_cache import get_branches_by_id_cached
from utils import style_status_badges, CORRECTIVE_STATUS_COLORS, PRIORITY_COLORS
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()


st.title(t("dashboard_title"))


@st.cache_data(ttl=15, show_spinner=False)
def load_dashboard_data(current_lang: str):
    """يحمّل كل بيانات الداشبورد دفعة واحدة ويخزّنها 15 ثانية لتسريع التنقّل."""
    branches_by_id = get_branches_by_id_cached()
    with get_session() as s:
        audits = s.query(Audit).all()
        actions = s.query(CorrectiveAction).all()

        def branch_name(bid):
            b = branches_by_id.get(bid)
            if not b:
                return "—"
            return b["name_en"] if current_lang == "en" else b["name_ar"]

        audits_data = [{
            "id": a.id, "reference": a.reference,
            "branch_id": a.branch_id,
            "branch": branch_name(a.branch_id),
            "status": a.status, "score": a.score,
            "auditor": a.auditor_email, "created_at": a.created_at,
        } for a in audits]

        actions_data = [{
            "title": a.title, "owner_email": a.owner_email,
            "priority": a.priority, "status": a.status, "due_at": a.due_at,
        } for a in actions]

    return audits_data, actions_data


branches_by_id = get_branches_by_id_cached()
audits_data, actions_data = load_dashboard_data(lang)
df_all = pd.DataFrame(audits_data)

# ---------------- لوحة حالة الفروع المرئية (بطاقات ملوّنة حسب الأداء) ----------------
st.subheader(t("branch_status_board"))

if branches_by_id:
    branch_scores = {}
    branch_counts = {}
    if not df_all.empty:
        scored = df_all.dropna(subset=["score"])
        for bid, grp in scored.groupby("branch_id"):
            branch_scores[bid] = round(grp["score"].mean(), 1)
        for bid, grp in df_all.groupby("branch_id"):
            branch_counts[bid] = len(grp)

    branch_list = list(branches_by_id.values())
    cols_per_row = 4
    for row_start in range(0, len(branch_list), cols_per_row):
        row_branches = branch_list[row_start:row_start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, b in zip(cols, row_branches):
            score = branch_scores.get(b["id"])
            count = branch_counts.get(b["id"], 0)
            if score is None:
                color, bg = "#9CA3AF", "#F3F4F6"
                score_display = t("no_data_yet")
            elif score >= 90:
                color, bg = BRAND_LIME, "#EAFBE7"
                score_display = f"{score}%"
            elif score >= 75:
                color, bg = "#F5A623", "#FFF6E5"
                score_display = f"{score}%"
            else:
                color, bg = "#E5484D", "#FDEBEC"
                score_display = f"{score}%"

            name = b["name_en"] if lang == "en" else b["name_ar"]
            with col:
                st.markdown(
                    f"""
                    <div style="
                        background:{bg}; border:2px solid {color}; border-radius:14px;
                        padding:14px 10px; text-align:center; margin-bottom:12px;
                    ">
                        <div style="font-size:13px; color:#555; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{name}</div>
                        <div style="font-size:26px; font-weight:800; color:{color}; margin:4px 0;">{score_display}</div>
                        <div style="font-size:11px; color:#888;">{count} {t("audits_count_label")}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
else:
    st.info(t("no_data_yet"))

st.divider()

# ---------------- فلاتر تفاعلية ----------------
fc1, fc2, fc3 = st.columns([2, 1, 1])
with fc1:
    branch_name_options = [(b["name_en"] if lang == "en" else b["name_ar"]) for b in branches_by_id.values()]
    selected_branches = st.multiselect(t("filter_branch_label"), options=branch_name_options, default=[])
with fc2:
    default_from = (datetime.utcnow() - timedelta(days=365)).date()
    date_from = st.date_input(t("filter_date_from"), value=default_from, key="dash_date_from")
with fc3:
    date_to = st.date_input(t("filter_date_to"), value=datetime.utcnow().date(), key="dash_date_to")

df = df_all.copy()
if not df.empty:
    if selected_branches:
        id_by_name = {(b["name_en"] if lang == "en" else b["name_ar"]): b["id"] for b in branches_by_id.values()}
        selected_ids = {id_by_name[n] for n in selected_branches if n in id_by_name}
        df = df[df["branch_id"].isin(selected_ids)]
    if "created_at" in df.columns:
        df = df[df["created_at"].apply(lambda d: d is not None and date_from <= d.date() <= date_to)]

st.divider()

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
        fig = px.pie(
            status_counts, names=t("status_col"), values=t("count_col"), hole=0.45,
            color_discrete_sequence=[BRAND_BLUE, BRAND_LIME, BRAND_PURPLE, "#F5A623", "#E5484D", "#9CA3AF"],
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_audit_data"))

with c2:
    st.subheader(t("score_by_branch"))
    if not df.empty and df["score"].notna().any():
        by_branch = df.dropna(subset=["score"]).groupby("branch")["score"].mean().reset_index()
        by_branch["color"] = by_branch["score"].apply(
            lambda s: BRAND_LIME if s >= 90 else ("#F5A623" if s >= 75 else "#E5484D")
        )
        fig2 = px.bar(
            by_branch, x="branch", y="score", labels={"branch": t("branch_col"), "score": t("score_col")},
            color="color", color_discrete_map="identity",
        )
        fig2.update_layout(showlegend=False)
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
    styled_adf = style_status_badges(adf, {
        t("priority_col"): PRIORITY_COLORS,
        t("status_col"): CORRECTIVE_STATUS_COLORS,
    })
    st.dataframe(styled_adf, use_container_width=True, hide_index=True)
else:
    st.success(t("no_open_actions"))

