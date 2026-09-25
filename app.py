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

import sys

# Ensure stdout uses UTF-8 encoding on Windows to prevent UnicodeEncodeError with emojis
if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8", errors="replace")

from core.database import get_student_history, create_tables
from quizmaster.agent import QuizmasterAgent


# =============================================================================
# STUDENT REPORT HISTORY VIEWER
# =============================================================================

def _view_past_reports(student_name: str) -> None:
    """
    Retrieves and displays past quiz attempts and evaluated report cards for the given student.

    Enforces strict student privacy: queries database exclusively for records where
    LOWER(student_name) matches the logged-in student.

    Args:
        student_name (str): The active student's name.
    """
    history = get_student_history(student_name)
    if not history:
        print(f"\n[Notice] No past quiz sessions found for '{student_name}'.")
        print("Complete a quiz first to see your evaluated report card!")
        return

    print(f"\nPast Quiz History for {student_name}:")
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

def _take_quiz(student_name: str) -> None:
    """
    Prompts the student to choose an academic subject and launches an adaptive quiz session.

    Supports:
    - Number keys ('1', '2', '3')
    - Colloquial abbreviations ('math', 'bio', 'chem')
    - Full subject names (case-insensitive)
    - Returning safely to main menu via 'b' or Ctrl+C / EOF

    Args:
        student_name (str): The active student's name.
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

    # Instantiate QuizmasterAgent and execute the adaptive quiz loop
    agent = QuizmasterAgent(student_name=student_name, subject=subject)
    report = agent.run()
    print("\n" + report)


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

    # Prompt student for their name
    try:
        student_name = input("Enter your name: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!\n")
        return

    if not student_name:
        student_name = "Student"

    # Interactive main menu event loop
    while True:
        print(f"\nWelcome, {student_name}! What would you like to do?")
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
            _take_quiz(student_name)
        elif choice == "2":
            _view_past_reports(student_name)
        elif choice in ("3", "q", "quit", "exit"):
            print(f"\nGoodbye, {student_name}! Keep learning.\n")
            break
        else:
            print(f"\n[Warning] '{choice}' is not a valid choice! Allowed options are: 1 (Start Adaptive Quiz), 2 (View My Past Report Cards), 3 (Exit).")


if __name__ == "__main__":
    main()
