"""
موجّه التنقّل الرئيسي للنظام. بدل الاعتماد على اكتشاف Streamlit التلقائي لمجلد
الصفحات (الذي يجمّد أسماء الصفحات من اسم الملف بلغة واحدة ثابتة)، نبني هنا قائمة
الصفحات صراحةً بعناوين مترجمة تُعاد قراءتها من TRANSLATIONS في كل مرة يُعاد فيها
تحميل هذا الملف — أي عند كل تبديل لغة، تتحدّث القائمة الجانبية بالكامل فورًا.
ملاحظة: مجلد الصفحات مُسمّى app_pages (بدل pages) بناءً على توصية Streamlit
الرسمية، لتفادي أي تعارض بين نظام التنقّل اليدوي هنا واكتشاف الصفحات التلقائي.

قبل تسجيل الدخول: تظهر فقط صفحة "الرئيسية" (بدون بقية عناصر القائمة، لأنها
غير مفيدة لمستخدم غير مسجّل دخول أصلًا وتضغط الشريط الجانبي بلا داعٍ)، والشريط
الجانبي يبدأ مطويًا لتفادي تغطية شاشة الدخول على الجوال.
بعد تسجيل الدخول: تظهر القائمة الكاملة، ونجبر الشريط الجانبي على الفتح تلقائيًا
عبر جافاسكريبت (لأن initial_sidebar_state لا يُعاد تطبيقه إلا عند أول تحميل
كامل للصفحة، وليس بعد تسجيل الدخول عبر st.rerun() ضمن نفس الجلسة). سهم الطي
يبقى ظاهرًا حتى تقدر المستخدمة تتحكم يدويًا لو رغبت.
"""
import streamlit as st
import streamlit.components.v1 as components
from i18n import t, get_lang, language_switcher
from branding import render_sidebar_logo, render_dev_credit
from auth import current_user
from database import is_persistent_db_configured

_is_logged_in = current_user() is not None

st.set_page_config(
    page_title="NXN Quality System | نظام NXN لإدارة الجودة",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded" if _is_logged_in else "collapsed",
)

# بعد تسجيل الدخول: نتأكد إن الشريط الجانبي مفتوح فعليًا (بضغط زر الفتح تلقائيًا
# عبر جافاسكريبت لو كان مطويًا)، لأن initial_sidebar_state وحده لا يكفي بعد
# تسجيل الدخول ضمن نفس الجلسة (st.rerun() لا يُعيد تطبيقه).
if _is_logged_in:
    components.html(
        """
        <script>
        (function() {
            function openSidebarIfCollapsed() {
                try {
                    const doc = window.parent.document;
                    const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                    const toggle = doc.querySelector('[data-testid="collapsedControl"]');
                    if (toggle && toggle.offsetParent !== null) {
                        toggle.click();
                    }
                } catch (e) {}
            }
            // تمييز الصفحة الحالية بالقائمة الجانبية: هذا الإصدار من Streamlit
            // لا يستخدم aria-current="page"، فنقارن يدويًا رابط كل عنصر
            // بمسار الصفحة الحالية ونضيف كلاس مخصّص (nxn-active-link) — راجع
            // branding.py حيث يُعرَّف شكل هذا الكلاس.
            function markActiveLink() {
                try {
                    const doc = window.parent.document;
                    const currentPath = window.parent.location.pathname;
                    const links = doc.querySelectorAll('[data-testid="stSidebarNav"] a');
                    links.forEach(function(link) {
                        let linkPath;
                        try { linkPath = new URL(link.href).pathname; } catch (e) { linkPath = null; }
                        if (linkPath !== null && linkPath === currentPath) {
                            link.classList.add('nxn-active-link');
                        } else {
                            link.classList.remove('nxn-active-link');
                        }
                    });
                } catch (e) {}
            }
            setTimeout(openSidebarIfCollapsed, 150);
            setTimeout(openSidebarIfCollapsed, 500);
            setTimeout(openSidebarIfCollapsed, 1000);
            setTimeout(markActiveLink, 150);
            setTimeout(markActiveLink, 500);
            setTimeout(markActiveLink, 1000);
        })();
        </script>
        """,
        height=0,
    )

# نقرأ اللغة الحالية فقط للتأكد من إعادة بناء القائمة عند كل تغيير (get_lang يقرأ من session_state)
_ = get_lang()

render_sidebar_logo()

# نص نسب تطوير النظام يظهر أعلى كل صفحة (يُستدعى من الموجّه ليظهر بنفس الموضع
# الثابت بكل صفحات النظام دون تكرار الكود بكل ملف).
render_dev_credit()

# نبني صفحة الرئيسية هنا (قبل استدعاء تبديل اللغة) لأن جرس الإشعارات يحتاج
# كائن الصفحة نفسه (وليس مجرد نص المسار) للتنقّل الموثوق عبر st.switch_page().
home_page = st.Page("home.py", title=t("nav_home"), url_path="", default=True)

# تبديل اللغة يُستدعى هنا (بالموجّه) بدل كل صفحة على حدة، ليظهر بنفس الموضع
# الثابت أعلى الشاشة بكل صفحات النظام دون تكرار الكود. يعرض أيضًا جرس
# الإشعارات بجانبه (لو مسجّل دخول) — يظهر بكل صفحة بالنظام.
language_switcher(home_page=home_page)

# ---------- تحذير حرج: لو قاعدة البيانات الدائمة (Postgres) غير متصلة فعليًا،
# النظام يعمل على تخزين مؤقت تُمسح بياناته بالكامل مع كل إعادة تشغيل للخادم.
# يظهر فقط لمالك النظام (الوحيد القادر يصلح إعداد الأسرار) حتى ينتبه فورًا
# بدل ما يكتشف إن بياناته ضاعت بدون أي سبب واضح له.
if _is_logged_in:
    _user = current_user()
    if _user and _user["role"] == "owner" and not is_persistent_db_configured():
        st.error(t("db_not_persistent_warning"), icon=None)

if _is_logged_in:
    pages = [
        home_page,
        st.Page("app_pages/1_Dashboard.py", title=t("nav_dashboard"), url_path="Dashboard"),
        st.Page("app_pages/2_Branches.py", title=t("nav_branches"), url_path="Branches"),
        st.Page("app_pages/3_Checklist.py", title=t("nav_checklist"), url_path="Checklist"),
        st.Page("app_pages/4_Audits.py", title=t("nav_audits"), url_path="Audits"),
        st.Page("app_pages/5_Corrective_Actions.py", title=t("nav_corrective"), url_path="Corrective_Actions"),
        st.Page("app_pages/6_Users.py", title=t("nav_users"), url_path="Users"),
        st.Page("app_pages/7_Reports.py", title=t("nav_reports"), url_path="Reports"),
        st.Page("app_pages/8_Audit_Log.py", title=t("nav_auditlog"), url_path="Audit_Log"),
        st.Page("app_pages/9_AI_Assistant.py", title=t("nav_ai"), url_path="AI_Assistant"),
        st.Page("app_pages/10_Backup.py", title=t("nav_backup"), url_path="Backup"),
        st.Page("app_pages/11_Help.py", title=t("nav_help"), url_path="Help"),
        st.Page("app_pages/12_Automation.py", title=t("nav_automation"), url_path="Automation"),
    ]
else:
    pages = [home_page]

pg = st.navigation(pages, position="sidebar")
pg.run()

