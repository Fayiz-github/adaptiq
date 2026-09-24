"""
question_generator.py
---------------------
Uses Groq (llama-3.3-70b) to generate the full question pool
for a quiz session in a single API call.

The pool contains 60 questions:
  - 5 topics × 3 levels (easy/medium/hard) × 4 questions each

All 60 questions are generated BEFORE the quiz starts.
No LLM calls happen during the quiz — questions are served from this pool.
"""

import json
import uuid
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import GROQ_API_KEY, GROQ_MODEL
from core.models import Question, Level, SUBJECTS


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client() -> ChatGroq:
    """Creates and returns a Groq LLM client."""
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.7,
    )


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Class 8 exam question writer.
Your job is to generate multiple-choice questions (MCQs) for Class 8 students.

Rules:
- Each question must have exactly 4 options: A, B, C, D
- Only ONE option must be correct
- Easy questions test basic recall
- Medium questions test understanding and application
- Hard questions test analysis and problem-solving
- Questions must be age-appropriate for a 13-14 year old student
- Return ONLY valid JSON — no extra text, no markdown, no explanation
"""


# ── Build the generation prompt ───────────────────────────────────────────────

def _build_prompt(subject: str, topics: list[str]) -> str:
    """
    Builds the prompt that asks Groq to generate 60 MCQs
    for the given subject and its 5 topics.
    """
    topics_listed = "\n".join(f"- {topic}" for topic in topics)

    return f"""Generate exactly 4 MCQ questions for each of the following topics at each difficulty level (easy, medium, hard).
Subject: {subject}
Topics:
{topics_listed}

For each question, return this exact JSON structure:
{{
  "topic": "topic name",
  "level": "easy" | "medium" | "hard",
  "question_text": "the question",
  "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
  "correct_answer": "A" | "B" | "C" | "D"
}}

Return a single JSON object with this structure:
{{
  "questions": [ ...all 60 questions here... ]
}}

Important:
- Exactly 4 questions per topic per level = 60 total questions
- The correct_answer must match one of the option keys exactly (A, B, C, or D)
- Do NOT include any text outside the JSON
"""


# ── Parse the LLM response into Question objects ──────────────────────────────

def _parse_questions(raw_json: str, subject: str) -> dict[str, list[Question]]:
    """
    Parses the JSON string returned by Groq into a dict of
    topic → list of Question objects.
    """
    data = json.loads(raw_json)
    questions_by_topic: dict[str, list[Question]] = {}

    for item in data["questions"]:
        topic = item["topic"]
        level: Level = item["level"]

        question = Question(
            question_id=str(uuid.uuid4()),
            subject=subject,
            topic=topic,
            level=level,
            question_text=item["question_text"],
            options=item["options"],
            correct_answer=item["correct_answer"].upper(),
        )

        if topic not in questions_by_topic:
            questions_by_topic[topic] = []
        questions_by_topic[topic].append(question)

    return questions_by_topic


# ── Main public function ──────────────────────────────────────────────────────

def generate_question_pool(subject: str) -> dict[str, list[Question]]:
    """
    Generates the full 60-question pool for a given subject.

    This is the ONLY Groq API call made by Agent 1.
    Called once at the start of each quiz session.

    Returns:
        A dict mapping each topic name to its list of Question objects.
        Example: {"Rational Numbers": [Question(...), ...], ...}
    """
    if subject not in SUBJECTS:
        raise ValueError(f"Unknown subject: '{subject}'. Choose from: {list(SUBJECTS.keys())}")

    topics = SUBJECTS[subject]
    llm = _get_groq_client()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_prompt(subject, topics)),
    ]

    print(f"[QuestionGenerator] Generating 60 questions for {subject}...")
    response = llm.invoke(messages)
    raw_content = response.content.strip()

    # Strip markdown code fences if the model added them
    if raw_content.startswith("```"):
        raw_content = raw_content.split("```")[1]
        if raw_content.startswith("json"):
            raw_content = raw_content[4:]
        raw_content = raw_content.strip()

    question_pool = _parse_questions(raw_content, subject)
    total = sum(len(q) for q in question_pool.values())
    print(f"[QuestionGenerator] Generated {total} questions across {len(question_pool)} topics.")

    return question_pool
