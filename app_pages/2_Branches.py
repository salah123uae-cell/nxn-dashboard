import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_login, current_user, log_action, render_logout_sidebar
from database import get_session
from models import Branch
from data_cache import get_branches_cached, clear_reference_cache
from utils import paginate_dataframe
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()
can_edit = user["role"] in ("owner", "manager")


st.title(t("branches_title"))

with get_session() as s:
    branches_raw = s.query(Branch).order_by(Branch.id).all()
    data = [{
        t("id_col"): b.id, t("code_col"): b.code, t("name_ar_col"): b.name_ar, t("name_en_col"): b.name_en,
        t("region_col"): b.region, t("city_col"): b.city, t("status_col"): b.status,
        t("branch_manager_col"): b.manager_email or "—",
    } for b in branches_raw]

st.dataframe(paginate_dataframe(pd.DataFrame(data), key_prefix="branches_list"), use_container_width=True, hide_index=True)

if can_edit:
    st.divider()
    st.subheader(t("add_branch_title"))
    with st.form("add_branch"):
        c1, c2 = st.columns(2)
        code = c1.text_input(t("branch_code_label"))
        region = c2.text_input(t("region_label"))
        name_ar = c1.text_input(t("name_ar_label"))
        name_en = c2.text_input(t("name_en_label"))
        city = c1.text_input(t("city_label"))
        manager_email = c2.text_input(t("manager_email_label"))
        address = st.text_area(t("address_label"))
        status = st.selectbox(t("status_col"), ["active", "inactive", "suspended"])

        if st.form_submit_button(t("save_branch_btn")):
            if not code or not region or not name_ar or not name_en:
                st.error(t("fill_required"))
            else:
                with get_session() as s:
                    exists = s.query(Branch).filter(Branch.code == code).first()
                    if exists:
                        st.error(t("branch_code_exists"))
                    else:
                        b = Branch(code=code, name_ar=name_ar, name_en=name_en, region=region,
                                   city=city, manager_email=manager_email or None,
                                   address=address, status=status)
                        s.add(b)
                        s.flush()
                        log_action(user["email"], "create", "branch", b.id, after={"code": code})
                        clear_reference_cache()
                        st.success(t("branch_added"))
                        st.rerun()

    st.divider()
    st.subheader(t("edit_branch_title"))
    branches = get_branches_cached()
    if branches:
        options = {f"{b['code']} - {b['name_ar']}": b["id"] for b in branches}
        choice = st.selectbox(t("select_branch"), list(options.keys()))
        branch_id = options[choice]
        new_status = st.selectbox(t("new_status_label"), ["active", "inactive", "suspended"], key="edit_status")
        if st.button(t("update_status_btn")):
            with get_session() as s:
                b = s.query(Branch).get(branch_id)
                before = {"status": b.status}
                b.status = new_status
                log_action(user["email"], "update", "branch", branch_id, before=before, after={"status": new_status})
            clear_reference_cache()
            st.success(t("updated_msg"))
            st.rerun()
else:
    st.info(t("no_branch_edit_permission"))

