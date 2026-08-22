import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
import json

from auth import require_role, current_user, hash_password, log_action, ROLES, ROLE_LABELS_AR, render_logout_sidebar
from database import get_session
from models import User, Credential, Branch
from data_cache import get_branches_cached
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Users | المستخدمون", page_icon="👥", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_role("owner", "manager")
render_logout_sidebar()
user = current_user()

with st.sidebar:
    language_switcher()

st.title(t("users_title"))

with get_session() as s:
    users_raw = s.query(User).order_by(User.id).all()
    rows = [{
        t("id_col"): u.id, t("email_col"): u.email, t("name_col"): u.name,
        t("role_col"): ROLE_LABELS_AR.get(u.role, u.role), t("active_status_col"): u.active,
        t("last_login_col"): u.last_login_at,
    } for u in users_raw]
    users = [{"id": u.id, "email": u.email, "name": u.name} for u in users_raw]

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.subheader(t("add_user_title"))

branches = get_branches_cached()

with st.form("add_user"):
    c1, c2 = st.columns(2)
    email = c1.text_input(t("email_label"))
    name = c2.text_input(t("name_label"))
    role = c1.selectbox(t("role_label"), ROLES, format_func=lambda r: ROLE_LABELS_AR.get(r, r))
    password = c2.text_input(t("initial_password_label"), type="password")
    phone = st.text_input(t("phone_label"))

    managed_branches = []
    if role in ("branch", "manager"):
        branch_options = {f"{b['code']} - {b['name_ar']}": b["id"] for b in branches}
        chosen = st.multiselect(t("managed_branches_label"), list(branch_options.keys()))
        managed_branches = [branch_options[c] for c in chosen]

    if st.form_submit_button(t("create_user_btn")):
        if not email or not name or not password:
            st.error(t("fill_required"))
        else:
            with get_session() as s:
                exists = s.query(User).filter(User.email == email.strip().lower()).first()
                if exists:
                    st.error(t("email_exists"))
                else:
                    new_user = User(
                        email=email.strip().lower(), name=name, role=role,
                        managed_branch_ids=json.dumps(managed_branches), phone=phone or None,
                    )
                    s.add(new_user)
                    s.flush()
                    s.add(Credential(user_id=new_user.id, password_hash=hash_password(password)))
                    log_action(user["email"], "create", "user", new_user.id, after={"email": email, "role": role})
            st.success(t("user_created"))
            st.rerun()

st.divider()
st.subheader(t("edit_user_title"))

if users:
    options = {f"{u['email']} ({u['name']})": u["id"] for u in users}
    choice = st.selectbox(t("select_user"), list(options.keys()))
    uid = options[choice]

    with get_session() as s:
        target = s.query(User).get(uid)
        target_active = target.active
        target_role = target.role

    c1, c2 = st.columns(2)
    new_active = c1.toggle(t("active_status_col"), value=target_active)
    new_role = c2.selectbox(t("role_label"), ROLES, index=ROLES.index(target_role), format_func=lambda r: ROLE_LABELS_AR.get(r, r))

    if st.button(t("save_changes_btn")):
        with get_session() as s:
            t_ = s.query(User).get(uid)
            before = {"active": t_.active, "role": t_.role}
            t_.active = new_active
            t_.role = new_role
            log_action(user["email"], "update", "user", uid, before=before, after={"active": new_active, "role": new_role})
        st.success(t("updated_msg"))
        st.rerun()
