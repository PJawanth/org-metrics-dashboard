#!/usr/bin/env python3
"""
Render the professional leadership metrics dashboard.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Error: Jinja2 required. pip install jinja2")
    exit(1)

AGGREGATED_DIR = Path("data/aggregated")
TEMPLATES_DIR = Path("metrics/templates")
SITE_DIR = Path("site")


def load_metrics() -> Dict[str, Any]:
    metrics_file = AGGREGATED_DIR / "dashboard.json"
    if not metrics_file.exists():
        print(f"Error: {metrics_file} not found.")
        return {}
    with open(metrics_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_number(value) -> str:
    """Format number with M/K suffixes. Return 'N/A' for None values."""
    if value is None:
        return "N/A"
    try:
        value = float(value)
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(int(value))
    except (ValueError, TypeError):
        return "N/A"


def format_date(date_str: str) -> str:
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except:
        return date_str


def time_ago(date_str: str) -> str:
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        elif diff.days > 30:
            return f"{diff.days // 30}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        else:
            return "just now"
    except:
        return date_str


def get_dora_color(category: str) -> str:
    colors = {
        "Elite": "#22c55e",
        "High": "#3b82f6", 
        "Medium": "#f59e0b",
        "Low": "#ef4444",
        "None": "#6b7280"
    }
    return colors.get(category, "#6b7280")


def get_lang_color(language: str) -> str:
    colors = {
        "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#2b7489",
        "Java": "#b07219", "C#": "#178600", "C++": "#f34b7d", "C": "#555555",
        "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95",
        "Swift": "#ffac45", "Kotlin": "#F18E33", "Shell": "#89e051",
        "HTML": "#e34c26", "CSS": "#563d7c", "Dockerfile": "#384d54"
    }
    return colors.get(language, "#586069")


def render_dashboard() -> None:
    print("Loading metrics...")
    metrics = load_metrics()
    
    if not metrics:
        return
    
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"])
    )
    
    env.filters["format_number"] = format_number
    env.filters["format_date"] = format_date
    env.filters["time_ago"] = time_ago
    env.filters["dora_color"] = get_dora_color
    env.filters["lang_color"] = get_lang_color

    # Add filter for None values in templates
    def default_na(value):
        """Display 'N/A' for None values."""
        return "N/A" if value is None else value

    env.filters["default_na"] = default_na
    
    org_name = os.environ.get("GITHUB_ORG", metrics.get("org_name", "Organization"))
    
    context = {
        "org_name": org_name,
        "generated_at": metrics.get("generated_at"),
        "summary": metrics.get("summary", {}),
        "dora": metrics.get("dora", {}),
        "flow": metrics.get("flow", {}),
        "ci": metrics.get("ci", {}),
        "devops": metrics.get("devops", {}),
        "security": metrics.get("security", {}),
        "issues": metrics.get("issues", {}),
        "governance": metrics.get("governance", {}),
        "languages": metrics.get("languages", []),
        "repos": metrics.get("repos", []),
        "contributors": metrics.get("contributors", [])
    }
    
    print("Rendering dashboard...")
    template = env.get_template("index.html")
    html = template.render(**context)
    
    output_file = SITE_DIR / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✓ Dashboard: {output_file}")
    
    data_file = SITE_DIR / "data.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f)
    print(f"✓ Data: {data_file}")


def main():
    render_dashboard()


if __name__ == "__main__":
    main()
