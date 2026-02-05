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

## 🧮 Metrics Calculation Formulas

### DORA Metrics

#### Deployment Frequency
```
Deployment Frequency = Total Releases (90 days) / 3

Categories:
  Elite  : ≥ 8 releases/month (multiple per week)
  High   : ≥ 4 releases/month (weekly)
  Medium : ≥ 1 release/month
  Low    : < 1 release/month
```

#### Lead Time for Changes
```
Lead Time = Average(PR Merge Time) for all merged PRs in 30 days

Where: PR Merge Time = PR Merged At - PR Created At (in hours)

Categories:
  Elite  : < 24 hours (less than one day)
  High   : < 168 hours (less than one week)
  Medium : < 720 hours (less than one month)
  Low    : ≥ 720 hours (one month or more)
```

#### Mean Time to Recovery (MTTR)
```
MTTR = Average(Issue Close Time) for issues labeled "bug" or "incident"

Where: Issue Close Time = Issue Closed At - Issue Created At (in hours)

Categories:
  Elite  : < 1 hour
  High   : < 24 hours (less than one day)
  Medium : < 168 hours (less than one week)
  Low    : ≥ 168 hours (one week or more)
```

#### Change Failure Rate (CFR)
```
CFR = (Failed Deployments / Total Deployments) × 100

Estimation: (Bug Issues Created in 30 days / Total Releases) × 100

Categories:
  Elite  : < 5%
  High   : < 15%
  Medium : < 30%
  Low    : ≥ 30%
```

#### Overall DORA Score
```
Score Mapping: Elite=4, High=3, Medium=2, Low=1

Overall Score = (DF_score + LT_score + MTTR_score + CFR_score) / 4

Final Category:
  Elite  : Score ≥ 3.5
  High   : Score ≥ 2.5
  Medium : Score ≥ 1.5
  Low    : Score < 1.5
```

### Flow Metrics

#### PR Review Time
```
PR Review Time = Average Merge Time × 0.6

(Estimates that review takes ~60% of the total merge time)
```

#### PR Cycle Time
```
PR Cycle Time = Average(Merged At - Created At) for all merged PRs
```

#### Work in Progress (WIP)
```
WIP = Count of Open Pull Requests
```

#### Throughput
```
Throughput = Count of PRs Merged in Last 30 Days
```

### CI/CD Metrics

#### CI Adoption Rate
```
CI Adoption = (Repos with CI/CD Workflows / Total Active Repos) × 100
```

#### CI Success Rate
```
CI Success Rate = (Successful Workflow Runs / Total Workflow Runs) × 100
```

#### CI Failure Rate
```
CI Failure Rate = 100 - CI Success Rate
```

#### Pipeline Duration
```
Pipeline Duration = Workflow Count × 5 minutes (estimated)
```

### DevSecOps Metrics

#### Vulnerability Distribution
```
Critical Vulns = Total Vulnerabilities × 0.10 (10%)
High Vulns     = Total Vulnerabilities × 0.20 (20%)
Medium Vulns   = Total Vulnerabilities × 0.40 (40%)
Low Vulns      = Total Vulnerabilities × 0.30 (30%)
```

#### Vulnerability Trend
```
Trend Categories:
  Improving : Total Vulns < 10
  Stable    : Total Vulns < 20
  Worsening : Total Vulns ≥ 20
```

#### SLA Compliance
```
SLA Compliance = (Repos with 0 Critical Vulns / Total Active Repos) × 100
```

#### Security Gate Pass Rate
```
Gate Pass Rate = (Repos with Security Score ≥ 50 / Total Active Repos) × 100
```

#### Security Adoption Rates
```
Branch Protection % = (Repos with Branch Protection / Total Repos) × 100
Dependabot %        = (Repos with Dependabot Enabled / Total Repos) × 100
Secret Scanning %   = (Repos with Secret Scanning / Total Repos) × 100
Code Scanning %     = (Repos with Code Scanning / Total Repos) × 100
Security Policy %   = (Repos with SECURITY.md / Total Repos) × 100
License Compliance %= (Repos with License File / Total Repos) × 100
```

### Governance Metrics

#### Risk Level Classification
```
Per Repository:
  Critical : Vulnerabilities > 5 OR Security Score < 30
  High     : Vulnerabilities > 2 OR Security Score < 50
  Medium   : Vulnerabilities > 0 OR Security Score < 70
  Low      : Vulnerabilities = 0 AND Security Score ≥ 70
```

#### Activity Status
```
Based on Last Updated Date:
  Active   : Updated within 30 days
  Stale    : Updated 30-180 days ago
  Inactive : Not updated in 180+ days
  Archived : Repository is archived
```

#### Health Score (0-100)
```
Factors considered:
  + Has README
  + Has License
  + Has Description
  + Has Topics/Tags
  + Recent Activity (commits in 30 days)
  + Has CI/CD
  + Has Branch Protection
  + Low Issue Count
```

#### Security Score (0-100)
```
Factors considered:
  + Branch Protection Enabled (+20)
  + Dependabot Enabled (+20)
  + Secret Scanning Enabled (+15)
  + Code Scanning Enabled (+15)
  + Has Security Policy (+10)
  + Has License (+10)
  + No Vulnerabilities (+10)
```

#### Scan Coverage
```
Scan Coverage = (Non-Archived Repos / Total Repos) × 100
```

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
| `GH_ORG_NAME` | Organization or username to scan | `xxxxxxxx` |

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
