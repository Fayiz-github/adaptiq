"""
memory.py
---------
Memory management for the quiz platform:
- Long-term: Save and fetch completed sessions from the database
- Episodic: Review historical trends, recurring weaknesses, and score improvements
"""

import json
import sqlite3
from core.database import (
    DB_PATH,
    save_session,
    get_student_history,
    get_session_by_id,
)


def _connect() -> sqlite3.Connection:
    """Connect to SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_past_weak_topics(student_name: str, subject: str) -> list[str]:
    """
    Find topics the student struggled with across past sessions.
    Returns a unique list of weak topic names.
    """
    conn = _connect()
    try:
        cursor = conn.execute("""
            SELECT weak_topics FROM quiz_sessions
            WHERE LOWER(student_name) = LOWER(?) AND LOWER(subject) = LOWER(?)
            ORDER BY created_at DESC
        """, (student_name, subject))

        seen = set()
        weak_topics = []
        for row in cursor.fetchall():
            for topic in json.loads(row["weak_topics"]):
                if topic not in seen:
                    seen.add(topic)
                    weak_topics.append(topic)
        return weak_topics
    finally:
        conn.close()


def get_latest_session(student_name: str, subject: str) -> dict | None:
    """Fetch the most recent session for this student and subject."""
    conn = _connect()
    try:
        cursor = conn.execute("""
            SELECT * FROM quiz_sessions
            WHERE LOWER(student_name) = LOWER(?) AND LOWER(subject) = LOWER(?)
            ORDER BY created_at DESC
            LIMIT 1
        """, (student_name, subject))

        row = cursor.fetchone()
        if not row:
            return None

        session = dict(row)
        session["mastered_topics"] = json.loads(session["mastered_topics"])
        session["weak_topics"] = json.loads(session["weak_topics"])
        return session
    finally:
        conn.close()


def get_improvement_summary(student_name: str, subject: str) -> dict:
    """
    Summarize student score progression over time.
    Returns attempt count, history of scores, and whether they are improving.
    """
    conn = _connect()
    try:
        cursor = conn.execute("""
            SELECT total_correct, total_questions, created_at
            FROM quiz_sessions
            WHERE LOWER(student_name) = LOWER(?) AND LOWER(subject) = LOWER(?)
            ORDER BY created_at ASC
        """, (student_name, subject))

        rows = cursor.fetchall()
        if not rows:
            return {
                "total_attempts": 0,
                "scores": [],
                "best_score": 0,
                "is_improving": False,
            }

        scores = [
            {
                "date": row["created_at"][:10],
                "correct": row["total_correct"],
                "total": row["total_questions"],
            }
            for row in rows
        ]

        return {
            "total_attempts": len(scores),
            "scores": scores,
            "best_score": max(s["correct"] for s in scores),
            "is_improving": (
                len(scores) >= 2 and scores[-1]["correct"] > scores[0]["correct"]
            ),
        }
    finally:
        conn.close()
