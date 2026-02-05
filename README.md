# 📊 Organization Metrics Dashboard

[![Dashboard](https://img.shields.io/badge/Dashboard-Live-success?style=for-the-badge&logo=github)](https://pjawanth.github.io/org-metrics-dashboard/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=for-the-badge&logo=github-actions)](https://github.com/PJawanth/org-metrics-dashboard/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

A **comprehensive GitHub Organization Metrics Dashboard** that automatically collects, aggregates, and visualizes engineering metrics for leadership and team visibility. Built with Python and deployed via GitHub Pages.

## 🎯 Purpose

This dashboard provides **executive-level visibility** into your GitHub organization's:

| Category | What You Get |
|----------|--------------|
| 🚀 **DevOps Performance** | DORA metrics (Deployment Frequency, Lead Time, MTTR, CFR) |
| 🔒 **Security Posture** | Vulnerability tracking, security adoption rates |
| 📋 **Governance & Compliance** | Risk ranking, repo inventory, audit information |
| 📈 **Flow Metrics** | PR cycle time, review time, WIP, throughput |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                      │
│                   (Runs daily at midnight UTC)                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. COLLECT (metrics/collect.py)                                │
│     • Fetches data from GitHub API for each repository          │
│     • Collects commits, PRs, issues, releases, contributors     │
│     • Gathers security alerts, workflow runs, branch protection │
│     • Saves per-repo JSON files to data/raw/                    │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. AGGREGATE (metrics/aggregate.py)                            │
│     • Reads all raw JSON files                                  │
│     • Calculates org-wide summaries and averages                │
│     • Computes DORA, DevSecOps, and Governance metrics          │
│     • Saves to data/aggregated/dashboard.json                   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. RENDER (metrics/render_dashboard.py)                        │
│     • Loads aggregated data                                     │
│     • Renders HTML using Jinja2 template                        │
│     • Generates site/index.html with Chart.js visualizations   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. DEPLOY (GitHub Pages)                                       │
│     • Publishes dashboard to GitHub Pages                       │
│     • Available at: https://<user>.github.io/org-metrics-dashboard │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Metrics Collected

### 🚀 DevOps Metrics (DORA + Flow)

| Metric | Description | Category Thresholds |
|--------|-------------|---------------------|
| **Deployment Frequency** | How often code is deployed to production | Elite: ≥8/mo, High: ≥4/mo, Medium: ≥1/mo, Low: <1/mo |
| **Lead Time for Changes** | Time from commit to production | Elite: <24h, High: <1wk, Medium: <1mo, Low: >1mo |
| **Change Failure Rate (CFR)** | % of deployments causing failures | Elite: <5%, High: <15%, Medium: <30%, Low: >30% |
| **Mean Time to Recovery (MTTR)** | Time to recover from failures | Elite: <1h, High: <24h, Medium: <1wk, Low: >1wk |
| **PR Review Time** | Time for first review on pull requests | Hours |
| **PR Cycle Time** | Time from PR open to merge | Hours |
| **Work in Progress (WIP)** | Count of open pull requests | Count |
| **Throughput** | PRs merged in last 30 days | Count |
| **CI Success Rate** | Percentage of successful builds | % |
| **CI Failure Rate** | Percentage of failed builds | % |
| **Pipeline Duration** | Average CI/CD run time | Minutes |

### 🔒 DevSecOps Metrics

| Metric | Description |
|--------|-------------|
| **Critical/High/Medium/Low Vulnerabilities** | Open security alerts by severity |
| **Vulnerability Trend** | Direction: Improving / Stable / Worsening |
| **Security MTTR** | Time to remediate security issues |
| **SLA Compliance** | % of vulnerabilities fixed within SLA |
| **Secrets Exposure** | Count of detected secret leaks |
| **Dependency Risk** | Dependabot alerts count |
| **Security Gate Pass Rate** | % of repos passing security checks |
| **Branch Protection Adoption** | % of repos with branch protection enabled |
| **Dependabot Adoption** | % of repos with Dependabot enabled |
| **Secret Scanning Adoption** | % of repos with secret scanning |
| **Code Scanning Adoption** | % of repos with code scanning |
| **Security Policy Adoption** | % of repos with SECURITY.md |
| **License Compliance** | % of repos with valid license |

### 📋 Governance & Audit Metrics

| Metric | Description |
|--------|-------------|
| **Repository Inventory** | Total, scanned, archived, and forked repos |
| **Risk Ranking** | Repos categorized as Critical/High/Medium/Low risk |
| **Health Score** | Overall repository health (0-100) |
| **Security Score** | Security posture score (0-100) |
| **Scan Coverage** | % of repositories with security scanning enabled |
| **Activity Status** | Active / Stale / Inactive / Archived |

---

## 🎨 Dashboard Features

The dashboard includes **5 interactive tabs**:

| Tab | Contents |
|-----|----------|
| **📊 Overview** | KPI cards, DORA performance cards, charts, risk summary, top contributors |
| **🚀 DevOps** | All DORA + Flow metrics with per-repository breakdown table |
| **🔒 DevSecOps** | Security KPIs, adoption progress bars, vulnerability charts, per-repo security table |
| **📋 Governance** | Audit info, risk distribution charts, complete repo inventory |
| **📁 Repository Details** | Comprehensive searchable table with all metrics per repository |

### Visualizations Include:
- 📊 Bar charts for repository activity
- 🍩 Doughnut charts for language and security distribution
- 📈 Radar charts for security adoption
- 🎯 DORA performance cards with Elite/High/Medium/Low ratings

---

## 📁 Project Structure

```
org-metrics-dashboard/
├── 📂 metrics/
│   ├── collect.py              # Fetches data from GitHub API
│   ├── aggregate.py            # Aggregates per-repo data to org-level
│   ├── render_dashboard.py     # Renders HTML dashboard using Jinja2
│   └── 📂 templates/
│       └── index.html          # Dashboard HTML template
│
├── 📂 data/                    # Generated data (gitignored)
│   ├── 📂 raw/                 # Per-repository JSON files
│   └── 📂 aggregated/          # Org-wide aggregated metrics
│
├── 📂 site/                    # Generated website (gitignored)
│   ├── index.html              # Final dashboard HTML
│   └── data.json               # Dashboard data for debugging
│
├── 📂 .github/
│   └── 📂 workflows/
│       └── metrics-dashboard.yml  # GitHub Actions workflow
│
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Fork or Clone This Repository

```bash
git clone https://github.com/YOUR_USERNAME/org-metrics-dashboard.git
cd org-metrics-dashboard
```

### 2️⃣ Configure GitHub Secrets & Variables

Go to **Settings → Secrets and variables → Actions**:

#### 🔐 Secrets (Required)

| Name | Description |
|------|-------------|
| `ORG_READ_TOKEN` | GitHub Personal Access Token with `repo` scope |

**To create a PAT:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with scopes: `repo`, `read:org`
3. Copy the token and add it as a repository secret

#### 📝 Variables (Required)

| Name | Description | Example |
|------|-------------|---------|
| `GH_ORG_NAME` | Organization or username to scan | `PJawanth` |

### 3️⃣ Enable GitHub Pages

1. Go to **Settings → Pages**
2. Set **Source** to: `GitHub Actions`
3. Save

### 4️⃣ Run the Workflow

**Option A: Manual trigger**
- Go to **Actions → Update Metrics Dashboard → Run workflow**

**Option B: Wait for automatic run**
- Runs daily at midnight UTC

**Option C: Push to trigger**
- Any push to `metrics/**` or the workflow file triggers a run

---

## ⏰ Workflow Triggers

| Trigger | When |
|---------|------|
| ⏰ **Schedule** | Daily at midnight UTC (`0 0 * * *`) |
| 🖱️ **Manual** | Click "Run workflow" in Actions tab |
| 📤 **Push** | When changes pushed to `metrics/**` or `.github/workflows/metrics-dashboard.yml` |

---

## 🔐 Required Permissions

The GitHub token needs the following scopes:

| Scope | Purpose |
|-------|---------|
| `repo` | Access to repository data (commits, PRs, issues, etc.) |
| `read:org` | Read organization information (for org-level scanning) |

---

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Install dependencies
pip install requests jinja2

# Create data directories
mkdir -p data/raw data/aggregated site
```

### Running Locally

```bash
# Set environment variables
export GITHUB_TOKEN="your_github_pat"
export GITHUB_ORG="your_org_or_username"

# Collect metrics
python metrics/collect.py

# Aggregate data
python metrics/aggregate.py

# Render dashboard
python metrics/render_dashboard.py

# Serve locally
python -m http.server 8080 -d site
# Open http://localhost:8080
```

---

## 📊 DORA Performance Categories

The dashboard categorizes DORA metrics according to industry standards:

| Category | Deployment Frequency | Lead Time | MTTR | CFR |
|----------|---------------------|-----------|------|-----|
| 🏆 **Elite** | ≥8 releases/month | <24 hours | <1 hour | <5% |
| 🥇 **High** | ≥4 releases/month | <1 week | <24 hours | <15% |
| 🥈 **Medium** | ≥1 release/month | <1 month | <1 week | <30% |
| 🥉 **Low** | <1 release/month | >1 month | >1 week | >30% |

---

## 🔧 Customization

### Modify Metrics Collection

Edit `metrics/collect.py` to add or remove data points collected from the GitHub API.

### Customize Aggregation Logic

Edit `metrics/aggregate.py` to change how metrics are calculated or add new derived metrics.

### Update Dashboard Design

Edit `metrics/templates/index.html` to modify the dashboard layout, colors, or add new visualizations.

### Change Thresholds

Modify the category thresholds in `aggregate.py`:
- `calc_dora()` - DORA metric thresholds
- `calc_governance()` - Risk level thresholds

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [DORA Metrics](https://dora.dev/) - DevOps Research and Assessment
- [Chart.js](https://www.chartjs.org/) - JavaScript charting library
- [Bootstrap](https://getbootstrap.com/) - CSS framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) - Icon library
- [Jinja2](https://jinja.palletsprojects.com/) - Python templating engine

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/PJawanth/org-metrics-dashboard/issues) page
2. Create a new issue with detailed information
3. Include error logs from GitHub Actions if applicable

---

<p align="center">
  <strong>Built with ❤️ for Engineering Leaders</strong><br>
  <sub>Automated DevOps, DevSecOps, and Governance Metrics</sub>
</p>
