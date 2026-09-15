"""
Schema Normalizer & Column Auto-Mapper
Handles arbitrary user CSV uploads gracefully without KeyError.
"""

import pandas as pd


def normalize_defects_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Intelligently maps and standardizes arbitrary CSV column names to canonical schema:
    [defect_id, req_id, defect_title, defect_description, severity, environment, reported_date]
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    lower_map = {c.lower().replace(" ", "_").replace("-", "_"): c for c in df.columns}

    # 1. Map defect_id
    id_cands = ["defect_id", "id", "defectid", "bug_id", "bugid", "issue_id", "issueid", "defect_number", "key", "defect"]
    mapped_id = next((lower_map[cand] for cand in id_cands if cand in lower_map), None)
    df["defect_id"] = df[mapped_id].astype(str).str.strip() if mapped_id else [f"DEF-{i+1:03d}" for i in range(len(df))]

    # 2. Map req_id
    req_cands = ["req_id", "requirement_id", "rule_id", "reqid", "linked_requirement", "requirement", "rule", "req"]
    mapped_req = next((lower_map[cand] for cand in req_cands if cand in lower_map), None)
    df["req_id"] = df[mapped_req].astype(str).str.strip().str.upper() if mapped_req else "REQ-101"

    # 3. Map defect_title
    title_cands = ["defect_title", "title", "name", "summary", "bug_title", "defect_name", "headline", "issue", "subject"]
    mapped_title = next((lower_map[cand] for cand in title_cands if cand in lower_map), None)
    df["defect_title"] = df[mapped_title].astype(str) if mapped_title else "Incident " + df["defect_id"]

    # 4. Map defect_description
    desc_cands = ["defect_description", "description", "details", "desc", "bug_description", "notes", "defect_details", "reproduction_steps"]
    mapped_desc = next((lower_map[cand] for cand in desc_cands if cand in lower_map), None)
    df["defect_description"] = df[mapped_desc].astype(str) if mapped_desc else df["defect_title"]

    # 5. Map severity
    sev_cands = ["severity", "priority", "criticality", "level", "sev", "impact"]
    mapped_sev = next((lower_map[cand] for cand in sev_cands if cand in lower_map), None)
    df["severity"] = df[mapped_sev].astype(str) if mapped_sev else "Critical"

    if "environment" not in df.columns:
        df["environment"] = "Production"
    if "reported_date" not in df.columns:
        df["reported_date"] = "2026-09-13"

    return df


def normalize_requirements_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes uploaded requirements.csv columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    lower_map = {c.lower().replace(" ", "_").replace("-", "_"): c for c in df.columns}

    # 1. Map req_id
    id_cands = ["req_id", "id", "requirement_id", "rule_id", "reqid", "key", "req", "code"]
    mapped_id = next((lower_map[cand] for cand in id_cands if cand in lower_map), None)
    df["req_id"] = df[mapped_id].astype(str).str.strip().str.upper() if mapped_id else [f"REQ-{i+1:03d}" for i in range(len(df))]

    # 2. Map req_title
    title_cands = ["req_title", "title", "name", "rule_title", "rule_name", "summary", "requirement_name"]
    mapped_title = next((lower_map[cand] for cand in title_cands if cand in lower_map), None)
    df["req_title"] = df[mapped_title].astype(str) if mapped_title else "Specification " + df["req_id"]

    # 3. Map rule_description
    desc_cands = ["rule_description", "description", "rule", "requirement", "spec", "specification", "acceptance_criteria", "details", "text"]
    mapped_desc = next((lower_map[cand] for cand in desc_cands if cand in lower_map), None)
    df["rule_description"] = df[mapped_desc].astype(str) if mapped_desc else df["req_title"]

    # 4. Map module
    mod_cands = ["module", "service", "component", "domain", "system", "feature", "area"]
    mapped_mod = next((lower_map[cand] for cand in mod_cands if cand in lower_map), None)
    df["module"] = df[mapped_mod].astype(str) if mapped_mod else "Core Service"

    # 5. Map criticality
    crit_cands = ["criticality", "severity", "priority", "importance"]
    mapped_crit = next((lower_map[cand] for cand in crit_cands if cand in lower_map), None)
    df["criticality"] = df[mapped_crit].astype(str) if mapped_crit else "High"

    return df


def normalize_tests_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes uploaded test_cases.csv columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    lower_map = {c.lower().replace(" ", "_").replace("-", "_"): c for c in df.columns}

    # 1. Map test_id
    id_cands = ["test_id", "id", "test_case_id", "tc_id", "testid", "testcase_id", "key"]
    mapped_id = next((lower_map[cand] for cand in id_cands if cand in lower_map), None)
    df["test_id"] = df[mapped_id].astype(str).str.strip() if mapped_id else [f"TC-{i+1:03d}" for i in range(len(df))]

    # 2. Map req_id
    req_cands = ["req_id", "requirement_id", "rule_id", "reqid", "linked_requirement", "requirement", "rule", "req"]
    mapped_req = next((lower_map[cand] for cand in req_cands if cand in lower_map), None)
    df["req_id"] = df[mapped_req].astype(str).str.strip().str.upper() if mapped_req else "REQ-101"

    # 3. Map test_title
    title_cands = ["test_title", "title", "name", "test_name", "summary", "description", "test_case_name"]
    mapped_title = next((lower_map[cand] for cand in title_cands if cand in lower_map), None)
    df["test_title"] = df[mapped_title].astype(str) if mapped_title else "Verify Test " + df["test_id"]

    # 4. Map execution_status
    stat_cands = ["execution_status", "status", "result", "state", "outcome"]
    mapped_stat = next((lower_map[cand] for cand in stat_cands if cand in lower_map), None)
    df["execution_status"] = df[mapped_stat].astype(str) if mapped_stat else "PASSED"

    # 5. Map test_type
    type_cands = ["test_type", "type", "category", "level"]
    mapped_type = next((lower_map[cand] for cand in type_cands if cand in lower_map), None)
    df["test_type"] = df[mapped_type].astype(str) if mapped_type else "Unit"

    return df
