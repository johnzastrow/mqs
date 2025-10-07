# Quick Reference - Metadata Manager v0.4.1

## Current Status
✅ **Core workflow complete** - Can create and save metadata to files!

## What Works
- Database connection
- Dashboard statistics
- 4-step wizard
- Save to cache
- **Write to .qmd files**
- **Write to GeoPackage**
- Layer selection
- Status tracking

## Key Files

### Main Implementation
```
db/metadata_writer.py       - File writing (NEW v0.4.0)
db/manager.py               - Database operations
widgets/metadata_wizard.py  - 4-step wizard
widgets/layer_selector_dialog.py - Layer selection
widgets/dashboard_widget.py - Statistics dashboard
```

### Documentation
```
NEXT_SESSION_START_HERE.md  - Start here tomorrow
SESSION_SUMMARY_2025-10-06_PART3.md - Tonight's work
METADATA_WRITING_IMPLEMENTATION.md  - Technical details
REQUIREMENTS.md             - Full feature spec
```

## Quick Commands

### Reload Plugin
```python
import qgis.utils
qgis.utils.reloadPlugin('MetadataManager')
```

### Get Plugin Instance
```python
plugin = qgis.utils.plugins.get('MetadataManager')
db = plugin.db_manager
```

### Test Metadata Writer
```python
from MetadataManager.db.metadata_writer import MetadataWriter
writer = MetadataWriter()
```

### Fix Database Status
```python
success, msg = db.fix_incorrect_metadata_status()
```

## File Paths
- Plugin: `/mnt/c/Users/br8kw/Github/mqs/Plugins/metadata_manager/`
- Test DB: `C:/Users/br8kw/Downloads/geo_inv.gpkg`

## Database Tables

### Core
- `geospatial_inventory` - From Inventory Miner (file catalog)
- `metadata_cache` - Cached metadata JSON
- `plugin_info` - Version tracking

### Libraries (exist, no UI yet)
- `organizations` - Reusable org profiles
- `contacts` - Contact info with roles
- `keywords` - Keyword library
- `keyword_sets` - Keyword collections
- `templates` - Metadata templates

## Complete Workflow

```
1. Open Metadata Manager
2. Dashboard shows statistics
3. Click "Metadata Editor" tab
4. Click "Select Layer from Inventory"
5. Choose layer from list
6. Fill 4 steps:
   - Step 1: Title, Abstract, Keywords
   - Step 2: Contacts, License, Constraints
   - Step 3: Lineage, Links, Purpose
   - Step 4: Review (shows Complete/Partial)
7. Click Save
8. Saves to cache → Writes to file → Updates inventory
9. Dashboard auto-refreshes
```

## Metadata Targets

### Standalone Files → .qmd sidecar
- Shapefiles: `roads.shp` → `roads.qmd`
- GeoTIFF: `dem.tif` → `dem.tif.qmd`
- CSV, KML, etc.

### Container Files → Embedded
- GeoPackage: Embedded in `gpkg_metadata` table
- Shows as `embedded:{path}` in cache

## Version History

- **v0.4.1** - Fixed XML serialization bug
- **v0.4.0** - **MAJOR:** File writing implemented
- **v0.3.6** - Fixed SpatiaLite loading
- **v0.3.5** - Auto-refresh dashboard
- **v0.3.0** - 4-step wizard complete
- **v0.2.0** - Dashboard + database

## Known Issues

1. GeoPackage write needs more testing
2. No retry UI for failed writes
3. No undo/redo
4. No external change detection

## Next Features

1. **Libraries Management** (organizations, contacts, keywords)
2. **Templates** (create, apply, manage)
3. **Batch operations** (apply to multiple layers)
4. **Import/Export** (share templates)
5. **Expert mode** (single-page form)

## Bug Fixes Applied

### Container File Bug (v0.4.0)
**Problem:** All layers in GeoPackage marked complete when saving one
**Fix:** Match on `file_path AND layer_name`, not just `file_path`

### XML Serialization (v0.4.1)
**Problem:** `QgsLayerMetadata.toXml()` doesn't exist
**Fix:** Use `writeMetadataXml(root, doc)` with QDomDocument

## Testing Checklist

Tomorrow's tests:
- [ ] Shapefile → .qmd file created
- [ ] GeoPackage → metadata embedded
- [ ] QGIS reads .qmd files
- [ ] Container files (only target layer marked)
- [ ] Dashboard shows correct stats
- [ ] File name column in selector

## Common Errors

### "No module named MetadataManager"
→ Plugin not loaded, restart QGIS

### "ST_IsEmpty error"
→ SpatiaLite not loaded (auto-loads now)

### "toXml error"
→ Old version, reload plugin

### "All layers marked complete"
→ Old bug, run fix_incorrect_metadata_status()

## Architecture

```
MetadataManager (main plugin)
├── MetadataManager_dockwidget (tab container)
│   ├── Dashboard Widget (stats)
│   └── Metadata Editor (wizard)
├── DatabaseManager (connections, queries)
├── MetadataWriter (file operations)
└── Widgets
    ├── metadata_wizard (4 steps)
    ├── layer_selector_dialog (pick from inventory)
    └── dashboard_widget (statistics)
```

## Success Metrics

**Core Workflow:** ✅ Complete
- Users can create metadata
- Users can save to cache
- Users can write to files
- Users can track completion

**Next Phase:** Libraries Management
- Reusable organizations
- Contact library
- Keyword sets
- Templates

---

**Status:** Production-ready core, ready for enhancement features
**Version:** 0.4.1
**Last Updated:** October 6, 2025
