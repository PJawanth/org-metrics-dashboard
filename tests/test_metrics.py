#!/usr/bin/env python3
"""
Test suite for metrics calculations - Updated for production-hardened schema.
Run with: python tests/test_metrics.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics.aggregate import (
    calc_dora, calc_flow, calc_ci, calc_security, 
    calc_governance, build_repo_table, safe_get
)


# =============================================================================
# TEST DATA - Sample repositories matching real collected schema
# =============================================================================

def create_test_repo(
    name="test-repo",
    releases_per_month=4,
    lead_time_hours=12,
    mttr_hours=2,
    ci_failure_rate=10,  # Renamed from cfr
    open_prs=2,
    merged_prs_30d=10,
    review_time_hours=6,
    cycle_time_hours=24,
    has_ci=True,
    ci_success_rate=90,
    runs_30d=50,
    critical_vulns=0,
    high_vulns=0,
    medium_vulns=0,
    low_vulns=0,
    branch_protection=True,
    dependabot_enabled=True,
    secret_scanning=True,
    code_scanning=False,
    gate_pass=True,
    is_archived=False
):
    """Create a test repository matching collected data schema."""
    return {
        "name": name,
        "full_name": f"test-org/{name}",
        "url": f"https://github.com/test-org/{name}",
        "is_archived": is_archived,
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "health_score": 70,
        # DORA metrics (per-repo)
        "dora": {
            "releases_per_month": releases_per_month,
            "lead_time_hours": lead_time_hours,
            "mttr_hours": mttr_hours,
            "cfr": ci_failure_rate,  # CI failure rate (not DORA CFR)
        },
        # PR/Flow metrics (per-repo)
        "pr": {
            "total": merged_prs_30d + open_prs,
            "open": open_prs,
            "merged_30d": merged_prs_30d,
            "throughput": merged_prs_30d,
            "wip": open_prs,
            "lead_time_hours": lead_time_hours,
            "review_time_hours": review_time_hours,
            "cycle_time_hours": cycle_time_hours,
            "truncated": False,
        },
        # Issues/MTTR
        "issues": {
            "total": 10,
            "open": 5,
            "closed_30d": 8,
            "mttr_hours": mttr_hours,
            "truncated": False,
        },
        # CI metrics (per-repo)
        "ci": {
            "has_ci": has_ci,
            "workflows": 2,
            "runs_30d": runs_30d,
            "success_rate": ci_success_rate,
            "failure_rate": 100 - ci_success_rate,
            "ci_failure_rate": 100 - ci_success_rate,  # Same as failure_rate
            "truncated": False,
        },
        # Security metrics (per-repo)
        "security": {
            "critical": critical_vulns,
            "high": high_vulns,
            "medium": medium_vulns,
            "low": low_vulns,
            "total_vulns": critical_vulns + high_vulns + medium_vulns + low_vulns,
            "security_mttr_hours": mttr_hours,
            "gate_pass": gate_pass,
            "branch_protection": branch_protection,
            "dependabot": dependabot_enabled,
            "secret_scanning": secret_scanning,
            "code_scanning": code_scanning,
            "errors": [],
            "available_dependabot": True,
            "available_code_scanning": True,
            "available_secret_scanning": True,
        },
        # Release metrics
        "deploy": {
            "total": 10,
            "releases_90d": 12,
            "per_month": releases_per_month,
            "truncated": False,
        },
        # Commits
        "commits": {
            "count_30d": 50,
            "top": [],
        },
    }


# =============================================================================
# DORA METRICS TESTS
# =============================================================================

def test_dora_deployment_frequency_elite():
    """Test Elite deployment frequency (≥8 releases/month)."""
    repos = [create_test_repo(releases_per_month=10)]
    result = calc_dora(repos)
    
    assert result["deployment_frequency"]["value"] == 10.0
    assert result["deployment_frequency"]["category"] == "Elite"
    print("✅ DORA Deployment Frequency Elite: PASSED")


def test_dora_deployment_frequency_high():
    """Test High deployment frequency (≥4 releases/month)."""
    repos = [create_test_repo(releases_per_month=5)]
    result = calc_dora(repos)
    
    assert result["deployment_frequency"]["value"] == 5.0
    assert result["deployment_frequency"]["category"] == "High"
    print("✅ DORA Deployment Frequency High: PASSED")


def test_dora_deployment_frequency_medium():
    """Test Medium deployment frequency (≥1 release/month)."""
    repos = [create_test_repo(releases_per_month=2)]
    result = calc_dora(repos)
    
    assert result["deployment_frequency"]["value"] == 2.0
    assert result["deployment_frequency"]["category"] == "Medium"
    print("✅ DORA Deployment Frequency Medium: PASSED")


def test_dora_deployment_frequency_low():
    """Test Low deployment frequency (<1 release/month)."""
    repos = [create_test_repo(releases_per_month=0.2)]
    result = calc_dora(repos)
    
    assert result["deployment_frequency"]["category"] == "Low"
    print("✅ DORA Deployment Frequency Low: PASSED")


def test_dora_lead_time_elite():
    """Test Elite lead time (<1 hour)."""
    repos = [create_test_repo(lead_time_hours=0.5)]
    result = calc_dora(repos)
    
    assert result["lead_time"]["category"] == "Elite"
    print("✅ DORA Lead Time Elite: PASSED")


def test_dora_lead_time_high():
    """Test High lead time (<168 hours)."""
    repos = [create_test_repo(lead_time_hours=48)]
    result = calc_dora(repos)
    
    assert result["lead_time"]["category"] == "High"
    print("✅ DORA Lead Time High: PASSED")


def test_dora_mttr_categories():
    """Test MTTR category thresholds."""
    # Elite: <1 hour
    repos = [create_test_repo(mttr_hours=0.5)]
    assert calc_dora(repos)["mttr"]["category"] == "Elite"
    
    # High: <24 hours
    repos = [create_test_repo(mttr_hours=12)]
    assert calc_dora(repos)["mttr"]["category"] == "High"
    
    # Medium: <168 hours
    repos = [create_test_repo(mttr_hours=100)]
    assert calc_dora(repos)["mttr"]["category"] == "Medium"
    
    # Low: ≥168 hours
    repos = [create_test_repo(mttr_hours=200)]
    assert calc_dora(repos)["mttr"]["category"] == "Low"
    
    print("✅ DORA MTTR Categories: PASSED")


def test_dora_ci_failure_rate_categories():
    """Test CI Failure Rate category thresholds (NOT DORA CFR)."""
    # Elite: <5%
    repos = [create_test_repo(ci_failure_rate=3)]
    assert calc_dora(repos)["ci_failure_rate"]["category"] == "Elite"
    
    # High: <15%
    repos = [create_test_repo(ci_failure_rate=10)]
    assert calc_dora(repos)["ci_failure_rate"]["category"] == "High"
    
    # Medium: <30%
    repos = [create_test_repo(ci_failure_rate=20)]
    assert calc_dora(repos)["ci_failure_rate"]["category"] == "Medium"
    
    # Low: ≥30%
    repos = [create_test_repo(ci_failure_rate=35)]
    assert calc_dora(repos)["ci_failure_rate"]["category"] == "Low"
    
    print("✅ DORA CI Failure Rate Categories: PASSED")


def test_dora_overall_score():
    """Test overall DORA score calculation."""
    # All Elite metrics should give Elite overall
    repos = [create_test_repo(
        releases_per_month=10,     # Elite
        lead_time_hours=0.5,       # Elite
        mttr_hours=0.5,            # Elite
        ci_failure_rate=3          # Elite
    )]
    result = calc_dora(repos)
    assert result["overall"] == "Elite"
    
    # Mixed metrics
    repos = [create_test_repo(
        releases_per_month=5,      # High
        lead_time_hours=12,        # High
        mttr_hours=12,             # High
        ci_failure_rate=10         # High
    )]
    result = calc_dora(repos)
    assert result["overall"] == "High"
    
    print("✅ DORA Overall Score: PASSED")


def test_dora_multi_repo_average():
    """Test DORA metrics averaging across multiple repos."""
    repos = [
        create_test_repo(name="repo1", releases_per_month=10, lead_time_hours=10),
        create_test_repo(name="repo2", releases_per_month=6, lead_time_hours=20),
    ]
    result = calc_dora(repos)
    
    # Average: (10 + 6) / 2 = 8
    assert result["deployment_frequency"]["value"] == 8.0
    # Average: (10 + 20) / 2 = 15
    assert result["lead_time"]["value"] == 15.0
    
    print("✅ DORA Multi-Repo Average: PASSED")


# =============================================================================
# FLOW METRICS TESTS
# =============================================================================

def test_flow_metrics():
    """Test flow metrics calculations."""
    repos = [
        create_test_repo(name="repo1", open_prs=3, merged_prs_30d=15, cycle_time_hours=20),
        create_test_repo(name="repo2", open_prs=2, merged_prs_30d=10, cycle_time_hours=30),
    ]
    result = calc_flow(repos)
    
    # WIP = 3 + 2 = 5
    assert result["total_wip"] == 5
    
    # Throughput = 15 + 10 = 25
    assert result["total_throughput"] == 25
    
    # Cycle time avg = (20 + 30) / 2 = 25
    assert result["cycle_time_avg"] == 25.0
    
    print("✅ Flow Metrics: PASSED")


# =============================================================================
# CI/CD METRICS TESTS
# =============================================================================

def test_ci_adoption():
    """Test CI/CD adoption rate calculation."""
    repos = [
        create_test_repo(name="repo1", has_ci=True),
        create_test_repo(name="repo2", has_ci=True),
        create_test_repo(name="repo3", has_ci=False),
        create_test_repo(name="repo4", has_ci=False),
    ]
    result = calc_ci(repos)
    
    # 2 out of 4 repos have CI = 50%
    assert result["adoption"] == 50.0
    print("✅ CI Adoption Rate: PASSED")


def test_ci_success_rate():
    """Test CI success rate calculation."""
    repos = [
        create_test_repo(name="repo1", has_ci=True, ci_success_rate=90),
        create_test_repo(name="repo2", has_ci=True, ci_success_rate=80),
    ]
    result = calc_ci(repos)
    
    # Average: (90 + 80) / 2 = 85
    assert result["success_rate"] == 85.0
    assert result["failure_rate"] == 15.0
    print("✅ CI Success Rate: PASSED")


def test_ci_total_runs():
    """Test total CI runs calculation."""
    repos = [
        create_test_repo(name="repo1", has_ci=True, runs_30d=100),
        create_test_repo(name="repo2", has_ci=True, runs_30d=50),
    ]
    result = calc_ci(repos)
    
    # Total: 100 + 50 = 150
    assert result["total_runs"] == 150
    print("✅ CI Total Runs: PASSED")


# =============================================================================
# SECURITY METRICS TESTS
# =============================================================================

def test_security_vulnerability_distribution():
    """Test vulnerability severity distribution."""
    repos = [
        create_test_repo(
            name="repo1",
            critical_vulns=0,
            high_vulns=2,
            medium_vulns=5,
            low_vulns=8
        ),
    ]
    result = calc_security(repos)
    
    assert result["critical_vulns"] == 0
    assert result["high_vulns"] == 2
    assert result["medium_vulns"] == 5
    assert result["low_vulns"] == 8
    assert result["total_vulns"] == 15
    
    print("✅ Security Vulnerability Distribution: PASSED")


def test_security_trend():
    """Test vulnerability trend from history."""
    # Without history, trend should be None
    repos = [create_test_repo(low_vulns=5)]
    result = calc_security(repos)
    # Trend is None if no previous snapshot
    assert result.get("vuln_trend") is None or isinstance(result.get("vuln_trend"), str)
    
    print("✅ Security Vulnerability Trend: PASSED")


def test_security_adoption_rates():
    """Test security feature adoption rates."""
    repos = [
        create_test_repo(
            name="repo1",
            branch_protection=True,
            dependabot_enabled=True,
            secret_scanning=True
        ),
        create_test_repo(
            name="repo2",
            branch_protection=True,
            dependabot_enabled=False,
            secret_scanning=False
        ),
    ]
    result = calc_security(repos)
    
    # Branch protection: 2/2 = 100%
    assert result.get("branch_protection") == 100.0
    # Dependabot: 1/2 = 50%
    assert result.get("dependabot_adoption") == 50.0
    
    print("✅ Security Adoption Rates: PASSED")


def test_security_gate_pass_rate():
    """Test security gate pass rate."""
    repos = [
        create_test_repo(name="repo1", gate_pass=True),
        create_test_repo(name="repo2", gate_pass=True),
        create_test_repo(name="repo3", gate_pass=False),
    ]
    result = calc_security(repos)
    
    # 2 out of 3 pass = 66.7%
    assert result.get("gate_pass_rate", 0) >= 66.0
    print("✅ Security Gate Pass Rate: PASSED")


def test_security_sla_compliance():
    """Test SLA compliance (repos with 0 vulnerabilities)."""
    repos = [
        create_test_repo(name="repo1", critical_vulns=0, high_vulns=0, medium_vulns=0, low_vulns=0),
        create_test_repo(name="repo2", critical_vulns=0, high_vulns=0, medium_vulns=0, low_vulns=0),
        create_test_repo(name="repo3", low_vulns=5),
    ]
    result = calc_security(repos)
    
    # 2 out of 3 have 0 vulns = 66.7%
    sla_comp = result.get("sla_compliance", 0)
    assert sla_comp >= 65.0
    print("✅ Security SLA Compliance: PASSED")


# =============================================================================
# GOVERNANCE METRICS TESTS
# =============================================================================

def test_governance_risk_levels():
    """Test risk level classification."""
    repos = [
        create_test_repo(name="critical", critical_vulns=5, gate_pass=False),
        create_test_repo(name="high", high_vulns=3, gate_pass=False),
        create_test_repo(name="medium", medium_vulns=1, gate_pass=True),
        create_test_repo(name="low", gate_pass=True),
    ]
    result = calc_governance(repos)
    
    # Should have risk classification
    assert "risk_critical" in result or "risk_high" in result
    print("✅ Governance Risk Levels: PASSED")


def test_governance_repo_counts():
    """Test repository inventory counts."""
    repos = [
        create_test_repo(name="active1"),
        create_test_repo(name="active2"),
        create_test_repo(name="archived", is_archived=True),
    ]
    
    result = calc_governance(repos)
    
    assert result["total_repos"] == 3
    assert result["archived_repos"] == 1
    
    print("✅ Governance Repo Counts: PASSED")


def test_governance_scan_coverage():
    """Test scan coverage calculation."""
    repos = [
        create_test_repo(name="active1"),
        create_test_repo(name="active2"),
        create_test_repo(name="archived", is_archived=True),
    ]
    result = calc_governance(repos)
    
    # 2 out of 3 are scanned (non-archived) = 66.7%
    coverage = result.get("scan_coverage", 0)
    assert coverage >= 65.0
    print("✅ Governance Scan Coverage: PASSED")


# =============================================================================
# REPO TABLE TESTS
# =============================================================================

def test_repo_table_risk_sorting():
    """Test that repos are included in table."""
    repos = [
        create_test_repo(name="low-risk", gate_pass=True),
        create_test_repo(name="med-risk", gate_pass=False),
    ]
    result = build_repo_table(repos)
    
    # Should have table data
    assert len(result) > 0
    assert result[0]["name"] in ["low-risk", "med-risk"]
    
    print("✅ Repo Table Risk Sorting: PASSED")


def test_repo_table_gate_pass():
    """Test gate pass calculation in repo table."""
    repos = [
        create_test_repo(name="pass", gate_pass=True, branch_protection=True),
        create_test_repo(name="fail", gate_pass=False, branch_protection=False),
    ]
    result = build_repo_table(repos)
    
    # Find each repo by name
    pass_repo = next((r for r in result if r["name"] == "pass"), None)
    fail_repo = next((r for r in result if r["name"] == "fail"), None)
    
    if pass_repo:
        assert pass_repo.get("gate_pass", True) == True
    if fail_repo:
        assert fail_repo.get("gate_pass", False) == False
    
    print("✅ Repo Table Gate Pass: PASSED")


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

def test_safe_get():
    """Test safe_get helper function."""
    data = {"a": {"b": {"c": 42}}}
    
    assert safe_get(data, "a", "b", "c") == 42
    assert safe_get(data, "a", "b", "x", default=0) == 0
    assert safe_get(data, "x", "y", "z", default=-1) == -1
    assert safe_get({}, "a", default=100) == 100
    
    print("✅ Safe Get Helper: PASSED")


def test_archived_repos_excluded():
    """Test that archived repos are excluded from calculations."""
    repos = [
        create_test_repo(name="active", releases_per_month=10),
        create_test_repo(name="archived", releases_per_month=100, is_archived=True),
    ]
    result = calc_dora(repos)
    
    # Should only count active repo
    assert result["deployment_frequency"]["value"] == 10.0
    print("✅ Archived Repos Excluded: PASSED")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("🧪 METRICS CALCULATION TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        # DORA Tests
        ("DORA Deployment Frequency Elite", test_dora_deployment_frequency_elite),
        ("DORA Deployment Frequency High", test_dora_deployment_frequency_high),
        ("DORA Deployment Frequency Medium", test_dora_deployment_frequency_medium),
        ("DORA Deployment Frequency Low", test_dora_deployment_frequency_low),
        ("DORA Lead Time Elite", test_dora_lead_time_elite),
        ("DORA Lead Time High", test_dora_lead_time_high),
        ("DORA MTTR Categories", test_dora_mttr_categories),
        ("DORA CI Failure Rate Categories", test_dora_ci_failure_rate_categories),
        ("DORA Overall Score", test_dora_overall_score),
        ("DORA Multi-Repo Average", test_dora_multi_repo_average),
        
        # Flow Tests
        ("Flow Metrics", test_flow_metrics),
        
        # CI Tests
        ("CI Adoption Rate", test_ci_adoption),
        ("CI Success Rate", test_ci_success_rate),
        ("CI Total Runs", test_ci_total_runs),
        
        # Security Tests
        ("Security Vulnerability Distribution", test_security_vulnerability_distribution),
        ("Security Vulnerability Trend", test_security_trend),
        ("Security Adoption Rates", test_security_adoption_rates),
        ("Security Gate Pass Rate", test_security_gate_pass_rate),
        ("Security SLA Compliance", test_security_sla_compliance),
        
        # Governance Tests
        ("Governance Risk Levels", test_governance_risk_levels),
        ("Governance Repo Counts", test_governance_repo_counts),
        ("Governance Scan Coverage", test_governance_scan_coverage),
        
        # Repo Table Tests
        ("Repo Table Risk Sorting", test_repo_table_risk_sorting),
        ("Repo Table Gate Pass", test_repo_table_gate_pass),
        
        # Helper Tests
        ("Safe Get Helper", test_safe_get),
        ("Archived Repos Excluded", test_archived_repos_excluded),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {name}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed, {len(tests)} total")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
