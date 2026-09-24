"""
test_quiz_engine.py
-------------------
Unit tests for the adaptive quiz routing logic in quiz_engine.py.

Tests all 5 routing conditions plus the level helper functions.
No API calls are made — pure logic testing.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import TopicState, Question
from quizmaster.quiz_engine import _level_up, _level_down, route_answer


# ── Shared test fixtures ──────────────────────────────────────────────────────

def make_state(topic_state: TopicState, is_correct: bool) -> dict:
    """Builds a minimal quiz state for testing route_answer."""
    return {
        "student_name": "TestStudent",
        "subject": "Mathematics",
        "topic_states": {topic_state.topic: topic_state},
        "question_pool": {},
        "question_history": [],
        "current_topic": topic_state.topic,
        "current_question": Question(
            question_id="q-test",
            subject="Mathematics",
            topic=topic_state.topic,
            level=topic_state.current_level,
            question_text="Test question?",
            options={"A": "a", "B": "b", "C": "c", "D": "d"},
            correct_answer="A",
        ),
        "quiz_complete": False,
        "_last_answer_correct": is_correct,
    }


# ── Test 1: Level helpers ─────────────────────────────────────────────────────

def test_level_up():
    assert _level_up("easy") == "medium"
    assert _level_up("medium") == "hard"
    assert _level_up("hard") is None


def test_level_down():
    assert _level_down("hard") == "medium"
    assert _level_down("medium") == "easy"
    assert _level_down("easy") is None


# ── Test 2: Condition 2a — Promote after 2 correct in a row ──────────────────

def test_condition_2a_promote():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="easy", status="easy", consecutive_correct=1
    )
    result = route_answer(make_state(ts, is_correct=True))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.current_level == "medium", "Should promote to medium"
    assert updated.consecutive_correct == 0, "Streak should reset after promotion"


# ── Test 3: Condition 2b — Stay after only 1 correct ─────────────────────────

def test_condition_2b_stay():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="easy", status="easy", consecutive_correct=0
    )
    result = route_answer(make_state(ts, is_correct=True))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.current_level == "easy", "Should stay at easy"
    assert updated.consecutive_correct == 1, "Streak should increment to 1"


# ── Test 4: Condition 4 — Demote from medium on wrong ────────────────────────

def test_condition_4_demote():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="medium", status="medium",
        demotion_count=0, consecutive_correct=1
    )
    result = route_answer(make_state(ts, is_correct=False))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.current_level == "easy", "Should demote to easy"
    assert updated.demotion_count == 1, "Demotion count should increment"
    assert updated.consecutive_correct == 0, "Streak should reset"


# ── Test 5: Condition 5 — Weak after 2 demotions + wrong ─────────────────────

def test_condition_5_weak_above_easy():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="medium", status="medium", demotion_count=2
    )
    result = route_answer(make_state(ts, is_correct=False))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.status == "weak", "Should be marked weak"


# ── Test 6: Condition 1 — Master on correct at hard (pending_mastery) ────────

def test_condition_1_master():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="hard", status="pending_mastery", consecutive_correct=0
    )
    result = route_answer(make_state(ts, is_correct=True))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.status == "mastered", "Should be mastered"


# ── Test 7: Condition 3 — Weak at easy after 2 demotions ─────────────────────

def test_condition_3_weak_at_easy():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="easy", status="easy", demotion_count=2
    )
    result = route_answer(make_state(ts, is_correct=False))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.status == "weak", "Should be weak at easy level"


# ── Test 8: Demotion count increments at easy ────────────────────────────────

def test_demotion_count_increments_at_easy():
    ts = TopicState(
        topic="Rational Numbers", subject="Mathematics",
        current_level="easy", status="easy", demotion_count=0
    )
    result = route_answer(make_state(ts, is_correct=False))
    updated = result["topic_states"]["Rational Numbers"]
    assert updated.demotion_count == 1, "Demotion count should increment"
    assert updated.current_level == "easy", "Should stay at easy"


# ── Run all tests ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_level_up()
    test_level_down()
    test_condition_2a_promote()
    test_condition_2b_stay()
    test_condition_4_demote()
    test_condition_5_weak_above_easy()
    test_condition_1_master()
    test_condition_3_weak_at_easy()
    test_demotion_count_increments_at_easy()
    print("All quiz engine tests passed!")
