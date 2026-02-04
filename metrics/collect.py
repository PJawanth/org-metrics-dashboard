#!/usr/bin/env python3
"""
Collect metrics from GitHub repositories in an organization.
Fetches repository stats, issues, PRs, and contributor data.
"""

import os
import json
import requests
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
ORG_NAME = os.environ.get("GITHUB_ORG", "")
API_BASE = "https://api.github.com"
RAW_DATA_DIR = Path("data/raw")


def get_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "org-metrics-dashboard"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def make_request(url: str, params: Optional[Dict] = None) -> Any:
    """Make a GET request to the GitHub API."""
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()


def get_paginated_results(url: str, params: Optional[Dict] = None) -> List[Any]:
    """Get all results from a paginated GitHub API endpoint."""
    results = []
    params = params or {}
    params["per_page"] = 100
    page = 1
    
    while True:
        params["page"] = page
        response = requests.get(url, headers=get_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            break
            
        results.extend(data)
        page += 1
        
        # Safety limit
        if page > 50:
            break
            
    return results


def get_org_repos(org: str) -> List[Dict]:
    """Get all repositories in an organization or user account."""
    # Try organization endpoint first
    try:
        url = f"{API_BASE}/orgs/{org}/repos"
        return get_paginated_results(url, {"type": "all", "sort": "updated"})
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # Fall back to user endpoint
            print(f"  '{org}' is a user account, not an organization. Using user repos endpoint.")
            url = f"{API_BASE}/users/{org}/repos"
            return get_paginated_results(url, {"type": "owner", "sort": "updated"})
        raise


def get_repo_stats(org: str, repo: str) -> Dict[str, Any]:
    """Get detailed statistics for a repository."""
    base_url = f"{API_BASE}/repos/{org}/{repo}"
    
    # Get basic repo info
    repo_info = make_request(base_url)
    
    # Get contributors
    try:
        contributors = get_paginated_results(f"{base_url}/contributors")
    except requests.exceptions.HTTPError:
        contributors = []
    
    # Get recent commits (last 30 days)
    since_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
    try:
        commits = get_paginated_results(f"{base_url}/commits", {"since": since_date})
    except requests.exceptions.HTTPError:
        commits = []
    
    # Get open issues and PRs
    try:
        issues = get_paginated_results(f"{base_url}/issues", {"state": "open"})
    except requests.exceptions.HTTPError:
        issues = []
    
    # Separate issues and PRs
    open_issues = [i for i in issues if "pull_request" not in i]
    open_prs = [i for i in issues if "pull_request" in i]
    
    # Get closed issues/PRs (last 30 days)
    try:
        closed_issues = get_paginated_results(
            f"{base_url}/issues", 
            {"state": "closed", "since": since_date}
        )
    except requests.exceptions.HTTPError:
        closed_issues = []
    
    closed_issues_count = len([i for i in closed_issues if "pull_request" not in i])
    merged_prs_count = len([i for i in closed_issues if "pull_request" in i])
    
    # Get languages
    try:
        languages = make_request(f"{base_url}/languages")
    except requests.exceptions.HTTPError:
        languages = {}
    
    # Get release info
    try:
        releases = make_request(f"{base_url}/releases")
        latest_release = releases[0] if releases else None
    except (requests.exceptions.HTTPError, IndexError):
        latest_release = None
    
    return {
        "name": repo_info["name"],
        "full_name": repo_info["full_name"],
        "description": repo_info.get("description", ""),
        "url": repo_info["html_url"],
        "homepage": repo_info.get("homepage", ""),
        "language": repo_info.get("language"),
        "languages": languages,
        "stars": repo_info["stargazers_count"],
        "forks": repo_info["forks_count"],
        "watchers": repo_info["watchers_count"],
        "open_issues_count": len(open_issues),
        "open_prs_count": len(open_prs),
        "closed_issues_30d": closed_issues_count,
        "merged_prs_30d": merged_prs_count,
        "commits_30d": len(commits),
        "contributors_count": len(contributors),
        "top_contributors": [
            {"login": c["login"], "contributions": c["contributions"]}
            for c in contributors[:10]
        ],
        "created_at": repo_info["created_at"],
        "updated_at": repo_info["updated_at"],
        "pushed_at": repo_info["pushed_at"],
        "default_branch": repo_info["default_branch"],
        "is_archived": repo_info["archived"],
        "is_fork": repo_info["fork"],
        "license": repo_info.get("license", {}).get("spdx_id") if repo_info.get("license") else None,
        "topics": repo_info.get("topics", []),
        "latest_release": {
            "tag": latest_release["tag_name"],
            "name": latest_release["name"],
            "published_at": latest_release["published_at"],
            "url": latest_release["html_url"]
        } if latest_release else None,
        "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }


def collect_org_metrics(org: str) -> None:
    """Collect metrics for all repositories in an organization."""
    print(f"Collecting metrics for organization: {org}")
    
    # Ensure output directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get all repos
    repos = get_org_repos(org)
    print(f"Found {len(repos)} repositories")
    
    # Collect stats for each repo
    for repo in repos:
        repo_name = repo["name"]
        print(f"  Collecting metrics for: {repo_name}")
        
        try:
            stats = get_repo_stats(org, repo_name)
            
            # Save to file
            output_file = RAW_DATA_DIR / f"{repo_name}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
                
            print(f"    ✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"    ✗ Error collecting metrics: {e}")
    
    print("Collection complete!")


def main():
    """Main entry point."""
    if not GITHUB_TOKEN:
        print("Warning: GITHUB_TOKEN not set. API rate limits will be very low.")
    
    if not ORG_NAME:
        print("Error: GITHUB_ORG environment variable not set.")
        print("Usage: GITHUB_ORG=your-org python collect.py")
        return
    
    collect_org_metrics(ORG_NAME)


if __name__ == "__main__":
    main()
