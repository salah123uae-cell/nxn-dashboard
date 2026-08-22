import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd
import json

from auth import require_role, current_user, hash_password, log_action, ROLES, ROLE_LABELS_AR
from database import get_session
from models import User, Credential, Branch
from data_cache import get_branches_cached

st.set_page_config(page_title="المستخدمون", page_icon="👥", layout="wide")
apply_theme()
render_logo(size="small")
require_role("owner", "manager")
user = current_user()

st.title("👥 إدارة المستخدمين")

with get_session() as s:
    users = s.query(User).order_by(User.id).all()
    rows = [{
        "المعرف": u.id, "البريد": u.email, "الاسم": u.name,
        "الدور": ROLE_LABELS_AR.get(u.role, u.role), "نشط": u.active,
        "آخر دخول": u.last_login_at,
    } for u in users]

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.subheader("➕ إضافة مستخدم جديد")

branches = get_branches_cached()

with st.form("add_user"):
    c1, c2 = st.columns(2)
    email = c1.text_input("البريد الإلكتروني *")
    name = c2.text_input("الاسم *")
    role = c1.selectbox("الدور", ROLES, format_func=lambda r: ROLE_LABELS_AR.get(r, r))
    password = c2.text_input("كلمة المرور المبدئية *", type="password")
    phone = st.text_input("رقم الجوال")

    managed_branches = []
    if role in ("branch", "manager"):
        branch_options = {f"{b['code']} - {b['name_ar']}": b["id"] for b in branches}
        chosen = st.multiselect("الفروع المُدارة", list(branch_options.keys()))
        managed_branches = [branch_options[c] for c in chosen]

    if st.form_submit_button("إنشاء المستخدم"):
        if not email or not name or not password:
            st.error("الرجاء تعبئة الحقول المطلوبة (*)")
        else:
            with get_session() as s:
                exists = s.query(User).filter(User.email == email.strip().lower()).first()
                if exists:
                    st.error("البريد الإلكتروني مستخدم مسبقًا")
                else:
                    new_user = User(
                        email=email.strip().lower(), name=name, role=role,
                        managed_branch_ids=json.dumps(managed_branches), phone=phone or None,
                    )
                    s.add(new_user)
                    s.flush()
                    s.add(Credential(user_id=new_user.id, password_hash=hash_password(password)))
                    log_action(user["email"], "create", "user", new_user.id, after={"email": email, "role": role})
            st.success("تم إنشاء المستخدم ✅")
            st.rerun()

st.divider()
st.subheader("⚙️ تعديل حالة مستخدم")

if users:
    options = {f"{u.email} ({u.name})": u.id for u in users}
    choice = st.selectbox("اختر المستخدم", list(options.keys()))
    uid = options[choice]

    with get_session() as s:
        target = s.query(User).get(uid)
        target_active = target.active
        target_role = target.role

    c1, c2 = st.columns(2)
    new_active = c1.toggle("نشط", value=target_active)
    new_role = c2.selectbox("الدور", ROLES, index=ROLES.index(target_role), format_func=lambda r: ROLE_LABELS_AR.get(r, r))

    if st.button("حفظ التعديلات"):
        with get_session() as s:
            t = s.query(User).get(uid)
            before = {"active": t.active, "role": t.role}
            t.active = new_active
            t.role = new_role
            log_action(user["email"], "update", "user", uid, before=before, after={"active": new_active, "role": new_role})
        st.success("تم التحديث ✅")
        st.rerun()
