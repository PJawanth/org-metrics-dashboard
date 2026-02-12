#!/usr/bin/env python3
"""
Schema definitions and validation for metrics collector/aggregator.
Ensures consistent data contracts and catches drift early.
"""

from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
# RAW REPO JSON SCHEMA (per-repo collected data)
# ============================================================================

RAW_REPO_REQUIRED_FIELDS = {
    "name": str,
    "full_name": str,
    "url": str,
    "description": (str, type(None)),
    "language": (str, type(None)),
    "is_archived": bool,
    "is_fork": bool,
    "is_private": bool,
    "created_at": str,
    "updated_at": str,
    "pushed_at": str,
    "stars": int,
    "forks": int,
    "health_score": int,
    "collected_at": str,
}

RAW_REPO_NESTED_SCHEMAS = {
    "dora": {
        "deployment_freq": str,
        "releases_per_month": (int, float),
        "lead_time_hours": (int, float),
        "lead_time_days": (int, float),
        "mttr_hours": (int, float),
        "cfr": (int, float),  # CI failure rate, NOT DORA CFR
        "cfr_category": str,
    },
    "flow": {
        "review_time": (int, float),
        "cycle_time": (int, float),
        "wip": int,
        "throughput": int,
    },
    "pr": {
        "total": int,
        "open": int,
        "merged_30d": int,
        "throughput": int,
        "wip": int,
        "stale": int,
        "lead_time_hours": (int, float),
        "lead_time_days": (int, float),
        "review_time_hours": (int, float),
        "cycle_time_hours": (int, float),
        "merge_rate": (int, float),
        "truncated": bool,  # true if results were paginated and capped
    },
    "issues": {
        "total": int,
        "open": int,
        "closed_30d": int,
        "mttr_hours": (int, float),
        "bugs": int,
        "critical": int,
        "security": int,
        "stale": int,
        "truncated": bool,
    },
    "ci": {
        "has_ci": bool,
        "workflows": int,
        "runs_30d": int,
        "success_rate": (int, float),
        "failure_rate": (int, float),
        "duration_mins": (int, float),
        "ci_failure_rate": (int, float),  # Renamed from cfr for clarity
        "truncated": bool,
    },
    "security": {
        "score": int,
        "critical": int,
        "high": int,
        "medium": int,
        "low": int,
        "total_vulns": int,
        "secrets": int,
        "dependency_alerts": int,
        "code_alerts": int,
        "security_policy": bool,
        "branch_protection": bool,
        "dependabot": bool,
        "secret_scanning": bool,
        "code_scanning": bool,
        "gate_pass": bool,
        "license": (str, type(None)),
        "security_mttr_hours": (int, float, type(None)),  # Real MTTR or null
        "dependabot_truncated": bool,
        "code_scanning_truncated": bool,
        "secret_scanning_truncated": bool,
        "available_dependabot": bool,  # Permission available
        "available_code_scanning": bool,
        "available_secret_scanning": bool,
        "errors": list,  # List of {"field": str, "reason": str}
    },
    "commits": {
        "count_30d": int,
        "authors": int,
        "top": list,  # [{"login": str, "commits": int}, ...]
    },
    "risk": {
        "score": int,
        "level": str,
        "factors": list,
    },
}

# ============================================================================
# AGGREGATED DASHBOARD JSON SCHEMA
# ============================================================================

AGGREGATED_DASHBOARD_REQUIRED_FIELDS = {
    "org_name": str,
    "generated_at": str,
    "run_id": str,  # Unique identifier for this aggregation run
    "repos": list,  # List of repo rows
    "dora": dict,
    "flow": dict,
    "ci": dict,
    "security": dict,
    "issues": dict,
    "governance": dict,
    "languages": list,
    "contributors": list,
}

AGGREGATED_DASHBOARD_NESTED_SCHEMAS = {
    "dora": {
        "deployment_frequency": dict,  # {"value": float, "category": str, "unit": str}
        "lead_time": dict,
        "mttr": dict,
        "ci_failure_rate": dict,  # Renamed from cfr
        "overall": str,
    },
    "flow": {
        "review_time_avg": (int, float, type(None)),
        "cycle_time_avg": (int, float, type(None)),
        "total_wip": int,
        "total_throughput": int,
    },
    "ci": {
        "adoption": (int, float),
        "success_rate": (int, float),
        "failure_rate": (int, float, type(None)),
        "avg_duration": (int, float, type(None)),
        "total_runs": int,
    },
    "security": {
        "critical_vulns": int,
        "high_vulns": int,
        "medium_vulns": int,
        "low_vulns": int,
        "total_vulns": int,
        "vuln_trend": (str, type(None)),  # "Improving", "Stable", "Worsening", or null
        "security_mttr": (int, float, type(None)),  # null if not available
        "sla_compliance": (int, float),
        "secrets_exposed": int,
        "dependency_risk": int,
        "code_issues": int,
        "gate_pass_rate": (int, float),
        "branch_protection": (int, float),
        "dependabot_adoption": (int, float),
        "secret_scanning": (int, float),
        "code_scanning": (int, float),
        "security_policy": (int, float),
        "license_compliance": (int, float),
    },
    "issues": {
        "open_count": int,
        "closed_30d": int,
        "bug_count": int,
    },
    "governance": {
        "total_repos": int,
        "scanned_repos": int,
        "scan_coverage": (int, float),
        "archived_repos": int,
        "forked_repos": int,
        "risk_critical": int,
        "risk_high": int,
        "risk_medium": int,
        "risk_low": int,
    },
}


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_type(value: Any, expected_types: tuple) -> bool:
    """Check if value matches expected type(s)."""
    if not isinstance(expected_types, tuple):
        expected_types = (expected_types,)
    return isinstance(value, expected_types)


def validate_dict_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    path: str = "root",
) -> Tuple[bool, List[str]]:
    """
    Validate dict against schema definition.
    Returns (is_valid, list_of_errors).
    """
    errors = []

    if not isinstance(data, dict):
        return False, [f"{path}: expected dict, got {type(data).__name__}"]

    for key, expected_type in schema.items():
        if key not in data:
            errors.append(f"{path}.{key}: missing required field")
            continue

        value = data[key]

        # Handle nested schemas
        if isinstance(expected_type, dict):
            if isinstance(value, dict):
                nested_valid, nested_errors = validate_dict_schema(
                    value, expected_type, f"{path}.{key}"
                )
                errors.extend(nested_errors)
            else:
                errors.append(f"{path}.{key}: expected dict, got {type(value).__name__}")
        # Handle list type (don't validate contents, just check it's a list)
        elif expected_type == list:
            if not isinstance(value, list):
                errors.append(f"{path}.{key}: expected list, got {type(value).__name__}")
        # Handle type tuples (multiple allowed types)
        elif isinstance(expected_type, tuple):
            if not validate_type(value, expected_type):
                type_names = " or ".join(t.__name__ for t in expected_type)
                errors.append(
                    f"{path}.{key}: expected {type_names}, got {type(value).__name__}"
                )
        # Handle simple types
        elif not validate_type(value, (expected_type,)):
            errors.append(
                f"{path}.{key}: expected {expected_type.__name__}, got {type(value).__name__}"
            )

    return len(errors) == 0, errors


def validate_raw_repo(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate raw repo json collected by collect.py."""
    # Validate top-level fields
    valid, errors = validate_dict_schema(data, RAW_REPO_REQUIRED_FIELDS, "repo")

    # Validate nested sections
    for section, schema in RAW_REPO_NESTED_SCHEMAS.items():
        if section in data:
            nested_valid, nested_errors = validate_dict_schema(
                data[section], schema, f"repo.{section}"
            )
            errors.extend(nested_errors)

    return len(errors) == 0, errors


def validate_aggregated_dashboard(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate aggregated dashboard.json."""
    valid, errors = validate_dict_schema(data, AGGREGATED_DASHBOARD_REQUIRED_FIELDS, "dashboard")

    # Validate nested sections
    for section, schema in AGGREGATED_DASHBOARD_NESTED_SCHEMAS.items():
        if section in data:
            nested_valid, nested_errors = validate_dict_schema(
                data[section], schema, f"dashboard.{section}"
            )
            errors.extend(nested_errors)

    return len(errors) == 0, errors


def assert_raw_repo(data: Dict[str, Any], repo_name: str) -> None:
    """Assert raw repo is valid or raise with detailed error."""
    valid, errors = validate_raw_repo(data)
    if not valid:
        msg = f"Schema validation failed for repo '{repo_name}':\n  " + "\n  ".join(errors)
        raise ValueError(msg)


def assert_aggregated_dashboard(data: Dict[str, Any]) -> None:
    """Assert dashboard is valid or raise with detailed error."""
    valid, errors = validate_aggregated_dashboard(data)
    if not valid:
        msg = f"Schema validation failed for aggregated dashboard:\n  " + "\n  ".join(errors)
        raise ValueError(msg)
