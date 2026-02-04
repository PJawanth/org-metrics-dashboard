#!/usr/bin/env python3
"""
Comprehensive DevOps/DevSecOps/Governance metrics collector.
Collects DORA, Flow, Security, and Audit metrics from GitHub.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ORG_READ_TOKEN")
ORG_NAME = os.environ.get("GITHUB_ORG", "")
API_BASE = "https://api.github.com"
RAW_DATA_DIR = Path("data/raw")

NOW = datetime.now(timezone.utc)
DAYS_30 = NOW - timedelta(days=30)
DAYS_90 = NOW - timedelta(days=90)


def get_headers():
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "metrics-dashboard"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def make_request(url, params=None):
    response = requests.get(url, headers=get_headers(), params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_paginated(url, params=None, max_pages=5):
    results, params = [], params or {}
    params["per_page"] = 100
    for page in range(1, max_pages + 1):
        params["page"] = page
        try:
            resp = requests.get(url, headers=get_headers(), params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if not data: break
            results.extend(data)
        except: break
    return results


def get_org_repos(org):
    try:
        url = f"{API_BASE}/orgs/{org}/repos"
        resp = requests.get(url, headers=get_headers(), params={"type": "all", "per_page": 100}, timeout=30)
        if resp.status_code == 200:
            return resp.json()
    except: pass
    print(f"  Using user endpoint for '{org}'")
    return get_paginated(f"{API_BASE}/users/{org}/repos", {"type": "owner"})


def parse_date(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def get_pr_metrics(owner, repo):
    prs = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/pulls", {"state": "all", "sort": "updated"})
    merged = [p for p in prs if p.get("merged_at")]
    open_prs = [p for p in prs if p["state"] == "open"]
    merged_30d = [p for p in merged if parse_date(p["merged_at"]) > DAYS_30]
    
    lead_times = [(parse_date(p["merged_at"]) - parse_date(p["created_at"])).total_seconds()/3600 for p in merged_30d]
    pr_ages = [(NOW - parse_date(p["created_at"])).days for p in open_prs]
    
    review_times = []
    for pr in merged_30d[:10]:
        try:
            reviews = make_request(f"{API_BASE}/repos/{owner}/{repo}/pulls/{pr['number']}/reviews")
            if reviews:
                created = parse_date(pr["created_at"])
                first = min(parse_date(r["submitted_at"]) for r in reviews if r.get("submitted_at"))
                review_times.append((first - created).total_seconds()/3600)
        except: pass
    
    return {
        "total": len(prs), "open": len(open_prs), "merged_30d": len(merged_30d),
        "throughput": len(merged_30d), "wip": len(open_prs),
        "stale": len([a for a in pr_ages if a > 14]),
        "lead_time_hours": round(sum(lead_times)/len(lead_times), 1) if lead_times else 0,
        "lead_time_days": round(sum(lead_times)/len(lead_times)/24, 2) if lead_times else 0,
        "review_time_hours": round(sum(review_times)/len(review_times), 1) if review_times else 0,
        "cycle_time_hours": round(sum(lead_times)/len(lead_times), 1) if lead_times else 0,
        "merge_rate": round(len(merged)/len(prs)*100, 1) if prs else 0,
    }


def get_issue_metrics(owner, repo):
    issues = [i for i in get_paginated(f"{API_BASE}/repos/{owner}/{repo}/issues", {"state": "all"}) if "pull_request" not in i]
    open_issues = [i for i in issues if i["state"] == "open"]
    closed = [i for i in issues if i["state"] == "closed"]
    closed_30d = [i for i in closed if i.get("closed_at") and parse_date(i["closed_at"]) > DAYS_30]
    
    mttr = [(parse_date(i["closed_at"]) - parse_date(i["created_at"])).total_seconds()/3600 for i in closed_30d if i.get("closed_at")]
    
    labels = defaultdict(int)
    for i in open_issues:
        for l in i.get("labels", []):
            labels[l.get("name", "").lower()] += 1
    
    return {
        "total": len(issues), "open": len(open_issues), "closed_30d": len(closed_30d),
        "mttr_hours": round(sum(mttr)/len(mttr), 1) if mttr else 0,
        "bugs": labels.get("bug", 0), "critical": labels.get("critical", 0) + labels.get("urgent", 0),
        "security": labels.get("security", 0), "stale": len([i for i in open_issues if (NOW - parse_date(i["created_at"])).days > 30]),
    }


def get_deployment_metrics(owner, repo):
    releases = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/releases", max_pages=2)
    releases_90d = [r for r in releases if r.get("published_at") and parse_date(r["published_at"]) > DAYS_90]
    rpm = round(len(releases_90d)/3, 1)
    cat = "Elite" if rpm >= 8 else "High" if rpm >= 4 else "Medium" if rpm >= 1 else "Low"
    return {"total": len(releases), "releases_90d": len(releases_90d), "per_month": rpm, "category": cat, "latest": releases[0]["tag_name"] if releases else None}


def get_ci_metrics(owner, repo):
    try:
        wf = make_request(f"{API_BASE}/repos/{owner}/{repo}/actions/workflows")
        workflows = wf.get("workflows", [])
        if not workflows:
            return {"has_ci": False, "workflows": 0, "success_rate": 0, "failure_rate": 0, "runs_30d": 0, "duration_mins": 0}
        
        runs = make_request(f"{API_BASE}/repos/{owner}/{repo}/actions/runs", {"per_page": 100}).get("workflow_runs", [])
        runs_30d = [r for r in runs if parse_date(r["created_at"]) > DAYS_30]
        success = len([r for r in runs_30d if r["conclusion"] == "success"])
        failure = len([r for r in runs_30d if r["conclusion"] == "failure"])
        total = success + failure
        
        durations = []
        for r in runs_30d[:15]:
            if r.get("updated_at"):
                durations.append((parse_date(r["updated_at"]) - parse_date(r["created_at"])).total_seconds()/60)
        
        return {
            "has_ci": True, "workflows": len(workflows), "runs_30d": len(runs_30d),
            "success_rate": round(success/total*100, 1) if total else 0,
            "failure_rate": round(failure/total*100, 1) if total else 0,
            "duration_mins": round(sum(durations)/len(durations), 1) if durations else 0,
        }
    except:
        return {"has_ci": False, "workflows": 0, "success_rate": 0, "failure_rate": 0, "runs_30d": 0, "duration_mins": 0}


def get_security_metrics(owner, repo):
    m = {"score": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "total_vulns": 0,
         "secrets": 0, "dependency_alerts": 0, "code_alerts": 0, "security_policy": False,
         "branch_protection": False, "dependabot": False, "secret_scanning": False,
         "code_scanning": False, "gate_pass": True, "license": None, "security_mttr_hours": 0}
    score = 0
    
    try:
        make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/SECURITY.md")
        m["security_policy"] = True; score += 15
    except: pass
    
    try:
        info = make_request(f"{API_BASE}/repos/{owner}/{repo}")
        make_request(f"{API_BASE}/repos/{owner}/{repo}/branches/{info.get('default_branch','main')}/protection")
        m["branch_protection"] = True; score += 20
    except: pass
    
    try:
        make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/.github/dependabot.yml")
        m["dependabot"] = True; score += 15
    except:
        try:
            make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/.github/dependabot.yaml")
            m["dependabot"] = True; score += 15
        except: pass
    
    try:
        alerts = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/dependabot/alerts", {"state": "open"})
        for a in alerts:
            sev = a.get("security_advisory", {}).get("severity", "").lower()
            if sev == "critical": m["critical"] += 1
            elif sev == "high": m["high"] += 1
            elif sev == "medium": m["medium"] += 1
            else: m["low"] += 1
        m["dependency_alerts"] = m["total_vulns"] = len(alerts)
        if not alerts: score += 20
        elif m["critical"] == 0: score += 10
    except: pass
    
    try:
        alerts = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/code-scanning/alerts", {"state": "open"})
        m["code_alerts"] = len(alerts); m["code_scanning"] = True; score += 15
    except: pass
    
    try:
        alerts = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/secret-scanning/alerts", {"state": "open"})
        m["secrets"] = len(alerts); m["secret_scanning"] = True; score += 10
    except: pass
    
    try:
        lic = make_request(f"{API_BASE}/repos/{owner}/{repo}/license")
        m["license"] = lic.get("license", {}).get("spdx_id"); score += 5
    except: pass
    
    if m["critical"] > 0 or m["secrets"] > 0:
        m["gate_pass"] = False
    
    m["score"] = min(100, score)
    return m


def get_commits(owner, repo):
    commits = get_paginated(f"{API_BASE}/repos/{owner}/{repo}/commits", {"since": DAYS_30.isoformat()}, max_pages=3)
    authors = defaultdict(int)
    for c in commits:
        a = c.get("author")
        if a: authors[a.get("login", "unknown")] += 1
    return {"count_30d": len(commits), "authors": len(authors), "top": [{"login": k, "commits": v} for k, v in sorted(authors.items(), key=lambda x: -x[1])[:5]]}


def calculate_risk(data):
    score, factors = 0, []
    if data["security"]["critical"] > 0:
        score += 40; factors.append(f"{data['security']['critical']} critical vulns")
    if data["security"]["high"] > 0:
        score += 20; factors.append(f"{data['security']['high']} high vulns")
    if data["security"]["secrets"] > 0:
        score += 50; factors.append(f"{data['security']['secrets']} exposed secrets")
    if not data["security"]["branch_protection"]:
        score += 15; factors.append("No branch protection")
    if data["ci"]["failure_rate"] > 30:
        score += 10; factors.append(f"High CI failure ({data['ci']['failure_rate']}%)")
    
    days = (NOW - parse_date(data["pushed_at"])).days if data.get("pushed_at") else 999
    if days > 90:
        score += 15; factors.append(f"Inactive {days} days")
    
    level = "Critical" if score >= 50 else "High" if score >= 30 else "Medium" if score >= 15 else "Low"
    return {"score": min(100, score), "level": level, "factors": factors[:5]}


def collect_repo(owner, repo_name):
    info = make_request(f"{API_BASE}/repos/{owner}/{repo_name}")
    pr = get_pr_metrics(owner, repo_name)
    issues = get_issue_metrics(owner, repo_name)
    deploy = get_deployment_metrics(owner, repo_name)
    ci = get_ci_metrics(owner, repo_name)
    sec = get_security_metrics(owner, repo_name)
    commits = get_commits(owner, repo_name)
    
    cfr = ci["failure_rate"]
    cfr_cat = "Elite" if cfr < 5 else "High" if cfr < 15 else "Medium" if cfr < 30 else "Low"
    
    health = sum([10 if info.get("description") else 0, 10 if not info.get("archived") else 0,
                  20 if ci["has_ci"] else 0, 10 if ci["success_rate"] >= 80 else 0,
                  15 if sec["branch_protection"] else 0, 15 if pr["lead_time_hours"] < 48 else 0,
                  10 if issues["stale"] < 5 else 0, 10 if commits["count_30d"] > 0 else 0])
    
    data = {
        "name": repo_name, "full_name": info["full_name"], "description": (info.get("description") or "")[:150],
        "url": info["html_url"], "language": info.get("language"), "default_branch": info.get("default_branch", "main"),
        "is_archived": info.get("archived", False), "is_fork": info.get("fork", False), "is_private": info.get("private", False),
        "created_at": info["created_at"], "updated_at": info["updated_at"], "pushed_at": info["pushed_at"],
        "stars": info["stargazers_count"], "forks": info["forks_count"], "health_score": min(100, health),
        
        "dora": {"deployment_freq": deploy["category"], "releases_per_month": deploy["per_month"],
                 "lead_time_hours": pr["lead_time_hours"], "lead_time_days": pr["lead_time_days"],
                 "mttr_hours": issues["mttr_hours"], "cfr": cfr, "cfr_category": cfr_cat},
        
        "flow": {"review_time": pr["review_time_hours"], "cycle_time": pr["cycle_time_hours"],
                 "wip": pr["wip"], "throughput": pr["throughput"]},
        
        "pr": pr, "issues": issues, "deploy": deploy, "ci": ci, "security": sec, "commits": commits,
        "collected_at": NOW.isoformat().replace("+00:00", "Z"),
    }
    data["risk"] = calculate_risk(data)
    return data


def main():
    if not GITHUB_TOKEN:
        print("Warning: No GITHUB_TOKEN. Rate limits will be low.")
    
    org = sys.argv[1] if len(sys.argv) > 1 else ORG_NAME
    if not org:
        print("Usage: python collect.py <org>"); return
    
    print(f"Collecting for: {org}")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    repos = get_org_repos(org)
    print(f"Found {len(repos)} repos")
    
    gov = {"total": len(repos), "scanned": 0, "archived": 0, "forked": 0, "date": NOW.isoformat()}
    
    for i, r in enumerate(repos):
        name = r["name"]
        print(f"  [{i+1}/{len(repos)}] {name}")
        if r.get("archived"):
            gov["archived"] += 1; print("    ⊘ Archived"); continue
        if r.get("fork"): gov["forked"] += 1
        try:
            data = collect_repo(org, name)
            with open(RAW_DATA_DIR / f"{name}.json", "w") as f:
                json.dump(data, f, indent=2)
            gov["scanned"] += 1; print("    ✓")
        except Exception as e:
            print(f"    ✗ {e}")
    
    with open(RAW_DATA_DIR / "_governance.json", "w") as f:
        json.dump(gov, f, indent=2)
    
    print(f"\n✓ Done: {gov['scanned']}/{len(repos)}")


if __name__ == "__main__":
    main()
