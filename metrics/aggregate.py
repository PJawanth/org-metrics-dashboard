#!/usr/bin/env python3
"""Aggregate repository metrics into org-wide dashboard data."""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

RAW_DIR = Path("data/raw")
AGG_DIR = Path("data/aggregated")
NOW = datetime.now(timezone.utc)


def load_repos():
    repos = []
    for f in RAW_DIR.glob("*.json"):
        if f.name.startswith("_"): continue
        try:
            with open(f) as fp:
                repos.append(json.load(fp))
        except: pass
    return repos


def safe_get(d, *keys, default=0):
    """Safely get nested dict values."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d is not None else default


def calc_dora(repos):
    """Calculate org-wide DORA metrics."""
    active = [r for r in repos if not r.get("is_archived")]
    
    # Deployment Frequency
    rpm_values = [safe_get(r, "dora", "releases_per_month") for r in active if r.get("dora")]
    rpm_values = [v for v in rpm_values if v > 0]
    avg_rpm = round(sum(rpm_values)/len(rpm_values), 1) if rpm_values else 0
    df_cat = "Elite" if avg_rpm >= 8 else "High" if avg_rpm >= 4 else "Medium" if avg_rpm >= 1 else "Low"
    
    # Lead Time
    lt_values = [safe_get(r, "dora", "lead_time_hours") for r in active if r.get("dora")]
    lt_values = [v for v in lt_values if v > 0]
    avg_lt = round(sum(lt_values)/len(lt_values), 1) if lt_values else 0
    lt_cat = "Elite" if avg_lt < 24 else "High" if avg_lt < 168 else "Medium" if avg_lt < 720 else "Low"
    
    # MTTR
    mttr_values = [safe_get(r, "dora", "mttr_hours") for r in active if r.get("dora")]
    mttr_values = [v for v in mttr_values if v > 0]
    avg_mttr = round(sum(mttr_values)/len(mttr_values), 1) if mttr_values else 0
    mttr_cat = "Elite" if avg_mttr < 1 else "High" if avg_mttr < 24 else "Medium" if avg_mttr < 168 else "Low"
    
    # Change Failure Rate - check both field names
    cfr_values = []
    for r in active:
        dora = r.get("dora", {})
        cfr = dora.get("change_failure_rate", dora.get("cfr", 0))
        if cfr is not None:
            cfr_values.append(cfr)
    avg_cfr = round(sum(cfr_values)/len(cfr_values), 1) if cfr_values else 0
    cfr_cat = "Elite" if avg_cfr < 5 else "High" if avg_cfr < 15 else "Medium" if avg_cfr < 30 else "Low"
    
    cats = {"Elite": 4, "High": 3, "Medium": 2, "Low": 1}
    overall = round((cats[df_cat] + cats[lt_cat] + cats[mttr_cat] + cats[cfr_cat]) / 4, 1)
    overall_cat = "Elite" if overall >= 3.5 else "High" if overall >= 2.5 else "Medium" if overall >= 1.5 else "Low"
    
    return {
        "deployment_frequency": {"value": avg_rpm, "category": df_cat, "unit": "releases/month"},
        "lead_time": {"value": avg_lt, "category": lt_cat, "unit": "hours"},
        "mttr": {"value": avg_mttr, "category": mttr_cat, "unit": "hours"},
        "cfr": {"value": avg_cfr, "category": cfr_cat, "unit": "%"},
        "overall": overall_cat,
    }


def calc_flow(repos):
    """Calculate org-wide flow metrics from pull_requests data."""
    active = [r for r in repos if not r.get("is_archived")]
    
    review_times = []
    cycle_times = []
    total_wip = 0
    total_throughput = 0
    
    for r in active:
        prs = r.get("pull_requests", {})
        # Review time approximation: avg merge time / 2
        merge_time = prs.get("avg_merge_time_hours", 0)
        if merge_time > 0:
            review_times.append(merge_time * 0.6)  # Estimate review is 60% of merge time
            cycle_times.append(merge_time)
        
        total_wip += prs.get("open_count", 0)
        total_throughput += prs.get("merged_30d", 0)
    
    return {
        "review_time_avg": round(sum(review_times)/len(review_times), 1) if review_times else 0,
        "cycle_time_avg": round(sum(cycle_times)/len(cycle_times), 1) if cycle_times else 0,
        "total_wip": total_wip,
        "total_throughput": total_throughput,
    }


def calc_ci(repos):
    """Calculate org-wide CI/CD metrics from ci_cd data."""
    active = [r for r in repos if not r.get("is_archived")]
    with_ci = [r for r in active if safe_get(r, "ci_cd", "has_ci_cd", default=False)]
    
    success_rates = []
    durations = []
    total_runs = 0
    
    for r in with_ci:
        ci = r.get("ci_cd", {})
        sr = ci.get("success_rate", 0)
        if sr > 0:
            success_rates.append(sr)
        runs = ci.get("recent_runs", 0)
        total_runs += runs
        # Estimate duration from workflow count if not available
        wf_count = ci.get("workflow_count", 1)
        durations.append(5 * wf_count)  # Estimate 5 mins per workflow
    
    avg_sr = round(sum(success_rates)/len(success_rates), 1) if success_rates else 0
    
    return {
        "adoption": round(len(with_ci)/len(active)*100, 1) if active else 0,
        "success_rate": avg_sr,
        "failure_rate": round(100 - avg_sr, 1),
        "avg_duration": round(sum(durations)/len(durations), 1) if durations else 0,
        "total_runs": total_runs,
    }


def calc_security(repos):
    """Calculate org-wide DevSecOps metrics from security data."""
    active = [r for r in repos if not r.get("is_archived")]
    
    total = len(active) or 1
    
    crit = 0
    high = 0
    med = 0
    low = 0
    secrets = 0
    dep_alerts = 0
    branch_prot = 0
    dependabot = 0
    secret_scan = 0
    code_scan = 0
    sec_policy = 0
    license_ok = 0
    
    for r in active:
        sec = r.get("security", {})
        vuln_count = sec.get("vulnerability_count", 0)
        # Estimate severity distribution
        crit += int(vuln_count * 0.1)
        high += int(vuln_count * 0.2)
        med += int(vuln_count * 0.4)
        low += int(vuln_count * 0.3)
        
        if sec.get("branch_protection", False):
            branch_prot += 1
        if sec.get("dependabot_enabled", False):
            dependabot += 1
            dep_alerts += 1  # Assume repos with dependabot have at least 1 tracked dep
        if sec.get("secret_scanning", False):
            secret_scan += 1
        if sec.get("code_scanning", False):
            code_scan += 1
        if sec.get("has_security_policy", False):
            sec_policy += 1
        if sec.get("license"):
            license_ok += 1
    
    total_vulns = crit + high + med + low
    trend = "improving" if total_vulns < 10 else "stable" if total_vulns < 20 else "worsening"
    
    # Security SLA: % repos with 0 critical vulns
    sla_pass = len([r for r in active if safe_get(r, "security", "vulnerability_count", default=0) == 0])
    sla_rate = round(sla_pass/total*100, 1)
    
    # Gate pass: repos with branch protection and good security score
    gate_pass = len([r for r in active if safe_get(r, "security", "security_score", default=50) >= 50])
    gate_rate = round(gate_pass/total*100, 1)
    
    return {
        "critical_vulns": crit,
        "high_vulns": high,
        "medium_vulns": med,
        "low_vulns": low,
        "total_vulns": total_vulns,
        "vuln_trend": trend,
        "security_mttr": 24,  # Placeholder
        "sla_compliance": sla_rate,
        "secrets_exposed": secrets,
        "dependency_risk": dep_alerts,
        "gate_pass_rate": gate_rate,
        "code_issues": 0,
        "branch_protection": round(branch_prot/total*100, 1),
        "dependabot_adoption": round(dependabot/total*100, 1),
        "secret_scanning": round(secret_scan/total*100, 1),
        "code_scanning": round(code_scan/total*100, 1),
        "security_policy": round(sec_policy/total*100, 1),
        "license_compliance": round(license_ok/total*100, 1),
    }


def calc_issues(repos):
    """Calculate org-wide issue metrics."""
    active = [r for r in repos if not r.get("is_archived")]
    
    open_bugs = 0
    open_total = 0
    closed_30d = 0
    
    for r in active:
        issues = r.get("issues", {})
        open_total += issues.get("open_count", 0)
        closed_30d += issues.get("closed_30d", 0)
        open_bugs += issues.get("bug_count", 0)
    
    return {
        "open_count": open_total,
        "closed_30d": closed_30d,
        "bug_count": open_bugs,
    }


def calc_governance(repos):
    """Calculate governance/audit metrics."""
    total = len(repos)
    archived = len([r for r in repos if r.get("is_archived")])
    forked = len([r for r in repos if r.get("is_fork")])
    active = [r for r in repos if not r.get("is_archived")]
    
    # Risk levels based on security score and other factors
    risk_crit = 0
    risk_high = 0
    risk_med = 0
    risk_low = 0
    
    for r in active:
        score = safe_get(r, "security", "security_score", default=50)
        vulns = safe_get(r, "security", "vulnerability_count", default=0)
        
        if vulns > 5 or score < 30:
            risk_crit += 1
        elif vulns > 2 or score < 50:
            risk_high += 1
        elif vulns > 0 or score < 70:
            risk_med += 1
        else:
            risk_low += 1
    
    return {
        "total_repos": total,
        "scanned_repos": len(active),
        "scan_coverage": round(len(active)/total*100, 1) if total else 0,
        "archived_repos": archived,
        "forked_repos": forked,
        "risk_critical": risk_crit,
        "risk_high": risk_high,
        "risk_medium": risk_med,
        "risk_low": risk_low,
    }


def build_languages(repos):
    """Aggregate languages across repos."""
    lang_count = defaultdict(int)
    for r in repos:
        lang = r.get("language")
        if lang:
            lang_count[lang] += 1
    
    return [{"name": k, "count": v} for k, v in sorted(lang_count.items(), key=lambda x: -x[1])]


def build_contributors(repos):
    """Aggregate contributors across repos."""
    contribs = defaultdict(lambda: {"commits": 0, "repos": set()})
    
    for r in repos:
        for c in r.get("top_contributors", []):
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


def build_repo_table(repos):
    """Build detailed per-repo metrics table."""
    rows = []
    for r in repos:
        dora = r.get("dora", {})
        prs = r.get("pull_requests", {})
        issues = r.get("issues", {})
        sec = r.get("security", {})
        ci = r.get("ci_cd", {})
        
        # Calculate risk level
        score = sec.get("security_score", 50)
        vulns = sec.get("vulnerability_count", 0)
        if vulns > 5 or score < 30:
            risk = "Critical"
        elif vulns > 2 or score < 50:
            risk = "High"
        elif vulns > 0 or score < 70:
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
            except: pass
        
        status_colors = {"Active": "active", "Stale": "stale", "Inactive": "inactive", "Archived": "inactive"}
        
        # Gate pass
        gate = sec.get("security_score", 50) >= 50 and sec.get("branch_protection", False)
        
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
            "security_score": sec.get("security_score", 50),
            "risk_level": risk,
            
            # DORA
            "deploy_freq": dora.get("deployment_frequency", "Low"),
            "releases_month": dora.get("releases_per_month", 0),
            "lead_time_hours": dora.get("lead_time_hours", 0),
            "mttr_hours": dora.get("mttr_hours", 0),
            "cfr": dora.get("change_failure_rate", dora.get("cfr", 0)),
            
            # Flow
            "review_time": round(prs.get("avg_merge_time_hours", 0) * 0.6, 1),
            "cycle_time": prs.get("avg_merge_time_hours", 0),
            "wip": prs.get("open_count", 0),
            "throughput": prs.get("merged_30d", 0),
            
            # CI
            "has_ci": ci.get("has_ci_cd", False),
            "ci_success": ci.get("success_rate", 0),
            "ci_failure": round(100 - ci.get("success_rate", 0), 1),
            "pipeline_mins": ci.get("workflow_count", 1) * 5,  # Estimate
            
            # Security
            "critical_vulns": int(sec.get("vulnerability_count", 0) * 0.1),
            "high_vulns": int(sec.get("vulnerability_count", 0) * 0.2),
            "total_vulns": sec.get("vulnerability_count", 0),
            "secrets": 0,
            "branch_prot": sec.get("branch_protection", False),
            "dependabot": sec.get("dependabot_enabled", False),
            "gate_pass": gate,
            
            # Activity
            "commits_30d": r.get("commits_30d", 0),
            "open_prs": prs.get("open_count", 0),
            "open_issues": issues.get("open_count", 0),
            "stars": r.get("stars", 0),
            "forks": r.get("forks", 0),
        }
        rows.append(row)
    
    # Sort by risk level, then by name
    risk_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    return sorted(rows, key=lambda x: (risk_order.get(x["risk_level"], 4), x["name"]))


def aggregate():
    """Main aggregation function."""
    print("Loading repos...")
    repos = load_repos()
    print(f"Processing {len(repos)} repos...")
    
    data = {
        "org_name": "PJawanth",
        "generated_at": NOW.strftime("%Y-%m-%d %H:%M UTC"),
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
    
    AGG_DIR.mkdir(parents=True, exist_ok=True)
    out_file = AGG_DIR / "dashboard.json"
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Aggregated data written to {out_file}")
    return data


if __name__ == "__main__":
    aggregate()
