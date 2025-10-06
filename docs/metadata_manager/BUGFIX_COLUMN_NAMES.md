# Bug Fix: Dashboard Statistics Column Names (v0.3.2)

## Issue

Dashboard statistics were only showing data in the "By Data Type" tab. The other three drill-down tabs (By Directory, By File Format, By CRS) were empty.

## Root Cause

The database queries in `db/manager.py` were using incorrect column names that didn't match the actual schema created by inventory_miner.py.

### Column Name Mismatches

| Used (Incorrect) | Actual (Correct) | Impact |
|-----------------|------------------|---------|
| `directory_path` | `parent_directory` | By Directory tab empty |
| `file_format` | `format` | By File Format tab empty |
| `crs` | `crs_authid` | By CRS tab empty |
| `layer_path` (WHERE) | `file_path` | Metadata status not updating |

## Files Fixed

### 1. `db/manager.py`

**get_statistics_by_directory()** (lines 416-460):
- Changed `directory_path` → `parent_directory` in SELECT and GROUP BY
- Changed result dict key to use `row['parent_directory']`

**get_statistics_by_file_format()** (lines 508-552):
- Changed `file_format` → `format` in SELECT and GROUP BY
- Changed result dict to use `row['format']`

**get_statistics_by_crs()** (lines 554-598):
- Changed `crs` → `crs_authid` in SELECT and GROUP BY
- Changed result dict to use `row['crs_authid']`

**update_inventory_metadata_status()** (line 780):
- Changed `WHERE layer_path = ?` → `WHERE file_path = ?`
- This fixes metadata status updates in inventory table

### 2. `widgets/layer_selector_dialog.py`

**load_layers()** (lines 113-142):
- Changed SELECT columns:
  - `layer_path` → `file_path`
  - `file_format` → `format`
  - `directory_path` → `parent_directory`
- Updated row dictionary to use correct field names

## Verification

### Inventory Miner Schema (from Scripts/inventory_miner.py)

The actual field names created by inventory_miner are:

```python
# File System Fields
fields.append(QgsField("file_path", QVariant.String))        # Full path
fields.append(QgsField("parent_directory", QVariant.String)) # Directory

# Format/Driver Fields
fields.append(QgsField("format", QVariant.String))           # File format
fields.append(QgsField("layer_name", QVariant.String))       # Layer name

# Spatial Fields
fields.append(QgsField("crs_authid", QVariant.String))       # CRS (e.g. EPSG:4326)
```

Note: `directory_path`, `file_format`, `layer_path`, and `crs` **do not exist** in the schema.

## Testing

After fix, verify:
1. ✅ Dashboard "By Directory" tab shows grouped statistics
2. ✅ Dashboard "By File Format" tab shows grouped statistics
3. ✅ Dashboard "By CRS" tab shows grouped statistics
4. ✅ Layer selector dialog shows correct format and directory
5. ✅ Metadata saves properly update inventory table status

## Why This Happened

The column names were likely assumed based on logical naming, but didn't match the actual inventory_miner implementation. The `data_type` query worked because it happened to use the correct column name.

## Prevention

- Always verify column names against actual database schema
- Reference inventory_miner.py field definitions when writing queries
- Test all dashboard tabs, not just one

## Impact

**Before Fix**:
- Only "By Data Type" tab worked
- Directory/Format/CRS tabs showed no data
- Metadata status updates may have failed silently

**After Fix**:
- All four drill-down tabs work correctly
- Layer selector shows accurate information
- Metadata status updates work reliably

---

**Version**: 0.3.2
**Date**: 2025-10-06
**Severity**: High (core feature broken)
**Status**: Fixed ✅
