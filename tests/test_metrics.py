#!/usr/bin/env python3
"""
Test suite for metrics calculations.
Run with: python -m pytest tests/test_metrics.py -v
Or simply: python tests/test_metrics.py
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
# TEST DATA - Sample repositories with known values
# =============================================================================

def create_test_repo(
    name="test-repo",
    releases_per_month=4,
    lead_time_hours=12,
    mttr_hours=2,
    cfr=10,
    open_prs=2,
    merged_prs=10,
    merge_time_hours=24,
    has_ci=True,
    ci_success_rate=90,
    workflow_runs=50,
    vulnerability_count=0,
    branch_protection=True,
    dependabot=True,
    secret_scanning=True,
    code_scanning=False,
    security_score=75,
    is_archived=False
):
    """Create a test repository with configurable metrics."""
    return {
        "name": name,
        "full_name": f"test-org/{name}",
        "url": f"https://github.com/test-org/{name}",
        "is_archived": is_archived,
        "updated_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "health_score": 70,
        "dora": {
            "releases_per_month": releases_per_month,
            "lead_time_hours": lead_time_hours,
            "mttr_hours": mttr_hours,
            "change_failure_rate": cfr,
            "deployment_frequency": "High" if releases_per_month >= 4 else "Medium"
        },
        "pull_requests": {
            "open_count": open_prs,
            "merged_30d": merged_prs,
            "avg_merge_time_hours": merge_time_hours
        },
        "issues": {
            "open_count": 5,
            "closed_30d": 10,
            "bug_count": 2
        },
        "ci_cd": {
            "has_ci_cd": has_ci,
            "success_rate": ci_success_rate,
            "recent_runs": workflow_runs,
            "workflow_count": 2
        },
        "security": {
            "vulnerability_count": vulnerability_count,
            "branch_protection": branch_protection,
            "dependabot_enabled": dependabot,
            "secret_scanning": secret_scanning,
            "code_scanning": code_scanning,
            "has_security_policy": True,
            "security_score": security_score,
            "license": "MIT"
        }
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
    repos = [create_test_repo(releases_per_month=0.5)]
    result = calc_dora(repos)
    
    assert result["deployment_frequency"]["value"] == 0.5
    assert result["deployment_frequency"]["category"] == "Low"
    print("✅ DORA Deployment Frequency Low: PASSED")


def test_dora_lead_time_elite():
    """Test Elite lead time (<24 hours)."""
    repos = [create_test_repo(lead_time_hours=12)]
    result = calc_dora(repos)
    
    assert result["lead_time"]["value"] == 12.0
    assert result["lead_time"]["category"] == "Elite"
    print("✅ DORA Lead Time Elite: PASSED")


def test_dora_lead_time_high():
    """Test High lead time (<168 hours / 1 week)."""
    repos = [create_test_repo(lead_time_hours=72)]
    result = calc_dora(repos)
    
    assert result["lead_time"]["value"] == 72.0
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


def test_dora_cfr_categories():
    """Test Change Failure Rate category thresholds."""
    # Elite: <5%
    repos = [create_test_repo(cfr=3)]
    assert calc_dora(repos)["cfr"]["category"] == "Elite"
    
    # High: <15%
    repos = [create_test_repo(cfr=10)]
    assert calc_dora(repos)["cfr"]["category"] == "High"
    
    # Medium: <30%
    repos = [create_test_repo(cfr=20)]
    assert calc_dora(repos)["cfr"]["category"] == "Medium"
    
    # Low: ≥30%
    repos = [create_test_repo(cfr=35)]
    assert calc_dora(repos)["cfr"]["category"] == "Low"
    
    print("✅ DORA CFR Categories: PASSED")


def test_dora_overall_score():
    """Test overall DORA score calculation."""
    # All Elite metrics should give Elite overall
    repos = [create_test_repo(
        releases_per_month=10,  # Elite
        lead_time_hours=12,     # Elite
        mttr_hours=0.5,         # Elite
        cfr=3                   # Elite
    )]
    result = calc_dora(repos)
    assert result["overall"] == "Elite"
    
    # Mixed metrics
    repos = [create_test_repo(
        releases_per_month=5,   # High
        lead_time_hours=48,     # High
        mttr_hours=12,          # High
        cfr=10                  # High
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
        create_test_repo(name="repo1", open_prs=3, merged_prs=15, merge_time_hours=20),
        create_test_repo(name="repo2", open_prs=2, merged_prs=10, merge_time_hours=30),
    ]
    result = calc_flow(repos)
    
    # WIP = 3 + 2 = 5
    assert result["total_wip"] == 5
    
    # Throughput = 15 + 10 = 25
    assert result["total_throughput"] == 25
    
    # Cycle time avg = (20 + 30) / 2 = 25
    assert result["cycle_time_avg"] == 25.0
    
    # Review time = cycle time * 0.6 = (12 + 18) / 2 = 15
    assert result["review_time_avg"] == 15.0
    
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
        create_test_repo(name="repo1", has_ci=True, workflow_runs=100),
        create_test_repo(name="repo2", has_ci=True, workflow_runs=50),
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
        create_test_repo(name="repo1", vulnerability_count=10),
    ]
    result = calc_security(repos)
    
    # Distribution: 10% critical, 20% high, 40% medium, 30% low
    assert result["critical_vulns"] == 1   # 10 * 0.1 = 1
    assert result["high_vulns"] == 2       # 10 * 0.2 = 2
    assert result["medium_vulns"] == 4     # 10 * 0.4 = 4
    assert result["low_vulns"] == 3        # 10 * 0.3 = 3
    assert result["total_vulns"] == 10
    
    print("✅ Security Vulnerability Distribution: PASSED")


def test_security_trend():
    """Test vulnerability trend classification."""
    # Improving: <10 vulns
    repos = [create_test_repo(vulnerability_count=5)]
    assert calc_security(repos)["vuln_trend"] == "improving"
    
    # Stable: 10-19 vulns
    repos = [create_test_repo(vulnerability_count=15)]
    assert calc_security(repos)["vuln_trend"] == "stable"
    
    # Worsening: ≥20 vulns
    repos = [create_test_repo(vulnerability_count=25)]
    assert calc_security(repos)["vuln_trend"] == "worsening"
    
    print("✅ Security Vulnerability Trend: PASSED")


def test_security_adoption_rates():
    """Test security feature adoption rates."""
    repos = [
        create_test_repo(name="repo1", branch_protection=True, dependabot=True, secret_scanning=True),
        create_test_repo(name="repo2", branch_protection=True, dependabot=False, secret_scanning=False),
    ]
    result = calc_security(repos)
    
    # Branch protection: 2/2 = 100%
    assert result["branch_protection"] == 100.0
    # Dependabot: 1/2 = 50%
    assert result["dependabot_adoption"] == 50.0
    # Secret scanning: 1/2 = 50%
    assert result["secret_scanning"] == 50.0
    
    print("✅ Security Adoption Rates: PASSED")


def test_security_gate_pass_rate():
    """Test security gate pass rate."""
    repos = [
        create_test_repo(name="repo1", security_score=75),  # Pass (≥50)
        create_test_repo(name="repo2", security_score=60),  # Pass
        create_test_repo(name="repo3", security_score=40),  # Fail (<50)
    ]
    result = calc_security(repos)
    
    # 2 out of 3 pass = 66.7%
    assert result["gate_pass_rate"] == 66.7
    print("✅ Security Gate Pass Rate: PASSED")


def test_security_sla_compliance():
    """Test SLA compliance (repos with 0 vulnerabilities)."""
    repos = [
        create_test_repo(name="repo1", vulnerability_count=0),
        create_test_repo(name="repo2", vulnerability_count=0),
        create_test_repo(name="repo3", vulnerability_count=5),
    ]
    result = calc_security(repos)
    
    # 2 out of 3 have 0 vulns = 66.7%
    assert result["sla_compliance"] == 66.7
    print("✅ Security SLA Compliance: PASSED")


# =============================================================================
# GOVERNANCE METRICS TESTS
# =============================================================================

def test_governance_risk_levels():
    """Test risk level classification."""
    repos = [
        create_test_repo(name="critical", vulnerability_count=10, security_score=25),  # Critical
        create_test_repo(name="high", vulnerability_count=3, security_score=45),       # High
        create_test_repo(name="medium", vulnerability_count=1, security_score=65),     # Medium
        create_test_repo(name="low", vulnerability_count=0, security_score=80),        # Low
    ]
    result = calc_governance(repos)
    
    assert result["risk_critical"] == 1
    assert result["risk_high"] == 1
    assert result["risk_medium"] == 1
    assert result["risk_low"] == 1
    
    print("✅ Governance Risk Levels: PASSED")


def test_governance_repo_counts():
    """Test repository inventory counts."""
    repos = [
        create_test_repo(name="active1"),
        create_test_repo(name="active2"),
        create_test_repo(name="archived", is_archived=True),
    ]
    # Add fork flag manually
    repos[1]["is_fork"] = True
    
    result = calc_governance(repos)
    
    assert result["total_repos"] == 3
    assert result["archived_repos"] == 1
    assert result["forked_repos"] == 1
    assert result["scanned_repos"] == 2  # Non-archived
    
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
    assert result["scan_coverage"] == 66.7
    print("✅ Governance Scan Coverage: PASSED")


# =============================================================================
# REPO TABLE TESTS
# =============================================================================

def test_repo_table_risk_sorting():
    """Test that repos are sorted by risk level."""
    repos = [
        create_test_repo(name="low-risk", vulnerability_count=0, security_score=80),
        create_test_repo(name="critical-risk", vulnerability_count=10, security_score=20),
        create_test_repo(name="medium-risk", vulnerability_count=1, security_score=65),
    ]
    result = build_repo_table(repos)
    
    # Should be sorted: Critical, Medium, Low
    assert result[0]["name"] == "critical-risk"
    assert result[0]["risk_level"] == "Critical"
    assert result[1]["name"] == "medium-risk"
    assert result[1]["risk_level"] == "Medium"
    assert result[2]["name"] == "low-risk"
    assert result[2]["risk_level"] == "Low"
    
    print("✅ Repo Table Risk Sorting: PASSED")


def test_repo_table_gate_pass():
    """Test gate pass calculation in repo table."""
    repos = [
        create_test_repo(name="pass", security_score=60, branch_protection=True),
        create_test_repo(name="fail-score", security_score=40, branch_protection=True),
        create_test_repo(name="fail-bp", security_score=60, branch_protection=False),
    ]
    result = build_repo_table(repos)
    
    # Find each repo by name
    pass_repo = next(r for r in result if r["name"] == "pass")
    fail_score = next(r for r in result if r["name"] == "fail-score")
    fail_bp = next(r for r in result if r["name"] == "fail-bp")
    
    assert pass_repo["gate_pass"] == True
    assert fail_score["gate_pass"] == False  # Score < 50
    assert fail_bp["gate_pass"] == False     # No branch protection
    
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
        ("DORA CFR Categories", test_dora_cfr_categories),
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
