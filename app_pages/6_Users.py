import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
import json

from auth import (
    require_role, current_user, hash_password, log_action, ROLES, ROLE_LABELS_AR,
    render_logout_sidebar, approve_signup_request, reject_signup_request,
    approve_password_reset, reject_password_reset,
)
from database import get_session
from models import User, Credential, SignupRequest, PasswordResetRequest
from data_cache import get_branches_cached
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_role("owner", "manager")
render_logout_sidebar()
user = current_user()


st.title(t("users_title"))

tab_list, tab_signups, tab_resets = st.tabs([
    t("users_tab_list"), t("users_tab_signups"), t("users_tab_resets"),
])

# ==================================================================
# تبويب: قائمة المستخدمين + إضافة + تعديل
# ==================================================================
with tab_list:
    with get_session() as s:
        users_raw = s.query(User).order_by(User.id).all()
        rows = [{
            t("id_col"): u.id, t("email_col"): u.email, t("name_col"): u.name,
            t("employee_number_col"): u.employee_number or "—",
            t("role_col"): ROLE_LABELS_AR.get(u.role, u.role), t("active_status_col"): u.active,
            t("last_login_col"): u.last_login_at,
        } for u in users_raw]
        users = [{
            "id": u.id, "email": u.email, "name": u.name, "phone": u.phone,
            "employee_number": u.employee_number,
            "managed_branch_ids": json.loads(u.managed_branch_ids or "[]"),
        } for u in users_raw]

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader(t("add_user_title"))

    branches = get_branches_cached()

    with st.form("add_user"):
        c1, c2 = st.columns(2)
        email = c1.text_input(t("email_label"))
        name = c2.text_input(t("name_label"))
        emp_num = c1.text_input(t("employee_number_label"))
        role = c2.selectbox(t("role_label"), ROLES, format_func=lambda r: ROLE_LABELS_AR.get(r, r))
        password = c1.text_input(t("initial_password_label"), type="password")
        phone = c2.text_input(t("phone_label"))

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
                            employee_number=emp_num or None,
                            managed_branch_ids=json.dumps(managed_branches), phone=phone or None,
                        )
                        s.add(new_user)
                        s.flush()
                        s.add(Credential(user_id=new_user.id, password_hash=hash_password(password)))
                        log_action(user["email"], "create", "user", new_user.id, after={"email": email, "role": role})
                st.success(t("user_created"))
                st.rerun()

    st.divider()
    st.subheader(t("edit_user_full_title"))

    if users:
        options = {f"{u['email']} ({u['name']})": u["id"] for u in users}
        choice = st.selectbox(t("select_user"), list(options.keys()))
        uid = options[choice]
        target = next(u for u in users if u["id"] == uid)

        with get_session() as s:
            db_target = s.query(User).get(uid)
            target_active = db_target.active
            target_role = db_target.role

        with st.form(f"edit_user_{uid}"):
            ec1, ec2 = st.columns(2)
            new_name = ec1.text_input(t("name_label").replace(" *", ""), value=target["name"])
            new_email = ec2.text_input(t("email_label").replace(" *", ""), value=target["email"])
            new_emp_num = ec1.text_input(t("employee_number_label"), value=target["employee_number"] or "")
            new_phone = ec2.text_input(t("phone_label"), value=target["phone"] or "")
            new_role = ec1.selectbox(
                t("role_label"), ROLES, index=ROLES.index(target_role),
                format_func=lambda r: ROLE_LABELS_AR.get(r, r),
            )
            new_active = ec2.toggle(t("suspend_account_label"), value=target_active)

            new_managed = target["managed_branch_ids"]
            if new_role in ("branch", "manager"):
                branch_options = {f"{b['code']} - {b['name_ar']}": b["id"] for b in branches}
                id_to_label = {v: k for k, v in branch_options.items()}
                default_labels = [id_to_label[bid] for bid in target["managed_branch_ids"] if bid in id_to_label]
                chosen = st.multiselect(t("managed_branches_label"), list(branch_options.keys()), default=default_labels)
                new_managed = [branch_options[c] for c in chosen]

            if st.form_submit_button(t("save_changes_btn")):
                with get_session() as s:
                    t_ = s.query(User).get(uid)
                    before = {"active": t_.active, "role": t_.role, "name": t_.name, "email": t_.email}
                    t_.name = new_name
                    t_.email = new_email.strip().lower()
                    t_.employee_number = new_emp_num or None
                    t_.phone = new_phone or None
                    t_.role = new_role
                    t_.active = new_active
                    t_.managed_branch_ids = json.dumps(new_managed)
                    log_action(user["email"], "update", "user", uid, before=before,
                               after={"active": new_active, "role": new_role, "name": new_name, "email": new_email})
                st.success(t("updated_msg"))
                st.rerun()

# ==================================================================
# تبويب: طلبات إنشاء حسابات جديدة
# ==================================================================
with tab_signups:
    st.subheader(t("pending_signups_title"))
    with get_session() as s:
        pending = s.query(SignupRequest).filter(SignupRequest.status == "pending").order_by(SignupRequest.created_at).all()
        pending_data = [{
            "id": r.id, "name": f"{r.first_name} {r.last_name}", "email": r.email,
            "employee_number": r.employee_number or "—", "created_at": r.created_at,
        } for r in pending]

    if not pending_data:
        st.success(t("no_pending_signups"))
    else:
        for req in pending_data:
            with st.container(border=True):
                cols = st.columns([3, 2, 2, 2, 1, 1])
                cols[0].write(f"**{req['name']}**")
                cols[1].write(req["email"])
                cols[2].write(f"{t('employee_number_col')}: {req['employee_number']}")
                role_choice = cols[3].selectbox(
                    t("assign_role_label"), ROLES, format_func=lambda r: ROLE_LABELS_AR.get(r, r),
                    key=f"role_choice_{req['id']}", label_visibility="collapsed",
                )
                if cols[4].button(t("approve_btn"), key=f"approve_signup_{req['id']}", use_container_width=True):
                    ok, _ = approve_signup_request(req["id"], user["email"], role=role_choice)
                    if ok:
                        st.toast(t("signup_approved_toast"))
                    else:
                        st.error(t("err_email_exists"))
                    st.rerun()
                if cols[5].button(t("reject_btn"), key=f"reject_signup_{req['id']}", use_container_width=True):
                    reject_signup_request(req["id"], user["email"])
                    st.toast(t("signup_rejected_toast"))
                    st.rerun()

# ==================================================================
# تبويب: طلبات استعادة كلمة المرور
# ==================================================================
with tab_resets:
    st.subheader(t("pending_resets_title"))
    with get_session() as s:
        pending_r = s.query(PasswordResetRequest).filter(PasswordResetRequest.status == "pending").order_by(PasswordResetRequest.created_at).all()
        pending_r_data = [{"id": r.id, "email": r.email, "created_at": r.created_at} for r in pending_r]

    if not pending_r_data:
        st.success(t("no_pending_resets"))
    else:
        for req in pending_r_data:
            with st.container(border=True):
                cols = st.columns([4, 2, 1, 1])
                cols[0].write(f"**{req['email']}**")
                cols[1].write(str(req["created_at"]))
                if cols[2].button(t("approve_btn"), key=f"approve_reset_{req['id']}", use_container_width=True):
                    approve_password_reset(req["id"], user["email"])
                    st.toast(t("reset_approved_toast"))
                    st.rerun()
                if cols[3].button(t("reject_btn"), key=f"reject_reset_{req['id']}", use_container_width=True):
                    reject_password_reset(req["id"], user["email"])
                    st.toast(t("reset_rejected_toast"))
                    st.rerun()

