import json
import unittest
from datetime import datetime

import backup


class BackupValidationTests(unittest.TestCase):
    def valid_payload(self):
        tables = {
            name: [
                {
                    column.name: (
                        1 if column.name in {"id", "user_id"}
                        else "owner" if column.name == "role"
                        else True if column.name == "active"
                        else "$2b$12$test" if column.name == "password_hash"
                        else None
                    )
                    for column in model.__table__.columns
                }
            ] if name in {"users", "credentials"} else []
            for name, model in backup.EXPORT_ORDER
        }
        meta = {
            "_format": backup.BACKUP_FORMAT,
            "_version": backup.BACKUP_VERSION,
            "_exported_at": datetime.utcnow().isoformat(),
            "_sha256": backup.hashlib.sha256(backup._canonical_tables(tables)).hexdigest(),
        }
        return json.dumps({"_meta": meta, **tables}).encode()

    def test_valid_payload_is_accepted(self):
        parsed = backup._validate_payload(self.valid_payload())
        self.assertEqual(parsed["_meta"]["_format"], backup.BACKUP_FORMAT)

    def test_tampered_payload_is_rejected(self):
        payload = json.loads(self.valid_payload())
        payload["users"][0]["name"] = "tampered"
        with self.assertRaises(backup.BackupValidationError):
            backup._validate_payload(json.dumps(payload).encode())

    def test_missing_table_is_rejected(self):
        payload = json.loads(self.valid_payload())
        del payload["audit_log"]
        with self.assertRaises(backup.BackupValidationError):
            backup._validate_payload(json.dumps(payload).encode())

    def test_invalid_base64_is_rejected(self):
        with self.assertRaises(backup.BackupValidationError):
            backup._deserialize_row(backup.EvidenceFile, {"file_data": {"__bytes_b64__": "%%%"}})

    def test_schema_mismatch_is_rejected(self):
        payload = json.loads(self.valid_payload())
        del payload["users"][0]["email"]
        tables = {name: payload[name] for name, _ in backup.EXPORT_ORDER}
        payload["_meta"]["_sha256"] = backup.hashlib.sha256(backup._canonical_tables(tables)).hexdigest()
        with self.assertRaises(backup.BackupValidationError):
            backup._validate_payload(json.dumps(payload).encode())


if __name__ == "__main__":
    unittest.main()
