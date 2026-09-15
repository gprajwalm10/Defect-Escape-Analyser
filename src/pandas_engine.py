"""
Step 2: The Pandas Matchmaker Engine
Executes mathematical reverse traceability with left joins and NaN gap detection.
"""

import pandas as pd

HISTORICAL_QA_DEFECTS_RESOLVED = 20


def execute_pandas_matchmaker(reqs_df: pd.DataFrame, tests_df: pd.DataFrame, defects_df: pd.DataFrame):
    """
    Executes the exact Pandas logic:
    1. Standardizes ID columns to strings to prevent merge mismatches.
    2. Left joins Requirements with Test Cases on req_id.
       Produces 'NaN' (blanks) next to requirements lacking test cases.
    3. Left joins Escaped Defects with the above Traceability result.
    4. Calculates enterprise QA KPIs.
    """
    reqs = reqs_df.copy()
    tests = tests_df.copy()
    defects = defects_df.copy()

    for df in [reqs, tests, defects]:
        if "req_id" in df.columns:
            df["req_id"] = df["req_id"].astype(str).str.strip().str.upper()
    if "defect_id" in defects.columns:
        defects["defect_id"] = defects["defect_id"].astype(str).str.strip()

    # Step 2 Part A: Link Requirements with Test Cases (Generates NaNs for gaps)
    reqs_with_tests = pd.merge(
        reqs,
        tests,
        on="req_id",
        how="left"
    )

    # Step 2 Part B: Link Escaped Defects with Traceability result
    merged_full = pd.merge(
        defects,
        reqs_with_tests,
        on="req_id",
        how="left",
        suffixes=("_defect", "_trace")
    )

    # Clean up column values & fill missing descriptors for clean display
    if "test_id" in merged_full.columns:
        is_nan_test = (
            merged_full["test_id"].isna() | 
            (merged_full["test_id"].astype(str).str.strip().str.upper().isin(["NAN", "NONE", "NULL", ""]))
        )
    else:
        merged_full["test_id"] = "NaN"
        is_nan_test = pd.Series([True] * len(merged_full))

    merged_full["is_nan_gap"] = is_nan_test
    merged_full["trace_verdict"] = merged_full["is_nan_gap"].apply(
        lambda x: "🚨 Untested (NaN Gap)" if x else "⚠️ Tested (Scenario Gap)"
    )

    # Fill defaults if requirement metadata wasn't found
    if "req_title" in merged_full.columns:
        merged_full["req_title"] = merged_full["req_title"].fillna("Specification " + merged_full["req_id"])
    if "rule_description" in merged_full.columns:
        merged_full["rule_description"] = merged_full["rule_description"].fillna("Specification rule for " + merged_full["req_id"])
    if "test_title" in merged_full.columns:
        merged_full["test_title"] = merged_full.apply(
            lambda r: "No test case authored in QA suite" if r["is_nan_gap"] else str(r["test_title"]),
            axis=1
        )

    all_req_ids = set(reqs["req_id"].unique())
    tested_req_ids = set(tests["req_id"].unique())
    orphaned_req_ids = all_req_ids - tested_req_ids

    total_escaped = len(defects["defect_id"].unique()) if "defect_id" in defects.columns else len(defects)

    # Calculate exact defect counts by category (guarantees nan_count + tested_count == total_escaped)
    defect_nan_map = {}
    for d_id, group in merged_full.groupby("defect_id"):
        # If any row has a valid test_id, this defect had a test case in QA
        has_any_test = (~group["is_nan_gap"]).any()
        defect_nan_map[d_id] = not has_any_test

    nan_defects_count = sum(1 for is_nan in defect_nan_map.values() if is_nan)
    tested_defects_count = total_escaped - nan_defects_count

    total_defects = HISTORICAL_QA_DEFECTS_RESOLVED + total_escaped
    escape_rate = (total_escaped / total_defects * 100) if total_defects > 0 else 0.0

    kpis = {
        "total_escaped": total_escaped,
        "nan_defects_count": nan_defects_count,
        "tested_defects_count": tested_defects_count,
        "orphaned_count": len(orphaned_req_ids),
        "escape_rate": round(escape_rate, 2),
        "total_reqs": len(all_req_ids),
        "qa_resolved": HISTORICAL_QA_DEFECTS_RESOLVED
    }

    return reqs_with_tests, merged_full, kpis
