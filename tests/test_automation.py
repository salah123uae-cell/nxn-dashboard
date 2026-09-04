import importlib
import json
import os
import tempfile
import unittest
import sqlite3
from datetime import datetime, timedelta


class AutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.tmp.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{cls.tmp.name}"
        os.environ["OVERDUE_AUTOMATION_ENABLED"] = "true"
        import database, models, notifications, automation
        importlib.reload(database)
        importlib.reload(notifications)
        importlib.reload(automation)
        cls.db, cls.m, cls.automation = database, models, automation
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        cls.db.engine.dispose()
        os.unlink(cls.tmp.name)
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("OVERDUE_AUTOMATION_ENABLED", None)

    def setUp(self):
        with self.db.get_session() as s:
            for table in reversed(self.m.Base.metadata.sorted_tables):
                s.execute(table.delete())
            owner = self.m.User(email="owner@nxn.local", name="Owner", role="owner", active=True)
            manager = self.m.User(email="manager@nxn.local", name="Manager", role="branch",
                                  active=True, managed_branch_ids="[]")
            old_manager = self.m.User(email="old@nxn.local", name="Old", role="branch", active=False)
            s.add_all([owner, manager, old_manager])
            s.flush()
            branch = self.m.Branch(code="B1", name_ar="فرع", name_en="Branch", region="R",
                                   manager_email=manager.email)
            s.add(branch)
            s.flush()
            manager.managed_branch_ids = json.dumps([branch.id])
            audit = self.m.Audit(reference="A1", branch_id=branch.id,
                                 auditor_email="auditor@nxn.local", status="submitted")
            s.add(audit)
            s.flush()
            s.add(self.m.CorrectiveAction(
                audit_id=audit.id, title="Late", description="Fix", owner_email=old_manager.email,
                due_at=datetime.utcnow() - timedelta(days=1), status="open",
            ))

    def test_routes_to_current_active_manager_and_owner_once(self):
        self.assertEqual(self.automation.check_overdue_corrective_actions(), 1)
        self.assertEqual(self.automation.check_overdue_corrective_actions(), 0)
        with self.db.get_session() as s:
            rows = s.query(self.m.Notification).all()
            emails = {s.get(self.m.User, row.user_id).email for row in rows}
            self.assertEqual(emails, {"owner@nxn.local", "manager@nxn.local"})
            self.assertEqual(len(rows), 2)

    def test_preview_does_not_write(self):
        preview = self.automation.preview_overdue_corrective_actions()
        self.assertEqual(preview, {"actions": 1, "recipients": 2})
        with self.db.get_session() as s:
            self.assertEqual(s.query(self.m.Notification).count(), 0)
            self.assertIsNone(s.query(self.m.CorrectiveAction).one().overdue_notified_at)

    def test_disabled_guard_does_not_write(self):
        os.environ["OVERDUE_AUTOMATION_ENABLED"] = "false"
        try:
            self.assertEqual(self.automation.check_overdue_corrective_actions(), 0)
        finally:
            os.environ["OVERDUE_AUTOMATION_ENABLED"] = "true"
        with self.db.get_session() as s:
            self.assertEqual(s.query(self.m.Notification).count(), 0)


if __name__ == "__main__":
    unittest.main()


class LegacyMigrationTests(unittest.TestCase):
    def test_existing_rows_survive_column_migration(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        conn = sqlite3.connect(tmp.name)
        conn.executescript("""
            CREATE TABLE users (id INTEGER PRIMARY KEY, email VARCHAR, name VARCHAR, role VARCHAR, active BOOLEAN);
            INSERT INTO users VALUES (1, 'owner@nxn.local', 'Owner', 'owner', 1);
            CREATE TABLE corrective_actions (id INTEGER PRIMARY KEY);
            INSERT INTO corrective_actions VALUES (10);
            CREATE TABLE notifications (id INTEGER PRIMARY KEY);
            INSERT INTO notifications VALUES (20);
        """)
        conn.close()
        old_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp.name}"
        try:
            import database
            importlib.reload(database)
            database.init_db()
            with database.engine.connect() as db_conn:
                from sqlalchemy import inspect, text
                inspector = inspect(database.engine)
                self.assertIn("overdue_notified_at", {c["name"] for c in inspector.get_columns("corrective_actions")})
                self.assertIn("dedupe_key", {c["name"] for c in inspector.get_columns("notifications")})
                self.assertEqual(db_conn.execute(text("SELECT COUNT(*) FROM users")).scalar(), 1)
                self.assertEqual(db_conn.execute(text("SELECT COUNT(*) FROM corrective_actions")).scalar(), 1)
                self.assertEqual(db_conn.execute(text("SELECT COUNT(*) FROM notifications")).scalar(), 1)
            database.engine.dispose()
        finally:
            if old_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old_url
            os.unlink(tmp.name)
