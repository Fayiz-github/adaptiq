"""
a2a_client.py
-------------
The HTTP client used by Agent 1 (Quizmaster) to send the A2A packet
to Agent 2 (Evaluator) and receive the report card back.

This is the CLIENT side of the Agent-to-Agent communication.
The SERVER side is in evaluator/a2a_server.py
"""

import sys
import json
import httpx
from dataclasses import asdict

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

from core.models import A2APacket
from core.config import EVALUATOR_URL


def send_packet_to_evaluator(packet: A2APacket) -> str:
    """
    Sends the A2A packet to the Evaluator server and returns
    the generated report card as a string.
    """
    payload = asdict(packet)

    try:
        response = httpx.post(
            EVALUATOR_URL,
            json=payload,
            timeout=20.0,  # 20s max before falling back cleanly
        )
    except httpx.ConnectError:
        raise ConnectionError(
            f"Could not connect to the Evaluator server at {EVALUATOR_URL}.\n"
            "Make sure the evaluator server is running:\n"
            "  uv run python -m evaluator.a2a_server"
        )
    except httpx.TimeoutException:
        raise TimeoutError(
            f"Evaluator server at {EVALUATOR_URL} timed out after 20 seconds."
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Evaluator server returned an error: "
            f"{response.status_code} — {response.text}"
        )

    result = response.json()
    return result.get("report_card", "No report card returned.")


if __name__ == "__main__":
    import uuid
    from datetime import datetime, timezone
    from core.models import PREREQUISITE_MAP

    print("=" * 60)
    print("  Testing A2A Client -> Server Connection")
    print(f"  Target Server: {EVALUATOR_URL}")
    print("=" * 60)

    sample_packet = A2APacket(
        packet_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        student_name="Test Student",
        subject="Mathematics",
        topic_states={
            "Rational Numbers": {"status": "mastered", "correct_answers": 3, "questions_asked": 4},
            "Linear Equations": {"status": "weak", "correct_answers": 0, "questions_asked": 2},
        },
        question_history=[],
        weighted_scores={},
        total_correct=3,
        total_questions=6,
        prerequisite_map=PREREQUISITE_MAP,
    )

    try:
        print("[Client] Sending test packet to server...")
        report = send_packet_to_evaluator(sample_packet)
        print("\n[Success] Received evaluated report from server:")
        print("-" * 60)
        print(report)
    except ConnectionError as err:
        print(f"\n[Connection Error] {err}")
    except TimeoutError as err:
        print(f"\n[Timeout Error] {err}")
    except Exception as err:
        print(f"\n[Error] {err}")
