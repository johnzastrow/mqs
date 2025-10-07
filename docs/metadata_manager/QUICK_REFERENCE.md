# Quick Reference - Metadata Manager v0.5.0

## Current Status
✅ **Phase 4 complete** - Smart Defaults + Layer Browser with Next/Previous navigation!

## What Works
- Database connection
- Dashboard statistics (Phase 2)
- 4-step wizard (Phase 3)
- Save to cache
- Write to .qmd files
- Write to GeoPackage
- **Smart defaults from inventory** (Phase 4)
- **Layer Browser with filtering** (Phase 4)
- **Next/Previous navigation** (Phase 4)
- **Auto-save before navigation** (Phase 4)
- Status tracking

## Key Files

### Main Implementation
```
db/metadata_writer.py       - File writing (v0.4.0)
db/manager.py               - Database ops + smart defaults (v0.5.0)
widgets/metadata_wizard.py  - 4-step wizard + smart defaults (v0.5.0)
widgets/layer_list_widget.py - Layer browser (NEW v0.5.0)
widgets/layer_selector_dialog.py - Layer selection (legacy)
widgets/dashboard_widget.py - Statistics dashboard (v0.2.0)
MetadataManager_dockwidget.py - Main UI with 3 tabs (v0.5.0)
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

## Complete Workflow (v0.5.0)

### Three-Tab Interface
1. **Dashboard** - See statistics and priorities
2. **Layer Browser** - Filter, search, navigate layers
3. **Metadata Editor** - Create/edit metadata with wizard

### Efficient Workflow with Smart Defaults
```
1. Open Metadata Manager
2. Dashboard shows completion statistics
3. Click "Layer Browser" tab
4. Filter: "Needs Metadata"
5. Search or sort to find target layers
6. Double-click a layer
   → Switches to "Metadata Editor" tab
   → Smart defaults auto-populate from inventory:
     * Title: "roads_2024" → "Roads 2024" (Title Case)
     * CRS, extent, geometry type
     * Field list in supplemental info
     * Existing GIS metadata if available
7. Fill 4 steps (most fields already populated!):
   - Step 1: Confirm title, add abstract, keywords
   - Step 2: Add contacts, select license
   - Step 3: Add lineage, links (optional)
   - Step 4: Review completeness
8. Click "Next →" button
   → Auto-saves current layer
   → Loads next layer with smart defaults
   → Repeat for next layer
9. All changes refresh Dashboard + Layer Browser automatically
```

### Navigation Features
- **Next/Previous buttons**: Move through filtered layers
- **Position indicator**: "Layer 5 of 42"
- **Auto-save**: Saves before navigation (no data loss)
- **Filter persistence**: Stays on filtered list (e.g., only "Needs Metadata")

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
