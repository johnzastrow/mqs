# Bug Fix: Metadata Save Failure (v0.3.4)

## Issue

**Severity**: CRITICAL
**Status**: Fixed ✅

Metadata could not be saved to cache. Save button appeared to work but nothing persisted to database.

## Error Messages

```
2025-10-06T14:45:56 CRITICAL Error saving metadata to cache:
    table metadata_cache has no column named created_datetime

2025-10-06T14:42:43 WARNING Error getting recommendations:
    no such column: directory_path
```

## Root Cause

### Problem 1: metadata_cache Column Name Mismatch

The `save_metadata_to_cache()` method was using column names that **don't exist** in the schema:

| Used (Incorrect) | Actual Schema | Impact |
|-----------------|---------------|---------|
| `created_datetime` | `created_date` | Save failed - column doesn't exist |
| `modified_datetime` | `last_edited_date` | Save failed - column doesn't exist |
| (missing) | `layer_name` | Schema requires NOT NULL, wasn't provided |

**Schema Definition** (`db/schema.py:142-153`):
```sql
CREATE TABLE IF NOT EXISTS metadata_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_path TEXT NOT NULL UNIQUE,
    layer_name TEXT NOT NULL,              -- REQUIRED but missing!
    file_type TEXT,
    metadata_json TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- NOT created_datetime
    last_edited_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- NOT modified_datetime
    last_written_date TIMESTAMP,
    target_location TEXT,
    in_sync INTEGER DEFAULT 1,
    UNIQUE(layer_path)
);
```

**Save Method** (`db/manager.py:673-689` - BEFORE FIX):
```python
cursor.execute("""
    INSERT OR REPLACE INTO metadata_cache (
        layer_path,
        metadata_json,
        created_datetime,    -- ❌ WRONG! Column doesn't exist
        modified_datetime,   -- ❌ WRONG! Column doesn't exist
        in_sync
    ) VALUES (?, ?,
        COALESCE((SELECT created_datetime FROM metadata_cache WHERE layer_path = ?), datetime('now')),
        datetime('now'),
        ?
    )
""", (layer_path, metadata_json, layer_path, 1 if in_sync else 0))
```

### Problem 2: get_priority_recommendations Column Names

The recommendations query used incorrect inventory column names:

| Used (Incorrect) | Actual Schema | Impact |
|-----------------|---------------|---------|
| `directory_path` | `parent_directory` | Recommendations failed - column doesn't exist |
| `file_format` | `format` | Recommendations failed - column doesn't exist |

## Fix Applied

### 1. Fixed save_metadata_to_cache() (lines 673-689)

```python
cursor.execute("""
    INSERT OR REPLACE INTO metadata_cache (
        layer_path,
        layer_name,           -- ✅ ADDED: Required by schema
        metadata_json,
        created_date,         -- ✅ FIXED: Correct column name
        last_edited_date,     -- ✅ FIXED: Correct column name
        in_sync
    ) VALUES (?, ?, ?,
        COALESCE((SELECT created_date FROM metadata_cache WHERE layer_path = ?), datetime('now')),
        datetime('now'),
        ?
    )
""", (layer_path, metadata.get('title', 'Unknown'), metadata_json, layer_path, 1 if in_sync else 0))
```

**Changes**:
- ✅ Added `layer_name` column (uses metadata title or 'Unknown')
- ✅ Changed `created_datetime` → `created_date`
- ✅ Changed `modified_datetime` → `last_edited_date`
- ✅ Fixed COALESCE to use `created_date` instead of `created_datetime`

### 2. Fixed get_priority_recommendations() (lines 619-639)

```python
cursor.execute("""
    SELECT
        parent_directory,    -- ✅ FIXED: Correct column name
        format,              -- ✅ FIXED: Correct column name
        COUNT(*) as count
    FROM geospatial_inventory
    WHERE retired_datetime IS NULL
      AND (metadata_status IS NULL OR metadata_status = 'none')
    GROUP BY parent_directory, format
    ORDER BY count DESC
    LIMIT ?
""", (limit,))

results = []
for row in cursor.fetchall():
    results.append({
        'directory': row['parent_directory'] or 'Root',
        'file_format': row['format'] or 'Unknown',
        'count': row['count'],
        'recommendation': f"{row['count']} {row['format'] or 'files'} in {row['parent_directory'] or 'Root'} need metadata"
    })
```

## Testing

### Before Fix
- ❌ Click Save → Error in log, no data saved
- ❌ Recommendations widget empty with warning in log
- ❌ Dashboard statistics never update after "saves"

### After Fix
- ✅ Click Save → Success message, data persists
- ✅ Recommendations widget displays top priority items
- ✅ Dashboard statistics update correctly after save
- ✅ Reload plugin → metadata still present (persisted)

## How This Bug Occurred

This appears to be a mismatch between:
1. **Schema definition** (`db/schema.py`) - Uses `created_date`, `last_edited_date`
2. **Database methods** (`db/manager.py`) - Was using `created_datetime`, `modified_datetime`

The schema was likely created first, then the save method was written later without checking the actual schema column names.

## Related Issues Fixed in v0.3.2

This is the **second** round of column name fixes. In v0.3.2, we fixed:
- Statistics queries (directory_path → parent_directory, etc.)

Both issues stem from the same root cause: **not verifying column names against actual schema**.

## Prevention

To prevent similar issues in the future:

1. **Always check schema** before writing queries
2. **Use constants** for column names to avoid typos
3. **Test all database operations** with actual data
4. **Log query errors** prominently (was only WARNING, should be CRITICAL)
5. **Schema documentation** - maintain a reference table of all column names

## Files Modified

- `Plugins/metadata_manager/db/manager.py`
  - Line 673-689: Fixed `save_metadata_to_cache()`
  - Line 619-639: Fixed `get_priority_recommendations()`
- `Plugins/metadata_manager/metadata.txt` - Version 0.3.4
- `Plugins/metadata_manager/MetadataManager.py` - Version 0.3.4
- `docs/metadata_manager/CHANGELOG.md` - v0.3.4 entry

---

**Version**: 0.3.4
**Date**: 2025-10-06
**Severity**: CRITICAL (prevented all saves)
**Status**: Fixed ✅
