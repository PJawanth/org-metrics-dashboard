# 📊 Organization Metrics Dashboard

> **Executive-Level Visibility into Engineering Performance**

[![Dashboard](https://img.shields.io/badge/Dashboard-Live-success?style=for-the-badge&logo=github)](https://pjawanth.github.io/org-metrics-dashboard/)
[![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?style=for-the-badge&logo=github-actions)](https://github.com/PJawanth/org-metrics-dashboard/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-26%2F26-brightgreen?style=for-the-badge)](tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

A **production-grade metrics dashboard** that automatically collects real data from GitHub APIs, aggregates organization-wide metrics, and visualizes engineering performance through interactive dashboards. Deployed via GitHub Pages with zero manual intervention.

---

## 🎯 What This Does

Track and visualize **DORA metrics**, **DevSecOps posture**, and **governance compliance** across your entire GitHub organization:

| 🚀 DevOps | 🔒 Security | 📋 Governance |
|-----------|-------------|---------------|
| Deployment Frequency | Vulnerabilities | Risk Ranking |
| Lead Time for Changes | Security MTTR | Compliance |
| Mean Time to Recovery | Adoption Rates | Repo Inventory |
| Change Failure Rate | SLA Compliance | Health Scores |
| PR Cycle Time | Branch Protection | Activity Status |

---

## 🏗️ How It Works

Three-stage automated pipeline runs daily:

```
┌─────────────────┐      ┌──────────────┐      ┌──────────────┐
│   GitHub API    │ ───→ │   COLLECT    │ ───→ │   data/raw   │
│  19 Repositories│      │  Real Data   │      │  Per-Repo    │
└─────────────────┘      └──────────────┘      └──────────────┘
                               │
                               │ data/raw/*.json
                               ▼
                         ┌──────────────┐      ┌──────────────┐
                         │ AGGREGATE    │ ───→ │  dashboard   │
                         │ Org Metrics  │      │  Aggregated  │
                         └──────────────┘      └──────────────┘
                               │
                               │ data/aggregated/dashboard.json
                               ▼
                         ┌──────────────┐      ┌──────────────┐
                         │   RENDER     │ ───→ │  site/       │
                         │  HTML + Charts      │  index.html  │
                         └──────────────┘      └──────────────┘
                               │
                               │ GitHub Pages
                               ▼
                         🌐 Live Dashboard
```

**Key Characteristics:**
- ✅ **Real Data Only** - All metrics from actual GitHub API calls
- ✅ **100% Automated** - Daily runs via GitHub Actions  
- ✅ **Production-Grade** - Comprehensive error handling & validation
- ✅ **Interactive Dashboard** - 5 tabs with charts & filterable tables
- ✅ **Zero Manual Work** - Fully self-service after setup

---

## 📈 Dashboard Overview

### 5 Interactive Tabs

| Tab | Purpose | Key Sections |
|-----|---------|--------------|
| **📊 Overview** | At-a-glance KPIs | DORA cards, risk summary, charts, top contributors |
| **🚀 DevOps** | DORA + Flow metrics | Performance breakdown, per-repo table |
| **🔒 DevSecOps** | Security posture | Vulnerabilities, adoption, SLA compliance |
| **📋 Governance** | Compliance & audit | Risk distribution, repo inventory |
| **📁 Repository Details** | All metrics | Searchable comprehensive table |

### Dashboard Features
- 📊 Real-time bar charts for repository metrics
- 🍩 Doughnut charts for language and vulnerability distribution
- 📈 Radar charts for security adoption progress
- 🎯 DORA performance cards (Elite/High/Medium/Low ratings)
- 🔍 Searchable repository table with sorting
- 📱 Fully responsive design
- ♿ Accessibility optimized

---

## 📊 Metrics Reference

### DORA Metrics (DevOps Performance)

| Metric | Description | Elite | High | Medium | Low |
|--------|-------------|-------|------|--------|-----|
| **Deployment Frequency** | Releases per month | ≥8 | ≥4 | ≥1 | <1 |
| **Lead Time** | Commit to production | <24h | <1wk | <1mo | >1mo |
| **MTTR** | Time to recovery | <1h | <24h | <1wk | >1wk |
| **CFR** | Change failure rate | <5% | <15% | <30% | >30% |

### Flow Metrics (Development Efficiency)

| Metric | Description |
|--------|-------------|
| **PR Cycle Time** | Average time from open to merge (hours) |
| **PR Review Time** | Average time to first review (hours) |
| **Work in Progress** | Open pull requests count |
| **Throughput** | PRs merged in 30 days |
| **CI Success Rate** | % of successful builds |
| **Pipeline Duration** | Average CI/CD runtime (minutes) |

### DevSecOps Metrics (Security Posture)

| Metric | Description |
|--------|-------------|
| **Critical Vulnerabilities** | Open critical security alerts |
| **High Vulnerabilities** | Open high-severity alerts |
| **Medium Vulnerabilities** | Open medium-severity alerts |
| **Low Vulnerabilities** | Open low-severity alerts |
| **Security MTTR** | Time to fix security issues (hours) |
| **Branch Protection** | % repos with branch protection |
| **Dependabot Adoption** | % repos with Dependabot enabled |
| **Secret Scanning** | % repos with secret scanning |
| **Code Scanning** | % repos with code scanning |
| **Security Policy** | % repos with SECURITY.md |

### Governance Metrics (Compliance & Audit)

| Metric | Description |
|--------|-------------|
| **Risk Ranking** | Repos categorized: Critical/High/Medium/Low |
| **Health Score** | Overall repo health (0-100) |
| **Security Score** | Security posture (0-100) |
| **Scan Coverage** | % non-archived repos scanned |
| **Activity Status** | Active/Stale/Inactive/Archived |
| **License Compliance** | % repos with valid license |

---

## 🧮 Calculation Formulas

#### Deployment Frequency
```
= Total releases in 90 days / 3
```

#### Lead Time for Changes
```
= Average time from PR created to merged (last 30 days)
```

#### Mean Time to Recovery (MTTR)
```
= Average time to fix/dismiss security alerts (last 30 days)
```

#### Change Failure Rate (CFR)
```
= (Bug issues created / Total releases) × 100
```

#### Overall DORA Score
```
= (Deployment_Score + LeadTime_Score + MTTR_Score + CFR_Score) / 4
Elite (≥3.5), High (≥2.5), Medium (≥1.5), Low (<1.5)
```

#### PR Cycle Time
```
= Average(merged_at - created_at) for merged PRs in 30 days
```

#### PR Review Time
```
= Average time to first review on PRs in 30 days
```

#### CI Success Rate
```
= (Successful workflow runs / Total runs) × 100
```

#### Risk Level Classification
```
Critical : Vulnerabilities > 5 OR Security Score < 30
High     : Vulnerabilities > 2 OR Security Score < 50
Medium   : Vulnerabilities > 0 OR Security Score < 70
Low      : Vulnerabilities = 0 AND Score ≥ 70
```

#### Security Score (0-100)
```
Branch Protection (+20) + Dependabot (+20) + Secret Scanning (+15)
+ Code Scanning (+15) + Security Policy (+10) + License (+10)
+ No Vulnerabilities (+10)
```

#### Activity Status
```
Active   : Updated within 30 days
Stale    : Updated 30-180 days ago
Inactive : Not updated in 180+ days
Archived : Repository archived
```

---

## 📁 Project Structure

```
org-metrics-dashboard/
├── metrics/
│   ├── collect.py              # GitHub API data collection
│   ├── aggregate.py            # Org-wide metric aggregation
│   ├── render_dashboard.py     # HTML dashboard generation
│   ├── schema.py               # Data validation schemas
│   └── templates/
│       └── index.html          # Dashboard template
│
├── data/                       # Generated data (gitignored)
│   ├── raw/                    # Per-repo JSON snapshots
│   ├── aggregated/             # Org-wide dashboard.json
│   └── history/                # Daily snapshots
│
├── site/                       # Generated website (gitignored)
│   ├── index.html              # Final dashboard
│   └── data.json               # Debugging data
│
├── tests/
│   └── test_metrics.py         # Unit tests (26 tests)
│
├── .github/workflows/
│   └── metrics-dashboard.yml   # Automated workflow
│
└── requirements.txt            # Python dependencies
```

---

## ⚡ Quick Start (5 Minutes)

### 1. Fork This Repository

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/org-metrics-dashboard.git
cd org-metrics-dashboard
```

### 2. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions**

**Add Secret:**
| Name | Value |
|------|-------|
| `ORG_READ_TOKEN` | GitHub PAT with `repo` + `read:org` scopes |

**Add Variable:**
| Name | Value |
|------|-------|
| `GH_ORG_NAME` | Your org/username to scan |

**How to create a PAT:**
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` + `read:org` scopes
3. Copy and paste into secret

### 3. Enable GitHub Pages

**Settings → Pages:**
- Source: GitHub Actions
- Save

### 4. Run the Workflow

**Actions → Update Metrics Dashboard → Run workflow**

**Done!** Dashboard will be live at `https://YOUR_USERNAME.github.io/org-metrics-dashboard`

---

## 🚀 Local Development

### Prerequisites
```bash
Python 3.11+
```

### Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/org-metrics-dashboard.git
cd org-metrics-dashboard

# Install dependencies
pip install -r requirements.txt

# Create data directories
mkdir -p data/{raw,aggregated,history} site
```

### Run Locally
```bash
# Set environment variables
export GITHUB_TOKEN="your_github_pat"
export GITHUB_ORG="your_org_or_username"

# Collect metrics from GitHub API
python metrics/collect.py

# Aggregate to org-level dashboard
python metrics/aggregate.py

# Generate HTML dashboard
python metrics/render_dashboard.py

# Serve locally
python -m http.server 8080 -d site

# Open http://localhost:8080
```

### Run Tests
```bash
python -m pytest tests/ -v
# Expected: 26/26 tests passing ✓
```

---

## 📊 Understanding DORA Categories

The dashboard rates your organization across the **DORA Framework**:

| Category | DF | Lead Time | MTTR | CFR |
|:--------:|:--:|:---------:|:----:|:---:|
| 🏆 **Elite** | ≥8/mo | <24h | <1h | <5% |
| 🥇 **High** | ≥4/mo | <1wk | <24h | <15% |
| 🥈 **Medium** | ≥1/mo | <1mo | <1wk | <30% |
| 🥉 **Low** | <1/mo | >1mo | >1wk | >30% |

**Your Score:**
```
Overall = (Deployment_Score + LeadTime_Score + MTTR_Score + CFR_Score) / 4

Elite  : ≥3.5  |  High  : ≥2.5  |  Medium  : ≥1.5  |  Low  : <1.5
```

---

## 🔧 Customization

### Modify Data Collection
Edit **`metrics/collect.py`** to add/remove metrics or API endpoints.

### Adjust Calculation Logic
Edit **`metrics/aggregate.py`** to change metric calculations or category thresholds.

### Customize Dashboard Layout
Edit **`metrics/templates/index.html`** to modify design, colors, or add new charts.

### Update Category Thresholds
In `aggregate.py`:
- `calc_dora()` - DORA metric thresholds
- `calc_security()` - DevSecOps thresholds
- `calc_governance()` - Risk level thresholds

---

## ⏰ Automated Workflow

The dashboard updates automatically:

| Trigger | When |
|---------|------|
| **Schedule** | Daily at midnight UTC |
| **Manual** | Click "Run workflow" in Actions tab |
| **Push** | Any changes to `metrics/` or workflow files |

**Workflow Steps:**
1. Collects real data from GitHub APIs
2. Aggregates org-wide metrics
3. Generates interactive HTML dashboard
4. Deploys to GitHub Pages
5. Runs 26 automated tests

---

## 🤝 Contributing

Help improve the dashboard! 

```bash
# 1. Fork repository
# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and commit
git commit -m 'Add amazing feature'

# 4. Push and open PR
git push origin feature/amazing-feature
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---

## 🙏 Credits

- [DORA Metrics](https://dora.dev/) - DevOps Research and Assessment
- [Chart.js](https://www.chartjs.org/) - JavaScript charting library
- [Bootstrap](https://getbootstrap.com/) - CSS framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) - Icon library
- [Jinja2](https://jinja.palletsprojects.com/) - Python templating engine

---

## 🆘 Support & Issues

**Encountering problems?**

1. Check existing [Issues](https://github.com/PJawanth/org-metrics-dashboard/issues)
2. Review GitHub Actions workflow logs
3. Create a new issue with:
   - Error message or screenshot
   - Steps to reproduce
   - Your setup (org size, repo count)

---

<div align="center">

### 🌟 **Built with ❤️ for Engineering Leaders**

**Automated DevOps, DevSecOps, and Governance Metrics**

[View Live Dashboard](https://pjawanth.github.io/org-metrics-dashboard/) • [Report Issue](https://github.com/PJawanth/org-metrics-dashboard/issues) • [Star Repository](https://github.com/PJawanth/org-metrics-dashboard)

</div>
