"""
منطق تسجيل الدخول، تشفير كلمات المرور، وإدارة الأدوار/الصلاحيات.
الأدوار: owner (مالك) > manager (مدير) > auditor (مدقق) > branch (فرع) > viewer (مشاهد)
"""
import json
import bcrypt
import streamlit as st
from datetime import datetime

from database import get_session
from models import User, Credential, AuditLog

ROLES = ["owner", "manager", "auditor", "branch", "viewer"]

ROLE_LABELS_AR = {
    "owner": "مالك النظام",
    "manager": "مدير",
    "auditor": "مدقق",
    "branch": "فرع",
    "viewer": "مشاهد",
}


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def log_action(actor_email: str, action: str, entity_type: str, entity_id=None, before=None, after=None):
    with get_session() as s:
        s.add(AuditLog(
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            before_json=json.dumps(before, ensure_ascii=False, default=str) if before else None,
            after_json=json.dumps(after, ensure_ascii=False, default=str) if after else None,
        ))


def login(email: str, password: str) -> tuple[bool, str]:
    """يحاول تسجيل الدخول. يرجع (نجاح, رسالة)."""
    with get_session() as s:
        user = s.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.active:
            return False, "البريد الإلكتروني غير موجود أو الحساب معطّل"

        if user.suspended_until and user.suspended_until > datetime.utcnow():
            return False, f"الحساب موقوف حتى {user.suspended_until}"

        cred = s.query(Credential).filter(Credential.user_id == user.id).first()
        if not cred or not verify_password(password, cred.password_hash):
            if cred:
                cred.failed_attempts = (cred.failed_attempts or 0) + 1
            return False, "كلمة المرور غير صحيحة"

        cred.failed_attempts = 0
        user.last_login_at = datetime.utcnow()

        st.session_state["user"] = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "managed_branch_ids": json.loads(user.managed_branch_ids or "[]"),
        }
    log_action(email, "login", "user", entity_id=email)
    return True, "تم تسجيل الدخول بنجاح"


def logout():
    if "user" in st.session_state:
        log_action(st.session_state["user"]["email"], "logout", "user")
    st.session_state.pop("user", None)


def current_user() -> dict | None:
    return st.session_state.get("user")


def require_login():
    """يوقف تنفيذ الصفحة إن لم يكن هناك مستخدم مسجّل دخول."""
    if not current_user():
        st.warning("🔒 الرجاء تسجيل الدخول أولاً من الصفحة الرئيسية")
        st.stop()


def require_role(*allowed_roles: str):
    """يوقف تنفيذ الصفحة إن لم يكن دور المستخدم من ضمن الأدوار المسموحة."""
    require_login()
    user = current_user()
    if user["role"] not in allowed_roles:
        st.error("🚫 ليس لديك صلاحية للوصول لهذه الصفحة")
        st.stop()


def can_manage_branch(user: dict, branch_id: int) -> bool:
    if user["role"] in ("owner", "manager"):
        return True
    if user["role"] == "branch":
        return branch_id in user.get("managed_branch_ids", [])
    return False
