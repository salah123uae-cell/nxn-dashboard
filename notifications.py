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

