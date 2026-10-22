"""SQLite 持久化：保存每轮答题记录并提供统计查询。

默认库在 ~/.qpquiz/history.db，可用 --db 或环境变量 QPQUIZ_DB 覆盖。
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import SessionResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, mode TEXT NOT NULL,
    total INTEGER NOT NULL, correct INTEGER NOT NULL, score INTEGER NOT NULL,
    duration REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL, category TEXT NOT NULL, difficulty INTEGER NOT NULL,
    choice INTEGER, correct INTEGER NOT NULL, elapsed REAL NOT NULL, points INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);
"""


def default_db_path() -> Path:
    return Path(os.environ.get("QPQUIZ_DB") or "~/.qpquiz/history.db").expanduser()


@dataclass
class Stats:
    """全局统计快照。"""

    sessions: int = 0
    answers: int = 0
    correct: int = 0
    score: int = 0
    best_score: int = 0
    last_played: str | None = None

    @property
    def accuracy(self) -> float:
        return self.correct / self.answers if self.answers else 0.0

    @property
    def average_score(self) -> float:
        return self.score / self.sessions if self.sessions else 0.0


class Store:
    """会话记录仓库，也可作为上下文管理器使用。"""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path).expanduser() if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def save(self, result: SessionResult) -> int:
        """保存一轮结果，返回新会话 id。"""
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO sessions (started_at, mode, total, correct, score, duration)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (result.started_at.isoformat(timespec="seconds"), result.mode, result.total,
                 result.correct_count, result.score, result.duration),
            )
            session_id = int(cursor.lastrowid)
            self._conn.executemany(
                "INSERT INTO answers (session_id, question_id, category, difficulty,"
                " choice, correct, elapsed, points) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [(session_id, item.question_id, item.category, item.difficulty, item.choice,
                  int(item.correct), item.elapsed, item.points) for item in result.answers],
            )
        result.session_id = session_id
        return session_id

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, started_at, mode, total, correct, score, duration"
            " FROM sessions ORDER BY id DESC LIMIT ?", (max(1, limit),)
        ).fetchall()
        return [dict(row) for row in rows]

    def all_sessions(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, started_at, mode, total, correct, score, duration"
            " FROM sessions ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> Stats:
        row = self._conn.execute(
            "SELECT COUNT(*) AS sessions, COALESCE(SUM(total), 0) AS total,"
            " COALESCE(SUM(correct), 0) AS correct, COALESCE(SUM(score), 0) AS score,"
            " COALESCE(MAX(score), 0) AS best, MAX(started_at) AS last FROM sessions"
        ).fetchone()
        return Stats(int(row["sessions"]), int(row["total"]), int(row["correct"]),
                     int(row["score"]), int(row["best"]), row["last"])

    def category_stats(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) AS total, COALESCE(SUM(correct), 0) AS correct"
            " FROM answers GROUP BY category ORDER BY total DESC, category ASC"
        ).fetchall()
        return [{"category": row["category"], "total": int(row["total"]),
                 "correct": int(row["correct"]),
                 "accuracy": row["correct"] / row["total"] if row["total"] else 0.0}
                for row in rows]

    def reset(self) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM answers")
            self._conn.execute("DELETE FROM sessions")
            try:
                self._conn.execute(
                    "DELETE FROM sqlite_sequence WHERE name IN ('sessions', 'answers')")
            except sqlite3.OperationalError:
                pass  # 从未插入过记录时 sqlite_sequence 可能不存在
