# 🧠 Adaptiq — AI-Powered Adaptive Quiz & Evaluation Platform

> Two autonomous AI agents, one mission: truly personalised, mastery-based learning with complete observability.

Adaptiq is a multi-agent educational platform built for Class 8 curriculum (Mathematics, Biology, Chemistry). **Agent 1 (Quizmaster)** generates dynamic, single-concept MCQs and adapts difficulty in real time based on student answers. At the end of the session, it packages the telemetry into an **A2A (Agent-to-Agent) protocol packet** and dispatches it to **Agent 2 (Evaluator)**, which analyses performance against past session history (**Episodic Memory**) and prescribes concrete cognitive study strategies.

Full end-to-end observability is instrumented via **[Langfuse](https://langfuse.com)**, tracking token usage, costs, latencies, and agent transitions tied directly to each student's verified email.

---

## ✨ Key Features

| Feature | Details |
| :--- | :--- |
| 🤖 **Two-Agent Architecture** | Quizmaster (OpenAI / Groq) + Evaluator (Google Gemini) communicating via structured A2A protocol. |
| 🎯 **Adaptive Difficulty Engine** | Real-time state machine scaling through **Easy** (Definitions) $\to$ **Medium** (Application) $\to$ **Hard** (Synthesis). |
| 🎲 **2-in-a-Row Promotion Rule** | Requires 2 consecutive correct answers to level up, reducing lucky-guess distortion from 25% to 6.25%. |
| 🛡️ **2-Loop Demotion Safeguard** | Graceful recovery on errors with lifetime error counters to prevent student fatigue. |
| 🧬 **Episodic & Long-Term Memory** | SQLite persistence isolates session history by verified email to detect recurring conceptual weaknesses over time. |
| 🔍 **Full Observability (Langfuse)** | Complete tracing from student onboarding to final evaluation, indexing costs and prompts by student email. |
| 🛡️ **Dual-Provider Resilience** | Automatic failover between OpenAI and Google Gemini with an offline deterministic mentor fallback. |
| 🗂️ **Cascading Prerequisite DAG** | Directed Acyclic Graph mapping foundational dependencies (e.g. *Atoms & Molecules* before *Chemical Reactions*). |

---

## 🏗️ Architecture & Telemetry Pipeline

```
Student (CLI Entry Point: app.py)
  │
  ├─► Enter Name & Verified Email (user_id)
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent 1: Quizmaster                       │
│  • Dynamically generates MCQs with anti-repetition filter   │
│  • Manages 3-tier adaptive state machine (LangGraph logic)  │
│  • Tracks topic mastery & consecutive answer streaks        │
│  • Packages session telemetry into A2APacket                │
└──────────────────────────────┬──────────────────────────────┘
                               │  A2A Packet (HTTP JSON / Local)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent 2: Evaluator                        │
│  • Receives telemetry packet (FastAPI endpoint /evaluate)   │
│  • Recalls past session weaknesses (Episodic Memory)        │
│  • Evaluates cascading prerequisite bottlenecks (DAG)       │
│  • Synthesizes pedagogical report card (Gemini 2.0 / Flash) │
│  • Persists finalized record to SQLite (results.db)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Langfuse Observability & Tracing                │
│  • Trace: Student Adaptive Quiz Session                     │
│  • User: student@example.com (Lifetime token & cost tracking)│
│  • Session: UUID timeline of questions, answers & report     │
│  • Generations: Prompts, completions, latencies & tokens    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Adaptive Difficulty Engine

Each curriculum topic begins at **Easy** and follows strict pedagogical rules:

```
✅ 2 correct in a row at Easy   ──► Promoted to MEDIUM
✅ 2 correct in a row at Medium ──► Promoted to HARD
✅ 1 correct at Hard            ──► Topic MASTERED 🏆
❌ Mistake at Medium or Hard    ──► Demoted 1 level to reinforce foundation
❌ 2 consecutive fails at Easy  ──► Topic marked WEAK (Focus Area)
```

### Supported Curriculum Topics (Class 8)
* **Mathematics:** Rational Numbers, Linear Equations, Mensuration, Exponents & Powers, Data Handling
* **Biology:** Cell Structure, Photosynthesis, Reproduction in Animals, Microorganisms, Life Processes
* **Chemistry:** States of Matter, Atoms & Molecules, Chemical Reactions, Acids & Bases, Metals & Non-metals

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Agent 1 LLM** | [OpenAI](https://platform.openai.com) / [Groq](https://groq.com) | Dynamic MCQ generation with anti-repetition memory |
| **Agent 2 LLM** | [Google Gemini](https://ai.google.dev) (`gemini-2.0-flash` / `gemini-3.8-flash`) | Deep pedagogical diagnosis and qualitative study plans |
| **Quiz State Machine** | [LangGraph](https://github.com/langchain-ai/langgraph) / Python State Machine | Adaptive promotion/demotion engine |
| **A2A Server** | [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) | Microservice endpoint for Agent-to-Agent handoff |
| **A2A Client** | [httpx](https://www.python-httpx.org) | Asynchronous HTTP client for telemetry transport |
| **Observability** | [Langfuse](https://langfuse.com) (SDK v2/v4) | Distributed tracing, session tracking & cost attribution |
| **Persistence** | SQLite (`sqlite3`) | Permanent storage of student attempts and episodic memory |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) | High-performance Python package management |

---

## 📁 Project Structure

```
adaptiq/
├── core/
│   ├── config.py              # Environment variable loader & Langfuse region setup
│   ├── models.py              # Dataclasses: Question, TopicState, A2APacket, DAG map
│   ├── database.py            # SQLite CRUD operations & session schema
│   └── memory.py              # Working, in-context, long-term & episodic memory queries
│
├── quizmaster/
│   ├── question_generator.py  # Dynamic LLM MCQ generator with dual-provider fallback
│   ├── quiz_engine.py         # LangGraph adaptive state machine
│   ├── agent.py               # QuizmasterAgent orchestrator (@observe agent node)
│   └── a2a_client.py          # HTTP client transmitting A2A packets
│
├── evaluator/
│   ├── report_generator.py    # Gemini report generator with study strategy guidance
│   ├── agent.py               # EvaluatorAgent synthesising feedback + episodic memory
│   └── a2a_server.py          # FastAPI ASGI microservice (@observe agent server)
│
├── app.py                     # Main interactive CLI menu with student login & tracing
├── pyproject.toml             # uv dependencies & project metadata
└── .env                       # API credentials (git-ignored)
```

---

## 🚀 Getting Started

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Fayiz-github/adaptiq.git
cd adaptiq
uv sync
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# ── Agent 1 (Question Generation) ─────────────────────────────
OPENAI_API_KEY=your_openai_or_groq_key_here
OPENAI_MODEL=gpt-5-nano

# ── Agent 2 (Evaluation & Feedback) ───────────────────────────
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3.8-flash

# ── Database ──────────────────────────────────────────────────
DB_PATH=results.db

# ── Langfuse Observability & Tracing (Free Cloud / Self-Hosted)
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key_here
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key_here
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com  # Use us.cloud.langfuse.com for US or cloud.langfuse.com for EU
```

> **API Key Portals:**
> * Groq: [console.groq.com](https://console.groq.com)
> * Google Gemini: [aistudio.google.com](https://aistudio.google.com)
> * Langfuse Cloud: [cloud.langfuse.com](https://cloud.langfuse.com) (Free 50,000 observations/month)

### 3. Launch the Application

You can run Adaptiq either in monolithic in-process mode or as two decoupled microservices:

#### Option A: Interactive CLI (All-in-One)
```bash
uv run python app.py
```
1. Enter student display name and email.
2. Select **1** to start an adaptive quiz, or **2** to inspect past evaluated report cards.

#### Option B: Standalone Two-Agent Microservice
```bash
# Terminal 1: Launch Agent 2 (Evaluator Server)
uv run python -m evaluator.a2a_server

# Terminal 2: Launch Agent 1 (Interactive Quizmaster)
uv run python app.py
```

---

## 🔍 Observability in the Langfuse Dashboard

Once a session is completed, open your [Langfuse Dashboard](https://cloud.langfuse.com):

* **Users View:** Search by student email (`user_id = student@example.com`) to view lifetime quiz frequency, accuracy trends, and cumulative token spend.
* **Sessions View:** Filter by `session_id` to inspect the complete multi-turn timeline—from the first Easy question through promotions to the final report card.
* **Traces View:** Drill into individual LLM generations to verify prompt templates, token consumption, latency, and dual-provider fallback triggers.

---

## 📖 Memory Architecture

Adaptiq uses all **4 paradigms of AI agent memory**:

| Memory Type | Implementation | Operational Purpose |
| :--- | :--- | :--- |
| **Working Memory** | Live `QuizState` dict in RAM | Scratchpad tracking current topic, question, streak, and level in real time. |
| **In-Context Memory** | Serialized `A2APacket` injected into LLM prompt | Feeds complete quiz telemetry directly to Gemini without querying active session. |
| **Long-Term Memory** | SQLite persistence (`results.db`) | Permanent storage of finalized session records, report cards, and scores. |
| **Episodic Memory** | Cross-session queries by email (`core/memory.py`) | Recalls recurring weak topics across past dates and calculates historical score trends. |

---

## 🤝 A2A Protocol

Agent 1 sends a structured JSON packet to Agent 2 over HTTP:

```json
{
  "packet_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "timestamp": "2026-09-29T06:30:00Z",
  "student_name": "Shameer",
  "email": "shameer@google.com",
  "subject": "Chemistry",
  "topic_states": {
    "States of Matter": { "status": "mastered", "current_level": "hard", "correct_answers": 3, "questions_asked": 3 }
  },
  "question_history": [],
  "weighted_scores": {},
  "total_correct": 9,
  "total_questions": 12,
  "prerequisite_map": {
    "Chemical Reactions": ["Atoms & Molecules", "States of Matter"]
  }
}
```

---

## 📄 License

MIT — open-source, free to use, modify, and build upon.

<p align="center">Built with 🤖 OpenAI / Groq + Google Gemini + LangGraph + Langfuse</p>
