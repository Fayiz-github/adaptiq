"""
agent.py (Quizmaster)
---------------------
Orchestrates the adaptive quiz session with progressive learning and direct SQLite storage.

No hardcoded questions: Questions are generated dynamically via LLM on demand.
No client-server setup: Direct in-process execution with database persistence.
"""

import os
import sys
import uuid
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

# Allow running directly from within the quizmaster/ directory or project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import (
    Question,
    Level,
    SUBJECTS,
    PREREQUISITE_MAP,
    LEVEL_SCORES,
    TopicState,
)
from core.config import validate_config
from core.database import create_tables, save_session
from quizmaster.question_generator import generate_dynamic_question


# =============================================================================
# QUIZMASTER AGENT IMPLEMENTATION
# =============================================================================

class QuizmasterAgent:
    """
    Adaptive Quizmaster Agent responsible for interactive testing, difficulty scaling,
    and performance tracking across multiple curriculum topics.

    Attributes:
        student_name (str): The unique display name of the student.
        subject (str): The chosen academic subject (e.g., Mathematics, Biology).
        session_id (str): Unique UUID4 identifier for the active quiz attempt.
        topics (list[str]): Ordered list of curriculum topics to assess.
    """

    def __init__(self, student_name: str, subject: str):
        """
        Initializes the Quizmaster session, validates configuration, and prepares database tables.

        Args:
            student_name (str): The student's name (defaults to 'Student' if whitespace/empty).
            subject (str): The selected subject (defaults to 'Mathematics' if whitespace/empty).
        """
        # Validate that required environment variables are set before quiz begins
        validate_config()

        # Sanitize and assign core student identity attributes
        self.student_name = student_name.strip() or "Student"
        self.subject = subject.strip() or "Mathematics"
        self.session_id = str(uuid.uuid4())

        # Load predefined topics from curriculum mapping or construct general fallbacks
        if self.subject in SUBJECTS:
            self.topics = SUBJECTS[self.subject]
        else:
            self.topics = [
                f"{self.subject} Fundamentals",
                f"{self.subject} Concepts",
                f"{self.subject} Applications",
            ]

        # Ensure SQLite database schema and tables exist locally
        create_tables()

    # -------------------------------------------------------------------------
    # Interactive Input & Validation Helpers
    # -------------------------------------------------------------------------

    def _ask_student(self, question: Question) -> str | None:
        """
        Presents a multiple-choice question to the student and captures validated input.

        This method supports:
        - Direct letter choices ('A', 'B', 'C', 'D')
        - Numeric aliases ('1' -> 'A', '2' -> 'B', etc.)
        - Punctuation-wrapped answers (e.g., 'A.', '(B)', 'Option C')
        - Full string matching (typing the actual choice text)
        - Clean exit commands ('Q', 'QUIT', 'EXIT', or Ctrl+C / EOF)

        Args:
            question (Question): The Question dataclass instance to display.

        Returns:
            str | None: The normalized option key ('A', 'B', 'C', 'D'), or None if the student quit.
        """
        print(f"\n[{question.topic}] [Difficulty: {question.level.upper()}]")
        print(f"Q: {question.question_text}")
        for opt in ["A", "B", "C", "D"]:
            if opt in question.options:
                print(f"   {opt}. {question.options[opt]}")

        # Map 1-4 numeric inputs to corresponding option letters
        digit_map = {"1": "A", "2": "B", "3": "C", "4": "D"}

        while True:
            try:
                raw = input("\nYour answer (A/B/C/D) or 'Q' to quit: ").strip()
                ans = raw.upper()

                # Clean common punctuation formatting: "A.", "(B)", "Option C", "[C]"
                clean = ans.strip(". )(:[]")
                if clean.startswith("OPTION ") or clean.startswith("CHOICE "):
                    clean = clean.split()[-1]

                # Match against standard option keys
                if clean in ("A", "B", "C", "D"):
                    return clean
                if clean in digit_map:
                    return digit_map[clean]
                if clean in ("Q", "QUIT", "EXIT", "STOP"):
                    return None

                # Check if the student entered the full text of one of the choices
                matched_opt = None
                for opt_key, opt_val in question.options.items():
                    if raw.lower() == opt_val.strip().lower():
                        matched_opt = opt_key
                        break
                if matched_opt:
                    return matched_opt

                # Graceful guidance if invalid input was provided
                print(f"\n[Warning] '{raw}' is not a valid choice! Allowed options are: A, B, C, D (or 1, 2, 3, 4, or 'Q' to quit).")
            except (EOFError, KeyboardInterrupt):
                print("\n[Notice] Quiz session stopped by user.")
                return None

    # -------------------------------------------------------------------------
    # Report Card Formatting & Pedagogical Analytics
    # -------------------------------------------------------------------------

    def _generate_report_card(
        self,
        topic_states: dict[str, TopicState],
        total_correct: int,
        total_questions: int,
    ) -> str:
        """
        Builds a comprehensive, formatted report card incorporating performance metrics,
        tier badges, learning takeaways, and cognitive study strategies.

        Pedagogical Tier Categorization:
        - Mastered: Student cleared all 3 difficulty tiers (Easy, Medium, Hard).
        - Tackling Hard: Student cleared Easy & Medium; currently solving Hard-level questions.
        - Passed Easy (Work on Medium): Student cleared foundational Easy level; building towards Medium.
        - Base Not Set: Student needs foundational reinforcement on definitions and introductory principles.

        Args:
            topic_states (dict[str, TopicState]): Mapping of topic names to their current TopicState.
            total_correct (int): Total number of correct answers across the entire quiz.
            total_questions (int): Total questions attempted by the student.

        Returns:
            str: Multi-line formatted ASCII report card suitable for terminal display and storage.
        """
        # Segregate topics into distinct pedagogical tiers
        mastered = [t for t, ts in topic_states.items() if ts.status == "mastered"]
        tackling_hard = [t for t, ts in topic_states.items() if ts.status != "mastered" and ts.current_level == "hard"]
        needs_work_med = [t for t, ts in topic_states.items() if ts.status != "mastered" and ts.current_level == "medium"]
        needs_work_easy = [t for t, ts in topic_states.items() if ts.status != "mastered" and ts.current_level == "easy"]
        all_needs_work = [t for t, ts in topic_states.items() if ts.status != "mastered"]

        # Calculate overall accuracy percentage (protected against zero division)
        pct = (total_correct / max(1, total_questions)) * 100

        # Construct header block
        lines = [
            "=" * 60,
            "          STUDENT PERFORMANCE REPORT CARD",
            "=" * 60,
            f"Student Name:    {self.student_name}",
            f"Subject:         {self.subject}",
            f"Questions Asked: {total_questions}",
            f"Total Correct:   {total_correct}",
            f"Overall Score:   {pct:.1f}%",
            "",
            "TOPIC PERFORMANCE BREAKDOWN:",
            "-" * 60,
        ]

        # Topic Breakdown table with explicit visual badges
        for topic, ts in topic_states.items():
            if ts.status == "mastered":
                badge = "[MASTERED ★ 🏆]"
            elif ts.current_level == "hard":
                badge = "[CLEARED MED - TACKLING HARD]"
            elif ts.current_level == "medium":
                badge = "[PASSED EASY - WORK ON MED]"
            else:
                badge = "[BASE NOT SET - REVISIT BASICS]"
            lines.append(f"  * {topic:<24} : {badge:<32} ({ts.correct_answers}/{ts.questions_asked} correct)")

        # High-level summary of goals achieved and pending
        lines.extend([
            "-" * 60,
            "KEY TAKEAWAYS & NEXT LEVEL GOALS:",
            f"  * Mastered (All Levels Cleared):     {', '.join(mastered) if mastered else 'None yet'}",
            f"  * Tackling Hard (Easy & Med Passed): {', '.join(tackling_hard) if tackling_hard else 'None'}",
            f"  * Passed Easy (Work on Medium):      {', '.join(needs_work_med) if needs_work_med else 'None'}",
            f"  * Base Not Set (Revisit Basics):     {', '.join(needs_work_easy) if needs_work_easy else 'None'}",
        ])

        # Prescriptive learning guidance: explains HOW to study for each difficulty tier
        lines.append("\nLEARNING GUIDANCE & HOW TO STUDY TO LEVEL UP:")
        if mastered:
            lines.append(f"  * 🏆 Exceptional work in {', '.join(mastered)}! You conquered Easy, Medium, and Hard levels.")
            lines.append("     💡 How to Maintain: Solidify by peer-teaching, exploring Olympiad problems, or connecting to real-world applications.")
        if tackling_hard:
            lines.append(f"  * 🚀 Fantastic achievement in {', '.join(tackling_hard)}! You successfully cleared both Easy and Medium levels.")
            lines.append("     💡 How to Study for Hard: Use 'What-If' stress-testing (e.g., how does doubling or removing a variable change outcomes?) and maintain an Error Log to diagnose edge-case slips.")
        if needs_work_med:
            lines.append(f"  * 🌟 Great effort in {', '.join(needs_work_med)}! You passed Easy, but Medium needs a little more work.")
            lines.append("     💡 How to Study for Medium: Build Compare-and-Contrast tables (e.g., contrasting two related concepts) and practice 2-step application problems rather than memorizing standalone facts.")
        if needs_work_easy:
            lines.append(f"  * 💪 Appreciate your effort in {', '.join(needs_work_easy)}! Foundational base is not yet set.")
            lines.append("     💡 How to Study for Easy: Stop passive textbook re-reading! Use Active Recall and the Feynman Technique — close your notes and write out definitions or sketch diagrams in your own words.")

        # Prerequisite reinforcement for foundational gaps
        if needs_work_easy:
            lines.append("\nPREREQUISITE REINFORCEMENT:")
            for w in needs_work_easy:
                prereqs = PREREQUISITE_MAP.get(w, [])
                if prereqs:
                    lines.append(f"  * Since base is not set in {w}, reinforce building blocks in: {', '.join(prereqs)}")

        lines.append("=" * 60)
        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Adaptive Difficulty Progression State Machine
    # -------------------------------------------------------------------------

    def _update_topic_progress(self, ts: TopicState, is_correct: bool) -> bool:
        """
        Updates topic difficulty level based on student performance using a state machine.

        Progression Rules:
        - 2 consecutive correct at Easy   -> Promoted to Medium level.
        - 2 consecutive correct at Medium -> Promoted to Hard level (advanced problem solving).
        - 1 correct at Hard              -> Topic is marked fully Mastered (conquered all tiers).
        - 2 consecutive mistakes at Easy -> Topic marked weak (marked for review, proceeds to next topic).
        - Mistake at Medium              -> Demoted to Easy for foundational reinforcement.
        - Mistake at Hard                -> Demoted to Medium for multi-step practice.

        Args:
            ts (TopicState): The active topic state tracker.
            is_correct (bool): True if the student answered the current question correctly.

        Returns:
            bool: True if the topic is concluded (mastered or marked weak for review), False otherwise.
        """
        if is_correct:
            ts.correct_answers += 1
            ts.consecutive_correct += 1

            # Check promotion from Easy to Medium
            if ts.current_level == "easy":
                if ts.consecutive_correct >= 2:
                    ts.current_level = "medium"
                    ts.status = "medium"
                    ts.consecutive_correct = 0
                    print("  -> Correct! Well done.")
                    print("  -> 🌟 Congratulations! You have successfully PASSED THE EASY LEVEL!")
                    print("     You've built a solid foundational base. Promoted to MEDIUM level —")
                    print("     to pass Medium and reach Hard, you have to work a little more on multi-step reasoning!")
                else:
                    print("  -> Correct! Great start on foundational concepts.")

            # Check promotion from Medium to Hard
            elif ts.current_level == "medium":
                if ts.consecutive_correct >= 2:
                    ts.current_level = "hard"
                    ts.status = "hard"
                    ts.consecutive_correct = 0
                    print("  -> Correct! Excellent analytical reasoning.")
                    print("  -> 🚀 Outstanding work! You have successfully CLEARED THE MEDIUM LEVEL!")
                    print("     Promoted to HARD level (Advanced Problem Solving). Conquer this level to reach full mastery!")
                else:
                    print("  -> Correct! Solid progress on Medium level.")

            # Check final topic mastery at Hard level
            elif ts.current_level == "hard":
                ts.status = "mastered"
                print("  -> Correct! Brilliant problem-solving on Hard level.")
                print(f"  -> 🏆 Incredible achievement! You conquered Easy, Medium, and Hard — full mastery achieved in '{ts.topic}'!")
                return True

        else:
            # Reset consecutive success streak and increment demotion counter
            ts.consecutive_correct = 0
            ts.demotion_count += 1

            # Handle difficulties / demotions at each level
            if ts.current_level == "easy":
                if ts.demotion_count >= 2:
                    ts.status = "weak"
                    print(f"  -> Good effort trying! Foundational base is not yet set in '{ts.topic}'. Marked for basic review.")
                    return True
                else:
                    print(f"  -> Good try! Foundational base is not set yet in '{ts.topic}'. Take time to review core definitions.")
            elif ts.current_level == "medium":
                ts.current_level = "easy"
                ts.status = "easy"
                print("  -> Nice attempt! You passed Easy earlier, but Medium needs a little more work.")
                print("     Adjusting level to EASY to reinforce foundations before tackling Medium again.")
            elif ts.current_level == "hard":
                ts.current_level = "medium"
                ts.status = "medium"
                print("  -> Great courage tackling Hard questions! You cleared Easy and Medium earlier.")
                print("     Adjusting to MEDIUM to solidify multi-step reasoning before re-attempting Hard.")

        return False

    # -------------------------------------------------------------------------
    # Quiz Session Orchestration
    # -------------------------------------------------------------------------

    def run(self) -> str:
        """
        Executes the end-to-end adaptive quiz workflow for all curriculum topics.

        Workflow Steps:
        1. Initialize TopicState trackers for each subject topic starting at Easy level.
        2. Iteratively generate LLM questions on-demand (with strict anti-repetition memory).
        3. Present questions, collect student input, and adaptively scale difficulty.
        4. Transmit performance telemetry packet to the Evaluator (via A2A HTTP or in-process).
        5. Persist student results and report cards to the local SQLite database.

        Returns:
            str: The final qualitative evaluation report card for the student.
        """
        print(f"\n{'='*60}")
        print(f"  Welcome, {self.student_name}!")
        print(f"  Subject: {self.subject}")
        print(f"  Starting adaptive session...")
        print(f"{'='*60}")

        # Initialize all topics at Easy level to ensure foundational competence is verified
        topic_states = {
            topic: TopicState(topic=topic, subject=self.subject, current_level="easy", status="easy")
            for topic in self.topics
        }

        total_correct = 0
        total_questions = 0
        # Allow up to 5 questions per topic so progressing students can conquer Hard level
        max_questions_per_topic = 5
        cancelled = False
        all_session_questions: list[str] = []

        # Iterate through curriculum topics sequentially
        for topic in self.topics:
            if cancelled:
                break
            ts = topic_states[topic]
            print(f"\n>>> Starting Topic: {topic}")
            asked_in_topic: list[str] = []

            # Deliver questions until the student masters the topic, fails out, or hits topic question cap
            while ts.status not in ("mastered", "weak") and ts.questions_asked < max_questions_per_topic:
                print(f"[AI Quizmaster] Generating question ({ts.current_level.upper()})...", flush=True)
                try:
                    # Dynamically generate unique MCQ using LLM, passing recent questions to prevent duplicates
                    question = generate_dynamic_question(
                        subject=self.subject,
                        topic=topic,
                        level=ts.current_level,
                        previous_questions=all_session_questions[-10:],
                    )
                except Exception as err:
                    # If LLM generation fails unexpectedly, log notice and gracefully advance to the next topic
                    print(f"[Notice] Moving to next topic: {err}")
                    break

                # Track questions to maintain anti-repetition memory
                all_session_questions.append(question.question_text)
                asked_in_topic.append(question.question_text)
                ts.questions_asked += 1
                total_questions += 1

                # Present question and receive sanitized student answer
                answer = self._ask_student(question)
                if answer is None:
                    # Student selected 'Q' to quit or pressed Ctrl+C / EOF
                    cancelled = True
                    ts.questions_asked -= 1
                    total_questions -= 1
                    print("\n[Quizmaster] Stopping quiz session...")
                    break

                # Validate answer against the dynamic answer key
                is_correct = (answer == question.correct_answer)
                if is_correct:
                    total_correct += 1
                else:
                    print(f"  -> Incorrect. The correct answer was {question.correct_answer}.")

                # Update adaptive state machine (promotion / demotion / mastery check)
                finished = self._update_topic_progress(ts, is_correct)
                if finished:
                    break

            # Sync final topic status after completing loop
            if ts.questions_asked > 0 and ts.status != "mastered":
                if ts.current_level == "hard":
                    ts.status = "hard"
                elif ts.current_level == "medium":
                    ts.status = "medium"
                else:
                    ts.status = "weak"

        # Handle early abort: do not pollute database with incomplete aborted sessions
        if cancelled:
            if total_questions == 0:
                return "\n[Quizmaster] Quiz session cancelled before any questions were answered."
            return (
                f"\n[Quizmaster] Quiz session stopped by {self.student_name}. "
                f"You completed {total_correct}/{total_questions} question(s) before stopping. "
                "The session was aborted and no report was recorded in the database."
            )

        print("\n[AI Evaluator] Analyzing session performance and preparing report card...", flush=True)

        # ---------------------------------------------------------------------
        # Phase 1: Try Evaluator A2A HTTP Service (if running)
        # ---------------------------------------------------------------------
        try:
            from quizmaster.a2a_client import send_packet_to_evaluator
            from core.models import A2APacket

            # Construct standardized telemetry packet
            packet = A2APacket(
                packet_id=self.session_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                student_name=self.student_name,
                subject=self.subject,
                topic_states={
                    t: {
                        "status": ts.status,
                        "current_level": ts.current_level,
                        "correct_answers": ts.correct_answers,
                        "questions_asked": ts.questions_asked,
                    }
                    for t, ts in topic_states.items()
                },
                question_history=[],
                weighted_scores={},
                total_correct=total_correct,
                total_questions=total_questions,
                prerequisite_map=PREREQUISITE_MAP,
            )

            server_report = send_packet_to_evaluator(packet)
            if server_report and "STUDENT PERFORMANCE REPORT CARD" in server_report:
                return server_report
        except Exception:
            pass  # Fall through to seamless in-process local evaluation

        # ---------------------------------------------------------------------
        # Phase 2: In-Process Local Evaluation & Report Card Generation
        # ---------------------------------------------------------------------
        report_card = self._generate_report_card(
            topic_states=topic_states,
            total_correct=total_correct,
            total_questions=total_questions,
        )

        mastered = [t for t, ts in topic_states.items() if ts.status == "mastered"]
        all_needs_work = [t for t, ts in topic_states.items() if ts.status != "mastered"]

        # Call Evaluator Agent for qualitative mentorship and study strategy recommendations
        try:
            from evaluator.agent import EvaluatorAgent
            print("\n[Evaluator] Reviewing performance and learning history...")
            evaluator = EvaluatorAgent(student_name=self.student_name, subject=self.subject)
            pct_str = f"{(total_correct / max(1, total_questions)) * 100:.1f}%"

            # Build detailed per-topic context so the Evaluator knows the exact tier reached
            topic_details_list = []
            for t, ts in topic_states.items():
                if ts.status == "mastered":
                    desc = f"Mastered (Cleared Easy, Medium, and Hard; {ts.correct_answers}/{ts.questions_asked} correct)"
                elif ts.current_level == "hard":
                    desc = f"Tackling Hard (Passed Easy & Medium; {ts.correct_answers}/{ts.questions_asked} correct)"
                elif ts.current_level == "medium":
                    desc = f"At Medium (Passed Easy, needs work to clear Medium; {ts.correct_answers}/{ts.questions_asked} correct)"
                else:
                    desc = f"At Easy (Base not set yet, needs foundational review; {ts.correct_answers}/{ts.questions_asked} correct)"
                topic_details_list.append(f"  - {t}: {desc}")
            topic_details = "\n".join(topic_details_list)

            # Generate qualitative feedback with cognitive study strategies
            feedback = evaluator.evaluate(
                score_summary=f"{total_correct}/{total_questions} ({pct_str})",
                mastered_topics=mastered,
                weak_topics=all_needs_work,
                topic_level_notes=topic_details,
            )
            if feedback and not feedback.startswith("[Evaluator Notice]"):
                report_card += f"\n\nMENTOR'S PERSONALIZED FEEDBACK:\n{'-'*60}\n{feedback}\n{'='*60}"
        except Exception:
            pass  # Fallback: report_card already contains rich local learning guidance

        # ---------------------------------------------------------------------
        # Phase 3: SQLite Persistence
        # ---------------------------------------------------------------------
        try:
            save_session(
                packet_id=self.session_id,
                student_name=self.student_name,
                subject=self.subject,
                total_correct=total_correct,
                total_questions=total_questions,
                mastered_topics=mastered,
                weak_topics=all_needs_work,
                report_card=report_card,
            )
            print("\n[Database] Session successfully recorded in results.db")
        except Exception as db_err:
            print(f"\n[Database Warning] Could not save session: {db_err}")

        return report_card


if __name__ == "__main__":
    try:
        student = input("Enter student name: ").strip() or "Student"
        subject = input("Choose subject (Mathematics, Biology, Chemistry) [Mathematics]: ").strip() or "Mathematics"
    except (EOFError, KeyboardInterrupt):
        print("\nSession aborted.")
        sys.exit(0)

    agent = QuizmasterAgent(student_name=student, subject=subject)
    report = agent.run()
    print("\n" + report)
