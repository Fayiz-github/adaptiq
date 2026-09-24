"""
agent.py (Quizmaster)
---------------------
QuizmasterAgent is Agent 1.

It:
1. Generates the 60-question pool (one Groq call)
2. Runs the adaptive quiz using the LangGraph engine
3. Collects the student's answers interactively
4. Packages all session data into an A2A packet
5. Sends the packet to Agent 2 (Evaluator) via the A2A client
"""

import uuid
from datetime import datetime, timezone

from core.models import (
    QuizState,
    A2APacket,
    SUBJECTS,
    PREREQUISITE_MAP,
    LEVEL_SCORES,
    TopicState,
)
from core.config import validate_config
from quizmaster.question_generator import generate_question_pool
from quizmaster.quiz_engine import build_quiz_graph, check_answer, route_answer
from quizmaster.a2a_client import send_packet_to_evaluator


class QuizmasterAgent:
    """
    Agent 1 — conducts the adaptive quiz session from start to finish.

    Usage:
        agent = QuizmasterAgent(student_name="Arjun", subject="Mathematics")
        report = agent.run()
        print(report)
    """

    def __init__(self, student_name: str, subject: str):
        validate_config()

        if subject not in SUBJECTS:
            raise ValueError(f"Invalid subject '{subject}'. Choose from: {list(SUBJECTS.keys())}")

        self.student_name = student_name
        self.subject = subject
        self.session_id = str(uuid.uuid4())
        self.graph = build_quiz_graph()

    # ── Step 1: Build initial state and generate questions ────────────────────

    def _build_initial_state(self, question_pool: dict) -> QuizState:
        topics = SUBJECTS[self.subject]
        return QuizState(
            student_name=self.student_name,
            subject=self.subject,
            topic_states={},
            question_pool=question_pool,
            question_history=[],
            current_topic=topics[0],
            current_question=None,
            quiz_complete=False,
        )

    # ── Step 2: Get answer from the student (CLI or UI override) ─────────────

    def _ask_student(self, question) -> str:
        """
        Displays the question and collects the student's answer.
        Override this method in a subclass to integrate with a custom UI.
        """
        print(f"\n[{question.topic}] [{question.level.upper()}]")
        print(f"Q: {question.question_text}")
        for key, value in question.options.items():
            print(f"   {key}. {value}")

        while True:
            answer = input("Your answer (A/B/C/D): ").strip().upper()
            if answer in ("A", "B", "C", "D"):
                return answer
            print("Please enter A, B, C, or D.")

    # ── Step 3: Calculate weighted scores per topic ───────────────────────────

    def _calculate_scores(self, topic_states: dict[str, TopicState]) -> dict[str, int]:
        """
        Awards points based on the highest level the student reached per topic.
        Hard = 3 pts, Medium = 2 pts, Easy = 1 pt
        """
        scores = {}
        for topic, ts in topic_states.items():
            if ts.status == "mastered":
                scores[topic] = LEVEL_SCORES["hard"]
            elif ts.current_level == "hard":
                scores[topic] = LEVEL_SCORES["hard"]
            elif ts.current_level == "medium":
                scores[topic] = LEVEL_SCORES["medium"]
            else:
                scores[topic] = LEVEL_SCORES["easy"]
        return scores

    # ── Step 4: Build the A2A packet ─────────────────────────────────────────

    def _build_a2a_packet(self, state: QuizState) -> A2APacket:
        """
        Packages all session data into the structured A2A packet
        that Agent 2 (Evaluator) will analyse.
        """
        topic_states_serialised = {
            topic: {
                "topic": ts.topic,
                "subject": ts.subject,
                "status": ts.status,
                "current_level": ts.current_level,
                "consecutive_correct": ts.consecutive_correct,
                "demotion_count": ts.demotion_count,
                "questions_asked": ts.questions_asked,
                "correct_answers": ts.correct_answers,
            }
            for topic, ts in state["topic_states"].items()
        }

        history_serialised = [
            {
                "question_id": r.question_id,
                "topic": r.topic,
                "level": r.level,
                "question_text": r.question_text,
                "student_answer": r.student_answer,
                "correct_answer": r.correct_answer,
                "is_correct": r.is_correct,
            }
            for r in state["question_history"]
        ]

        weighted_scores = self._calculate_scores(state["topic_states"])
        total_correct = sum(r.is_correct for r in state["question_history"])
        total_questions = len(state["question_history"])

        return A2APacket(
            packet_id=self.session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            student_name=self.student_name,
            subject=self.subject,
            topic_states=topic_states_serialised,
            question_history=history_serialised,
            weighted_scores=weighted_scores,
            total_correct=total_correct,
            total_questions=total_questions,
            prerequisite_map=PREREQUISITE_MAP,
        )

    # ── Main run loop ─────────────────────────────────────────────────────────

    def run(self) -> str:
        """
        Runs the full quiz session end-to-end.

        Returns:
            The personalised report card text generated by Agent 2.
        """
        print(f"\n{'='*60}")
        print(f"  Welcome, {self.student_name}!")
        print(f"  Subject: {self.subject}")
        print(f"  Generating your question pool, please wait...")
        print(f"{'='*60}\n")

        # Step 1: Generate all questions (single Groq call)
        question_pool = generate_question_pool(self.subject)

        # Step 2: Initialise state and start the graph
        state = self._build_initial_state(question_pool)
        state = self.graph.invoke(state)

        # Step 3: Quiz loop — ask questions until the quiz is complete
        while not state.get("quiz_complete"):
            question = state.get("current_question")
            if question is None:
                break

            # Ask the student and collect the answer
            answer = self._ask_student(question)

            # Process the answer through the engine
            state = check_answer(state, answer)
            state = route_answer(state)

            # Advance the graph (pick next question or end)
            state = self.graph.invoke(state)

        # Step 4: Build and send the A2A packet to Agent 2
        print("\n[Quizmaster] Quiz complete. Sending results to Evaluator...")
        packet = self._build_a2a_packet(state)

        # Step 5: Receive and return the report card
        report_card = send_packet_to_evaluator(packet)
        return report_card
