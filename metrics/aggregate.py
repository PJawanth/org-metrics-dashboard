#!/usr/bin/env python3
"""
Aggregate raw repository metrics into organization-level summaries.
Creates rollup statistics and trends for the dashboard.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

RAW_DATA_DIR = Path("data/raw")
AGGREGATED_DIR = Path("data/aggregated")


def load_raw_data() -> List[Dict[str, Any]]:
    """Load all raw repository data files."""
    repos = []
    
    if not RAW_DATA_DIR.exists():
        print(f"Warning: {RAW_DATA_DIR} does not exist")
        return repos
    
    for json_file in RAW_DATA_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                repos.append(data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return repos


def calculate_org_summary(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate organization-wide summary statistics."""
    if not repos:
        return {}
    
    # Filter out archived repos for activity metrics
    active_repos = [r for r in repos if not r.get("is_archived", False)]
    
    # Basic counts
    total_repos = len(repos)
    active_repo_count = len(active_repos)
    archived_count = len([r for r in repos if r.get("is_archived", False)])
    forked_count = len([r for r in repos if r.get("is_fork", False)])
    
    # Aggregate metrics
    total_stars = sum(r.get("stars", 0) for r in repos)
    total_forks = sum(r.get("forks", 0) for r in repos)
    total_watchers = sum(r.get("watchers", 0) for r in repos)
    total_open_issues = sum(r.get("open_issues_count", 0) for r in active_repos)
    total_open_prs = sum(r.get("open_prs_count", 0) for r in active_repos)
    total_commits_30d = sum(r.get("commits_30d", 0) for r in active_repos)
    total_closed_issues_30d = sum(r.get("closed_issues_30d", 0) for r in active_repos)
    total_merged_prs_30d = sum(r.get("merged_prs_30d", 0) for r in active_repos)
    
    # Unique contributors across all repos
    all_contributors = set()
    for repo in repos:
        for contributor in repo.get("top_contributors", []):
            all_contributors.add(contributor["login"])
    
    return {
        "total_repos": total_repos,
        "active_repos": active_repo_count,
        "archived_repos": archived_count,
        "forked_repos": forked_count,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_watchers": total_watchers,
        "total_open_issues": total_open_issues,
        "total_open_prs": total_open_prs,
        "total_commits_30d": total_commits_30d,
        "total_closed_issues_30d": total_closed_issues_30d,
        "total_merged_prs_30d": total_merged_prs_30d,
        "unique_contributors": len(all_contributors),
        "avg_stars_per_repo": round(total_stars / total_repos, 2) if total_repos > 0 else 0,
        "avg_open_issues_per_repo": round(total_open_issues / active_repo_count, 2) if active_repo_count > 0 else 0,
    }


def calculate_language_stats(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate language distribution across repositories."""
    language_bytes = defaultdict(int)
    language_repos = defaultdict(int)
    
    for repo in repos:
        if repo.get("is_archived"):
            continue
            
        # Primary language
        primary_lang = repo.get("language")
        if primary_lang:
            language_repos[primary_lang] += 1
        
        # All languages (by bytes)
        languages = repo.get("languages", {})
        for lang, bytes_count in languages.items():
            language_bytes[lang] += bytes_count
    
    # Calculate percentages
    total_bytes = sum(language_bytes.values())
    language_percentages = {}
    
    if total_bytes > 0:
        for lang, bytes_count in sorted(language_bytes.items(), key=lambda x: -x[1]):
            percentage = round((bytes_count / total_bytes) * 100, 2)
            if percentage >= 0.1:  # Only include languages with >= 0.1%
                language_percentages[lang] = {
                    "bytes": bytes_count,
                    "percentage": percentage,
                    "repo_count": language_repos.get(lang, 0)
                }
    
    return {
        "by_bytes": language_percentages,
        "primary_language_count": dict(sorted(language_repos.items(), key=lambda x: -x[1])),
        "total_languages": len(language_bytes)
    }


def calculate_top_repos(repos: List[Dict], limit: int = 10) -> Dict[str, List[Dict]]:
    """Calculate top repositories by various metrics."""
    active_repos = [r for r in repos if not r.get("is_archived", False)]
    
    def get_top(key: str, repo_list: List[Dict] = None) -> List[Dict]:
        repo_list = repo_list or active_repos
        sorted_repos = sorted(repo_list, key=lambda x: x.get(key, 0), reverse=True)
        return [
            {
                "name": r["name"],
                "url": r["url"],
                "value": r.get(key, 0),
                "language": r.get("language"),
                "description": (r.get("description") or "")[:100]
            }
            for r in sorted_repos[:limit]
        ]
    
    return {
        "by_stars": get_top("stars", repos),  # Include archived for stars
        "by_forks": get_top("forks", repos),
        "by_commits_30d": get_top("commits_30d"),
        "by_open_issues": get_top("open_issues_count"),
        "by_contributors": get_top("contributors_count"),
    }


def calculate_activity_trends(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate activity indicators and health metrics."""
    active_repos = [r for r in repos if not r.get("is_archived", False)]
    
    # Categorize repos by activity level
    very_active = []  # >10 commits in 30 days
    active = []       # 1-10 commits in 30 days
    inactive = []     # 0 commits in 30 days
    
    for repo in active_repos:
        commits = repo.get("commits_30d", 0)
        repo_info = {
            "name": repo["name"],
            "url": repo["url"],
            "commits_30d": commits,
            "language": repo.get("language")
        }
        
        if commits > 10:
            very_active.append(repo_info)
        elif commits > 0:
            active.append(repo_info)
        else:
            inactive.append(repo_info)
    
    # Calculate issue velocity
    total_open = sum(r.get("open_issues_count", 0) for r in active_repos)
    total_closed_30d = sum(r.get("closed_issues_30d", 0) for r in active_repos)
    
    # PR velocity
    total_open_prs = sum(r.get("open_prs_count", 0) for r in active_repos)
    total_merged_30d = sum(r.get("merged_prs_30d", 0) for r in active_repos)
    
    return {
        "very_active_repos": len(very_active),
        "active_repos": len(active),
        "inactive_repos": len(inactive),
        "activity_breakdown": {
            "very_active": very_active[:5],
            "active": active[:5],
            "inactive": inactive[:5]
        },
        "issue_velocity": {
            "open": total_open,
            "closed_30d": total_closed_30d,
            "net_change": total_closed_30d - total_open  # Positive = reducing backlog
        },
        "pr_velocity": {
            "open": total_open_prs,
            "merged_30d": total_merged_30d
        }
    }


def calculate_contributor_stats(repos: List[Dict]) -> Dict[str, Any]:
    """Calculate contributor statistics across the organization."""
    contributor_contributions = defaultdict(int)
    contributor_repos = defaultdict(set)
    
    for repo in repos:
        if repo.get("is_archived"):
            continue
            
        for contributor in repo.get("top_contributors", []):
            login = contributor["login"]
            contributor_contributions[login] += contributor["contributions"]
            contributor_repos[login].add(repo["name"])
    
    # Sort by total contributions
    sorted_contributors = sorted(
        contributor_contributions.items(), 
        key=lambda x: -x[1]
    )
    
    top_contributors = [
        {
            "login": login,
            "total_contributions": contributions,
            "repo_count": len(contributor_repos[login]),
            "profile_url": f"https://github.com/{login}"
        }
        for login, contributions in sorted_contributors[:20]
    ]
    
    return {
        "total_unique_contributors": len(contributor_contributions),
        "top_contributors": top_contributors,
        "multi_repo_contributors": len([c for c, repos in contributor_repos.items() if len(repos) > 1])
    }


def calculate_license_stats(repos: List[Dict]) -> Dict[str, int]:
    """Calculate license distribution."""
    license_counts = defaultdict(int)
    
    for repo in repos:
        license_type = repo.get("license") or "None"
        license_counts[license_type] += 1
    
    return dict(sorted(license_counts.items(), key=lambda x: -x[1]))


def calculate_topic_stats(repos: List[Dict]) -> Dict[str, int]:
    """Calculate topic/tag distribution."""
    topic_counts = defaultdict(int)
    
    for repo in repos:
        for topic in repo.get("topics", []):
            topic_counts[topic] += 1
    
    return dict(sorted(topic_counts.items(), key=lambda x: -x[1])[:30])


def aggregate_metrics() -> None:
    """Main aggregation function."""
    print("Loading raw repository data...")
    repos = load_raw_data()
    
    if not repos:
        print("No repository data found. Run collect.py first.")
        return
    
    print(f"Loaded data for {len(repos)} repositories")
    
    # Ensure output directory exists
    AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Calculate all aggregations
    print("Calculating aggregations...")
    
    aggregated_data = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repo_count": len(repos),
        "summary": calculate_org_summary(repos),
        "languages": calculate_language_stats(repos),
        "top_repos": calculate_top_repos(repos),
        "activity": calculate_activity_trends(repos),
        "contributors": calculate_contributor_stats(repos),
        "licenses": calculate_license_stats(repos),
        "topics": calculate_topic_stats(repos),
        "repos": [
            {
                "name": r["name"],
                "url": r["url"],
                "description": r.get("description", ""),
                "language": r.get("language"),
                "stars": r.get("stars", 0),
                "forks": r.get("forks", 0),
                "open_issues": r.get("open_issues_count", 0),
                "open_prs": r.get("open_prs_count", 0),
                "commits_30d": r.get("commits_30d", 0),
                "updated_at": r.get("updated_at"),
                "is_archived": r.get("is_archived", False),
                "license": r.get("license"),
                "topics": r.get("topics", [])
            }
            for r in sorted(repos, key=lambda x: x.get("stars", 0), reverse=True)
        ]
    }
    
    # Save aggregated data
    output_file = AGGREGATED_DIR / "org-metrics.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=2)
    
    print(f"✓ Aggregated metrics saved to {output_file}")
    
    # Print summary
    summary = aggregated_data["summary"]
    print("\n=== Organization Summary ===")
    print(f"Total Repositories: {summary.get('total_repos', 0)}")
    print(f"Active Repositories: {summary.get('active_repos', 0)}")
    print(f"Total Stars: {summary.get('total_stars', 0)}")
    print(f"Total Forks: {summary.get('total_forks', 0)}")
    print(f"Open Issues: {summary.get('total_open_issues', 0)}")
    print(f"Open PRs: {summary.get('total_open_prs', 0)}")
    print(f"Commits (30d): {summary.get('total_commits_30d', 0)}")
    print(f"Unique Contributors: {summary.get('unique_contributors', 0)}")


def main():
    """Main entry point."""
    aggregate_metrics()


if __name__ == "__main__":
    main()
