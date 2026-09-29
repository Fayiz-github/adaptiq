"""
a2a_server.py
-------------
FastAPI HTTP Server for Agent 2 (Evaluator Agent).

Architecture & Role:
- Serves as the receiving endpoint in the Agent-to-Agent (A2A) protocol.
- Accepts telemetry data (A2APacket) from Agent 1 (Quizmaster) via HTTP POST.
- Executes comprehensive pedagogical diagnosis using LLM (Gemini / OpenAI).
- Formats a human-readable ASCII report card with pedagogical badges and cognitive study advice.
- Persists finalized session records into the SQLite database (results.db).
- Returns the generated evaluation report back to the calling client.
"""

import sys
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
import uvicorn

# ---------------------------------------------------------------------------
# Cross-Platform Console Encoding Setup
# ---------------------------------------------------------------------------
# Ensure standard output supports UTF-8 characters (useful for Windows terminals)
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

# Ensure repository root is on sys.path for direct script execution
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Internal project imports: configurations, database layer, and evaluator agent
from core.config import EVALUATOR_HOST, EVALUATOR_PORT
from core.database import save_session
from evaluator.agent import EvaluatorAgent

# Safe import for Langfuse tracing
try:
    from langfuse import observe, propagate_attributes, get_client
except ImportError:
    from contextlib import contextmanager

    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    @contextmanager
    def propagate_attributes(*args, **kwargs):
        yield

    def get_client():
        class DummyClient:
            def flush(self):
                pass
        return DummyClient()

# ---------------------------------------------------------------------------
# FastAPI Application Initialization
# ---------------------------------------------------------------------------
# Initialize the web application instance with metadata for OpenAPI/Swagger docs
app = FastAPI(
    title="Adaptiq Evaluator Agent",
    description="A2A Server for evaluating student quiz sessions and diagnosing learning gaps.",
    version="1.0.0",
)


# ===========================================================================
# Health & Status Endpoints
# ===========================================================================

@app.get("/")
def root() -> dict[str, str]:
    """
    Root discovery endpoint.
    Allows clients or monitoring tools to verify server identity and availability.
    """
    return {
        "service": "Adaptiq Evaluator Agent (A2A Server)",
        "status": "online",
        "endpoint": "/evaluate",
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Liveness probe / health check endpoint.
    Used for monitoring service uptime in production or microservice setups.
    """
    return {"status": "healthy"}


# ===========================================================================
# Core A2A Evaluation Endpoint
# ===========================================================================

@app.post("/evaluate")
@observe(name="Evaluator Agent Server", as_type="agent")
def evaluate_session(packet: dict[str, Any]) -> dict[str, Any]:
    """
    Primary Agent-to-Agent (A2A) evaluation handler.
    
    Workflow:
    1. Parse and validate the incoming A2APacket payload from Quizmaster.
    2. Extract student performance metrics and topic progression states.
    3. Categorize topics into 'mastered' vs 'weak' based on difficulty levels reached.
    4. Compute overall accuracy percentage with zero-division safeguard.
    5. Invoke EvaluatorAgent (LLM) to perform deep pedagogical diagnosis.
    6. Assemble an ASCII report card with clear headers, scores, and mentor notes.
    7. Persist session data to the SQLite database (results.db).
    8. Return JSON response containing the report card and structured feedback.
    """
    # -----------------------------------------------------------------------
    # Step 1: Extract packet fields with safe defaults
    # -----------------------------------------------------------------------
    packet_id: str = packet.get("packet_id", "")
    student_name: str = packet.get("student_name", "Student")
    email: str = packet.get("email", "")
    subject: str = packet.get("subject", "Mathematics")
    total_correct: int = packet.get("total_correct", 0)
    total_questions: int = packet.get("total_questions", 0)
    topic_states: dict[str, Any] = packet.get("topic_states", {})

    # -----------------------------------------------------------------------
    # Step 2: Validate required payload fields
    # -----------------------------------------------------------------------
    if not packet_id:
        raise HTTPException(
            status_code=400,
            detail="Missing packet_id in request payload. Valid A2APacket required."
        )

    with propagate_attributes(
        user_id=email,
        session_id=packet_id,
        tags=["adaptiq", "evaluator-server", subject.lower(), f"user:{email}"],
        metadata={
            "student_name": student_name,
            "email": email,
            "subject": subject,
            "session_id": packet_id,
        },
    ):
        return _process_evaluation(
            packet_id=packet_id,
            student_name=student_name,
            email=email,
            subject=subject,
            total_correct=total_correct,
            total_questions=total_questions,
            topic_states=topic_states,
        )


def _process_evaluation(
    packet_id: str,
    student_name: str,
    email: str,
    subject: str,
    total_correct: int,
    total_questions: int,
    topic_states: dict[str, Any],
) -> dict[str, Any]:

    # -----------------------------------------------------------------------
    # Step 3: Analyze topic states and map learning tiers
    # -----------------------------------------------------------------------
    mastered_topics: list[str] = []
    weak_topics: list[str] = []
    topic_details_list: list[str] = []

    # Iterate through each topic state sent by Quizmaster
    for topic, state in topic_states.items():
        status = state.get("status", "") if isinstance(state, dict) else str(state)
        
        # Categorize into mastered vs weak / in-progress
        if status == "mastered":
            mastered_topics.append(topic)
        else:
            weak_topics.append(topic)

        # Build descriptive breakdown showing exact progress and accuracy
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

    # Combine topic notes into a single multi-line string for LLM context
    topic_details: str = "\n".join(topic_details_list)

    # -----------------------------------------------------------------------
    # Step 4: Calculate overall student accuracy percentage
    # -----------------------------------------------------------------------
    # Safeguard against division by zero if total_questions is 0
    pct: float = (total_correct / max(1, total_questions)) * 100
    score_summary: str = f"{total_correct}/{total_questions} ({pct:.1f}%)"

    # -----------------------------------------------------------------------
    # Step 5: Invoke AI Evaluator Agent
    # -----------------------------------------------------------------------
    # EvaluatorAgent synthesizes student data and generates empathetic mentor advice
    evaluator = EvaluatorAgent(student_name=student_name, subject=subject, email=email)
    feedback: str = evaluator.evaluate(
        score_summary=score_summary,
        mastered_topics=mastered_topics,
        weak_topics=weak_topics,
        topic_level_notes=topic_details,
    )

    # -----------------------------------------------------------------------
    # Step 6: Construct formatted ASCII Report Card
    # -----------------------------------------------------------------------
    report_lines: list[str] = [
        "=" * 60,
        "          STUDENT PERFORMANCE REPORT CARD",
        "=" * 60,
        f"Student Name:    {student_name}",
        f"Email:           {email}" if email else "",
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
    # Remove any empty header lines
    report_lines = [line for line in report_lines if line != ""]
    report_card: str = "\n".join(report_lines)

    # -----------------------------------------------------------------------
    # Step 7: Persist session record to SQLite database
    # -----------------------------------------------------------------------
    # Wrapped in try-except so database write errors do not crash the API response
    try:
        save_session(
            packet_id=packet_id,
            student_name=student_name,
            email=email,
            subject=subject,
            total_correct=total_correct,
            total_questions=total_questions,
            mastered_topics=mastered_topics,
            weak_topics=weak_topics,
            report_card=report_card,
        )
    except Exception as db_err:
        print(f"[Warning] Failed to save session to DB: {db_err}")

    # Flush telemetry to Langfuse
    try:
        get_client().flush()
    except Exception:
        pass

    # -----------------------------------------------------------------------
    # Step 8: Return structured response back to Agent 1 (Quizmaster)
    # -----------------------------------------------------------------------
    return {
        "status": "success",
        "packet_id": packet_id,
        "report_card": report_card,
        "feedback": feedback,
    }


# ===========================================================================
# Server Entrypoint
# ===========================================================================

def start_server() -> None:
    """
    Starts the Uvicorn ASGI server with host and port from core.config.
    Runs synchronously and listens for incoming A2A HTTP requests.
    """
    print(f"Starting Evaluator A2A Server on http://{EVALUATOR_HOST}:{EVALUATOR_PORT}...")
    uvicorn.run(app, host=EVALUATOR_HOST, port=EVALUATOR_PORT)


if __name__ == "__main__":
    # Allows starting the server directly via:
    # uv run python -m evaluator.a2a_server
    start_server()

