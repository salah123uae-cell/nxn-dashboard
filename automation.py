"""Safe overdue-corrective-action notification automation."""
import json
import os
from datetime import datetime

from database import get_session
from models import Audit, Branch, CorrectiveAction, Notification, User
from notifications import create_notification

OPEN_STATUSES = ("open", "in_progress")


def automation_enabled() -> bool:
    return os.getenv("OVERDUE_AUTOMATION_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }


def _recipient_users(session, action) -> list[User]:
    """Resolve active current branch managers and active system owners."""
    audit = session.get(Audit, action.audit_id)
    branch = session.get(Branch, audit.branch_id) if audit else None
    recipients: dict[int, User] = {}
    for user in session.query(User).filter(User.role == "owner", User.active.is_(True)).all():
        recipients[user.id] = user
    if branch:
        configured_email = (branch.manager_email or "").strip().lower()
        if configured_email:
            user = session.query(User).filter(
                User.email == configured_email, User.active.is_(True)
            ).first()
            if user:
                recipients[user.id] = user
        for user in session.query(User).filter(
            User.role == "branch", User.active.is_(True)
        ).all():
            try:
                if branch.id in json.loads(user.managed_branch_ids or "[]"):
                    recipients[user.id] = user
            except (TypeError, ValueError):
                continue
    return list(recipients.values())


def preview_overdue_corrective_actions() -> dict:
    now = datetime.utcnow()
    with get_session() as s:
        actions = s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(OPEN_STATUSES),
            CorrectiveAction.due_at < now,
            CorrectiveAction.overdue_notified_at.is_(None),
        ).all()
        return {
            "actions": len(actions),
            "recipients": sum(len(_recipient_users(s, action)) for action in actions),
        }


def check_overdue_corrective_actions(force: bool = False) -> int:
    """Create at-most-once notifications, guarded during production rollout."""
    if not force and not automation_enabled():
        return 0
    now = datetime.utcnow()
    notified_actions = 0
    with get_session() as s:
        query = s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(OPEN_STATUSES),
            CorrectiveAction.due_at < now,
            CorrectiveAction.overdue_notified_at.is_(None),
        )
        if s.bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)
        for action in query.all():
            recipients = _recipient_users(s, action)
            if not recipients:
                continue
            expected_keys = []
            for user in recipients:
                key = f"corrective-action-overdue:{action.id}:{user.id}"
                expected_keys.append(key)
                create_notification(
                    user.email, "corrective_action_overdue",
                    f"إجراء تصحيحي متأخر: {action.title}",
                    f"تجاوز الإجراء موعد استحقاقه ({action.due_at:%Y-%m-%d}) ولم يكتمل.",
                    link="Corrective_Actions", dedupe_key=key, session=s,
                )
            persisted = s.query(Notification.id).filter(
                Notification.dedupe_key.in_(expected_keys)
            ).count()
            if persisted == len(expected_keys):
                action.overdue_notified_at = now
                notified_actions += 1
    return notified_actions


def get_automation_stats() -> dict:
    with get_session() as s:
        currently_overdue = s.query(CorrectiveAction).filter(
            CorrectiveAction.status.in_(OPEN_STATUSES),
            CorrectiveAction.due_at < datetime.utcnow(),
        ).count()
        total_ever_notified = s.query(CorrectiveAction).filter(
            CorrectiveAction.overdue_notified_at.isnot(None)
        ).count()
    return {"currently_overdue": currently_overdue, "total_ever_notified": total_ever_notified}
