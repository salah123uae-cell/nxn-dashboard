"""
اختبار "دخان" (smoke test) شامل: يتأكد إن كل صفحة بالنظام تُحمَّل بدون أي
استثناء (Exception)، لكل الأدوار الخمسة وكل لغة. هذا لا يتحقق من التصميم أو
المحتوى الدقيق، فقط إن الصفحة "ما تنهار" — أهم خط دفاع أول ضد أي كسر بالكود.
"""
import os
import tempfile
import unittest
import datetime as dt

from streamlit.testing.v1 import AppTest

PAGES = [
    "app_pages/1_Dashboard.py", "app_pages/2_Branches.py", "app_pages/3_Checklist.py",
    "app_pages/4_Audits.py", "app_pages/5_Corrective_Actions.py", "app_pages/6_Users.py",
    "app_pages/7_Reports.py", "app_pages/8_Audit_Log.py", "app_pages/9_AI_Assistant.py",
    "app_pages/10_Backup.py", "app_pages/11_Help.py", "app_pages/12_Automation.py",
]

ROLES = [
    ("owner@nxn.local", "owner", []),
    ("manager@nxn.local", "manager", []),
    ("auditor@nxn.local", "auditor", []),
    ("branch@nxn.local", "branch", [1]),
    ("viewer@nxn.local", "viewer", []),
]


class PageSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls._tmp_db.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{cls._tmp_db.name}"

        import importlib
        import database
        importlib.reload(database)
        cls.database = database
        cls.database.init_db()

        import models
        cls.models = models
        import auth
        cls.auth = auth

        with cls.database.get_session() as s:
            for email, role, mbi in ROLES:
                u = cls.models.User(email=email, name=role, role=role,
                                     managed_branch_ids=str(mbi).replace("'", '"'))
                s.add(u)
                s.flush()
                s.add(cls.models.Credential(user_id=u.id, password_hash=cls.auth.hash_password("Test1234!")))

            b1 = cls.models.Branch(code="BR-001", name_ar="فرع1", name_en="B1",
                                    region="R", city="C", status="active")
            s.add(b1)
            s.flush()
            audit = cls.models.Audit(reference="AUD-1", branch_id=b1.id,
                                      auditor_email="auditor@nxn.local", status="submitted",
                                      score=85.0, checklist_version="QV1")
            s.add(audit)
            s.flush()
            s.add(cls.models.CorrectiveAction(
                audit_id=audit.id, title="Fix 1", description="d", owner_email="auditor@nxn.local",
                due_at=dt.datetime.utcnow(), priority="high", status="open",
            ))
            s.add(cls.models.ChecklistVersion(code="QV1", name_ar="ن1", name_en="V1",
                                               status="active", created_by="owner@nxn.local"))

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls._tmp_db.name)
        except OSError:
            pass
        os.environ.pop("DATABASE_URL", None)

    def _assert_page_loads(self, page: str, lang: str, email: str, role: str, mbi: list):
        at = AppTest.from_file("app.py", default_timeout=25)
        at.session_state["lang"] = lang
        at.session_state["user"] = {
            "id": 1, "email": email, "name": role, "role": role, "managed_branch_ids": mbi,
        }
        at.switch_page(page)
        at.run(timeout=25)
        # ملاحظة: at.exception يرجّع دائمًا ElementList (حتى لو فارغة)، أبدًا None
        # فعليًا — لازم نتحقق من الطول/القيمة المنطقية، لا نقارن بـ None مباشرة.
        self.assertFalse(
            bool(at.exception),
            f"صفحة {page} انهارت لدور {role} بلغة {lang}: "
            f"{at.exception[0].value if at.exception else ''}",
        )


def _make_test(page, lang, email, role, mbi):
    def test(self):
        self._assert_page_loads(page, lang, email, role, mbi)
    return test


# نولّد اختبارًا منفصلًا لكل تركيبة (صفحة × لغة × دور) ديناميكيًا، بحيث تظهر
# نتيجة كل تركيبة بشكل مستقل وواضح بتقرير الاختبار بدل اختبار واحد ضخم.
for _page in PAGES:
    for _lang in ["ar", "en"]:
        for _email, _role, _mbi in ROLES:
            _test_name = f"test_{_page.split('/')[-1].replace('.py', '')}_{_lang}_{_role}"
            setattr(PageSmokeTests, _test_name, _make_test(_page, _lang, _email, _role, _mbi))


if __name__ == "__main__":
    unittest.main()
