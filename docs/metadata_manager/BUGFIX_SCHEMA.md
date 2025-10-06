# Bug Fix: SQLite Multi-Statement Error

## Issue

When trying to initialize Metadata Manager tables, the following error occurred:

```
Failed to initialize tables: You can only execute one statement at a time
```

## Root Cause

The `get_metadata_cache_schema()` method in `db/schema.py` was returning a single string containing multiple SQL statements:

```python
def get_metadata_cache_schema():
    return """
    CREATE TABLE IF NOT EXISTS metadata_cache (...);

    CREATE INDEX IF NOT EXISTS idx_metadata_cache_path ON metadata_cache(layer_path);

    CREATE INDEX IF NOT EXISTS idx_metadata_cache_sync ON metadata_cache(in_sync);
    """
```

SQLite's `cursor.execute()` can only handle **one SQL statement at a time**. When the manager tried to execute this multi-statement string, SQLite raised an error.

## Solution

Changed `get_metadata_cache_schema()` to return a **list of individual statements** instead of a single multi-statement string:

```python
def get_metadata_cache_schema():
    return [
        """
        CREATE TABLE IF NOT EXISTS metadata_cache (...);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_metadata_cache_path
        ON metadata_cache(layer_path);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_metadata_cache_sync
        ON metadata_cache(in_sync);
        """
    ]
```

Also updated `get_all_schemas()` to use `extend()` instead of `append()` for this method:

```python
# Before
schemas.append(DatabaseSchema.get_metadata_cache_schema())

# After
schemas.extend(DatabaseSchema.get_metadata_cache_schema())
```

## Files Modified

1. **`Plugins/metadata_manager/db/schema.py`**:
   - Changed `get_metadata_cache_schema()` to return list
   - Updated `get_all_schemas()` to extend instead of append

## Testing

Created standalone test (`docs/metadata_manager/testing/test_schema_standalone.py`) that verifies:
- ✅ All SQL statements execute without errors
- ✅ Table and indexes are created successfully
- ✅ No multi-statement error occurs

Test result:
```
✓ TEST PASSED - Multi-statement issue is FIXED!
```

## Installation

After the fix, run the installer to update the plugin:

**Windows:**
```cmd
cd C:\Users\br8kw\Github\mqs\Plugins\metadata_manager
install.bat
```

**Linux/Mac:**
```bash
cd ~/Github/mqs/Plugins/metadata_manager
./install.sh
```

Then restart QGIS and try initializing the tables again.

## Prevention

This pattern was already correctly implemented in `get_keyword_sets_schema()`, which returned a list of two CREATE TABLE statements. The fix ensures consistency across all schema methods.

**Best Practice**: When a schema method needs to execute multiple SQL statements, always return a list of individual statements rather than a single multi-statement string.

## Related Methods

Other schema methods that correctly return single statements:
- ✅ `get_plugin_info_schema()` - single CREATE TABLE
- ✅ `get_organizations_schema()` - single CREATE TABLE
- ✅ `get_contacts_schema()` - single CREATE TABLE
- ✅ `get_keywords_schema()` - single CREATE TABLE
- ✅ `get_keyword_sets_schema()` - list of 2 statements (already correct)
- ✅ `get_templates_schema()` - single CREATE TABLE
- ✅ `get_settings_schema()` - single CREATE TABLE
- ✅ `get_metadata_cache_schema()` - **FIXED** - now list of 3 statements
- ✅ `get_upgrade_history_schema()` - single CREATE TABLE

## Status

✅ **FIXED** - Version 0.2.0 (2025-10-05)
