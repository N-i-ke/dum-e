"""短期記憶: 会話履歴を SQLite に永続化する。"""

import sqlite3
from datetime import datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "memory.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
CREATE TABLE IF NOT EXISTS flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    reason TEXT NOT NULL,
    context TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Memory:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)

    def resume_or_create_session(self) -> int:
        """最新セッションを返す。存在しなければ新規作成する。"""
        row = self.conn.execute(
            "SELECT id FROM sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else self.new_session()

    def new_session(self) -> int:
        cur = self.conn.execute(
            "INSERT INTO sessions (started_at) VALUES (?)", (_now(),)
        )
        self.conn.commit()
        return cur.lastrowid

    def add(self, session_id: int, role: str, content: str) -> None:
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at)"
            " VALUES (?, ?, ?, ?)",
            (session_id, role, content, _now()),
        )
        self.conn.commit()

    def recent(self, session_id: int, limit: int = 20) -> list[dict]:
        """直近 limit 件のメッセージを時系列順で返す。"""
        rows = self.conn.execute(
            "SELECT role, content FROM ("
            "  SELECT id, role, content FROM messages"
            "  WHERE session_id = ? ORDER BY id DESC LIMIT ?"
            ") ORDER BY id",
            (session_id, limit),
        ).fetchall()
        return [{"role": role, "content": content} for role, content in rows]

    def add_flag(self, session_id: int, reason: str, context: str = "") -> None:
        """モデルや記憶の不足事例を記録する。Phase 2・3 導入の判断材料。"""
        self.conn.execute(
            "INSERT INTO flags (session_id, reason, context, created_at)"
            " VALUES (?, ?, ?, ?)",
            (session_id, reason, context, _now()),
        )
        self.conn.commit()

    def flags(self) -> list[tuple]:
        """記録済みの不足事例を (id, created_at, reason, context) で返す。"""
        return self.conn.execute(
            "SELECT id, created_at, reason, context FROM flags ORDER BY id"
        ).fetchall()

    def close(self) -> None:
        self.conn.close()
