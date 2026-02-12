# Running Metrics Collector Locally

## Step 1: Set Up GitHub Personal Access Token

### Generate PAT (if you don't have one)
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token"
3. Name it: `metrics-dashboard`
4. Select scopes:
   - `public_repo` (for public repos)
   - `repo` (for private repos - if needed)
   - `read:org` (to list org repos)
   - `security_events` (for Dependabot/code scanning - requires GitHub Advanced Security)
5. Click "Generate token"
6. **Copy the token** (you'll only see it once)

### Set Environment Variables (PowerShell)
```powershell
$env:GITHUB_TOKEN = "github_pat_xxxxxxxxxxxx"
$env:GITHUB_ORG = "PJawanth"  # Replace with your org name
```

Or for bash/zsh:
```bash
export GITHUB_TOKEN="github_pat_xxxxxxxxxxxx"
export GITHUB_ORG="PJawanth"
```

## Step 2: Run the Collector

```powershell
cd "e:\AI Demo\github action\Metrics\org-metrics-dashboard"
python metrics/collect.py
```

### Expected Output
```
================================================================================
  Collecting metrics from GitHub org: PJawanth
================================================================================

📊 Fetching org repos...
  ✓ Found 18 repos

📦 Collecting metrics...
  [1/18] admin-dashboard          ✓ 5.2s
  [2/18] analytics-service       ✓ 4.8s
  ...
  [18/18] web-frontend           ✓ 6.1s

📝 Writing metadata...
  ✓ Run ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  ✓ Metadata saved: data/meta/run_20260212_120000.json

✅ Collection complete!
  - Repos scanned: 18
  - Errors: 0
  - Requests: 1,234
  - Duration: 2m 15s
```

### Output Files
- **Raw metrics:** `data/raw/{repo_name}.json` (one per repo)
- **Run metadata:** `data/meta/run_{timestamp}.json`

## Step 3: Aggregate Metrics

```powershell
python metrics/aggregate.py
```

### Expected Output
```
================================================================================
  Aggregating metrics from 18 repos
================================================================================

📊 Loading raw repo data...
  ✓ Loaded: 18 repos

🔄 Aggregating metrics...
  - DORA metrics
  - Flow metrics
  - Security metrics
  - CI/CD metrics
  - Governance metrics

📝 Saving results...
  ✓ Dashboard: data/aggregated/dashboard.json
  ✓ History snapshot: data/history/2026-02-12/dashboard.json

✅ Aggregation complete!
  - Total vulns: 42 (3 critical, 8 high, 15 medium, 16 low)
  - Mean lead time: 18.5 hours
  - PR throughput: 127 merged (30d)
  - Secrets found: 0
```

### Output Files
- **Aggregated dashboard:** `data/aggregated/dashboard.json`
- **History snapshot:** `data/history/{YYYY-MM-DD}/dashboard.json`

## Step 4: Render HTML Dashboard

```powershell
python metrics/render_dashboard.py
```

### Expected Output
```
✅ Dashboard rendered: site/index.html
✅ Data exported: site/data.json
```

### View Dashboard
Open in browser:
```powershell
Invoke-Item "site/index.html"
```

## Troubleshooting

### Error: 403 Forbidden (insufficient permissions)
- Check that your PAT has required scopes
- May need GitHub Advanced Security for security alerts
- Some repos may be private/archived

### Error: 404 Not Found
- Feature not available (e.g., Dependabot not enabled)
- Repo may be archived
- Check that repo exists

### Error: Timeout
- GitHub API is slow
- Try running again or increase REQUEST_TIMEOUT

## Audit Trail

Check collection metadata:
```powershell
# List all runs
Get-ChildItem data/meta/ | Sort-Object LastWriteTime -Descending | Select-Object -First 5

# View latest run details
Get-Content data/meta/run_*.json | ConvertFrom-Json | Select-Object run_id, repos_scanned, errors_count, duration_seconds
```

Check history snapshots:
```powershell
# View trend data
Get-Content data/history/2026-02-12/dashboard.json | ConvertFrom-Json | Select-Object -ExpandProperty security
```

## Full Workflow (One-liner)

```powershell
$env:GITHUB_TOKEN = "github_pat_xxxxxxxxxxxx"; $env:GITHUB_ORG = "PJawanth"; `
cd "e:\AI Demo\github action\Metrics\org-metrics-dashboard"; `
python metrics/collect.py; `
python metrics/aggregate.py; `
python metrics/render_dashboard.py; `
Invoke-Item site/index.html
```

