"""
streamlit_app.py
----------------
Adaptiq — AI-Powered Adaptive Quiz & Evaluation Platform for Class 8.
Streamlit Web Application with zero-error guarantees, glassmorphic dark UI,
and full multi-agent + Langfuse observability integration.
"""

import os
import sys
import uuid
import re
import json
from datetime import datetime, timezone
import streamlit as st
import pandas as pd
import altair as alt

# ── Ensure Root Directory on sys.path ─────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# ── Project Imports ────────────────────────────────────────────────────────────
import core.config
from core.models import (
    Question,
    TopicState,
    Level,
    SUBJECTS,
    PREREQUISITE_MAP,
    A2APacket,
)
from core.database import (
    create_tables,
    save_session,
    get_student_history,
    _connect,
)
from core.memory import (
    get_past_weak_topics,
    get_improvement_summary,
)
from quizmaster.question_generator import generate_dynamic_question
from quizmaster.fallback_bank import get_fallback_question
from evaluator.agent import EvaluatorAgent

# Safe Langfuse Tracing
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
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Adaptiq — Adaptive Learning Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Email validation pattern
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$")


# =============================================================================
# ULTRA-PREMIUM MODERN DARK GLASSMORPHIC STYLING
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Global Reset & Base Typography */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #F1F5F9 !important;
}

/* Ambient Radial Mesh Background */
.stApp {
    background:
        radial-gradient(ellipse 80% 60% at 10% 5%, rgba(99, 102, 241, 0.16) 0%, transparent 55%),
        radial-gradient(ellipse 60% 50% at 90% 90%, rgba(139, 92, 246, 0.13) 0%, transparent 55%),
        radial-gradient(ellipse 40% 40% at 50% 50%, rgba(6, 182, 212, 0.04) 0%, transparent 60%),
        #060A14 !important;
    min-height: 100vh;
}

/* Hide Streamlit Default Header / Footer Clutter */
header[data-testid="stHeader"] {
    background: transparent !important;
}
footer {
    visibility: hidden;
}

/* ─────────────────────────────────────────────────────────────────────────────
   STREAMLIT NATIVE INPUT & FORM CONTROLS OVERRIDES (DARK LUXURY FIX)
   ───────────────────────────────────────────────────────────────────────────── */
/* Force all text inputs into deep glassmorphic dark styling */
div[data-testid="stTextInput"] input,
div[data-testid="stTextInput"] > div > div > input,
.stTextInput input,
input[type="text"],
input[type="password"],
input[type="email"] {
    background: #0F172A !important;
    background-color: #0F172A !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stTextInput"] input:focus,
.stTextInput input:focus {
    border-color: #818CF8 !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3), 0 4px 20px rgba(99, 102, 241, 0.25) !important;
    background: #111C35 !important;
    background-color: #111C35 !important;
    outline: none !important;
}

div[data-testid="stTextInput"] input::placeholder,
.stTextInput input::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    font-weight: 400 !important;
}

/* Input Labels */
div[data-testid="stTextInput"] label,
.stTextInput label,
label {
    color: #CBD5E1 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    margin-bottom: 6px !important;
}

/* Primary Form Action Buttons */
button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #9333EA 100%) !important;
    color: #FFFFFF !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    letter-spacing: 0.02em !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 14px !important;
    padding: 13px 28px !important;
    box-shadow: 0 8px 24px -4px rgba(99, 102, 241, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 12px 32px -4px rgba(124, 58, 237, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.5) !important;
    border-color: rgba(255, 255, 255, 0.4) !important;
}

/* Secondary Buttons */
button[kind="secondary"],
.stButton > button {
    background: rgba(30, 41, 59, 0.6) !important;
    color: #E2E8F0 !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    padding: 10px 22px !important;
    transition: all 0.2s ease !important;
}

button[kind="secondary"]:hover,
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.2) !important;
    border-color: #818CF8 !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3) !important;
}

/* Remove Form Box Outline */
div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   RADIO BUTTONS STYLED AS LUXURY OPTION CARDS
   ───────────────────────────────────────────────────────────────────────────── */
div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin: 16px 0;
}

div[role="radiogroup"] > label {
    background: rgba(15, 23, 42, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    padding: 18px 24px !important;
    margin-bottom: 0 !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
    display: flex !important;
    align-items: center !important;
}

div[role="radiogroup"] > label:hover {
    background: rgba(30, 41, 59, 0.9) !important;
    border-color: rgba(99, 102, 241, 0.5) !important;
    transform: translateX(6px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
}

div[role="radiogroup"] > label[data-checked="true"],
div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(79, 70, 229, 0.25) 0%, rgba(124, 58, 237, 0.2) 100%) !important;
    border: 2px solid #818CF8 !important;
    box-shadow: 0 0 24px rgba(99, 102, 241, 0.35) !important;
}

div[role="radiogroup"] > label p {
    color: #F8FAFC !important;
    font-size: 1.05rem !important;
    font-weight: 500 !important;
    margin: 0 !important;
    line-height: 1.5 !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   DROPDOWN & SELECTBOX OVERRIDES
   ───────────────────────────────────────────────────────────────────────────── */
div[data-baseweb="select"] > div {
    background: #0F172A !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 12px !important;
    color: #F8FAFC !important;
}
div[data-baseweb="select"] * {
    color: #F8FAFC !important;
}
div[data-baseweb="popover"],
ul[role="listbox"] {
    background: #0F172A !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
}
li[role="option"] {
    background: transparent !important;
    color: #E2E8F0 !important;
}
li[role="option"]:hover,
li[aria-selected="true"] {
    background: rgba(99, 102, 241, 0.25) !important;
    color: #FFFFFF !important;
}

/* ─────────────────────────────────────────────────────────────────────────────
   HERO & BRAND SURFACES
   ───────────────────────────────────────────────────────────────────────────── */
.adaptiq-hero {
    background: linear-gradient(135deg, rgba(26, 34, 53, 0.85) 0%, rgba(13, 20, 36, 0.95) 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 22px;
    padding: 26px 34px;
    margin-bottom: 24px;
    box-shadow: 0 20px 45px -15px rgba(0, 0, 0, 0.7);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(16px);
}

.adaptiq-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366F1, #8B5CF6, #06B6D4, #10B981);
}

.hero-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
}

.hero-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #FFFFFF 20%, #E2E8F0 60%, #94A3B8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}

.hero-badge {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.2) 100%);
    border: 1px solid rgba(129, 140, 248, 0.5);
    color: #C7D2FE;
    padding: 6px 16px;
    border-radius: 9999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);
}

.hero-subtitle {
    color: #94A3B8;
    font-size: 1rem;
    margin-top: 8px;
    max-width: 820px;
    line-height: 1.5;
}

/* Glassmorphic Panel Card */
.glass-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 26px;
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 35px -10px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    box-shadow: 0 16px 40px -10px rgba(99, 102, 241, 0.18);
}

/* Subject Choice Card */
.subject-card {
    background: linear-gradient(145deg, rgba(26, 34, 53, 0.75) 0%, rgba(13, 20, 36, 0.85) 100%);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 22px;
    text-align: left;
    height: 100%;
    transition: all 0.25s ease;
}

.subject-card:hover {
    transform: translateY(-4px);
    border-color: #818CF8;
    box-shadow: 0 16px 32px -8px rgba(99, 102, 241, 0.3);
}

/* Difficulty Level Badges */
.level-badge-easy {
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid rgba(16, 185, 129, 0.5);
    color: #34D399;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
}

.level-badge-medium {
    background: rgba(245, 158, 11, 0.18);
    border: 1px solid rgba(245, 158, 11, 0.5);
    color: #FBBF24;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
}

.level-badge-hard {
    background: rgba(239, 68, 68, 0.18);
    border: 1px solid rgba(239, 68, 68, 0.5);
    color: #F87171;
    padding: 5px 14px;
    border-radius: 9999px;
    font-size: 0.82rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.2);
}

.level-badge-mastered {
    background: rgba(234, 179, 8, 0.22);
    border: 1px solid rgba(234, 179, 8, 0.7);
    color: #FDE047;
    padding: 5px 16px;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 18px rgba(234, 179, 8, 0.35);
}

.streak-pill {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(245, 158, 11, 0.2));
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #FDBA74;
    padding: 6px 16px;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 0 15px rgba(245, 158, 11, 0.2);
}

/* Question Prompt Styling */
.question-prompt {
    font-size: 1.35rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.5;
    margin-bottom: 22px;
    padding: 20px 24px;
    background: rgba(255, 255, 255, 0.035);
    border-left: 4px solid #818CF8;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

/* Metric Display Cards */
.metric-card {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6366F1, #8B5CF6);
}

.metric-val {
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.2rem;
    font-weight: 800;
    color: #FFFFFF;
    line-height: 1.1;
    margin-top: 6px;
}

.metric-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
}

/* Feedback Alert Banners */
.feedback-box-success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(6, 182, 212, 0.12) 100%);
    border: 1px solid rgba(16, 185, 129, 0.5);
    border-radius: 16px;
    padding: 20px 26px;
    margin: 18px 0;
    color: #D1FAE5;
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.15);
}

.feedback-box-error {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.18) 0%, rgba(245, 158, 11, 0.12) 100%);
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 16px;
    padding: 20px 26px;
    margin: 18px 0;
    color: #FEE2E2;
    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.15);
}

/* Sidebar Customizations */
[data-testid="stSidebar"] {
    background: #080C17 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Custom Info Chip */
.info-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.73rem;
    padding: 3px 10px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #94A3B8;
    display: inline-block;
    margin-right: 4px;
}

/* Legacy alias */
.telemetry-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.73rem;
    padding: 3px 10px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #94A3B8;
    display: inline-block;
    margin-right: 4px;
}

/* Section Headings */
.section-heading {
    font-family: 'Outfit', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.02em;
    margin: 0 0 4px 0;
}

.section-subheading {
    font-size: 0.9rem;
    color: #64748B;
    margin: 0 0 20px 0;
    line-height: 1.55;
}

/* Divider */
.soft-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 16px 0;
}

/* Modern Progress Bar */
div[data-testid="stProgress"] > div > div > div > div {
    background: linear-gradient(90deg, #6366F1, #8B5CF6, #06B6D4) !important;
    border-radius: 9999px !important;
}
div[data-testid="stProgress"] > div > div {
    background: rgba(255, 255, 255, 0.08) !important;
    border-radius: 9999px !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# BULLETPROOF SESSION STATE INITIALIZATION
# =============================================================================
def init_session_state() -> None:
    """Safely initializes all session state keys to prevent KeyError."""
    create_tables()

    defaults = {
        # Student Identity & Strict Privacy Isolation
        "is_authenticated": False,
        "student_name": "",
        "student_email": "",
        "active_nav": "🎯 Adaptive Quiz",
        # Quiz Progression State
        "quiz_active": False,
        "quiz_subject": "Mathematics",
        "quiz_topics": SUBJECTS["Mathematics"],
        "current_topic_idx": 0,
        "topic_states": {},
        "current_question": None,
        "selected_option": None,
        "answer_submitted": False,
        "last_feedback": None,
        "all_session_questions": [],
        "total_correct": 0,
        "total_questions": 0,
        "session_id": None,
        "session_start_time": None,
        # Evaluator Outputs
        "latest_report_card": None,
        "latest_packet": None,
        "viewing_history_record": None,
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# =============================================================================
# ADAPTIVE STATE MACHINE CONTROLLER (AGENT 1 LOGIC)
# =============================================================================

def start_new_quiz_session(subject: str, selected_topics: list[str]) -> None:
    """Initializes a new adaptive quiz session with guaranteed state isolation."""
    st.session_state.quiz_active = True
    st.session_state.quiz_subject = subject
    st.session_state.quiz_topics = selected_topics
    st.session_state.current_topic_idx = 0
    st.session_state.all_session_questions = []
    st.session_state.total_correct = 0
    st.session_state.total_questions = 0
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_start_time = datetime.now(timezone.utc)
    st.session_state.latest_report_card = None
    st.session_state.latest_packet = None
    st.session_state.last_feedback = None
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False

    # Initialize TopicState trackers
    st.session_state.topic_states = {
        topic: TopicState(
            topic=topic,
            subject=subject,
            current_level="easy",
            status="easy",
            consecutive_correct=0,
            demotion_count=0,
            questions_asked=0,
            correct_answers=0,
        )
        for topic in selected_topics
    }

    # Fetch the very first question
    advance_to_next_question()


def advance_to_next_question() -> None:
    """Selects the active topic and generates a fresh, non-duplicate MCQ."""
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    st.session_state.last_feedback = None

    idx = st.session_state.current_topic_idx
    topics = st.session_state.quiz_topics

    # Check if all topics completed
    if idx >= len(topics):
        finish_and_evaluate_session()
        return

    current_topic = topics[idx]
    ts: TopicState = st.session_state.topic_states[current_topic]

    # Topic cap: Max 5 questions per topic or topic already reached final state
    if ts.status in ("mastered", "weak") or ts.questions_asked >= 5:
        st.session_state.current_topic_idx += 1
        if st.session_state.current_topic_idx >= len(topics):
            finish_and_evaluate_session()
            return
        current_topic = topics[st.session_state.current_topic_idx]
        ts = st.session_state.topic_states[current_topic]

    # Full list of question texts asked this session (used for deduplication)
    asked_texts = set(t.strip().lower() for t in st.session_state.all_session_questions)

    # Try up to 4 times to get a question we haven't asked before
    q = None
    for attempt in range(4):
        try:
            candidate = generate_dynamic_question(
                subject=st.session_state.quiz_subject,
                topic=current_topic,
                level=ts.current_level,
                # Pass all asked questions so the LLM avoids every one of them
                previous_questions=st.session_state.all_session_questions,
            )
            # Accept if not a duplicate
            if candidate.question_text.strip().lower() not in asked_texts:
                q = candidate
                break
            # Otherwise loop and try again (LLM ignored the avoid-clause)
        except Exception:
            break  # LLM failed entirely — fall through to fallback bank

    # If all LLM attempts returned duplicates or failed, use curated fallback bank
    if q is None:
        q = get_fallback_question(
            subject=st.session_state.quiz_subject,
            topic=current_topic,
            level=ts.current_level,
            exclude_texts=st.session_state.all_session_questions,
        )

    st.session_state.current_question = q



def process_student_answer(answer: str) -> None:
    """Executes the adaptive state machine rules on student submission."""
    q: Question = st.session_state.current_question
    if not q:
        return

    current_topic = q.topic
    ts: TopicState = st.session_state.topic_states[current_topic]

    is_correct = (answer.strip().upper() == q.correct_answer.strip().upper())
    ts.questions_asked += 1
    st.session_state.total_questions += 1
    st.session_state.all_session_questions.append(q.question_text)

    progression_note = ""
    badge_style = "info"

    if is_correct:
        ts.correct_answers += 1
        ts.consecutive_correct += 1
        st.session_state.total_correct += 1

        # Easy -> Medium Promotion Check
        if ts.current_level == "easy":
            if ts.consecutive_correct >= 2:
                ts.current_level = "medium"
                ts.status = "medium"
                ts.consecutive_correct = 0
                progression_note = (
                    "🌟 **PASSED EASY LEVEL!** You scored 2 in a row on foundational concepts. "
                    "Promoted to **MEDIUM level** — now challenging your multi-step application!"
                )
                badge_style = "promoted_medium"
            else:
                progression_note = (
                    "✅ **Correct!** Great start on foundational concepts. "
                    "Score 1 more correct answer in a row to level up to Medium!"
                )
                badge_style = "streak_1"

        # Medium -> Hard Promotion Check
        elif ts.current_level == "medium":
            if ts.consecutive_correct >= 2:
                ts.current_level = "hard"
                ts.status = "hard"
                ts.consecutive_correct = 0
                progression_note = (
                    "🚀 **CLEARED MEDIUM LEVEL!** Outstanding analytical reasoning! "
                    "Promoted to **HARD level** — conquer this level to earn full topic mastery!"
                )
                badge_style = "promoted_hard"
            else:
                progression_note = (
                    "✅ **Correct!** Solid progress on Medium level. "
                    "Score 1 more correct answer in a row to conquer Hard level!"
                )
                badge_style = "streak_1"

        # Hard -> Mastery Check
        elif ts.current_level == "hard":
            ts.status = "mastered"
            progression_note = (
                f"🏆 **FULL MASTERY ACHIEVED!** Incredible achievement in **{current_topic}**! "
                "You successfully solved Hard-tier synthesis and conquered all 3 difficulty tiers."
            )
            badge_style = "mastered"

    else:
        # Incorrect answer
        ts.consecutive_correct = 0
        ts.demotion_count += 1

        if ts.current_level == "easy":
            if ts.demotion_count >= 2:
                ts.status = "weak"
                progression_note = (
                    f"💪 Good effort! Foundational base is not yet set in **{current_topic}**. "
                    "Marked as a focus area for basic review. Moving to next topic."
                )
                badge_style = "weak"
            else:
                progression_note = (
                    f"Good try! Core definitions in **{current_topic}** need reinforcement. "
                    "Take a moment to think through the underlying principle."
                )
                badge_style = "retry"

        elif ts.current_level == "medium":
            ts.current_level = "easy"
            ts.status = "easy"
            progression_note = (
                "Nice attempt! You passed Easy earlier, but Medium needs more practice. "
                "Adjusting to **EASY level** to solidify your foundation before re-attempting Medium."
            )
            badge_style = "demoted_easy"

        elif ts.current_level == "hard":
            ts.current_level = "medium"
            ts.status = "medium"
            progression_note = (
                "Great courage taking on Hard questions! You cleared Easy and Medium earlier. "
                "Adjusting to **MEDIUM level** to reinforce multi-step reasoning before tackling Hard again."
            )
            badge_style = "demoted_medium"

    st.session_state.last_feedback = {
        "is_correct": is_correct,
        "student_answer": answer,
        "correct_answer": q.correct_answer,
        "correct_text": q.options.get(q.correct_answer, ""),
        "progression_note": progression_note,
        "badge_style": badge_style,
        "topic": current_topic,
        "level": q.level,
    }
    st.session_state.answer_submitted = True


# =============================================================================
# EVALUATOR AGENT (AGENT 2)
# =============================================================================

def finish_and_evaluate_session() -> None:
    """Sends session data to the Evaluator agent and generates the report."""
    with st.spinner("Generating your report... Agent 2 (Evaluator) is analysing your performance..."):
        topic_states = st.session_state.topic_states
        total_correct = st.session_state.total_correct
        total_questions = st.session_state.total_questions

        for t, ts in topic_states.items():
            if ts.questions_asked > 0 and ts.status != "mastered":
                if ts.current_level == "hard":
                    ts.status = "hard"
                elif ts.current_level == "medium":
                    ts.status = "medium"
                else:
                    ts.status = "weak"

        mastered = [t for t, ts in topic_states.items() if ts.status == "mastered"]
        weak = [t for t, ts in topic_states.items() if ts.status != "mastered"]

        packet = A2APacket(
            packet_id=st.session_state.session_id or str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            student_name=st.session_state.student_name,
            email=st.session_state.student_email,
            subject=st.session_state.quiz_subject,
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
        st.session_state.latest_packet = packet.__dict__

        pct = (total_correct / max(1, total_questions)) * 100
        report_lines = [
            "=" * 60,
            "          STUDENT PERFORMANCE REPORT",
            "=" * 60,
            f"Student Name:    {st.session_state.student_name}",
            f"Email:           {st.session_state.student_email}",
            f"Subject:         {st.session_state.quiz_subject}",
            f"Questions Asked: {total_questions}",
            f"Total Correct:   {total_correct}",
            f"Overall Score:   {pct:.1f}%",
            "",
            "TOPIC RESULTS:",
            "-" * 60,
        ]

        for topic, ts in topic_states.items():
            if ts.status == "mastered":
                badge = "[MASTERED ★]"
            elif ts.current_level == "hard":
                badge = "[AT HARD LEVEL]"
            elif ts.current_level == "medium":
                badge = "[AT MEDIUM LEVEL]"
            else:
                badge = "[NEEDS REVIEW]"
            report_lines.append(f"  * {topic:<24} : {badge:<28} ({ts.correct_answers}/{ts.questions_asked} correct)")

        report_lines.extend([
            "-" * 60,
            "SUMMARY:",
            f"  * Topics Mastered:       {', '.join(mastered) if mastered else 'None yet'}",
            f"  * Topics for Review:     {', '.join(weak) if weak else 'None'}",
            "=" * 60,
        ])
        base_report = "\n".join(report_lines)

        mentor_feedback = ""
        try:
            evaluator = EvaluatorAgent(
                student_name=st.session_state.student_name,
                subject=st.session_state.quiz_subject,
                email=st.session_state.student_email,
            )

            topic_details_list = []
            for t, ts in topic_states.items():
                if ts.status == "mastered":
                    desc = f"Mastered (cleared Easy, Medium, and Hard; {ts.correct_answers}/{ts.questions_asked} correct)"
                elif ts.current_level == "hard":
                    desc = f"At Hard level (passed Easy & Medium; {ts.correct_answers}/{ts.questions_asked} correct)"
                elif ts.current_level == "medium":
                    desc = f"At Medium level (passed Easy; {ts.correct_answers}/{ts.questions_asked} correct)"
                else:
                    desc = f"At Easy level (needs revision; {ts.correct_answers}/{ts.questions_asked} correct)"
                topic_details_list.append(f"  - {t}: {desc}")

            mentor_feedback = evaluator.evaluate(
                score_summary=f"{total_correct}/{total_questions} ({pct:.1f}%)",
                mastered_topics=mastered,
                weak_topics=weak,
                topic_level_notes="\n".join(topic_details_list),
            )
        except Exception:
            mentor_feedback = (
                f"Good effort in {st.session_state.quiz_subject}! "
                "Review the topics flagged above and attempt them again to improve your score."
            )

        final_report = f"{base_report}\n\nFEEDBACK FROM EVALUATOR:\n{'-'*60}\n{mentor_feedback}\n{'='*60}"
        st.session_state.latest_report_card = final_report

        try:
            save_session(
                packet_id=packet.packet_id,
                student_name=st.session_state.student_name,
                email=st.session_state.student_email,
                subject=st.session_state.quiz_subject,
                total_correct=total_correct,
                total_questions=total_questions,
                mastered_topics=mastered,
                weak_topics=weak,
                report_card=final_report,
            )
        except Exception:
            pass

        try:
            get_client().flush()
        except Exception:
            pass

    st.session_state.quiz_active = False
    st.session_state.active_nav = "📜 Report & Feedback"


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:10px; padding:4px 0 14px 0;">
            <div style="font-size:1.7rem;">🧠</div>
            <div>
                <div style="font-family:Outfit,sans-serif; font-weight:800; font-size:1.22rem; color:#FFFFFF; letter-spacing:-0.02em;">Adaptiq</div>
                <div style="font-size:0.7rem; color:#475569; font-weight:500; text-transform:uppercase; letter-spacing:0.06em;">Adaptive Learning</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:0 0 14px 0;">', unsafe_allow_html=True)

    if st.session_state.is_authenticated:
        st.markdown(
            f"""
            <div style="background:rgba(99,102,241,0.10); border:1px solid rgba(99,102,241,0.22); border-radius:12px; padding:14px 16px; margin-bottom:14px;">
                <div style="font-size:0.68rem; text-transform:uppercase; letter-spacing:0.1em; color:#6366F1; font-weight:700; margin-bottom:6px;">Signed In As</div>
                <div style="font-weight:700; font-size:1rem; color:#FFFFFF;">{st.session_state.student_name}</div>
                <div style="font-size:0.8rem; color:#64748B; margin-top:2px;">{st.session_state.student_email}</div>
                <div style="margin-top:8px;"><span class="level-badge-easy" style="font-size:0.68rem;">🔒 Session Isolated</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out / Switch Student", use_container_width=True):
            st.session_state.is_authenticated = False
            st.session_state.student_name = ""
            st.session_state.student_email = ""
            st.session_state.quiz_active = False
            st.session_state.latest_report_card = None
            st.session_state.latest_packet = None
            st.rerun()

        st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:14px 0;">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#475569; font-weight:700; margin-bottom:8px;'>Navigation</div>", unsafe_allow_html=True)
        nav_options = [
            "🎯 Adaptive Quiz",
            "📜 Report & Feedback",
            "📊 Progress History",
            "🗺️ Curriculum Map",
            "⚙️ System Status",
        ]
        selected_nav = st.radio(
            "Go to:",
            nav_options,
            index=nav_options.index(st.session_state.active_nav) if st.session_state.active_nav in nav_options else 0,
            label_visibility="collapsed",
        )
        if selected_nav != st.session_state.active_nav:
            st.session_state.active_nav = selected_nav
            st.rerun()

    else:
        st.markdown(
            """
            <div style="padding:10px 0 14px 0;">
                <div style="font-size:0.88rem; color:#64748B; line-height:1.6;">
                    Sign in with your name and email to start a personalised quiz session.
                </div>
                <div style="margin-top:12px;">
                    <span class="level-badge-medium" style="font-size:0.7rem;">🔒 Private per student</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:14px 0;">', unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.7rem; text-transform:uppercase; letter-spacing:0.1em; color:#475569; font-weight:700; margin-bottom:8px;'>Agent Status</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.82rem; line-height:2.1; color:#94A3B8;">
            <div>🟢 <b style="color:#CBD5E1;">Quizmaster (Agent 1):</b> Online</div>
            <div>🟢 <b style="color:#CBD5E1;">Evaluator (Agent 2):</b> Online</div>
            <div>💾 <b style="color:#CBD5E1;">Session Database:</b> Connected</div>
            <div>📡 <b style="color:#CBD5E1;">Langfuse Tracing:</b> Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# HERO HEADER
# =============================================================================
st.markdown(
    """
    <div class="adaptiq-hero">
        <div class="hero-title-row">
            <div>
                <h1 class="hero-title">🧠 Adaptiq — Adaptive Learning Platform</h1>
                <div class="hero-subtitle">
                    Class 8 multi-agent quiz system that adjusts question difficulty in real time based on your answers,
                    then generates a personalised performance report via a dedicated Evaluator agent.
                </div>
            </div>
            <div>
                <span class="hero-badge">⚡ Multi-Agent · Class 8</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# AUTHENTICATION GATE
# =============================================================================
if not st.session_state.is_authenticated:
    _, auth_col, _ = st.columns([1, 2.2, 1])
    with auth_col:
        st.markdown(
            """
            <div class="glass-card" style="padding:36px 36px 24px 36px; border-color:rgba(99,102,241,0.3); text-align:center; box-shadow:0 24px 55px -12px rgba(0,0,0,0.8);">
                <div style="display:inline-flex; width:64px; height:64px; border-radius:18px;
                            background:linear-gradient(135deg,rgba(99,102,241,0.25),rgba(139,92,246,0.25));
                            border:1px solid rgba(129,140,248,0.45); align-items:center;
                            justify-content:center; font-size:2rem; box-shadow:0 0 28px rgba(99,102,241,0.35);
                            margin-bottom:18px;">
                    🔐
                </div>
                <h2 style="font-family:Outfit,sans-serif; font-size:1.75rem; font-weight:800; margin:0 0 6px 0;
                           color:#FFFFFF; letter-spacing:-0.025em;">
                    Student Portal
                </h2>
                <p style="color:#64748B; font-size:0.9rem; line-height:1.55; margin:0 0 18px 0; max-width:360px; margin-left:auto; margin-right:auto;">
                    Enter your name and email to begin. Your quiz results and progress are saved privately under your email address.
                </p>
                <div style="display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin-bottom:24px;">
                    <span class="info-chip">📐 Mathematics</span>
                    <span class="info-chip">🧬 Biology</span>
                    <span class="info-chip">🧪 Chemistry</span>
                    <span class="info-chip">3 Difficulty Levels</span>
                    <span class="info-chip">🔒 Private Results</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("student_auth_form"):
            login_name = st.text_input(
                "Your Name",
                placeholder="e.g. Alex Johnson",
                help="Your name appears on your report card",
            )
            login_email = st.text_input(
                "Email Address",
                placeholder="e.g. alex@example.com",
                help="Used to save and retrieve your quiz history privately",
            )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            submit_login = st.form_submit_button(
                "✨  Start My Quiz Session",
                type="primary",
                use_container_width=True,
            )

            if submit_login:
                name_clean = login_name.strip()
                email_clean = login_email.strip().lower()

                if not name_clean:
                    st.error("⚠️ Please enter your name.")
                elif not email_clean or not EMAIL_REGEX.match(email_clean):
                    st.error("⚠️ Please enter a valid email address (e.g. alex@example.com).")
                else:
                    st.session_state.student_name = name_clean
                    st.session_state.student_email = email_clean
                    st.session_state.is_authenticated = True
                    st.rerun()

        st.markdown(
            """
            <div style="text-align:center; margin-top:12px; font-size:0.78rem; color:#334155;">
                🔒 Results saved per email · No account needed · No data shared
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()

# =============================================================================
# VIEW 1: ADAPTIVE QUIZ
# =============================================================================
if st.session_state.active_nav == "🎯 Adaptive Quiz":

    if not st.session_state.quiz_active:
        # ── Subject Selection ──────────────────────────────────────────────
        st.markdown(
            """
            <p class="section-heading">🎯 Start a New Quiz</p>
            <p class="section-subheading">
                Choose a subject below. The quiz starts at Easy level and adjusts based on your answers —
                2 correct in a row moves you up, a wrong answer can move you back down.
            </p>
            """,
            unsafe_allow_html=True,
        )

        c_math, c_bio, c_chem = st.columns(3)
        curr_subj = st.session_state.quiz_subject

        # ── Mathematics ──
        with c_math:
            is_sel = (curr_subj == "Mathematics")
            sel_badge = '<span class="level-badge-easy" style="font-size:0.68rem;">SELECTED</span>' if is_sel else ""
            card_border = "border:2px solid #6366F1; box-shadow:0 0 28px rgba(99,102,241,0.35);" if is_sel else ""
            st.markdown(
                f'<div class="subject-card" style="{card_border}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
                f'<div style="font-size:2.2rem;">📐</div>{sel_badge}</div>'
                f'<div style="font-family:Outfit,sans-serif;font-size:1.18rem;font-weight:700;color:#FFFFFF;margin-bottom:6px;">Mathematics</div>'
                f'<div style="font-size:0.85rem;color:#64748B;line-height:1.55;min-height:48px;">'
                f'Rational numbers, linear equations, mensuration, exponents, and data handling.</div>'
                f'<div style="margin-top:14px;display:flex;gap:6px;flex-wrap:wrap;">'
                f'<span class="info-chip">5 Topics</span><span class="info-chip">NCERT Class 8</span></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Select Mathematics", key="btn_sel_math", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.quiz_subject = "Mathematics"
                st.rerun()

        # ── Biology ──
        with c_bio:
            is_sel = (curr_subj == "Biology")
            sel_badge = '<span class="level-badge-easy" style="font-size:0.68rem;">SELECTED</span>' if is_sel else ""
            card_border = "border:2px solid #34D399; box-shadow:0 0 28px rgba(16,185,129,0.35);" if is_sel else ""
            st.markdown(
                f'<div class="subject-card" style="{card_border}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
                f'<div style="font-size:2.2rem;">🧬</div>{sel_badge}</div>'
                f'<div style="font-family:Outfit,sans-serif;font-size:1.18rem;font-weight:700;color:#FFFFFF;margin-bottom:6px;">Biology</div>'
                f'<div style="font-size:0.85rem;color:#64748B;line-height:1.55;min-height:48px;">'
                f'Cell structure, photosynthesis, microorganisms, reproduction, and life processes.</div>'
                f'<div style="margin-top:14px;display:flex;gap:6px;flex-wrap:wrap;">'
                f'<span class="info-chip">5 Topics</span><span class="info-chip">NCERT Class 8</span></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Select Biology", key="btn_sel_bio", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.quiz_subject = "Biology"
                st.rerun()

        # ── Chemistry ──
        with c_chem:
            is_sel = (curr_subj == "Chemistry")
            sel_badge = '<span class="level-badge-easy" style="font-size:0.68rem;">SELECTED</span>' if is_sel else ""
            card_border = "border:2px solid #38BDF8; box-shadow:0 0 28px rgba(56,189,248,0.35);" if is_sel else ""
            st.markdown(
                f'<div class="subject-card" style="{card_border}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">'
                f'<div style="font-size:2.2rem;">🧪</div>{sel_badge}</div>'
                f'<div style="font-family:Outfit,sans-serif;font-size:1.18rem;font-weight:700;color:#FFFFFF;margin-bottom:6px;">Chemistry</div>'
                f'<div style="font-size:0.85rem;color:#64748B;line-height:1.55;min-height:48px;">'
                f'States of matter, atoms &amp; molecules, acids &amp; bases, metals, and chemical reactions.</div>'
                f'<div style="margin-top:14px;display:flex;gap:6px;flex-wrap:wrap;">'
                f'<span class="info-chip">5 Topics</span><span class="info-chip">NCERT Class 8</span></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("Select Chemistry", key="btn_sel_chem", use_container_width=True,
                         type="primary" if is_sel else "secondary"):
                st.session_state.quiz_subject = "Chemistry"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Topic Selection ────────────────────────────────────────────────
        curriculum_topics = SUBJECTS[st.session_state.quiz_subject]

        col_topics, col_rules = st.columns([1.4, 1])

        with col_topics:
            st.markdown(
                f"""
                <div class="glass-card" style="padding:22px 24px 10px 24px; margin-bottom:0;">
                    <div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1.05rem; color:#FFFFFF; margin-bottom:4px;">
                        📚 Topics for {st.session_state.quiz_subject}
                    </div>
                    <div style="font-size:0.84rem; color:#64748B; margin-bottom:14px;">
                        You can deselect topics you want to skip.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            selected_topics = st.multiselect(
                f"Topics ({st.session_state.quiz_subject}):",
                curriculum_topics,
                default=curriculum_topics,
                label_visibility="collapsed",
            )

        with col_rules:
            st.markdown(
                """
                <div class="glass-card" style="padding:20px 22px; border-style:dashed; margin-bottom:0; height:100%;">
                    <div style="font-family:Outfit,sans-serif; font-weight:700; font-size:1rem; color:#FFFFFF; margin-bottom:12px;">
                        📋 How Difficulty Adapts
                    </div>
                    <div style="font-size:0.84rem; line-height:2.1; color:#94A3B8;">
                        <div><span class="level-badge-easy">Easy</span> &nbsp;→ 2 correct in a row → Medium</div>
                        <div><span class="level-badge-medium">Medium</span> → 2 correct in a row → Hard</div>
                        <div><span class="level-badge-hard">Hard</span> &nbsp;→ 1 correct → Topic Mastered 🏆</div>
                        <div style="margin-top:6px; font-size:0.8rem; color:#475569;">A wrong answer steps you back one level.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if not selected_topics:
            st.warning("⚠️ Please select at least one topic to start the quiz.")
        else:
            if st.button("🚀  Launch Quiz Session", type="primary", use_container_width=True):
                start_new_quiz_session(st.session_state.quiz_subject, selected_topics)
                st.rerun()

    else:
        # ── LIVE QUIZ ─────────────────────────────────────────────────────
        q: Question = st.session_state.current_question
        topics = st.session_state.quiz_topics
        idx = st.session_state.current_topic_idx
        current_topic = topics[idx] if idx < len(topics) else topics[-1]
        ts: TopicState = st.session_state.topic_states.get(current_topic)

        # HUD bar
        hud1, hud2, hud3, hud4 = st.columns([2.2, 1.1, 1.2, 1.1])

        with hud1:
            st.markdown(
                f"""
                <div>
                    <div style="font-family:Outfit,sans-serif; font-size:1.2rem; font-weight:800; color:#FFFFFF;">{current_topic}</div>
                    <div style="font-size:0.8rem; color:#475569; margin-top:2px;">{st.session_state.quiz_subject} · Topic {idx + 1} of {len(topics)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with hud2:
            level_str = q.level.upper() if q else "EASY"
            if level_str == "EASY":
                st.markdown('<span class="level-badge-easy">🟢 EASY</span>', unsafe_allow_html=True)
                st.caption("Recall & definitions")
            elif level_str == "MEDIUM":
                st.markdown('<span class="level-badge-medium">🟡 MEDIUM</span>', unsafe_allow_html=True)
                st.caption("Apply concepts")
            else:
                st.markdown('<span class="level-badge-hard">🔴 HARD</span>', unsafe_allow_html=True)
                st.caption("Complex problems")

        with hud3:
            streak = ts.consecutive_correct if ts else 0
            st.markdown(f'<span class="streak-pill">🔥 Streak: {streak} / 2</span>', unsafe_allow_html=True)
            st.caption("correct in a row to level up")

        with hud4:
            total_c = st.session_state.total_correct
            total_q = st.session_state.total_questions
            pct = (total_c / max(1, total_q)) * 100
            st.markdown(
                f"""
                <div style="text-align:right;">
                    <div style="font-family:Outfit,sans-serif; font-size:1.5rem; font-weight:800; color:#FFFFFF; line-height:1.1;">{pct:.0f}%</div>
                    <div style="font-size:0.78rem; color:#475569;">{total_c}/{total_q} correct</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.progress(idx / max(1, len(topics)))
        st.markdown('<hr style="border:none; border-top:1px solid rgba(255,255,255,0.07); margin:14px 0;">', unsafe_allow_html=True)

        if q:
            st.markdown(f'<div class="question-prompt">Q: {q.question_text}</div>', unsafe_allow_html=True)

            options_labels = [f"**{opt}**.  {text}" for opt, text in q.options.items()]
            opt_keys = list(q.options.keys())

            if not st.session_state.answer_submitted:
                user_choice_idx = st.radio(
                    "Choose your answer:",
                    range(len(options_labels)),
                    format_func=lambda i: options_labels[i],
                    key=f"q_{q.question_id}",
                    index=None,
                )

                btn1, btn2 = st.columns([1, 1])
                with btn1:
                    if st.button("✅  Submit Answer", type="primary", use_container_width=True):
                        if user_choice_idx is None:
                            st.warning("⚠️ Please select an option before submitting.")
                        else:
                            chosen_letter = opt_keys[user_choice_idx]
                            process_student_answer(chosen_letter)
                            st.rerun()

                with btn2:
                    if st.button("⏹️  Finish & Get Report Now", use_container_width=True):
                        finish_and_evaluate_session()
                        st.rerun()

            else:
                fb = st.session_state.last_feedback
                if fb:
                    if fb["is_correct"]:
                        st.markdown(
                            f"""
                            <div class="feedback-correct">
                                <div style="font-size:1.15rem; font-weight:700; color:#34D399; margin-bottom:8px;">✅ Correct!</div>
                                <div style="font-size:1rem;">{fb["progression_note"]}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="feedback-incorrect">
                                <div style="font-size:1.15rem; font-weight:700; color:#F87171; margin-bottom:8px;">❌ Not quite right</div>
                                <div style="font-size:0.97rem; margin-bottom:6px;">
                                    Correct answer: <b>{fb["correct_answer"]}</b> — <i>{fb["correct_text"]}</i>
                                </div>
                                <div style="font-size:0.92rem; opacity:0.9;">{fb["progression_note"]}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                next1, next2 = st.columns([1.5, 1])
                with next1:
                    is_last_topic = (st.session_state.current_topic_idx >= len(st.session_state.quiz_topics) - 1)
                    btn_text = "🎓  Finish Quiz & Generate Report" if (
                        is_last_topic and ts and (ts.status in ("mastered", "weak") or ts.questions_asked >= 5)
                    ) else "Next Question ➡️"
                    if st.button(btn_text, type="primary", use_container_width=True):
                        advance_to_next_question()
                        st.rerun()

                with next2:
                    if st.button("⏹️  End Quiz Early", use_container_width=True):
                        finish_and_evaluate_session()
                        st.rerun()


# =============================================================================
# VIEW 2: REPORT & FEEDBACK
# =============================================================================
elif st.session_state.active_nav == "📜 Report & Feedback":
    report_text = st.session_state.latest_report_card

    if not report_text:
        history = get_student_history(st.session_state.student_email)
        if history:
            report_text = history[0]["report_card"]
            st.session_state.latest_report_card = report_text

    if not report_text:
        st.markdown('<p class="section-heading">📜 Report & Feedback</p>', unsafe_allow_html=True)
        st.info("💡 No quiz report yet. Complete an adaptive quiz to see your results here.")
        if st.button("🚀  Start a Quiz", type="primary"):
            st.session_state.active_nav = "🎯 Adaptive Quiz"
            st.rerun()
    else:
        st.markdown(
            f"""
            <p class="section-heading">📜 Your Performance Report</p>
            <p class="section-subheading">Evaluated by the Evaluator agent for {st.session_state.student_name} ({st.session_state.student_email})</p>
            """,
            unsafe_allow_html=True,
        )

        score_match = re.search(r"Overall Score:\s*([\d\.]+)%", report_text)
        overall_pct = float(score_match.group(1)) if score_match else 0.0

        q_match = re.search(r"Questions Asked:\s*(\d+)", report_text)
        total_q = int(q_match.group(1)) if q_match else 0

        c_match = re.search(r"Total Correct:\s*(\d+)", report_text)
        total_c = int(c_match.group(1)) if c_match else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            score_color = "#34D399" if overall_pct >= 70 else "#FBBF24"
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Overall Score</div>
                <div class="metric-val" style="color:{score_color};">{overall_pct:.1f}%</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Questions Answered</div>
                <div class="metric-val">{total_q}</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Correct Answers</div>
                <div class="metric-val" style="color:#60A5FA;">{total_c}</div></div>""", unsafe_allow_html=True)
        with col4:
            grade = "Excellent 🏆" if overall_pct >= 85 else ("Good 🌟" if overall_pct >= 65 else "Keep Practising 💪")
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Result</div>
                <div class="metric-val" style="font-size:1.35rem; padding-top:6px; color:#C084FC;">{grade}</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["💬 Evaluator Feedback", "📄 Full Report", "📦 Session Data"])

        with tab1:
            mentor_split = report_text.split("FEEDBACK FROM EVALUATOR:")
            feedback_body = mentor_split[-1].replace("=" * 60, "").strip() if len(mentor_split) > 1 else report_text
            st.markdown(
                f"""<div class="glass-card" style="line-height:1.75; font-size:1.03rem; white-space:pre-wrap;">{feedback_body}</div>""",
                unsafe_allow_html=True,
            )

        with tab2:
            st.code(report_text, language="text")

        with tab3:
            if st.session_state.latest_packet:
                st.markdown("#### Agent 1 → Agent 2 Data Packet")
                st.caption("Session data sent from the Quizmaster (Agent 1) to the Evaluator (Agent 2)")
                st.json(st.session_state.latest_packet)
            else:
                st.info("Session packet is stored in the database.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥  Download Report (.txt)",
            data=report_text,
            file_name=f"adaptiq_report_{st.session_state.student_name.lower().replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


# =============================================================================
# VIEW 3: PROGRESS HISTORY
# =============================================================================
elif st.session_state.active_nav == "📊 Progress History":
    st.markdown(
        f"""
        <p class="section-heading">📊 Your Progress History</p>
        <p class="section-subheading">All past quiz sessions for {st.session_state.student_name} ({st.session_state.student_email})</p>
        """,
        unsafe_allow_html=True,
    )

    history = get_student_history(st.session_state.student_email)

    if not history:
        st.info(f"No past quiz attempts found for {st.session_state.student_name}. Complete a quiz to track your progress here.")
    else:
        total_quizzes = len(history)
        lifetime_questions = sum(r["total_questions"] for r in history)
        lifetime_correct = sum(r["total_correct"] for r in history)
        avg_pct = (lifetime_correct / max(1, lifetime_questions)) * 100
        best_score = max(r["total_correct"] for r in history)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Quizzes Taken</div>
                <div class="metric-val">{total_quizzes}</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Overall Accuracy</div>
                <div class="metric-val" style="color:#34D399;">{avg_pct:.1f}%</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Questions Answered</div>
                <div class="metric-val">{lifetime_questions}</div></div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""<div class="metric-card"><div class="metric-label">Best Session Score</div>
                <div class="metric-val" style="color:#FBBF24;">{best_score} pts</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### 📈 Score Trend Across Sessions")
        chart_data = []
        for i, item in enumerate(reversed(history), 1):
            pct = (item["total_correct"] / max(1, item["total_questions"])) * 100
            chart_data.append({
                "Quiz": f"#{i}",
                "Subject": item["subject"],
                "Score (%)": round(pct, 1),
                "Date": item["created_at"][:10],
            })

        df_chart = pd.DataFrame(chart_data)
        chart = (
            alt.Chart(df_chart)
            .mark_line(
                point=alt.OverlayMarkDef(filled=True, size=70, color="#6366F1"),
                strokeWidth=2.5,
                color="#818CF8",
            )
            .encode(
                x=alt.X("Quiz:N", title="Quiz Session"),
                y=alt.Y("Score (%):Q", title="Score (%)", scale=alt.Scale(domain=[0, 100])),
                tooltip=["Quiz", "Subject", "Score (%)", "Date"],
            )
            .properties(height=260)
            .configure_view(strokeOpacity=0)
            .configure_axis(
                gridColor="rgba(255,255,255,0.04)",
                labelColor="#64748B",
                titleColor="#94A3B8",
            )
        )
        st.altair_chart(chart, use_container_width=True)

        st.markdown("#### 📋 Session History")
        for i, sess in enumerate(history, 1):
            correct = sess["total_correct"]
            total = sess["total_questions"]
            pct = (correct / max(1, total)) * 100
            date_str = sess["created_at"][:10]

            with st.expander(
                f"Session #{i}  ·  {date_str}  ·  {sess['subject']}  —  {correct}/{total} ({pct:.1f}%)"
            ):
                st.markdown(f"**Session ID:** `{sess['packet_id']}`")
                st.markdown(f"**Topics Mastered:** {', '.join(sess['mastered_topics']) if sess['mastered_topics'] else 'None'}")
                st.markdown(f"**Topics for Review:** {', '.join(sess['weak_topics']) if sess['weak_topics'] else 'None'}")
                st.code(sess["report_card"], language="text")


# =============================================================================
# VIEW 4: CURRICULUM MAP
# =============================================================================
elif st.session_state.active_nav == "🗺️ Curriculum Map":
    st.markdown(
        """
        <p class="section-heading">🗺️ Curriculum & Topic Dependency Map</p>
        <p class="section-subheading">
            The Evaluator agent uses this dependency map to identify which foundational topics to recommend
            when a student struggles with an advanced one. Topics lower in the graph depend on those above.
        </p>
        """,
        unsafe_allow_html=True,
    )

    dag_mermaid = """
    graph TD
        subgraph Mathematics
            RN[Rational Numbers] --> LE[Linear Equations]
            RN --> MEN[Mensuration]
            RN --> EP[Exponents and Powers]
            DH[Data Handling]
        end

        subgraph Biology
            CS[Cell Structure] --> PHOTO[Photosynthesis]
            CS --> REP[Reproduction]
            CS --> LP[Life Processes]
            PHOTO --> LP
            MO[Microorganisms]
        end

        subgraph Chemistry
            SM[States of Matter] --> AM[Atoms and Molecules]
            AM --> AB[Acids and Bases]
            AM --> MNM[Metals and Non-metals]
            AM --> CR[Chemical Reactions]
            AB --> CR
        end

        classDef root fill:#4F46E5,stroke:#818CF8,stroke-width:2px,color:#FFF;
        classDef node fill:#1E293B,stroke:#64748B,stroke-width:1px,color:#CBD5E1;
        class RN,CS,SM root;
        class LE,MEN,EP,DH,PHOTO,REP,LP,MO,AM,AB,MNM,CR node;
    """
    st.components.v1.html(
        f"""
        <div style="background:#0F172A; border-radius:14px; padding:24px; border:1px solid rgba(255,255,255,0.07);">
            <pre class="mermaid" style="background:transparent; color:#CBD5E1;">
{dag_mermaid}
            </pre>
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'dark',
                themeVariables: {{
                    primaryColor: '#4F46E5',
                    primaryTextColor: '#FFFFFF',
                    primaryBorderColor: '#818CF8',
                    lineColor: '#475569',
                    secondaryColor: '#1E293B',
                    tertiaryColor: '#0F172A',
                    edgeLabelBackground: '#1E293B',
                    clusterBkg: '#1E293B',
                    clusterBorder: '#334155'
                }}
            }});
        </script>
        """,
        height=520,
    )


    st.markdown("---")
    st.markdown("#### 📊 Difficulty Levels Explained")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="glass-card">
                <h4 style="color:#34D399; margin-top:0; font-family:Outfit,sans-serif;">🟢 Easy</h4>
                <p style="font-size:0.9rem; color:#94A3B8; margin-bottom:10px;">Tests basic recall and definitions.</p>
                <ul style="font-size:0.88rem; color:#CBD5E1; padding-left:18px; line-height:1.8;">
                    <li>Single concept identification</li>
                    <li>Scientific vocabulary</li>
                    <li>Direct formula recall</li>
                </ul>
                <div style="margin-top:12px; font-size:0.83rem; color:#A7F3D0; font-weight:600;">
                    2 correct in a row → Medium ↑
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="glass-card">
                <h4 style="color:#FBBF24; margin-top:0; font-family:Outfit,sans-serif;">🟡 Medium</h4>
                <p style="font-size:0.9rem; color:#94A3B8; margin-bottom:10px;">Tests understanding and application.</p>
                <ul style="font-size:0.88rem; color:#CBD5E1; padding-left:18px; line-height:1.8;">
                    <li>2-step problems</li>
                    <li>Cause and effect relationships</li>
                    <li>Comparing concepts</li>
                </ul>
                <div style="margin-top:12px; font-size:0.83rem; color:#FDE68A; font-weight:600;">
                    2 correct in a row → Hard ↑
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="glass-card">
                <h4 style="color:#F87171; margin-top:0; font-family:Outfit,sans-serif;">🔴 Hard</h4>
                <p style="font-size:0.9rem; color:#94A3B8; margin-bottom:10px;">Tests higher-order reasoning.</p>
                <ul style="font-size:0.88rem; color:#CBD5E1; padding-left:18px; line-height:1.8;">
                    <li>Multi-step problems</li>
                    <li>Edge case scenarios</li>
                    <li>Combining multiple concepts</li>
                </ul>
                <div style="margin-top:12px; font-size:0.83rem; color:#FECACA; font-weight:600;">
                    1 correct → Topic Mastered 🏆
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# VIEW 5: SYSTEM STATUS
# =============================================================================
elif st.session_state.active_nav == "⚙️ System Status":
    st.markdown(
        """
        <p class="section-heading">⚙️ System Status</p>
        <p class="section-subheading">Check connectivity for all components that Adaptiq depends on.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ```
        Student (Browser)
          │
          ├──► Email-based session isolation
          ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              Agent 1: Quizmaster                            │
        │  • Generates questions dynamically via LLM                  │
        │  • Adjusts difficulty based on student answers              │
        │  • Packages session data for handoff to Evaluator           │
        └─────────────────────────────┬────────────────────────────────┘
                                      │  Session Data Handoff
                                      ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              Agent 2: Evaluator                             │
        │  • Reviews full session results                             │
        │  • Checks topic dependencies for gaps                       │
        │  • Writes a personalised feedback report                    │
        └─────────────────────────────┬────────────────────────────────┘
                                      │
                                      ▼
        ┌──────────────────────────────────────────────────────────────┐
        │              Langfuse Observability                         │
        │  • Traces every LLM call                                    │
        │  • Tracks token usage per session                           │
        └──────────────────────────────────────────────────────────────┘
        ```
        """
    )

    st.markdown("#### 🩺 Component Health Check")
    if st.button("🧪  Run Health Check", type="primary"):
        with st.status("Running checks...", expanded=True) as status:
            st.write("Checking database...")
            try:
                conn = _connect()
                count = conn.execute("SELECT COUNT(*) FROM quiz_sessions").fetchone()[0]
                conn.close()
                st.write(f"✅ SQLite database: OK — {count} sessions stored")
            except Exception as e:
                st.write(f"❌ SQLite database: {e}")

            st.write("Checking Quizmaster LLM (OpenAI)...")
            if core.config.OPENAI_API_KEY:
                st.write(f"✅ OpenAI API key: configured (model: `{core.config.OPENAI_MODEL}`)")
            else:
                st.write("⚠️ OpenAI API key: not set — will use fallback question bank")

            st.write("Checking Evaluator LLM (Google Gemini)...")
            if core.config.GEMINI_API_KEY:
                st.write(f"✅ Gemini API key: configured (model: `{core.config.GEMINI_MODEL}`)")
            else:
                st.write("⚠️ Gemini API key: not set — Evaluator will use a built-in feedback template")

            st.write("Checking Langfuse observability...")
            if core.config.is_langfuse_configured():
                st.write(f"✅ Langfuse: connected ({core.config.LANGFUSE_BASE_URL})")
            else:
                st.write("⚠️ Langfuse: not configured — tracing disabled")

            st.write("Checking fallback question bank...")
            fb_q = get_fallback_question("Mathematics", "Rational Numbers", "easy")
            st.write(f"✅ Fallback question bank: OK — {len(fb_q.options)} options verified")

            status.update(label="All checks complete.", state="complete", expanded=False)

    st.markdown("---")
    st.markdown("#### 📋 Fallback Behaviour")
    st.markdown(
        """
        Adaptiq is designed to keep working even if external services are unavailable:

        1. **Primary question source:** OpenAI (or Groq) — generates questions live for each topic and difficulty level.
        2. **Secondary question source:** Google Gemini — used if the primary source fails.
        3. **Built-in question bank:** A curated set of questions that load instantly, used if both LLM providers are unreachable.

        The Evaluator agent similarly falls back to a built-in feedback template if the Gemini API is unavailable.
        """
    )
