import streamlit as st
from branding import render_logo, apply_theme, render_card, BRAND_LIME, BRAND_BLUE, BRAND_PURPLE

from auth import require_role, render_logout_sidebar
from automation import (
    automation_enabled, check_overdue_corrective_actions,
    get_automation_stats, preview_overdue_corrective_actions,
)
from i18n import t, get_lang

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
require_role("owner", "manager")
render_logout_sidebar()

st.title(t("automation_title"))
st.caption(t("automation_caption"))

# ---------- قواعد الأتمتة النشطة حاليًا (توثيق شفاف لما يشتغل تلقائيًا بالفعل) ----------
st.markdown(f"##### {t('automation_active_rules_title')}")

render_card(
    f"""
    <div style="font-weight:700; color:{BRAND_BLUE}; font-size:15px;">{t('automation_rule_lockout')}</div>
    <div style="color:#5B5F73; font-size:13px; margin-top:4px; line-height:1.6;">{t('automation_rule_lockout_desc')}</div>
    """,
    accent=BRAND_LIME,
)
render_card(
    f"""
    <div style="font-weight:700; color:{BRAND_BLUE}; font-size:15px;">{t('automation_rule_corrective')}</div>
    <div style="color:#5B5F73; font-size:13px; margin-top:4px; line-height:1.6;">{t('automation_rule_corrective_desc')}</div>
    """,
    accent=BRAND_PURPLE,
)
render_card(
    f"""
    <div style="font-weight:700; color:{BRAND_BLUE}; font-size:15px;">{t('automation_rule_notifications')}</div>
    <div style="color:#5B5F73; font-size:13px; margin-top:4px; line-height:1.6;">{t('automation_rule_notifications_desc')}</div>
    """,
    accent=BRAND_BLUE,
)

st.divider()

# ---------- أتمتة تنبيه الإجراءات المتأخرة ----------
st.markdown(f"##### {t('automation_overdue_section_title')}")
st.info(t("automation_overdue_desc"))

_enabled = automation_enabled()
_preview = preview_overdue_corrective_actions()
if _enabled:
    st.success("الأتمتة مفعّلة" if lang == "ar" else "Automation is enabled")
else:
    st.warning(
        "وضع المعاينة الآمن: لن تُرسل تنبيهات حتى ضبط OVERDUE_AUTOMATION_ENABLED=true."
        if lang == "ar" else
        "Safe preview mode: no alerts are sent until OVERDUE_AUTOMATION_ENABLED=true."
    )
st.caption(
    (f"المعاينة: {_preview['actions']} إجراء، {_preview['recipients']} مستلم محتمل"
     if lang == "ar" else
     f"Preview: {_preview['actions']} actions, {_preview['recipients']} potential recipients")
)

# يشتغل الفحص تلقائيًا مرة واحدة بكل جلسة عند فتح الصفحة (بدون إزعاج بإعادة
# الفحص مع كل rerun ناتج عن تفاعل آخر بنفس الصفحة).
if _enabled and "automation_auto_ran" not in st.session_state:
    _auto_notified = check_overdue_corrective_actions()
    st.session_state["automation_auto_ran"] = True
    if _auto_notified:
        st.success(t("automation_run_result", n=_auto_notified))

_stats = get_automation_stats()
sc1, sc2 = st.columns(2)
sc1.metric(t("automation_currently_overdue"), _stats["currently_overdue"])
sc2.metric(t("automation_total_notified"), _stats["total_ever_notified"])

if st.button(t("automation_run_now_btn"), key="automation_run_now", disabled=not _enabled):
    _notified = check_overdue_corrective_actions()
    if _notified:
        st.success(t("automation_run_result", n=_notified))
    else:
        st.info(t("automation_run_result_none"))
    st.rerun()
