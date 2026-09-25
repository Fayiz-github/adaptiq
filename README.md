# 🧠 Adaptiq — AI-Powered Adaptive Quiz Platform

> Two AI agents, one mission: truly personalised learning.

Adaptiq is a multi-agent adaptive quiz system where **Agent 1 (Quizmaster)** generates and delivers questions that adjust in real-time to the student's performance, then hands off a structured packet to **Agent 2 (Evaluator)** via the **A2A (Agent-to-Agent) protocol** for deep, personalised report generation.

---

## ✨ What Makes It Different

| Feature | Details |
|--------|---------|
| 🤖 **Two-Agent Architecture** | Quizmaster (Groq/LLaMA) + Evaluator (Gemini) communicate via A2A |
| 🎯 **Adaptive Difficulty** | Questions promote/demote across Easy → Medium → Hard per topic |
| 🧬 **Episodic Memory** | Evaluator recalls past sessions — *"You were weak in Exponents last time too"* |
| 📊 **Personalised Reports** | Gemini writes evidence-based, motivating report cards |
| 🔗 **A2A Protocol** | Clean JSON packet interface between agents — no shared state |
| 🗃️ **Persistent History** | SQLite stores all sessions for long-term improvement tracking |

---

## 🏗️ Architecture

```
Student
  │
  ▼
┌─────────────────────────────────────────┐
│         Agent 1: Quizmaster             │
│  • Generates 60-question pool (Groq)    │
│  • Runs adaptive quiz (LangGraph)       │
│  • Tracks topic mastery per student     │
│  • Builds structured A2A packet         │
└────────────────┬────────────────────────┘
                 │  A2A Packet (HTTP/JSON)
                 ▼
┌─────────────────────────────────────────┐
│         Agent 2: Evaluator              │
│  • Receives packet via FastAPI server   │
│  • Reads episodic memory (past sessions)│
│  • Calls Gemini to write report card    │
│  • Saves session to SQLite              │
└────────────────┬────────────────────────┘
                 │  Report Card (text)
                 ▼
             Student
```

---

## 🧩 Adaptive Engine — How It Works

Each topic starts at **Easy** and follows these rules:

```
✅ 2 correct in a row  →  PROMOTE to next level
❌ Wrong at Easy       →  Stay (retry), 3rd fail = WEAK
❌ Wrong above Easy    →  DEMOTE one level
❌ 2 demotions + wrong →  Topic marked WEAK
✅ Correct at Hard     →  Topic MASTERED 🏆
```

**Quiz Flow (8 Steps):**

| Step | What Happens |
|------|-------------|
| **Step 1** | Student enters name & picks subject. All 60 questions generated in one LLM call. |
| **Step 2** | Easy Round — one easy question per topic (5 questions) |
| **Step 3** | Medium Round — topics that passed Easy move up |
| **Step 4** | Hard Round — topics that passed Medium move up |
| **Step 5** | Mastery Verification — PENDING_MASTERY topics get one final Hard re-test |
| **Step 6** | Retention Round — MASTERED topics get a spaced-repetition recap question |
| **Step 7** | A2A Handoff — session data packaged as JSON, sent to Agent 2 |
| **Step 8** | Report Card — Gemini analyses the packet and writes a personalised report |

> **Total LLM calls per session: exactly 2** — one at start, one at end. Zero mid-quiz calls.

Subjects supported: **Mathematics**, **Biology**, **Chemistry** (Class 8)

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent 1 LLM | [Groq](https://groq.com) — `llama-3.3-70b-versatile` |
| Agent 2 LLM | [Google Gemini](https://ai.google.dev) — `gemini-2.0-flash` |
| Quiz State Machine | [LangGraph](https://github.com/langchain-ai/langgraph) |
| A2A Server | [FastAPI](https://fastapi.tiangolo.com) |
| A2A Client | [httpx](https://www.python-httpx.org) |
| Memory Store | SQLite (via `sqlite3`) |
| Package Manager | [uv](https://github.com/astral-sh/uv) |
| Testing | [pytest](https://pytest.org) |

---

## 📁 Project Structure

```
adaptiq/
├── core/
│   ├── config.py              # All env vars & constants
│   ├── models.py              # Shared data models (Question, A2APacket, QuizState…)
│   ├── database.py            # Raw SQLite CRUD operations
│   └── memory.py              # All 4 memory types: working, in-context, long-term, episodic
│
├── quizmaster/
│   ├── question_generator.py  # Groq call — generates 60-question pool
│   ├── quiz_engine.py         # LangGraph adaptive state machine
│   ├── agent.py               # QuizmasterAgent — orchestrates the full session
│   └── a2a_client.py          # HTTP client — sends packet to Evaluator
│
├── evaluator/
│   ├── report_generator.py    # Gemini call — writes personalised report card
│   ├── agent.py               # EvaluatorAgent — processes packet + saves session
│   └── a2a_server.py          # FastAPI server — receives A2A packets
│
├── tests/
│   ├── test_database.py       # Tests: session CRUD + episodic memory queries
│   └── test_quiz_engine.py    # Tests: all 5 adaptive routing conditions
│
├── app.py                     # Entry point — launches both agents
└── .env                       # API keys (not committed)
```

---

## 🚀 Getting Started

### 1. Clone & install

```bash
git clone https://github.com/Fayiz-github/adaptiq.git
cd adaptiq
uv sync
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

> Get your free keys: [Groq Console](https://console.groq.com) · [Google AI Studio](https://aistudio.google.com)

### 3. Run the tests

```bash
uv run pytest tests/ -v
```

### 4. Start a quiz session

```bash
# Terminal 1 — start the Evaluator server
uv run python -m evaluator.a2a_server

# Terminal 2 — run the quiz
uv run python app.py
```

---

## 🧪 Test Coverage

```
tests/test_database.py      ✅ 9 tests — session CRUD + episodic memory
tests/test_quiz_engine.py   ✅ 8 tests — all 5 adaptive routing conditions
```

---

## 📖 Memory Architecture

Adaptiq uses all **4 types of AI agent memory**:

| Type | How it is used |
|------|----------------|
| **Working** | Live `QuizState` dict — managed by LangGraph during the session |
| **In-context** | The A2A packet passed directly to Gemini's prompt |
| **Long-term** | Completed sessions saved to SQLite permanently |
| **Episodic** | Past-session recall — Evaluator references history in the report |

---

## 🤝 A2A Protocol

Agent 1 sends a structured JSON packet to Agent 2 over HTTP:

```json
{
  "packet_id": "uuid",
  "student_name": "Arjun",
  "subject": "Mathematics",
  "topic_states": { "Rational Numbers": { "status": "mastered" } },
  "question_history": [ { "topic": "...", "is_correct": true } ],
  "weighted_scores": { "Rational Numbers": 3, "Exponents & Powers": 1 },
  "total_correct": 9,
  "total_questions": 15,
  "prerequisite_map": { "Linear Equations": ["Rational Numbers"] }
}
```

---

## 📄 License

MIT — free to use, modify, and build on.

---

<p align="center">Built with 🤖 Groq + Gemini + LangGraph</p>
