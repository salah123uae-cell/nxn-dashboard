"""Consistent, validated backup and restore for NXN system tables."""
import base64
import binascii
import hashlib
import json
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, func, text

from database import get_session
from models import (
    User, Credential, Branch, ChecklistVersion, AuditSection, AuditQuestion,
    Audit, AuditAnswer, EvidenceFile, CorrectiveAction, ReportChangeRequest,
    Notification, AuditLog,
)

BACKUP_FORMAT = "nxn-dashboard"
BACKUP_VERSION = 2
MAX_BACKUP_BYTES = 100 * 1024 * 1024

# Parent tables first for inserts; reverse this order for a full replacement.
EXPORT_ORDER = [
    ("users", User),
    ("credentials", Credential),
    ("branches", Branch),
    ("checklist_versions", ChecklistVersion),
    ("audit_sections", AuditSection),
    ("audit_questions", AuditQuestion),
    ("audits", Audit),
    ("audit_answers", AuditAnswer),
    ("evidence_files", EvidenceFile),
    ("corrective_actions", CorrectiveAction),
    ("report_change_requests", ReportChangeRequest),
    ("notifications", Notification),
    ("audit_log", AuditLog),
]


class BackupValidationError(ValueError):
    """Raised before database mutation when a backup is malformed or incompatible."""


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"__bytes_b64__": base64.b64encode(value).decode("ascii")}
    return value


def _canonical_tables(data: dict) -> bytes:
    tables = {name: data[name] for name, _ in EXPORT_ORDER}
    return json.dumps(tables, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _validate_payload(json_bytes: bytes) -> dict:
    if not isinstance(json_bytes, bytes):
        raise BackupValidationError("Backup must be uploaded as bytes")
    if not json_bytes or len(json_bytes) > MAX_BACKUP_BYTES:
        raise BackupValidationError("Backup is empty or exceeds the 100 MB limit")
    try:
        data = json.loads(json_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupValidationError("Backup is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or not isinstance(data.get("_meta"), dict):
        raise BackupValidationError("Backup metadata is missing")

    meta = data["_meta"]
    if meta.get("_format") != BACKUP_FORMAT or meta.get("_version") != BACKUP_VERSION:
        raise BackupValidationError("Backup format or version is not supported")

    for name, model in EXPORT_ORDER:
        rows = data.get(name)
        if not isinstance(rows, list):
            raise BackupValidationError(f"Missing or invalid table: {name}")
        if any(not isinstance(row, dict) for row in rows):
            raise BackupValidationError(f"Invalid row in table: {name}")
        expected_columns = {column.name for column in model.__table__.columns}
        if any(set(row) != expected_columns for row in rows):
            raise BackupValidationError(f"Schema mismatch in table: {name}")

    owners = [row for row in data["users"] if row.get("role") == "owner" and row.get("active") is True]
    credential_user_ids = {
        row.get("user_id") for row in data["credentials"] if row.get("password_hash")
    }
    if not owners or not any(owner.get("id") in credential_user_ids for owner in owners):
        raise BackupValidationError("Backup has no active owner with credentials")

    expected_checksum = meta.get("_sha256")
    actual_checksum = hashlib.sha256(_canonical_tables(data)).hexdigest()
    if not expected_checksum or expected_checksum != actual_checksum:
        raise BackupValidationError("Backup checksum does not match its contents")
    return data


def export_all_data() -> bytes:
    """Export all system tables from one consistent database snapshot."""
    data = {}
    with get_session() as session:
        if session.bind.dialect.name == "postgresql":
            session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
            session.execute(text("SET TRANSACTION READ ONLY"))
        for name, model in EXPORT_ORDER:
            columns = [column.name for column in model.__table__.columns]
            data[name] = [
                {column: _serialize_value(getattr(row, column)) for column in columns}
                for row in session.query(model).order_by(model.id).all()
            ]

    meta = {
        "_format": BACKUP_FORMAT,
        "_version": BACKUP_VERSION,
        "_exported_at": datetime.now(timezone.utc).isoformat(),
        "_sha256": hashlib.sha256(_canonical_tables(data)).hexdigest(),
    }
    return json.dumps({"_meta": meta, **data}, ensure_ascii=False, indent=2).encode("utf-8")


def _deserialize_row(model, row: dict) -> dict:
    column_types = {column.name: column.type for column in model.__table__.columns}
    clean_row = {}
    for key, value in row.items():
        if key not in column_types:
            raise BackupValidationError(f"Unknown column {key!r} in {model.__tablename__}")
        column_type = column_types[key]
        if isinstance(value, dict):
            if set(value) != {"__bytes_b64__"} or not isinstance(value["__bytes_b64__"], str):
                raise BackupValidationError(f"Invalid binary value in {model.__tablename__}.{key}")
            try:
                value = base64.b64decode(value["__bytes_b64__"], validate=True)
            except (binascii.Error, ValueError) as exc:
                raise BackupValidationError(f"Invalid base64 in {model.__tablename__}.{key}") from exc
        elif isinstance(value, str) and isinstance(column_type, DateTime):
            try:
                value = datetime.fromisoformat(value)
            except ValueError as exc:
                raise BackupValidationError(f"Invalid datetime in {model.__tablename__}.{key}") from exc
        elif isinstance(value, str) and isinstance(column_type, Date):
            try:
                value = date.fromisoformat(value)
            except ValueError as exc:
                raise BackupValidationError(f"Invalid date in {model.__tablename__}.{key}") from exc
        clean_row[key] = value
    return clean_row


def _reset_postgresql_sequences(session) -> None:
    if session.bind.dialect.name != "postgresql":
        return
    for _, model in EXPORT_ORDER:
        table_name = model.__tablename__
        sequence_name = session.execute(
            text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
            {"table_name": table_name},
        ).scalar_one_or_none()
        if not sequence_name:
            continue
        maximum_id = session.query(func.max(model.id)).scalar()
        session.execute(
            text("SELECT setval(to_regclass(:sequence_name), :value, :is_called)"),
            {
                "sequence_name": sequence_name,
                "value": maximum_id if maximum_id is not None else 1,
                "is_called": maximum_id is not None,
            },
        )


def import_all_data(json_bytes: bytes, *, replace_existing: bool = False) -> dict:
    """Restore a validated backup atomically.

    By default only an empty database is accepted. ``replace_existing=True`` performs
    a full replacement inside the same transaction and must only be exposed behind
    owner authorization and an explicit destructive confirmation.
    """
    data = _validate_payload(json_bytes)
    parsed_rows = {
        name: [_deserialize_row(model, row) for row in data[name]]
        for name, model in EXPORT_ORDER
    }
    counts = {name: len(rows) for name, rows in parsed_rows.items()}

    with get_session() as session:
        has_existing_data = any(session.query(model.id).first() is not None for _, model in EXPORT_ORDER)
        if has_existing_data and not replace_existing:
            raise BackupValidationError("Target database is not empty")
        if replace_existing:
            for _, model in reversed(EXPORT_ORDER):
                session.query(model).delete(synchronize_session=False)
            session.flush()

        for name, model in EXPORT_ORDER:
            session.add_all(model(**row) for row in parsed_rows[name])
            session.flush()
        _reset_postgresql_sequences(session)
    return counts
