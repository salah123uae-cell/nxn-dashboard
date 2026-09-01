import streamlit as st
from auth import (
    login, current_user, ROLE_LABELS_AR, hash_password, render_logout_sidebar,
    create_signup_request, create_password_reset_request,
)
from database import init_db, get_session
from models import User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion, Audit, CorrectiveAction
from branding import render_logo, apply_theme, render_hero_banner
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo()

# قبل تسجيل الدخول: نخفي سهم فتح/طيّ الشريط الجانبي بالكامل (لا حاجة له
# بصفحة تسجيل الدخول أصلًا بما إن القائمة مخفية حتى الدخول).
if not current_user():
    st.markdown(
        '<style>[data-testid="collapsedControl"] {display: none !important;}</style>',
        unsafe_allow_html=True,
    )

# ---------- التأكد من وجود الجداول (مرة واحدة فقط بكل جلسة، لتفادي الفحص المتكرر) ----------
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

with get_session() as _s:
    _has_users = _s.query(User).count() > 0

if not _has_users:
    render_hero_banner(title=t("app_title"), subtitle=t("setup_title"))
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

render_hero_banner(title=t("app_title"), subtitle=t("app_caption"))

user = current_user()

if user:
    render_logout_sidebar()
    role_label = ROLE_LABELS_AR.get(user["role"], user["role"])
    welcome_text = t("welcome_msg", name=user["name"], role=role_label).replace("**", "")
    render_hero_banner(title=welcome_text, subtitle=t("nav_hint"))

    # ---------- داشبورد حي: مؤشرات لحظية مباشرة أعلى الصفحة الرئيسية ----------
    with get_session() as _s:
        _total_branches = _s.query(Branch).filter(Branch.status == "active").count()
        _total_audits = _s.query(Audit).count()
        _open_actions = _s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(["open", "in_progress"])
        ).count()
        _scored = [a.score for a in _s.query(Audit).filter(Audit.score.isnot(None)).all()]
    _avg_score = round(sum(_scored) / len(_scored), 1) if _scored else 0

    st.markdown(f"##### {t('live_dashboard_title')}")
    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric(t('nav_branches'), _total_branches)
    lc2.metric(t('total_audits'), _total_audits)
    lc3.metric(t('open_corrective_actions'), _open_actions)
    lc4.metric(t('avg_score'), f"{_avg_score}%")
    st.divider()

    # ---------- الإشعارات ----------
    from notifications import get_notifications, get_unread_count, mark_as_read, mark_all_as_read
    _unread = get_unread_count(user["id"])
    _notif_title = t("notifications_title") + (f" ({_unread})" if _unread else "")
    with st.expander(_notif_title, expanded=bool(_unread)):
        _notifs = get_notifications(user["id"])
        if not _notifs:
            st.caption(t("no_notifications"))
        else:
            if _unread and st.button(t("mark_all_read_btn"), key="mark_all_read"):
                mark_all_as_read(user["id"])
                st.rerun()
            for n in _notifs:
                nc1, nc2 = st.columns([5, 1])
                is_unread = n["read_at"] is None
                prefix = "**" if is_unread else ""
                nc1.markdown(f"{prefix}{n['title']}{prefix}  \n{n['body']}")
                if is_unread:
                    if nc2.button(t("mark_read_btn"), key=f"read_{n['id']}"):
                        mark_as_read(n["id"])
                        st.rerun()
                st.divider()
    st.divider()
else:
    tab_login, tab_signup, tab_forgot = st.tabs([
        t("login_tab_login"), t("login_tab_signup"), t("login_tab_forgot"),
    ])

    with tab_login:
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

    with tab_signup:
        st.subheader(t("login_tab_signup"))
        with st.form("signup_form"):
            sc1, sc2 = st.columns(2)
            s_first = sc1.text_input(t("first_name_label"))
            s_last = sc2.text_input(t("last_name_label"))
            s_email = st.text_input(t("email_label"))
            s_emp_num = st.text_input(t("employee_number_label"))
            s_pass1 = st.text_input(t("new_password_label2"), type="password")
            s_pass2 = st.text_input(t("confirm_new_password_label"), type="password")
            signup_submitted = st.form_submit_button(t("signup_submit_btn"))

            if signup_submitted:
                if not s_first or not s_last or not s_email or not s_pass1:
                    st.error(t("fill_required"))
                elif s_pass1 != s_pass2:
                    st.error(t("password_mismatch"))
                else:
                    ok, msg_key = create_signup_request(s_first, s_last, s_email, s_emp_num, s_pass1)
                    if ok:
                        st.success(t("signup_success"))
                    else:
                        st.error(t("err_" + msg_key))

    with tab_forgot:
        st.subheader(t("login_tab_forgot"))
        st.info(t("forgot_password_info"))
        with st.form("forgot_password_form"):
            f_email = st.text_input(t("email_label").replace(" *", ""), key="forgot_email")
            f_pass1 = st.text_input(t("new_password_label2"), type="password", key="forgot_pass1")
            f_pass2 = st.text_input(t("confirm_new_password_label"), type="password", key="forgot_pass2")
            forgot_submitted = st.form_submit_button(t("forgot_password_submit_btn"))

            if forgot_submitted:
                if not f_email or not f_pass1:
                    st.error(t("fill_required"))
                elif f_pass1 != f_pass2:
                    st.error(t("password_mismatch"))
                else:
                    ok, msg_key = create_password_reset_request(f_email, f_pass1)
                    if ok:
                        st.success(t("reset_request_success"))
                    else:
                        st.error(t("err_" + msg_key))
import streamlit as st
from auth import (
    login, current_user, ROLE_LABELS_AR, hash_password, render_logout_sidebar,
    create_signup_request, create_password_reset_request,
)
from database import init_db, get_session
from models import User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion, Audit, CorrectiveAction
from branding import render_logo, apply_theme, render_hero_banner
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo()

# قبل تسجيل الدخول: نخفي سهم فتح/طيّ الشريط الجانبي بالكامل (لا حاجة له
# بصفحة تسجيل الدخول أصلًا بما إن القائمة مخفية حتى الدخول).
if not current_user():
    st.markdown(
        '<style>[data-testid="collapsedControl"] {display: none !important;}</style>',
        unsafe_allow_html=True,
    )

# ---------- التأكد من وجود الجداول (مرة واحدة فقط بكل جلسة، لتفادي الفحص المتكرر) ----------
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

with get_session() as _s:
    _has_users = _s.query(User).count() > 0

if not _has_users:
    render_hero_banner(title=t("app_title"), subtitle=t("setup_title"))
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

render_hero_banner(title=t("app_title"), subtitle=t("app_caption"))

user = current_user()

if user:
    render_logout_sidebar()
    role_label = ROLE_LABELS_AR.get(user["role"], user["role"])
    welcome_text = t("welcome_msg", name=user["name"], role=role_label).replace("**", "")
    render_hero_banner(title=welcome_text, subtitle=t("nav_hint"))

    # ---------- داشبورد حي: مؤشرات لحظية مباشرة أعلى الصفحة الرئيسية ----------
    with get_session() as _s:
        _total_branches = _s.query(Branch).filter(Branch.status == "active").count()
        _total_audits = _s.query(Audit).count()
        _open_actions = _s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(["open", "in_progress"])
        ).count()
        _scored = [a.score for a in _s.query(Audit).filter(Audit.score.isnot(None)).all()]
    _avg_score = round(sum(_scored) / len(_scored), 1) if _scored else 0

    st.markdown(f"##### {t('live_dashboard_title')}")
    lc1, lc2, lc3, lc4 = st.columns(4)
    lc1.metric(t('nav_branches'), _total_branches)
    lc2.metric(t('total_audits'), _total_audits)
    lc3.metric(t('open_corrective_actions'), _open_actions)
    lc4.metric(t('avg_score'), f"{_avg_score}%")
    st.divider()
else:
    tab_login, tab_signup, tab_forgot = st.tabs([
        t("login_tab_login"), t("login_tab_signup"), t("login_tab_forgot"),
    ])

    with tab_login:
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

    with tab_signup:
        st.subheader(t("login_tab_signup"))
        with st.form("signup_form"):
            sc1, sc2 = st.columns(2)
            s_first = sc1.text_input(t("first_name_label"))
            s_last = sc2.text_input(t("last_name_label"))
            s_email = st.text_input(t("email_label"))
            s_emp_num = st.text_input(t("employee_number_label"))
            s_pass1 = st.text_input(t("new_password_label2"), type="password")
            s_pass2 = st.text_input(t("confirm_new_password_label"), type="password")
            signup_submitted = st.form_submit_button(t("signup_submit_btn"))

            if signup_submitted:
                if not s_first or not s_last or not s_email or not s_pass1:
                    st.error(t("fill_required"))
                elif s_pass1 != s_pass2:
                    st.error(t("password_mismatch"))
                else:
                    ok, msg_key = create_signup_request(s_first, s_last, s_email, s_emp_num, s_pass1)
                    if ok:
                        st.success(t("signup_success"))
                    else:
                        st.error(t("err_" + msg_key))

    with tab_forgot:
        st.subheader(t("login_tab_forgot"))
        st.info(t("forgot_password_info"))
        with st.form("forgot_password_form"):
            f_email = st.text_input(t("email_label").replace(" *", ""), key="forgot_email")
            f_pass1 = st.text_input(t("new_password_label2"), type="password", key="forgot_pass1")
            f_pass2 = st.text_input(t("confirm_new_password_label"), type="password", key="forgot_pass2")
            forgot_submitted = st.form_submit_button(t("forgot_password_submit_btn"))

            if forgot_submitted:
                if not f_email or not f_pass1:
                    st.error(t("fill_required"))
                elif f_pass1 != f_pass2:
                    st.error(t("password_mismatch"))
                else:
                    ok, msg_key = create_password_reset_request(f_email, f_pass1)
                    if ok:
                        st.success(t("reset_request_success"))
                    else:
                        st.error(t("err_" + msg_key))

