"""PostgreSQL-only schema and transaction check used by GitHub Actions."""
import importlib
import os
import unittest


@unittest.skipUnless(os.getenv("POSTGRES_TEST_URL"), "PostgreSQL service is not configured")
class PostgresIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = os.environ["POSTGRES_TEST_URL"]
        import database, models
        importlib.reload(database)
        cls.db, cls.models = database, models
        models.Base.metadata.drop_all(bind=database.engine)
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        cls.models.Base.metadata.drop_all(bind=cls.db.engine)
        cls.db.engine.dispose()

    def test_constraints_and_transaction_rollback(self):
        with self.db.get_session() as s:
            s.add(self.models.Branch(code="PG-1", name_ar="فرع", name_en="Branch",
                                     region="R", city="C", status="active"))
        with self.assertRaises(Exception):
            with self.db.get_session() as s:
                s.add(self.models.Branch(code="PG-1", name_ar="مكرر", name_en="Duplicate",
                                         region="R", city="C", status="active"))
        with self.db.get_session() as s:
            self.assertEqual(s.query(self.models.Branch).filter_by(code="PG-1").count(), 1)


if __name__ == "__main__":
    unittest.main()
