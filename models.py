"""
نماذج قاعدة البيانات - مقتبسة من db/schema.ts الأصلي (Drizzle ORM)
تمت إعادة بنائها باستخدام SQLAlchemy لتعمل مع PostgreSQL.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, UniqueConstraint, Index, LargeBinary
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def now():
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    employee_number = Column(String, nullable=True)
    role = Column(String, nullable=False, default="auditor")  # owner, manager, auditor, branch, viewer
    managed_branch_ids = Column(Text, nullable=False, default="[]")  # JSON list كنص
    phone = Column(String)
    active = Column(Boolean, nullable=False, default=True)
    suspended_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    credential = relationship("Credential", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Credential(Base):
    __tablename__ = "credentials"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    password_hash = Column(String, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    user = relationship("User", back_populates="credential")


class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    region = Column(String, nullable=False)
    city = Column(String, nullable=False, default="")
    manager_email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="active")  # active, inactive, suspended
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    __table_args__ = (
        Index("branches_status_idx", "status"),
        Index("branches_region_idx", "region"),
    )


class ChecklistVersion(Base):
    __tablename__ = "checklist_versions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    status = Column(String, nullable=False, default="draft")  # draft, active, retired
    effective_from = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)


class AuditSection(Base):
    __tablename__ = "audit_sections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    name_ar = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    weight = Column(Integer, nullable=False)
    sort_order = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class AuditQuestion(Base):
    __tablename__ = "audit_questions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(Integer, ForeignKey("audit_sections.id"), nullable=False)
    code = Column(String, nullable=False, unique=True)
    question_ar = Column(Text, nullable=False)
    question_en = Column(Text, nullable=False)
    weight = Column(Float, nullable=False)
    checklist_version = Column(String, nullable=False, default="QV1")
    evidence_required_on_failure = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    section = relationship("AuditSection")

    __table_args__ = (
        Index("questions_section_idx", "section_id"),
        Index("questions_version_idx", "checklist_version"),
    )


class Audit(Base):
    __tablename__ = "audits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reference = Column(String, nullable=False, unique=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    auditor_email = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    visit_latitude = Column(Float, nullable=True)
    visit_longitude = Column(Float, nullable=True)
    visit_accuracy = Column(Float, nullable=True)
    location_captured_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="scheduled")
    # scheduled, draft, submitted, reviewed, closed, cancelled
    score = Column(Float, nullable=True)
    dashboard_visible = Column(Boolean, nullable=False, default=True)
    checklist_version = Column(String, nullable=False, default="QV1")
    notes = Column(Text, nullable=False, default="")
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    branch = relationship("Branch")

    __table_args__ = (
        Index("audits_branch_idx", "branch_id"),
        Index("audits_status_idx", "status"),
        Index("audits_auditor_idx", "auditor_email"),
    )


class AuditAnswer(Base):
    __tablename__ = "audit_answers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("audit_questions.id"), nullable=False)
    answer = Column(String, nullable=True)  # compliant, non_compliant, not_applicable
    score_awarded = Column(Float, nullable=False, default=0)
    note = Column(Text, nullable=False, default="")
    answered_by = Column(String, nullable=True)
    answered_at = Column(DateTime, nullable=True)

    audit = relationship("Audit")
    question = relationship("AuditQuestion")

    __table_args__ = (
        UniqueConstraint("audit_id", "question_id", name="answers_audit_question_uq"),
        Index("answers_audit_idx", "audit_id"),
    )


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=False)
    answer_id = Column(Integer, nullable=True)
    corrective_action_id = Column(Integer, nullable=True)
    file_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    file_data = Column(LargeBinary, nullable=False)  # تخزين الملف داخل القاعدة مباشرة
    checksum = Column(String, nullable=True)
    uploaded_by = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (Index("evidence_audit_idx", "audit_id"),)


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=False)
    answer_id = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    owner_email = Column(String, nullable=False)
    due_at = Column(DateTime, nullable=False)
    priority = Column(String, nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String, nullable=False, default="open")
    # open, in_progress, pending_review, closed, rejected
    response_note = Column(Text, nullable=True)
    responded_by = Column(String, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    closed_by = Column(String, nullable=True)
    overdue_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)

    audit = relationship("Audit")

    __table_args__ = (
        Index("actions_audit_idx", "audit_id"),
        Index("actions_owner_idx", "owner_email"),
        Index("actions_status_idx", "status"),
    )


class ReportChangeRequest(Base):
    __tablename__ = "report_change_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(Integer, ForeignKey("audits.id"), nullable=False)
    requested_by = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    proposed_changes = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected, applied
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (Index("change_requests_status_idx", "status"),)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    link = Column(String, nullable=True)
    dedupe_key = Column(String, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (
        Index("notifications_user_read_idx", "user_id", "read_at"),
        UniqueConstraint("dedupe_key", name="notifications_dedupe_key_uq"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_email = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (
        Index("audit_log_entity_idx", "entity_type", "entity_id"),
        Index("audit_log_actor_idx", "actor_email"),
    )


class SignupRequest(Base):
    """طلب إنشاء حساب جديد يقدّمه موظف من صفحة تسجيل الدخول — بانتظار موافقة الإدارة."""
    __tablename__ = "signup_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    employee_number = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (Index("signup_requests_status_idx", "status"),)


class PasswordResetRequest(Base):
    """طلب استعادة/تغيير كلمة مرور يقدّمه موظف نسي كلمة مروره — بانتظار موافقة الإدارة."""
    __tablename__ = "password_reset_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    new_password_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, approved, rejected
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=now)

    __table_args__ = (Index("password_reset_requests_status_idx", "status"),)
