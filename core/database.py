"""
database.py
-----------
Raw SQLite operations for the A2A Quiz Platform.

This file handles only the low-level database work:
- Connecting to the database
- Creating tables
- Saving and retrieving sessions

Higher-level memory operations (episodic queries, improvement tracking)
are in core/memory.py, which imports from here.
"""

import sqlite3
import json
from datetime import datetime, timezone
from core.config import DB_PATH


# ── Internal connection helper ─────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    """
    Opens and returns a connection to the SQLite database.
    Used internally by this module and by core/memory.py.
    """
    return sqlite3.connect(DB_PATH)


# ── Table creation ────────────────────────────────────────────────────────────

def create_tables() -> None:
    """
    Creates the database tables if they do not already exist.
    Called once at application startup.
    """
    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            packet_id       TEXT    NOT NULL UNIQUE,
            student_name    TEXT    NOT NULL,
            subject         TEXT    NOT NULL,
            total_correct   INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            mastered_topics TEXT    NOT NULL,  -- JSON list
            weak_topics     TEXT    NOT NULL,  -- JSON list
            report_card     TEXT    NOT NULL,  -- Full text of the report
            created_at      TEXT    NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# ── Save a completed session ──────────────────────────────────────────────────

def save_session(
    packet_id: str,
    student_name: str,
    subject: str,
    total_correct: int,
    total_questions: int,
    mastered_topics: list[str],
    weak_topics: list[str],
    report_card: str,
) -> None:
    """
    Saves the result of a completed quiz session to the database.
    Called by Agent 2 (Evaluator) after generating the report card.
    """
    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO quiz_sessions
            (packet_id, student_name, subject, total_correct, total_questions,
             mastered_topics, weak_topics, report_card, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        packet_id,
        student_name,
        subject,
        total_correct,
        total_questions,
        json.dumps(mastered_topics),
        json.dumps(weak_topics),
        report_card,
        datetime.now(timezone.utc).isoformat(),
    ))

    connection.commit()
    connection.close()


# ── Fetch all past sessions for a student ─────────────────────────────────────

def get_student_history(student_name: str) -> list[dict]:
    """
    Returns all past quiz sessions for a given student,
    ordered from most recent to oldest.
    """
    connection = _connect()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM quiz_sessions
        WHERE student_name = ?
        ORDER BY created_at DESC
    """, (student_name,))

    rows = cursor.fetchall()
    connection.close()

    results = []
    for row in rows:
        session = dict(row)
        session["mastered_topics"] = json.loads(session["mastered_topics"])
        session["weak_topics"] = json.loads(session["weak_topics"])
        results.append(session)

    return results


# ── Fetch a single session by packet ID ──────────────────────────────────────

def get_session_by_id(packet_id: str) -> dict | None:
    """
    Returns a single session by its unique packet ID.
    Returns None if not found.
    """
    connection = _connect()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM quiz_sessions WHERE packet_id = ?",
        (packet_id,)
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    session = dict(row)
    session["mastered_topics"] = json.loads(session["mastered_topics"])
    session["weak_topics"] = json.loads(session["weak_topics"])
    return session
