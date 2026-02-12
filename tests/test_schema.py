#!/usr/bin/env python3
"""
Basic unit tests for schema validation and metrics.
Run: python -m pytest tests/test_metrics.py -v
"""

import json
import sys
from pathlib import Path

# Add metrics module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "metrics"))

from schema import (
    validate_raw_repo,
    validate_aggregated_dashboard,
    assert_raw_repo,
    assert_aggregated_dashboard,
)


# ============================================================================
# SAMPLE DATA FOR TESTING
# ============================================================================


SAMPLE_RAW_REPO = {
    "name": "test-repo",
    "full_name": "org/test-repo",
    "description": "Test repository",
    "url": "https://github.com/org/test-repo",
    "language": "Python",
    "is_archived": False,
    "is_fork": False,
    "is_private": False,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-02-01T00:00:00Z",
    "pushed_at": "2024-02-01T00:00:00Z",
    "stars": 10,
    "forks": 5,
    "health_score": 75,
    "collected_at": "2024-02-12T00:00:00Z",
    "dora": {
        "deployment_freq": "High",
        "releases_per_month": 4.5,
        "lead_time_hours": 24.0,
        "lead_time_days": 1.0,
        "mttr_hours": 2.0,
        "cfr": 10.0,
        "cfr_category": "High",
    },
    "flow": {
        "review_time": 4.0,
        "cycle_time": 24.0,
        "wip": 3,
        "throughput": 10,
    },
    "pr": {
        "total": 50,
        "open": 3,
        "merged_30d": 10,
        "throughput": 10,
        "wip": 3,
        "stale": 0,
        "lead_time_hours": 24.0,
        "lead_time_days": 1.0,
        "review_time_hours": 4.0,
        "cycle_time_hours": 24.0,
        "merge_rate": 95.0,
        "truncated": False,
    },
    "issues": {
        "total": 15,
        "open": 5,
        "closed_30d": 10,
        "mttr_hours": 48.0,
        "bugs": 2,
        "critical": 0,
        "security": 0,
        "stale": 1,
        "truncated": False,
    },
    "ci": {
        "has_ci": True,
        "workflows": 3,
        "runs_30d": 30,
        "success_rate": 95.0,
        "failure_rate": 5.0,
        "ci_failure_rate": 5.0,
        "duration_mins": 15.0,
        "truncated": False,
    },
    "security": {
        "score": 80,
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "total_vulns": 6,
        "secrets": 0,
        "dependency_alerts": 1,
        "code_alerts": 0,
        "security_policy": True,
        "branch_protection": True,
        "dependabot": True,
        "secret_scanning": True,
        "code_scanning": False,
        "gate_pass": True,
        "license": "MIT",
        "security_mttr_hours": 24.0,
        "available_dependabot": True,
        "available_code_scanning": True,
        "available_secret_scanning": True,
        "dependabot_truncated": False,
        "code_scanning_truncated": False,
        "secret_scanning_truncated": False,
        "errors": [],
    },
    "commits": {
        "count_30d": 50,
        "authors": 5,
        "top": [
            {"login": "alice", "commits": 20},
            {"login": "bob", "commits": 15},
        ],
    },
    "risk": {
        "score": 20,
        "level": "Low",
        "factors": ["Healthy repository"],
    },
}


SAMPLE_DASHBOARD = {
    "org_name": "test-org",
    "generated_at": "2024-02-12 12:00 UTC",
    "run_id": "test-run-001",
    "repos": [],
    "dora": {
        "deployment_frequency": {
            "value": 4.5,
            "category": "High",
            "unit": "releases/month",
        },
        "lead_time": {
            "value": 24.0,
            "category": "High",
            "unit": "hours",
        },
        "mttr": {
            "value": 2.0,
            "category": "Elite",
            "unit": "hours",
        },
        "ci_failure_rate": {
            "value": 10.0,
            "category": "High",
            "unit": "%",
        },
        "overall": "High",
    },
    "flow": {
        "review_time_avg": 4.0,
        "cycle_time_avg": 24.0,
        "total_wip": 10,
        "total_throughput": 50,
    },
    "ci": {
        "adoption": 90.0,
        "success_rate": 95.0,
        "failure_rate": 5.0,
        "avg_duration": 15.0,
        "total_runs": 100,
    },
    "security": {
        "critical_vulns": 0,
        "high_vulns": 5,
        "medium_vulns": 10,
        "low_vulns": 15,
        "total_vulns": 30,
        "vuln_trend": "Stable",
        "security_mttr": 24.0,
        "sla_compliance": 90.0,
        "secrets_exposed": 0,
        "dependency_risk": 10,
        "code_issues": 5,
        "gate_pass_rate": 85.0,
        "branch_protection": 95.0,
        "dependabot_adoption": 90.0,
        "secret_scanning": 85.0,
        "code_scanning": 80.0,
        "security_policy": 85.0,
        "license_compliance": 75.0,
    },
    "issues": {
        "open_count": 50,
        "closed_30d": 100,
        "bug_count": 10,
    },
    "governance": {
        "total_repos": 50,
        "scanned_repos": 50,
        "scan_coverage": 100.0,
        "archived_repos": 5,
        "forked_repos": 3,
        "risk_critical": 2,
        "risk_high": 5,
        "risk_medium": 10,
        "risk_low": 33,
    },
    "languages": [
        {"name": "Python", "count": 20},
        {"name": "JavaScript", "count": 15},
    ],
    "contributors": [
        {"login": "alice", "commits": 500, "repo_count": 10},
        {"login": "bob", "commits": 400, "repo_count": 8},
    ],
}


# ============================================================================
# TESTS
# ============================================================================


def test_raw_repo_schema_valid():
    """Test that sample raw repo passes schema validation."""
    valid, errors = validate_raw_repo(SAMPLE_RAW_REPO)
    assert valid, f"Schema validation failed: {errors}"


def test_raw_repo_schema_missing_field():
    """Test that validation fails when required field is missing."""
    bad_repo = SAMPLE_RAW_REPO.copy()
    del bad_repo["name"]
    valid, errors = validate_raw_repo(bad_repo)
    assert not valid, "Should fail when required field missing"
    assert any("name" in e for e in errors), "Error should mention missing 'name' field"


def test_raw_repo_schema_wrong_type():
    """Test that validation fails when field has wrong type."""
    bad_repo = SAMPLE_RAW_REPO.copy()
    bad_repo["stars"] = "not-a-number"
    valid, errors = validate_raw_repo(bad_repo)
    assert not valid, "Should fail when field type is wrong"


def test_aggregated_dashboard_schema_valid():
    """Test that sample dashboard passes schema validation."""
    valid, errors = validate_aggregated_dashboard(SAMPLE_DASHBOARD)
    assert valid, f"Schema validation failed: {errors}"


def test_aggregated_dashboard_missing_field():
    """Test that validation fails when required field is missing."""
    bad_dashboard = SAMPLE_DASHBOARD.copy()
    del bad_dashboard["org_name"]
    valid, errors = validate_aggregated_dashboard(bad_dashboard)
    assert not valid, "Should fail when required field missing"


def test_assert_raw_repo_raises_on_invalid():
    """Test that assert_raw_repo raises exception on invalid data."""
    bad_repo = SAMPLE_RAW_REPO.copy()
    bad_repo["is_archived"] = "not-a-boolean"

    try:
        assert_raw_repo(bad_repo, "test-repo")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "is_archived" in str(e)


def test_null_security_mttr():
    """Test that security MTTR can be null."""
    repo = SAMPLE_RAW_REPO.copy()
    repo["security"]["security_mttr_hours"] = None
    valid, errors = validate_raw_repo(repo)
    assert valid, f"Should allow null security_mttr_hours: {errors}"


def test_null_vuln_trend():
    """Test that vuln_trend can be null."""
    dashboard = SAMPLE_DASHBOARD.copy()
    dashboard["security"]["vuln_trend"] = None
    valid, errors = validate_aggregated_dashboard(dashboard)
    assert valid, f"Should allow null vuln_trend: {errors}"


# ============================================================================
# RUN TESTS
# ============================================================================


if __name__ == "__main__":
    print("Running schema validation tests...\n")

    tests = [
        test_raw_repo_schema_valid,
        test_raw_repo_schema_missing_field,
        test_raw_repo_schema_wrong_type,
        test_aggregated_dashboard_schema_valid,
        test_aggregated_dashboard_missing_field,
        test_assert_raw_repo_raises_on_invalid,
        test_null_security_mttr,
        test_null_vuln_trend,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print(f"{'='*60}")

    sys.exit(0 if failed == 0 else 1)
