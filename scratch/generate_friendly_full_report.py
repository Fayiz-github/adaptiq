"""
generate_friendly_full_report.py
--------------------------------
Generates the comprehensive, deeply detailed, yet completely accessible
Adaptiq Full Project Report in Microsoft Word (.docx) with 100% Calibri formatting.
Contains NO headers, NO footers, and professional section headings.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

OUTPUT_PATH = r"c:\Users\moham\agent2agent\Adaptiq_Full_Project_Report.docx"

def build():
    doc = docx.Document()

    COLOR_PRIMARY = RGBColor(0x1B, 0x36, 0x5D)    # Deep Navy
    COLOR_SECONDARY = RGBColor(0x2E, 0x5B, 0x88)  # Slate Blue
    COLOR_BODY = RGBColor(0x22, 0x22, 0x22)       # Off-black Charcoal
    COLOR_MUTED = RGBColor(0x55, 0x55, 0x55)      # Muted Gray
    HEX_HEADER_BG = "1B365D"
    HEX_ZEBRA_BG = "F4F6F9"
    HEX_CALLOUT_BG = "EBF3FA"
    HEX_CALLOUT_BORDER = "2E5B88"

    # Margins: 1 inch, strictly NO headers and NO footers
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)
        s.header_distance = Inches(0)
        s.footer_distance = Inches(0)

        # Clear any default header or footer content
        s.header.is_linked_to_previous = False
        s.footer.is_linked_to_previous = False
        for p in s.header.paragraphs:
            p.text = ""
        for p in s.footer.paragraphs:
            p.text = ""

        # Remove headerReference and footerReference from sectPr
        for hr in s._sectPr.xpath('./w:headerReference'):
            s._sectPr.remove(hr)
        for fr in s._sectPr.xpath('./w:footerReference'):
            s._sectPr.remove(fr)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = COLOR_BODY
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = COLOR_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(13)
        run.font.bold = True
        run.font.color.rgb = COLOR_SECONDARY
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = COLOR_BODY
        return p

    def add_p(text, bold_prefix=None):
        p = doc.add_paragraph()
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = "Calibri"
            r_bold.font.size = Pt(10.5)
            r_bold.font.bold = True
            r_bold.font.color.rgb = COLOR_BODY
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_BODY
        return p

    def add_bullet(text, bold_prefix=None):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2.5)
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.name = "Calibri"
            r_bold.font.size = Pt(10.5)
            r_bold.font.bold = True
            r_bold.font.color.rgb = COLOR_BODY
        run = p.add_run(text)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = COLOR_BODY
        return p

    def add_callout(text, title=None):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = tbl.cell(0, 0)
        cell.width = Inches(6.5)

        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_CALLOUT_BG}"/>')
        tcPr.append(shd)

        borders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{HEX_CALLOUT_BORDER}"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(borders)

        cp = cell.paragraphs[0]
        cp.paragraph_format.space_before = Pt(4)
        cp.paragraph_format.space_after = Pt(4)
        cp.paragraph_format.left_indent = Inches(0.1)
        cp.paragraph_format.right_indent = Inches(0.1)

        if title:
            tr = cp.add_run(f"{title}\n")
            tr.font.name = "Calibri"
            tr.font.size = Pt(10.5)
            tr.font.bold = True
            tr.font.color.rgb = COLOR_PRIMARY

        cr = cp.add_run(text)
        cr.font.name = "Calibri"
        cr.font.size = Pt(10)
        cr.font.color.rgb = COLOR_BODY

        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def style_table(table, col_widths, headers, data):
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = table.rows[0].cells
        for i, title in enumerate(headers):
            hdr_cells[i].text = title
            hdr_cells[i].width = col_widths[i]
            tcPr = hdr_cells[i]._tc.get_or_add_tcPr()
            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_HEADER_BG}"/>')
            tcPr.append(shd)
            p = hdr_cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9.5)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        for row_idx, row_data in enumerate(data):
            row_cells = table.rows[row_idx + 1].cells
            is_zebra = (row_idx % 2 == 1)
            for col_idx, cell_value in enumerate(row_data):
                row_cells[col_idx].text = str(cell_value)
                row_cells[col_idx].width = col_widths[col_idx]
                tcPr = row_cells[col_idx]._tc.get_or_add_tcPr()
                if is_zebra:
                    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{HEX_ZEBRA_BG}"/>')
                    tcPr.append(shd)
                p = row_cells[col_idx].paragraphs[0]
                p.paragraph_format.space_before = Pt(2.5)
                p.paragraph_format.space_after = Pt(2.5)
                for run in p.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(9)
                    run.font.color.rgb = COLOR_BODY

        doc.add_paragraph().paragraph_format.space_after = Pt(3)

    # -------------------------------------------------------------------------
    # DOCUMENT TITLE BLOCK
    # -------------------------------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(2)
    r_title = p_title.add_run("ADAPTIQ: FULL PROJECT ARCHITECTURE & PEDAGOGICAL REPORT")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    r_sub = p_sub.add_run("A Complete Technical and Pedagogical Guide to the Autonomous Two-Agent Adaptive Examination Platform for Class 8 Curriculum")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(12)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_SECONDARY

    add_callout(
        "Author & Developer: Mohamed Fayiz\n"
        "Project Repository: https://github.com/Fayiz-github/adaptiq\n"
        "Target Academic Domain: Class 8 Curriculum (Mathematics, Biology, Chemistry)\n"
        "Core Technologies: Python 3.13, LangGraph, FastAPI, SQLite, Google Gemini 2.0 Flash, OpenAI / Groq\n"
        "Document Formatting: 100% Calibri Typography (Headers, Body, Callouts, Tables | No Headers or Footers)",
        "PROJECT SPECIFICATION SHEET"
    )

    # -------------------------------------------------------------------------
    # SECTION 1: PROJECT OVERVIEW & PURPOSE
    # -------------------------------------------------------------------------
    add_h1("1. Project Overview & Purpose")
    add_p(
        "In traditional academic testing, every student receives the exact same set of questions in the exact same sequence. "
        "A student who already understands the material is forced to answer repetitive, simple questions, while a student who struggles "
        "experiences immediate confusion, leading to cognitive fatigue. When the test finishes, the student receives a single percentage score "
        "(such as 60%) that gives no insight into what went wrong or how to improve."
    )
    add_p(
        "Adaptiq is an intelligent examination platform designed to replace this rigid model. It implements two autonomous AI agents "
        "that collaborate like private tutors:\n"
        "• Agent 1 (The Quizmaster): Conducts the live examination. If a student answers two questions correctly in a row, the platform promotes them to more challenging questions. If the student makes an error, the platform steps down a level to test foundational understanding.\n"
        "• Agent 2 (The Evaluator): When the session concludes, this agent examines the student's complete performance, reviews historical tests from previous sessions (Episodic Memory), verifies whether foundational concepts were mastered (Cascading Prerequisite Analysis), and writes a detailed report card featuring structured study techniques."
    )

    # -------------------------------------------------------------------------
    # SECTION 2: LIMITATIONS OF CONVENTIONAL TESTING
    # -------------------------------------------------------------------------
    add_h1("2. Limitations of Conventional Academic Testing")
    add_p("Conventional digital quizzes suffer from four key structural weaknesses:")

    add_bullet(
        "When an unprepared student encounters difficult questions early, cognitive overload causes them to give up. When an advanced student is repeatedly tested on basic definitions, they lose interest. Adaptiq addresses this by calibrating difficulty in real time per topic.",
        "1. Cognitive Mismatch: "
    )
    add_bullet(
        "In a standard 4-option multiple-choice test (A, B, C, or D), an unprepared student has a 25% probability of choosing the correct answer by chance. Conventional tests promote students on single lucky guesses. Adaptiq requires two consecutive correct answers, reducing lucky guess probability to 6.25%.",
        "2. Lucky Guess Distortion: "
    )
    add_bullet(
        "Standard testing platforms retain no memory across attempts. If a student struggled with 'Exponents & Powers' last week, the platform forgets this today. Adaptiq uses Episodic Memory to track recurring weaknesses across sessions.",
        "3. Lack of Cross-Session Memory: "
    )
    add_bullet(
        "A numeric score indicates how many questions were answered correctly, but does not explain the root cause of errors. Was an answer incorrect due to a vocabulary gap, a multi-step calculation error, or a missing prerequisite? Adaptiq diagnoses the specific cognitive tier and provides a concrete study plan.",
        "4. Absence of Actionable Feedback: "
    )

    # -------------------------------------------------------------------------
    # SECTION 3: TWO-AGENT ARCHITECTURE (THE A2A PROTOCOL)
    # -------------------------------------------------------------------------
    add_h1("3. Two-Agent Architecture & The A2A Protocol")
    add_p(
        "Adaptiq adopts a two-agent architecture rather than a single monolithic script. "
        "Separating the real-time quiz proctor from the post-quiz evaluator ensures that active testing remains fast and responsive, "
        "while in-depth diagnostic analysis can take the necessary time to synthesize longitudinal records without slowing down the student."
    )

    t_agent_headers = ["Technical Dimension", "Agent 1: Quizmaster", "Agent 2: Evaluator"]
    t_agent_widths = [Inches(1.5), Inches(2.5), Inches(2.5)]
    t_agent_data = [
        ["Primary Role", "Interactive examination conductor and adaptive proctor", "Pedagogical diagnostician and long-term academic mentor"],
        ["Implementation Files", "quizmaster/agent.py & quizmaster/quiz_engine.py", "evaluator/a2a_server.py & evaluator/agent.py"],
        ["Execution Topology", "Interactive command-line interface event loop (app.py)", "Asynchronous ASGI web service (FastAPI / Uvicorn on port 8000)"],
        ["AI Models", "OpenAI (gpt-5-nano) / Groq (LLaMA 3.3 70B)", "Google Gemini 2.0 Flash (with 8-second timeout guard)"],
        ["Memory Scope", "Working Memory (live QuizState dictionary in RAM)", "Episodic & Long-Term Memory (results.db SQLite store)"],
        ["Communication Mechanism", "Serializes session and posts JSON payload over HTTP", "Receives POST request at /evaluate and returns ASCII report"],
    ]
    tbl_ag = doc.add_table(rows=len(t_agent_data) + 1, cols=3)
    style_table(tbl_ag, t_agent_widths, t_agent_headers, t_agent_data)

    add_h2("3.1 The Agent-to-Agent (A2A) Telemetry Packet")
    add_p(
        "The two agents do not share global variables or database handles. All communication occurs via the A2APacket dataclass "
        "(defined in core/models.py). The packet includes:\n"
        "• packet_id: Unique UUID4 identifier for the quiz attempt\n"
        "• timestamp: ISO-8601 UTC timestamp of session completion\n"
        "• student_name: Display name used on report headers\n"
        "• email: Unique student identifier used for database lookups and memory isolation\n"
        "• subject: Academic discipline (Mathematics, Biology, or Chemistry)\n"
        "• topic_states: Dictionary recording questions asked, correct answers, current level, and mastery status per topic\n"
        "• prerequisite_map: Directed curriculum dependency graph\n"
        "• total_correct & total_questions: Cumulative score totals."
    )

    # -------------------------------------------------------------------------
    # SECTION 4: ADAPTIVE DIFFICULTY ENGINE
    # -------------------------------------------------------------------------
    add_h1("4. Adaptive Difficulty Engine & State Machine")
    add_p(
        "In Adaptiq, every subject contains 5 curriculum topics. Each topic operates through an independent state machine that scales across three cognitive tiers:"
    )
    add_bullet("Tests basic recall, definitions, and core terminology (e.g. 'Which organelle is the powerhouse of the cell?').", "1. Easy Tier (Foundational Recall): ")
    add_bullet("Tests conceptual understanding, formula application, and two-step reasoning (e.g. 'Which energy-rich molecules produced in light reactions power the Calvin cycle?').", "2. Medium Tier (Conceptual Application): ")
    add_bullet("Tests multi-step problem solving, edge cases, and synthesis (e.g. 'Predict photosynthesis rates under simultaneous light saturation and carbon dioxide limitation.').", "3. Hard Tier (Complex Synthesis): ")

    add_h2("4.1 The 2-in-a-Row Promotion Rule: Mathematical Derivation")
    add_p(
        "In a 4-option multiple-choice question, the probability of selecting the correct option by random guessing is:\n"
        "P(Random Correct) = 1 / 4 = 0.25 (25%)\n"
        "If a platform promotes a student on a single correct answer, 25% of guessing students are falsely promoted to harder content. "
        "Adaptiq enforces the 2-in-a-Row Promotion Rule: a student must answer two consecutive questions correctly at their current level. "
        "The probability of guessing two consecutive questions correctly is:\n"
        "P(Promotion by Guessing) = 0.25 * 0.25 = 0.0625 (6.25%)\n"
        "This reduces lucky-guess distortion by 75%, ensuring that promotions reflect genuine understanding."
    )

    add_h2("4.2 The 2-Loop Demotion Rule: Graceful Failure Handling")
    add_p(
        "When an error occurs, Adaptiq applies a structured recovery mechanism:\n"
        "• An incorrect answer at Medium or Hard demotes the topic by one level to verify foundational concepts.\n"
        "• A lifetime counter (demotion_count) tracks errors. If a student experiences two demotions and fails again at Easy, the topic is marked as 'Weak / Focus Area' and closed. "
        "This prevents endless looping and keeps the assessment focused on achievable targets."
    )

    # -------------------------------------------------------------------------
    # SECTION 5: MULTI-TIER AI AGENT MEMORY SYSTEMS
    # -------------------------------------------------------------------------
    add_h1("5. Multi-Tier AI Agent Memory Systems")
    add_p(
        "Adaptiq implements the four foundational memory paradigms established in agentic cognitive systems:"
    )

    t_mem_headers = ["Memory Type", "Technical Implementation", "Operational Purpose"]
    t_mem_widths = [Inches(1.5), Inches(2.2), Inches(2.8)]
    t_mem_data = [
        ["1. Working Memory", "core/models.py (QuizState in RAM)", "Maintains the live session scratchpad: current topic, current question, consecutive correct streak, and question history during active testing."],
        ["2. In-Context Memory", "evaluator/report_generator.py (Gemini prompt)", "The serialized A2APacket injected into the LLM prompt window, allowing Agent 2 to inspect full session telemetry without querying the active session."],
        ["3. Long-Term Memory", "core/database.py (results.db in SQLite)", "Permanent storage of completed records: session UUID, student email, mastered topics, weak topics, and ASCII report cards."],
        ["4. Episodic Memory", "core/memory.py (Historical queries)", "Cross-session analytical engine: recalls recurring weak topics across past dates and calculates historical score improvement trends."],
    ]
    tbl_mem2 = doc.add_table(rows=len(t_mem_data) + 1, cols=3)
    style_table(tbl_mem2, t_mem_widths, t_mem_headers, t_mem_data)

    # -------------------------------------------------------------------------
    # SECTION 6: CURRICULUM HIERARCHY & PREREQUISITE DAG
    # -------------------------------------------------------------------------
    add_h1("6. Curriculum Hierarchy & Cascading Prerequisite DAG")
    add_p(
        "Academic learning is cumulative: advanced concepts depend on foundational understanding. "
        "If a student struggles with 'Chemical Reactions', the root cause is frequently an unmastered prerequisite in 'Atoms & Molecules'. "
        "In core/models.py, Adaptiq structures all 15 topics across a Directed Acyclic Graph (DAG) of prerequisites:\n"
        "• Mathematics: Rational Numbers -> Linear Equations, Mensuration, Exponents & Powers (Data Handling is independent)\n"
        "• Biology: Cell Structure -> Photosynthesis, Reproduction, Life Processes (Microorganisms is independent)\n"
        "• Chemistry: States of Matter -> Atoms & Molecules -> Acids & Bases, Metals & Non-metals, Chemical Reactions"
    )
    add_callout(
        "Cascading Root-Cause Diagnosis Example:\n"
        "When Agent 2 evaluates a student who struggled in Chemical Reactions, it checks their performance in Atoms & Molecules and Acids & Bases. "
        "If those topics were also weak, Agent 2 issues a targeted alert:\n"
        "\"Your difficulty with Chemical Reactions is linked to an unmastered foundation in Atoms & Molecules. "
        "Reviewing chemical valence and atomic formulas is required before complex multi-reactant equations can be mastered.\"",
        "PREREQUISITE DIAGNOSIS IN PRACTICE"
    )

    # -------------------------------------------------------------------------
    # SECTION 7: STUDENT IDENTITY & DATA PRIVACY
    # -------------------------------------------------------------------------
    add_h1("7. Student Identity & Data Privacy Architecture")
    add_p(
        "A key design consideration was preventing data crossover when multiple students share the same display name. "
        "In early development, database queries filtered solely by student_name. This created two issues:\n"
        "1. Privacy Breach: A student could view the past report cards of other students with the same name.\n"
        "2. Memory Contamination: Episodic memory combined the errors of all students sharing that name, distorting AI diagnosis."
    )
    add_h2("7.1 The Solution: Identity Decoupling & Email Validation")
    add_p(
        "The architecture decouples the presentation name from the identity key:\n"
        "• student_name (e.g. 'Fayiz'): Used for friendly greetings and report card banners.\n"
        "• email (e.g. 'fayiz1@school.edu'): Used as the primary key for all database filters and episodic memory calculations.\n"
        "In app.py, the application enforces regular expression validation (EMAIL_PATTERN = re.compile(r'^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$')). "
        "Any typo (such as a comma in place of a period) or non-email text is rejected, ensuring all session records are isolated under verified email addresses."
    )

    # -------------------------------------------------------------------------
    # SECTION 8: RESILIENCE & DUAL-LLM PIPELINE
    # -------------------------------------------------------------------------
    add_h1("8. Engineering Resilience & Dual-LLM Pipeline")
    add_p(
        "To ensure stability during external service disruptions, quizmaster/question_generator.py implements four engineering safeguards:"
    )
    add_bullet(
        "Question generation first queries OpenAI / Groq (configured with a 12-second timeout). If a timeout or outage occurs, the engine automatically falls back to Google Gemini with zero disruption to the student.",
        "1. Dual-Provider Automatic Fallback: "
    )
    add_bullet(
        "LLMs may format answers in non-standard ways (such as 'Option B: Mitochondria' or 'B)'). The answer parsing engine applies a 4-tier check: (1) Direct letter check, (2) Exact option text match, (3) Regex word boundary check, and (4) String containment match.",
        "2. 4-Tier Answer Resolution Engine: "
    )
    add_bullet(
        "To avoid duplicate questions during a single quiz, Agent 1 tracks the last 6 questions served in that topic and injects an avoid-clause prompt constraint.",
        "3. Anti-Repetition Session Memory: "
    )
    add_bullet(
        "In evaluator/a2a_server.py, dynamic root path resolution ensures the server can be started from the project root or from inside the evaluator/ directory without encountering module import errors.",
        "4. Standalone Microservice Path Resolution: "
    )

    # -------------------------------------------------------------------------
    # SECTION 9: PEDAGOGICAL GUIDANCE & COGNITIVE STUDY METHODS
    # -------------------------------------------------------------------------
    add_h1("9. Pedagogical Guidance & Cognitive Study Methodologies")
    add_p(
        "In evaluator/report_generator.py, Agent 2 is prompted with cognitive learning principles to provide level-specific study guidance:"
    )
    add_bullet(
        "The AI cautions against passive re-reading. It prescribes Active Recall (writing out definitions without consulting notes) and the Feynman Technique (explaining concepts in simple, everyday language).",
        "For Easy Topics (Base Not Set): "
    )
    add_bullet(
        "The AI commends clearing Easy, but notes that Medium requires relational reasoning. It prescribes Compare-and-Contrast Tables (such as contrasting Mitosis versus Meiosis) and Step-by-Step Scenario Practice.",
        "For Medium Topics (Passed Easy): "
    )
    add_bullet(
        "The AI commends tackling advanced questions. It prescribes 'What-If' Parameter Testing (evaluating how changing one variable alters an entire system) and maintaining an Error Notebook to classify calculation slips versus conceptual gaps.",
        "For Hard Topics (Tackling Hard): "
    )
    add_bullet(
        "The AI celebrates comprehensive mastery across all three difficulty tiers and recommends advanced challenge problems or peer tutoring.",
        "For Mastered Topics (Confirmed Mastery): "
    )

    # -------------------------------------------------------------------------
    # SECTION 10: TECHNICAL CODEBASE STRUCTURE
    # -------------------------------------------------------------------------
    add_h1("10. Technical Codebase Structure & Module Responsibilities")
    add_p("The platform is structured into modular packages:")

    t_cat_headers = ["File Relative Path", "Module Role", "Key Responsibilities"]
    t_cat_widths = [Inches(1.8), Inches(2.2), Inches(2.5)]
    t_cat_data = [
        ["core/config.py", "Configuration Loader", "Loads environment variables (.env), manages host/port settings, and validates required API keys."],
        ["core/models.py", "Domain Models", "Defines shared dataclasses: Question, TopicState, QuizState, A2APacket, and the prerequisite DAG."],
        ["core/database.py", "SQLite Persistence", "Manages the quiz_sessions table, handles schema migrations, and saves finalized report cards."],
        ["core/memory.py", "Episodic Memory Engine", "Queries historical records by email to extract recurring weak topics and calculate score trajectories."],
        ["quizmaster/agent.py", "Quizmaster Agent", "Conducts the interactive quiz, manages the adaptive difficulty elevator, and packages the A2A telemetry packet."],
        ["quizmaster/question_generator.py", "Question Generator", "Generates single-concept Class 8 MCQs using OpenAI or Gemini with anti-repetition constraints."],
        ["quizmaster/quiz_engine.py", "Adaptive State Machine", "LangGraph decision nodes: checks answers, evaluates 2-in-a-row promotions, and handles 2-loop demotions."],
        ["quizmaster/a2a_client.py", "A2A HTTP Client", "Transmits the completed quiz packet over HTTP to the Evaluator server with a 20-second timeout guard."],
        ["evaluator/agent.py", "Evaluator Agent", "Loads episodic memory and directs Gemini to synthesize structured pedagogical feedback."],
        ["evaluator/report_generator.py", "Report Prompt Engine", "Generates level-by-level study methodology feedback based on cognitive science principles."],
        ["evaluator/a2a_server.py", "FastAPI A2A Server", "ASGI REST service listening on port 8000 that receives quiz packets and persists reports into results.db."],
        ["app.py / main.py", "Interactive CLI Application", "Handles student onboarding, email regex validation, subject selection, and historical report review."],
    ]
    tbl_cat = doc.add_table(rows=len(t_cat_data) + 1, cols=3)
    style_table(tbl_cat, t_cat_widths, t_cat_headers, t_cat_data)

    # -------------------------------------------------------------------------
    # SECTION 11: LOCAL DEPLOYMENT & EXECUTION WORKFLOW
    # -------------------------------------------------------------------------
    add_h1("11. Local Deployment & Execution Workflow")
    add_p("To run Adaptiq with full two-agent execution:")

    add_h2("Step 1: Environment File Configuration")
    add_p(
        "Create a .env file in the workspace root with valid API credentials:\n"
        "OPENAI_API_KEY=your_openai_or_groq_key\n"
        "GEMINI_API_KEY=your_gemini_api_key\n"
        "EVALUATOR_HOST=127.0.0.1\n"
        "EVALUATOR_PORT=8000"
    )

    add_h2("Step 2: Start Agent 2 (The Evaluator Server)")
    add_p(
        "Open a terminal and start the FastAPI service:\n"
        "uv run python -m evaluator.a2a_server\n"
        "The server will listen at http://127.0.0.1:8000 with interactive docs at http://127.0.0.1:8000/docs."
    )

    add_h2("Step 3: Start Agent 1 (The Interactive Quiz)")
    add_p(
        "Open a second terminal and start the quiz proctor:\n"
        "uv run app.py\n"
        "1. Enter student display name (e.g. 'Fayiz').\n"
        "2. Enter student email (e.g. 'fayiz@school.edu').\n"
        "3. Choose option 1 to start an adaptive session in Mathematics, Biology, or Chemistry, or option 2 to review past report cards."
    )

    # -------------------------------------------------------------------------
    # SECTION 12: FUTURE ROADMAP & SCALABILITY
    # -------------------------------------------------------------------------
    add_h1("12. Future Roadmap & Scalability")
    add_bullet("Developing a web interface using Streamlit or Next.js with radar charts displaying mastery per topic.", "1. Web Interface: ")
    add_bullet("Adding educator dashboards to allow teachers to identify class-wide learning gaps and prerequisite bottlenecks.", "2. Educator Dashboards: ")
    add_bullet("Incorporating Item Response Theory (IRT) to mathematically calibrate question difficulty based on student response data.", "3. Psychometric Calibration: ")
    add_bullet("Adding speech-to-text input to enable oral quizzing for auditory learners.", "4. Voice-Enabled Assessment: ")

    doc.save(OUTPUT_PATH)
    print(f"Document updated successfully at: {OUTPUT_PATH}")

if __name__ == "__main__":
    build()
