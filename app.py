"""
app.py
------
Main CLI interactive application for the Adaptiq Adaptive Quiz Platform.

Features:
- UTF-8 console output encoding reconfiguration for reliable cross-platform emoji rendering.
- Student profile login and isolated historical performance review.
- Interactive subject selection with friendly input aliases (1-3, short names, full names).
- Orchestration of live adaptive quizzes and instantaneous report card presentations.
"""

import re
import sys

# Ensure stdout uses UTF-8 encoding on Windows to prevent UnicodeEncodeError with emojis
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

# Standard email format validator (e.g., user@domain.com)
EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")

# Ensure core configurations and Langfuse environment variables are initialized
import core.config  # noqa: F401
from core.database import get_student_history, create_tables
from quizmaster.agent import QuizmasterAgent

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


# =============================================================================
# STUDENT REPORT HISTORY VIEWER
# =============================================================================

@observe(
    as_type="tool",
    name="View Past Student Reports",
)
def _view_past_reports(email: str, student_name: str) -> None:
    """
    Retrieves and displays past quiz attempts and evaluated report cards for the given student.

    Enforces strict student privacy: queries database exclusively for records where
    LOWER(email) matches the logged-in student's email.

    Args:
        email (str): The active student's email.
        student_name (str): The active student's display name.
    """
    with propagate_attributes(
        user_id=email,
        tags=["adaptiq", "history", f"user:{email}"],
        metadata={"student_name": student_name, "email": email},
    ):
        history = get_student_history(email)
    if not history:
        print(f"\n[Notice] No past quiz sessions found for '{student_name}' ({email}).")
        print("Complete a quiz first to see your evaluated report card!")
        return

    print(f"\nPast Quiz History for {student_name} ({email}):")
    print("-" * 60)
    for idx, session in enumerate(history, 1):
        date_str = session["created_at"][:10]
        correct = session["total_correct"]
        total = session["total_questions"]
        pct = (correct / max(1, total)) * 100
        print(f"  [{idx}] {date_str} | {session['subject']:<12} | Score: {correct}/{total} ({pct:.1f}%)")
    print("-" * 60)

    try:
        choice = input(f"\nEnter quiz number (1 to {len(history)}) to view full report card (or press Enter to go back): ").strip()
    except (KeyboardInterrupt, EOFError):
        return

    if choice.isdigit() and 1 <= int(choice) <= len(history):
        selected = history[int(choice) - 1]
        print("\n" + selected["report_card"])
    elif choice:
        print(f"\n[Warning] '{choice}' is not valid! Allowed options are: 1 to {len(history)} (or press Enter to go back).")


# =============================================================================
# ADAPTIVE QUIZ RUNNER
# =============================================================================

def _take_quiz(student_name: str, email: str) -> None:
    """
    Prompts the student to choose an academic subject and launches an adaptive quiz session.

    Supports:
    - Number keys ('1', '2', '3')
    - Colloquial abbreviations ('math', 'bio', 'chem')
    - Full subject names (case-insensitive)
    - Returning safely to main menu via 'b' or Ctrl+C / EOF

    Args:
        student_name (str): The active student's name.
        email (str): The active student's email address.
    """
    print("\nSubjects:")
    print("  1. Mathematics")
    print("  2. Biology")
    print("  3. Chemistry\n")

    # Flexible alias mapping for human-friendly input recognition
    subject_lookup = {
        "1": "Mathematics",
        "math": "Mathematics",
        "mathematics": "Mathematics",
        "2": "Biology",
        "bio": "Biology",
        "biology": "Biology",
        "3": "Chemistry",
        "chem": "Chemistry",
        "chemistry": "Chemistry",
    }

    while True:
        try:
            subject_input = input("Select subject (1-3 or name, 'b' to go back) [Mathematics]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Notice] Returning to main menu...")
            return

        # Default to Mathematics if user hits Enter without input
        if not subject_input:
            subject = "Mathematics"
            break
        elif subject_input.lower() in ("b", "back", "q", "quit", "exit"):
            return
        elif subject_input.lower() in subject_lookup:
            subject = subject_lookup[subject_input.lower()]
            break
        else:
            print(f"\n[Warning] '{subject_input}' is not a valid subject! Allowed options are: 1 (Mathematics), 2 (Biology), 3 (Chemistry), or 'b' (Back).")

    @observe(name="Student Adaptive Quiz Session")
    def _run_traced_quiz(s_name: str, s_email: str, s_subject: str) -> str:
        agent = QuizmasterAgent(student_name=s_name, subject=s_subject, email=s_email)
        with propagate_attributes(
            user_id=s_email,
            session_id=agent.session_id,
            tags=["adaptiq", s_subject.lower(), f"user:{s_email}"],
            metadata={
                "student_name": s_name,
                "email": s_email,
                "subject": s_subject,
            },
        ):
            return agent.run()

    # Execute adaptive quiz session traced under student's identity in Langfuse
    report = _run_traced_quiz(
        s_name=student_name,
        s_email=email,
        s_subject=subject,
    )
    print("\n" + report)

    # Flush telemetry to Langfuse
    try:
        get_client().flush()
    except Exception:
        pass


# =============================================================================
# APPLICATION ENTRY POINT & EVENT LOOP
# =============================================================================

def main() -> None:
    """
    Main loop providing student onboarding, menu routing, and graceful exit handling.
    """
    # Ensure database schema is primed
    create_tables()

    print("=" * 60)
    print("         Adaptiq Adaptive Quiz Platform")
    print("=" * 60)

    # Prompt student for their name and unique email
    try:
        student_name = input("Enter your name: ").strip() or "Student"
        while True:
            email = input("Enter your email: ").strip()
            if EMAIL_PATTERN.match(email):
                break
            print("[Warning] Please enter a valid email address (e.g. name@example.com).")
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!\n")
        return

    # Interactive main menu event loop
    while True:
        print(f"\nWelcome, {student_name} ({email})! What would you like to do?")
        print("  1. Start Adaptive Quiz")
        print("  2. View My Past Report Cards")
        print("  3. Exit")

        try:
            choice = input("\nSelect an option (1-3) [1]: ").strip() or "1"
        except (KeyboardInterrupt, EOFError):
            print(f"\n\nGoodbye, {student_name}! Keep learning.\n")
            break

        # Dispatch chosen user action
        if choice == "1":
            _take_quiz(student_name, email)
        elif choice == "2":
            _view_past_reports(email, student_name)
        elif choice in ("3", "q", "quit", "exit"):
            print(f"\nGoodbye, {student_name}! Keep learning.\n")
            break
        else:
            print(f"\n[Warning] '{choice}' is not a valid choice! Allowed options are: 1 (Start Adaptive Quiz), 2 (View My Past Report Cards), 3 (Exit).")


if __name__ == "__main__":
    main()
