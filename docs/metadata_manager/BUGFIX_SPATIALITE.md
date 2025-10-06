# Bug Fix: ST_IsEmpty Error on Metadata Save (v0.3.6)

## Issue

**Severity**: CRITICAL
**Status**: Fixed ✅

Metadata saved to cache successfully, but inventory status never updated. Dashboard statistics remained at zero even after saving complete metadata.

## Error Message

```
2025-10-06T15:10:11 CRITICAL Error updating inventory: no such function: ST_IsEmpty
```

## Root Cause

### GeoPackage Triggers Require SpatiaLite

**What's happening**:
1. Inventory Miner creates GeoPackage with `geospatial_inventory` table
2. GeoPackage standard adds **automatic triggers** to maintain spatial data integrity
3. These triggers use **SpatiaLite spatial functions** like `ST_IsEmpty()`
4. When we UPDATE the inventory table, the triggers fire
5. Plain `sqlite3.connect()` doesn't have SpatiaLite loaded by default
6. Triggers fail with "no such function: ST_IsEmpty"

**GeoPackage Trigger Example** (auto-created by GeoPackage spec):
```sql
CREATE TRIGGER "geospatial_inventory_geom_update"
BEFORE UPDATE OF geom ON "geospatial_inventory"
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'update on geospatial_inventory violates constraint: geom must be valid')
    WHERE ST_IsEmpty(NEW.geom) = 1;  -- ❌ This function doesn't exist!
END;
```

Even though we're only updating `metadata_status`, `metadata_last_updated`, etc., the GeoPackage triggers still fire because they're defined as `BEFORE UPDATE` on the entire table.

## The Fix

### Load SpatiaLite Extension on Connect

Modified `db/manager.py` `connect()` method (lines 59-88):

```python
# Load SpatiaLite extension (required for GeoPackage operations)
self.connection.enable_load_extension(True)
try:
    # Try loading SpatiaLite (path varies by platform)
    try:
        self.connection.load_extension("mod_spatialite")  # Linux/Mac
    except:
        try:
            self.connection.load_extension("libspatialite")  # Alternative name
        except:
            # On Windows, might be in QGIS install
            import platform
            if platform.system() == "Windows":
                import os
                qgis_prefix = os.environ.get('QGIS_PREFIX_PATH', '')
                if qgis_prefix:
                    spatialite_path = os.path.join(qgis_prefix, 'bin', 'mod_spatialite')
                    self.connection.load_extension(spatialite_path)
            else:
                raise
except Exception as ext_error:
    QgsMessageLog.logMessage(
        f"Warning: Could not load SpatiaLite extension: {ext_error}\n"
        f"Spatial functions may not work in triggers.",
        "Metadata Manager",
        Qgis.Warning
    )
finally:
    self.connection.enable_load_extension(False)
```

### How It Works

1. **Enable extension loading** (security feature, disabled by default)
2. **Try multiple extension names** (platform-specific):
   - `mod_spatialite` - Common on Linux and macOS
   - `libspatialite` - Alternative naming convention
   - QGIS install path on Windows
3. **Catch errors gracefully** - Log warning if can't load (but continue)
4. **Disable extension loading** - Re-secure the connection

## Testing

### Before Fix
```
✅ Metadata cached for: C:\path\to\layer.shp
❌ CRITICAL Error updating inventory: no such function: ST_IsEmpty
```

Dashboard shows:
- Total Layers: 100
- Complete: 0  ← Never changes!
- Partial: 0
- No Metadata: 100

### After Fix
```
✅ Metadata cached for: C:\path\to\layer.shp
✅ Inventory updated: C:\path\to\layer.shp → status=complete
```

Dashboard shows:
- Total Layers: 100
- Complete: 1  ← Updates correctly!
- Partial: 0
- No Metadata: 99

## Why This Matters

### GeoPackage is a Spatial Format

GeoPackage isn't just a SQLite database - it's a **standardized spatial database format** (OGC standard) that:
- Has geometry columns with spatial reference systems
- Uses triggers to enforce spatial integrity
- Requires SpatiaLite extension for spatial functions
- Is similar to PostGIS but file-based

### Plain SQLite ≠ Spatial SQLite

| Plain SQLite | Spatial SQLite (SpatiaLite) |
|-------------|----------------------------|
| Basic data types | Geometry types (POINT, LINESTRING, etc.) |
| No spatial functions | 400+ spatial functions (ST_*, etc.) |
| File-based only | Spatial indexing (R-tree) |
| Simple triggers | Geometry validation triggers |

When you connect with `sqlite3.connect()`, you get **plain SQLite**. You must explicitly load the SpatiaLite extension to get spatial capabilities.

## Related Context

### Why Use GeoPackage for Inventory?

Inventory Miner creates GeoPackage because:
1. Stores **layer extents as polygons** (spatial data)
2. Allows **spatial queries** (e.g., "find all layers in this area")
3. **Single file** contains both tabular and spatial data
4. **Open standard** (OGC approved)
5. **QGIS native format** - best integration

### Alternative Would Be

If we used plain SQLite (non-spatial):
- ✅ No SpatiaLite dependency
- ❌ Can't store extent polygons
- ❌ Can't do spatial queries
- ❌ Would need separate extent table as text
- ❌ Less QGIS integration

The spatial capability is worth the SpatiaLite dependency.

## Prevention

### For Future Development

1. **Always load SpatiaLite** when connecting to GeoPackage
2. **Document spatial dependencies** in README
3. **Test on all platforms** (Windows, Linux, Mac) - extension paths differ
4. **Provide fallback** if SpatiaLite unavailable (log warning, continue)
5. **Consider QGIS's QgsVectorLayer** instead of raw sqlite3 for spatial operations

### Error Checking

When connecting to GeoPackage, verify spatial functions work:
```python
try:
    cursor.execute("SELECT ST_IsEmpty(NULL)")
    spatialite_available = True
except:
    spatialite_available = False
    # Log warning, may have issues with triggers
```

## Platform-Specific Notes

### Windows
- SpatiaLite usually in: `C:\Program Files\QGIS 3.x\bin\mod_spatialite.dll`
- Loaded via `QGIS_PREFIX_PATH` environment variable
- May need to add QGIS bin to PATH

### Linux
- Usually: `libspatialite.so` or `mod_spatialite.so`
- Installed via package manager: `sudo apt install libspatialite7`
- Available system-wide

### macOS
- Similar to Linux: `libspatialite.dylib`
- Installed via Homebrew: `brew install libspatialite`
- QGIS includes bundled copy

## Files Modified

- `Plugins/metadata_manager/db/manager.py` (lines 59-88)
  - Added SpatiaLite extension loading in `connect()` method
  - Multi-platform fallback logic
  - Graceful error handling
- Version updated to 0.3.6
- Documentation updated (CHANGELOG, metadata.txt)

---

**Version**: 0.3.6
**Date**: 2025-10-06
**Severity**: CRITICAL (blocked all inventory updates)
**Status**: Fixed ✅

## Verification

After applying fix, check the log:
- ✅ "Connected to database: ..." (should appear)
- ✅ "Inventory updated: ... → status=complete" (should appear after save)
- ❌ No "Error updating inventory: no such function: ST_IsEmpty" errors

If you still see the ST_IsEmpty error:
1. Check QGIS install path
2. Verify SpatiaLite is installed
3. Check log for "Warning: Could not load SpatiaLite extension"
4. Contact for platform-specific help
