"""
database.py
-----------
SQLite persistence layer for quiz sessions, performance metrics, and evaluated report cards.

Design & Security Principles:
- Parameterized Queries: All queries use parameterized '?' placeholders to prevent SQL injection.
- Case-Insensitive Privacy Isolation: Uses LOWER(student_name) = LOWER(?) to guarantee student data segregation.
- Structured Serialization: Complex nested data (mastered and weak topic lists) are serialized to JSON strings.
"""

import sqlite3
import json
from datetime import datetime, timezone
from core.config import DB_PATH


# =============================================================================
# CONNECTION & SCHEMA MANAGEMENT
# =============================================================================

def _connect() -> sqlite3.Connection:
    """
    Establishes an active connection to the SQLite database with dictionary-like row access.

    Returns:
        sqlite3.Connection: Configured connection with sqlite3.Row row_factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables() -> None:
    """
    Initializes the database schema by creating the 'quiz_sessions' table if not present.
    """
    conn = _connect()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS quiz_sessions (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    packet_id       TEXT    NOT NULL UNIQUE,
                    student_name    TEXT    NOT NULL,
                    subject         TEXT    NOT NULL,
                    total_correct   INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    mastered_topics TEXT    NOT NULL,
                    weak_topics     TEXT    NOT NULL,
                    report_card     TEXT    NOT NULL,
                    created_at      TEXT    NOT NULL
                )
            """)
    finally:
        conn.close()


# =============================================================================
# RECORD PERSISTENCE & RETRIEVAL
# =============================================================================

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
    Persists a completed quiz session and final report card into SQLite.

    Args:
        packet_id (str): Unique UUID4 identifier for the quiz session.
        student_name (str): The student's display name.
        subject (str): The academic subject tested.
        total_correct (int): Count of correct answers.
        total_questions (int): Total questions attempted.
        mastered_topics (list[str]): Topics where the student cleared Hard level.
        weak_topics (list[str]): Topics still requiring reinforcement or review.
        report_card (str): The complete evaluated report card text.
    """
    conn = _connect()
    try:
        with conn:
            conn.execute("""
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
    finally:
        conn.close()


def _format_row(row: sqlite3.Row) -> dict:
    """
    Converts an SQLite row record into a clean dictionary with deserialized JSON lists.

    Args:
        row (sqlite3.Row): Raw database row.

    Returns:
        dict: Normalized session dictionary with parsed JSON collections.
    """
    data = dict(row)
    data["mastered_topics"] = json.loads(data["mastered_topics"])
    data["weak_topics"] = json.loads(data["weak_topics"])
    return data


def get_student_history(student_name: str) -> list[dict]:
    """
    Retrieves all past quiz attempts for a specific student, ordered newest first.

    Guarantees strict privacy: students only see their own sessions.

    Args:
        student_name (str): The student's name to filter by.

    Returns:
        list[dict]: Chronological list of past session records.
    """
    conn = _connect()
    try:
        cursor = conn.execute(
            "SELECT * FROM quiz_sessions WHERE LOWER(student_name) = LOWER(?) ORDER BY created_at DESC",
            (student_name,),
        )
        return [_format_row(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_session_by_id(packet_id: str) -> dict | None:
    """
    Retrieves a single quiz session record by its unique packet UUID.

    Args:
        packet_id (str): The unique packet UUID to query.

    Returns:
        dict | None: The session dictionary if found, or None if no match.
    """
    conn = _connect()
    try:
        cursor = conn.execute(
            "SELECT * FROM quiz_sessions WHERE packet_id = ?",
            (packet_id,),
        )
        row = cursor.fetchone()
        return _format_row(row) if row else None
    finally:
        conn.close()
