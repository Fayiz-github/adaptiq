"""
quiz_engine.py
--------------
The adaptive quiz engine built with LangGraph.

The quiz is modelled as a state machine where every step is a node
and every decision (promote/demote/stay/master/weak) is an edge.

Flow:
  start → pick_question → ask_question → check_answer → route_answer
                                                              |
                          ┌───────────────┬─────────────────┼──────────────┐
                          ↓               ↓                 ↓              ↓
                      PROMOTE          DEMOTE             STAY           MASTER/WEAK
                          └───────────────┴─────────────────┴──────────────┘
                                                              |
                                                       (next topic or end)
"""

import random
from typing import Optional
from langgraph.graph import StateGraph, END

from core.models import (
    QuizState,
    TopicState,
    Question,
    QuestionRecord,
    TopicStatus,
    Level,
    SUBJECTS,
)


# ── Helper: get the next level up or down ────────────────────────────────────

LEVEL_ORDER: list[Level] = ["easy", "medium", "hard"]


def _level_up(current: Level) -> Optional[Level]:
    """Returns the next harder level, or None if already at hard."""
    index = LEVEL_ORDER.index(current)
    if index < len(LEVEL_ORDER) - 1:
        return LEVEL_ORDER[index + 1]
    return None


def _level_down(current: Level) -> Optional[Level]:
    """Returns the next easier level, or None if already at easy."""
    index = LEVEL_ORDER.index(current)
    if index > 0:
        return LEVEL_ORDER[index - 1]
    return None


# ── Helper: pick next unanswered question from the pool ──────────────────────

def _pick_question(
    pool: dict[str, list[Question]],
    topic: str,
    level: Level,
    already_asked: list[str],
) -> Optional[Question]:
    """
    Returns an unused question for the given topic and level.
    Returns None if the pool is exhausted for that topic+level.
    """
    candidates = [
        q for q in pool.get(topic, [])
        if q.level == level and q.question_id not in already_asked
    ]
    return random.choice(candidates) if candidates else None


# ── Helper: find the next active topic ───────────────────────────────────────

def _find_next_active_topic(state: QuizState) -> Optional[str]:
    """
    Returns the name of the next topic that is not yet closed
    (not mastered or weak). Returns None if all topics are closed.
    """
    for topic, ts in state["topic_states"].items():
        if ts.status not in ("mastered", "weak"):
            return topic
    return None


# ── Node 1: Start the quiz ────────────────────────────────────────────────────

def start_quiz(state: QuizState) -> QuizState:
    """
    Initialises topic states for all topics in the selected subject.
    Every topic starts at the easy level.
    """
    topics = SUBJECTS[state["subject"]]
    topic_states = {
        topic: TopicState(topic=topic, subject=state["subject"])
        for topic in topics
    }
    return {
        **state,
        "topic_states": topic_states,
        "question_history": [],
        "quiz_complete": False,
        "current_topic": topics[0],
        "current_question": None,
    }


# ── Node 2: Select the next question ─────────────────────────────────────────

def select_question(state: QuizState) -> QuizState:
    """
    Picks the next question for the current topic at its current level.
    If no questions are left in the pool, closes the topic as mastered.
    """
    topic_name = state["current_topic"]
    if topic_name is None:
        return {**state, "quiz_complete": True}

    topic_state = state["topic_states"][topic_name]
    already_asked = [r.question_id for r in state["question_history"]]

    question = _pick_question(
        state["question_pool"],
        topic_name,
        topic_state.current_level,
        already_asked,
    )

    if question is None:
        # Pool exhausted for this topic — treat as mastered
        topic_state.status = "mastered"
        next_topic = _find_next_active_topic(state)
        return {
            **state,
            "current_topic": next_topic,
            "current_question": None,
        }

    return {**state, "current_question": question}


# ── Node 3: Check the student's answer ───────────────────────────────────────

def check_answer(state: QuizState, student_answer: str) -> QuizState:
    """
    Records whether the student's answer was correct.
    Adds the result to question_history.
    """
    question = state["current_question"]
    is_correct = student_answer.upper() == question.correct_answer

    record = QuestionRecord(
        question_id=question.question_id,
        topic=question.topic,
        level=question.level,
        question_text=question.question_text,
        student_answer=student_answer.upper(),
        correct_answer=question.correct_answer,
        is_correct=is_correct,
    )

    return {
        **state,
        "question_history": state["question_history"] + [record],
        "_last_answer_correct": is_correct,  # used by the router
    }


# ── Node 4: Route to next action based on the answer ─────────────────────────

def route_answer(state: QuizState) -> QuizState:
    """
    The heart of the adaptive engine.

    Evaluates the student's answer and applies one of 5 conditions:

    Condition 1: Correct + Hard + PENDING_MASTERY  →  MASTER (topic closed)
    Condition 2a: Correct + Easy/Medium + 2 in a row  →  PROMOTE to next level
    Condition 2b: Correct + Easy/Medium + only 1 correct  →  STAY (need 2 in a row)
    Condition 3: Wrong + Easy  →  retry if demotion_count < 2, else WEAK
    Condition 4: Wrong + Medium/Hard + demotion_count < 2  →  DEMOTE one level
    Condition 5: Wrong + Medium/Hard + demotion_count >= 2  →  WEAK (topic closed)
    """
    topic_name = state["current_topic"]
    topic_state: TopicState = state["topic_states"][topic_name]
    is_correct: bool = state.get("_last_answer_correct", False)

    # ── CORRECT answer ─────────────────────────────────────────────────────
    if is_correct:
        topic_state.correct_answers += 1
        topic_state.consecutive_correct += 1

        # Condition 1: Mastery confirmation
        if topic_state.status == "pending_mastery" and topic_state.current_level == "hard":
            topic_state.status = "mastered"
            next_topic = _find_next_active_topic(state)
            return {**state, "current_topic": next_topic}

        # Condition 2a: Promote (2 consecutive correct)
        if topic_state.consecutive_correct >= 2:
            next_level = _level_up(topic_state.current_level)
            if next_level:
                topic_state.current_level = next_level
                topic_state.consecutive_correct = 0
                # If promoted to hard, mark as pending mastery
                if next_level == "hard":
                    topic_state.status = "pending_mastery"
                else:
                    topic_state.status = next_level
            else:
                # Already at hard — mark pending mastery
                topic_state.status = "pending_mastery"
            return {**state}

        # Condition 2b: Stay (only 1 correct so far, need 2 in a row)
        return {**state}

    # ── WRONG answer ───────────────────────────────────────────────────────
    else:
        topic_state.consecutive_correct = 0  # reset streak

        # Condition 3: Wrong at Easy level
        if topic_state.current_level == "easy":
            if topic_state.demotion_count >= 2:
                # Condition 5 equivalent at easy: 3rd failure → WEAK
                topic_state.status = "weak"
                next_topic = _find_next_active_topic(state)
                return {**state, "current_topic": next_topic}
            else:
                # Stay at easy, increment lifetime demotion counter
                topic_state.demotion_count += 1
                return {**state}

        # Condition 4: Wrong above Easy — demote if allowed
        if topic_state.demotion_count < 2:
            lower_level = _level_down(topic_state.current_level)
            topic_state.current_level = lower_level
            topic_state.status = lower_level
            topic_state.demotion_count += 1
            return {**state}

        # Condition 5: demotion_count >= 2 — WEAK POINT, close topic
        topic_state.status = "weak"
        next_topic = _find_next_active_topic(state)
        return {**state, "current_topic": next_topic}


# ── Node 5: Check if quiz is finished ────────────────────────────────────────

def check_completion(state: QuizState) -> QuizState:
    """
    Checks whether all topics have been closed (mastered or weak).
    If so, marks the quiz as complete.
    """
    all_closed = all(
        ts.status in ("mastered", "weak")
        for ts in state["topic_states"].values()
    )
    return {**state, "quiz_complete": all_closed}


# ── Router: decide the next node after routing ───────────────────────────────

def should_continue(state: QuizState) -> str:
    """
    Conditional edge function used by LangGraph.
    Returns "end" if the quiz is complete, "select_question" otherwise.
    """
    if state.get("quiz_complete") or state.get("current_topic") is None:
        return "end"
    return "select_question"


# ── Build the LangGraph state machine ────────────────────────────────────────

def build_quiz_graph() -> StateGraph:
    """
    Assembles and compiles the quiz state machine.

    Nodes:
      start_quiz       → initialises topic states
      select_question  → picks the next question from the pool
      check_completion → decides whether to end or continue

    The check_answer and route_answer nodes are called manually
    by QuizmasterAgent because they need external input (the student's answer).
    """
    graph = StateGraph(QuizState)

    graph.add_node("start_quiz", start_quiz)
    graph.add_node("select_question", select_question)
    graph.add_node("check_completion", check_completion)

    graph.set_entry_point("start_quiz")
    graph.add_edge("start_quiz", "select_question")
    graph.add_edge("select_question", "check_completion")

    graph.add_conditional_edges(
        "check_completion",
        should_continue,
        {
            "select_question": "select_question",
            "end": END,
        },
    )

    return graph.compile()
