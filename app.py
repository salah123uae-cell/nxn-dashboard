"""
موجّه التنقّل الرئيسي للنظام. بدل الاعتماد على اكتشاف Streamlit التلقائي لمجلد
الصفحات (الذي يجمّد أسماء الصفحات من اسم الملف بلغة واحدة ثابتة)، نبني هنا قائمة
الصفحات صراحةً بعناوين مترجمة تُعاد قراءتها من TRANSLATIONS في كل مرة يُعاد فيها
تحميل هذا الملف — أي عند كل تبديل لغة، تتحدّث القائمة الجانبية بالكامل فورًا.
ملاحظة: مجلد الصفحات مُسمّى app_pages (بدل pages) بناءً على توصية Streamlit
الرسمية، لتفادي أي تعارض بين نظام التنقّل اليدوي هنا واكتشاف الصفحات التلقائي.
"""
import streamlit as st
from i18n import t, get_lang

st.set_page_config(
    page_title="NXN Quality System | نظام NXN لإدارة الجودة",
    page_icon="✅",
    layout="wide",
)

# نقرأ اللغة الحالية فقط للتأكد من إعادة بناء القائمة عند كل تغيير (get_lang يقرأ من session_state)
_ = get_lang()

pages = [
    st.Page("home.py", title=t("nav_home"), url_path="", default=True),
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
]

pg = st.navigation(pages, position="sidebar")
pg.run()
