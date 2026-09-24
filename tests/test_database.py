"""
test_database.py
----------------
Tests for the database module — covers both basic session operations
and the three episodic memory query functions.

No API calls — uses a temporary test database that is deleted after the tests.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import core.database as db
import core.memory as mem

# ── Use a temporary test database ─────────────────────────────────────────────

TEST_DB = "test_temp.db"


@pytest.fixture(autouse=True)
def temp_database(monkeypatch):
    """
    Before each test: point the database module at a fresh temp file.
    After each test: delete it so tests never share state.
    """
    monkeypatch.setattr(db, "DB_PATH", TEST_DB)
    monkeypatch.setattr(mem, "DB_PATH", TEST_DB)
    db.create_tables()
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


# ── Helper: insert a fake session ─────────────────────────────────────────────

def insert_session(
    packet_id="pkt-1",
    student_name="Arjun",
    subject="Mathematics",
    total_correct=7,
    total_questions=15,
    mastered_topics=None,
    weak_topics=None,
    report_card="Test report",
):
    db.save_session(
        packet_id=packet_id,
        student_name=student_name,
        subject=subject,
        total_correct=total_correct,
        total_questions=total_questions,
        mastered_topics=mastered_topics or ["Rational Numbers"],
        weak_topics=weak_topics or ["Exponents & Powers"],
        report_card=report_card,
    )


# ── Test 1: Save and retrieve a session ──────────────────────────────────────

def test_save_and_retrieve_session():
    insert_session()
    history = db.get_student_history("Arjun")
    assert len(history) == 1
    assert history[0]["student_name"] == "Arjun"
    assert history[0]["total_correct"] == 7
    assert "Rational Numbers" in history[0]["mastered_topics"]
    assert "Exponents & Powers" in history[0]["weak_topics"]


# ── Test 2: get_session_by_id ─────────────────────────────────────────────────

def test_get_session_by_id():
    insert_session(packet_id="unique-123")
    session = db.get_session_by_id("unique-123")
    assert session is not None
    assert session["packet_id"] == "unique-123"


def test_get_session_by_id_not_found():
    result = db.get_session_by_id("does-not-exist")
    assert result is None


# ── Test 3: Episodic — get_past_weak_topics ───────────────────────────────────

def test_get_past_weak_topics_returns_all_unique_weak():
    insert_session(packet_id="p1", weak_topics=["Exponents & Powers", "Mensuration"])
    insert_session(packet_id="p2", weak_topics=["Exponents & Powers", "Data Handling"])

    weak = mem.get_past_weak_topics("Arjun", "Mathematics")

    # All 3 unique weak topics should appear (no duplicates)
    assert "Exponents & Powers" in weak
    assert "Mensuration" in weak
    assert "Data Handling" in weak
    assert len(weak) == 3, "Should deduplicate — Exponents & Powers appeared twice"


def test_get_past_weak_topics_empty_for_new_student():
    weak = mem.get_past_weak_topics("NewStudent", "Mathematics")
    assert weak == []


# ── Test 4: Episodic — get_latest_session ────────────────────────────────────

def test_get_latest_session_returns_most_recent():
    insert_session(packet_id="old", total_correct=5)
    insert_session(packet_id="new", total_correct=11)

    latest = mem.get_latest_session("Arjun", "Mathematics")
    assert latest is not None
    # The most recently inserted session should be returned
    assert latest["total_correct"] == 11


def test_get_latest_session_none_for_new_student():
    result = mem.get_latest_session("Ghost", "Mathematics")
    assert result is None


# ── Test 5: Episodic — get_improvement_summary ───────────────────────────────

def test_improvement_summary_shows_upward_trend():
    insert_session(packet_id="s1", total_correct=5)
    insert_session(packet_id="s2", total_correct=9)
    insert_session(packet_id="s3", total_correct=13)

    summary = mem.get_improvement_summary("Arjun", "Mathematics")

    assert summary["total_attempts"] == 3
    assert summary["best_score"] == 13
    assert summary["is_improving"] is True
    assert len(summary["scores"]) == 3


def test_improvement_summary_empty_for_new_student():
    summary = mem.get_improvement_summary("Ghost", "Mathematics")
    assert summary["total_attempts"] == 0
    assert summary["is_improving"] is False
    assert summary["scores"] == []


def test_improvement_summary_not_improving():
    insert_session(packet_id="s1", total_correct=10)
    insert_session(packet_id="s2", total_correct=6)

    summary = mem.get_improvement_summary("Arjun", "Mathematics")
    assert summary["is_improving"] is False
    assert summary["best_score"] == 10
