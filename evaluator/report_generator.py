"""
report_generator.py
-------------------
Uses Gemini to generate a thoughtful, encouraging, and personalized
student evaluation report based on their quiz performance and learning history.
"""

import sys
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)


# =============================================================================
# CONTENT EXTRACTION & NORMALIZATION
# =============================================================================

def _extract_content_text(content: Any) -> str:
    """
    Robustly extracts clean plaintext from disparate LangChain response types.

    Handles:
    - Raw strings
    - Lists of text chunks or AIMessage chunk dictionaries
    - Objects with '.text' attributes

    Args:
        content (Any): The response.content object from a ChatModel invocation.

    Returns:
        str: Cleaned, concatenated plaintext representation.
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


# =============================================================================
# QUALITATIVE EVALUATION GENERATION
# =============================================================================

def generate_evaluation_report(
    student_name: str,
    subject: str,
    score_summary: str,
    mastered_topics: list[str],
    weak_topics: list[str],
    topic_level_notes: str = "",
    past_history_note: str = "",
) -> str:
    """
    Generates a personalized, encouraging educational evaluation report
    teaching students cognitive study strategies tailored to their exact tier.

    Resilience Fallback Sequence:
    1. Attempts Gemini (with strict 8.0s timeout).
    2. Falls back to OpenAI (with 6.0s timeout).
    3. Falls back to deterministic rule-based mentor generator (zero failure rate).

    Args:
        student_name (str): Name of the student.
        subject (str): The academic subject evaluated.
        score_summary (str): Formatted score string (e.g. '11/16 (68.8%)').
        mastered_topics (list[str]): Topics where the student cleared Hard difficulty.
        weak_topics (list[str]): Topics still requiring work or reinforcement.
        topic_level_notes (str, optional): Detailed breakdown of each topic's tier. Defaults to "".
        past_history_note (str, optional): Longitudinal learning trends from SQLite. Defaults to "".

    Returns:
        str: Comprehensive, qualitative feedback string including study methodology.
    """
    system_prompt = (
        "You are an inspiring, warm, and expert educational mentor and learning scientist. "
        "Your mission is to motivate the student, appreciate their effort and progress, "
        "and crucially TEACH THEM HOW TO STUDY IN THE RIGHT WAY to achieve higher levels.\n\n"
        "Pedagogical & Study Strategy Guidelines:\n"
        "1. APPRECIATE FIRST: Warmly acknowledge their courage and effort taking on the challenge.\n"
        "2. FOR TOPICS AT EASY LEVEL (Base Not Set):\n"
        "   - Honest Assessment: Foundational base is not yet set.\n"
        "   - HOW TO STUDY RIGHT: Warn against passive textbook re-reading (the most common trap!). Recommend Active Recall (writing out definitions without notes), Flashcards, and the Feynman Technique (explaining the concept in simple, everyday language or sketching diagrams from memory).\n"
        "3. FOR TOPICS AT MEDIUM LEVEL (Passed Easy):\n"
        "   - Honest Assessment: Congratulate on passing Easy, but remind them that Medium also needs dedicated work to clear.\n"
        "   - HOW TO STUDY RIGHT: Recommend Compare-and-Contrast tables (contrasting two concepts, e.g. Mitosis vs. Meiosis, Reactants vs. Products) and Step-by-Step Scenario Practice (breaking problems down into 'Given -> Underlying Rule -> Output').\n"
        "4. FOR TOPICS AT HARD LEVEL (Tackling Hard):\n"
        "   - Honest Assessment: Commend them for clearing Easy & Medium and taking on complex challenges.\n"
        "   - HOW TO STUDY RIGHT: Recommend 'What-If' Parameter Testing (how changes in one component ripple through the system) and maintaining an Error Notebook to diagnose conceptual vs calculation errors.\n"
        "5. FOR MASTERED TOPICS: Celebrate full mastery across Easy, Medium, and Hard, and suggest peer-teaching or advanced Olympiad questions.\n"
        "6. Provide a concrete 2-step 'How to Study' Action Plan."
    )

    user_prompt = f"""
Student Name: {student_name}
Subject: {subject}
Results Summary: {score_summary}
Mastered Topics (Hard Cleared): {', '.join(mastered_topics) if mastered_topics else 'None yet'}
Topics Needing Work: {', '.join(weak_topics) if weak_topics else 'None'}
Topic Details:
{topic_level_notes}
Historical Context: {past_history_note or 'First session'}

Please provide a warm, encouraging, and structured evaluation following these points:
1. Warm Appreciation & Overall Effort Recognition
2. Level-by-Level Feedback with EXPLICIT ADVICE ON HOW TO STUDY THE RIGHT WAY:
   - For Easy topics: Kindly explain base is not set, and prescribe Active Recall / Feynman Technique instead of passive reading.
   - For Medium topics: Praise passing Easy, explain that Medium requires extra work, and prescribe Compare-and-Contrast / 2-step application practice.
   - For Hard topics: Celebrate clearing Medium, and prescribe 'What-If' synthesis & Error Log analysis.
   - For Mastered topics: Celebrate complete mastery across all 3 tiers.
3. Actionable 2-Step 'Level-Up' Study Action Plan
Keep the tone inspiring, practical, and scientifically grounded in effective study habits!
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    # 1. Try Gemini first (with strict 8s timeout to prevent freezing)
    if GEMINI_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL,
                temperature=0.7,
                request_timeout=8.0,
            )
            response = llm.invoke(messages)
            text = _extract_content_text(response.content).strip()
            if text:
                return text
        except Exception:
            pass  # Seamlessly fall through to OpenAI fallback

    # 2. Fast, reliable fallback to OpenAI (gpt-5-nano)
    if OPENAI_API_KEY:
        try:
            llm = ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model=OPENAI_MODEL,
                temperature=0.7,
                timeout=6.0,
            )
            response = llm.invoke(messages)
            text = _extract_content_text(response.content).strip()
            if text:
                return text
        except Exception:
            pass

    # 3. Built-in resilient mentor evaluation fallback (ensures flawless live demonstrations)
    return _generate_resilient_mentor_report(
        student_name=student_name,
        subject=subject,
        score_summary=score_summary,
        mastered_topics=mastered_topics,
        weak_topics=weak_topics,
        topic_level_notes=topic_level_notes,
    )


def _generate_resilient_mentor_report(
    student_name: str,
    subject: str,
    score_summary: str,
    mastered_topics: list[str],
    weak_topics: list[str],
    topic_level_notes: str = "",
) -> str:
    """
    Constructs a deterministic, pedagogically sound mentor evaluation report.

    Guarantees that a rich, encouraging evaluation teaching actionable study strategies
    is delivered even during offline demos or when external LLM endpoints experience latency.

    Args:
        student_name (str): Name of the student.
        subject (str): The subject evaluated.
        score_summary (str): Formatted score string (e.g. '11/16 (68.8%)').
        mastered_topics (list[str]): Topics where the student cleared Hard difficulty.
        weak_topics (list[str]): Topics that need further work.
        topic_level_notes (str, optional): Formatted string containing individual topic tier details. Defaults to "".

    Returns:
        str: Structured mentor evaluation text complete with level assessments and a 2-step study plan.
    """
    lines = [
        f"Warm greetings, {student_name}! Thank you for your hard work and genuine effort in today's {subject} quiz.",
        f"You achieved an overall score of {score_summary}. Remember: every quiz is a diagnostic tool to help you level up!",
        "",
        "PEDAGOGICAL ASSESSMENT & HOW TO STUDY TO LEVEL UP:",
    ]

    if mastered_topics:
        lines.append(f"  * 🏆 FULL MASTERY CLEARED in {', '.join(mastered_topics)}:")
        lines.append("    -> Congratulations! You conquered Easy, Medium, and Hard tiers with exceptional skill.")
        lines.append("    -> 💡 How to Study: Maintain mastery by peer-teaching or tackling advanced competitive problems.")

    if topic_level_notes:
        for t_line in topic_level_notes.split("\n"):
            t_line = t_line.strip()
            if not t_line:
                continue
            topic_name = t_line.split(":")[0].strip("- ")
            if "Tackling Hard" in t_line or "Hard level" in t_line:
                lines.append(f"  * 🚀 TACKLING HARD in {topic_name}:")
                lines.append("    -> Assessment: You successfully cleared Easy and Medium! You are now confronting advanced synthesis.")
                lines.append("    -> 💡 HOW TO STUDY RIGHT: Practice 'What-If' Stress-Testing (e.g., what happens if a variable is doubled or removed?) and keep an Error Log to diagnose root-cause thinking slips.")
            elif "At Medium" in t_line or "Medium level" in t_line:
                lines.append(f"  * 🌟 PASSED EASY / WORKING ON MEDIUM in {topic_name}:")
                lines.append("    -> Assessment: Great job passing Easy! However, to pass Medium and reach Hard, you need to work a little more.")
                lines.append("    -> 💡 HOW TO STUDY RIGHT: Build Compare-and-Contrast tables (contrasting two related processes) and practice 2-step application problems rather than memorizing isolated facts.")
            elif "At Easy" in t_line or "Easy level" in t_line or "Base not set" in t_line:
                lines.append(f"  * 💪 BASE NOT SET (REVISIT BASICS) in {topic_name}:")
                lines.append("    -> Assessment: Appreciate your effort! Foundational base is not yet set in this topic.")
                lines.append("    -> 💡 HOW TO STUDY RIGHT: Avoid passive textbook re-reading! Use Active Recall and the Feynman Technique — close your notes and write out definitions or sketch diagrams in your own words.")
    elif weak_topics:
        lines.append(f"  * Focus on reinforcing foundational definitions in: {', '.join(weak_topics)} using Active Recall.")

    lines.extend([
        "",
        "ACTIONABLE 'HOW TO STUDY' LEVEL-UP PLAN:",
        "  1. Step 1 (Build The Base): For Easy-tier topics, spend 15 minutes quizzing yourself on flashcards or explaining concepts to a friend from memory (Feynman Technique).",
        "  2. Step 2 (Bridge to Hard): For Medium-tier topics, don't just memorize definitions — practice multi-step scenario questions that connect two concepts together.",
        "Keep up the great enthusiasm and dedication!"
    ])
    return "\n".join(lines)
