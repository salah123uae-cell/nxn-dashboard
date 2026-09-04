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
    """يعرض جرس إشعارات تفاعليًا (شكل SVG أنيق + شارة عدّاد ملوّنة، بدون إيموجي)
    أعلى كل صفحة — مو بس بالصفحة الرئيسية. عند الضغط عليه، ينتقل المستخدم مباشرة
    للصفحة الرئيسية حيث تظهر بطاقات الإشعارات الكاملة الملوّنة. الشارة تنبض
    بحركة خفيفة لما فيه إشعارات غير مقروءة، لجذب الانتباه بدون إزعاج.
    home_page: كائن st.Page الفعلي (وليس نص المسار) — مطلوب هنا تحديدًا لأن
    النظام يبني التنقّل يدويًا عبر st.navigation()+st.Page()، و st.switch_page()
    لا يتعرّف بشكل موثوق على مسار نصي بهذا النمط، فنمرّر الكائن نفسه بدلًا من ذلك.
    ملاحظة تقنية: نستخدم st.container(key=...) بدل أسلوب "علامة + شقيق مجاور"
    بالـ CSS، لأن الأخير هشّ ويعتمد على افتراض دقيق لبنية DOM الداخلية
    (قد يفشل بصمت لو أضافت Streamlit طبقة تغليف إضافية حول st.markdown)."""
    import streamlit as st
    from auth import current_user

    user = current_user()
    if not user:
        return

    unread = get_unread_count(user["id"])
    has_unread = unread > 0
    badge_color = "#B91C1C" if has_unread else "#4B5563"
    bell_color = "#44D62C" if has_unread else "#9CA3AF"
    count_display = str(unread) if unread < 100 else "99+"

    st.markdown(
        f"""
        <style>
        @keyframes nxn-bell-pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.12); }}
        }}
        @keyframes nxn-badge-pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(185, 28, 28, 0.55); }}
            70% {{ box-shadow: 0 0 0 8px rgba(185, 28, 28, 0); }}
        }}
        .st-key-nxn_bell_container {{
            display: flex; justify-content: center;
        }}
        .st-key-nxn_bell_container button {{
            position: relative;
            background: white !important;
            border: 2px solid {bell_color} !important;
            border-radius: 50% !important;
            width: 42px !important; height: 42px !important;
            min-width: 42px !important;
            padding: 0 !important;
            box-shadow: 0 2px 8px rgba(30,34,170,0.12) !important;
            transition: all 0.2s ease !important;
        }}
        .st-key-nxn_bell_container button p {{
            font-size: 0 !important;
        }}
        .st-key-nxn_bell_container button::before {{
            content: "";
            position: absolute; inset: 0; margin: auto;
            width: 18px; height: 18px;
            background-color: {bell_color};
            -webkit-mask-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2a6 6 0 0 0-6 6v3.09c0 .49-.2.96-.55 1.3L4 14v2h16v-2l-1.45-1.61a1.8 1.8 0 0 1-.55-1.3V8a6 6 0 0 0-6-6zm0 20a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22z"/></svg>');
            mask-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2a6 6 0 0 0-6 6v3.09c0 .49-.2.96-.55 1.3L4 14v2h16v-2l-1.45-1.61a1.8 1.8 0 0 1-.55-1.3V8a6 6 0 0 0-6-6zm0 20a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22z"/></svg>');
            -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat;
            -webkit-mask-position: center; mask-position: center;
            animation: {"nxn-bell-pulse 2s ease-in-out infinite" if has_unread else "none"};
        }}
        .st-key-nxn_bell_container button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(30,34,170,0.2) !important;
        }}
        .st-key-nxn_bell_container button:after {{
            content: "{count_display if has_unread else ''}";
            position: absolute; top: -6px; right: -6px;
            background: {badge_color}; color: white;
            font-size: 10px; font-weight: 800;
            min-width: 18px; height: 18px; line-height: 18px;
            border-radius: 9px; padding: 0 4px;
            box-shadow: 0 0 0 2px white;
            animation: {"nxn-badge-pulse 2s ease-in-out infinite" if has_unread else "none"};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="nxn_bell_container"):
        clicked = st.button(
            " ", key="nxn_notif_bell_btn",
            help="الإشعارات" if unread else "لا توجد إشعارات جديدة",
        )
    if clicked:
        if home_page is not None:
            st.switch_page(home_page)
        else:
            st.switch_page("home.py")

