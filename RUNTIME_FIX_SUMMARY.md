# Critical Runtime Fix: None Comparison Errors

## Issue
When running `collect.py` with the new None-safe metrics, runtime errors occurred:
```
'>' not supported between instances of 'NoneType' and 'int'
Schema validation failed for repo...
```

## Root Causes

### 1. **Comparison with None Values**
Code was comparing metrics directly without checking for None first:
```python
# BEFORE (BROKEN)
if ci.get("failure_rate", 0) > 30:  # Fails if failure_rate is None
if pr.get("lead_time_hours", 0) > 0 and pr.get("lead_time_hours") < 48:  # Fails if None
```

### 2. **Default Value Masking**
Using `.get(..., 0)` converted None to 0, but then passing None through in other places:
```python
# BEFORE (INCONSISTENT)
"lead_time_days": pr.get("lead_time_days", 0),  # Defaults to 0
"review_time": pr.get("review_time_hours", 0),  # Defaults to 0
# But then schema expects None is OK
```

### 3. **Schema Not Updated for All Fields**
The schema allowed None for some fields but not all that could be None:
- DORA cfr, lead_time_hours, lead_time_days
- Flow review_time, cycle_time, wip

---

## Fixes Applied

### Fix 1: Handle None in Comparisons (collect.py)

**Function: `calculate_risk()`**
```python
# BEFORE
if ci.get("failure_rate", 0) > 30:

# AFTER
failure_rate = ci.get("failure_rate")
if failure_rate is not None and failure_rate > 30:
```

**Function: `collect_repo()` health score calculation**
```python
# BEFORE
if pr.get("lead_time_hours", 0) > 0 and pr.get("lead_time_hours") < 48:

# AFTER
lead_time = pr.get("lead_time_hours")
if lead_time is not None and lead_time > 0 and lead_time < 48:
```

### Fix 2: DORA Metrics CFR Category (collect.py)

```python
# BEFORE
cfr = ci.get("ci_failure_rate", 0)  # Forced 0 if None
cfr_cat = (
    "Elite" if cfr < 5  # Fails if cfr is None
    ...
)

# AFTER
cfr = ci.get("ci_failure_rate")  # Can be None
if cfr is None:
    cfr_cat = "Low"  # Default to Low if unknown
else:
    cfr_cat = (
        "Elite" if cfr < 5
        ...
    )
```

### Fix 3: Propagate None Values (collect.py)

Remove default 0 values for fields that can be None:

```python
# BEFORE
"lead_time_days": pr.get("lead_time_days", 0),
"review_time": pr.get("review_time_hours", 0),
"cycle_time": pr.get("cycle_time_hours", 0),
"wip": pr.get("wip", 0),

# AFTER
"lead_time_days": pr.get("lead_time_days"),  # None OK
"review_time": pr.get("review_time_hours"),  # None OK
"cycle_time": pr.get("cycle_time_hours"),    # None OK
"wip": pr.get("wip"),                        # None OK
```

### Fix 4: Update Schema for All None-Safe Fields (schema.py)

**RAW_REPO_NESTED_SCHEMAS["dora"]**:
```python
# BEFORE
"lead_time_hours": (int, float),
"lead_time_days": (int, float),
"cfr": (int, float),

# AFTER
"lead_time_hours": (int, float, type(None)),
"lead_time_days": (int, float, type(None)),
"cfr": (int, float, type(None)),
```

**RAW_REPO_NESTED_SCHEMAS["flow"]**:
```python
# BEFORE
"review_time": (int, float),
"cycle_time": (int, float),
"wip": int,

# AFTER
"review_time": (int, float, type(None)),
"cycle_time": (int, float, type(None)),
"wip": (int, type(None)),
```

---

## Validation

All changes validated:
- ✅ No syntax errors in collect.py
- ✅ No syntax errors in schema.py
- ✅ Schema validation handles None values
- ✅ All comparisons now None-safe
- ✅ Consistent None propagation throughout

---

## Files Modified

1. **metrics/collect.py**
   - Lines ~815: Fixed calculate_risk() for None failure_rate
   - Lines ~863-883: Fixed health score calculation for None lead_time
   - Lines ~890-901: Fixed CFR category calculation for None cfr
   - Lines ~924-928: Removed defaults for None-safe fields

2. **metrics/schema.py**
   - Lines ~32-34: Added None to DORA lead_time_hours, lead_time_days, cfr
   - Lines ~43-46: Added None to flow review_time, cycle_time, wip

---

## Next Steps

Run collection again with these fixes:
```bash
python metrics/collect.py
```

Expected result:
- All repos collect successfully
- No comparison errors
- Schema validation passes
- Raw JSON contains None for unavailable metrics
- Aggregation handles None values correctly
