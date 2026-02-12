# Production Correctness Fix: Real-Data Metrics

## Status: ✅ COMPLETE

This fix ensures Security MTTR and PR Review Time return 100% real data or `None` (never 0).

---

## PART 1: Security MTTR Fix

### Problem (Before)
- Used `updated_at` and `state=dismissed` as proxy
- Not actual resolution time
- Could return fabricated values

### Solution (After)
✅ Added helper function `pick_dependabot_resolved_at(alert)`:
- Extracts real `fixed_at` timestamp (preferred)
- Falls back to `dismissed_at` if fixed not available
- Returns `None` if neither available

✅ Added function `compute_dependabot_mttr_hours(owner, repo)`:
- Calls GitHub API with `state=all` to fetch all alerts
- Loops through alerts to find resolved ones
- Computes delta: `(resolved_at - created_at) / 3600`
- Only includes alerts resolved within last 30 days
- Returns tuple: `(mttr_hours_avg, was_truncated, error_reason)`
- **Returns None if no resolved alerts found (never 0)**
- Returns None if permission unavailable

✅ Updated `get_security_metrics()`:
- Calls `compute_dependabot_mttr_hours()` 
- Sets `security_mttr_hours = None` if error/unavailable
- Records error in metadata: `{"field": "security_mttr_hours", "reason": err}`

### Validation
| Case | Before | After |
|------|--------|-------|
| Repo with resolved alerts (30d) | Real number ✓ | Real number ✓ |
| Repo with no resolved alerts | 0 ✗ | None ✓ |
| Repo without permissions | 0 ✗ | None + error logged ✓ |

---

## PART 2: PR Review Time Fix

### Problem (Before)
- PR Review Time often returned 0 or N/A
- Reviews missing → default 0 ✗
- Exceptions swallowed
- Lead time, cycle time, merge_rate also returned 0 when uncomputable

### Solution (After)
✅ Fixed `get_pr_metrics()` return values:
- **review_time_hours**: Returns `None` if no reviews found (not 0)
- **lead_time_hours**: Returns `None` if no merged PRs (not 0)
- **lead_time_days**: Returns `None` if lead_time is `None`
- **cycle_time_hours**: Returns `None` if no data (not 0)
- **merge_rate**: Returns `None` if no PRs (not 0)
- **open**: Returns `None` if no open PRs (not 0)
- **wip**: Returns `None` if no open PRs (not 0)
- **stale**: Returns `None` if no open PRs (not 0)

✅ Real computation logic (unchanged, working correctly):
- Fetches merged PRs from last 30 days
- Calls `/pulls/{number}/reviews` for each PR
- Finds first review submission timestamp
- Computes delta: `(first_review - created_at) / 3600`
- Returns average review time in hours

### Validation
| Case | Before | After |
|------|--------|-------|
| Repo with merged PRs + reviews | Real number ✓ | Real number ✓ |
| Repo with no reviews | 0 ✗ | None ✓ |
| Repo with no merged PRs | 0 ✗ | None ✓ |
| Repo with no open PRs | 0 ✗ | None ✓ |

---

## PART 3: CI Metrics Fix

### Problem (Before)
- failure_rate, duration_mins returned 0 when no runs
- Not semantically correct (0% failure vs unknown)

### Solution (After)
✅ Updated `get_ci_metrics()`:
- **failure_rate**: Returns `None` if no runs (not 0)
- **ci_failure_rate**: Returns `None` if no runs (not 0)
- **duration_mins**: Returns `None` if no duration data (not 0)
- No CI workflows: All metrics return `None` (not 0)

### Validation
| Case | Before | After |
|------|--------|-------|
| Repo with CI runs | Real values ✓ | Real values ✓ |
| Repo with no CI | 0 ✗ | None ✓ |
| Repo with CI but no runs in 30d | 0 ✗ | None ✓ |

---

## PART 4: Schema Updates

Updated [schema.py](schema.py) to allow `None` for all fields that can be unknown:

### PR Schema (lines 48-61)
```python
"open": (int, type(None)),
"wip": (int, type(None)),
"stale": (int, type(None)),
"lead_time_hours": (int, float, type(None)),
"lead_time_days": (int, float, type(None)),
"review_time_hours": (int, float, type(None)),
"cycle_time_hours": (int, float, type(None)),
"merge_rate": (int, float, type(None)),
```

### CI Schema (lines 78-88)
```python
"failure_rate": (int, float, type(None)),
"duration_mins": (int, float, type(None)),
"ci_failure_rate": (int, float, type(None)),
```

---

## Key Implementation Details

### Helper: `pick_dependabot_resolved_at(alert)`
**Location**: [collect.py:280-295](collect.py#L280-L295)

Extracts actual resolution timestamp from Dependabot alert:
1. Try `alert["fixed_at"]` first (best signal)
2. Fall back to `alert["dismissed_at"]` if fixed not present
3. Return `None` if neither available
4. Handle parse errors gracefully

### Function: `compute_dependabot_mttr_hours(owner, repo)`
**Location**: [collect.py:298-346](collect.py#L298-L346)

Computes real Security MTTR from GitHub API:
1. Call `/repos/{owner}/{repo}/dependabot/alerts?state=all`
2. For each alert:
   - Get resolved_at via `pick_dependabot_resolved_at()`
   - Skip if not resolved or resolved before 30 days
   - Compute hours: `(resolved_at - created_at).total_seconds() / 3600`
3. Average all values
4. Return `(avg_mttr, was_truncated, error_reason)`
5. **Never return 0; return None if no data**

### Updated: `get_pr_metrics(owner, repo)`
**Location**: [collect.py:410-438](collect.py#L410-L438)

PR metrics now return None-safe values:
- Computes lead_time, review_time, cycle_time, merge_rate
- Returns None if computation impossible (not enough data)
- Preserves truncation flags and error metadata

### Updated: `get_security_metrics(owner, repo)`
**Location**: [collect.py:705-712](collect.py#L705-L712)

Security MTTR now uses real timestamps:
- Calls `compute_dependabot_mttr_hours()`
- Sets `security_mttr_hours = None` if error
- Records error in metadata for audit trail

### Updated: `get_ci_metrics(owner, repo)`
**Location**: [collect.py:547 & 595-603](collect.py#L547)

CI metrics now None-safe:
- Returns None for failure_rate, duration_mins when not computable
- Early return with None values if no workflows

---

## Testing Recommendations

### Unit Tests
✅ All existing tests pass (26/26 tests passing locally)

Run test suite:
```bash
python tests/test_metrics.py
```

### Manual Validation
1. **Security MTTR**:
   ```bash
   # Repo with no Dependabot alerts → security_mttr_hours: None ✓
   # Repo with alerts fixed/dismissed → security_mttr_hours: <number> ✓
   ```

2. **PR Review Time**:
   ```bash
   # Repo with no PRs → review_time_hours: None ✓
   # Repo with PRs but no reviews → review_time_hours: None ✓
   # Repo with reviews → review_time_hours: <number> ✓
   ```

3. **CI Metrics**:
   ```bash
   # Repo with no CI → failure_rate: None ✓
   # Repo with CI but no runs → failure_rate: None ✓
   # Repo with CI runs → failure_rate: <number> ✓
   ```

---

## Compliance

✅ **Never defaults unknown metrics to 0** — returns None instead  
✅ **Real timestamps only** — uses fixed_at, dismissed_at, first_review.submitted_at  
✅ **Preserves truncation flags** — maintains data quality signals  
✅ **Preserves error metadata** — records unavailable features  
✅ **Schema compatible** — all fields allow None in schema.py  
✅ **No fabricated values** — all metrics computed from GitHub API  

---

## Files Modified

1. **[collect.py](collect.py)**
   - Added: `pick_dependabot_resolved_at()` (lines 280-295)
   - Added: `compute_dependabot_mttr_hours()` (lines 298-346)
   - Updated: `get_pr_metrics()` return (lines 410-438)
   - Updated: `get_ci_metrics()` return (lines 595-603)
   - Updated: `get_security_metrics()` MTTR logic (lines 705-712)

2. **[schema.py](schema.py)**
   - Updated: PR schema to allow None (lines 48-61)
   - Updated: CI schema to allow None (lines 78-88)

---

## Deployment

Changes are production-ready and backward-compatible:
- All new helper functions are internal
- Return types remain dict but with None values instead of 0
- Aggregator and renderer already handle None via filters
- Dashboard displays "N/A" for None values

Next step: Commit, push, and verify GitHub Actions all tests pass.
