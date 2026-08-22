"""
وحدة دعم تعدد اللغات (i18n) لكل صفحات النظام — عربي/إنجليزي.
تحفظ اللغة المختارة في st.session_state وتوفر دالة t(key) للترجمة،
ودالة language_switcher() لعرض قائمة اختيار اللغة بالشريط الجانبي.
"""
import streamlit as st

TRANSLATIONS = {
    # ---------- عام / مشترك ----------
    "language_label": {"ar": "🌐 اللغة", "en": "🌐 Language"},
    "logout": {"ar": "🚪 تسجيل الخروج", "en": "🚪 Logout"},
    "login_required": {"ar": "🔒 الرجاء تسجيل الدخول أولاً من الصفحة الرئيسية", "en": "🔒 Please log in first from the home page"},
    "no_permission": {"ar": "🚫 ليس لديك صلاحية للوصول لهذه الصفحة", "en": "🚫 You don't have permission to access this page"},
    "save": {"ar": "حفظ", "en": "Save"},
    "update": {"ar": "تحديث", "en": "Update"},
    "add": {"ar": "إضافة", "en": "Add"},
    "code_col": {"ar": "الكود", "en": "Code"},
    "name_ar_col": {"ar": "الاسم (عربي)", "en": "Name (Arabic)"},
    "name_en_col": {"ar": "الاسم (English)", "en": "Name (English)"},
    "status_col": {"ar": "الحالة", "en": "Status"},
    "count_col": {"ar": "العدد", "en": "Count"},
    "branch_col": {"ar": "الفرع", "en": "Branch"},
    "score_col": {"ar": "النتيجة", "en": "Score"},
    "title_col": {"ar": "العنوان", "en": "Title"},
    "owner_col": {"ar": "المسؤول", "en": "Owner"},
    "priority_col": {"ar": "الأولوية", "en": "Priority"},
    "due_col": {"ar": "الاستحقاق", "en": "Due"},
    "reference_col": {"ar": "المرجع", "en": "Reference"},
    "auditor_col": {"ar": "المدقق", "en": "Auditor"},
    "created_at_col": {"ar": "تاريخ الإنشاء", "en": "Created At"},

    # ---------- app.py (تسجيل الدخول / التهيئة الأولى) ----------
    "app_title": {"ar": "✅ نظام NXN لإدارة جودة الفروع", "en": "✅ NXN Branch Quality Management System"},
    "app_caption": {"ar": "النسخة البايثونية — Streamlit", "en": "Python Edition — Streamlit"},
    "setup_title": {"ar": "⚙️ التهيئة الأولى — إنشاء حساب المالك", "en": "⚙️ First-Time Setup — Create Owner Account"},
    "setup_info": {"ar": "لا يوجد أي مستخدم في النظام بعد. أنشئ حساب المالك الأول لتبدأ استخدام النظام (تُنشأ أيضًا فروع وأسئلة تجريبية تلقائيًا).",
                   "en": "No users exist yet. Create the first owner account to start using the system (sample branches and questions are created automatically)."},
    "email_label": {"ar": "البريد الإلكتروني *", "en": "Email *"},
    "name_label": {"ar": "الاسم *", "en": "Name *"},
    "password_label": {"ar": "كلمة المرور *", "en": "Password *"},
    "password_confirm_label": {"ar": "تأكيد كلمة المرور *", "en": "Confirm Password *"},
    "create_account_btn": {"ar": "🚀 إنشاء الحساب وبدء النظام", "en": "🚀 Create Account & Start"},
    "fill_required": {"ar": "الرجاء تعبئة جميع الحقول المطلوبة (*)", "en": "Please fill in all required fields (*)"},
    "password_mismatch": {"ar": "كلمتا المرور غير متطابقتين", "en": "Passwords do not match"},
    "account_created": {"ar": "🎉 تم إنشاء الحساب بنجاح! سجّل الدخول الآن من الأسفل.", "en": "🎉 Account created successfully! Log in below."},
    "welcome_msg": {"ar": "مرحبًا **{name}** — الدور: {role}", "en": "Welcome **{name}** — Role: {role}"},
    "nav_hint": {"ar": "استخدم القائمة الجانبية للتنقّل بين صفحات النظام.", "en": "Use the sidebar to navigate between system pages."},
    "login_title": {"ar": "🔐 تسجيل الدخول", "en": "🔐 Login"},
    "login_btn": {"ar": "دخول", "en": "Log in"},
    "first_time_hint": {"ar": "أول مرة؟ أنشئ حساب المالك من النموذج أعلاه.", "en": "First time? Create the owner account from the form above."},

    # ---------- Dashboard ----------
    "dashboard_title": {"ar": "📊 لوحة المعلومات", "en": "📊 Dashboard"},
    "total_audits": {"ar": "إجمالي التدقيقات", "en": "Total Audits"},
    "closed_audits": {"ar": "مكتملة (مغلقة)", "en": "Closed"},
    "in_progress": {"ar": "قيد التنفيذ", "en": "In Progress"},
    "avg_score": {"ar": "متوسط النتيجة", "en": "Average Score"},
    "status_distribution": {"ar": "توزيع حالات التدقيق", "en": "Audit Status Distribution"},
    "score_by_branch": {"ar": "متوسط النتيجة حسب الفرع", "en": "Average Score by Branch"},
    "no_audit_data": {"ar": "لا توجد بيانات تدقيق بعد", "en": "No audit data yet"},
    "no_score_data": {"ar": "لا توجد نتائج محسوبة بعد", "en": "No scores calculated yet"},
    "open_corrective_actions": {"ar": "🛠️ الإجراءات التصحيحية المفتوحة", "en": "🛠️ Open Corrective Actions"},
    "no_open_actions": {"ar": "لا توجد إجراءات تصحيحية مفتوحة 🎉", "en": "No open corrective actions 🎉"},

    # ---------- Branches ----------
    "branches_title": {"ar": "🏢 إدارة الفروع", "en": "🏢 Branch Management"},
    "region_col": {"ar": "المنطقة", "en": "Region"},
    "city_col": {"ar": "المدينة", "en": "City"},
    "branch_manager_col": {"ar": "مدير الفرع", "en": "Branch Manager"},
    "add_branch_title": {"ar": "➕ إضافة فرع جديد", "en": "➕ Add New Branch"},
    "branch_code_label": {"ar": "كود الفرع *", "en": "Branch Code *"},
    "region_label": {"ar": "المنطقة *", "en": "Region *"},
    "name_ar_label": {"ar": "الاسم بالعربي *", "en": "Arabic Name *"},
    "name_en_label": {"ar": "الاسم بالإنجليزي *", "en": "English Name *"},
    "city_label": {"ar": "المدينة", "en": "City"},
    "manager_email_label": {"ar": "بريد مدير الفرع", "en": "Manager Email"},
    "address_label": {"ar": "العنوان", "en": "Address"},
    "save_branch_btn": {"ar": "حفظ الفرع", "en": "Save Branch"},
    "branch_code_exists": {"ar": "كود الفرع مستخدم مسبقًا", "en": "Branch code already in use"},
    "branch_added": {"ar": "تم إضافة الفرع ✅", "en": "Branch added ✅"},
    "edit_branch_title": {"ar": "✏️ تعديل / تغيير حالة فرع", "en": "✏️ Edit / Change Branch Status"},
    "select_branch": {"ar": "اختر الفرع", "en": "Select Branch"},
    "new_status_label": {"ar": "الحالة الجديدة", "en": "New Status"},
    "update_status_btn": {"ar": "تحديث الحالة", "en": "Update Status"},
    "updated_msg": {"ar": "تم التحديث ✅", "en": "Updated ✅"},
    "no_branch_edit_permission": {"ar": "ليس لديك صلاحية تعديل الفروع (متاح فقط للمالك والمدير)", "en": "You don't have permission to edit branches (owner/manager only)"},

    # ---------- Checklist ----------
    "checklist_title": {"ar": "📋 قوائم الفحص (Checklist)", "en": "📋 Checklist"},
    "tab_versions": {"ar": "نُسخ التشيك ليست", "en": "Checklist Versions"},
    "tab_sections": {"ar": "الأقسام", "en": "Sections"},
    "tab_questions": {"ar": "الأسئلة", "en": "Questions"},
    "created_by_col": {"ar": "أنشأها", "en": "Created By"},
    "add_version_title": {"ar": "➕ إضافة نسخة جديدة", "en": "➕ Add New Version"},
    "version_code_label": {"ar": "الكود (مثال: QV2)", "en": "Code (e.g. QV2)"},
    "weight_col": {"ar": "الوزن", "en": "Weight"},
    "sort_order_col": {"ar": "الترتيب", "en": "Sort Order"},
    "active_col": {"ar": "مفعّل", "en": "Active"},
    "add_section_title": {"ar": "➕ إضافة قسم جديد", "en": "➕ Add New Section"},
    "section_code_label": {"ar": "كود القسم", "en": "Section Code"},
    "weight_label": {"ar": "الوزن", "en": "Weight"},
    "sort_order_label": {"ar": "ترتيب العرض", "en": "Display Order"},
    "save_section_btn": {"ar": "حفظ القسم", "en": "Save Section"},
    "section_col": {"ar": "القسم", "en": "Section"},
    "question_col": {"ar": "السؤال", "en": "Question"},
    "checklist_version_col": {"ar": "نسخة التشيك ليست", "en": "Checklist Version"},
    "add_question_title": {"ar": "➕ إضافة سؤال جديد", "en": "➕ Add New Question"},
    "question_code_label": {"ar": "كود السؤال", "en": "Question Code"},
    "question_ar_label": {"ar": "نص السؤال بالعربي", "en": "Question Text (Arabic)"},
    "question_en_label": {"ar": "نص السؤال بالإنجليزي", "en": "Question Text (English)"},
    "question_weight_label": {"ar": "وزن السؤال", "en": "Question Weight"},
    "save_question_btn": {"ar": "حفظ السؤال", "en": "Save Question"},

    # ---------- Audits ----------
    "audits_title": {"ar": "🔍 التدقيقات", "en": "🔍 Audits"},
    "tab_audit_list": {"ar": "📄 قائمة التدقيقات", "en": "📄 Audit List"},
    "tab_new_audit": {"ar": "➕ تدقيق جديد", "en": "➕ New Audit"},
    "tab_conduct": {"ar": "📝 تنفيذ / مراجعة تدقيق", "en": "📝 Conduct / Review Audit"},
    "filter_by_status": {"ar": "تصفية حسب الحالة", "en": "Filter by Status"},
    "export_excel": {"ar": "⬇️ تصدير Excel", "en": "⬇️ Export Excel"},
    "no_create_permission": {"ar": "ليس لديك صلاحية إنشاء تدقيقات جديدة", "en": "You don't have permission to create new audits"},
    "no_active_branches": {"ar": "لا توجد فروع نشطة. أضف فرعًا أولًا من صفحة الفروع.", "en": "No active branches. Add a branch first from the Branches page."},
    "auditor_email_label": {"ar": "بريد المدقق", "en": "Auditor Email"},
    "schedule_date_label": {"ar": "تاريخ الجدولة", "en": "Scheduled Date"},
    "checklist_version_label": {"ar": "نسخة التشيك ليست", "en": "Checklist Version"},
    "create_audit_btn": {"ar": "إنشاء التدقيق", "en": "Create Audit"},
    "audit_created": {"ar": "تم إنشاء التدقيق: {ref} ✅", "en": "Audit created: {ref} ✅"},
    "no_audits_available": {"ar": "لا توجد تدقيقات متاحة للتنفيذ حاليًا", "en": "No audits available to conduct right now"},
    "select_audit": {"ar": "اختر التدقيق", "en": "Select Audit"},
    "audit_summary_line": {"ar": "**الفرع:** {branch} | **الحالة:** {status} | **النتيجة الحالية:** {score}",
                            "en": "**Branch:** {branch} | **Status:** {status} | **Current Score:** {score}"},
    "note_placeholder": {"ar": "ملاحظة (اختياري)", "en": "Note (optional)"},
    "note_label": {"ar": "ملاحظة", "en": "Note"},
    "answer_label": {"ar": "الإجابة", "en": "Answer"},
    "already_submitted_info": {"ar": "هذا التدقيق مُرسل بالفعل — يمكن للمدير مراجعته وإغلاقه من الأسفل",
                                "en": "This audit is already submitted — a manager can review and close it below"},
    "save_draft_btn": {"ar": "💾 حفظ كمسودة", "en": "💾 Save as Draft"},
    "submit_final_btn": {"ar": "📤 إرسال التدقيق النهائي", "en": "📤 Submit Final Audit"},
    "saved_draft_msg": {"ar": "تم الحفظ كمسودة ✅", "en": "Saved as draft ✅"},
    "unanswered_error": {"ar": "يوجد {n} سؤال بدون إجابة. أكمل الإجابات قبل الإرسال.", "en": "{n} question(s) unanswered. Complete all answers before submitting."},
    "audit_submitted_msg": {"ar": "تم إرسال التدقيق ✅ النتيجة: {score}%", "en": "Audit submitted ✅ Score: {score}%"},
    "close_audit_btn": {"ar": "✅ اعتماد وإغلاق التدقيق", "en": "✅ Approve & Close Audit"},
    "audit_closed_msg": {"ar": "تم إغلاق التدقيق ✅", "en": "Audit closed ✅"},

    # ---------- Corrective Actions ----------
    "corrective_actions_title": {"ar": "🛠️ الإجراءات التصحيحية", "en": "🛠️ Corrective Actions"},
    "update_action_title": {"ar": "📝 تحديث حالة إجراء تصحيحي", "en": "📝 Update Corrective Action Status"},
    "select_action": {"ar": "اختر الإجراء", "en": "Select Action"},
    "new_status_action_label": {"ar": "الحالة الجديدة", "en": "New Status"},
    "response_note_label": {"ar": "ملاحظة الرد", "en": "Response Note"},
    "no_actions": {"ar": "لا توجد إجراءات تصحيحية 🎉", "en": "No corrective actions 🎉"},
    "no_action_update_permission": {"ar": "ليس لديك صلاحية تحديث هذا الإجراء", "en": "You don't have permission to update this action"},

    # ---------- Users ----------
    "users_title": {"ar": "👥 إدارة المستخدمين", "en": "👥 User Management"},
    "id_col": {"ar": "المعرف", "en": "ID"},
    "email_col": {"ar": "البريد", "en": "Email"},
    "name_col": {"ar": "الاسم", "en": "Name"},
    "role_col": {"ar": "الدور", "en": "Role"},
    "active_status_col": {"ar": "نشط", "en": "Active"},
    "last_login_col": {"ar": "آخر دخول", "en": "Last Login"},
    "add_user_title": {"ar": "➕ إضافة مستخدم جديد", "en": "➕ Add New User"},
    "role_label": {"ar": "الدور", "en": "Role"},
    "initial_password_label": {"ar": "كلمة المرور المبدئية *", "en": "Initial Password *"},
    "phone_label": {"ar": "رقم الجوال", "en": "Phone Number"},
    "managed_branches_label": {"ar": "الفروع المُدارة", "en": "Managed Branches"},
    "create_user_btn": {"ar": "إنشاء المستخدم", "en": "Create User"},
    "email_exists": {"ar": "البريد الإلكتروني مستخدم مسبقًا", "en": "Email already in use"},
    "user_created": {"ar": "تم إنشاء المستخدم ✅", "en": "User created ✅"},
    "edit_user_title": {"ar": "⚙️ تعديل حالة مستخدم", "en": "⚙️ Edit User Status"},
    "select_user": {"ar": "اختر المستخدم", "en": "Select User"},
    "save_changes_btn": {"ar": "حفظ التعديلات", "en": "Save Changes"},

    # ---------- Reports ----------
    "reports_title": {"ar": "📈 التقارير", "en": "📈 Reports"},
    "no_submitted_audits": {"ar": "لا توجد تدقيقات مُرسلة بعد لتوليد تقرير عنها", "en": "No submitted audits yet to generate a report"},
    "select_audit_report": {"ar": "اختر تدقيقًا لعرض تقريره", "en": "Select an audit to view its report"},
    "report_summary_line": {"ar": "**المرجع:** {ref} | **الفرع:** {branch} | **النتيجة:** {score}%",
                             "en": "**Reference:** {ref} | **Branch:** {branch} | **Score:** {score}%"},
    "download_pdf_btn": {"ar": "⬇️ تحميل تقرير PDF", "en": "⬇️ Download PDF Report"},
    "export_all_title": {"ar": "📊 تصدير كل التدقيقات", "en": "📊 Export All Audits"},
    "export_all_excel_btn": {"ar": "⬇️ تصدير الكل Excel", "en": "⬇️ Export All (Excel)"},

    # ---------- Audit Log ----------
    "audit_log_title": {"ar": "📜 سجل النشاط (Audit Log)", "en": "📜 Activity Log"},
    "filter_by_email": {"ar": "تصفية حسب البريد الإلكتروني", "en": "Filter by Email"},
    "filter_by_entity": {"ar": "تصفية حسب نوع الكيان (مثال: audit, branch, user)", "en": "Filter by entity type (e.g. audit, branch, user)"},
    "time_col": {"ar": "الوقت", "en": "Time"},
    "actor_col": {"ar": "الفاعل", "en": "Actor"},
    "action_col": {"ar": "الإجراء", "en": "Action"},
    "entity_type_col": {"ar": "النوع", "en": "Type"},
    "entity_id_col": {"ar": "المعرف", "en": "ID"},
    "log_caption": {"ar": "آخر {n} حدث معروض من أصل السجل الكامل", "en": "Last {n} events shown out of the full log"},

    # ---------- AI Assistant ----------
    "ai_title": {"ar": "🤖 المساعد الذكي والوكيل الذكي", "en": "🤖 AI Assistant & Smart Agent"},
    "ai_caption": {"ar": "مدعوم بنموذج Claude من Anthropic", "en": "Powered by Anthropic's Claude"},
    "ai_not_configured": {"ar": "⚠️ **المساعد الذكي غير مفعّل بعد.**", "en": "⚠️ **The AI Assistant is not enabled yet.**"},
    "tab_chat": {"ar": "💬 محادثة مع المساعد", "en": "💬 Chat with Assistant"},
    "tab_insights": {"ar": "📊 ملخصات ذكية للتدقيقات", "en": "📊 Smart Audit Summaries"},
    "chat_placeholder": {"ar": "اسأل المساعد الذكي عن أي شيء يخص جودة الفروع...", "en": "Ask the assistant anything about branch quality..."},
    "clear_chat_btn": {"ar": "🗑️ مسح المحادثة", "en": "🗑️ Clear Chat"},
    "chat_limit_reached": {"ar": "⚠️ وصلت للحد الأقصى من الرسائل بهذي الجلسة ({n} رسالة) للحفاظ على استهلاك معقول. حدّثي الصفحة لبدء جلسة جديدة.",
                            "en": "⚠️ You've reached the message limit for this session ({n} messages) to keep usage reasonable. Refresh the page to start a new session."},
    "no_submitted_for_ai": {"ar": "لا توجد تدقيقات مُرسلة بعد لتوليد ملخص ذكي عنها", "en": "No submitted audits yet to summarize"},
    "select_audit_ai": {"ar": "اختر تدقيقًا لتحليله بالذكاء الاصطناعي", "en": "Select an audit to analyze with AI"},
    "generate_summary_btn": {"ar": "🧠 توليد ملخص ذكي", "en": "🧠 Generate Smart Summary"},
    "ai_analyzing": {"ar": "المساعد الذكي يحلل بيانات التدقيق...", "en": "The assistant is analyzing audit data..."},
    "ai_thinking": {"ar": "جارٍ التفكير...", "en": "Thinking..."},
}


def get_lang() -> str:
    """يقرأ اللغة الحالية من حالة الجلسة، وإلا العربية افتراضيًا."""
    return st.session_state.get("lang", "ar")


def t(key: str, **kwargs) -> str:
    """يرجع النص المترجم حسب اللغة الحالية، مع دعم التنسيق {name} إن وُجد."""
    lang = get_lang()
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("ar", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def language_switcher():
    """يعرض زرّي تبديل اللغة بالشريط الجانبي (عربي/إنجليزي) — أزرار Streamlit حقيقية،
    تعتمد فقط على session_state (بدون query params) لتفادي أي تعارض مع نظام
    التنقّل الداخلي لـ Streamlit بين صفحات التطبيق."""
    current = get_lang()
    col1, col2 = st.sidebar.columns(2)
    ar_label = "🔵 العربية" if current == "ar" else "العربية"
    en_label = "🔵 English" if current == "en" else "English"
    if col1.button(ar_label, key="lang_btn_ar", use_container_width=True) and current != "ar":
        st.session_state["lang"] = "ar"
        st.rerun()
    if col2.button(en_label, key="lang_btn_en", use_container_width=True) and current != "en":
        st.session_state["lang"] = "en"
        st.rerun()
