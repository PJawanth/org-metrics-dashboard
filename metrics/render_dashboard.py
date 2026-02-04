#!/usr/bin/env python3
"""
Render the metrics dashboard as a static HTML website.
Uses Jinja2 templates to generate the final output.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: Jinja2 is required. Install with: pip install jinja2")
    exit(1)

AGGREGATED_DIR = Path("data/aggregated")
TEMPLATES_DIR = Path("metrics/templates")
SITE_DIR = Path("site")


def load_metrics() -> Dict[str, Any]:
    """Load aggregated metrics data."""
    metrics_file = AGGREGATED_DIR / "org-metrics.json"
    
    if not metrics_file.exists():
        print(f"Error: {metrics_file} not found. Run aggregate.py first.")
        return {}
    
    with open(metrics_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_number(value: int) -> str:
    """Format large numbers with K/M suffixes."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except:
        return date_str


def time_ago(date_str: str) -> str:
    """Convert ISO date to relative time."""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            return "just now"
    except:
        return date_str


def get_language_color(language: str) -> str:
    """Get color for programming language (GitHub-style)."""
    colors = {
        "Python": "#3572A5",
        "JavaScript": "#f1e05a",
        "TypeScript": "#2b7489",
        "Java": "#b07219",
        "C#": "#178600",
        "C++": "#f34b7d",
        "C": "#555555",
        "Go": "#00ADD8",
        "Rust": "#dea584",
        "Ruby": "#701516",
        "PHP": "#4F5D95",
        "Swift": "#ffac45",
        "Kotlin": "#F18E33",
        "Scala": "#c22d40",
        "Shell": "#89e051",
        "PowerShell": "#012456",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "Dockerfile": "#384d54",
        "HCL": "#844FBA",
        "Bicep": "#519aba",
    }
    return colors.get(language, "#586069")


def render_dashboard() -> None:
    """Render the dashboard HTML."""
    print("Loading metrics data...")
    metrics = load_metrics()
    
    if not metrics:
        return
    
    # Ensure output directory exists
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"])
    )
    
    # Add custom filters
    env.filters["format_number"] = format_number
    env.filters["format_date"] = format_date
    env.filters["time_ago"] = time_ago
    env.filters["lang_color"] = get_language_color
    
    # Get organization name from environment or metrics
    org_name = os.environ.get("GITHUB_ORG", "Organization")
    
    # Prepare template context
    context = {
        "org_name": org_name,
        "generated_at": metrics.get("generated_at"),
        "summary": metrics.get("summary", {}),
        "languages": metrics.get("languages", {}),
        "top_repos": metrics.get("top_repos", {}),
        "activity": metrics.get("activity", {}),
        "contributors": metrics.get("contributors", {}),
        "licenses": metrics.get("licenses", {}),
        "topics": metrics.get("topics", {}),
        "repos": metrics.get("repos", []),
        "now": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }
    
    # Render main template
    print("Rendering dashboard...")
    template = env.get_template("index.html")
    html_output = template.render(**context)
    
    # Write output
    output_file = SITE_DIR / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)
    
    print(f"✓ Dashboard rendered to {output_file}")
    
    # Copy any static assets if they exist
    static_src = TEMPLATES_DIR / "static"
    if static_src.exists():
        import shutil
        static_dst = SITE_DIR / "static"
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)
        print(f"✓ Static assets copied to {static_dst}")
    
    # Create a simple data.json for any client-side needs
    data_file = SITE_DIR / "data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f)
    print(f"✓ Data file saved to {data_file}")


def main():
    """Main entry point."""
    render_dashboard()


if __name__ == "__main__":
    main()
