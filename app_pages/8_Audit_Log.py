import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_role, render_logout_sidebar
from database import get_session
from models import AuditLog
from i18n import t, language_switcher, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_role("owner", "manager")
render_logout_sidebar()


st.title(t("audit_log_title"))

with get_session() as s:
    logs = s.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(500).all()
    rows = [{
        t("time_col"): l.created_at, t("actor_col"): l.actor_email, t("action_col"): l.action,
        t("entity_type_col"): l.entity_type, t("entity_id_col"): l.entity_id,
    } for l in logs]

df = pd.DataFrame(rows)

c1, c2 = st.columns(2)
actor_filter = c1.text_input(t("filter_by_email"))
entity_filter = c2.text_input(t("filter_by_entity"))

if not df.empty:
    if actor_filter:
        df = df[df[t("actor_col")].str.contains(actor_filter, case=False, na=False)]
    if entity_filter:
        df = df[df[t("entity_type_col")].str.contains(entity_filter, case=False, na=False)]

st.dataframe(df, use_container_width=True, hide_index=True)
st.caption(t("log_caption", n=len(rows)))
