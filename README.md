# 🛡️ TraceGuard AI: Defect Escape Analyser

> **Autonomous Reverse Traceability & AI-Powered QA Root Cause Diagnostic Platform**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458.svg)](https://pandas.pydata.org/)
[![Google Gemini](https://img.shields.io/badge/Gemini_3.5_Flash-Google_GenAI-4285F4.svg)](https://ai.google.dev/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.5+-E92063.svg)](https://docs.pydantic.dev/)

---

## 🎯 Executive Overview & Business Problem

In enterprise software engineering, software defects that escape into production incur catastrophic financial, compliance, and reputational costs. According to **Boehm's Cost of Quality law**, catching and fixing a defect in production is up to **100x more expensive** than preventing it during early QA test cycles.

**TraceGuard AI** mathematically automates the reverse engineering of testing failures:
1. **The Evidence:** Audits raw requirements, executed test suites, and escaped production bugs.
2. **The Pandas Matchmaker:** Deterministically performs Left Joins to reveal **NaN (blank) gaps**, mathematically proving where QA coverage was missing.
3. **The AI Detective:** Passes the exact merged Pandas row into Google Gemini using **Pydantic Structured Outputs** to generate strict, actionable test specifications without walls of text.

---

## 📂 Project Structure

```
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
│   ├── pandas_engine.py          # Step 2: Left joins, NaN proof, and KPI calculations
│   └── ai_detective.py           # Step 3: Google Gemini client + Pydantic schema
├── app.py                        # Main Streamlit web application & top navigation bar
├── requirements.txt              # Production package dependencies
├── .env.example                  # Template for API credentials
├── .gitignore                    # Git exclusion rules
└── README.md                     # Project documentation
```

---

## 🚀 3-Step Execution Pipeline

### Step 1: The Evidence (Data Ingestion & CSV Upload)
* **File 1 of 3: Business Specifications (`requirements.csv`)**: Functional rules across IAM, Payment Gateways, Cart Checkout, FX, and Wallets.
* **File 2 of 3: Executed Test Suite (`test_cases.csv`)**: Executed QA tests. High-risk rules (`REQ-101` and `REQ-104`) are **deliberately omitted** to create detectable mathematical gaps.
* **File 3 of 3: Production Escapes (`escaped_defects.csv`)**: Actual production incidents linked back to the requirements.
* *Feature:* Users can either load the default verified datasets or upload their own custom CSVs via the sidebar.

### Step 2: The Pandas Matchmaker (The Mathematical Logic)
* Performs a Pandas `Left Join` on `req_id`:
  $$\text{Requirements} \xrightarrow{\text{Left Join}} \text{Test Cases}$$
* Requirements without tests automatically evaluate to **`NaN`**. This mathematical proof identifies coverage blind spots without AI hallucination.
* Calculates core QA metrics:
  $$\text{Defect Escape Rate (DER)} = \frac{\text{Escaped Defects}}{\text{QA Defects Caught} + \text{Escaped Defects}} \times 100\%$$

### Step 3: The AI Detective (Strict Structured Outputs)
* Takes the exact **merged Pandas row from Step 2** (the bug + the requirement + the `NaN` or existing test).
* Enforces strict Pydantic structured outputs with **exactly 3 required fields**:
  1. `prevention_gap_category`: Categorization of testing breakdown (e.g., *Missing Concurrency / Race Condition Test*).
  2. `explanation`: Architectural root cause explanation of why testing missed it.
  3. `recommended_new_test`: Actionable, production-ready test specification.

---

## 💻 Quick Start & Local Execution

### 1. Clone & Navigate
```bash
git clone <your-repo-url>
cd defect_escape_analyser
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Credentials
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Add your Google Gemini API key:
```env
GEMINI_API_KEY_1=AQ.Ab8...
```

### 4. Run the Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501` (or specified port).

---

## 🌐 Pushing to Your GitHub Repository

```bash
# 1. Add your remote GitHub repository
git remote add origin https://github.com/<your-username>/<your-repo-name>.git

# 2. Rename branch to main
git branch -M main

# 3. Push all files to GitHub
git push -u origin main
```
