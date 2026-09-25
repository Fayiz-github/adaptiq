"""
a2a_server.py
-------------
FastAPI HTTP server for Agent 2 (Evaluator).
Receives quiz session packets from Agent 1 (Quizmaster), runs
pedagogical evaluation using Gemini, and saves results to SQLite.
"""

import sys
from typing import Any
from fastapi import FastAPI, HTTPException
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

from core.config import EVALUATOR_HOST, EVALUATOR_PORT
from core.database import save_session
from evaluator.agent import EvaluatorAgent

app = FastAPI(
    title="Adaptiq Evaluator Agent",
    description="A2A Server for evaluating student quiz sessions.",
)


@app.get("/")
def root():
    """Basic health check endpoint."""
    return {
        "service": "Adaptiq Evaluator Agent (A2A Server)",
        "status": "online",
        "endpoint": "/evaluate",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/evaluate")
def evaluate_session(packet: dict[str, Any]):
    """
    Receives an A2A packet from Quizmaster, evaluates the student,
    persists the session to the database, and returns the report.
    """
    packet_id = packet.get("packet_id", "")
    student_name = packet.get("student_name", "Student")
    subject = packet.get("subject", "Mathematics")
    total_correct = packet.get("total_correct", 0)
    total_questions = packet.get("total_questions", 0)
    topic_states = packet.get("topic_states", {})

    if not packet_id:
        raise HTTPException(status_code=400, detail="Missing packet_id in request payload.")

    # Determine mastered and weak topics from topic_states
    mastered_topics = []
    weak_topics = []

    topic_details_list = []
    for topic, state in topic_states.items():
        status = state.get("status", "") if isinstance(state, dict) else str(state)
        if status == "mastered":
            mastered_topics.append(topic)
        elif status == "weak" or status != "mastered":
            weak_topics.append(topic)

        if isinstance(state, dict):
            lvl = state.get("current_level", "")
            c = state.get("correct_answers", 0)
            q = state.get("questions_asked", 0)
            if status == "mastered":
                desc = f"Mastered (Cleared Easy, Medium, and Hard; {c}/{q} correct)"
            elif lvl == "hard":
                desc = f"Tackling Hard (Passed Easy & Medium; {c}/{q} correct)"
            elif lvl == "medium":
                desc = f"At Medium (Passed Easy, needs work to clear Medium; {c}/{q} correct)"
            else:
                desc = f"At Easy (Base not set yet, needs foundational review; {c}/{q} correct)"
            topic_details_list.append(f"  - {topic}: {desc}")

    topic_details = "\n".join(topic_details_list)

    # Calculate overall percentage
    pct = (total_correct / max(1, total_questions)) * 100
    score_summary = f"{total_correct}/{total_questions} ({pct:.1f}%)"

    # Run AI evaluation using EvaluatorAgent
    evaluator = EvaluatorAgent(student_name=student_name, subject=subject)
    feedback = evaluator.evaluate(
        score_summary=score_summary,
        mastered_topics=mastered_topics,
        weak_topics=weak_topics,
        topic_level_notes=topic_details,
    )

    # Format the complete report card
    report_lines = [
        "=" * 60,
        "          STUDENT PERFORMANCE REPORT CARD",
        "=" * 60,
        f"Student Name:    {student_name}",
        f"Subject:         {subject}",
        f"Questions Asked: {total_questions}",
        f"Total Correct:   {total_correct}",
        f"Overall Score:   {pct:.1f}%",
        "",
        "TOPIC SUMMARY:",
        f"  * Mastered Topics: {', '.join(mastered_topics) if mastered_topics else 'None yet'}",
        f"  * Focus Areas:     {', '.join(weak_topics) if weak_topics else 'None'}",
        "-" * 60,
        "MENTOR'S EVALUATION & FEEDBACK:",
        "-" * 60,
        feedback,
        "=" * 60,
    ]
    report_card = "\n".join(report_lines)

    # Save to SQLite database
    try:
        save_session(
            packet_id=packet_id,
            student_name=student_name,
            subject=subject,
            total_correct=total_correct,
            total_questions=total_questions,
            mastered_topics=mastered_topics,
            weak_topics=weak_topics,
            report_card=report_card,
        )
    except Exception as db_err:
        print(f"[Warning] Failed to save session to DB: {db_err}")

    return {
        "status": "success",
        "packet_id": packet_id,
        "report_card": report_card,
        "feedback": feedback,
    }


def start_server():
    """Starts the Uvicorn web server."""
    print(f"Starting Evaluator A2A Server on http://{EVALUATOR_HOST}:{EVALUATOR_PORT}...")
    uvicorn.run(app, host=EVALUATOR_HOST, port=EVALUATOR_PORT)


if __name__ == "__main__":
    start_server()
