#!/usr/bin/env python3
"""Generate synthetic test data for dashboard testing."""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

NOW = datetime.now(timezone.utc)

# Synthetic repository configurations
REPOS = [
    {
        "name": "payment-service",
        "language": "Java",
        "description": "Core payment processing microservice",
        "profile": "elite",  # High performer
    },
    {
        "name": "user-auth-api",
        "language": "Python",
        "description": "User authentication and authorization service",
        "profile": "high",
    },
    {
        "name": "web-frontend",
        "language": "TypeScript",
        "description": "Main customer-facing web application",
        "profile": "high",
    },
    {
        "name": "mobile-app",
        "language": "Swift",
        "description": "iOS mobile application",
        "profile": "medium",
    },
    {
        "name": "data-pipeline",
        "language": "Python",
        "description": "ETL and data processing pipeline",
        "profile": "medium",
    },
    {
        "name": "notification-service",
        "language": "Go",
        "description": "Push notification and email service",
        "profile": "high",
    },
    {
        "name": "admin-dashboard",
        "language": "JavaScript",
        "description": "Internal admin management dashboard",
        "profile": "medium",
    },
    {
        "name": "legacy-billing",
        "language": "PHP",
        "description": "Legacy billing system (deprecated)",
        "profile": "low",
    },
    {
        "name": "ml-recommendation",
        "language": "Python",
        "description": "Machine learning recommendation engine",
        "profile": "elite",
    },
    {
        "name": "api-gateway",
        "language": "Go",
        "description": "API Gateway and rate limiting service",
        "profile": "high",
    },
    {
        "name": "docs-site",
        "language": "Markdown",
        "description": "Developer documentation website",
        "profile": "low",
    },
    {
        "name": "infrastructure-terraform",
        "language": "HCL",
        "description": "Infrastructure as Code - Terraform configs",
        "profile": "medium",
    },
    {
        "name": "analytics-service",
        "language": "Python",
        "description": "Real-time analytics and metrics collection",
        "profile": "high",
    },
    {
        "name": "search-service",
        "language": "Java",
        "description": "Elasticsearch-based search service",
        "profile": "elite",
    },
    {
        "name": "cache-layer",
        "language": "Go",
        "description": "Redis caching abstraction layer",
        "profile": "high",
    },
]

# Profile configurations
PROFILES = {
    "elite": {
        "releases_per_month": (8, 15),
        "lead_time_hours": (4, 20),
        "mttr_hours": (0.5, 1),
        "cfr": (1, 5),
        "ci_success_rate": (95, 99),
        "vulnerability_count": (0, 0),
        "security_score": (85, 100),
        "health_score": (85, 100),
        "commits_30d": (80, 150),
        "open_prs": (2, 5),
        "merged_prs": (20, 40),
        "has_ci": True,
        "branch_protection": True,
        "dependabot": True,
        "secret_scanning": True,
        "code_scanning": True,
    },
    "high": {
        "releases_per_month": (4, 8),
        "lead_time_hours": (20, 100),
        "mttr_hours": (2, 20),
        "cfr": (5, 15),
        "ci_success_rate": (85, 95),
        "vulnerability_count": (0, 2),
        "security_score": (65, 85),
        "health_score": (70, 85),
        "commits_30d": (40, 80),
        "open_prs": (3, 8),
        "merged_prs": (10, 25),
        "has_ci": True,
        "branch_protection": True,
        "dependabot": True,
        "secret_scanning": random.choice([True, False]),
        "code_scanning": False,
    },
    "medium": {
        "releases_per_month": (1, 4),
        "lead_time_hours": (100, 500),
        "mttr_hours": (20, 100),
        "cfr": (15, 30),
        "ci_success_rate": (70, 85),
        "vulnerability_count": (1, 5),
        "security_score": (45, 65),
        "health_score": (50, 70),
        "commits_30d": (15, 40),
        "open_prs": (1, 5),
        "merged_prs": (5, 15),
        "has_ci": True,
        "branch_protection": random.choice([True, False]),
        "dependabot": random.choice([True, False]),
        "secret_scanning": False,
        "code_scanning": False,
    },
    "low": {
        "releases_per_month": (0, 1),
        "lead_time_hours": (500, 1000),
        "mttr_hours": (100, 300),
        "cfr": (30, 50),
        "ci_success_rate": (50, 70),
        "vulnerability_count": (3, 10),
        "security_score": (20, 45),
        "health_score": (30, 50),
        "commits_30d": (0, 15),
        "open_prs": (0, 3),
        "merged_prs": (0, 5),
        "has_ci": False,
        "branch_protection": False,
        "dependabot": False,
        "secret_scanning": False,
        "code_scanning": False,
    },
}

def rand_range(r):
    """Get random value in range."""
    return round(random.uniform(r[0], r[1]), 1)

def rand_int_range(r):
    """Get random integer in range."""
    return random.randint(r[0], r[1])

def generate_repo(config):
    """Generate a synthetic repository with realistic metrics."""
    profile = PROFILES[config["profile"]]
    name = config["name"]
    
    releases_per_month = rand_range(profile["releases_per_month"])
    lead_time = rand_range(profile["lead_time_hours"])
    mttr = rand_range(profile["mttr_hours"])
    cfr = rand_range(profile["cfr"])
    
    # Determine DORA category
    if releases_per_month >= 8:
        deploy_freq = "Elite"
    elif releases_per_month >= 4:
        deploy_freq = "High"
    elif releases_per_month >= 1:
        deploy_freq = "Medium"
    else:
        deploy_freq = "Low"
    
    ci_success = rand_range(profile["ci_success_rate"]) if profile["has_ci"] else 0
    vuln_count = rand_int_range(profile["vulnerability_count"])
    security_score = rand_int_range(profile["security_score"])
    health_score = rand_int_range(profile["health_score"])
    
    # Activity dates
    days_ago = random.randint(1, 30) if config["profile"] != "low" else random.randint(30, 180)
    updated_at = (NOW - timedelta(days=days_ago)).isoformat()
    created_at = (NOW - timedelta(days=random.randint(365, 1000))).isoformat()
    
    open_prs = rand_int_range(profile["open_prs"])
    merged_prs = rand_int_range(profile["merged_prs"])
    commits = rand_int_range(profile["commits_30d"])
    
    # Generate contributor data
    contributors = []
    for i in range(random.randint(1, 5)):
        contributors.append({
            "login": f"dev{i+1}_{name[:3]}",
            "commits": random.randint(5, max(10, commits // 2))
        })
    
    repo_data = {
        "name": name,
        "full_name": f"TestOrg/{name}",
        "description": config["description"],
        "url": f"https://github.com/TestOrg/{name}",
        "language": config["language"],
        "languages": {config["language"]: random.randint(10000, 100000)},
        "default_branch": "main",
        "is_archived": False,
        "is_fork": name == "docs-site",  # One fork for testing
        "is_private": random.choice([True, False]),
        "topics": ["microservice", config["language"].lower()],
        "created_at": created_at,
        "updated_at": updated_at,
        "pushed_at": updated_at,
        "stars": random.randint(0, 500),
        "forks": random.randint(0, 50),
        "watchers": random.randint(1, 100),
        "contributors_count": len(contributors),
        "health_score": health_score,
        "dora": {
            "deployment_frequency": deploy_freq,
            "releases_per_month": releases_per_month,
            "lead_time_hours": lead_time,
            "lead_time_days": round(lead_time / 24, 1),
            "mttr_hours": mttr,
            "change_failure_rate": cfr,
        },
        "pull_requests": {
            "total_30d": open_prs + merged_prs,
            "merged_30d": merged_prs,
            "open_count": open_prs,
            "merge_rate": round(merged_prs / max(1, open_prs + merged_prs) * 100, 1),
            "avg_merge_time_hours": round(lead_time * 0.8, 1),
            "avg_open_age_hours": random.randint(12, 72),
            "stale_prs": random.randint(0, 2),
        },
        "issues": {
            "open_count": random.randint(2, 20),
            "closed_30d": random.randint(5, 30),
            "mttr_hours": mttr,
            "avg_age_days": random.randint(1, 14),
            "bug_count": random.randint(0, 5),
            "critical_count": 1 if vuln_count > 5 else 0,
            "stale_count": random.randint(0, 3),
        },
        "deployments": {
            "total_releases": int(releases_per_month * 6),
            "releases_90d": int(releases_per_month * 3),
            "releases_per_month": releases_per_month,
            "frequency_category": deploy_freq,
            "latest_release": f"v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,20)}",
            "total_tags": int(releases_per_month * 6),
        },
        "security": {
            "security_score": security_score,
            "has_security_policy": profile["branch_protection"],
            "branch_protection": profile["branch_protection"],
            "dependabot_enabled": profile["dependabot"],
            "vulnerability_count": vuln_count,
            "secret_scanning": profile["secret_scanning"],
            "code_scanning": profile["code_scanning"],
            "license": "MIT" if random.random() > 0.2 else None,
        },
        "ci_cd": {
            "has_ci_cd": profile["has_ci"],
            "workflow_count": random.randint(1, 4) if profile["has_ci"] else 0,
            "recent_runs": random.randint(20, 100) if profile["has_ci"] else 0,
            "success_rate": ci_success,
            "workflows": [
                {"name": "CI", "state": "active"},
                {"name": "Deploy", "state": "active"},
            ] if profile["has_ci"] else [],
        },
        "commits_30d": commits,
        "unique_authors_30d": len(contributors),
        "top_contributors": contributors,
        "collected_at": NOW.isoformat(),
    }
    
    return repo_data


def generate_all():
    """Generate all synthetic repositories."""
    print("🔧 Generating synthetic test data...")
    print(f"   Creating {len(REPOS)} repositories with varied profiles\n")
    
    for config in REPOS:
        repo = generate_repo(config)
        filename = RAW_DIR / f"{config['name']}.json"
        with open(filename, 'w') as f:
            json.dump(repo, f, indent=2)
        print(f"   ✅ {config['name']:25} [{config['profile']:6}] - {config['language']}")
    
    # Add one archived repo
    archived = generate_repo({
        "name": "old-service",
        "language": "Ruby",
        "description": "Archived legacy service",
        "profile": "low"
    })
    archived["is_archived"] = True
    with open(RAW_DIR / "old-service.json", 'w') as f:
        json.dump(archived, f, indent=2)
    print(f"   ✅ {'old-service':25} [archived] - Ruby")
    
    print(f"\n📁 Generated {len(REPOS) + 1} synthetic repositories in {RAW_DIR}/")


if __name__ == "__main__":
    generate_all()
