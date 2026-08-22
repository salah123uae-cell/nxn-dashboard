import streamlit as st
from branding import render_logo, apply_theme

from auth import require_role, current_user, render_logout_sidebar, log_action
from backup import BackupValidationError, export_all_data, import_all_data
from i18n import t, language_switcher, get_lang

st.set_page_config(page_title="Backup | النسخ الاحتياطي", page_icon="💾", layout="wide")

lang = get_lang()
apply_theme(direction="ltr" if lang == "en" else "rtl")
render_logo(size="small")
language_switcher()
require_role("owner")
render_logout_sidebar()
user = current_user()

st.title(t("backup_title"))
st.warning(t("backup_warning"))

st.divider()
st.subheader(t("export_backup_title"))
st.write(t("export_backup_desc"))

if st.button(t("export_backup_btn"), key="prepare_export"):
    backup_bytes = export_all_data()
    st.session_state["_backup_bytes"] = backup_bytes
    log_action(user["email"], "export", "backup")

if "_backup_bytes" in st.session_state:
    from datetime import datetime
    fname = f"nxn_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button(
        t("export_backup_btn"), data=st.session_state["_backup_bytes"],
        file_name=fname, mime="application/json", key="download_backup_btn",
    )

st.divider()
st.subheader(t("import_backup_title"))
st.error(t("import_backup_desc"))
st.caption("Full restore replaces every system table atomically. الاستعادة الكاملة تستبدل جميع بيانات النظام.")

uploaded = st.file_uploader(t("import_backup_uploader"), type=["json"], key="restore_uploader")
confirmation = st.text_input(
    "Type RESTORE to confirm | اكتب RESTORE للتأكيد",
    key="restore_confirmation",
)
if uploaded is not None:
    restore_disabled = confirmation != "RESTORE"
    if st.button(t("import_backup_btn"), key="run_import", disabled=restore_disabled):
        try:
            counts = import_all_data(uploaded.getvalue(), replace_existing=True)
            st.session_state.pop("_backup_bytes", None)
            log_action(user["email"], "restore", "backup", after=counts)
            st.success(f"{t('import_success')} {counts}")
            st.session_state.pop("user", None)
            st.rerun()
        except BackupValidationError:
            st.error(t("import_error"))
        except Exception:
            st.error(t("import_error"))
