import streamlit as st
from auth import login, logout, current_user, ROLE_LABELS_AR, hash_password
from database import init_db, get_session
from models import User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion

st.set_page_config(
    page_title="نظام NXN لإدارة جودة الفروع",
    page_icon="✅",
    layout="wide",
)

# ---------- التأكد من وجود الجداول، وتهيئة أولى إن لم يوجد أي مستخدم ----------
init_db()

with get_session() as _s:
    _has_users = _s.query(User).count() > 0

if not _has_users:
    st.title("✅ نظام NXN لإدارة جودة الفروع")
    st.subheader("⚙️ التهيئة الأولى — إنشاء حساب المالك")
    st.info("لا يوجد أي مستخدم في النظام بعد. أنشئ حساب المالك الأول لتبدأ استخدام النظام (تُنشأ أيضًا فروع وأسئلة تجريبية تلقائيًا).")

    with st.form("initial_setup"):
        owner_email = st.text_input("البريد الإلكتروني *")
        owner_name = st.text_input("الاسم *")
        owner_password = st.text_input("كلمة المرور *", type="password")
        owner_password2 = st.text_input("تأكيد كلمة المرور *", type="password")
        submitted = st.form_submit_button("🚀 إنشاء الحساب وبدء النظام")

        if submitted:
            if not owner_email or not owner_name or not owner_password:
                st.error("الرجاء تعبئة جميع الحقول المطلوبة (*)")
            elif owner_password != owner_password2:
                st.error("كلمتا المرور غير متطابقتين")
            else:
                with get_session() as s:
                    owner = User(email=owner_email.strip().lower(), name=owner_name, role="owner")
                    s.add(owner)
                    s.flush()
                    s.add(Credential(user_id=owner.id, password_hash=hash_password(owner_password)))

                    if s.query(Branch).count() == 0:
                        s.add_all([
                            Branch(code="BR-001", name_ar="فرع الرياض الرئيسي", name_en="Riyadh Main Branch",
                                   region="الرياض", city="الرياض", status="active"),
                            Branch(code="BR-002", name_ar="فرع جدة", name_en="Jeddah Branch",
                                   region="مكة المكرمة", city="جدة", status="active"),
                        ])

                    if s.query(ChecklistVersion).count() == 0:
                        s.add(ChecklistVersion(code="QV1", name_ar="نسخة الفحص الأولى", name_en="Checklist v1",
                                                status="active", created_by=owner_email))

                    if s.query(AuditSection).count() == 0:
                        sec1 = AuditSection(code="SEC-SAFETY", name_ar="السلامة", name_en="Safety",
                                             weight=40, sort_order=1, active=True)
                        sec2 = AuditSection(code="SEC-SERVICE", name_ar="جودة الخدمة", name_en="Service Quality",
                                             weight=60, sort_order=2, active=True)
                        s.add_all([sec1, sec2])
                        s.flush()
                        s.add_all([
                            AuditQuestion(section_id=sec1.id, code="Q-001",
                                          question_ar="هل يوجد طفايات حريق سارية الصلاحية؟",
                                          question_en="Are fire extinguishers valid?",
                                          weight=10, checklist_version="QV1", sort_order=1),
                            AuditQuestion(section_id=sec1.id, code="Q-002",
                                          question_ar="هل مخارج الطوارئ غير مسدودة؟",
                                          question_en="Are emergency exits unobstructed?",
                                          weight=10, checklist_version="QV1", sort_order=2),
                            AuditQuestion(section_id=sec2.id, code="Q-003",
                                          question_ar="هل الموظفون يرتدون الزي الرسمي؟",
                                          question_en="Are staff wearing uniforms?",
                                          weight=15, checklist_version="QV1", sort_order=1),
                            AuditQuestion(section_id=sec2.id, code="Q-004",
                                          question_ar="هل تم الرد على العميل خلال دقيقتين؟",
                                          question_en="Was the customer greeted within 2 minutes?",
                                          weight=15, checklist_version="QV1", sort_order=2),
                        ])
                st.success("🎉 تم إنشاء الحساب بنجاح! سجّل الدخول الآن من الأسفل.")
                st.rerun()
    st.stop()

st.markdown(
    """
    <style>
    .block-container { direction: rtl; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("✅ نظام NXN لإدارة جودة الفروع")
st.caption("النسخة البايثونية — Streamlit + PostgreSQL")

user = current_user()

if user:
    st.success(f"مرحبًا **{user['name']}** — الدور: {ROLE_LABELS_AR.get(user['role'], user['role'])}")
    st.info("استخدم القائمة الجانبية للتنقّل بين صفحات النظام: الداشبورد، الفروع، التدقيقات، الإجراءات التصحيحية، التقارير، المستخدمين، وسجل النشاط.")
    if st.button("🚪 تسجيل الخروج"):
        logout()
        st.rerun()
else:
    st.subheader("🔐 تسجيل الدخول")
    with st.form("login_form"):
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")

        if submitted:
            ok, msg = login(email, password)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.caption("أول مرة؟ شغّل `python seed.py` لإنشاء مستخدم مالك افتراضي (راجع ملف .env).")
