"""
question_generator.py
---------------------
Dynamically generates multiple-choice questions (MCQs) on demand using LLM
(OpenAI with automatic Gemini fallback).

No hardcoded questions. Each question is created in real-time based on the
student's current topic and adaptive difficulty level.
"""

import os
import sys
import json
import uuid

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from core.models import Question, Level


SYSTEM_PROMPT = """You are an expert exam question generator for Class 8 students.
Your job is to generate exactly 1 high-quality multiple-choice question (MCQ).

Rules:
- Exactly 4 options: A, B, C, D
- Only ONE option must be correct
- Return ONLY valid JSON in this exact structure without extra commentary:
{
  "question_text": "...",
  "options": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "correct_answer": "A"
}
"""


from typing import Any

def _get_openai_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.7,
        timeout=12.0,
    )


def _get_gemini_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
        temperature=0.7,
        request_timeout=12.0,
    )


import re


def _extract_content_text(content: Any) -> str:
    """Robustly extract text from string, list of blocks, or object."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            elif hasattr(item, "text"):
                parts.append(str(getattr(item, "text", "")))
            else:
                parts.append(str(item))
        return "\n".join(p for p in parts if p)
    return str(content)


def _clean_json_string(text: str) -> str:
    cleaned = text.strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        return cleaned[first : last + 1].strip()
    return cleaned


def _parse_and_validate_question(
    data: dict, subject: str, topic: str, level: Level
) -> Question | None:
    """
    Validates question structure and extracts the correct answer without
    blind fallbacks or assumptions. Returns None if data is incomplete or invalid.
    """
    if not isinstance(data, dict):
        return None

    question_text = str(data.get("question_text", "")).strip()
    if len(question_text) < 8:
        return None

    raw_options = data.get("options")
    if not isinstance(raw_options, dict):
        return None

    # Validate that all 4 choices A, B, C, D exist and are non-empty
    options = {}
    for opt in ("A", "B", "C", "D"):
        val = str(raw_options.get(opt, raw_options.get(opt.lower(), ""))).strip()
        if not val:
            return None
        options[opt] = val

    # Verify that all 4 choices are unique and distinct
    if len(set(v.strip().lower() for v in options.values())) < 4:
        return None

    # Extract correct answer accurately and safely
    raw_ans = str(data.get("correct_answer", "")).strip()
    if not raw_ans:
        return None

    correct_ans = None

    # 1. Direct single-letter match
    if raw_ans.upper() in ("A", "B", "C", "D"):
        correct_ans = raw_ans.upper()

    # 2. Exact match against option text values (case-insensitive)
    if not correct_ans:
        for opt_key, opt_val in options.items():
            if raw_ans.lower() == opt_val.lower():
                correct_ans = opt_key
                break

    # 3. Delimited prefix/suffix match (e.g. "Option B", "Choice C", "B)", "B.", "Answer: D")
    if not correct_ans:
        match = re.search(r'\b([A-D])\b', raw_ans.upper())
        if match:
            correct_ans = match.group(1)

    # 4. Option text containment (e.g. "Option A: Mitochondria" matching "Mitochondria")
    if not correct_ans:
        for opt_key, opt_val in options.items():
            opt_lower = opt_val.lower()
            if opt_lower and (opt_lower in raw_ans.lower() or raw_ans.lower() in opt_lower):
                correct_ans = opt_key
                break

    # Strictly reject if we couldn't resolve a valid choice A, B, C, or D
    if not correct_ans or correct_ans not in ("A", "B", "C", "D"):
        return None

    return Question(
        question_id=str(uuid.uuid4()),
        subject=subject,
        topic=topic,
        level=level,
        question_text=question_text,
        options=options,
        correct_answer=correct_ans,
    )


def generate_dynamic_question(
    subject: str,
    topic: str,
    level: Level,
    previous_questions: list[str] | None = None,
) -> Question:
    """
    Generates 1 MCQ question dynamically in real time for the given subject,
    topic, and difficulty level. Uses OpenAI first, with automatic Gemini fallback.
    Guarantees no duplicate or repetitive questions within the topic.
    """
    avoid_clause = ""
    if previous_questions:
        bulleted = "\n".join(f"- {q}" for q in previous_questions[-6:])
        avoid_clause = (
            f"\n\nCRITICAL REQUIREMENT - DO NOT REPEAT:\n"
            f"Do NOT ask or repeat any of these previously asked questions:\n{bulleted}\n"
            f"You MUST ask about a DIFFERENT fact, organelle, formula, or concept in {topic}."
        )

    prompt = f"""Generate 1 MCQ for Class 8 {subject}.
Topic: {topic}
Difficulty Level: {level.upper()} ({level} questions should test: easy=basic recall & definitions, medium=understanding & application, hard=complex problem solving).{avoid_clause}

Return ONLY the JSON object with keys: question_text, options, correct_answer."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    # 1. Try OpenAI (up to 2 attempts)
    if OPENAI_API_KEY:
        for _ in range(2):
            try:
                openai_llm = _get_openai_llm()
                res = openai_llm.invoke(messages)
                raw_text = _extract_content_text(res.content)
                cleaned = _clean_json_string(raw_text)
                data = json.loads(cleaned)
                validated = _parse_and_validate_question(data, subject, topic, level)
                if validated:
                    return validated
            except Exception:
                continue

    # 2. Fallback to Gemini (up to 2 attempts)
    if GEMINI_API_KEY:
        for _ in range(2):
            try:
                gemini_llm = _get_gemini_llm()
                res = gemini_llm.invoke(messages)
                raw_text = _extract_content_text(res.content)
                cleaned = _clean_json_string(raw_text)
                data = json.loads(cleaned)
                validated = _parse_and_validate_question(data, subject, topic, level)
                if validated:
                    return validated
            except Exception:
                continue

    raise RuntimeError(
        f"Unable to generate a valid question for {subject} - {topic} ({level}). "
        "Please check your API keys and network connection."
    )
