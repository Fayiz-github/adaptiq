"""
memory.py
---------
The unified memory interface for the A2A Quiz Platform.

This file is the single place that documents and exposes all
four memory types used by both agents:

┌─────────────────────────────────────────────────────────────────┐
│                    Memory Architecture                          │
├──────────────────┬──────────────────────────────────────────────┤
│  Memory Type     │  Description                                 │
├──────────────────┼──────────────────────────────────────────────┤
│  Working         │  Live quiz state (QuizState TypedDict).      │
│                  │  Exists only during an active quiz session.  │
│                  │  Managed by LangGraph in quiz_engine.py.     │
├──────────────────┼──────────────────────────────────────────────┤
│  In-context      │  The A2A packet passed to Gemini's prompt.   │
│                  │  Everything Agent 2 needs is in this packet. │
│                  │  Exists only during the Gemini API call.     │
├──────────────────┼──────────────────────────────────────────────┤
│  Long-term       │  Completed sessions saved to SQLite.         │
│                  │  Persists permanently across all sessions.   │
│                  │  → save_session() / get_student_history()    │
├──────────────────┼──────────────────────────────────────────────┤
│  Episodic        │  Past-session recall used by Agent 2.        │
│                  │  Lets the report card reference history:     │
│                  │  "Last time you were weak in Exponents too." │
│                  │  → get_past_weak_topics()                    │
│                  │  → get_latest_session()                      │
│                  │  → get_improvement_summary()                 │
└──────────────────┴──────────────────────────────────────────────┘
"""

import json
import sqlite3
from core.database import DB_PATH  # re-exported so tests can monkeypatch mem.DB_PATH


def _connect() -> sqlite3.Connection:
    """Opens a connection to whatever DB_PATH is set to (testable via monkeypatch)."""
    return sqlite3.connect(DB_PATH)


# ── Long-term Memory ──────────────────────────────────────────────────────────
# Exposes the save and retrieve functions from database.py
# so callers only need to import from memory.py

from core.database import (
    save_session,        # Saves a completed session permanently
    get_student_history, # Returns all past sessions for a student
    get_session_by_id,   # Returns a single session by its packet ID
)


# ── Episodic Memory: Recurring weak topics ────────────────────────────────────

def get_past_weak_topics(student_name: str, subject: str) -> list[str]:
    """
    Episodic memory — returns every topic the student has been
    weak in across ALL past sessions for a given subject.

    Used by Agent 2 to detect recurring weaknesses:
    "You were also weak in Exponents in your last 2 sessions.
     This is a pattern — it needs focused attention."

    Returns an empty list if this is the student's first session.

    Example return value:
        ["Exponents & Powers", "Data Handling"]
    """
    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT weak_topics FROM quiz_sessions
        WHERE student_name = ? AND subject = ?
        ORDER BY created_at DESC
    """, (student_name, subject))

    rows = cursor.fetchall()
    connection.close()

    # Collect unique weak topics across all past sessions
    seen: set[str] = set()
    all_weak: list[str] = []
    for row in rows:
        for topic in json.loads(row[0]):
            if topic not in seen:
                seen.add(topic)
                all_weak.append(topic)

    return all_weak


# ── Episodic Memory: Most recent session ─────────────────────────────────────

def get_latest_session(student_name: str, subject: str) -> dict | None:
    """
    Episodic memory — returns the student's most recent quiz session
    for a given subject.

    Returns None if the student has never attempted this subject before.

    Used by Agent 2 to compare the current session with the last:
    "Last time you scored 5/15. This time you scored 9/15 — great progress!"
    """
    connection = _connect()
    import sqlite3
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM quiz_sessions
        WHERE student_name = ? AND subject = ?
        ORDER BY created_at DESC
        LIMIT 1
    """, (student_name, subject))

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    session = dict(row)
    session["mastered_topics"] = json.loads(session["mastered_topics"])
    session["weak_topics"] = json.loads(session["weak_topics"])
    return session


# ── Episodic Memory: Score improvement over time ─────────────────────────────

def get_improvement_summary(student_name: str, subject: str) -> dict:
    """
    Episodic memory — returns a summary of the student's score trend
    across all past sessions for a given subject.

    Returns:
        total_attempts  — how many times they have taken this quiz
        scores          — list of {date, correct, total}, oldest first
        best_score      — highest correct answers ever achieved
        is_improving    — True if the last score > the first score

    Used by Agent 2 to write motivating, evidence-based feedback:
    "You have attempted Mathematics 3 times. Your scores were 5, 8,
     and 11 — a clear upward trend. Keep going!"

    Returns safe empty defaults for a first-time student.
    """
    connection = _connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT total_correct, total_questions, created_at
        FROM quiz_sessions
        WHERE student_name = ? AND subject = ?
        ORDER BY created_at ASC
    """, (student_name, subject))

    rows = cursor.fetchall()
    connection.close()

    if not rows:
        return {
            "total_attempts": 0,
            "scores": [],
            "best_score": 0,
            "is_improving": False,
        }

    scores = [
        {
            "date": row[2][:10],   # ISO date e.g. "2026-09-24"
            "correct": row[0],
            "total": row[1],
        }
        for row in rows
    ]

    return {
        "total_attempts": len(scores),
        "scores": scores,
        "best_score": max(s["correct"] for s in scores),
        "is_improving": (
            len(scores) >= 2 and
            scores[-1]["correct"] > scores[0]["correct"]
        ),
    }
