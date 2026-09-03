"""Transactional audit submission and corrective-action workflow."""
import json
from datetime import datetime

from models import Audit, AuditAnswer, AuditQuestion, Branch, CorrectiveAction, User
from utils import calculate_audit_score


VALID_ANSWERS = {"compliant", "non_compliant", "not_applicable"}


def _branch_manager_email(session, branch_id: int) -> str:
    branch = session.get(Branch, branch_id)
    if branch and branch.manager_email:
        return branch.manager_email.strip().lower()
    for user in session.query(User).filter(User.role == "branch", User.active.is_(True)).all():
        try:
            if branch_id in json.loads(user.managed_branch_ids or "[]"):
                return user.email
        except (TypeError, ValueError):
            continue
    # Keeps the action addressable by branch even before a manager account is assigned.
    return f"branch:{branch_id}"


def submit_audit(session, audit_id: int, answers: list[dict], actor_email: str) -> float:
    """Persist a complete audit once and create one action per failed answer."""
    audit = session.get(Audit, audit_id)
    if not audit or audit.status not in ("scheduled", "draft"):
        raise ValueError("audit_not_editable")

    questions = session.query(AuditQuestion).filter(
        AuditQuestion.checklist_version == audit.checklist_version,
        AuditQuestion.active.is_(True),
    ).all()
    qmap = {q.id: q for q in questions}
    supplied = {item.get("question_id"): item for item in answers}
    if len(supplied) != len(answers) or set(supplied) != set(qmap):
        raise ValueError("answers_incomplete_or_duplicate")
    if any(item.get("answer") not in VALID_ANSWERS for item in answers):
        raise ValueError("invalid_answer")
    if any(q.weight < 0 for q in questions):
        raise ValueError("invalid_question_weight")

    stored = []
    for question_id, question in qmap.items():
        data = supplied[question_id]
        row = session.query(AuditAnswer).filter_by(audit_id=audit_id, question_id=question_id).first()
        if row is None:
            row = AuditAnswer(audit_id=audit_id, question_id=question_id)
            session.add(row)
        row.answer = data["answer"]
        row.note = data.get("note", "")
        row.score_awarded = question.weight if row.answer == "compliant" else 0
        row.answered_by = actor_email
        row.answered_at = datetime.utcnow()
        stored.append(row)
    session.flush()

    score = calculate_audit_score(answers, qmap)
    audit.status = "submitted"
    audit.submitted_at = datetime.utcnow()
    audit.score = score
    manager_email = _branch_manager_email(session, audit.branch_id)
    for answer in stored:
        if answer.answer != "non_compliant":
            continue
        existing = session.query(CorrectiveAction).filter_by(answer_id=answer.id).first()
        if existing:
            continue
        question = qmap[answer.question_id]
        session.add(CorrectiveAction(
            audit_id=audit.id,
            answer_id=answer.id,
            title=f"معالجة عدم توافق: {question.code}",
            description=question.question_ar,
            owner_email=manager_email,
            due_at=datetime.utcnow(),
            priority="high",
            status="open",
        ))
    session.flush()
    return score


def respond_to_corrective_action(session, action_id: int, response_note: str, actor_email: str) -> None:
    action = session.get(CorrectiveAction, action_id)
    if not action or action.status not in ("open", "in_progress", "rejected"):
        raise ValueError("action_not_respondable")
    if not response_note.strip():
        raise ValueError("response_required")
    action.response_note = response_note.strip()
    action.responded_by = actor_email
    action.responded_at = datetime.utcnow()
    action.status = "pending_review"


def review_corrective_action(session, action_id: int, approve: bool, actor_email: str) -> None:
    action = session.get(CorrectiveAction, action_id)
    if not action or action.status != "pending_review":
        raise ValueError("action_not_pending_review")
    action.status = "closed" if approve else "rejected"
    action.closed_by = actor_email if approve else None
    action.completed_at = datetime.utcnow() if approve else None
