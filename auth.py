"""
منطق تسجيل الدخول، تشفير كلمات المرور، وإدارة الأدوار/الصلاحيات.
الأدوار: owner (مالك) > manager (مدير) > auditor (مدقق) > branch (فرع) > viewer (مشاهد)
"""
import json
import bcrypt
import streamlit as st
from datetime import datetime

from database import get_session
from models import User, Credential, AuditLog, SignupRequest, PasswordResetRequest

LOCKOUT_THRESHOLD = 5          # عدد المحاولات الفاشلة المتتالية قبل القفل المؤقت
LOCKOUT_DURATION_MINUTES = 15  # مدة القفل بالدقائق

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
    from datetime import timedelta
    from i18n import t  # استيراد محلي لتفادي أي حلقة استيراد دائرية

    with get_session() as s:
        user = s.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.active:
            return False, t("account_disabled_or_pending")

        if user.suspended_until and user.suspended_until > datetime.utcnow():
            return False, f"الحساب موقوف حتى {user.suspended_until}"

        cred = s.query(Credential).filter(Credential.user_id == user.id).first()

        # ---------- التحقق من القفل المؤقت بسبب محاولات فاشلة متكررة ----------
        if cred and cred.locked_until and cred.locked_until > datetime.utcnow():
            remaining = cred.locked_until - datetime.utcnow()
            minutes_left = max(1, int(remaining.total_seconds() // 60) + 1)
            return False, f"الحساب مقفل مؤقتًا بسبب محاولات دخول فاشلة متكررة. حاول بعد {minutes_left} دقيقة."

        if not cred or not verify_password(password, cred.password_hash):
            if cred:
                cred.failed_attempts = (cred.failed_attempts or 0) + 1
                if cred.failed_attempts >= LOCKOUT_THRESHOLD:
                    cred.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                    cred.failed_attempts = 0
                    log_action(email, "lockout", "user", entity_id=email)
                    return False, f"تم قفل الحساب مؤقتًا لمدة {LOCKOUT_DURATION_MINUTES} دقيقة بسبب محاولات دخول فاشلة متكررة."
            return False, "كلمة المرور غير صحيحة"

        cred.failed_attempts = 0
        cred.locked_until = None
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
    from i18n import t  # استيراد محلي لتفادي أي حلقة استيراد دائرية

    if not current_user():
        st.warning(t("login_required"))
        st.stop()


def require_role(*allowed_roles: str):
    """يوقف تنفيذ الصفحة إن لم يكن دور المستخدم من ضمن الأدوار المسموحة."""
    from i18n import t  # استيراد محلي لتفادي أي حلقة استيراد دائرية

    require_login()
    user = current_user()
    if user["role"] not in allowed_roles:
        st.error(t("no_permission"))
        st.stop()


def can_manage_branch(user: dict, branch_id: int) -> bool:
    if user["role"] in ("owner", "manager"):
        return True
    if user["role"] == "branch":
        return branch_id in user.get("managed_branch_ids", [])
    return False


def create_signup_request(first_name: str, last_name: str, email: str,
                           employee_number: str, password: str) -> tuple[bool, str]:
    """ينشئ طلب حساب جديد بانتظار موافقة الإدارة. يرجع (نجاح, رسالة)."""
    email = email.strip().lower()
    with get_session() as s:
        if s.query(User).filter(User.email == email).first():
            return False, "email_exists"
        if s.query(SignupRequest).filter(
            SignupRequest.email == email, SignupRequest.status == "pending"
        ).first():
            return False, "signup_already_pending"
        s.add(SignupRequest(
            first_name=first_name.strip(), last_name=last_name.strip(), email=email,
            employee_number=employee_number.strip() or None,
            password_hash=hash_password(password), status="pending",
        ))
    return True, "signup_request_created"


def approve_signup_request(request_id: int, reviewer_email: str, role: str = "auditor") -> tuple[bool, str]:
    """يوافق على طلب حساب: ينشئ المستخدم والاعتماد الفعليين، ويعلّم الطلب كمقبول."""
    with get_session() as s:
        req = s.query(SignupRequest).get(request_id)
        if not req or req.status != "pending":
            return False, "request_not_found"
        if s.query(User).filter(User.email == req.email).first():
            req.status = "rejected"
            req.reviewed_by = reviewer_email
            req.reviewed_at = datetime.utcnow()
            return False, "email_exists"

        new_user = User(
            email=req.email, name=f"{req.first_name} {req.last_name}".strip(),
            employee_number=req.employee_number, role=role,
        )
        s.add(new_user)
        s.flush()
        s.add(Credential(user_id=new_user.id, password_hash=req.password_hash))

        req.status = "approved"
        req.reviewed_by = reviewer_email
        req.reviewed_at = datetime.utcnow()
        req_email = req.email
    log_action(reviewer_email, "approve", "signup_request", request_id, after={"email": req_email})
    from notifications import create_notification
    create_notification(
        req_email, "signup_approved", "تم قبول حسابك",
        "تمت الموافقة على طلب إنشاء حسابك، تقدر تسجّلين الدخول الآن.",
    )
    return True, "signup_approved"


def reject_signup_request(request_id: int, reviewer_email: str) -> tuple[bool, str]:
    with get_session() as s:
        req = s.query(SignupRequest).get(request_id)
        if not req or req.status != "pending":
            return False, "request_not_found"
        req.status = "rejected"
        req.reviewed_by = reviewer_email
        req.reviewed_at = datetime.utcnow()
        req_email = req.email
    log_action(reviewer_email, "reject", "signup_request", request_id, after={"email": req_email})
    return True, "signup_rejected"


def create_password_reset_request(email: str, new_password: str) -> tuple[bool, str]:
    """ينشئ طلب تغيير كلمة مرور بانتظار موافقة الإدارة. يرجع (نجاح, رسالة)."""
    email = email.strip().lower()
    with get_session() as s:
        user = s.query(User).filter(User.email == email).first()
        if not user:
            return False, "email_not_found"
        if s.query(PasswordResetRequest).filter(
            PasswordResetRequest.email == email, PasswordResetRequest.status == "pending"
        ).first():
            return False, "reset_already_pending"
        s.add(PasswordResetRequest(
            email=email, new_password_hash=hash_password(new_password), status="pending",
        ))
    return True, "reset_request_created"


def approve_password_reset(request_id: int, reviewer_email: str) -> tuple[bool, str]:
    with get_session() as s:
        req = s.query(PasswordResetRequest).get(request_id)
        if not req or req.status != "pending":
            return False, "request_not_found"
        user = s.query(User).filter(User.email == req.email).first()
        if not user:
            req.status = "rejected"
            req.reviewed_by = reviewer_email
            req.reviewed_at = datetime.utcnow()
            return False, "email_not_found"

        cred = s.query(Credential).filter(Credential.user_id == user.id).first()
        if not cred:
            cred = Credential(user_id=user.id)
            s.add(cred)
        cred.password_hash = req.new_password_hash
        cred.password_changed_at = datetime.utcnow()
        cred.failed_attempts = 0

        req.status = "approved"
        req.reviewed_by = reviewer_email
        req.reviewed_at = datetime.utcnow()
        req_email = req.email
    log_action(reviewer_email, "approve", "password_reset_request", request_id, after={"email": req_email})
    from notifications import create_notification
    create_notification(
        req_email, "reset_approved", "تم تحديث كلمة المرور",
        "تمت الموافقة على طلب استعادة كلمة المرور وتحديثها.",
    )
    return True, "reset_approved"


def reject_password_reset(request_id: int, reviewer_email: str) -> tuple[bool, str]:
    with get_session() as s:
        req = s.query(PasswordResetRequest).get(request_id)
        if not req or req.status != "pending":
            return False, "request_not_found"
        req.status = "rejected"
        req.reviewed_by = reviewer_email
        req.reviewed_at = datetime.utcnow()
        req_email = req.email
    log_action(reviewer_email, "reject", "password_reset_request", request_id, after={"email": req_email})
    return True, "reset_rejected"


def change_own_password(user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
    """يغيّر كلمة مرور المستخدم الحالي مباشرة، بعد التأكد من كلمة المرور الحالية.
    لا يحتاج موافقة إدارية (بخلاف مسار \"نسيت كلمة المرور\") لأن المستخدم أثبت
    هويته بالفعل بمعرفة كلمة المرور الحالية وتسجيل دخوله."""
    with get_session() as s:
        cred = s.query(Credential).filter(Credential.user_id == user_id).first()
        if not cred or not verify_password(current_password, cred.password_hash):
            return False, "current_password_incorrect"
        cred.password_hash = hash_password(new_password)
        cred.password_changed_at = datetime.utcnow()
    return True, "password_changed"


def render_logout_sidebar():
    """يعرض اسم المستخدم الحالي، تغيير كلمة المرور، وزر تسجيل الخروج بالشريط
    الجانبي — يظهر بكل صفحة."""
    from i18n import t  # استيراد محلي لتفادي أي حلقة استيراد دائرية

    user = current_user()
    if not user:
        return
    with st.sidebar:
        st.divider()
        role_label = ROLE_LABELS_AR.get(user["role"], user["role"])
        st.caption(f"{user['name']} — {role_label}")

        with st.expander(t("change_password_title")):
            with st.form("change_own_password_form", clear_on_submit=True):
                current_pw = st.text_input(t("current_password_label"), type="password")
                new_pw1 = st.text_input(t("new_password_label2"), type="password", key="cop_new1")
                new_pw2 = st.text_input(t("confirm_new_password_label"), type="password", key="cop_new2")
                submitted = st.form_submit_button(t("change_password_btn"))
                if submitted:
                    if not current_pw or not new_pw1:
                        st.error(t("fill_required"))
                    elif new_pw1 != new_pw2:
                        st.error(t("password_mismatch"))
                    else:
                        ok, msg_key = change_own_password(user["id"], current_pw, new_pw1)
                        if ok:
                            log_action(user["email"], "change_password", "user", user["id"])
                            st.success(t("password_changed_msg"))
                        else:
                            st.error(t("current_password_wrong"))

        if st.button(t("logout"), key="global_logout_btn", use_container_width=True):
            logout()
            st.rerun()

