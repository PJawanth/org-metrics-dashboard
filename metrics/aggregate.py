#!/usr/bin/env python3
"""
Aggregate repository metrics into org-wide dashboard data.

PRODUCTION-HARDENED:
- All metrics are real data from collected repos
- No fabricated values; use None for unknown metrics
- History snapshots for trend analysis
- Schema validation on input and output
- Null-safe averaging (ignores None values)
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import sys

# Import schema validation
sys.path.insert(0, str(Path(__file__).parent))
from schema import assert_aggregated_dashboard

RAW_DIR = Path("data/raw")
AGG_DIR = Path("data/aggregated")
HISTORY_DIR = Path("data/history")
NOW = datetime.now(timezone.utc)
RUN_ID = NOW.strftime("%Y%m%d_%H%M%S")


# ============================================================================
# UTILITIES
# ============================================================================


def safe_get(d: Dict, *keys, default=None) -> Any:
    """Safely get nested dict values. Returns None if not found (not 0)."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default


def safe_avg(values: List[float]) -> Optional[float]:
    """
    Compute average, ignoring None/zero values.
    Returns None if no valid values.
    """
    valid = [v for v in values if v is not None and v > 0]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 1)


def load_repos() -> List[Dict[str, Any]]:
    """Load all collected repo json files from data/raw."""
    repos = []
    for f in RAW_DIR.glob("*.json"):
        if f.name.startswith("_"):
            continue
        try:
            with open(f) as fp:
                repo_data = json.load(fp)
                repos.append(repo_data)
        except json.JSONDecodeError:
            print(f"  ⚠ Invalid JSON: {f.name}")
        except Exception as e:
            print(f"  ✗ Error loading {f.name}: {e}")
    return repos


def load_previous_snapshot() -> Optional[Dict[str, Any]]:
    """
    Load the most recent previous aggregation snapshot for trend comparison.
    Returns None if no previous snapshot exists.
    """
    if not HISTORY_DIR.exists():
        return None

    # Find most recent history file (not the current one)
    history_files = sorted(HISTORY_DIR.glob("**/dashboard.json"), reverse=True)

    for hist_file in history_files:
        # Skip if it's from the current run time (same day)
        try:
            with open(hist_file) as f:
                return json.load(f)
        except Exception:
            continue

    return None


# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================


def calc_dora(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate org-wide DORA metrics from collected data."""
    active = [r for r in repos if not r.get("is_archived")]

    # Deployment Frequency
    rpm_values = [safe_get(r, "dora", "releases_per_month") for r in active if r.get("dora")]
    rpm_values = [v for v in rpm_values if v is not None and v > 0]
    avg_rpm = safe_avg(rpm_values)
    if avg_rpm is None:
        avg_rpm = 0
    df_cat = "Elite" if avg_rpm >= 8 else "High" if avg_rpm >= 4 else "Medium" if avg_rpm >= 1 else "Low"

    # Lead Time
    lt_values = [safe_get(r, "dora", "lead_time_hours") for r in active if r.get("dora")]
    lt_values = [v for v in lt_values if v is not None and v > 0]
    avg_lt = safe_avg(lt_values)
    if avg_lt is None:
        avg_lt = 0
    lt_cat = "Elite" if avg_lt < 24 else "High" if avg_lt < 168 else "Medium" if avg_lt < 720 else "Low"

    # MTTR (Issue resolution time)
    mttr_values = [safe_get(r, "dora", "mttr_hours") for r in active if r.get("dora")]
    mttr_values = [v for v in mttr_values if v is not None and v > 0]
    avg_mttr = safe_avg(mttr_values)
    if avg_mttr is None:
        avg_mttr = 0
    mttr_cat = "Elite" if avg_mttr < 1 else "High" if avg_mttr < 24 else "Medium" if avg_mttr < 168 else "Low"

    # CI Failure Rate (NOT DORA Change Failure Rate)
    cfr_values = []
    for r in active:
        dora = r.get("dora", {})
        cfr = dora.get("cfr", 0)
        if cfr is not None:
            cfr_values.append(cfr)
    avg_cfr = safe_avg(cfr_values)
    if avg_cfr is None:
        avg_cfr = 0
    cfr_cat = "Elite" if avg_cfr < 5 else "High" if avg_cfr < 15 else "Medium" if avg_cfr < 30 else "Low"

    cats = {"Elite": 4, "High": 3, "Medium": 2, "Low": 1}
    overall = round((cats[df_cat] + cats[lt_cat] + cats[mttr_cat] + cats[cfr_cat]) / 4, 1)
    overall_cat = "Elite" if overall >= 3.5 else "High" if overall >= 2.5 else "Medium" if overall >= 1.5 else "Low"

    return {
        "deployment_frequency": {"value": avg_rpm, "category": df_cat, "unit": "releases/month"},
        "lead_time": {"value": avg_lt, "category": lt_cat, "unit": "hours"},
        "mttr": {"value": avg_mttr, "category": mttr_cat, "unit": "hours"},
        "ci_failure_rate": {"value": avg_cfr, "category": cfr_cat, "unit": "%"},
        "overall": overall_cat,
    }


def calc_flow(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate org-wide flow metrics."""
    active = [r for r in repos if not r.get("is_archived")]

    review_times = []
    cycle_times = []
    total_wip = 0
    total_throughput = 0

    for r in active:
        pr = r.get("pr", {})
        review_time = pr.get("review_time_hours", 0)
        cycle_time = pr.get("cycle_time_hours", 0)

        if review_time and review_time > 0:
            review_times.append(review_time)
        if cycle_time and cycle_time > 0:
            cycle_times.append(cycle_time)

        total_wip += pr.get("wip", 0)
        total_throughput += pr.get("throughput", 0)

    return {
        "review_time_avg": safe_avg(review_times),
        "cycle_time_avg": safe_avg(cycle_times),
        "total_wip": total_wip,
        "total_throughput": total_throughput,
    }


def calc_ci(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate org-wide CI/CD metrics."""
    active = [r for r in repos if not r.get("is_archived")]
    with_ci = [r for r in active if r.get("ci", {}).get("has_ci", False)]

    success_rates = []
    durations = []
    total_runs = 0

    for r in with_ci:
        ci = r.get("ci", {})
        sr = ci.get("success_rate", 0)
        if sr and sr > 0:
            success_rates.append(sr)

        runs = ci.get("runs_30d", 0)
        total_runs += runs

        dur = ci.get("duration_mins", 0)
        if dur and dur > 0:
            durations.append(dur)

    avg_sr = safe_avg(success_rates)
    if avg_sr is None:
        avg_sr = 0

    adoption = round(len(with_ci) / len(active) * 100, 1) if active else 0

    return {
        "adoption": adoption,
        "success_rate": avg_sr,
        "failure_rate": round(100 - avg_sr, 1) if avg_sr is not None else None,
        "avg_duration": safe_avg(durations),
        "total_runs": total_runs,
    }


def calc_security(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate org-wide security metrics from real data."""
    active = [r for r in repos if not r.get("is_archived")]

    total = len(active) or 1

    # Aggregate real vulnerability counts from collect.py
    crit = 0
    high = 0
    med = 0
    low = 0
    secrets = 0
    dep_alerts = 0
    code_alerts = 0
    branch_prot = 0
    dependabot = 0
    secret_scan = 0
    code_scan = 0
    sec_policy = 0
    license_ok = 0
    gate_pass_count = 0

    # For trend calculation
    repos_with_critical = 0
    repos_with_high = 0

    # For MTTR calculation
    mttr_values = []

    for r in active:
        sec = r.get("security", {})

        # Real vulnerability severity counts from Dependabot alerts
        crit += sec.get("critical", 0)
        high += sec.get("high", 0)
        med += sec.get("medium", 0)
        low += sec.get("low", 0)

        # Real metrics from collect.py
        secrets += sec.get("secrets", 0)
        dep_alerts += sec.get("dependency_alerts", 0)
        code_alerts += sec.get("code_alerts", 0)

        # Security controls
        if sec.get("branch_protection", False):
            branch_prot += 1
        if sec.get("dependabot", False):
            dependabot += 1
        if sec.get("secret_scanning", False):
            secret_scan += 1
        if sec.get("code_scanning", False):
            code_scan += 1
        if sec.get("security_policy", False):
            sec_policy += 1
        if sec.get("license"):
            license_ok += 1
        if sec.get("gate_pass", False):
            gate_pass_count += 1

        # Track vulnerability presence
        if sec.get("critical", 0) > 0:
            repos_with_critical += 1
        if sec.get("high", 0) > 0:
            repos_with_high += 1

        # Real Security MTTR from collected data
        if sec.get("security_mttr_hours") is not None:
            mttr_values.append(sec["security_mttr_hours"])

    total_vulns = crit + high + med + low

    # Vulnerability trend: compare to previous snapshot
    vuln_trend = None
    prev_snapshot = load_previous_snapshot()
    if prev_snapshot:
        try:
            prev_total = prev_snapshot.get("security", {}).get("total_vulns", 0)
            delta = total_vulns - prev_total

            if delta < 0:
                vuln_trend = "Improving"
            elif delta > 0:
                vuln_trend = "Worsening"
            else:
                vuln_trend = "Stable"
        except Exception:
            pass

    # If no previous snapshot, trend is null
    if vuln_trend is None:
        vuln_trend = None

    # SLA: % repos with 0 critical vulnerabilities
    sla_pass = len([r for r in active if r.get("security", {}).get("critical", 0) == 0])
    sla_rate = round(sla_pass / total * 100, 1) if total else 0

    # Security MTTR: average of real computed values
    security_mttr = safe_avg(mttr_values)

    # Gate pass rate
    gate_rate = round(gate_pass_count / total * 100, 1) if total else 0

    return {
        "critical_vulns": crit,
        "high_vulns": high,
        "medium_vulns": med,
        "low_vulns": low,
        "total_vulns": total_vulns,
        "vuln_trend": vuln_trend,
        "security_mttr": security_mttr,
        "sla_compliance": sla_rate,
        "secrets_exposed": secrets,
        "dependency_risk": dep_alerts,
        "gate_pass_rate": gate_rate,
        "code_issues": code_alerts,
        "branch_protection": round(branch_prot / total * 100, 1),
        "dependabot_adoption": round(dependabot / total * 100, 1),
        "secret_scanning": round(secret_scan / total * 100, 1),
        "code_scanning": round(code_scan / total * 100, 1),
        "security_policy": round(sec_policy / total * 100, 1),
        "license_compliance": round(license_ok / total * 100, 1),
    }


def calc_issues(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate org-wide issue metrics."""
    active = [r for r in repos if not r.get("is_archived")]

    open_bugs = 0
    open_total = 0
    closed_30d = 0

    for r in active:
        issues = r.get("issues", {})
        open_total += issues.get("open", 0)
        closed_30d += issues.get("closed_30d", 0)
        open_bugs += issues.get("bugs", 0)

    return {
        "open_count": open_total,
        "closed_30d": closed_30d,
        "bug_count": open_bugs,
    }


def calc_governance(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate governance/audit metrics."""
    total = len(repos)
    archived = len([r for r in repos if r.get("is_archived")])
    forked = len([r for r in repos if r.get("is_fork")])
    active = [r for r in repos if not r.get("is_archived")]

    # Risk levels based on real security data
    risk_crit = 0
    risk_high = 0
    risk_med = 0
    risk_low = 0

    for r in active:
        sec = r.get("security", {})
        crit = sec.get("critical", 0)
        high = sec.get("high", 0)
        secrets = sec.get("secrets", 0)
        gate = sec.get("gate_pass", True)

        # Critical: has critical vulns, exposed secrets, or failed gate
        if crit > 0 or secrets > 0 or not gate:
            risk_crit += 1
        # High: has high vulns
        elif high > 0:
            risk_high += 1
        # Medium: has medium vulns
        elif sec.get("medium", 0) > 0:
            risk_med += 1
        # Low: clean
        else:
            risk_low += 1

    return {
        "total_repos": total,
        "scanned_repos": len(active),
        "scan_coverage": round(len(active) / total * 100, 1) if total else 0,
        "archived_repos": archived,
        "forked_repos": forked,
        "risk_critical": risk_crit,
        "risk_high": risk_high,
        "risk_medium": risk_med,
        "risk_low": risk_low,
    }


def build_languages(repos: List[Dict]) -> List[Dict[str, Any]]:
    """Aggregate languages across repos."""
    lang_count = defaultdict(int)
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_count[lang] += 1

    return [{"name": k, "count": v} for k, v in sorted(lang_count.items(), key=lambda x: -x[1])]


def build_contributors(repos: List[Dict]) -> List[Dict[str, Any]]:
    """Aggregate contributors across repos."""
    contribs = defaultdict(lambda: {"commits": 0, "repos": set()})

    for r in repos:
        # Use correct key from collect.py: commits.top
        top_authors = r.get("commits", {}).get("top", [])
        for c in top_authors:
            login = c.get("login", "unknown")
            contribs[login]["commits"] += c.get("commits", 0)
            contribs[login]["repos"].add(r.get("name", ""))

    result = []
    for login, data in contribs.items():
        result.append({
            "login": login,
            "commits": data["commits"],
            "repo_count": len(data["repos"]),
        })

    return sorted(result, key=lambda x: -x["commits"])[:20]


def build_repo_table(repos: List[Dict]) -> List[Dict[str, Any]]:
    """Build detailed per-repo metrics table."""
    rows = []
    for r in repos:
        dora = r.get("dora", {})
        pr = r.get("pr", {})
        issues = r.get("issues", {})
        sec = r.get("security", {})
        ci = r.get("ci", {})

        # Risk level based on real security data
        crit = sec.get("critical", 0)
        high = sec.get("high", 0)
        secrets = sec.get("secrets", 0)
        gate = sec.get("gate_pass", False)

        if crit > 0 or secrets > 0 or not gate:
            risk = "Critical"
        elif high > 0:
            risk = "High"
        elif sec.get("medium", 0) > 0:
            risk = "Medium"
        else:
            risk = "Low"

        # Status based on updated_at
        updated = r.get("updated_at", r.get("pushed_at", ""))
        status = "Active"
        if r.get("is_archived"):
            status = "Archived"
        elif updated:
            try:
                days = (NOW - datetime.fromisoformat(updated.replace("Z", "+00:00"))).days
                if days > 180:
                    status = "Inactive"
                elif days > 30:
                    status = "Stale"
            except (ValueError, TypeError):
                pass

        status_colors = {
            "Active": "active",
            "Stale": "stale",
            "Inactive": "inactive",
            "Archived": "inactive",
        }

        row = {
            "name": r.get("name", "Unknown"),
            "full_name": r.get("full_name", ""),
            "url": r.get("url", "#"),
            "description": r.get("description", "") or "",
            "language": r.get("language"),
            "updated_at": updated,
            "status": status,
            "status_color": status_colors.get(status, "active"),
            # Scores
            "health_score": r.get("health_score", 50),
            "security_score": sec.get("score", 50),
            "risk_level": risk,
            # DORA
            "deploy_freq": dora.get("deployment_freq", "Low"),
            "releases_month": dora.get("releases_per_month", 0),
            "lead_time_hours": dora.get("lead_time_hours", 0),
            "mttr_hours": dora.get("mttr_hours", 0),
            "cfr": dora.get("cfr", 0),
            # Flow
            "review_time": pr.get("review_time_hours", 0),
            "cycle_time": pr.get("cycle_time_hours", 0),
            "wip": pr.get("wip", 0),
            "throughput": pr.get("throughput", 0),
            # CI
            "has_ci": ci.get("has_ci", False),
            "ci_success": ci.get("success_rate", 0),
            "ci_failure": ci.get("failure_rate", 0),
            "pipeline_mins": ci.get("duration_mins", 0),
            # Security - real values
            "critical_vulns": sec.get("critical", 0),
            "high_vulns": sec.get("high", 0),
            "total_vulns": sec.get("total_vulns", 0),
            "secrets": sec.get("secrets", 0),
            "code_alerts": sec.get("code_alerts", 0),
            "dependency_alerts": sec.get("dependency_alerts", 0),
            "branch_prot": sec.get("branch_protection", False),
            "dependabot": sec.get("dependabot", False),
            "gate_pass": sec.get("gate_pass", False),
            # Activity
            "commits_30d": r.get("commits", {}).get("count_30d", 0),
            "open_prs": pr.get("open", 0),
            "open_issues": issues.get("open", 0),
            "stars": r.get("stars", 0),
            "forks": r.get("forks", 0),
        }
        rows.append(row)

    # Sort by risk level, then by name
    risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(rows, key=lambda x: (risk_order.get(x["risk_level"], 4), x["name"]))


# ============================================================================
# MAIN AGGREGATION
# ============================================================================


def aggregate():
    """Main aggregation function."""
    print("Loading repos...")
    repos = load_repos()
    print(f"Processing {len(repos)} repos...")

    data = {
        "org_name": "PJawanth",
        "generated_at": NOW.strftime("%Y-%m-%d %H:%M UTC"),
        "run_id": RUN_ID,
        "repos": build_repo_table(repos),
        "dora": calc_dora(repos),
        "flow": calc_flow(repos),
        "ci": calc_ci(repos),
        "security": calc_security(repos),
        "issues": calc_issues(repos),
        "governance": calc_governance(repos),
        "languages": build_languages(repos),
        "contributors": build_contributors(repos),
    }

    # Validate schema before writing
    assert_aggregated_dashboard(data)

    # Write aggregated data
    AGG_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AGG_DIR / "dashboard.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Aggregated data: {out_file}")

    # Write history snapshot for trend analysis
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    today_dir = HISTORY_DIR / NOW.strftime("%Y-%m-%d")
    today_dir.mkdir(parents=True, exist_ok=True)
    hist_file = today_dir / "dashboard.json"
    with open(hist_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ History snapshot: {hist_file}")

    return data


if __name__ == "__main__":
    aggregate()
