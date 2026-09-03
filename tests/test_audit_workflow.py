"""
اختبارات آلية لحساب نتيجة التدقيق وإنشاء الإجراءات التصحيحية التلقائية.
"""
import os
import tempfile
import unittest
import datetime as dt


class AuditWorkflowTests(unittest.TestCase):
    def setUp(self):
        self._tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp_db.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{self._tmp_db.name}"

        import importlib
        import database
        importlib.reload(database)
        self.database = database
        self.database.init_db()

        import models
        self.models = models
        import utils
        self.utils = utils

    def tearDown(self):
        try:
            os.unlink(self._tmp_db.name)
        except OSError:
            pass
        os.environ.pop("DATABASE_URL", None)

    def test_score_calculation_excludes_not_applicable(self):
        """السؤال not_applicable يجب أن يُستبعد كليًا من مجموع الوزن القابل للتطبيق."""
        with self.database.get_session() as s:
            q1 = self.models.AuditQuestion(section_id=1, code="Q1", question_ar="س1", question_en="Q1",
                                            weight=60, checklist_version="QV1", sort_order=1)
            q2 = self.models.AuditQuestion(section_id=1, code="Q2", question_ar="س2", question_en="Q2",
                                            weight=40, checklist_version="QV1", sort_order=2)
            q3 = self.models.AuditQuestion(section_id=1, code="Q3", question_ar="س3", question_en="Q3",
                                            weight=100, checklist_version="QV1", sort_order=3)
            s.add_all([q1, q2, q3])
            s.flush()
            qmap = {q1.id: q1, q2.id: q2, q3.id: q3}
            answers = [
                {"question_id": q1.id, "answer": "compliant"},
                {"question_id": q2.id, "answer": "non_compliant"},
                {"question_id": q3.id, "answer": "not_applicable"},
            ]
            # نحسب النتيجة ونحن لسا داخل الجلسة، لتفادي DetachedInstanceError
            # عند وصول calculate_audit_score لخاصية weight بعد إغلاق الجلسة.
            score = self.utils.calculate_audit_score(answers, qmap)
        # المتوقع: 60 / (60+40) * 100 = 60.0 (Q3 مستبعد تمامًا من المقام والبسط)
        self.assertEqual(score, 60.0)

    def test_score_is_zero_when_all_non_compliant(self):
        with self.database.get_session() as s:
            q1 = self.models.AuditQuestion(section_id=1, code="Q1", question_ar="س1", question_en="Q1",
                                            weight=100, checklist_version="QV1", sort_order=1)
            s.add(q1)
            s.flush()
            qmap = {q1.id: q1}
            answers = [{"question_id": q1.id, "answer": "non_compliant"}]
            score = self.utils.calculate_audit_score(answers, qmap)
        self.assertEqual(score, 0.0)

    def test_score_is_zero_when_no_applicable_questions(self):
        """لو كل الأسئلة not_applicable، المقام صفر — يجب ألا يحدث انقسام على صفر."""
        with self.database.get_session() as s:
            q1 = self.models.AuditQuestion(section_id=1, code="Q1", question_ar="س1", question_en="Q1",
                                            weight=100, checklist_version="QV1", sort_order=1)
            s.add(q1)
            s.flush()
            qmap = {q1.id: q1}
            answers = [{"question_id": q1.id, "answer": "not_applicable"}]
            score = self.utils.calculate_audit_score(answers, qmap)
        self.assertEqual(score, 0.0)

    def test_corrective_action_created_for_non_compliant_answer(self):
        """محاكاة تصغيرة لمنطق إنشاء إجراء تصحيحي تلقائي (نفس منطق 4_Audits.py)."""
        with self.database.get_session() as s:
            branch = self.models.Branch(code="BR-1", name_ar="ف1", name_en="B1",
                                         region="R", city="C", status="active")
            s.add(branch)
            s.flush()
            audit = self.models.Audit(reference="AUD-1", branch_id=branch.id,
                                       auditor_email="a@nxn.local", status="submitted",
                                       checklist_version="QV1")
            s.add(audit)
            s.flush()
            audit_id = audit.id
            q1 = self.models.AuditQuestion(section_id=1, code="Q1", question_ar="سؤال حرج", question_en="Critical",
                                            weight=100, checklist_version="QV1", sort_order=1)
            s.add(q1)
            s.flush()
            ans = self.models.AuditAnswer(audit_id=audit_id, question_id=q1.id,
                                           answer="non_compliant", answered_by="a@nxn.local",
                                           answered_at=dt.datetime.utcnow())
            s.add(ans)
            s.flush()
            if ans.answer == "non_compliant":
                s.add(self.models.CorrectiveAction(
                    audit_id=audit_id, answer_id=ans.id, title=f"معالجة: {q1.code}",
                    description=q1.question_ar, owner_email="a@nxn.local",
                    due_at=dt.datetime.utcnow(), priority="high", status="open",
                ))

        with self.database.get_session() as s:
            count = s.query(self.models.CorrectiveAction).filter_by(audit_id=audit_id).count()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
