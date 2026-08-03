import sqlite3
import json
from datetime import datetime
from app.config import settings


def get_connection():
    conn = sqlite3.connect(settings.SQLITE_DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_message(session_id: str, role: str, content: str, sources: list[str] = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, role, content, sources, timestamp) VALUES (?, ?, ?, ?, ?)",
        (
            session_id,
            role,
            content,
            json.dumps(sources or []),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content, sources, timestamp FROM chat_history "
        "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    conn.close()

    return [
        {
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources"]) if row["sources"] else [],
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]


def format_history_for_prompt(session_id: str, max_turns: int = 5) -> str:
    """Return the last few turns as a plain text block for prompt context."""
    history = get_history(session_id, limit=max_turns * 2)
    lines = []
    for turn in history:
        prefix = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {turn['content']}")
    return "\n".join(lines)
