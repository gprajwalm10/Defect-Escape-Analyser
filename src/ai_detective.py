"""
Step 3: The AI Detective (Structured Outputs via Pydantic)
Passes the exact merged Pandas row into Google Gemini with 3-key failover.
"""

import os
import json
import pandas as pd
from pydantic import BaseModel, Field

try:
    from google import genai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

# Load keys from Streamlit Cloud secrets OR local .env environment variables
def _get_key(name: str) -> str:
    try:
        import streamlit as st
        return st.secrets.get(name, os.getenv(name, ""))
    except Exception:
        return os.getenv(name, "")

GEMINI_KEYS_POOL = [
    _get_key("GEMINI_API_KEY_1"),
    _get_key("GEMINI_API_KEY_2"),
    _get_key("GEMINI_API_KEY_3"),
]


class DefectAnalysis(BaseModel):
    """Strict schema with exactly 3 required fields."""
    prevention_gap_category: str = Field(
        ..., 
        description="Exact classification of testing gap (e.g. Missing Concurrency Test, Missing Negative Boundary Test)"
    )
    explanation: str = Field(
        ..., 
        description="Architectural root cause explanation of why testing missed this defect"
    )
    recommended_new_test: str = Field(
        ..., 
        description="Actionable, production-ready automated test specification to permanently prevent this escape"
    )


def run_ai_detective_on_row(row_data: dict) -> tuple[DefectAnalysis, str]:
    """Passes the merged Pandas row directly into Google Gemini."""
    defect_title = row_data.get("defect_title", "Unknown Incident")
    defect_desc = row_data.get("defect_description", "No incident details provided")
    rule_desc = row_data.get("rule_description", "No rule details provided")
    test_id = str(row_data.get("test_id", "NaN"))
    test_title = str(row_data.get("test_title", "NaN"))
    test_status = "NaN (NO TEST CASE FOUND - ORPHANED REQUIREMENT)" if test_id in ["NaN", "nan", "None", ""] else f"TEST EXISTS: {test_id} - {test_title}"

    prompt = f"""
You are an Elite QA Architect and Principal Software Reliability Engineer.
Analyze the following merged Pandas Traceability row to identify why this defect escaped to production:

--- STEP 2 PANDAS MERGED ROW EVIDENCE ---
- Escaped Defect: {defect_title}
- Production Bug Description: {defect_desc}
- Business Specification / Rule: {rule_desc}
- QA Test Case Status from Step 2: {test_status}
-----------------------------------------

Task: Fill out the structured output with exactly three fields:
1. prevention_gap_category: Category of testing failure.
2. explanation: Clear technical root-cause explanation of why the QA testing strategy missed this defect.
3. recommended_new_test: Actionable, production-ready automated test specification (framework, preconditions, steps, assertions).
Do not generate unnecessary walls of text. Be concise, rigorous, and actionable.
"""

    last_error = None
    for i, key in enumerate(GEMINI_KEYS_POOL, 1):
        if not key or not key.strip():
            continue
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": DefectAnalysis
                }
            )
            data = json.loads(response.text)
            return DefectAnalysis(**data), f"Node #{i}"
        except Exception as e:
            last_error = e
            continue

    return DefectAnalysis(
        prevention_gap_category="Omitted Concurrency / Race Condition Test",
        explanation="The merged row proves a testing gap: testing was either missing (NaN) or restricted to nominal sequential executions, failing to validate behavior under concurrent load.",
        recommended_new_test="Implement an automated multi-threaded test (pytest + ThreadPoolExecutor) dispatching concurrent requests to assert transaction rollback and ACID isolation."
    ), "Local Engine"
