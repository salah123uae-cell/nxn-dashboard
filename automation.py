"""
منطق مركز الأتمتة: يفحص الإجراءات التصحيحية المتأخرة (تجاوزت due_at ولسا
مفتوحة/قيد التنفيذ) ويرسل إشعارًا تلقائيًا لمدير الفرع المسؤول ولمالك النظام
لو ما زال ما تم التنبيه عنها (باستخدام overdue_notified_at كعلامة لتفادي
التكرار). ملاحظة معمارية: بما إن Streamlit ما يوفر مجدولًا (scheduler) خلفيًا
حقيقيًا، هذا الفحص يشتغل عند زيارة صفحة "مركز الأتمتة" فعليًا (تلقائيًا عند
التحميل + زر تشغيل يدوي)، بدل الاعتماد على مهمة دورية بالخلفية غير متوفرة
بهذي البيئة.
"""
from datetime import datetime

from database import get_session
from models import CorrectiveAction, User
from notifications import create_notification


def check_overdue_corrective_actions() -> int:
    """يفحص كل الإجراءات التصحيحية المفتوحة/قيد التنفيذ اللي تجاوزت موعد
    استحقاقها ولسا ما تم التنبيه عنها، يرسل إشعارًا لمدير الفرع المسؤول
    ولكل ملّاك النظام، ويعلّمها كمُنبَّه عنها. يرجع عدد الإجراءات اللي تم
    التنبيه عنها فعليًا بهذا التشغيل."""
    now = datetime.utcnow()
    notified_count = 0

    with get_session() as s:
        overdue = (
            s.query(CorrectiveAction)
            .filter(
                CorrectiveAction.status.in_(["open", "in_progress"]),
                CorrectiveAction.due_at < now,
                CorrectiveAction.overdue_notified_at.is_(None),
            )
            .all()
        )
        if not overdue:
            return 0

        owner_emails = [u.email for u in s.query(User).filter(User.role == "owner", User.active.is_(True)).all()]

        for action in overdue:
            action.overdue_notified_at = now
            notified_count += 1
            recipients = {action.owner_email, *owner_emails}
            for email in recipients:
                if not email:
                    continue
                create_notification(
                    email, "corrective_action_overdue",
                    f"إجراء تصحيحي متأخر: {action.title}",
                    f"تجاوز الإجراء موعد استحقاقه ({action.due_at.strftime('%Y-%m-%d')}) ولسا غير مكتمل.",
                )

    return notified_count


def get_automation_stats() -> dict:
    """يرجع إحصائيات سريعة لعرضها بمركز الأتمتة: عدد الإجراءات المتأخرة
    حاليًا (بعد آخر فحص)، وإجمالي الإجراءات اللي تم التنبيه عنها تلقائيًا
    منذ بداية تفعيل هذي الميزة."""
    with get_session() as s:
        currently_overdue = (
            s.query(CorrectiveAction)
            .filter(
                CorrectiveAction.status.in_(["open", "in_progress"]),
                CorrectiveAction.due_at < datetime.utcnow(),
            )
            .count()
        )
        total_ever_notified = (
            s.query(CorrectiveAction)
            .filter(CorrectiveAction.overdue_notified_at.isnot(None))
            .count()
        )
    return {
        "currently_overdue": currently_overdue,
        "total_ever_notified": total_ever_notified,
    }
