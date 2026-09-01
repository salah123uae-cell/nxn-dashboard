import streamlit as st
from branding import render_logo, apply_theme, BRAND_LIME, BRAND_BLUE, BRAND_PURPLE

from auth import require_login, current_user, render_logout_sidebar
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_login()
render_logout_sidebar()
user = current_user()

st.title(t("help_title"))

tab_guide, tab_tour = st.tabs([t("help_tab_guide"), t("help_tab_tour")])

# ==================================================================
# التبويب الأول: الدليل البصري التفاعلي (بطاقات قابلة للطي بدل نص طويل)
# ملاحظة للمطوّر: هذا الدليل مبني من قائمة بيانات GUIDE_SECTIONS أدناه —
# أي صفحة أو ميزة جديدة تُضاف للنظام مستقبلًا يجب إضافة عنصر لها هنا فورًا
# حتى يبقى الدليل مطابقًا للنظام الفعلي بشكل دائم.
# ==================================================================
with tab_guide:
    GUIDE_SECTIONS = [
        {
            "accent": BRAND_BLUE,
            "title": {"ar": "نظرة عامة", "en": "Overview"},
            "body": {
                "ar": "نظام NXN لإدارة جودة الفروع يساعدك على تنظيم عمليات تدقيق الجودة بكل "
                      "الفروع، متابعة النتائج، وإدارة الإجراءات التصحيحية من مكان واحد.",
                "en": "The NXN Branch Quality Management System helps you organize quality "
                      "audits across all branches, track results, and manage corrective "
                      "actions from one place.",
            },
        },
        {
            "accent": BRAND_PURPLE,
            "title": {"ar": "الأدوار والصلاحيات", "en": "Roles & Permissions"},
            "table": [
                {"ar": ("مالك النظام", "كل الصلاحيات، بما فيها إدارة المستخدمين والنسخ الاحتياطي"),
                 "en": ("Owner", "Full access, including user management and backups")},
                {"ar": ("مدير", "إدارة الفروع وقوائم الفحص، اعتماد التدقيقات، إدارة المستخدمين"),
                 "en": ("Manager", "Manage branches, checklists, approve audits, manage users")},
                {"ar": ("مدقق", "إنشاء وتنفيذ التدقيقات الخاصة به"),
                 "en": ("Auditor", "Create and conduct their own audits")},
                {"ar": ("فرع", "متابعة تدقيقات فرعه والإجراءات التصحيحية الخاصة به"),
                 "en": ("Branch", "Track their branch's audits and corrective actions")},
                {"ar": ("مشاهد", "عرض فقط بدون تعديل"),
                 "en": ("Viewer", "Read-only access")},
            ],
        },
        {
            "accent": BRAND_LIME,
            "title": {"ar": "لوحة المعلومات", "en": "Dashboard"},
            "body": {
                "ar": "**لوحة حالة الفروع**: بطاقات ملوّنة تعطيك نظرة سريعة على أداء كل فرع "
                      "(أخضر = ممتاز 90%+، برتقالي = جيد 75-89%، أحمر = يحتاج متابعة).\n\n"
                      "**الفلاتر**: صفّي البيانات حسب فرع معيّن أو فترة زمنية محددة.\n\n"
                      "**الرسوم البيانية**: توزيع حالات التدقيق ومتوسط النتيجة لكل فرع.",
                "en": "**Branch Status Board**: colored cards give you an instant view of each "
                      "branch's performance (Green = excellent 90%+, Orange = good "
                      "75-89%, Red = needs attention).\n\n"
                      "**Filters**: filter data by specific branch or date range.\n\n"
                      "**Charts**: audit status distribution and average score per branch.",
            },
        },
        {
            "accent": BRAND_BLUE,
            "title": {"ar": "الفروع", "en": "Branches"},
            "body": {
                "ar": "أضيفي فروع جديدة، وحدّثي حالتها (نشط / غير نشط / موقوف) من هنا.",
                "en": "Add new branches and update their status (active / inactive / "
                      "suspended) here.",
            },
        },
        {
            "accent": BRAND_PURPLE,
            "title": {"ar": "قوائم الفحص", "en": "Checklist"},
            "body": {
                "ar": "أضيفي نُسخ قوائم فحص، أقسام، وأسئلة تدقيق جديدة. كل سؤال له وزن يُستخدم "
                      "بحساب النتيجة.",
                "en": "Add checklist versions, sections, and audit questions. Each question "
                      "has a weight used in score calculation.",
            },
        },
        {
            "accent": BRAND_LIME,
            "title": {"ar": "التدقيقات", "en": "Audits"},
            "body": {
                "ar": "1. **تدقيق جديد**: اختاري الفرع وتاريخ الزيارة لجدولة تدقيق.\n"
                      "2. **تنفيذ / مراجعة**: أجيبي على الأسئلة (متوافق / غير متوافق / لا "
                      "ينطبق)، احفظي كمسودة أو أرسلي التدقيق النهائي. عند وجود إجابة \"غير "
                      "متوافق\"، يُنشأ إجراء تصحيحي تلقائيًا.\n"
                      "3. النتيجة النهائية = (مجموع أوزان الأسئلة المتوافقة) ÷ (مجموع أوزان "
                      "الأسئلة القابلة للتطبيق) × 100.",
                "en": "1. **New Audit**: choose the branch and visit date to schedule an "
                      "audit.\n"
                      "2. **Conduct / Review**: answer the questions (compliant / "
                      "non-compliant / not applicable), save as draft or submit the final "
                      "audit. A \"non-compliant\" answer automatically creates a corrective "
                      "action.\n"
                      "3. Final score = (sum of weights of compliant questions) ÷ (sum of "
                      "weights of applicable questions) × 100.",
            },
        },
        {
            "accent": BRAND_BLUE,
            "title": {"ar": "الإجراءات التصحيحية", "en": "Corrective Actions"},
            "body": {
                "ar": "تابعي الإجراءات المفتوحة، حدّثي حالتها، وأضيفي ملاحظة عند الحل.",
                "en": "Track open actions, update their status, and add a resolution note.",
            },
        },
        {
            "accent": BRAND_PURPLE,
            "title": {"ar": "المستخدمون", "en": "Users"},
            "body": {
                "ar": "أضيفي مستخدمين جدد وحدّدي أدوارهم (يظهر فقط للمالك والمدير).",
                "en": "Add new users and assign their roles (visible to Owner and Manager "
                      "only).",
            },
        },
        {
            "accent": BRAND_LIME,
            "title": {"ar": "التقارير", "en": "Reports"},
            "body": {
                "ar": "حمّلي تقرير PDF لتدقيق معيّن، أو صدّري كل التدقيقات كملف Excel.",
                "en": "Download a PDF report for a specific audit, or export all audits as "
                      "an Excel file.",
            },
        },
        {
            "accent": BRAND_BLUE,
            "title": {"ar": "سجل النشاط", "en": "Audit Log"},
            "body": {
                "ar": "سجل كامل لكل العمليات الحساسة بالنظام (من فعل ماذا ومتى).",
                "en": "A complete log of every sensitive operation in the system (who did "
                      "what, and when).",
            },
        },
        {
            "accent": BRAND_PURPLE,
            "title": {"ar": "المساعد الذكي", "en": "AI Assistant"},
            "body": {
                "ar": "اسألي عن بيانات النظام أو احصلي على ملخص وتوصيات ذكية لأي تدقيق مُرسل.",
                "en": "Ask about system data or get a smart summary and recommendations for "
                      "any submitted audit.",
            },
        },
        {
            "accent": BRAND_LIME,
            "title": {"ar": "النسخ الاحتياطي", "en": "Backup"},
            "body": {
                "ar": "**مهم جدًا**: نزّلي نسخة احتياطية بشكل دوري (أسبوعيًا مثلاً) من صفحة "
                      "\"النسخ الاحتياطي\" لحماية بياناتك من أي طارئ.",
                "en": "**Very important**: download a backup regularly (weekly, for "
                      "example) from the \"Backup\" page to protect your data from any "
                      "unexpected issue.",
            },
        },
        {
            "accent": BRAND_BLUE,
            "title": {"ar": "تبديل اللغة", "en": "Language Switching"},
            "body": {
                "ar": "قائمة تبديل اللغة أعلى الصفحة تبدّل لغة الواجهة بالكامل فورًا، بما في "
                      "ذلك موضع الشريط الجانبي (يمين للعربية، يسار للإنجليزية).",
                "en": "The language dropdown at the top of the page switches the entire "
                      "interface language instantly, including the sidebar's position "
                      "(right for Arabic, left for English).",
            },
        },
    ]

    st.caption(
        "اضغطي على أي بطاقة لعرض تفاصيلها — الدليل يتحدّث تلقائيًا مع كل تحديث جديد بالنظام."
        if lang == "ar" else
        "Tap any card to expand it — this guide is kept in sync automatically with every new system update."
    )
    st.write("")

    for sec in GUIDE_SECTIONS:
        accent = sec["accent"]
        title = sec["title"][lang]
        with st.expander(title):
            st.markdown(
                f'<div style="height:3px; background:{accent}; border-radius:2px; '
                f'margin-bottom:12px; width:60px;"></div>',
                unsafe_allow_html=True,
            )
            if "table" in sec:
                rows_html = "".join(
                    f'<tr><td style="padding:8px 12px; font-weight:700; color:{accent}; '
                    f'white-space:nowrap; vertical-align:top;">{row[lang][0]}</td>'
                    f'<td style="padding:8px 12px; color:#333;">{row[lang][1]}</td></tr>'
                    for row in sec["table"]
                )
                st.markdown(
                    f'<table style="width:100%; border-collapse:collapse;">{rows_html}</table>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(sec["body"][lang])

    st.divider()
    st.caption(
        "آخر تحديث لهذا الدليل: يُحدَّث هذا الدليل مع كل تحديث جديد بالنظام."
        if lang == "ar" else
        "Last updated with the system: this guide is refreshed alongside every system update."
    )

# ==================================================================
# التبويب الثاني: جولة تفاعلية إرشادية
# ==================================================================
with tab_tour:
    TOUR_STEPS = [
        {"ar": ("مرحبًا بك في نظام NXN", "هذه جولة سريعة تعرّفك على أهم أجزاء النظام خطوة بخطوة."),
         "en": ("Welcome to the NXN System", "A quick tour introducing you to the main parts of the system, step by step.")},
        {"ar": ("لوحة المعلومات", "أول ما تدخلين، شوفي لوحة حالة الفروع الملوّنة لمعرفة أداء كل فرع بلمحة."),
         "en": ("Dashboard", "As soon as you log in, check the colored Branch Status Board for an instant view of each branch's performance.")},
        {"ar": ("الفروع", "من هنا تضيفين فروعًا جديدة وتتابعين حالتها (نشط / موقوف)."),
         "en": ("Branches", "Add new branches and track their status (active / suspended) from here.")},
        {"ar": ("قوائم الفحص", "جهّزي أسئلة التدقيق وأقسامها وأوزانها هنا قبل البدء بأي تدقيق."),
         "en": ("Checklist", "Prepare your audit questions, sections, and weights here before starting any audit.")},
        {"ar": ("التدقيقات", "أنشئي تدقيقًا جديدًا لفرع معيّن، نفّذيه بالإجابة على الأسئلة، ثم أرسليه — النتيجة تُحسب تلقائيًا!"),
         "en": ("Audits", "Create a new audit for a branch, conduct it by answering the questions, then submit — the score is calculated automatically!")},
        {"ar": ("الإجراءات التصحيحية", "أي إجابة غير متوافقة تنشئ إجراءً تصحيحيًا تلقائيًا — تابعيه هنا لين يُحل."),
         "en": ("Corrective Actions", "Any non-compliant answer automatically creates a corrective action — track it here until resolved.")},
        {"ar": ("التقارير", "حمّلي تقرير PDF لأي تدقيق، أو صدّري كل البيانات كملف Excel بضغطة واحدة."),
         "en": ("Reports", "Download a PDF report for any audit, or export all data to Excel with one click.")},
        {"ar": ("المساعد الذكي", "اسأليه عن بيانات النظام، أو خليه يلخّص لك أي تدقيق ويقترح توصيات."),
         "en": ("AI Assistant", "Ask it about system data, or let it summarize any audit and suggest recommendations.")},
        {"ar": ("النسخ الاحتياطي", "أهم عادة! نزّلي نسخة احتياطية بشكل دوري من هذي الصفحة لحماية بياناتك."),
         "en": ("Backup", "The most important habit! Download a backup regularly from this page to protect your data.")},
        {"ar": ("جاهزة تبدين!", "كذا خلصت الجولة. استخدمي الدليل المكتوب بالتبويب المجاور لو احتجتي تفاصيل أكثر بأي وقت."),
         "en": ("You're ready to start!", "That's the end of the tour. Use the written guide in the next tab anytime you need more detail.")},
    ]

    if "tour_step" not in st.session_state:
        st.session_state["tour_step"] = 0

    step = st.session_state["tour_step"]
    total = len(TOUR_STEPS)
    step = max(0, min(step, total - 1))

    st.progress((step + 1) / total)
    st.caption(f"{t('tour_step_label')} {step + 1} / {total}")

    current = TOUR_STEPS[step]
    title, desc = current["ar"] if lang == "ar" else current["en"]
    accent = [BRAND_BLUE, BRAND_LIME, BRAND_PURPLE][step % 3]

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {accent}12 0%, {accent}05 100%);
            border: 2px solid {accent}; border-radius: 20px;
            padding: 48px 32px; text-align: center; margin: 16px 0 24px 0;
        ">
            <div style="font-size: 26px; font-weight: 800; color: {accent}; margin-bottom: 12px;">{title}</div>
            <div style="font-size: 16px; color: #444; max-width: 560px; margin: 0 auto; line-height: 1.7;">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nc1, nc2, nc3 = st.columns([1, 1, 1])
    with nc1:
        if step > 0:
            if st.button(t("tour_back"), use_container_width=True, key="tour_back_btn"):
                st.session_state["tour_step"] = step - 1
                st.rerun()
    with nc3:
        if step < total - 1:
            if st.button(t("tour_next"), use_container_width=True, key="tour_next_btn", type="primary"):
                st.session_state["tour_step"] = step + 1
                st.rerun()
        else:
            if st.button(t("tour_finish"), use_container_width=True, key="tour_finish_btn"):
                st.session_state["tour_step"] = 0
                st.rerun()

