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
    """يعرض جرس إشعارات احترافي تفاعليًا: أيقونة SVG حقيقية لشكل جرس (مرسومة
    مباشرة كعنصر HTML، بدون الاعتماد على تقنية CSS mask-image غير الموثوقة
    عبر المتصفحات المختلفة)، فوق زر دائري شفاف يتولى فعل الضغط والتنقّل.
    شارة عدّاد حمراء صغيرة بأعلى الزاوية تنبض بحركة خفيفة لما فيه إشعارات
    غير مقروءة، لجذب الانتباه بدون إزعاج. يظهر أعلى كل صفحة بالنظام.
    home_page: كائن st.Page الفعلي (وليس نص المسار) — مطلوب هنا تحديدًا لأن
    النظام يبني التنقّل يدويًا عبر st.navigation()+st.Page()، و st.switch_page()
    لا يتعرّف بشكل موثوق على مسار نصي بهذا النمط، فنمرّر الكائن نفسه بدلًا من ذلك.
    ملاحظة تقنية: نستخدم st.container(key=...) (موثّق رسميًا من Streamlit
    لهذا الغرض بالضبط) لتنسيق الزر بدقة، ونضع أيقونة SVG حقيقية فوقه بموضع
    مطلق (pointer-events:none حتى يمرّ الضغط للزر تحتها مباشرة)."""
    import streamlit as st
    from auth import current_user

    user = current_user()
    if not user:
        return

    unread = get_unread_count(user["id"])
    has_unread = unread > 0
    bell_color = "#1E22AA" if has_unread else "#6B7280"
    ring_color = "#44D62C" if has_unread else "#E3E4F6"
    badge_display = str(unread) if unread < 100 else "99+"

    st.markdown(
        f"""
        <style>
        @keyframes nxn-bell-swing {{
            0%, 100% {{ transform: rotate(0deg); }}
            20% {{ transform: rotate(-12deg); }}
            40% {{ transform: rotate(10deg); }}
            60% {{ transform: rotate(-6deg); }}
            80% {{ transform: rotate(3deg); }}
        }}
        @keyframes nxn-badge-pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(185, 28, 28, 0.55); }}
            70% {{ box-shadow: 0 0 0 7px rgba(185, 28, 28, 0); }}
        }}
        .st-key-nxn_bell_container {{
            position: relative;
            display: flex; justify-content: center;
            width: 44px; height: 44px;
        }}
        .st-key-nxn_bell_container button {{
            background: white !important;
            border: 2px solid {ring_color} !important;
            border-radius: 50% !important;
            width: 44px !important; height: 44px !important;
            min-width: 44px !important;
            padding: 0 !important;
            box-shadow: 0 2px 10px rgba(30,34,170,0.14) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
        }}
        .st-key-nxn_bell_container button p {{
            font-size: 0 !important;
        }}
        .st-key-nxn_bell_container button:hover {{
            transform: translateY(-2px);
            border-color: {bell_color} !important;
            box-shadow: 0 8px 18px rgba(30,34,170,0.22) !important;
        }}
        .nxn-bell-icon {{
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            display: flex; align-items: center; justify-content: center;
            pointer-events: none;
        }}
        .nxn-bell-icon svg {{
            width: 20px; height: 20px;
            animation: {"nxn-bell-swing 1.8s ease-in-out infinite" if has_unread else "none"};
            transform-origin: top center;
        }}
        .nxn-bell-badge {{
            position: absolute; top: -4px; right: -4px;
            min-width: 18px; height: 18px; padding: 0 4px;
            background: #B91C1C; color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, Arial, sans-serif;
            font-size: 10px; font-weight: 800; line-height: 18px; text-align: center;
            border-radius: 9px; box-shadow: 0 0 0 2px white;
            pointer-events: none;
            animation: {"nxn-badge-pulse 2s ease-in-out infinite" if has_unread else "none"};
        }}
        </style>
        <div class="nxn-bell-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 3C9.5 3 7.5 5 7.5 7.5V11C7.5 11.8 7.15 12.55 6.55 13.1L5 14.5V16H19V14.5L17.45 13.1C16.85 12.55 16.5 11.8 16.5 11V7.5C16.5 5 14.5 3 12 3Z"
                      stroke="{bell_color}" stroke-width="1.8" stroke-linejoin="round" fill="{bell_color}22"/>
                <path d="M9.5 18.5C9.8 19.6 10.8 20.5 12 20.5C13.2 20.5 14.2 19.6 14.5 18.5"
                      stroke="{bell_color}" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            {f'<div class="nxn-bell-badge">{badge_display}</div>' if has_unread else ''}
        </div>
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

