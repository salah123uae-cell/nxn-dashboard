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
    "app_title": {"ar": "نظام NXN لإدارة جودة الفروع", "en": "NXN Branch Quality Management System"},
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
    "branch_status_board": {"ar": "🗺️ لوحة حالة الفروع", "en": "🗺️ Branch Status Board"},
    "filter_branch_label": {"ar": "🔎 تصفية حسب الفرع", "en": "🔎 Filter by Branch"},
    "filter_date_from": {"ar": "من تاريخ", "en": "From Date"},
    "filter_date_to": {"ar": "إلى تاريخ", "en": "To Date"},
    "no_data_yet": {"ar": "لا توجد بيانات بعد", "en": "No data yet"},
    "audits_count_label": {"ar": "تدقيق", "en": "audits"},

    # ---------- دليل الاستخدام والجولة التفاعلية ----------
    "help_title": {"ar": "📖 دليل الاستخدام", "en": "📖 User Guide"},
    "help_tab_guide": {"ar": "📄 الدليل المكتوب", "en": "📄 Written Guide"},
    "help_tab_tour": {"ar": "✨ جولة تفاعلية", "en": "✨ Interactive Tour"},
    "tour_next": {"ar": "التالي ▶", "en": "Next ▶"},
    "tour_back": {"ar": "◀ السابق", "en": "◀ Back"},
    "tour_finish": {"ar": "🔁 إعادة الجولة", "en": "🔁 Restart Tour"},
    "tour_step_label": {"ar": "خطوة", "en": "Step"},

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
    "ai_caption": {"ar": "مساعد ذكي لتحليل بيانات الجودة وتقديم توصيات عملية", "en": "A smart assistant for analyzing quality data and providing actionable recommendations"},
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
    "ai_setup_step1": {"ar": "1. احصل على مفتاح تفعيل خدمة الذكاء الاصطناعي من مزوّد الخدمة.", "en": "1. Get an activation key for the AI service from the provider."},
    "ai_setup_step2": {"ar": "2. في إعدادات الاستضافة: **Manage app → Settings → Secrets**، أضف السطر:", "en": "2. In hosting settings: **Manage app → Settings → Secrets**, add this line:"},
    "ai_setup_step3": {"ar": "3. أعد تشغيل التطبيق (**Reboot app**).", "en": "3. Restart the app (**Reboot app**)."},
    "ai_setup_cost_note": {"ar": "💡 **للتحكم بالتكلفة**: تقدر تضبط حدًا أقصى شهريًا للإنفاق من لوحة تحكم مزوّد الخدمة.", "en": "💡 **Cost control**: You can set a monthly spending cap from the provider's dashboard."},
    "ai_not_ready_generic": {"ar": "🤖 هذه الميزة قيد التفعيل حاليًا. تواصل مع إدارة النظام لتفعيلها.", "en": "🤖 This feature is currently being activated. Please contact system administration."},

    # ---------- Backup / Restore ----------
    "backup_title": {"ar": "💾 النسخ الاحتياطي واستعادة البيانات", "en": "💾 Backup & Restore"},
    "backup_warning": {"ar": "⚠️ **مهم جدًا**: قاعدة البيانات الحالية قد لا تكون دائمة على الاستضافة السحابية. نزّلي نسخة احتياطية بشكل دوري لتفادي فقدان البيانات.",
                        "en": "⚠️ **Important**: The current database may not be permanent on cloud hosting. Download a backup regularly to avoid data loss."},
    "export_backup_title": {"ar": "⬇️ تصدير نسخة احتياطية كاملة", "en": "⬇️ Export Full Backup"},
    "export_backup_desc": {"ar": "يحمّل ملف JSON واحد فيه كل بيانات النظام (فروع، مستخدمين، تدقيقات، إجراءات تصحيحية، سجل النشاط).",
                            "en": "Downloads a single JSON file containing all system data (branches, users, audits, corrective actions, activity log)."},
    "export_backup_btn": {"ar": "⬇️ تنزيل النسخة الاحتياطية", "en": "⬇️ Download Backup"},
    "import_backup_title": {"ar": "⬆️ استعادة من نسخة احتياطية", "en": "⬆️ Restore from Backup"},
    "import_backup_desc": {"ar": "⚠️ سيتم استبدال أي بيانات بنفس المعرّفات. استخدم هذا فقط عند نقل قاعدة البيانات أو الاستعادة بعد مشكلة.",
                            "en": "⚠️ Existing data with matching IDs will be overwritten. Use this only when migrating databases or recovering from an issue."},
    "import_backup_uploader": {"ar": "اختر ملف النسخة الاحتياطية (JSON)", "en": "Choose backup file (JSON)"},
    "import_backup_btn": {"ar": "⬆️ استعادة البيانات الآن", "en": "⬆️ Restore Data Now"},
    "import_success": {"ar": "✅ تمت الاستعادة بنجاح:", "en": "✅ Restore completed successfully:"},
    "import_error": {"ar": "❌ حدث خطأ أثناء الاستعادة", "en": "❌ An error occurred during restore"},
    "restore_setup_title": {"ar": "أو استعد نظامك كاملًا من نسخة احتياطية سابقة", "en": "Or restore your entire system from a previous backup"},
    "restore_setup_uploader": {"ar": "ملف النسخة الاحتياطية (JSON)", "en": "Backup file (JSON)"},
    "restore_setup_btn": {"ar": "⬆️ استعادة كل شي من النسخة الاحتياطية", "en": "⬆️ Restore Everything from Backup"},

    # ---------- عناوين القائمة الجانبية (تُقرأ ديناميكيًا عند كل تبديل لغة) ----------
    "nav_home": {"ar": "الرئيسية", "en": "Home"},
    "nav_dashboard": {"ar": "لوحة المعلومات", "en": "Dashboard"},
    "nav_branches": {"ar": "الفروع", "en": "Branches"},
    "nav_checklist": {"ar": "قوائم الفحص", "en": "Checklist"},
    "nav_audits": {"ar": "التدقيقات", "en": "Audits"},
    "nav_corrective": {"ar": "الإجراءات التصحيحية", "en": "Corrective Actions"},
    "nav_users": {"ar": "المستخدمون", "en": "Users"},
    "nav_reports": {"ar": "التقارير", "en": "Reports"},
    "nav_auditlog": {"ar": "سجل النشاط", "en": "Audit Log"},
    "nav_ai": {"ar": "المساعد الذكي", "en": "AI Assistant"},
    "nav_backup": {"ar": "النسخ الاحتياطي", "en": "Backup"},
    "nav_help": {"ar": "دليل الاستخدام", "en": "User Guide"},

    # ---------- تسجيل الدخول: تبويبات وإنشاء حساب واستعادة كلمة المرور ----------
    "login_tab_login": {"ar": "🔐 تسجيل الدخول", "en": "🔐 Log In"},
    "login_tab_signup": {"ar": "🆕 إنشاء حساب جديد", "en": "🆕 Create Account"},
    "login_tab_forgot": {"ar": "❓ نسيت كلمة المرور", "en": "❓ Forgot Password"},
    "first_name_label": {"ar": "الاسم الأول *", "en": "First Name *"},
    "last_name_label": {"ar": "الاسم الأخير *", "en": "Last Name *"},
    "employee_number_label": {"ar": "الرقم الوظيفي", "en": "Employee Number"},
    "employee_number_col": {"ar": "الرقم الوظيفي", "en": "Employee Number"},
    "new_password_label2": {"ar": "كلمة المرور الجديدة *", "en": "New Password *"},
    "confirm_new_password_label": {"ar": "تأكيد كلمة المرور الجديدة *", "en": "Confirm New Password *"},
    "signup_submit_btn": {"ar": "📨 إرسال طلب إنشاء الحساب", "en": "📨 Submit Account Request"},
    "forgot_password_info": {"ar": "أدخلي بريدك الإلكتروني وكلمة المرور الجديدة اللي تبينها. راح يُرسل طلبك للإدارة للموافقة عليه.",
                              "en": "Enter your email and the new password you'd like. Your request will be sent to management for approval."},
    "forgot_password_submit_btn": {"ar": "📨 إرسال طلب استعادة كلمة المرور", "en": "📨 Submit Password Reset Request"},
    "signup_success": {"ar": "✅ تم إرسال طلبك بنجاح! بانتظار موافقة الإدارة — راح تقدرين تسجّلين الدخول بعد الموافقة.",
                        "en": "✅ Your request was submitted successfully! Awaiting management approval — you'll be able to log in once approved."},
    "reset_request_success": {"ar": "✅ تم إرسال طلب استعادة كلمة المرور! بانتظار موافقة الإدارة.",
                               "en": "✅ Password reset request submitted! Awaiting management approval."},
    "err_email_exists": {"ar": "هذا البريد الإلكتروني مسجّل بالفعل بالنظام", "en": "This email is already registered in the system"},
    "err_signup_already_pending": {"ar": "يوجد طلب سابق بنفس البريد بانتظار المراجعة", "en": "A request with this email is already pending review"},
    "err_email_not_found": {"ar": "ما فيه حساب بهذا البريد الإلكتروني", "en": "No account found with this email"},
    "err_reset_already_pending": {"ar": "يوجد طلب استعادة سابق بنفس البريد بانتظار المراجعة", "en": "A reset request with this email is already pending review"},
    "account_disabled_or_pending": {"ar": "الحساب غير موجود، معطّل، أو طلبك لسا قيد المراجعة", "en": "Account not found, disabled, or your request is still under review"},

    # ---------- طلبات إدارية بصفحة المستخدمين ----------
    "users_tab_list": {"ar": "👥 المستخدمون", "en": "👥 Users"},
    "users_tab_signups": {"ar": "🆕 طلبات حسابات جديدة", "en": "🆕 New Account Requests"},
    "users_tab_resets": {"ar": "🔑 طلبات استعادة كلمة المرور", "en": "🔑 Password Reset Requests"},
    "pending_signups_title": {"ar": "طلبات الحسابات الجديدة قيد المراجعة", "en": "Pending New Account Requests"},
    "pending_resets_title": {"ar": "طلبات استعادة كلمة المرور قيد المراجعة", "en": "Pending Password Reset Requests"},
    "no_pending_signups": {"ar": "لا توجد طلبات حسابات جديدة حاليًا 🎉", "en": "No pending account requests 🎉"},
    "no_pending_resets": {"ar": "لا توجد طلبات استعادة كلمة مرور حاليًا 🎉", "en": "No pending password reset requests 🎉"},
    "approve_btn": {"ar": "✅ قبول", "en": "✅ Approve"},
    "reject_btn": {"ar": "❌ رفض", "en": "❌ Reject"},
    "assign_role_label": {"ar": "الدور عند القبول", "en": "Role on Approval"},
    "requested_at_col": {"ar": "تاريخ الطلب", "en": "Requested At"},
    "signup_approved_toast": {"ar": "✅ تم قبول الطلب وإنشاء الحساب", "en": "✅ Request approved and account created"},
    "signup_rejected_toast": {"ar": "تم رفض الطلب", "en": "Request rejected"},
    "reset_approved_toast": {"ar": "✅ تم قبول طلب استعادة كلمة المرور وتحديثها", "en": "✅ Password reset approved and updated"},
    "reset_rejected_toast": {"ar": "تم رفض طلب الاستعادة", "en": "Reset request rejected"},
    "edit_user_full_title": {"ar": "⚙️ تعديل بيانات مستخدم", "en": "⚙️ Edit User Details"},
    "suspend_account_label": {"ar": "🔓 الحساب مفعّل (أوقفي المفتاح لإيقاف الحساب)", "en": "🔓 Account Active (toggle off to suspend)"},
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
    """يعرض قائمة منسدلة صغيرة أعلى يمين المحتوى لتبديل اللغة (عربي/إنجليزي)."""
    current = get_lang()
    options = ["ar", "en"]
    labels = {"ar": "🌐 AR", "en": "🌐 EN"}
    _spacer, corner = st.columns([6, 1])
    with corner:
        choice = st.selectbox(
            "language_switcher_select",
            options,
            index=options.index(current),
            format_func=lambda code: labels[code],
            key="lang_select",
            label_visibility="collapsed",
        )
    if choice != current:
        st.session_state["lang"] = choice
        st.rerun()

