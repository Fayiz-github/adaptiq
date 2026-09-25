"""
agent.py (Evaluator)
--------------------
Coordinates evaluation: reads student memory and generates comprehensive feedback.
"""

from core.memory import get_past_weak_topics, get_improvement_summary
from evaluator.report_generator import generate_evaluation_report


class EvaluatorAgent:
    """Evaluates student performance using historical context and AI."""

    def __init__(self, student_name: str, subject: str):
        self.student_name = student_name
        self.subject = subject

    def evaluate(
        self,
        score_summary: str,
        mastered_topics: list[str],
        weak_topics: list[str],
        topic_level_notes: str = "",
    ) -> str:
        """Generates qualitative feedback incorporating past session trends."""
        past_weak = get_past_weak_topics(self.student_name, self.subject)
        summary = get_improvement_summary(self.student_name, self.subject)

        history_note = ""
        if past_weak:
            history_note += f"Recurring weak topics in past sessions: {', '.join(past_weak)}. "
        if summary.get("total_attempts", 0) > 1:
            trend = "improving" if summary.get("is_improving") else "stable"
            history_note += f"Student has completed {summary['total_attempts']} quizzes with a {trend} trend."

        return generate_evaluation_report(
            student_name=self.student_name,
            subject=self.subject,
            score_summary=score_summary,
            mastered_topics=mastered_topics,
            weak_topics=weak_topics,
            topic_level_notes=topic_level_notes,
            past_history_note=history_note,
        )
