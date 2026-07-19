import sqlite3
import tempfile
import unittest
from pathlib import Path

from dum_e.memory import Memory


class MemoryTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.memory = Memory(Path(self.tmpdir.name) / "test.db")

    def tearDown(self):
        self.memory.close()
        self.tmpdir.cleanup()

    def test_resume_creates_first_session(self):
        session_id = self.memory.resume_or_create_session()
        self.assertEqual(session_id, 1)

    def test_resume_returns_latest_session(self):
        self.memory.new_session()
        latest = self.memory.new_session()
        self.assertEqual(self.memory.resume_or_create_session(), latest)

    def test_add_and_recent_preserve_order(self):
        sid = self.memory.new_session()
        self.memory.add(sid, "user", "こんにちは")
        self.memory.add(sid, "assistant", "ご用件をどうぞ")
        self.assertEqual(
            self.memory.recent(sid),
            [
                {"role": "user", "content": "こんにちは"},
                {"role": "assistant", "content": "ご用件をどうぞ"},
            ],
        )

    def test_recent_limits_to_latest_messages(self):
        sid = self.memory.new_session()
        for i in range(30):
            self.memory.add(sid, "user", f"msg{i}")
        recent = self.memory.recent(sid, limit=20)
        self.assertEqual(len(recent), 20)
        self.assertEqual(recent[0]["content"], "msg10")
        self.assertEqual(recent[-1]["content"], "msg29")

    def test_sessions_are_isolated(self):
        sid1 = self.memory.new_session()
        sid2 = self.memory.new_session()
        self.memory.add(sid1, "user", "セッション1の発言")
        self.assertEqual(self.memory.recent(sid2), [])

    def test_rejects_unknown_role(self):
        sid = self.memory.new_session()
        with self.assertRaises(sqlite3.IntegrityError):
            self.memory.add(sid, "system", "不正なロール")


if __name__ == "__main__":
    unittest.main()
