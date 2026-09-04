"""
وحدة الإشعارات داخل النظام — تنشئ إشعارات للمستخدمين عند أحداث مهمة
(إسناد تدقيق، إنشاء إجراء تصحيحي، قبول طلب حساب/استعادة كلمة مرور)،
وتوفر دوال لعرضها وتحديد المقروء منها.
"""
from datetime import datetime

from database import get_session
from models import Notification, User


def create_notification(user_email: str, ntype: str, title: str, body: str, link: str | None = None):
    """ينشئ إشعارًا لمستخدم عبر بريده الإلكتروني (يبحث عن معرّفه أولًا)."""
    with get_session() as s:
        user = s.query(User).filter(User.email == user_email.strip().lower()).first()
        if not user:
            return
        s.add(Notification(
            user_id=user.id, type=ntype, title=title, body=body, link=link,
        ))


def get_notifications(user_id: int, limit: int = 15) -> list[dict]:
    with get_session() as s:
        rows = (
            s.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        return [{
            "id": n.id, "type": n.type, "title": n.title, "body": n.body,
            "link": n.link, "read_at": n.read_at, "created_at": n.created_at,
        } for n in rows]


def get_unread_count(user_id: int) -> int:
    with get_session() as s:
        return (
            s.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
            .count()
        )


def mark_as_read(notification_id: int):
    with get_session() as s:
        n = s.query(Notification).get(notification_id)
        if n and not n.read_at:
            n.read_at = datetime.utcnow()


def mark_all_as_read(user_id: int):
    with get_session() as s:
        (
            s.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
            .update({"read_at": datetime.utcnow()})
        )


def render_notification_bell(home_page=None):
    """يعرض مؤشر إشعارات دائري ملوّن (رقم العدّاد نفسه ظاهر داخل الدائرة، بدون
    محاولة رسم شكل جرس عبر CSS mask-image بصيغة SVG — تلك التقنية غير موثوقة
    عبر كل المتصفحات وتُنتج نقطة مشوّهة بدل شكل واضح). يظهر أعلى كل صفحة
    بالنظام، مو بس الرئيسية. عند الضغط عليه، ينتقل المستخدم مباشرة للصفحة
    الرئيسية حيث تظهر بطاقات الإشعارات الكاملة الملوّنة. الدائرة تنبض بحركة
    خفيفة لما فيه إشعارات غير مقروءة، لجذب الانتباه بدون إزعاج.
    home_page: كائن st.Page الفعلي (وليس نص المسار) — مطلوب هنا تحديدًا لأن
    النظام يبني التنقّل يدويًا عبر st.navigation()+st.Page()، و st.switch_page()
    لا يتعرّف بشكل موثوق على مسار نصي بهذا النمط، فنمرّر الكائن نفسه بدلًا من ذلك.
    ملاحظة تقنية: نستخدم st.container(key=...) (موثّق رسميًا من Streamlit
    لهذا الغرض بالضبط) لتنسيق الزر بدقة، بدل أساليب CSS هشّة تعتمد على تخمين
    بنية DOM الداخلية."""
    import streamlit as st
    from auth import current_user

    user = current_user()
    if not user:
        return

    unread = get_unread_count(user["id"])
    has_unread = unread > 0
    bell_color = "#B91C1C" if has_unread else "#9CA3AF"
    label = str(unread) if unread < 100 else "99+"

    st.markdown(
        f"""
        <style>
        @keyframes nxn-badge-pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(185, 28, 28, 0.5); }}
            70% {{ box-shadow: 0 0 0 7px rgba(185, 28, 28, 0); }}
        }}
        .st-key-nxn_bell_container {{
            display: flex; justify-content: center;
        }}
        .st-key-nxn_bell_container button {{
            background: {bell_color} !important;
            color: white !important;
            border: none !important;
            border-radius: 50% !important;
            width: 38px !important; height: 38px !important;
            min-width: 38px !important;
            padding: 0 !important;
            font-weight: 800 !important;
            box-shadow: 0 2px 8px rgba(30,34,170,0.18) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
            animation: {"nxn-badge-pulse 2s ease-in-out infinite" if has_unread else "none"};
        }}
        .st-key-nxn_bell_container button p {{
            font-size: 14px !important;
            font-weight: 800 !important;
            margin: 0 !important;
            color: white !important;
        }}
        .st-key-nxn_bell_container button:hover {{
            transform: translateY(-2px) scale(1.06);
            box-shadow: 0 6px 16px rgba(30,34,170,0.3) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="nxn_bell_container"):
        clicked = st.button(
            label, key="nxn_notif_bell_btn",
            help="الإشعارات" if unread else "لا توجد إشعارات جديدة",
        )
    if clicked:
        if home_page is not None:
            st.switch_page(home_page)
        else:
            st.switch_page("home.py")

