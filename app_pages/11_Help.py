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
# التبويب الأول: الدليل المكتوب
# ==================================================================
with tab_guide:
    GUIDE_AR = """
### 🗂️ نظرة عامة
نظام NXN لإدارة جودة الفروع يساعدك على تنظيم عمليات تدقيق الجودة بكل الفروع، متابعة
النتائج، وإدارة الإجراءات التصحيحية من مكان واحد.

---

### 👤 الأدوار والصلاحيات
| الدور | الصلاحيات |
|---|---|
| **مالك النظام** | كل الصلاحيات، بما فيها إدارة المستخدمين والنسخ الاحتياطي |
| **مدير** | إدارة الفروع وقوائم الفحص، اعتماد التدقيقات، إدارة المستخدمين |
| **مدقق** | إنشاء وتنفيذ التدقيقات الخاصة به |
| **فرع** | متابعة تدقيقات فرعه والإجراءات التصحيحية الخاصة به |
| **مشاهد** | عرض فقط بدون تعديل |

---

### 📊 لوحة المعلومات (Dashboard)
- **لوحة حالة الفروع**: بطاقات ملوّنة تعطيك نظرة سريعة على أداء كل فرع
  (🟢 أخضر = ممتاز 90%+، 🟡 برتقالي = جيد 75-89%، 🔴 أحمر = يحتاج متابعة).
- **الفلاتر**: صفّي البيانات حسب فرع معيّن أو فترة زمنية محددة.
- **الرسوم البيانية**: توزيع حالات التدقيق ومتوسط النتيجة لكل فرع.

### 🏢 الفروع
أضيفي فروع جديدة، وحدّثي حالتها (نشط / غير نشط / موقوف) من هنا.

### 📋 قوائم الفحص
أضيفي نُسخ قوائم فحص، أقسام، وأسئلة تدقيق جديدة. كل سؤال له وزن يُستخدم بحساب النتيجة.

### 🔍 التدقيقات
1. **تدقيق جديد**: اختاري الفرع وتاريخ الزيارة لجدولة تدقيق.
2. **تنفيذ / مراجعة**: أجيبي على الأسئلة (متوافق / غير متوافق / لا ينطبق)، احفظي كمسودة
   أو أرسلي التدقيق النهائي. عند وجود إجابة "غير متوافق"، يُنشأ إجراء تصحيحي تلقائيًا.
3. النتيجة النهائية = (مجموع أوزان الأسئلة المتوافقة) ÷ (مجموع أوزان الأسئلة القابلة للتطبيق) × 100.

### 🛠️ الإجراءات التصحيحية
تابعي الإجراءات المفتوحة، حدّثي حالتها، وأضيفي ملاحظة عند الحل.

### 👥 المستخدمون
أضيفي مستخدمين جدد وحدّدي أدوارهم (يظهر فقط للمالك والمدير).

### 📈 التقارير
حمّلي تقرير PDF لتدقيق معيّن، أو صدّري كل التدقيقات كملف Excel.

### 📜 سجل النشاط
سجل كامل لكل العمليات الحساسة بالنظام (من فعل ماذا ومتى).

### 🤖 المساعد الذكي
اسألي عن بيانات النظام أو احصلي على ملخص وتوصيات ذكية لأي تدقيق مُرسل.

### 💾 النسخ الاحتياطي
**مهم جدًا**: نزّلي نسخة احتياطية بشكل دوري (أسبوعيًا مثلاً) من صفحة "النسخ الاحتياطي"
لحماية بياناتك من أي طارئ.

### 🌐 تبديل اللغة
قائمة تبديل اللغة أعلى الصفحة تبدّل لغة الواجهة بالكامل فورًا.

---
*آخر تحديث لهذا الدليل: يُحدَّث هذا الدليل مع كل تحديث جديد بالنظام.*
"""

    GUIDE_EN = """
### 🗂️ Overview
The NXN Branch Quality Management System helps you organize quality audits across all
branches, track results, and manage corrective actions from one place.

---

### 👤 Roles & Permissions
| Role | Permissions |
|---|---|
| **Owner** | Full access, including user management and backups |
| **Manager** | Manage branches, checklists, approve audits, manage users |
| **Auditor** | Create and conduct their own audits |
| **Branch** | Track their branch's audits and corrective actions |
| **Viewer** | Read-only access |

---

### 📊 Dashboard
- **Branch Status Board**: colored cards give you an instant view of each branch's
  performance (🟢 Green = excellent 90%+, 🟡 Orange = good 75-89%, 🔴 Red = needs attention).
- **Filters**: filter data by specific branch or date range.
- **Charts**: audit status distribution and average score per branch.

### 🏢 Branches
Add new branches and update their status (active / inactive / suspended) here.

### 📋 Checklist
Add checklist versions, sections, and audit questions. Each question has a weight
used in score calculation.

### 🔍 Audits
1. **New Audit**: choose the branch and visit date to schedule an audit.
2. **Conduct / Review**: answer the questions (compliant / non-compliant / not
   applicable), save as draft or submit the final audit. A "non-compliant" answer
   automatically creates a corrective action.
3. Final score = (sum of weights of compliant questions) ÷ (sum of weights of
   applicable questions) × 100.

### 🛠️ Corrective Actions
Track open actions, update their status, and add a resolution note.

### 👥 Users
Add new users and assign their roles (visible to Owner and Manager only).

### 📈 Reports
Download a PDF report for a specific audit, or export all audits as an Excel file.

### 📜 Audit Log
A complete log of every sensitive operation in the system (who did what, and when).

### 🤖 AI Assistant
Ask about system data or get a smart summary and recommendations for any submitted audit.

### 💾 Backup
**Very important**: download a backup regularly (weekly, for example) from the
"Backup" page to protect your data from any unexpected issue.

### 🌐 Language Switching
The language dropdown at the top of the page switches the entire interface language
instantly.

---
*This guide is kept up to date with every new system update.*
"""

    st.markdown(GUIDE_AR if lang == "ar" else GUIDE_EN)

# ==================================================================
# التبويب الثاني: جولة تفاعلية إرشادية
# ==================================================================
with tab_tour:
    TOUR_STEPS = [
        {"icon": "👋", "ar": ("مرحبًا بك في نظام NXN", "هذه جولة سريعة تعرّفك على أهم أجزاء النظام خطوة بخطوة."),
         "en": ("Welcome to the NXN System", "A quick tour introducing you to the main parts of the system, step by step.")},
        {"icon": "📊", "ar": ("لوحة المعلومات", "أول ما تدخلين، شوفي لوحة حالة الفروع الملوّنة لمعرفة أداء كل فرع بلمحة."),
         "en": ("Dashboard", "As soon as you log in, check the colored Branch Status Board for an instant view of each branch's performance.")},
        {"icon": "🏢", "ar": ("الفروع", "من هنا تضيفين فروعًا جديدة وتتابعين حالتها (نشط / موقوف)."),
         "en": ("Branches", "Add new branches and track their status (active / suspended) from here.")},
        {"icon": "📋", "ar": ("قوائم الفحص", "جهّزي أسئلة التدقيق وأقسامها وأوزانها هنا قبل البدء بأي تدقيق."),
         "en": ("Checklist", "Prepare your audit questions, sections, and weights here before starting any audit.")},
        {"icon": "🔍", "ar": ("التدقيقات", "أنشئي تدقيقًا جديدًا لفرع معيّن، نفّذيه بالإجابة على الأسئلة، ثم أرسليه — النتيجة تُحسب تلقائيًا!"),
         "en": ("Audits", "Create a new audit for a branch, conduct it by answering the questions, then submit — the score is calculated automatically!")},
        {"icon": "🛠️", "ar": ("الإجراءات التصحيحية", "أي إجابة غير متوافقة تنشئ إجراءً تصحيحيًا تلقائيًا — تابعيه هنا لين يُحل."),
         "en": ("Corrective Actions", "Any non-compliant answer automatically creates a corrective action — track it here until resolved.")},
        {"icon": "📈", "ar": ("التقارير", "حمّلي تقرير PDF لأي تدقيق، أو صدّري كل البيانات كملف Excel بضغطة واحدة."),
         "en": ("Reports", "Download a PDF report for any audit, or export all data to Excel with one click.")},
        {"icon": "🤖", "ar": ("المساعد الذكي", "اسأليه عن بيانات النظام، أو خليه يلخّص لك أي تدقيق ويقترح توصيات."),
         "en": ("AI Assistant", "Ask it about system data, or let it summarize any audit and suggest recommendations.")},
        {"icon": "💾", "ar": ("النسخ الاحتياطي", "أهم عادة! نزّلي نسخة احتياطية بشكل دوري من هذي الصفحة لحماية بياناتك."),
         "en": ("Backup", "The most important habit! Download a backup regularly from this page to protect your data.")},
        {"icon": "🎉", "ar": ("جاهزة تبدين!", "كذا خلصت الجولة. استخدمي الدليل المكتوب بالتبويب المجاور لو احتجتي تفاصيل أكثر بأي وقت."),
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
            <div style="font-size: 64px; margin-bottom: 12px;">{current['icon']}</div>
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

