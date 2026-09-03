"""
اختبارات آلية لمنطق المصادقة والصلاحيات: قفل الحساب بعد محاولات فاشلة،
قوة كلمة المرور، تغيير كلمة المرور الذاتي، وعزل صلاحيات الفروع.
تشتغل على قاعدة بيانات SQLite مؤقتة (بدون أي اتصال خارجي) لتصلح للتشغيل
الآلي عبر GitHub Actions بدون أي إعداد إضافي.
"""
import os
import tempfile
import unittest


class AuthTestsBase(unittest.TestCase):
    """قاعدة مشتركة: تنشئ قاعدة بيانات SQLite مؤقتة جديدة تمامًا لكل اختبار،
    لضمان عدم تأثير اختبار على آخر."""

    def setUp(self):
        self._tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp_db.close()
        os.environ["DATABASE_URL"] = f"sqlite:///{self._tmp_db.name}"

        # نستورد الوحدات هنا (بعد ضبط DATABASE_URL) لضمان قراءتها للإعداد الصحيح
        import importlib
        import database
        importlib.reload(database)
        self.database = database
        self.database.init_db()

        import models
        self.models = models
        import auth
        importlib.reload(auth)
        self.auth = auth
        import utils
        self.utils = utils

    def tearDown(self):
        try:
            os.unlink(self._tmp_db.name)
        except OSError:
            pass
        os.environ.pop("DATABASE_URL", None)

    def _create_user(self, email, password, role="owner", **kwargs):
        with self.database.get_session() as s:
            user = self.models.User(email=email, name=email.split("@")[0], role=role, **kwargs)
            s.add(user)
            s.flush()
            user_id = user.id
            s.add(self.models.Credential(user_id=user_id, password_hash=self.auth.hash_password(password)))
        return user_id


class LockoutTests(AuthTestsBase):
    def test_remaining_attempts_counts_down(self):
        self._create_user("owner@nxn.local", "Test1234!")
        for expected_remaining in [4, 3, 2, 1]:
            ok, msg = self.auth.login("owner@nxn.local", "WrongPass!")
            self.assertFalse(ok)
            self.assertIn(str(expected_remaining), msg)

    def test_account_locks_after_threshold(self):
        self._create_user("owner@nxn.local", "Test1234!")
        for _ in range(self.auth.LOCKOUT_THRESHOLD):
            self.auth.login("owner@nxn.local", "WrongPass!")
        ok, msg = self.auth.login("owner@nxn.local", "Test1234!")
        self.assertFalse(ok, "الحساب يفترض يكون مقفولًا حتى بكلمة مرور صحيحة")
        self.assertTrue("مقفل" in msg or "قفل" in msg)

    def test_correct_login_resets_failed_attempts(self):
        self._create_user("owner@nxn.local", "Test1234!")
        self.auth.login("owner@nxn.local", "WrongPass!")
        self.auth.login("owner@nxn.local", "WrongPass!")
        ok, _ = self.auth.login("owner@nxn.local", "Test1234!")
        self.assertTrue(ok)
        with self.database.get_session() as s:
            user = s.query(self.models.User).filter_by(email="owner@nxn.local").first()
            cred = s.query(self.models.Credential).filter_by(user_id=user.id).first()
            self.assertEqual(cred.failed_attempts, 0)


class PasswordStrengthTests(AuthTestsBase):
    def test_weak_passwords_score_low(self):
        for pw in ["123", "abcdefgh", "aaaa"]:
            score, _, _ = self.utils.password_strength(pw)
            self.assertLessEqual(score, 1, f"'{pw}' يفترض تُصنّف ضعيفة جدًا")

    def test_strong_passwords_score_high(self):
        score, _, _ = self.utils.password_strength("Abc123!@#xyz")
        self.assertGreaterEqual(score, 4)

    def test_change_own_password_requires_correct_current(self):
        user_id = self._create_user("owner@nxn.local", "Test1234!")
        ok, msg = self.auth.change_own_password(user_id, "WrongCurrent!", "New1234!")
        self.assertFalse(ok)
        self.assertEqual(msg, "current_password_incorrect")

    def test_change_own_password_succeeds_and_persists(self):
        user_id = self._create_user("owner@nxn.local", "Test1234!")
        ok, _ = self.auth.change_own_password(user_id, "Test1234!", "New1234!")
        self.assertTrue(ok)
        with self.database.get_session() as s:
            cred = s.query(self.models.Credential).filter_by(user_id=user_id).first()
            self.assertTrue(self.auth.verify_password("New1234!", cred.password_hash))
            self.assertFalse(self.auth.verify_password("Test1234!", cred.password_hash))


class BranchPermissionTests(AuthTestsBase):
    def test_owner_and_manager_can_manage_any_branch(self):
        for role in ("owner", "manager"):
            user = {"role": role, "managed_branch_ids": []}
            self.assertTrue(self.auth.can_manage_branch(user, branch_id=999))

    def test_branch_role_limited_to_own_branches(self):
        user = {"role": "branch", "managed_branch_ids": [1, 2]}
        self.assertTrue(self.auth.can_manage_branch(user, branch_id=1))
        self.assertTrue(self.auth.can_manage_branch(user, branch_id=2))
        self.assertFalse(self.auth.can_manage_branch(user, branch_id=3), "تسريب صلاحيات: فرع خارج النطاق!")

    def test_viewer_role_cannot_manage_any_branch(self):
        user = {"role": "viewer", "managed_branch_ids": []}
        self.assertFalse(self.auth.can_manage_branch(user, branch_id=1))


if __name__ == "__main__":
    unittest.main()
