"""
================================================================================
TRACEGUARD AI - ENTERPRISE DEFECT ESCAPE & REVERSE TRACEABILITY PLATFORM
================================================================================
Architecture:
- STEP 1: The Evidence (Clear 3-File CSV Uploader & Synthetic Evidence)
- STEP 2: The Pandas Matchmaker (Mathematical Traceability & NaN Proof)
- STEP 3: The AI Detective (Strict Structured Outputs from Step 2 Merged Row)

Tech Stack: Python 3.12, Streamlit, Pandas, Google Gemini (google-genai), Pydantic
================================================================================
"""

import os
import sys
import json
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Import modular components from src
from src.normalizer import (
    normalize_defects_df,
    normalize_requirements_df,
    normalize_tests_df
)
from src.pandas_engine import execute_pandas_matchmaker, HISTORICAL_QA_DEFECTS_RESOLVED
from src.ai_detective import run_ai_detective_on_row, DefectAnalysis

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REQS_FILE = os.path.join(DATA_DIR, "requirements.csv")
TESTS_FILE = os.path.join(DATA_DIR, "test_cases.csv")
DEFECTS_FILE = os.path.join(DATA_DIR, "escaped_defects.csv")


# ==============================================================================
# DEFAULT EVIDENCE LOADER (WITH INTENTIONAL TESTING GAPS)
# ==============================================================================
def get_default_datasets():
    """
    Default evidence datasets with intentional test gaps:
    - REQ-101 and REQ-104 have ZERO test cases (Orphaned Requirements).
    - REQ-102, REQ-103, REQ-105 have only nominal tests missing edge conditions.
    """
    if os.path.exists(REQS_FILE) and os.path.exists(TESTS_FILE) and os.path.exists(DEFECTS_FILE):
        reqs = pd.read_csv(REQS_FILE)
        tests = pd.read_csv(TESTS_FILE)
        defects = pd.read_csv(DEFECTS_FILE)
    else:
        reqs = pd.DataFrame([
            {"req_id": "REQ-101", "module": "Authentication & IAM", "req_title": "Account Lockout on Failed Logins", "rule_description": "User accounts must lock for 15 minutes after 5 consecutive failed attempts to mitigate credential stuffing.", "criticality": "Critical"},
            {"req_id": "REQ-102", "module": "Checkout & Pricing", "req_title": "Coupon Stacking Floor", "rule_description": "Promotional discount coupons cannot be stacked beyond 50%, and cart total must never fall below $0.00.", "criticality": "High"},
            {"req_id": "REQ-103", "module": "Payment Gateway", "req_title": "Payment Idempotency Protection", "rule_description": "All charge requests must supply unique Idempotency-Key. Retries within 60s must return cached response without double charge.", "criticality": "Critical"},
            {"req_id": "REQ-104", "module": "Digital Wallet Ledger", "req_title": "Atomic Wallet Debit Concurrency", "rule_description": "Wallet balance deductions must execute inside serializable ACID transactions with pessimistic row locks (SELECT FOR UPDATE).", "criticality": "Blocker"},
            {"req_id": "REQ-105", "module": "Treasury & FX", "req_title": "Cross-Border Banker's Rounding", "rule_description": "Currency conversions must preserve 6 decimal places during calculation and apply round-half-to-even before ledger persistence.", "criticality": "Medium"},
            {"req_id": "REQ-106", "module": "Taxation Engine", "req_title": "Automated State Sales Tax", "rule_description": "Automated sales tax must calculate state and municipal rates based on 9-digit postal ZIP code.", "criticality": "High"},
            {"req_id": "REQ-107", "module": "Customer Notifications", "req_title": "Transactional SMS Dispatch", "rule_description": "SMS confirmation must be dispatched within 3 seconds of payment authorization.", "criticality": "Low"}
        ])
        tests = pd.DataFrame([
            {"test_id": "TC-201", "req_id": "REQ-102", "test_title": "Verify single 20% coupon reduces subtotal", "test_type": "Unit", "execution_status": "PASSED"},
            {"test_id": "TC-202", "req_id": "REQ-103", "test_title": "Verify payment authorization succeeds with valid idempotency key", "test_type": "Integration", "execution_status": "PASSED"},
            {"test_id": "TC-203", "req_id": "REQ-105", "test_title": "Verify standard USD to EUR single conversion calculation", "test_type": "Unit", "execution_status": "PASSED"},
            {"test_id": "TC-204", "req_id": "REQ-106", "test_title": "Verify California sales tax calculation on retail orders", "test_type": "Regression", "execution_status": "PASSED"},
            {"test_id": "TC-205", "req_id": "REQ-107", "test_title": "Verify SMS notification queue receives order confirmation trigger", "test_type": "Integration", "execution_status": "PASSED"}
        ])
        defects = pd.DataFrame([
            {"defect_id": "DEF-001", "req_id": "REQ-101", "defect_title": "Credential stuffing attack bypassed login lockout", "defect_description": "Production security monitoring detected 25,000 automated login attempts against accounts in 5 minutes without lockouts. 3 accounts compromised.", "severity": "Critical", "environment": "Production", "reported_date": "2026-08-12"},
            {"defect_id": "DEF-002", "req_id": "REQ-102", "defect_title": "Coupon stacking glitch produces negative cart balance", "defect_description": "Customers stacked multiple promotional codes simultaneously, resulting in -$15.00 total. The checkout accepted the order without payment.", "severity": "High", "environment": "Production", "reported_date": "2026-08-18"},
            {"defect_id": "DEF-003", "req_id": "REQ-103", "defect_title": "Duplicate card charges during network latency spike", "defect_description": "During mobile cellular latency spike, users clicked 'Pay Now' repeatedly. Concurrent API requests bypassed in-memory locks, billing cards twice.", "severity": "Critical", "environment": "Production", "reported_date": "2026-08-25"},
            {"defect_id": "DEF-004", "req_id": "REQ-104", "defect_title": "Wallet double-spending race condition on concurrent withdrawals", "defect_description": "An adversary executed 8 concurrent API withdrawal requests for $200 against a $200 balance. Without row locks, all read $200, creating -$1,400 deficit.", "severity": "Blocker", "environment": "Production", "reported_date": "2026-09-02"},
            {"defect_id": "DEF-005", "req_id": "REQ-105", "defect_title": "Cumulative rounding variance in daily cross-border bank clearing", "defect_description": "Clearinghouse reported unreconciled $4,830 variance. Floating-point truncation in high-volume micro-transactions caused cumulative drift.", "severity": "Major", "environment": "Production", "reported_date": "2026-09-08"}
        ])
    return normalize_requirements_df(reqs), normalize_tests_df(tests), normalize_defects_df(defects)


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
def init_session():
    if "reqs_df" not in st.session_state or "tests_df" not in st.session_state or "defects_df" not in st.session_state:
        reqs, tests, defects = get_default_datasets()
        st.session_state.reqs_df = reqs
        st.session_state.tests_df = tests
        st.session_state.defects_df = defects

    if "selected_defect_id" not in st.session_state:
        st.session_state.selected_defect_id = st.session_state.defects_df["defect_id"].iloc[0]

    if "analyses" not in st.session_state:
        st.session_state.analyses = {}


# ==============================================================================
# HTML TABLE GENERATOR (LIGHT MODE & MATCHING BACKGROUND COLOR)
# ==============================================================================
def render_light_html_table(df: pd.DataFrame, max_rows: int = 15) -> str:
    """
    Renders an enterprise light HTML table matching the #F8FAFC / #FFFFFF background.
    Explicit inline styles with !important prevent browser dark mode overrides.
    """
    cols = df.columns.tolist()
    rows = df.head(max_rows).to_dict(orient="records")

    html = """
    <div style="overflow-x:auto; background-color:#FFFFFF !important; border:1px solid #E2E8F0 !important; border-radius:8px !important; box-shadow:0 1px 3px rgba(0,0,0,0.04) !important; margin-bottom:12px !important;">
      <table style="width:100% !important; text-align:left !important; border-collapse:collapse !important; font-size:0.82rem !important; font-family:'Inter', sans-serif !important; background-color:#FFFFFF !important; color:#0F172A !important;">
        <thead>
          <tr style="background-color:#F1F5F9 !important; border-bottom:2px solid #CBD5E1 !important;">
    """
    for col in cols:
        label = col.replace("_", " ").title()
        html += f'<th style="background-color:#F1F5F9 !important; color:#1E293B !important; padding:10px 12px !important; font-weight:700 !important; white-space:nowrap !important; border:none !important; border-bottom:2px solid #CBD5E1 !important;">{label}</th>'
    html += "</tr></thead><tbody>"

    for idx, row in enumerate(rows):
        bg = "#FFFFFF" if idx % 2 == 0 else "#F8FAFC"
        html += f'<tr style="background-color:{bg} !important; border-bottom:1px solid #E2E8F0 !important;">'
        for col in cols:
            val = str(row.get(col, ""))
            if val in ["nan", "NaN", "None", "NONE", "null", "NULL"]:
                val_rendered = "<span style='background:#FEF2F2; color:#DC2626; padding:2px 6px; border-radius:4px; font-weight:700; font-family:monospace;'>NaN</span>"
            elif "🚨" in val:
                val_rendered = f"<span style='background:#FFF1F2; color:#BE123C; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.75rem;'>{val}</span>"
            elif "⚠️" in val:
                val_rendered = f"<span style='background:#EFF6FF; color:#1D4ED8; padding:2px 6px; border-radius:4px; font-weight:700; font-size:0.75rem;'>{val}</span>"
            elif len(val) > 42:
                val_rendered = val[:39] + "..."
            else:
                val_rendered = val

            html += f'<td style="background-color:{bg} !important; color:#0F172A !important; padding:9px 12px !important; border:none !important; border-bottom:1px solid #E2E8F0 !important;">{val_rendered}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================
def main():
    st.set_page_config(
        page_title="TraceGuard AI | Enterprise Traceability Platform",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session()

    # Premium Web Application Stylesheet (Clean Light SaaS + Top Navigation Bar)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* Global Light Canvas */
        .stApp {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
            font-family: 'Inter', -apple-system, sans-serif !important;
        }

        /* Top Web App Navigation Bar */
        .top-navbar {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            font-size: 1.15rem;
            color: #0F172A;
            letter-spacing: -0.02em;
        }
        .nav-links {
            display: flex;
            gap: 16px;
            font-size: 0.82rem;
            font-weight: 600;
            color: #64748B;
        }
        .nav-link-active {
            color: #2563EB;
            background-color: #EFF6FF;
            padding: 4px 10px;
            border-radius: 6px;
        }
        .nav-telemetry {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            color: #475569;
        }

        /* KPI Metric Cards */
        .metric-card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 1.25rem !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s ease !important;
        }
        .metric-card:hover {
            border-color: #CBD5E1 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        }
        .metric-title {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            margin-bottom: 0.35rem;
        }
        .metric-val {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
        }
        .metric-note {
            font-size: 0.8rem;
            font-weight: 500;
            margin-top: 0.35rem;
        }

        /* Step Indicator Pills */
        .step-pill {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .step-pill-1 { background:#EFF6FF; color:#1D4ED8; border:1px solid #BFDBFE; }
        .step-pill-2 { background:#F0FDF4; color:#15803D; border:1px solid #BBF7D0; }
        .step-pill-3 { background:#FAF5FF; color:#7E22CE; border:1px solid #E9D5FF; }

        /* Content Cards */
        .content-card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.25rem !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04) !important;
        }

        .nan-badge {
            background-color: #FEF2F2;
            color: #DC2626;
            border: 1px solid #FECACA;
            padding: 2px 8px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .pass-badge {
            background-color: #F0FDF4;
            color: #16A34A;
            border: 1px solid #BBF7D0;
            padding: 2px 8px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 0.75rem;
        }

        /* File Upload Box Styling */
        .upload-card {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            border-bottom: 1px solid #E2E8F0 !important;
            margin-bottom: 1.25rem !important;
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            color: #64748B !important;
            padding: 10px 18px !important;
        }
        .stTabs [aria-selected="true"] {
            color: #2563EB !important;
            border-bottom: 2px solid #2563EB !important;
        }

        /* Buttons */
        .stButton>button {
            background-color: #2563EB !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.65rem 1.4rem !important;
            box-shadow: 0 1px 2px 0 rgba(37, 99, 235, 0.2) !important;
        }
        .stButton>button:hover {
            background-color: #1D4ED8 !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E2E8F0 !important;
        }

        /* Universal Light Mode Override for All Tables */
        table, thead, tbody, tr, th, td {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        th {
            background-color: #F1F5F9 !important;
            color: #1E293B !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TOP BROWSER NAVIGATION BAR
    # --------------------------------------------------------------------------
    st.markdown("""
        <div class="top-navbar">
            <div class="nav-brand">
                <span style="font-size: 1.4rem;">🛡️</span>
                <div>
                    <div>TraceGuard AI</div>
                    <div style="font-size: 0.7rem; color: #64748B; font-weight: 500;">Enterprise Quality Observability</div>
                </div>
            </div>
            <div class="nav-links">
                <span class="nav-link-active">📊 Reverse Traceability</span>
                <span>🧩 Logic Gaps</span>
                <span>🧠 AI Detective</span>
                <span>📑 Governance</span>
            </div>
            <div class="nav-telemetry">
                <span style="display:inline-flex; align-items:center; gap:5px; background:#F0FDF4; color:#15803D; padding:3px 8px; border-radius:6px; border:1px solid #BBF7D0;">
                    ● Cluster: Production-US
                </span>
                <span style="display:inline-flex; align-items:center; gap:5px; background:#EFF6FF; color:#1D4ED8; padding:3px 8px; border-radius:6px; border:1px solid #BFDBFE;">
                    ⚡ Gemini 3.5 Engine
                </span>
                <span style="color:#0F172A; font-weight:600;">👤 QA Architect</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # SIDEBAR: DATA INGESTION & DEFECT SELECTOR
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("<h3 style='font-weight:800; color:#0F172A; margin-bottom:0.1rem;'>🛡️ AI Defect Escape Analyser</h3>", unsafe_allow_html=True)
        st.caption("Production Observability & Reverse Traceability")
        st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # STEP 1: DIRECT CUSTOM CSV DATA INGESTION (NO RADIO BUTTONS)
        # ----------------------------------------------------------------------
        st.markdown("<span class='step-pill step-pill-1'>STEP 1: INGESTION</span>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.95rem; font-weight:700; color:#1E293B; margin-top:6px;'>Upload Custom CSV Files</h4>", unsafe_allow_html=True)
        st.caption("Upload your three project CSV files below to run the reverse traceability pipeline:")

        # File 1: Requirements
        st.markdown("""
            <div class="upload-card">
                <div style="font-weight:700; font-size:0.82rem; color:#1D4ED8;">📜 1. Requirements (requirements.csv)</div>
                <div style="font-size:0.75rem; color:#64748B;">Columns: <code>req_id</code>, <code>req_title</code>, <code>rule_description</code>, <code>module</code>, <code>criticality</code></div>
            </div>
        """, unsafe_allow_html=True)
        uploaded_reqs = st.file_uploader("Upload requirements.csv", type=["csv"], key="uploader_reqs", label_visibility="collapsed")

        # File 2: Test Cases
        st.markdown("""
            <div class="upload-card">
                <div style="font-weight:700; font-size:0.82rem; color:#15803D;">🧪 2. Test Cases (test_cases.csv)</div>
                <div style="font-size:0.75rem; color:#64748B;">Columns: <code>test_id</code>, <code>req_id</code>, <code>test_title</code>, <code>execution_status</code>, <code>test_type</code></div>
            </div>
        """, unsafe_allow_html=True)
        uploaded_tests = st.file_uploader("Upload test_cases.csv", type=["csv"], key="uploader_tests", label_visibility="collapsed")

        # File 3: Escaped Defects
        st.markdown("""
            <div class="upload-card">
                <div style="font-weight:700; font-size:0.82rem; color:#B91C1C;">🐞 3. Escaped Defects (escaped_defects.csv)</div>
                <div style="font-size:0.75rem; color:#64748B;">Columns: <code>defect_id</code>, <code>req_id</code>, <code>defect_title</code>, <code>defect_description</code>, <code>severity</code></div>
            </div>
        """, unsafe_allow_html=True)
        uploaded_defects = st.file_uploader("Upload escaped_defects.csv", type=["csv"], key="uploader_defects", label_visibility="collapsed")

        if st.button("📥 Ingest & Process All 3 Datasets", type="primary", use_container_width=True):
            loaded_count = 0
            if uploaded_reqs:
                st.session_state.reqs_df = normalize_requirements_df(pd.read_csv(uploaded_reqs))
                loaded_count += 1
            if uploaded_tests:
                st.session_state.tests_df = normalize_tests_df(pd.read_csv(uploaded_tests))
                loaded_count += 1
            if uploaded_defects:
                st.session_state.defects_df = normalize_defects_df(pd.read_csv(uploaded_defects))
                loaded_count += 1

            if loaded_count > 0:
                st.session_state.selected_defect_id = st.session_state.defects_df["defect_id"].iloc[0]
                st.session_state.analyses = {}
                st.success(f"{loaded_count} dataset(s) processed and normalized!")
                st.rerun()
            else:
                st.warning("Please upload at least one CSV file above to ingest.")

        if st.button("↺ Reset to Sample Data (FinTech Baseline)", use_container_width=True):
            reqs, tests, defects = get_default_datasets()
            st.session_state.reqs_df = reqs
            st.session_state.tests_df = tests
            st.session_state.defects_df = defects
            st.session_state.selected_defect_id = defects["defect_id"].iloc[0]
            st.session_state.analyses = {}
            st.info("Demonstration datasets reloaded.")
            st.rerun()

        st.markdown("---")

        # 3. DEFECT SELECTION DROPDOWN (REACTIVELY BOUND)
        st.markdown("<span class='step-pill step-pill-3'>STEP 3 TARGET</span>", unsafe_allow_html=True)
        st.markdown("<h4 style='font-size:0.95rem; font-weight:700; color:#1E293B; margin-top:6px;'>Select Defect to Investigate</h4>", unsafe_allow_html=True)

        defect_options = st.session_state.defects_df["defect_id"].tolist()
        if not defect_options:
            st.session_state.defects_df = normalize_defects_df(pd.DataFrame([{"defect_id": "DEF-001", "defect_title": "Default Incident", "defect_description": "Default"}]))
            defect_options = ["DEF-001"]

        if st.session_state.selected_defect_id not in defect_options:
            st.session_state.selected_defect_id = defect_options[0]

        curr_idx = defect_options.index(st.session_state.selected_defect_id)

        def format_label(d_id):
            matching = st.session_state.defects_df[st.session_state.defects_df["defect_id"] == d_id]
            if matching.empty:
                return str(d_id)
            row = matching.iloc[0]
            title = row.get("defect_title") or row.get("title") or row.get("summary") or row.get("name") or f"Defect {d_id}"
            return f"{d_id} • {str(title)[:24]}..."

        def on_defect_dropdown_change():
            st.session_state.selected_defect_id = st.session_state.sb_defect_selector

        st.selectbox(
            "Select Defect ID",
            options=defect_options,
            index=curr_idx,
            format_func=format_label,
            key="sb_defect_selector",
            on_change=on_defect_dropdown_change,
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("""
            <div style='background-color:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px;'>
                <div style='font-size:0.75rem; font-weight:700; color:#475569;'>Boehm's Cost of Quality Law</div>
                <div style='font-size:0.75rem; color:#64748B; margin-top:4px;'>
                    Defects in production cost <b>100x more</b> than bugs caught in QA. Reverse traceability identifies exactly what testing missed.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # EXECUTE STEP 2 PANDAS MATCHMAKER LOGIC
    # --------------------------------------------------------------------------
    reqs_with_tests, merged_full, kpis = execute_pandas_matchmaker(
        st.session_state.reqs_df,
        st.session_state.tests_df,
        st.session_state.defects_df
    )

    total_escaped_val = kpis.get("total_escaped", len(st.session_state.defects_df))
    nan_count_val = kpis.get("nan_defects_count", 0)
    tested_count_val = kpis.get("tested_defects_count", max(0, total_escaped_val - nan_count_val))
    total_reqs_val = kpis.get("total_reqs", len(st.session_state.reqs_df))
    escape_rate_val = kpis.get("escape_rate", 0.0)

    # --------------------------------------------------------------------------
    # EXECUTIVE KPI METRIC ROW
    # --------------------------------------------------------------------------
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Total Escaped Defects</div>
                <div class='metric-val' style='color:#E11D48;'>{total_escaped_val}</div>
                <div class='metric-note' style='color:#E11D48;'>↑ {total_escaped_val} Incident(s) Analyzed</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Untested Specs (NaN Proof)</div>
                <div class='metric-val' style='color:#D97706;'>{nan_count_val}</div>
                <div class='metric-note' style='color:#D97706;'>0 Test Cases in QA Suite</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Qualitative Test Gaps</div>
                <div class='metric-val' style='color:#2563EB;'>{tested_count_val}</div>
                <div class='metric-note' style='color:#2563EB;'>Tested but Missed Edge Scenarios</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Total Specifications</div>
                <div class='metric-val' style='color:#059669;'>{total_reqs_val}</div>
                <div class='metric-note' style='color:#059669;'>Defect Escape Rate: {escape_rate_val}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 3-STEP PIPELINE TABS
    # --------------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📁 Step 1: The Evidence (Three Raw Datasets)", 
        "🧩 Step 2: The Pandas Matchmaker (NaN Proof)", 
        "🧠 Step 3: The AI Detective (Structured Outputs)",
        "📂 Project Source Code (Repository)"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: STEP 1 - THE EVIDENCE DATASETS (LIGHT THEMED TABLES)
    # --------------------------------------------------------------------------
    with tab1:
        st.markdown("""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <div>
                    <span class='step-pill step-pill-1'>STEP 1</span>
                    <h3 style='font-size:1.15rem; font-weight:800; color:#0F172A; margin:4px 0 0 0;'>The Evidence: Three Raw Datasets</h3>
                </div>
            </div>
            <p style='font-size:0.85rem; color:#64748B;'>
                Displayed below are the 3 baseline evidence datasets rendered in clean, light-colored tables matching the page background.
                Notice: We intentionally left some requirements without test cases so our Pandas logic can detect the gaps!
            </p>
        """, unsafe_allow_html=True)

        col_r, col_t, col_d = st.columns(3)
        with col_r:
            st.markdown("##### 📜 1. Requirements (`requirements.csv`)")
            reqs_display = st.session_state.reqs_df[["req_id", "module", "req_title", "criticality"]]
            st.markdown(render_light_html_table(reqs_display), unsafe_allow_html=True)
            st.caption(f"Total Requirements: {len(st.session_state.reqs_df)}")
        with col_t:
            st.markdown("##### 🧪 2. Test Cases (`test_cases.csv`)")
            tests_display = st.session_state.tests_df[["test_id", "req_id", "test_title", "execution_status"]]
            st.markdown(render_light_html_table(tests_display), unsafe_allow_html=True)
            st.caption(f"Total Test Cases: {len(st.session_state.tests_df)} (Notice REQ-101 and REQ-104 are missing!)")
        with col_d:
            st.markdown("##### 🐞 3. Escaped Defects (`escaped_defects.csv`)")
            defects_display = st.session_state.defects_df[["defect_id", "req_id", "severity", "defect_title"]]
            st.markdown(render_light_html_table(defects_display), unsafe_allow_html=True)
            st.caption(f"Total Escaped Defects: {len(st.session_state.defects_df)}")

    # --------------------------------------------------------------------------
    # TAB 2: STEP 2 - THE PANDAS MATCHMAKER (THE MATHEMATICAL LOGIC)
    # --------------------------------------------------------------------------
    with tab2:
        st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <div>
                    <span class='step-pill step-pill-2'>STEP 2</span>
                    <h3 style='font-size:1.15rem; font-weight:800; color:#0F172A; margin:4px 0 0 0;'>The Pandas Matchmaker: Mathematical Traceability & Root Cause</h3>
                </div>
            </div>
            <p style='font-size:0.85rem; color:#64748B;'>
                Before touching AI, Pandas performs mathematical reverse matching. A <code>Left Join</code> on <code>req_id</code> links 
                Requirements with Test Cases. The presence of <b>NaN (blanks)</b> mathematically proves where QA testing never existed, 
                while present test cases prove qualitative coverage gaps.
            </p>
        """, unsafe_allow_html=True)

        # DIAGNOSTIC CARDS (ACCURATE & SYNCHRONIZED)
        s1, s2 = st.columns(2)
        with s1:
            if nan_count_val > 0:
                st.markdown(f"""
                    <div style='background-color:#FFF1F2; border:1px solid #FECDD3; border-radius:10px; padding:12px;'>
                        <span style='color:#BE123C; font-weight:700; font-size:0.9rem;'>🚨 {nan_count_val} of {total_escaped_val} Defects: Untested Specifications (NaN Proof)</span>
                        <p style='color:#4C0519; font-size:0.8rem; margin:4px 0 0 0;'>
                            Pandas left join produced <code>NaN</code> for test_id, mathematically confirming these requirements were completely orphaned in the test suite.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px;'>
                        <span style='color:#15803D; font-weight:700; font-size:0.9rem;'>✓ 0 Orphaned Specifications (No NaN Gaps)</span>
                        <p style='color:#166534; font-size:0.8rem; margin:4px 0 0 0;'>
                            All escaped defects were linked to requirements that had existing test cases in the QA suite.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

        with s2:
            if tested_count_val > 0:
                st.markdown(f"""
                    <div style='background-color:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:12px;'>
                        <span style='color:#1D4ED8; font-weight:700; font-size:0.9rem;'>⚠️ {tested_count_val} of {total_escaped_val} Defects: Qualitative Testing Gaps</span>
                        <p style='color:#1E3A8A; font-size:0.8rem; margin:4px 0 0 0;'>
                            Test cases existed in the suite, but they only verified nominal happy paths and missed edge cases, concurrency, or boundary conditions.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color:#F8FAFC; border:1px solid #E2E8F0; border-radius:10px; padding:12px;'>
                        <span style='color:#475569; font-weight:700; font-size:0.9rem;'>✓ 0 Qualitative Test Gaps</span>
                        <p style='color:#64748B; font-size:0.8rem; margin:4px 0 0 0;'>
                            All production escapes were strictly due to missing test specifications.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)

        # Traceability Matrix Table with Root Cause Verdict Column
        cols_order = [
            "defect_id", "trace_verdict", "severity", "defect_title", 
            "req_id", "module", "rule_description", 
            "test_id", "test_title"
        ]
        available = [c for c in cols_order if c in merged_full.columns]
        st.markdown(render_light_html_table(merged_full[available], max_rows=20), unsafe_allow_html=True)

        # Active Defect Callout Linking Step 2 to Step 3
        curr_d = st.session_state.selected_defect_id
        matching_curr = merged_full[merged_full["defect_id"] == curr_d]
        curr_verdict = matching_curr["trace_verdict"].iloc[0] if not matching_curr.empty else "Pending"

        st.markdown(f"""
            <div style='background-color:#FFFFFF; border:1px solid #E2E8F0; border-radius:10px; padding:14px; margin-top:10px; display:flex; justify-content:space-between; align-items:center;'>
                <div>
                    <span style='font-weight:700; color:#0F172A; font-size:0.92rem;'>Selected Defect for AI Investigation: <code>{curr_d}</code></span>
                    <div style='font-size:0.8rem; color:#64748B; margin-top:2px;'>Step 2 Verdict: <b>{curr_verdict}</b></div>
                </div>
                <div style='font-size:0.82rem; font-weight:600; color:#2563EB;'>
                    👉 Switch to Step 3 tab to generate the AI Detective report
                </div>
            </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 3: STEP 3 - THE AI DETECTIVE (STRUCTURED OUTPUTS ON MERGED ROW)
    # --------------------------------------------------------------------------
    with tab3:
        st.markdown("""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <div>
                    <span class='step-pill step-pill-3'>STEP 3</span>
                    <h3 style='font-size:1.15rem; font-weight:800; color:#0F172A; margin:4px 0 0 0;'>The AI Detective: Strict Structured Outputs</h3>
                </div>
            </div>
            <p style='font-size:0.85rem; color:#64748B;'>
                AI is used for <b>exactly one task: explaining the prevention gap</b>. We pass the exact <b>merged Pandas row from Step 2</b> 
                (the bug + the requirement + the test or NaN) directly into Pydantic to enforce a strict JSON schema with exactly three fields:
                <code>prevention_gap_category</code>, <code>explanation</code>, and <code>recommended_new_test</code>.
            </p>
        """, unsafe_allow_html=True)

        current_id = st.session_state.selected_defect_id
        matching_rows = merged_full[merged_full["defect_id"] == current_id]

        if matching_rows.empty:
            current_id = merged_full["defect_id"].iloc[0]
            st.session_state.selected_defect_id = current_id
            matching_rows = merged_full[merged_full["defect_id"] == current_id]

        row_data = matching_rows.iloc[0].to_dict()
        is_nan_test = row_data.get("is_nan_gap", False) or pd.isna(row_data.get("test_id")) or str(row_data.get("test_id")).strip().upper() in ["NAN", "NONE", "NULL", ""]

        # Display Merged Row Evidence Box
        st.markdown(f"""
            <div class='content-card'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <span style='font-weight:700; color:#0F172A; font-size:1rem;'>Step 2 Merged Row Fed Directly to AI // <code>{current_id}</code></span>
                    {'<span class="nan-badge">TEST CASE: NaN (MISSING TEST CASE)</span>' if is_nan_test else '<span class="pass-badge">TEST CASE: ' + str(row_data.get("test_id")) + ' (INSUFFICIENT SCENARIO)</span>'}
                </div>
                <div style='display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-top:8px;'>
                    <div style='background-color:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px;'>
                        <div style='font-size:0.75rem; font-weight:700; color:#E11D48; text-transform:uppercase;'>Production Defect</div>
                        <div style='font-weight:700; font-size:0.9rem; color:#0F172A; margin-top:2px;'>{row_data.get('defect_title', '')}</div>
                        <div style='font-size:0.8rem; color:#475569; margin-top:4px;'>{row_data.get('defect_description', '')}</div>
                    </div>
                    <div style='background-color:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px;'>
                        <div style='font-size:0.75rem; font-weight:700; color:#2563EB; text-transform:uppercase;'>Specification Rule</div>
                        <div style='font-weight:700; font-size:0.9rem; color:#0F172A; margin-top:2px;'>{row_data.get('req_id', '')}: {row_data.get('req_title', '')}</div>
                        <div style='font-size:0.8rem; color:#475569; margin-top:4px;'>{row_data.get('rule_description', '')}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Trigger Buttons: Single Run & Batch Run
        b_col1, b_col2 = st.columns([2, 1])
        with b_col1:
            btn_label = f"🚀 Execute AI Detective on Row {current_id}"
            if current_id in st.session_state.analyses:
                btn_label = f"🔄 Re-Analyze Row {current_id}"
            run_btn = st.button(btn_label, type="primary", use_container_width=True)
        with b_col2:
            run_all_btn = st.button("⚡ Batch Analyze All Escaped Defects", use_container_width=True)

        if run_btn:
            with st.spinner(f"AI Detective analyzing merged row for {current_id} with Pydantic structured outputs..."):
                try:
                    analysis_result, node_used = run_ai_detective_on_row(row_data)
                    st.session_state.analyses[current_id] = {
                        "category": analysis_result.prevention_gap_category,
                        "explanation": analysis_result.explanation,
                        "recommended_test": analysis_result.recommended_new_test,
                        "node": node_used,
                        "time": time.strftime("%H:%M:%S")
                    }
                    st.success(f"Structured Output generated for {current_id}!")
                except Exception as err:
                    st.error(f"Execution interrupted: {str(err)}")

        if run_all_btn:
            unique_defects = merged_full.drop_duplicates(subset=["defect_id"])
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            total_u = len(unique_defects)
            for idx, (_, d_row) in enumerate(unique_defects.iterrows()):
                d_id = d_row["defect_id"]
                status_text.text(f"Analyzing {d_id} ({idx + 1} of {total_u})...")
                try:
                    res, node = run_ai_detective_on_row(d_row.to_dict())
                    st.session_state.analyses[d_id] = {
                        "category": res.prevention_gap_category,
                        "explanation": res.explanation,
                        "recommended_test": res.recommended_new_test,
                        "node": node,
                        "time": time.strftime("%H:%M:%S")
                    }
                except Exception as e:
                    pass
                progress_bar.progress((idx + 1) / total_u)
            status_text.text("Batch analysis complete!")
            time.sleep(0.4)
            st.rerun()

        # DISPLAY THE EXACT 3 STRUCTURED OUTPUT FIELDS
        if current_id in st.session_state.analyses:
            data = st.session_state.analyses[current_id]

            st.markdown(f"""
                <div style='margin-top:1.5rem; margin-bottom:0.75rem; display:flex; justify-content:space-between; align-items:center;'>
                    <h4 style='font-size:1.1rem; font-weight:800; color:#0F172A; margin:0;'>Pydantic Structured Output // {current_id}</h4>
                    <span style='font-size:0.75rem; color:#64748B; background:#F1F5F9; padding:3px 8px; border-radius:6px; font-weight:600;'>Schema: DefectAnalysis (3 Fields)</span>
                </div>
            """, unsafe_allow_html=True)

            # Field 1: prevention_gap_category
            st.markdown(f"""
                <div class='content-card' style='border-left:4px solid #6366F1 !important; margin-bottom:12px;'>
                    <div style='font-size:0.75rem; font-weight:700; color:#4F46E5; text-transform:uppercase;'>1. prevention_gap_category</div>
                    <div style='font-size:1.1rem; font-weight:800; color:#0F172A; margin-top:2px;'>
                        {data['category']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Field 2: explanation
            st.markdown(f"""
                <div class='content-card' style='border-left:4px solid #0284C7 !important; margin-bottom:12px;'>
                    <div style='font-size:0.75rem; font-weight:700; color:#0284C7; text-transform:uppercase;'>2. explanation</div>
                    <div style='font-size:0.9rem; color:#334155; line-height:1.6; margin-top:4px;'>
                        {data['explanation']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Field 3: recommended_new_test
            st.markdown(f"""
                <div class='content-card' style='border-left:4px solid #059669 !important; margin-bottom:12px;'>
                    <div style='font-size:0.75rem; font-weight:700; color:#059669; text-transform:uppercase;'>3. recommended_new_test</div>
                    <div style='font-size:0.9rem; color:#1E293B; line-height:1.6; margin-top:6px;'>
                        {data['recommended_test']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
                <div style='background-color:#F8FAFC; border:1px dashed #CBD5E1; border-radius:10px; padding:2rem; text-align:center; margin-top:1.5rem;'>
                    <div style='font-size:1.5rem; margin-bottom:6px;'>🔍</div>
                    <div style='font-weight:700; color:#334155; font-size:0.95rem;'>No AI Analysis generated yet for {current_id}</div>
                    <div style='font-size:0.85rem; color:#64748B; margin-top:4px;'>
                        Click the button above to pass this merged Pandas row into the AI Detective.
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 4: PROJECT SOURCE CODE (REPOSITORY)
    # --------------------------------------------------------------------------
    with tab4:
        st.markdown("""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <div>
                    <span class='step-pill' style='background:#6366F1; color:#fff; padding:3px 12px; border-radius:20px; font-size:0.7rem; font-weight:700; letter-spacing:1px;'>REPOSITORY</span>
                    <h3 style='font-size:1.15rem; font-weight:800; color:#0F172A; margin:4px 0 0 0;'>Project Source Code Explorer</h3>
                </div>
            </div>
            <p style='font-size:0.85rem; color:#64748B; margin-bottom:1.2rem;'>
                Browse every file powering this tool — architecture, AI logic, data engine, and configuration — all inline below.
            </p>
        """, unsafe_allow_html=True)

        # ── File tree ──────────────────────────────────────────────────────────
        st.markdown("""
            <div style='background:#0F172A; border-radius:12px; padding:1.2rem 1.5rem; font-family:monospace;
                        font-size:0.82rem; color:#94A3B8; line-height:2; margin-bottom:1.5rem;'>
                <span style='color:#F8FAFC; font-weight:700;'>&#128230; defect-escape-analyser/</span><br>
                &#9500;&#9472;&#9472; <span style='color:#60A5FA;'>app.py</span> &nbsp;<span style='color:#475569;'>&#8592; Streamlit entry point &amp; full UI</span><br>
                &#9500;&#9472;&#9472; <span style='color:#60A5FA;'>requirements.txt</span> &nbsp;<span style='color:#475569;'>&#8592; Python dependencies</span><br>
                &#9500;&#9472;&#9472; <span style='color:#60A5FA;'>README.md</span> &nbsp;<span style='color:#475569;'>&#8592; Project documentation</span><br>
                &#9500;&#9472;&#9472; <span style='color:#60A5FA;'>.env.example</span> &nbsp;<span style='color:#475569;'>&#8592; API key template</span><br>
                &#9500;&#9472;&#9472; <span style='color:#A78BFA;'>src/</span><br>
                &#9474;&nbsp;&nbsp;&nbsp;&#9500;&#9472;&#9472; <span style='color:#34D399;'>ai_detective.py</span> &nbsp;<span style='color:#475569;'>&#8592; Gemini AI + Pydantic schema</span><br>
                &#9474;&nbsp;&nbsp;&nbsp;&#9500;&#9472;&#9472; <span style='color:#34D399;'>pandas_engine.py</span> &nbsp;<span style='color:#475569;'>&#8592; Pandas traceability engine</span><br>
                &#9474;&nbsp;&nbsp;&nbsp;&#9500;&#9472;&#9472; <span style='color:#34D399;'>normalizer.py</span> &nbsp;<span style='color:#475569;'>&#8592; Universal CSV column mapper</span><br>
                &#9474;&nbsp;&nbsp;&nbsp;&#9492;&#9472;&#9472; <span style='color:#34D399;'>__init__.py</span><br>
                &#9492;&#9472;&#9472; <span style='color:#FBBF24;'>data/</span><br>
                &nbsp;&nbsp;&nbsp;&nbsp;&#9500;&#9472;&#9472; <span style='color:#FB923C;'>requirements.csv</span><br>
                &nbsp;&nbsp;&nbsp;&nbsp;&#9500;&#9472;&#9472; <span style='color:#FB923C;'>test_cases.csv</span><br>
                &nbsp;&nbsp;&nbsp;&nbsp;&#9492;&#9472;&#9472; <span style='color:#FB923C;'>escaped_defects.csv</span>
            </div>
        """, unsafe_allow_html=True)

        # ── File picker ────────────────────────────────────────────────────────
        FILE_MAP = {
            "app.py  —  Streamlit UI & main app": "app.py",
            "src/ai_detective.py  —  Gemini AI engine": os.path.join("src", "ai_detective.py"),
            "src/pandas_engine.py  —  Pandas matchmaker": os.path.join("src", "pandas_engine.py"),
            "src/normalizer.py  —  CSV column normalizer": os.path.join("src", "normalizer.py"),
            "src/__init__.py  —  Package init": os.path.join("src", "__init__.py"),
            "data/requirements.csv  —  Sample requirements": os.path.join("data", "requirements.csv"),
            "data/test_cases.csv  —  Sample test cases": os.path.join("data", "test_cases.csv"),
            "data/escaped_defects.csv  —  Sample defects": os.path.join("data", "escaped_defects.csv"),
            "requirements.txt  —  Python dependencies": "requirements.txt",
            "README.md  —  Project documentation": "README.md",
            ".env.example  —  API key template": ".env.example",
        }

        LANG_MAP = {
            ".py": "python",
            ".csv": "text",
            ".txt": "text",
            ".md": "markdown",
            ".toml": "toml",
            ".example": "bash",
        }

        col_pick, col_badge = st.columns([3, 1])
        with col_pick:
            selected_label = st.selectbox(
                "🗂️ Select a file to inspect:",
                options=list(FILE_MAP.keys()),
                key="repo_file_select"
            )
        with col_badge:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            rel_path = FILE_MAP[selected_label]
            ext = os.path.splitext(rel_path)[1].lower()
            lang = LANG_MAP.get(ext, "text")
            badge_color = {
                "python": "#6366F1", "markdown": "#0EA5E9",
                "text": "#F59E0B", "toml": "#10B981", "bash": "#64748B"
            }.get(lang, "#64748B")
            st.markdown(f"""
                <div style='background:{badge_color}18; border:1px solid {badge_color}55; border-radius:8px;
                            padding:6px 14px; text-align:center; font-size:0.78rem; font-weight:700;
                            color:{badge_color}; margin-top:4px;'>
                    {lang.upper()}
                </div>
            """, unsafe_allow_html=True)

        # ── Code viewer ────────────────────────────────────────────────────────
        abs_path = os.path.join(BASE_DIR, rel_path)
        st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center;
                        background:#0F172A; border-radius:10px 10px 0 0; padding:10px 18px; margin-top:12px;'>
                <span style='color:#94A3B8; font-size:0.78rem; font-family:monospace;'>&#128196; {rel_path}</span>
                <span style='color:#475569; font-size:0.72rem;'>defect-escape-analyser</span>
            </div>
        """, unsafe_allow_html=True)

        try:
            with open(abs_path, "r", encoding="utf-8") as fh:
                file_content = fh.read()
            line_count = file_content.count("\n") + 1
            st.code(file_content, language=lang, line_numbers=True)
            st.markdown(f"""
                <div style='font-size:0.75rem; color:#94A3B8; text-align:right; margin-top:4px;'>
                    {line_count} lines &nbsp;·&nbsp; {len(file_content):,} bytes &nbsp;·&nbsp; {rel_path}
                </div>
            """, unsafe_allow_html=True)
        except FileNotFoundError:
            st.warning(f"File not found at `{abs_path}`")
        except Exception as ex:
            st.error(f"Could not read file: {ex}")


if __name__ == "__main__":
    main()

