"""
a2a_client.py
-------------
The HTTP client used by Agent 1 (Quizmaster) to send the A2A packet
to Agent 2 (Evaluator) and receive the report card back.

This is the CLIENT side of the Agent-to-Agent communication.
The SERVER side is in evaluator/a2a_server.py
"""

import json
import httpx
from dataclasses import asdict

from core.models import A2APacket
from core.config import EVALUATOR_URL


def send_packet_to_evaluator(packet: A2APacket) -> str:
    """
    Sends the A2A packet to the Evaluator server and returns
    the generated report card as a string.

    Raises:
        ConnectionError: If the evaluator server is not running.
        RuntimeError: If the server returns an error response.
    """
    payload = asdict(packet)  # Convert dataclass to plain dict for JSON serialisation

    try:
        response = httpx.post(
            EVALUATOR_URL,
            json=payload,
            timeout=60.0,  # Gemini can take a few seconds
        )
    except httpx.ConnectError:
        raise ConnectionError(
            f"Could not connect to the Evaluator server at {EVALUATOR_URL}.\n"
            "Make sure the evaluator server is running:\n"
            "  python -m evaluator.a2a_server"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Evaluator server returned an error: "
            f"{response.status_code} — {response.text}"
        )

    result = response.json()
    return result.get("report_card", "No report card returned.")
