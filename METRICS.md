# Metrics Definitions and Data Sources

This document defines all metrics collected and computed by the org-metrics-dashboard engine.

---

## DORA Metrics

### Deployment Frequency

**Definition:** Number of releases deployed to production per month.

**Source:** GitHub Releases API
- Endpoint: `GET /repos/{owner}/{repo}/releases`
- Fields: `published_at` (filter: last 90 days)

**Calculation:** 
- Count releases published in last 90 days
- Divide by 3 to get per-month average
- Round to 1 decimal place

**Categories:**
- Elite: ≥ 8 releases/month
- High: ≥ 4 releases/month
- Medium: ≥ 1 release/month
- Low: < 1 release/month

**Window:** 90 days

**Known Limitations:**
- Does not distinguish pre-releases or draft releases
- Requires release creation; repos without explicit releases show 0
- Only counts releases tagged via GitHub Releases API

---

### Lead Time for Changes

**Definition:** Time from commit to code landing in production (merged PR).

**Source:** GitHub Pull Requests API
- Endpoint: `GET /repos/{owner}/{repo}/pulls?state=all`
- Fields: `created_at`, `merged_at` (filter: merged in last 30 days)

**Calculation:**
- For each merged PR in last 30 days: (merged_at - created_at)
- Compute mean, round to 1 decimal place
- Convert to both hours and days

**Categories:**
- Elite: < 24 hours
- High: < 1 week (168 hours)
- Medium: < 1 month (720 hours)
- Low: ≥ 1 month

**Window:** 30 days (for merged PRs)

**Known Limitations:**
- Does not account for draft/WIP time before PR creation
- Pagination capped at 500 items per repo; truncation flag included
- Draft PRs may have long creation-to-merge times if drafted weeks before submission

---

### Mean Time to Recovery (MTTR) - Issues

**Definition:** Average time to resolve (close) an issue, measured as issue open duration.

**Source:** GitHub Issues API
- Endpoint: `GET /repos/{owner}/{repo}/issues?state=all`
- Fields: `created_at`, `closed_at` (filter: closed in last 30 days)

**Calculation:**
- For each closed issue in last 30 days: (closed_at - created_at)
- Compute mean, round to 1 decimal place
- Return in hours

**Categories:**
- Elite: < 1 hour
- High: < 24 hours
- Medium: < 1 week (168 hours)
- Low: ≥ 1 week

**Window:** 30 days (for closed issues)

**Known Limitations:**
- Measures time to close any issue, not just production incidents
- Does not distinguish critical/emergency fixes from routine issues
- True DORA MTTR requires incident tracking (separate from issue tracking)

---

### CI Failure Rate (NOT DORA Change Failure Rate)

**Definition:** Percentage of GitHub Actions workflow runs that failed in the last 30 days.

**Source:** GitHub Actions API
- Endpoint: `GET /repos/{owner}/{repo}/actions/runs`
- Fields: `conclusion` (filter: runs in last 30 days)

**Calculation:**
- Count runs with `conclusion == "failure"` in last 30 days
- Count total runs in last 30 days
- Compute: (failures / total) * 100
- Round to 1 decimal place

**Categories:**
- Elite: < 5% failure rate
- High: < 15% failure rate
- Medium: < 30% failure rate
- Low: ≥ 30% failure rate

**Window:** 30 days

**Known Limitations:**
- **NOT DORA Change Failure Rate**: DORA CFR is "% of deployments causing production incidents/rollbacks/hotfixes", not CI run failures.
- This metric measures CI pipeline health, not production outcomes.
- Does not account for skipped or cancelled runs.
- Requires GitHub Actions to be enabled; no data if disabled.
- Renamed field: `ci.ci_failure_rate` (historical: was wrongly called `dora.cfr`)

**Future Work:** Implement true DORA CFR by tracking deployment outcomes (rollbacks, hotfixes) via GitHub Deployments API + incident correlation.

---

## Flow Metrics

### Review Time (Hours)

**Definition:** Average time from PR creation to first review.

**Source:** GitHub Pull Requests API + Reviews API
- Endpoints:
  - `GET /repos/{owner}/{repo}/pulls?state=all`
  - `GET /repos/{owner}/{repo}/pulls/{number}/reviews`
- Fields: `created_at` (PR), `submitted_at` (first review)

**Calculation:**
- For each PR in last 30 days: (first_review.submitted_at - PR.created_at)
- Sample up to 10 PRs per repo (API limit)
- Compute mean, round to 1 decimal place
- Return in hours

**Window:** 30 days

**Known Limitations:**
- Only samples 10 PRs due to API rate limits
- Does not reflect typical review latency for older/merged PRs

---

### Cycle Time (Hours)

**Definition:** Total time from PR creation to merge.

**Source:** GitHub Pull Requests API
- Endpoint: `GET /repos/{owner}/{repo}/pulls?state=all`
- Fields: `created_at`, `merged_at`

**Calculation:**
- For each merged PR in last 30 days: (merged_at - created_at)
- Compute mean, round to 1 decimal place
- Return in hours

**Window:** 30 days

---

### Work in Progress (WIP)

**Definition:** Number of open (unmerged) pull requests.

**Source:** GitHub Pull Requests API
- Endpoint: `GET /repos/{owner}/{repo}/pulls?state=open`

**Calculation:** Count of open PRs at collection time.

**Known Limitations:**
- Snapshot at collection time; does not reflect intra-day changes
- Includes draft PRs

---

### Throughput

**Definition:** Number of PRs merged in the last 30 days.

**Source:** GitHub Pull Requests API
- Endpoint: `GET /repos/{owner}/{repo}/pulls?state=all`
- Fields: `merged_at` (filter: last 30 days)

**Calculation:** Count of PRs with `merged_at > now() - 30 days`.

**Window:** 30 days

---

## Security Metrics

### Vulnerability Counts (Critical/High/Medium/Low)

**Definition:** Open security alerts from Dependabot, categorized by severity.

**Source:** GitHub Dependabot Alerts API
- Endpoint: `GET /repos/{owner}/{repo}/dependabot/alerts?state=open`
- Fields: `security_advisory.severity`

**Calculation:** Count alerts by severity level.

**Severity Mapping:**
- "critical" → critical_vulns
- "high" → high_vulns
- "medium" → medium_vulns
- "low" → low_vulns

**Known Limitations:**
- Requires "Dependency Alerts" permission (403 if not granted)
- Only counts **open** alerts; fixed/dismissed alerts not counted
- Not all package managers/ecosystems have severity data
- Endpoint may be unavailable on public repos without GitHub Advanced Security

**Data Availability Flag:** `security.available_dependabot` (boolean)

---

### Vulnerability Trend

**Definition:** Change in total vulnerability count compared to previous aggregation snapshot.

**Source:** Time-series history snapshots
- Location: `data/history/{YYYY-MM-DD}/dashboard.json`

**Calculation:**
- Load previous snapshot (most recent prior to current run)
- Compute delta: current.total_vulns - previous.total_vulns
- Trend:
  - delta < 0 → "Improving"
  - delta = 0 → "Stable"
  - delta > 0 → "Worsening"
- If no previous snapshot exists: trend = null

**Known Limitations:**
- Requires history snapshots; first run produces trend = null
- Only compares most recent two snapshots; does not smooth outliers
- Point-in-time comparison; does not account for suppressed/dismissed alerts

---

### Security MTTR (Hours)

**Definition:** Average time to resolve (dismiss/fix) a security alert.

**Source:** GitHub Security Alerts APIs
- Dependabot Alerts: `GET /repos/{owner}/{repo}/dependabot/alerts?state=all`
  - Fields: `created_at`, `updated_at` (when state transitions to fixed/dismissed)
- Code Scanning: `GET /repos/{owner}/{repo}/code-scanning/alerts?state=all`
  - Fields: `created_at`, (closed_at if available via GraphQL)

**Calculation:**
- For each resolved alert in last 30 days: (resolved_at - created_at)
- Compute mean across all resolved alerts
- Round to 1 decimal place
- Return in hours
- If no alerts resolved in window: security_mttr = null

**Known Limitations:**
- Requires state=all to see dismissed/fixed alerts (higher API cost)
- `updated_at` may not correspond to actual resolution time
- Dependabot alerts use `updated_at` as proxy for resolution time
- Code scanning endpoint may not return closed_at; use GraphQL for reliable data
- Endpoints may return 403 if permissions missing

**Data Availability Flags:**
- `security.available_dependabot`
- `security.available_code_scanning`

---

### Secrets Exposed

**Definition:** Count of exposed secrets detected by GitHub Secret Scanning.

**Source:** GitHub Secret Scanning Alerts API
- Endpoint: `GET /repos/{owner}/{repo}/secret-scanning/alerts?state=open`

**Calculation:** Count of open alerts.

**Known Limitations:**
- Requires GitHub Advanced Security + Secret Scanning enabled
- Only counts **open** (not remediated) secrets
- Endpoint may not be available on public repos
- Pagination capped; truncation flag included

**Data Availability Flag:** `security.available_secret_scanning`

---

### Code Alerts

**Definition:** Count of code quality/security issues detected by Code Scanning.

**Source:** GitHub Code Scanning Alerts API
- Endpoint: `GET /repos/{owner}/{repo}/code-scanning/alerts?state=open`

**Calculation:** Count of open alerts.

**Known Limitations:**
- Requires GitHub Advanced Security + Code Scanning enabled
- Requires configured code scanning workflows (SAST)
- Only counts **open** alerts
- Pagination capped; truncation flag included

**Data Availability Flag:** `security.available_code_scanning`

---

### Dependency Alerts

**Definition:** Count of dependency updates recommended by Dependabot (includes security + non-security).

**Source:** GitHub Dependabot Alerts API
- Endpoint: `GET /repos/{owner}/{repo}/dependabot/alerts?state=open`

**Calculation:** Count of open alerts (same endpoint as vulnerabilities).

**Known Limitations:**
- Overlaps with Vulnerability metrics; includes both security and maintenance updates
- Only counts open PRs/alerts

---

### Gate Pass Rate

**Definition:** Percentage of repos that pass security gate (no critical vulns, no exposed secrets, branch protection enabled).

**Source:** Multiple
- Dependabot critical alerts: `GET /repos/{owner}/{repo}/dependabot/alerts?state=open`
- Secret scanning alerts: `GET /repos/{owner}/{repo}/secret-scanning/alerts?state=open`
- Branch protection: `GET /repos/{owner}/{repo}/branches/{branch}/protection`

**Calculation:**
- Gate Pass = (critical_vulns == 0) AND (secrets == 0) AND (branch_protection == true)
- Aggregate: (repos_passing_gate / total_active_repos) * 100

---

### SLA Compliance

**Definition:** Percentage of repositories with zero critical vulnerabilities.

**Source:** GitHub Dependabot Alerts API

**Calculation:**
- Count repos where critical_vulns == 0
- Divide by total active repos
- Compute percentage

---

## CI/CD Metrics

### CI Adoption

**Definition:** Percentage of repos with GitHub Actions workflows enabled.

**Source:** GitHub Actions API
- Endpoint: `GET /repos/{owner}/{repo}/actions/workflows`

**Calculation:** (repos_with_ci / total_active_repos) * 100

**Known Limitations:**
- Only counts repos with workflows defined
- Does not measure effectiveness or run frequency

---

### CI Success Rate

**Definition:** Percentage of GitHub Actions runs that succeeded in last 30 days.

**Source:** GitHub Actions API
- Endpoint: `GET /repos/{owner}/{repo}/actions/runs`
- Fields: `conclusion`

**Calculation:** (successful_runs / total_runs) * 100

**Window:** 30 days

---

### CI Pipeline Duration

**Definition:** Average time to complete a GitHub Actions run.

**Source:** GitHub Actions API
- Endpoint: `GET /repos/{owner}/{repo}/actions/runs`
- Fields: `created_at`, `updated_at`

**Calculation:**
- For each run: (updated_at - created_at)
- Compute mean, round to 1 decimal place
- Return in minutes
- Sample limited to 15 runs per repo

**Known Limitations:**
- Does not distinguish job duration from queue wait time
- Limited to 15 recent runs per repo

---

## Activity Metrics

### Commits (30 days)

**Definition:** Number of commits in the last 30 days.

**Source:** GitHub Commits API
- Endpoint: `GET /repos/{owner}/{repo}/commits`
- Parameters: `since: now() - 30 days`

**Calculation:** Count of commits in window.

**Window:** 30 days

---

### Contributors (30 days)

**Definition:** List of top contributors by commit count in last 30 days.

**Source:** GitHub Commits API (aggregated)

**Calculation:**
- For each commit in last 30 days, extract author login
- Group and count by login
- Sort by count descending
- Return top 5 per repo, aggregated top 20 org-wide

**Window:** 30 days

---

## Risk Scoring

### Per-Repo Risk Level

**Definition:** Qualitative risk categorization based on security posture.

**Source:** Multiple (security, activity, branch protection)

**Calculation:**
- **Critical:** critical_vulns > 0 OR secrets > 0 OR gate_pass == false
- **High:** high_vulns > 0
- **Medium:** medium_vulns > 0
- **Low:** no issues

---

### Health Score

**Definition:** Aggregate health indicator (0-100) based on repo metadata and controls.

**Source:** Computed from multiple signals
- Description presence: +10
- Not archived: +10
- CI enabled: +20
- CI success rate ≥ 80%: +10
- Branch protection: +15
- Lead time < 48h: +15
- Stale issues < 5: +10
- Recent commits (30d) > 0: +10

**Calculation:** Sum of applicable signals (max 100)

---

## Data Availability & Error Handling

### Truncation Flags

Metrics may be truncated due to pagination limits or API constraints. Each section includes:
- `truncated: bool` - Data was paginated and capped
- `available_*: bool` - Endpoint available and permission granted

### Error Tracking

Per-repo errors logged in:
```json
{
  "security": {
    "errors": [
      {"field": "dependabot_alerts", "reason": "403 Forbidden (insufficient permissions)"},
      {"field": "secret_scanning_alerts", "reason": "404 Not Found (feature not enabled)"}
    ]
  }
}
```

### Rate Limits

Captured in run metadata:
```json
{
  "rate_limit_remaining": 4800,
  "rate_limit_reset": "2026-02-12T23:45:00Z"
}
```

---

## Aggregation & Time Windows

### Org-Wide Aggregation

All metrics are aggregated across **active** repos (not archived).

- **30-day window metrics:** Average/sum of last 30 days
- **90-day window metrics:** Average/sum of last 90 days
- **Point-in-time metrics:** Snapshot at collection time

### History Snapshots

Full aggregated dashboard snapshots written to `data/history/{YYYY-MM-DD}/dashboard.json` for:
- Trend analysis
- Audit trail
- Time-series visualization

---

## Known Limitations & Future Work

### API Constraints
- GitHub rate limit: 5,000 req/hour (or 15,000 with GitHub Pro)
- Pagination caps to prevent timeout; truncation flags surface limits
- Some endpoints require GitHub Advanced Security (cost)

### Data Gaps
- True DORA Change Failure Rate requires incident/deployment tracking (not yet implemented)
- Security MTTR limited to open-close transition time; root-cause resolution time not available
- PR lead time does not account for draft/WIP phases before submission

### Roadmap
1. Implement true DORA CFR via GitHub Deployments + incident correlation
2. Add GraphQL client for efficient bulk data fetching
3. Implement exponential backoff for rate-limit recovery
4. Add custom alert thresholds & SLA definitions per org
5. Time-series trend analysis with forecasting
