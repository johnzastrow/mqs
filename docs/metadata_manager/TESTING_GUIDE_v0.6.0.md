# Testing Guide - Metadata Manager v0.6.0

**Date:** October 7, 2025
**Version:** 0.6.0

## Pre-Testing Setup

### 1. Plugin Installation
The plugin is located at:
```
/mnt/c/Users/br8kw/Github/mqs/Plugins/metadata_manager/
```

Should be installed/linked to:
```
C:\Users\br8kw\AppData\Roaming\QGIS\QGIS3\profiles\AdvancedUser\python\plugins\metadata_manager\
```

### 2. Recompilation Complete
- ✅ `resources.py` compiled (31KB, current)
- ✅ Python cache files cleaned
- ✅ Syntax validation passed on all new files:
  - `widgets/inventory_widget.py`
  - `processors/inventory_runner.py`
  - `processors/__init__.py`

### 3. Dependencies
- ✅ Requires `inventory_miner.py` in: `/mnt/c/Users/br8kw/Github/mqs/Scripts/`
- ✅ Plugin imports from `../../../Scripts` relative path

## Testing Checklist

### Phase 1: Plugin Loading
- [ ] Plugin loads without errors in QGIS
- [ ] Metadata Manager icon appears in toolbar
- [ ] Dockable widget opens when clicked
- [ ] Widget shows 4 tabs: ① Inventory, ② Dashboard, ③ Layer Browser, ④ Metadata Editor

### Phase 2: Inventory Tab (NEW in v0.6.0)
- [ ] Tab shows "Inventory Integration" header
- [ ] Description text displays correctly
- [ ] All UI controls present:
  - [ ] Directory browse button
  - [ ] Database browse button
  - [ ] Layer name text field (default: "geospatial_inventory")
  - [ ] Mode radio buttons (Create New / Update Existing)
  - [ ] Data type checkboxes (Vectors, Rasters, Tables)
  - [ ] Processing checkboxes (Parse metadata, Sidecar files, Validate)
  - [ ] Run button
  - [ ] Stop button (disabled initially)
  - [ ] "Use Current Database" button
  - [ ] Progress bar
  - [ ] Status label
  - [ ] Statistics label
  - [ ] Log text display
  - [ ] Clear Log button

### Phase 3: Inventory Scan Functionality

#### Test 3A: Basic Scan
1. [ ] Click "Browse..." for directory
2. [ ] Select a test directory with geospatial files
3. [ ] Click "Browse..." for database
4. [ ] Enter path like `C:\Users\br8kw\Downloads\test_catalog.gpkg`
5. [ ] Keep all default options checked
6. [ ] Click "▶ Run Inventory Scan"
7. [ ] Verify:
   - [ ] Run button becomes disabled
   - [ ] Stop button becomes enabled
   - [ ] Progress bar updates
   - [ ] Status label updates
   - [ ] Statistics display shows counts
   - [ ] Log displays messages with timestamps
   - [ ] Log colors: ERROR=red, WARNING=orange, SUCCESS=green, INFO=black

#### Test 3B: Scan Completion
1. [ ] Wait for scan to complete
2. [ ] Verify completion message box appears
3. [ ] Verify shows: Database path, layer name, statistics
4. [ ] Click OK on message box
5. [ ] Verify:
   - [ ] Progress bar at 100%
   - [ ] Status shows "✓ Inventory complete!"
   - [ ] UI automatically switches to Dashboard tab
   - [ ] Dashboard shows new statistics
   - [ ] Layer Browser loads inventory list

#### Test 3C: Stop Functionality
1. [ ] Start a scan on large directory
2. [ ] Click "■ Stop" button after a few seconds
3. [ ] Verify:
   - [ ] Scan stops gracefully
   - [ ] Warning message in log
   - [ ] UI returns to ready state

#### Test 3D: Use Current Database
1. [ ] Have an existing database connected
2. [ ] Click "Use Current Database" button
3. [ ] Verify database field populates with current path
4. [ ] Run scan (should update existing database)

### Phase 4: Metadata Parsing (v0.6.0 Enhancement)

Test that metadata is extracted from various sources:

#### Test 4A: FGDC XML Files
1. [ ] Create/use directory with shapefiles having `.shp.xml` metadata (FGDC format)
2. [ ] Run inventory with "Parse GIS Metadata" checked
3. [ ] After completion, go to Layer Browser
4. [ ] Select a layer
5. [ ] Switch to Metadata Editor
6. [ ] Verify Smart Defaults populated from FGDC:
   - [ ] Title field filled
   - [ ] Abstract filled
   - [ ] Keywords filled
   - [ ] Lineage filled (if present)

#### Test 4B: ESRI XML Files
1. [ ] Use directory with `.xml` ESRI metadata files
2. [ ] Run inventory with metadata parsing
3. [ ] Verify Smart Defaults populated from ESRI XML

#### Test 4C: QGIS .qmd Files
1. [ ] Use directory with existing `.qmd` files
2. [ ] Run inventory
3. [ ] Verify Smart Defaults populated from .qmd

#### Test 4D: Embedded GeoPackage Metadata
1. [ ] Use GeoPackage with embedded metadata
2. [ ] Run inventory
3. [ ] Verify Smart Defaults populated from embedded metadata

### Phase 5: Integration Testing

#### Test 5A: End-to-End Workflow
1. [ ] Start fresh (no database)
2. [ ] Go to ① Inventory tab
3. [ ] Select directory with various geospatial files
4. [ ] Create new database
5. [ ] Run scan with all options enabled
6. [ ] Wait for completion
7. [ ] Verify auto-switch to ② Dashboard
8. [ ] Check Dashboard statistics are correct
9. [ ] Go to ③ Layer Browser
10. [ ] Verify layers listed with correct status
11. [ ] Filter by "Needs Metadata"
12. [ ] Double-click a layer
13. [ ] Verify auto-switch to ④ Metadata Editor
14. [ ] Verify Smart Defaults populated
15. [ ] Fill remaining fields
16. [ ] Click Save
17. [ ] Verify Dashboard refreshes
18. [ ] Verify Layer Browser refreshes
19. [ ] Verify status changes from "none" to "complete"

#### Test 5B: Update Mode
1. [ ] Have existing database with some layers having metadata
2. [ ] Select "Update Existing" mode
3. [ ] Run inventory scan
4. [ ] Verify:
   - [ ] Layers with metadata keep their status
   - [ ] New layers added with "none" status
   - [ ] Deleted layers marked as retired

### Phase 6: Error Handling

#### Test 6A: Missing inventory_miner.py
1. [ ] Temporarily rename `Scripts/inventory_miner.py`
2. [ ] Try to run inventory scan
3. [ ] Verify:
   - [ ] Error message appears
   - [ ] Message explains inventory_miner.py needed
   - [ ] Shows expected path
4. [ ] Restore inventory_miner.py filename

#### Test 6B: Invalid Directory
1. [ ] Enter non-existent directory path manually
2. [ ] Click Run
3. [ ] Verify warning message appears

#### Test 6C: Invalid Database Path
1. [ ] Leave database field empty
2. [ ] Click Run
3. [ ] Verify warning message appears

### Phase 7: Previous Functionality (Regression Testing)

Ensure v0.5.0 features still work:

#### Test 7A: Smart Defaults (Phase 4)
- [ ] Smart Defaults still populate from inventory
- [ ] Title Case conversion works
- [ ] CRS, extent, geometry type populated

#### Test 7B: Layer Browser (Phase 4)
- [ ] Filter by status works
- [ ] Search works
- [ ] Next/Previous navigation works
- [ ] Auto-save before navigation works

#### Test 7C: Dashboard (Phase 2)
- [ ] Statistics display correctly
- [ ] Drill-down tabs work
- [ ] Priority recommendations shown
- [ ] Refresh button works

#### Test 7D: Metadata Wizard (Phase 3)
- [ ] 4-step wizard navigation works
- [ ] Save to cache works
- [ ] Write to .qmd files works
- [ ] Write to GeoPackage works
- [ ] Contact/link management works

## Common Issues & Solutions

### Issue 1: Plugin Won't Load
**Symptoms:** Error on QGIS startup, plugin not in list
**Check:**
- Look in QGIS Python Console for errors
- Check `plugins/metadata_manager/__init__.py` exists
- Check `classFactory()` function present
- Check all `__init__.py` files in subdirectories

### Issue 2: Import Errors
**Symptoms:** "ModuleNotFoundError" or "ImportError"
**Check:**
- All `__init__.py` files present in:
  - `widgets/__init__.py`
  - `processors/__init__.py`
  - `db/__init__.py`
- All imports use correct paths
- No circular imports

### Issue 3: "inventory_miner not found"
**Symptoms:** Error when clicking Run in Inventory tab
**Solution:**
- Ensure `inventory_miner.py` exists in `Scripts/` directory
- Path from plugin: `../../../Scripts/inventory_miner.py`
- Check sys.path modification in `inventory_runner.py`

### Issue 4: UI Not Responsive During Scan
**Expected:** This is normal - scan runs in background thread
**Note:** UI should still be clickable, Stop button should work

### Issue 5: Resources Not Found
**Symptoms:** Missing icons, UI elements
**Solution:**
- Recompile resources: See recompilation section above
- Check `resources.py` exists and is current (31KB)

## Performance Benchmarks

Expected performance (approximate):
- **Small directory** (< 100 files): 10-30 seconds
- **Medium directory** (100-1000 files): 1-5 minutes
- **Large directory** (1000-10000 files): 5-30 minutes
- **Very large** (10000+ files): 30+ minutes

Progress bar should update smoothly throughout.

## Test Data Recommendations

For comprehensive testing, use directory containing:
- [ ] Shapefiles with .shp.xml (FGDC metadata)
- [ ] Shapefiles without metadata
- [ ] GeoTIFFs with .tif.xml (ESRI metadata)
- [ ] GeoTIFFs without metadata
- [ ] GeoPackages with multiple layers
- [ ] GeoPackages with embedded metadata
- [ ] Files with existing .qmd files
- [ ] Non-spatial tables (CSV with lat/lon)
- [ ] Mix of projected and geographic CRS
- [ ] Files in subdirectories (test recursion)

## Reporting Issues

When reporting issues, include:
1. QGIS version
2. Plugin version (0.6.0)
3. Operating system
4. Steps to reproduce
5. Error messages from:
   - Plugin log display
   - QGIS Python Console
   - QGIS Message Log (View → Panels → Log Messages)
6. Screenshot if UI issue

## Success Criteria

Version 0.6.0 is successful if:
- ✅ Plugin loads without errors
- ✅ All 4 tabs display correctly
- ✅ Inventory scan creates database successfully
- ✅ Metadata extracted from FGDC/ESRI/ISO/.qmd sources
- ✅ Smart Defaults populated from inventory
- ✅ Complete workflow: Scan → Dashboard → Browser → Editor → Save
- ✅ Progress monitoring works smoothly
- ✅ No regression in v0.5.0 features

---

**Good luck testing!** 🚀
