import streamlit as st
from auth import login, current_user, ROLE_LABELS_AR, hash_password, render_logout_sidebar
from database import init_db, get_session
from models import User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion
from branding import render_logo, apply_theme
from i18n import t, language_switcher, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo()

language_switcher()

# ---------- التأكد من وجود الجداول (مرة واحدة فقط بكل جلسة، لتفادي الفحص المتكرر) ----------
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

with get_session() as _s:
    _has_users = _s.query(User).count() > 0

if not _has_users:
    st.title(t("app_title"))
    st.subheader(t("setup_title"))
    st.info(t("setup_info"))

    with st.form("initial_setup"):
        owner_email = st.text_input(t("email_label"))
        owner_name = st.text_input(t("name_label"))
        owner_password = st.text_input(t("password_label"), type="password")
        owner_password2 = st.text_input(t("password_confirm_label"), type="password")
        submitted = st.form_submit_button(t("create_account_btn"))

        if submitted:
            if not owner_email or not owner_name or not owner_password:
                st.error(t("fill_required"))
            elif owner_password != owner_password2:
                st.error(t("password_mismatch"))
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
                st.success(t("account_created"))
                st.rerun()

    st.divider()
    st.subheader(t("restore_setup_title"))
    restore_file = st.file_uploader(t("restore_setup_uploader"), type=["json"], key="setup_restore_uploader")
    if restore_file is not None:
        if st.button(t("restore_setup_btn"), key="setup_restore_btn"):
            from backup import import_all_data
            try:
                counts = import_all_data(restore_file.getvalue())
                st.success(f"{t('import_success')} {counts}")
                st.rerun()
            except Exception as e:
                st.error(f"{t('import_error')}: {e}")

    st.stop()

st.title(t("app_title"))
st.caption(t("app_caption"))

user = current_user()

if user:
    render_logout_sidebar()
    role_label = ROLE_LABELS_AR.get(user["role"], user["role"])
    st.success(t("welcome_msg", name=user["name"], role=role_label))
    st.info(t("nav_hint"))
else:
    st.subheader(t("login_title"))
    with st.form("login_form"):
        email = st.text_input(t("email_label").replace(" *", ""))
        password = st.text_input(t("password_label").replace(" *", ""), type="password")
        submitted = st.form_submit_button(t("login_btn"))

        if submitted:
            ok, msg = login(email, password)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.caption(t("first_time_hint"))
