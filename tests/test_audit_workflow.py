"""Tests the real transactional audit and corrective-action workflow."""
import os
import tempfile
import unittest
from datetime import datetime, timedelta


class AuditWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{self.tmp.name}"
        import importlib, database, models, audit_workflow
        importlib.reload(database)
        importlib.reload(audit_workflow)
        self.db, self.m, self.workflow = database, models, audit_workflow
        self.db.init_db()
        with self.db.get_session() as s:
            section = self.m.AuditSection(code="S1", name_ar="قسم", name_en="Section", weight=100, sort_order=1)
            s.add(section); s.flush()
            s.add_all([
                self.m.AuditQuestion(section_id=section.id, code="Q1", question_ar="س1", question_en="Q1", weight=60, checklist_version="QV1", sort_order=1),
                self.m.AuditQuestion(section_id=section.id, code="Q2", question_ar="س2", question_en="Q2", weight=40, checklist_version="QV1", sort_order=2),
            ])
            branch = self.m.Branch(code="BR1", name_ar="فرع", name_en="Branch", region="R", city="C", status="active", manager_email="branch@nxn.local")
            s.add(branch); s.flush()
            audit = self.m.Audit(reference="AUD1", branch_id=branch.id, auditor_email="auditor@nxn.local", status="scheduled", checklist_version="QV1")
            s.add(audit); s.flush()
            self.audit_id = audit.id
            self.question_ids = [q.id for q in s.query(self.m.AuditQuestion).order_by(self.m.AuditQuestion.id)]

    def tearDown(self):
        self.db.engine.dispose()
        os.unlink(self.tmp.name)
        os.environ.pop("DATABASE_URL", None)

    def _answers(self, first="compliant", second="non_compliant"):
        return [{"question_id": self.question_ids[0], "answer": first},
                {"question_id": self.question_ids[1], "answer": second}]

    def test_submit_persists_score_and_assigns_action_to_branch_manager(self):
        with self.db.get_session() as s:
            score = self.workflow.submit_audit(s, self.audit_id, self._answers(), "auditor@nxn.local")
        self.assertEqual(score, 60.0)
        with self.db.get_session() as s:
            audit = s.get(self.m.Audit, self.audit_id)
            actions = s.query(self.m.CorrectiveAction).filter_by(audit_id=self.audit_id).all()
            self.assertEqual(audit.score, 60.0)
            self.assertEqual(len(actions), 1)
            self.assertEqual(actions[0].owner_email, "branch@nxn.local")
            remaining = actions[0].due_at - datetime.utcnow()
            self.assertGreater(remaining, timedelta(days=6, hours=23))
            self.assertLessEqual(remaining, timedelta(days=7))

    def test_not_applicable_is_excluded_and_all_compliant_is_100(self):
        with self.db.get_session() as s:
            score = self.workflow.submit_audit(s, self.audit_id, self._answers("compliant", "not_applicable"), "auditor@nxn.local")
        self.assertEqual(score, 100.0)

    def test_incomplete_duplicate_and_invalid_answers_are_rejected(self):
        cases = [
            [self._answers()[0]],
            [self._answers()[0], self._answers()[0]],
            [{"question_id": self.question_ids[0], "answer": "yes"}, self._answers()[1]],
        ]
        for answers in cases:
            with self.subTest(answers=answers), self.assertRaises(ValueError), self.db.get_session() as s:
                self.workflow.submit_audit(s, self.audit_id, answers, "auditor@nxn.local")

    def test_branch_response_requires_note_then_owner_can_approve(self):
        with self.db.get_session() as s:
            self.workflow.submit_audit(s, self.audit_id, self._answers(), "auditor@nxn.local")
            action_id = s.query(self.m.CorrectiveAction).filter_by(audit_id=self.audit_id).one().id
        with self.assertRaises(ValueError), self.db.get_session() as s:
            self.workflow.respond_to_corrective_action(s, action_id, " ", "branch@nxn.local")
        with self.db.get_session() as s:
            self.workflow.respond_to_corrective_action(s, action_id, "تم التصحيح وإرفاق الدليل", "branch@nxn.local")
        with self.db.get_session() as s:
            self.assertEqual(s.get(self.m.CorrectiveAction, action_id).status, "pending_review")
            self.workflow.review_corrective_action(s, action_id, True, "owner@nxn.local")
        with self.db.get_session() as s:
            action = s.get(self.m.CorrectiveAction, action_id)
            self.assertEqual(action.status, "closed")
            self.assertEqual(action.closed_by, "owner@nxn.local")


if __name__ == "__main__":
    unittest.main()
