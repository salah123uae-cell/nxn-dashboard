import streamlit as st
from branding import render_logo, apply_theme
import pandas as pd

from auth import require_login, current_user, log_action
from database import get_session
from models import Branch
from data_cache import clear_reference_cache

st.set_page_config(page_title="الفروع", page_icon="🏢", layout="wide")
apply_theme()
render_logo(size="small")
require_login()
user = current_user()
can_edit = user["role"] in ("owner", "manager")

st.title("🏢 إدارة الفروع")

with get_session() as s:
    branches = s.query(Branch).order_by(Branch.id).all()
    data = [{
        "المعرف": b.id, "الكود": b.code, "الاسم (عربي)": b.name_ar, "الاسم (English)": b.name_en,
        "المنطقة": b.region, "المدينة": b.city, "الحالة": b.status, "مدير الفرع": b.manager_email or "—",
    } for b in branches]

st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

if can_edit:
    st.divider()
    st.subheader("➕ إضافة فرع جديد")
    with st.form("add_branch"):
        c1, c2 = st.columns(2)
        code = c1.text_input("كود الفرع *")
        region = c2.text_input("المنطقة *")
        name_ar = c1.text_input("الاسم بالعربي *")
        name_en = c2.text_input("الاسم بالإنجليزي *")
        city = c1.text_input("المدينة")
        manager_email = c2.text_input("بريد مدير الفرع")
        address = st.text_area("العنوان")
        status = st.selectbox("الحالة", ["active", "inactive", "suspended"])

        if st.form_submit_button("حفظ الفرع"):
            if not code or not region or not name_ar or not name_en:
                st.error("الرجاء تعبئة الحقول المطلوبة (*)")
            else:
                with get_session() as s:
                    exists = s.query(Branch).filter(Branch.code == code).first()
                    if exists:
                        st.error("كود الفرع مستخدم مسبقًا")
                    else:
                        b = Branch(code=code, name_ar=name_ar, name_en=name_en, region=region,
                                   city=city, manager_email=manager_email or None,
                                   address=address, status=status)
                        s.add(b)
                        s.flush()
                        log_action(user["email"], "create", "branch", b.id, after={"code": code})
                        clear_reference_cache()
                        st.success("تم إضافة الفرع ✅")
                        st.rerun()

    st.divider()
    st.subheader("✏️ تعديل / تغيير حالة فرع")
    if branches:
        options = {f"{b.code} - {b.name_ar}": b.id for b in branches}
        choice = st.selectbox("اختر الفرع", list(options.keys()))
        branch_id = options[choice]
        new_status = st.selectbox("الحالة الجديدة", ["active", "inactive", "suspended"], key="edit_status")
        if st.button("تحديث الحالة"):
            with get_session() as s:
                b = s.query(Branch).get(branch_id)
                before = {"status": b.status}
                b.status = new_status
                log_action(user["email"], "update", "branch", branch_id, before=before, after={"status": new_status})
            clear_reference_cache()
            st.success("تم التحديث ✅")
            st.rerun()
else:
    st.info("ليس لديك صلاحية تعديل الفروع (متاح فقط للمالك والمدير)")
