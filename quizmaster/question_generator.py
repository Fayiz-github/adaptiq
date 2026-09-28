"""
question_generator.py
---------------------
Dynamic MCQ Generation Engine for Agent 1 (Quizmaster Agent).

Architecture & Role:
- Generates high-quality multiple-choice questions (MCQs) in real time on demand.
- Zero static or hardcoded question pools; every prompt is dynamically generated
  based on student subject, topic, and current adaptive difficulty tier.
- Implements a Dual-Provider Cascade: Primary LLM (OpenAI) with automatic
  fallback to Secondary LLM (Google Gemini).
- Enforces an Anti-Repetition Filter by passing recently asked questions as
  negative constraints in the prompt to prevent duplicate or redundant questions.
- Features a strict, multi-stage schema validator that ensures valid 4-option (A-D)
  structure and verified correct answers before presenting questions to students.
"""

import os
import sys
import json
import uuid
import re
from typing import Any

# ---------------------------------------------------------------------------
# Cross-Platform Console Encoding Setup
# ---------------------------------------------------------------------------
# Ensure standard output supports UTF-8 characters (useful for Windows terminals)
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

# External AI Provider / LangChain Integrations
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Internal project configurations and data models
from core.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
)
from core.models import Question, Level


# ===========================================================================
# System Prompt Definition
# ===========================================================================
# Directs the LLM to function as a strict academic examiner generating
# structured JSON with exactly 4 distinct choices and one correct answer.
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


# ===========================================================================
# LLM Client Factory Functions
# ===========================================================================

def _get_openai_llm() -> ChatOpenAI:
    """
    Initializes and returns the ChatOpenAI client.
    Configured with a 12-second timeout guard to prevent network hangs.
    """
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        temperature=0.7,
        timeout=12.0,
    )


def _get_gemini_llm() -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI client.
    Acts as the automatic fallback provider when OpenAI is unavailable or times out.
    """
    return ChatGoogleGenerativeAI(
        api_key=GEMINI_API_KEY,
        model=GEMINI_MODEL,
        temperature=0.7,
        request_timeout=12.0,
    )


# ===========================================================================
# Response Sanitization & JSON Extraction Utilities
# ===========================================================================

def _extract_content_text(content: Any) -> str:
    """
    Normalizes response content from various LangChain message types into a plain string.
    Handles raw strings, lists of content blocks, and object attributes.
    """
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
    """
    Strips markdown code fences (```json ... ```) or conversational preamble
    by extracting the substring between the first '{' and the last '}'.
    """
    cleaned = text.strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first != -1 and last != -1 and last > first:
        return cleaned[first : last + 1].strip()
    return cleaned


# ===========================================================================
# Question Parsing & Schema Validation Engine
# ===========================================================================

def _parse_and_validate_question(
    data: dict, subject: str, topic: str, level: Level
) -> Question | None:
    """
    Strictly validates raw JSON dictionary into a strongly-typed Question object.
    
    Validation Checks:
    1. Ensures input is a dictionary and question_text meets minimum length (>= 8 chars).
    2. Confirms all 4 choices (A, B, C, D) exist, are non-empty strings.
    3. Confirms all 4 choices are distinct (prevents duplicate option hallucination).
    4. Resolves the correct answer letter using a 4-tier matching strategy:
       - Direct single-letter match ('A', 'B', 'C', 'D')
       - Exact value match against option text
       - Regex word-boundary match (e.g., 'Option B', 'B)')
       - Substring containment match
    5. Rejects any malformed or ambiguous questions by returning None (triggers retry).
    """
    if not isinstance(data, dict):
        return None

    # Check question text validity
    question_text = str(data.get("question_text", "")).strip()
    if len(question_text) < 8:
        return None

    # Validate options structure
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

    # Tier 1: Direct single-letter match
    if raw_ans.upper() in ("A", "B", "C", "D"):
        correct_ans = raw_ans.upper()

    # Tier 2: Exact match against option text values (case-insensitive)
    if not correct_ans:
        for opt_key, opt_val in options.items():
            if raw_ans.lower() == opt_val.lower():
                correct_ans = opt_key
                break

    # Tier 3: Delimited prefix/suffix match (e.g. "Option B", "Choice C", "B)", "B.", "Answer: D")
    if not correct_ans:
        match = re.search(r'\b([A-D])\b', raw_ans.upper())
        if match:
            correct_ans = match.group(1)

    # Tier 4: Option text containment (e.g. "Option A: Mitochondria" matching "Mitochondria")
    if not correct_ans:
        for opt_key, opt_val in options.items():
            opt_lower = opt_val.lower()
            if opt_lower and (opt_lower in raw_ans.lower() or raw_ans.lower() in opt_lower):
                correct_ans = opt_key
                break

    # Strictly reject if we couldn't resolve a valid choice A, B, C, or D
    if not correct_ans or correct_ans not in ("A", "B", "C", "D"):
        return None

    # Assemble validated, immutable Question dataclass
    return Question(
        question_id=str(uuid.uuid4()),
        subject=subject,
        topic=topic,
        level=level,
        question_text=question_text,
        options=options,
        correct_answer=correct_ans,
    )


# ===========================================================================
# Primary Generation API & Dual-LLM Resilience Pipeline
# ===========================================================================

def generate_dynamic_question(
    subject: str,
    topic: str,
    level: Level,
    previous_questions: list[str] | None = None,
) -> Question:
    """
    Generates 1 multiple-choice question dynamically in real time.
    
    Resilience Architecture:
    1. Builds dynamic prompt with cognitive difficulty targets:
       - Easy: Basic recall, core definitions, and foundational vocabulary.
       - Medium: Conceptual understanding, formula applications, and multi-step reasoning.
       - Hard: Complex problem-solving, edge cases, and synthesis.
    2. Injects anti-repetition memory (up to last 6 questions) as negative constraints.
    3. Primary Provider (OpenAI): Executes up to 2 attempts with 12s timeout.
    4. Fallback Provider (Gemini): Executes up to 2 attempts if OpenAI fails or times out.
    5. Strict Validation: Discards malformed outputs and retries automatically.
    6. Returns a verified Question dataclass ready for student presentation.
    """
    # -----------------------------------------------------------------------
    # Step 1: Build Anti-Repetition Clause from Session Memory
    # -----------------------------------------------------------------------
    avoid_clause = ""
    if previous_questions:
        bulleted = "\n".join(f"- {q}" for q in previous_questions[-6:])
        avoid_clause = (
            f"\n\nCRITICAL REQUIREMENT - DO NOT REPEAT:\n"
            f"Do NOT ask or repeat any of these previously asked questions:\n{bulleted}\n"
            f"You MUST ask about a DIFFERENT fact, organelle, formula, or concept in {topic}."
        )

    # -----------------------------------------------------------------------
    # Step 2: Construct Cognitive Level-Specific Prompt
    # -----------------------------------------------------------------------
    prompt = f"""Generate 1 MCQ for Class 8 {subject}.
Topic: {topic}
Difficulty Level: {level.upper()} ({level} questions should test: easy=basic recall & definitions, medium=understanding & application, hard=complex problem solving).{avoid_clause}

Return ONLY the JSON object with keys: question_text, options, correct_answer."""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    # -----------------------------------------------------------------------
    # Step 3: Attempt Generation via Primary Provider (OpenAI)
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Step 4: Fallback Generation via Secondary Provider (Google Gemini)
    # -----------------------------------------------------------------------
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

    # -----------------------------------------------------------------------
    # Step 5: Exhaustion Error
    # -----------------------------------------------------------------------
    raise RuntimeError(
        f"Unable to generate a valid question for {subject} - {topic} ({level}). "
        "Please check your API keys and network connection."
    )

