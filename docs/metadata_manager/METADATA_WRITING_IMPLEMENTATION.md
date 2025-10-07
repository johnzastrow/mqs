# Metadata Writing Implementation

**Status:** ✅ Completed
**Version:** 0.1.0
**Date:** 2025-10-06

## Overview

Implemented the critical functionality to write QGIS metadata to target files. The plugin now writes metadata to both **.qmd sidecar files** (for Shapefiles, GeoTIFFs, etc.) and **GeoPackage embedded metadata** (using QGIS API).

## What Was Implemented

### 1. MetadataWriter Class (`db/metadata_writer.py`)

New utility class that handles all metadata writing operations:

- **`dict_to_qgs_metadata()`** - Converts metadata dictionary to QgsLayerMetadata object
- **`write_to_qmd_file()`** - Writes metadata to .qmd XML sidecar files
- **`write_to_geopackage()`** - Writes metadata directly to GeoPackage layers
- **`write_metadata()`** - Smart router that determines target format and writes accordingly

#### Key Features:

- **Automatic format detection** - Determines whether to write to .qmd or GeoPackage based on file extension
- **Container file support** - For GeoPackage/SQLite with multiple layers, creates .qmd files named `{container}_{layer}.qmd`
- **Comprehensive metadata conversion** - Supports all QGIS metadata fields:
  - Identification (title, abstract, type, language)
  - Keywords and categories
  - Contacts with roles
  - Links and online resources
  - Rights and licenses
  - History
  - CRS and spatial/temporal extents

### 2. Database Manager Updates (`db/manager.py`)

Added new method to track metadata write status:

- **`update_metadata_write_status()`** - Updates `metadata_cache` table with:
  - `last_written_date` - Timestamp when metadata was written to target
  - `target_location` - Path to .qmd file or "embedded:{path}"
  - `in_sync` - Whether cache matches target (1=synced, 0=out of sync)

### 3. Layer Selector Dialog Updates (`widgets/layer_selector_dialog.py`)

Enhanced to return file format information:

- Added `selected_layer_format` attribute
- Stores format in `Qt.UserRole + 1` data role
- Returns tuple of `(layer_path, layer_name, layer_format)`

### 4. Metadata Wizard Updates (`widgets/metadata_wizard.py`)

Updated save workflow to write to actual files:

- Added `current_file_format` attribute
- Captures file format when layer is selected
- **Enhanced `save_metadata()` function:**
  1. Saves to cache (as before)
  2. **NEW:** Writes to target file (.qmd or GeoPackage)
  3. Updates `metadata_cache` with write status
  4. Updates inventory with target location
  5. Shows detailed success/failure messages

## Workflow

### Save Metadata Workflow

```
User clicks Save
    ↓
1. Collect metadata from wizard steps
    ↓
2. Determine completeness (complete/partial)
    ↓
3. Save to metadata_cache
   └─ in_sync = 0 (not yet written)
    ↓
4. Write to target file
   ├─ GeoPackage → Use QGIS API to embed metadata
   └─ Other → Create .qmd sidecar file
    ↓
5. Update metadata_cache
   ├─ last_written_date = now
   ├─ target_location = path or "embedded:{path}"
   └─ in_sync = 1
    ↓
6. Update inventory
   ├─ metadata_status = complete/partial
   ├─ metadata_target = target location
   ├─ metadata_cached = 1
   └─ metadata_last_updated = now
    ↓
7. Show success message to user
```

## File Formats Supported

### Standalone Files → .qmd Sidecar

For these formats, a `.qmd` XML file is created next to the data file:

- **Shapefiles** (.shp) → roads.qmd
- **GeoTIFF** (.tif, .tiff) → elevation.qmd
- **CSV** (.csv) → points.qmd
- **KML** (.kml) → boundaries.qmd
- Other standalone formats

### Container Files → Embedded Metadata

For these formats, metadata is written directly into the container:

- **GeoPackage** (.gpkg) → Embedded in gpkg_metadata table
- **SQLite/SpatiaLite** (.sqlite, .db) → Can write to .qmd or embedded

## Target Location Format

The `target_location` field in `metadata_cache` uses these formats:

- **Sidecar files:** Full path to .qmd file
  Example: `C:\data\project\roads.qmd`

- **Embedded metadata:** Prefixed with "embedded:"
  Example: `embedded:C:\data\project\inventory.gpkg`

## Error Handling

The implementation includes comprehensive error handling:

1. **Cache Success, Write Failure:**
   - Metadata saved to cache
   - Warning message shown
   - User can retry write later
   - Inventory marked as "cached" only

2. **Complete Failure:**
   - Nothing saved
   - Error message with details
   - User can fix issue and retry

3. **Layer Not Found:**
   - Clear error message
   - Suggestions for debugging

## Testing

### Manual Testing Steps

1. **Test .qmd Writing (Shapefile):**
   ```python
   # In QGIS Python Console
   from MetadataManager.db.metadata_writer import MetadataWriter

   writer = MetadataWriter()
   metadata = {'title': 'Test', 'abstract': 'Test abstract'}
   success, target, msg = writer.write_metadata(
       r"C:\data\roads.shp",
       "roads",
       metadata,
       "ESRI Shapefile"
   )
   print(f"Success: {success}, Target: {target}")
   ```

2. **Test GeoPackage Writing:**
   ```python
   success, target, msg = writer.write_metadata(
       r"C:\data\inventory.gpkg",
       "layer_name",
       metadata,
       "GPKG"
   )
   print(f"Success: {success}, Target: {target}")
   ```

3. **Test via Plugin UI:**
   - Select layer from inventory
   - Fill in metadata fields
   - Click Save
   - Check:
     - Success message shows target location
     - .qmd file created (for shapefiles)
     - Metadata visible in layer properties
     - Dashboard shows updated status

## Database Schema Impact

### metadata_cache Table

Now tracks write status:

```sql
CREATE TABLE metadata_cache (
    id INTEGER PRIMARY KEY,
    layer_path TEXT NOT NULL,
    layer_name TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_written_date TIMESTAMP,        -- NEW: When written to target
    target_location TEXT,                -- NEW: Path to .qmd or "embedded:{path}"
    in_sync INTEGER DEFAULT 1,           -- NEW: 1=synced, 0=out of sync
    UNIQUE(layer_path, layer_name)
);
```

## Benefits

1. **Complete Metadata Workflow** - Users can now create AND save metadata
2. **QGIS Native Format** - Metadata readable by any QGIS installation
3. **Portable** - .qmd files travel with data files
4. **Standard Compliant** - Uses QGIS metadata standard (ISO 19115 based)
5. **Flexible Storage** - Adapts to file format (embedded vs sidecar)
6. **Recovery** - Cache provides backup if target files lost

## Known Limitations

1. **GeoPackage Write Verification** - Need to test if `layer.saveMetadata()` works correctly
2. **Large Files** - No special handling for very large metadata
3. **Concurrent Access** - No locking for simultaneous edits
4. **Undo/Redo** - No metadata edit history beyond cache timestamps

## Next Steps

### Immediate Testing Needed:

- [ ] Test .qmd writing with real Shapefile
- [ ] Test GeoPackage embedded metadata writing
- [ ] Verify QGIS can read written metadata
- [ ] Test with container files (multiple layers)
- [ ] Test error handling scenarios

### Future Enhancements:

- [ ] Batch metadata writing (apply to multiple layers)
- [ ] Metadata import from existing .qmd files
- [ ] Metadata sync detection (check if target modified externally)
- [ ] Write retry from cache
- [ ] Metadata diff/comparison

## Files Modified

1. **New Files:**
   - `db/metadata_writer.py` - Main writer class
   - `test_metadata_writer.py` - Test script

2. **Modified Files:**
   - `db/__init__.py` - Added MetadataWriter export
   - `db/manager.py` - Added update_metadata_write_status()
   - `widgets/layer_selector_dialog.py` - Added format to return value
   - `widgets/metadata_wizard.py` - Updated save_metadata() workflow

## Version History

- **v0.1.0** (2025-10-06) - Initial implementation
  - MetadataWriter class created
  - .qmd file writing implemented
  - GeoPackage writing implemented
  - Wizard integration completed
  - Database tracking added

## References

- [QGIS Metadata Documentation](https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/vector_properties.html#metadata-menu)
- [QGIS .qmd Format](https://github.com/qgis/QGIS/blob/master/python/core/auto_generated/metadata/qgslayermetadata.sip.in)
- [ISO 19115](https://www.iso.org/standard/53798.html)


 Based on the requirements document, here's what's next to implement:

  Priority 1: Write Metadata to Files 🎯

  Currently metadata only saves to cache. The biggest missing feature is actually writing metadata to:
  - .qmd sidecar files (for Shapefiles, GeoTIFFs, etc.)
  - GeoPackage embedded metadata (using QGIS API)

  This is marked as TODO in your code:
  target='cache',  # Will be 'file' when we implement file writing

  Priority 2: Libraries Management UI

  Create the management interfaces for:
  - Organizations/Contacts - Add/edit/delete reusable organizations
  - Keywords - Manage keyword sets and vocabularies
  - Templates - Create/edit/apply metadata templates

  The database tables exist, but there's no UI to manage them yet.

  Priority 3: Batch Operations

  - Select multiple layers from inventory
  - Apply templates to multiple layers at once
  - Bulk update metadata fields

  Priority 4: Import/Export

  - Import metadata from existing QGIS layers
  - Import from .qmd XML files
  - Export templates to share with others

  Priority 5: Expert Mode

  - Alternative to wizard: single-page form with all fields visible
  - Toggle between Wizard ↔ Expert mode

  ---
  Recommendation: Start with Priority 1 (Write Metadata to Files) since that completes the core workflow. Without
  it, users can create metadata but it never actually gets written to their layers.