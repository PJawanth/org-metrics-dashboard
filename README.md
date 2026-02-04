# Organization Metrics Dashboard

A GitHub organization metrics dashboard that collects repository statistics and renders them as a beautiful static website, automatically deployed via GitHub Pages.

![Dashboard Preview](https://img.shields.io/badge/Metrics-Dashboard-blue?style=for-the-badge)

## 🚀 Features

- **Repository Metrics**: Stars, forks, issues, PRs, commit activity
- **Language Distribution**: Visual breakdown of programming languages
- **Activity Tracking**: 30-day commit trends and velocity metrics
- **Contributor Stats**: Top contributors across the organization
- **Automated Updates**: Daily refresh via GitHub Actions
- **Static Deployment**: Hosted on GitHub Pages (free!)

## 📁 Project Structure

```
org-metrics-dashboard/
├── metrics/
│   ├── collect.py           # Fetches data from GitHub API
│   ├── aggregate.py         # Aggregates repo data into org-level stats
│   ├── render_dashboard.py  # Renders HTML dashboard
│   └── templates/
│       └── index.html       # Jinja2 template for the dashboard
├── data/
│   ├── raw/                  # Per-repo raw JSON (generated)
│   └── aggregated/           # Org rollups (generated)
├── site/                     # Final website output (generated)
├── .github/
│   └── workflows/
│       └── metrics-dashboard.yml
├── requirements.txt
└── README.md
```

## ⚙️ Setup

### 1. Fork or Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/org-metrics-dashboard.git
cd org-metrics-dashboard
```

### 2. Configure GitHub Secrets & Variables

Go to **Settings → Secrets and variables → Actions** and add:

#### Secrets:
| Name | Description |
|------|-------------|
| `ORG_READ_TOKEN` | Personal Access Token with `repo` and `read:org` scopes |

#### Variables:
| Name | Description |
|------|-------------|
| `GH_ORG_NAME` | Your GitHub organization name |

### 3. Enable GitHub Pages

1. Go to **Settings → Pages**
2. Set **Source** to "GitHub Actions"

### 4. Run the Workflow

The dashboard updates automatically:
- **Daily** at midnight UTC
- **On push** to main branch
- **Manually** via Actions → "Update Metrics Dashboard" → "Run workflow"

## 🖥️ Local Development

### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Locally

```bash
# Set environment variables
export GITHUB_TOKEN="your_personal_access_token"
export GITHUB_ORG="your_organization"

# Collect metrics
python metrics/collect.py

# Aggregate data
python metrics/aggregate.py

# Render dashboard
python metrics/render_dashboard.py

# View the dashboard
open site/index.html  # Or use a local server
```

### Using a Local Server

```bash
cd site
python -m http.server 8000
# Open http://localhost:8000
```

## 📊 Metrics Collected

### Repository Level
- Basic info (name, description, URL, language)
- Stars, forks, watchers
- Open issues and PRs
- Commits in last 30 days
- Contributors and their contributions
- Topics/tags
- License information
- Latest release

### Organization Level
- Total repositories (active, archived, forked)
- Aggregate stars, forks, watchers
- Combined open issues and PRs
- 30-day activity metrics
- Language distribution
- Top contributors
- Activity health indicators

## 🎨 Customization

### Modify the Template

Edit `metrics/templates/index.html` to customize the dashboard appearance.

### Add New Metrics

1. Update `metrics/collect.py` to fetch additional data
2. Update `metrics/aggregate.py` to aggregate the new metrics
3. Update `metrics/templates/index.html` to display them

### Change the Schedule

Edit `.github/workflows/metrics-dashboard.yml`:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

## 🔑 GitHub Token Permissions

Create a Personal Access Token (classic) with:
- `repo` - Full repository access
- `read:org` - Read organization membership

For fine-grained tokens:
- Repository access: All repositories
- Permissions: Read access to metadata, issues, pull requests

## 📝 License

MIT License - feel free to use and modify!