"""Shared business assertions against buggy/fixed implementations; real SQLite."""
import importlib
import os
import sqlite3
import unittest

name = os.environ.get("ARCHIVE_IMPL", "fixed")
if name not in ("buggy", "fixed"):
    raise ValueError("ARCHIVE_IMPL must be buggy or fixed")
implementation = importlib.import_module(name)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE archive (id INTEGER PRIMARY KEY, state TEXT NOT NULL);
            CREATE TABLE receipt (archive_id INTEGER PRIMARY KEY);
            INSERT INTO archive VALUES (1, 'DRAFT'), (2, 'DRAFT');
        """)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def state(self, archive_id):
        return self.db.execute("SELECT state FROM archive WHERE id=?", (archive_id,)).fetchone()[0]

    def test_success_commits_both(self):
        implementation.archive(self.db, 1)
        self.assertEqual("ARCHIVED", self.state(1))
        self.assertEqual([(1,)], self.db.execute("SELECT archive_id FROM receipt").fetchall())

    def test_interruption_rolls_back(self):
        with self.assertRaisesRegex(RuntimeError, "injected interruption"):
            implementation.archive(self.db, 1, inject_failure=True)
        # Unchanged business expectation: failure must not publish a partial archive.
        self.assertEqual("DRAFT", self.state(1))
        self.assertEqual([], self.db.execute("SELECT archive_id FROM receipt").fetchall())

    def test_unrelated_draft_unchanged(self):
        implementation.archive(self.db, 1)
        self.assertEqual("DRAFT", self.state(2))
        self.assertEqual([], self.db.execute("SELECT archive_id FROM receipt WHERE archive_id=2").fetchall())


if __name__ == "__main__":
    unittest.main()
