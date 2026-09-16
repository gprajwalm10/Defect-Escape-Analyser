# 🛡️ TraceGuard AI: Defect Escape Analyser

---

## 🟢 Live Demo
**Try the application live here:** [TraceGuard AI on Streamlit](https://defect-escape-analyser-9bj4loqr5oicwvkg5bqmzp.streamlit.app/)

---

## 🚨 The Problem Statement
In enterprise software engineering, letting a bug slip past the testing team and into the live application is a massive problem. According to historical software economics, finding and fixing a bug after it reaches production is exponentially more expensive than catching it early in the design or testing phase. Production defects lead to emergency hotfixes, degraded user trust, and direct financial loss. 

When a bug "escapes," engineering teams need to know exactly *why* their testing checklists failed to catch it so they can systemically prevent it from happening again.

## ✨ Key Features
* **Input Validation:** The application validates uploaded datasets before analysis. Validation includes required column checks, duplicate ID detection, empty/missing values checks, and cross-reference validation (test cases and defects must reference valid requirement IDs).
* **Defect-to-Requirement Mapping:** Each escaped defect is mapped to its associated requirement using the `requirement_id`.
* **Test Coverage Analysis:** The analyzer evaluates existing test cases related to each escaped defect. Coverage is classified as:
    * *Covered:* An existing test directly addresses the escaped scenario.
    * *Partially Covered:* Related tests exist, but the specific escaped scenario is not directly represented.
    * *Not Covered:* No meaningful test exists for the requirement or scenario.
* **Prevention Gap Classification:** Each defect is assigned a likely prevention-gap category based on evidence from the requirement, defect, escape phase, related tests, and coverage status (e.g., Requirement Gap, Test Coverage Gap, Negative Testing Gap, Boundary Testing Gap, Data Validation Gap, Integration Gap, Process Gap).
* **AI-Assisted Recommendation:** AI explains the likely prevention gap and recommends one specific missing test area based strictly on evidence.
* **Streamlit Dashboard:** Provides a CSV upload interface, validation feedback, gap distribution metrics, detailed defect analysis, AI explanations, and CSV export of analysis results.

## 🌍 Real-World Use Cases (Synthetic Data)
The tool is built to analyze and solve various levels of testing failures. The synthetic sample pack includes:
1. **Level 1 (Missing Basic Tests):** A user leaves a password blank and the site crashes because QA only tested valid passwords.
2. **Level 2 (Boundary Failures):** A user uploads a file exactly at the 5MB limit, freezing the system because QA only tested files well above or below the limit.
3. **Level 3 (Logic Interactions):** A user combines a discount code with free shipping, getting an unintended double discount because QA didn't test how the two rules interact.
4. **Level 4 (Load Issues):** A chat app crashes when 200 people message at once because QA only tested the room with 3 users.
5. **Level 5 (FinTech Race Conditions):** A user double-clicks a "Buy Stock" button in a millisecond, bypassing balance checks because QA didn't test concurrent rapid requests.

## ⚙️ How We Solve It (The 3-Step Pipeline)

### Step 1: The Evidence (Data Ingestion)
The system ingests three critical pieces of data via CSV files:
* `requirements.csv`: The definitive business rules and specifications.
* `test_cases.csv`: The actual checks and validations the QA team performed.
* `escaped_defects.csv`: The live production incident reports.

### Step 2: The Pandas Matchmaker (Mathematical Logic)
The application acts as an automated Requirements Traceability Matrix. It uses Python's Pandas library to perform a series of relational merges. It matches the bug to the rule, and the rule to the test. If a requirement was deployed but never tested, Pandas mathematically flags it. This completely removes the need for AI guessing—the coverage gap is proven with hard data.

### Step 3: The AI Detective (Strict Structured Outputs)
Once the missing piece is found, that specific, isolated row of data is sent to the AI. To prevent the AI from generating useless conversational filler, the tool uses strict data schemas. The AI is forced to return exactly three actionable items:
1. Prevention Gap Category
2. Architectural Explanation
3. New Test Recommendation

## 🧠 AI Design & Architecture
AI is intentionally constrained to one task to keep the analysis explainable and reproducible.

**Deterministic Layer**
Python logic handles:
`Requirement Mapping` ➔ `Test Coverage Analysis` ➔ `Prevention Gap Classification`

**AI Layer**
The AI receives the relevant analysis evidence and produces:
1. Explanation of the likely escape reason.
2. One recommended missing test area.

**Constraints:** The AI is instructed *not* to change the deterministic coverage result, change the prevention-gap category, invent requirements, invent existing test cases, or claim unsupported system behavior as fact. This separation keeps the core QA analysis reproducible while using AI only where contextual reasoning is useful. Where the available evidence is insufficient, the AI is instructed to frame the result as a hypothesis rather than a confirmed fact.

## 🔄 System Workflow
1. **Upload:** User uploads `requirements.csv`, `test_cases.csv`, and `escaped_defects.csv`.
2. **Validate:** System checks datasets for errors, missing values, and valid cross-references.
3. **Map & Analyze:** Pandas deterministically maps defects to requirements and calculates test coverage status.
4. **Classify Gap:** The system categorizes the prevention gap based on the mapped data.
5. **AI Insight:** The AI generates an explanation and a specific test recommendation based on the isolated evidence.
6. **Review & Export:** User views the dashboard metrics, reads the AI analysis, and exports the results to CSV.

## 🛠️ Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python** | Core application and analysis logic |
| **Pandas** | Dataset processing and analysis |
| **Streamlit** | User interface and dashboard |
| **Pytest** | Automated testing |
| **OpenAI Python SDK** | OpenAI-compatible client used for Groq integration |
| **Groq API** | AI recommendation generation |
| **python-dotenv** | Secure loading of environment variables |
| **Git & GitHub** | Version control and source-code repository |

## 📂 Project Structure

```text
defect_escape_analyser/
├── .streamlit/
│   └── config.toml               # Light theme configuration & matching table styling
├── data/
│   ├── requirements.csv          # Business rules (with intentional gaps)
│   ├── test_cases.csv            # Executed test suite (missing tests for REQ-101/104)
│   └── escaped_defects.csv       # Production incident reports (DEF-001 to DEF-005)
├── src/
│   ├── __init__.py
│   ├── normalizer.py             # Schema auto-mapper (handles arbitrary CSV headers)
│   ├── pandas_engine.py          # Left joins, NaN proof, and KPI calculations
│   └── ai_detective.py           # LLM integration + structured outputs
├── app.py                        # Main Streamlit web application & top navigation bar
├── requirements.txt              # Production package dependencies
├── .env.example                  # Template for API credentials
├── .gitignore                    # Git exclusion rules
└── README.md                     # Project documentation
