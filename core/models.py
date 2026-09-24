"""
models.py
---------
All shared data shapes used across Agent 1 and Agent 2.

Keeping all data models in one place means:
- Both agents speak the same language
- The A2A packet format is defined exactly once
- Easy to update without hunting across multiple files
"""

from typing import TypedDict, Literal, Optional
from dataclasses import dataclass, field


# ── Difficulty Levels ─────────────────────────────────────────────────────────

Level = Literal["easy", "medium", "hard"]

# ── Topic Status ──────────────────────────────────────────────────────────────

TopicStatus = Literal[
    "easy",            # Currently at easy level
    "medium",          # Currently at medium level
    "hard",            # Currently at hard level
    "pending_mastery", # Passed hard, waiting for mastery re-test
    "mastered",        # Confirmed mastered — topic closed
    "weak",            # Failed demotion 3 times — topic closed
]


# ── A Single MCQ Question ─────────────────────────────────────────────────────

@dataclass
class Question:
    """One multiple-choice question with 4 options."""
    question_id: str          # e.g. "math_rational_easy_1"
    subject: str              # e.g. "Mathematics"
    topic: str                # e.g. "Rational Numbers"
    level: Level              # "easy", "medium", or "hard"
    question_text: str        # The question asked to the student
    options: dict             # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: str       # "A", "B", "C", or "D"


# ── Per-Topic State tracked during the quiz ───────────────────────────────────

@dataclass
class TopicState:
    """Tracks everything about one topic during the quiz session."""
    topic: str
    subject: str
    status: TopicStatus = "easy"
    current_level: Level = "easy"
    consecutive_correct: int = 0   # Must reach 2 in a row to promote
    demotion_count: int = 0        # Lifetime counter — never resets on promotion
    questions_asked: int = 0
    correct_answers: int = 0


# ── Record of every question served during the session ───────────────────────

@dataclass
class QuestionRecord:
    """Stores what was asked and how the student answered."""
    question_id: str
    topic: str
    level: Level
    question_text: str
    student_answer: str       # "A", "B", "C", or "D"
    correct_answer: str
    is_correct: bool


# ── LangGraph Quiz State (passed between every node in the graph) ─────────────

class QuizState(TypedDict):
    """
    The full state of the quiz at any point in time.
    LangGraph passes this dict between every node.
    """
    student_name: str
    subject: str
    topic_states: dict[str, TopicState]      # topic name → TopicState
    question_pool: dict[str, list[Question]] # topic name → list of Questions
    question_history: list[QuestionRecord]
    current_topic: Optional[str]
    current_question: Optional[Question]
    quiz_complete: bool


# ── A2A Packet — what Agent 1 sends to Agent 2 ───────────────────────────────

@dataclass
class A2APacket:
    """
    The structured JSON packet Agent 1 (Quizmaster) sends to
    Agent 2 (Evaluator) after the quiz is complete.

    Agent 2 uses only this packet — it never sees the quiz session directly.
    """
    packet_id: str                          # Unique ID for this session
    timestamp: str                          # ISO format datetime
    student_name: str
    subject: str
    topic_states: dict[str, dict]           # Serialised TopicState per topic
    question_history: list[dict]            # Serialised QuestionRecord list
    weighted_scores: dict[str, int]         # topic → score (hard=3, med=2, easy=1)
    total_correct: int
    total_questions: int
    prerequisite_map: dict[str, list[str]]  # topic → list of prerequisite topics


# ── Prerequisite Map — used by Agent 2 for cascade analysis ──────────────────

# If a student is weak in a topic, Agent 2 also checks its prerequisites.
# Example: weak in "Linear Equations" → also flag "Rational Numbers"
PREREQUISITE_MAP: dict[str, list[str]] = {
    # Mathematics
    "Rational Numbers": [],
    "Linear Equations": ["Rational Numbers"],
    "Mensuration": ["Rational Numbers"],
    "Exponents & Powers": ["Rational Numbers"],
    "Data Handling": [],

    # Biology
    "Cell Structure": [],
    "Photosynthesis": ["Cell Structure"],
    "Microorganisms": [],
    "Reproduction": ["Cell Structure"],
    "Life Processes": ["Cell Structure", "Photosynthesis"],

    # Chemistry
    "States of Matter": [],
    "Atoms & Molecules": ["States of Matter"],
    "Acids & Bases": ["Atoms & Molecules"],
    "Metals & Non-metals": ["Atoms & Molecules"],
    "Chemical Reactions": ["Atoms & Molecules", "Acids & Bases"],
}

# ── Subjects and their topics ─────────────────────────────────────────────────

SUBJECTS: dict[str, list[str]] = {
    "Mathematics": [
        "Rational Numbers",
        "Linear Equations",
        "Mensuration",
        "Exponents & Powers",
        "Data Handling",
    ],
    "Biology": [
        "Cell Structure",
        "Photosynthesis",
        "Microorganisms",
        "Reproduction",
        "Life Processes",
    ],
    "Chemistry": [
        "States of Matter",
        "Atoms & Molecules",
        "Acids & Bases",
        "Metals & Non-metals",
        "Chemical Reactions",
    ],
}

# ── Scoring weights per level ─────────────────────────────────────────────────

LEVEL_SCORES: dict[Level, int] = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}
