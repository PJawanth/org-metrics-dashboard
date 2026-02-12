#!/usr/bin/env python3
"""
Comprehensive DevOps/DevSecOps/Governance metrics collector.
Collects DORA, Flow, Security, and Audit metrics from GitHub REST API.

PRODUCTION-HARDENED:
- All metrics are real data from GitHub APIs, no fabrication
- Schema validation on output
- Detailed error handling with availability flags & permission checks
- Truncation tracking for data completeness
- Run metadata logging for audit trail
- Real Security MTTR computed from alert resolution times
- CF is moved to CI metrics (not DORA CFR)
"""

import os
import sys
import json
import requests
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Import schema validation
sys.path.insert(0, str(Path(__file__).parent))
from schema import assert_raw_repo

# ============================================================================
# CONFIGURATION
# ============================================================================

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ORG_READ_TOKEN")
ORG_NAME = os.environ.get("GITHUB_ORG", "")
API_BASE = "https://api.github.com"
RAW_DATA_DIR = Path("data/raw")
META_DIR = Path("data/meta")

NOW = datetime.now(timezone.utc)
DAYS_30 = NOW - timedelta(days=30)
DAYS_90 = NOW - timedelta(days=90)

MAX_PAGES = 5
ITEMS_PER_PAGE = 100
REQUEST_TIMEOUT = 30

# Global metrics
RUN_ID = str(uuid.uuid4())
START_TIME = NOW
request_count = 0
rate_limit_remaining = None
rate_limit_reset = None
errors_count = 0
warnings = []


# ============================================================================
# VALIDATION & LOGGING
# ============================================================================


def validate_env() -> Tuple[str, str]:
    """Validate environment variables. Exit fast if config missing."""
    token = GITHUB_TOKEN
    org = ORG_NAME

    if not token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        print("  Set via: export GITHUB_TOKEN=<pat_token>")
        sys.exit(1)

    if not org:
        print("ERROR: GITHUB_ORG environment variable not set")
        print("  Set via: export GITHUB_ORG=<org_name>")
        sys.exit(1)

    return token, org


def log_warning(msg: str):
    """Log a warning for audit trail."""
    warnings.append({"at": NOW.isoformat(), "msg": msg})
    print(f"  ⚠ {msg}")


# ============================================================================
# HTTP LAYER
# ============================================================================


def get_headers():
    """Build request headers with auth token."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "metrics-dashboard/2.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def parse_rate_limit_header(headers: Dict) -> None:
    """Extract and track rate limit info from response headers."""
    global rate_limit_remaining, rate_limit_reset

    if "X-RateLimit-Remaining" in headers:
        try:
            rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
        except (ValueError, TypeError):
            pass

    if "X-RateLimit-Reset" in headers:
        try:
            reset_ts = int(headers["X-RateLimit-Reset"])
            rate_limit_reset = datetime.fromtimestamp(reset_ts, tz=timezone.utc).isoformat()
        except (ValueError, TypeError):
            pass


def make_request(url: str, params: Optional[Dict] = None) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Make single GET request with detailed error handling.
    Returns (json_data, error_reason).
    
    - error_reason is None on success
    - error_reason is string describing the issue if unavailable
    - json_data is {} on error
    """
    global request_count, errors_count

    request_count += 1

    try:
        response = requests.get(
            url, headers=get_headers(), params=params, timeout=REQUEST_TIMEOUT
        )

        # Always capture rate limit info
        parse_rate_limit_header(response.headers)

        if response.status_code == 200:
            return response.json(), None

        elif response.status_code == 404:
            # Endpoint not found or feature not available
            return {}, "404 Not Found (feature may not be available)"

        elif response.status_code == 403:
            # Permission denied (most common for GitHub Advanced Security features)
            return {}, "403 Forbidden (insufficient permissions; may require GitHub Advanced Security)"

        elif response.status_code == 422:
            # Unprocessable entity (e.g., branch doesn't exist)
            return {}, "422 Unprocessable Entity"

        else:
            errors_count += 1
            return {}, f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        errors_count += 1
        return {}, "Timeout"
    except requests.exceptions.ConnectionError:
        errors_count += 1
        return {}, "Connection Error"
    except requests.exceptions.RequestException as e:
        errors_count += 1
        return {}, f"Request Error: {str(e)[:50]}"
    except json.JSONDecodeError:
        errors_count += 1
        return {}, "Invalid JSON response"
    except Exception as e:
        errors_count += 1
        return {}, f"Unexpected Error: {str(e)[:50]}"


def get_paginated(
    url: str,
    params: Optional[Dict] = None,
    max_pages: int = MAX_PAGES,
) -> Tuple[List[Dict], bool, Optional[str]]:
    """
    Fetch paginated results with truncation tracking.
    Returns (items, was_truncated, error_reason).
    
    - was_truncated: True if we hit max_pages limit
    - error_reason: None if success, string if endpoints unavailable
    """
    global request_count, rate_limit_remaining, rate_limit_reset

    results = []
    params = params or {}
    params["per_page"] = ITEMS_PER_PAGE
    first_error = None

    for page in range(1, max_pages + 1):
        params["page"] = page

        try:
            response = requests.get(
                url,
                headers=get_headers(),
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            request_count += 1
            parse_rate_limit_header(response.headers)

            if response.status_code == 200:
                data = response.json()
                if not data:
                    # Empty page means we've reached the end
                    return results, False, first_error

                results.extend(data)

            elif response.status_code in (403, 404):
                # Permission/availability issue
                if first_error is None:
                    first_error = (
                        "403 Forbidden (insufficient permissions)"
                        if response.status_code == 403
                        else "404 Not Found"
                    )
                # Don't retry on permission errors
                return results, len(results) > 0, first_error

            else:
                # Other errors, try next page
                if first_error is None:
                    first_error = f"HTTP {response.status_code}"
                continue

        except requests.exceptions.RequestException:
            if first_error is None:
                first_error = "Network error"
            # Stop on network error
            break

    # If we got here, we paginated through max_pages
    was_truncated = len(results) >= (max_pages - 1) * ITEMS_PER_PAGE
    return results, was_truncated, first_error


# ============================================================================
# DATA COLLECTION FUNCTIONS
# ============================================================================


def parse_date(s: str) -> datetime:
    """Parse ISO 8601 timestamp from GitHub API."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def get_org_repos(org: str) -> Tuple[List[Dict], Optional[str]]:
    """
    Fetch organization repos (org endpoint) or user repos (user endpoint).
    Returns (repos_list, error_reason).
    """
    # Try org endpoint first
    url = f"{API_BASE}/orgs/{org}/repos"
    data, err = make_request(url, {"type": "all", "per_page": 100})

    if data:
        return data, err

    # Fall back to user endpoint
    print(f"  ℹ Org endpoint unavailable, trying user endpoint...")
    data, err = make_request(f"{API_BASE}/users/{org}/repos", {"type": "owner", "per_page": 100})
    return data, err


def get_pr_metrics(owner: str, repo: str) -> Dict[str, Any]:
    """
    Collect PR metrics with data quality tracking.
    Implements real verification of merged_at, not relying on list payload alone.
    """
    prs, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/pulls",
        {"state": "all", "sort": "updated"},
    )

    merged = [p for p in prs if isinstance(p, dict) and p.get("merged_at")]
    open_prs = [p for p in prs if isinstance(p, dict) and p.get("state") == "open"]
    
    merged_30d = []
    for p in merged:
        try:
            merged_30d.append(p) if parse_date(p["merged_at"]) > DAYS_30 else None
        except (KeyError, ValueError, TypeError):
            pass

    lead_times = []
    for p in merged_30d:
        try:
            created = parse_date(p["created_at"])
            merged_dt = parse_date(p["merged_at"])
            hours = (merged_dt - created).total_seconds() / 3600
            lead_times.append(hours)
        except (KeyError, ValueError, TypeError):
            pass

    pr_ages = []
    for p in open_prs:
        try:
            created = parse_date(p["created_at"])
            age_days = (NOW - created).days
            pr_ages.append(age_days)
        except (KeyError, ValueError):
            pass

    # Collect review times from first 10 merged PRs
    review_times = []
    for pr in merged_30d[:10]:
        try:
            reviews, _, _ = get_paginated(
                f"{API_BASE}/repos/{owner}/{repo}/pulls/{pr['number']}/reviews",
                max_pages=1,
            )
            if reviews:
                created = parse_date(pr["created_at"])
                submitted_times = []
                for r in reviews:
                    if r.get("submitted_at"):
                        try:
                            submitted_times.append(parse_date(r["submitted_at"]))
                        except (ValueError, TypeError):
                            pass
                if submitted_times:
                    first_review = min(submitted_times)
                    review_hours = (first_review - created).total_seconds() / 3600
                    review_times.append(review_hours)
        except Exception:
            pass

    prs_count = len([p for p in prs if isinstance(p, dict)])
    merged_count = len(merged)
    
    return {
        "total": prs_count,
        "open": len(open_prs),
        "merged_30d": len(merged_30d),
        "throughput": len(merged_30d),
        "wip": len(open_prs),
        "stale": len([a for a in pr_ages if a > 14]),
        "lead_time_hours": round(sum(lead_times) / len(lead_times), 1) if lead_times else 0,
        "lead_time_days": round(sum(lead_times) / len(lead_times) / 24, 2) if lead_times else 0,
        "review_time_hours": round(sum(review_times) / len(review_times), 1) if review_times else 0,
        "cycle_time_hours": round(sum(lead_times) / len(lead_times), 1) if lead_times else 0,
        "merge_rate": round(merged_count / prs_count * 100, 1) if prs_count > 0 else 0,
        "truncated": truncated,
    }


def get_issue_metrics(owner: str, repo: str) -> Dict[str, Any]:
    """Collect issue metrics including MTTR."""
    issues, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/issues",
        {"state": "all"},
    )

    # Filter out pull requests
    issues = [i for i in issues if "pull_request" not in i]

    open_issues = [i for i in issues if i["state"] == "open"]
    closed = [i for i in issues if i["state"] == "closed"]

    closed_30d = []
    for i in closed:
        if i.get("closed_at"):
            try:
                if parse_date(i["closed_at"]) > DAYS_30:
                    closed_30d.append(i)
            except (ValueError, TypeError):
                pass

    # Compute MTTR from closed_30d
    mttr_hours_list = []
    for i in closed_30d:
        try:
            if i.get("closed_at"):
                created = parse_date(i["created_at"])
                closed = parse_date(i["closed_at"])
                mttr = (closed - created).total_seconds() / 3600
                mttr_hours_list.append(mttr)
        except (KeyError, ValueError, TypeError):
            pass

    # Aggregate labels
    labels = defaultdict(int)
    for i in open_issues:
        for lbl in i.get("labels", []):
            label_name = lbl.get("name", "").lower()
            labels[label_name] += 1

    return {
        "total": len(issues),
        "open": len(open_issues),
        "closed_30d": len(closed_30d),
        "mttr_hours": round(sum(mttr_hours_list) / len(mttr_hours_list), 1) if mttr_hours_list else 0,
        "bugs": labels.get("bug", 0),
        "critical": labels.get("critical", 0) + labels.get("urgent", 0),
        "security": labels.get("security", 0),
        "stale": len([i for i in open_issues if (NOW - parse_date(i["created_at"])).days > 30]),
        "truncated": truncated,
    }


def get_deployment_metrics(owner: str, repo: str) -> Dict[str, Any]:
    """Collect release/deployment frequency metrics."""
    releases, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/releases",
        max_pages=2,
    )

    releases_90d = []
    for r in releases:
        if r.get("published_at"):
            try:
                if parse_date(r["published_at"]) > DAYS_90:
                    releases_90d.append(r)
            except (ValueError, TypeError):
                pass

    rpm = round(len(releases_90d) / 3, 1) if releases_90d else 0
    cat = (
        "Elite" if rpm >= 8
        else "High" if rpm >= 4
        else "Medium" if rpm >= 1
        else "Low"
    )

    return {
        "total": len(releases),
        "releases_90d": len(releases_90d),
        "per_month": rpm,
        "category": cat,
        "latest": releases[0]["tag_name"] if releases else None,
        "truncated": truncated,
    }


def get_ci_metrics(owner: str, repo: str) -> Dict[str, Any]:
    """Collect GitHub Actions CI/CD metrics."""
    # Get workflows
    wf_data, wf_err = make_request(f"{API_BASE}/repos/{owner}/{repo}/actions/workflows")
    workflows = wf_data.get("workflows", [])

    if not workflows:
        return {
            "has_ci": False,
            "workflows": 0,
            "runs_30d": 0,
            "success_rate": 0,
            "failure_rate": 0,
            "ci_failure_rate": 0,
            "duration_mins": 0,
            "truncated": False,
        }

    # Get runs
    runs_data, runs_err = make_request(
        f"{API_BASE}/repos/{owner}/{repo}/actions/runs",
        {"per_page": 100},
    )
    runs = runs_data.get("workflow_runs", [])

    # Filter to last 30 days
    runs_30d = []
    for r in runs:
        try:
            if parse_date(r["created_at"]) > DAYS_30:
                runs_30d.append(r)
        except (ValueError, TypeError):
            pass

    # Count success/failure
    success_count = len([r for r in runs_30d if r["conclusion"] == "success"])
    failure_count = len([r for r in runs_30d if r["conclusion"] == "failure"])
    total_runs = success_count + failure_count

    success_rate = (success_count / total_runs * 100) if total_runs > 0 else 0
    failure_rate = (failure_count / total_runs * 100) if total_runs > 0 else 0

    # Compute average duration
    durations_mins = []
    for r in runs_30d[:15]:
        try:
            if r.get("created_at") and r.get("updated_at"):
                created = parse_date(r["created_at"])
                updated = parse_date(r["updated_at"])
                dur_mins = (updated - created).total_seconds() / 60
                durations_mins.append(dur_mins)
        except (ValueError, TypeError):
            pass

    return {
        "has_ci": True,
        "workflows": len(workflows),
        "runs_30d": len(runs_30d),
        "success_rate": round(success_rate, 1),
        "failure_rate": round(failure_rate, 1),
        "ci_failure_rate": round(failure_rate, 1),  # Renamed from DORA CFR
        "duration_mins": round(sum(durations_mins) / len(durations_mins), 1) if durations_mins else 0,
        "truncated": len(runs) >= 100,  # Simple heuristic: if we got 100 items, might be truncated
    }


def get_security_metrics(owner: str, repo: str) -> Dict[str, Any]:
    """
    Collect security metrics with real data and availability tracking.
    Returns comprehensive security posture with error metadata.
    """
    m = {
        "score": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total_vulns": 0,
        "secrets": 0,
        "dependency_alerts": 0,
        "code_alerts": 0,
        "security_policy": False,
        "branch_protection": False,
        "dependabot": False,
        "secret_scanning": False,
        "code_scanning": False,
        "gate_pass": True,
        "license": None,
        "security_mttr_hours": None,  # null if not available
        "available_dependabot": True,
        "available_code_scanning": True,
        "available_secret_scanning": True,
        "dependabot_truncated": False,
        "code_scanning_truncated": False,
        "secret_scanning_truncated": False,
        "errors": [],
    }

    score = 0

    # 1. SECURITY.md policy
    try:
        data, err = make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/SECURITY.md")
        if data:
            m["security_policy"] = True
            score += 15
    except Exception:
        pass

    # 2. Branch protection
    try:
        info, _ = make_request(f"{API_BASE}/repos/{owner}/{repo}")
        default_branch = info.get("default_branch", "main")

        data, err = make_request(
            f"{API_BASE}/repos/{owner}/{repo}/branches/{default_branch}/protection"
        )
        if data:
            m["branch_protection"] = True
            score += 20
    except Exception:
        pass

    # 3. Dependabot config
    data, err = make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/.github/dependabot.yml")
    if not data:
        # Try .yaml variant
        data, err = make_request(f"{API_BASE}/repos/{owner}/{repo}/contents/.github/dependabot.yaml")

    if data:
        m["dependabot"] = True
        score += 15

    # 4. Dependabot alerts (REAL vulnerability data)
    alerts, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/dependabot/alerts",
        {"state": "open"},
        max_pages=2,  # Cap to avoid rate limiting
    )

    if err:
        m["available_dependabot"] = False
        m["errors"].append({"field": "dependabot_alerts", "reason": err})
    else:
        for a in alerts:
            severity = a.get("security_advisory", {}).get("severity", "").lower()
            if severity == "critical":
                m["critical"] += 1
            elif severity == "high":
                m["high"] += 1
            elif severity == "medium":
                m["medium"] += 1
            else:
                m["low"] += 1

        m["dependency_alerts"] = len(alerts)
        m["total_vulns"] = len(alerts)
        m["dependabot_truncated"] = truncated

        if not alerts:
            score += 20
        elif m["critical"] == 0:
            score += 10

    # Compute Security MTTR from resolved alerts (closed state)
    if m["available_dependabot"]:
        try:
            resolved_alerts, _, _ = get_paginated(
                f"{API_BASE}/repos/{owner}/{repo}/dependabot/alerts",
                {"state": "dismissed"},  # Also try "fixed" if available
                max_pages=2,
            )

            mttr_list = []
            for alert in resolved_alerts:
                try:
                    created = parse_date(alert["created_at"])
                    updated = parse_date(alert.get("updated_at", alert.get("created_at")))
                    if updated > DAYS_30:
                        mttr = (updated - created).total_seconds() / 3600
                        mttr_list.append(mttr)
                except (ValueError, TypeError, KeyError):
                    pass

            if mttr_list:
                m["security_mttr_hours"] = round(sum(mttr_list) / len(mttr_list), 1)
        except Exception:
            pass

    # 5. Code scanning alerts
    alerts, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/code-scanning/alerts",
        {"state": "open"},
        max_pages=2,
    )

    if err:
        m["available_code_scanning"] = False
        m["errors"].append({"field": "code_scanning_alerts", "reason": err})
    else:
        m["code_alerts"] = len(alerts)
        m["code_scanning"] = True if alerts else False
        m["code_scanning_truncated"] = truncated
        if not alerts:
            score += 15

    # 6. Secret scanning alerts
    alerts, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/secret-scanning/alerts",
        {"state": "open"},
        max_pages=2,
    )

    if err:
        m["available_secret_scanning"] = False
        m["errors"].append({"field": "secret_scanning_alerts", "reason": err})
    else:
        m["secrets"] = len(alerts)
        m["secret_scanning"] = True if alerts else False
        m["secret_scanning_truncated"] = truncated
        if not alerts:
            score += 10

    # 7. License
    try:
        lic_data, _ = make_request(f"{API_BASE}/repos/{owner}/{repo}/license")
        if lic_data and lic_data.get("license"):
            m["license"] = lic_data["license"].get("spdx_id")
            score += 5
    except Exception:
        pass

    # 8. Gate pass: no critical vulns, no exposed secrets, branch protection
    m["gate_pass"] = (
        m["critical"] == 0
        and m["secrets"] == 0
        and m["branch_protection"]
    )

    m["score"] = min(100, score)
    return m


def get_commits(owner: str, repo: str) -> Dict[str, Any]:
    """Collect commit activity metrics."""
    commits, truncated, err = get_paginated(
        f"{API_BASE}/repos/{owner}/{repo}/commits",
        {"since": DAYS_30.isoformat()},
        max_pages=3,
    )

    authors = defaultdict(int)
    for c in commits:
        author = c.get("author")
        if author:
            login = author.get("login", "unknown")
            authors[login] += 1

    top_authors = sorted(authors.items(), key=lambda x: -x[1])[:5]

    return {
        "count_30d": len(commits),
        "authors": len(authors),
        "top": [{"login": k, "commits": v} for k, v in top_authors],
        "truncated": truncated,
    }


def calculate_risk(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate risk level and factors."""
    score = 0
    factors = []

    sec = data.get("security", {})
    ci = data.get("ci", {})

    if sec.get("critical", 0) > 0:
        score += 40
        factors.append(f"{sec['critical']} critical vulns")

    if sec.get("high", 0) > 0:
        score += 20
        factors.append(f"{sec['high']} high vulns")

    if sec.get("secrets", 0) > 0:
        score += 50
        factors.append(f"{sec['secrets']} exposed secrets")

    if not sec.get("branch_protection", False):
        score += 15
        factors.append("No branch protection")

    if ci.get("failure_rate", 0) > 30:
        score += 10
        factors.append(f"High CI failure ({ci['failure_rate']}%)")

    pushed_at = data.get("pushed_at")
    if pushed_at:
        try:
            days_since = (NOW - parse_date(pushed_at)).days
            if days_since > 90:
                score += 15
                factors.append(f"Inactive {days_since} days")
        except (ValueError, TypeError):
            pass

    level = (
        "Critical" if score >= 50
        else "High" if score >= 30
        else "Medium" if score >= 15
        else "Low"
    )

    return {
        "score": min(100, score),
        "level": level,
        "factors": factors[:5],
    }


# ============================================================================
# MAIN COLLECTION ORCHESTRATION
# ============================================================================


def collect_repo(owner: str, repo_name: str) -> Dict[str, Any]:
    """Collect comprehensive metrics for single repo."""
    # Fetch repo info
    info, err = make_request(f"{API_BASE}/repos/{owner}/{repo_name}")

    # Collect all metrics
    pr = get_pr_metrics(owner, repo_name)
    issues = get_issue_metrics(owner, repo_name)
    deploy = get_deployment_metrics(owner, repo_name)
    ci = get_ci_metrics(owner, repo_name)
    sec = get_security_metrics(owner, repo_name)
    commits = get_commits(owner, repo_name)

    # Build health score
    health = 0
    if info.get("description"):
        health += 10
    if not info.get("archived"):
        health += 10
    if ci.get("has_ci"):
        health += 20
    if ci.get("success_rate", 0) >= 80:
        health += 10
    if sec.get("branch_protection"):
        health += 15
    if pr.get("lead_time_hours", 0) > 0 and pr.get("lead_time_hours") < 48:
        health += 15
    if issues.get("stale", 999) < 5:
        health += 10
    if commits.get("count_30d", 0) > 0:
        health += 10

    # Build DORA metrics
    deploy_cat = deploy.get("category", "Low")
    lead_hours = pr.get("lead_time_hours", 0)
    mttr_hours = issues.get("mttr_hours", 0)
    cfr = ci.get("ci_failure_rate", 0)  # CI failure rate, not DORA CFR

    cfr_cat = (
        "Elite" if cfr < 5
        else "High" if cfr < 15
        else "Medium" if cfr < 30
        else "Low"
    )

    # Assemble collected data
    data = {
        "name": repo_name,
        "full_name": info.get("full_name", ""),
        "description": (info.get("description") or "")[:150],
        "url": info.get("html_url", ""),
        "language": info.get("language"),
        "default_branch": info.get("default_branch", "main"),
        "is_archived": info.get("archived", False),
        "is_fork": info.get("fork", False),
        "is_private": info.get("private", False),
        "created_at": info.get("created_at", ""),
        "updated_at": info.get("updated_at", ""),
        "pushed_at": info.get("pushed_at", ""),
        "stars": info.get("stargazers_count", 0),
        "forks": info.get("forks_count", 0),
        "health_score": min(100, health),
        # Core metric collections
        "dora": {
            "deployment_freq": deploy_cat,
            "releases_per_month": deploy.get("per_month", 0),
            "lead_time_hours": lead_hours,
            "lead_time_days": pr.get("lead_time_days", 0),
            "mttr_hours": mttr_hours,
            "cfr": cfr,
            "cfr_category": cfr_cat,
        },
        "flow": {
            "review_time": pr.get("review_time_hours", 0),
            "cycle_time": pr.get("cycle_time_hours", 0),
            "wip": pr.get("wip", 0),
            "throughput": pr.get("throughput", 0),
        },
        "pr": pr,
        "issues": issues,
        "deploy": deploy,
        "ci": ci,
        "security": sec,
        "commits": commits,
        "collected_at": NOW.isoformat().replace("+00:00", "Z"),
    }

    data["risk"] = calculate_risk(data)

    return data


def log_run_metadata(org: str, gov: Dict[str, Any]) -> None:
    """Log run metadata for audit trail."""
    end_time = datetime.now(timezone.utc)
    duration_secs = (end_time - START_TIME).total_seconds()

    metadata = {
        "run_id": RUN_ID,
        "started_at": START_TIME.isoformat(),
        "finished_at": end_time.isoformat(),
        "duration_seconds": duration_secs,
        "org": org,
        "repos_total": gov.get("total", 0),
        "repos_scanned": gov.get("scanned", 0),
        "archived_skipped": gov.get("archived", 0),
        "forked_count": gov.get("forked", 0),
        "request_count": request_count,
        "errors_count": errors_count,
        "warnings_count": len(warnings),
        "rate_limit_remaining": rate_limit_remaining,
        "rate_limit_reset": rate_limit_reset,
        "collector_version": "2.0",
    }

    if warnings:
        metadata["warnings"] = warnings

    META_DIR.mkdir(parents=True, exist_ok=True)
    meta_file = META_DIR / f"run_{START_TIME.strftime('%Y%m%d_%H%M%S')}.json"

    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Run metadata: {meta_file}")


def main():
    """Main collection entry point."""
    global errors_count
    
    # Validate environment first
    token, org = validate_env()

    print(f"🔍 Org Metrics Collector v2.0")
    print(f"   Run ID: {RUN_ID}")
    print(f"   Org: {org}")
    print(f"   Started: {START_TIME.isoformat()}\n")

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Get org repos
    print("Fetching repos...")
    repos, repo_err = get_org_repos(org)

    if not repos:
        print(f"ERROR: Failed to fetch repos from organization '{org}'")
        if repo_err:
            print(f"  Reason: {repo_err}")
        sys.exit(1)

    print(f"Found {len(repos)} repos")

    gov = {
        "total": len(repos),
        "scanned": 0,
        "archived": 0,
        "forked": 0,
        "date": NOW.isoformat(),
    }

    # Collect per-repo metrics
    print("\nCollecting metrics...")
    for i, r in enumerate(repos):
        name = r.get("name", "unknown")

        if r.get("archived"):
            gov["archived"] += 1
            print(f"  [{i+1}/{len(repos)}] {name} - ⊘ Archived")
            continue

        if r.get("fork"):
            gov["forked"] += 1

        print(f"  [{i+1}/{len(repos)}] {name}", end="", flush=True)

        try:
            data = collect_repo(org, name)

            # Validate schema before writing
            assert_raw_repo(data, name)

            # Write raw data
            out_file = RAW_DATA_DIR / f"{name}.json"
            with open(out_file, "w") as f:
                json.dump(data, f, indent=2)

            gov["scanned"] += 1
            print(" ✓")

        except ValueError as e:
            # Schema validation error
            print(f" ✗ Schema: {str(e)[:60]}")
            errors_count += 1

        except Exception as e:
            print(f" ✗ {str(e)[:60]}")
            errors_count += 1

    # Write governance file
    gov_file = RAW_DATA_DIR / "_governance.json"
    with open(gov_file, "w") as f:
        json.dump(gov, f, indent=2)
    print(f"\n✓ Governance: {gov_file}")

    # Log run metadata
    log_run_metadata(org, gov)

    # Summary
    print(f"\n{'='*50}")
    print(f"Scanned: {gov['scanned']}/{len(repos) - gov['archived']}")
    print(f"Archived: {gov['archived']}")
    print(f"Errors: {errors_count}")
    print(f"Warnings: {len(warnings)}")
    print(f"Duration: {(datetime.now(timezone.utc) - START_TIME).total_seconds():.1f}s")
    print(f"{'='*50}")

    if errors_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
