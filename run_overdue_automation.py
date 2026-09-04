"""Entrypoint used by the scheduled production automation."""
from database import init_db
from automation import check_overdue_corrective_actions, preview_overdue_corrective_actions


if __name__ == "__main__":
    init_db()
    preview = preview_overdue_corrective_actions()
    sent = check_overdue_corrective_actions()
    print(f"eligible_actions={preview['actions']} potential_recipients={preview['recipients']} processed={sent}")
