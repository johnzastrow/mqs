# Metadata File Handling Strategy

## Overview

This document describes how Metadata Manager handles existing XML metadata files (FGDC, ESRI, ISO 19115) and QGIS .qmd files.

## Current File Formats

### FGDC-STD-001-1998 (Federal Geographic Data Committee)
- **File naming**: `layer.shp.xml` or `layer.xml`
- **Used by**: ESRI ArcGIS (export), USGS, many US federal agencies
- **Standard**: XML-based, hierarchical structure
- **Example elements**: `<metadata><idinfo><citation>...`

### ESRI ArcGIS Metadata
- **File naming**: `layer.shp.xml` or `layer.xml`
- **Used by**: ESRI ArcGIS products
- **Standard**: Similar to FGDC but with ESRI extensions
- **Example elements**: `<metadata><Esri><ModDate>...`

### ISO 19115 / ISO 19139
- **File naming**: `layer.xml`
- **Used by**: International standard, many open-source tools
- **Standard**: XML-based, comprehensive geographic metadata
- **Example elements**: `<gmd:MD_Metadata>...`

### QGIS .qmd Files
- **File naming**: `layer.qmd`
- **Used by**: QGIS 3.x
- **Standard**: QGIS-specific XML format based on ISO 19115
- **Example elements**: `<qgis><identifier>...`

## Current Behavior (v0.5.0)

### Detection (Inventory Miner)
1. Scans for `.xml` metadata files alongside data files
2. Detects format: FGDC, ESRI, ISO 19115, or unknown
3. Extracts metadata: title, abstract, keywords, lineage, constraints, contacts
4. Stores in inventory table fields:
   - `layer_title`, `layer_abstract`, `keywords`
   - `lineage`, `constraints`, `url`, `contact_info`
   - `has_metadata_xml` (boolean)
   - `metadata_file_path` (path to .xml file)
   - `metadata_standard` (FGDC, ESRI, ISO, etc.)

### Smart Defaults (Metadata Manager)
1. Loads extracted metadata from inventory
2. Auto-populates wizard fields with existing metadata
3. User refines/confirms metadata in QGIS wizard
4. User saves metadata

### Writing (Metadata Manager)
**Current behavior:**
- Always writes `.qmd` file in QGIS format
- For shapefiles: `roads.shp` → `roads.qmd`
- Does NOT modify existing `.xml` file
- Both files coexist: `roads.shp.xml` (FGDC/ESRI) + `roads.qmd` (QGIS)

**QGIS precedence:**
- QGIS reads `.qmd` first if present
- Falls back to `.xml` if no `.qmd`
- Other software (ArcGIS, etc.) reads `.shp.xml` only

## File Coexistence Scenarios

### Scenario 1: Shapefile with FGDC metadata
```
Before:
  roads.shp
  roads.shp.xml (FGDC format)

After Metadata Manager:
  roads.shp
  roads.shp.xml (FGDC format - unchanged)
  roads.qmd (QGIS format - new)

QGIS reads: roads.qmd
ArcGIS reads: roads.shp.xml
```

### Scenario 2: GeoTIFF with ESRI metadata
```
Before:
  dem.tif
  dem.tif.xml (ESRI format)

After Metadata Manager:
  dem.tif
  dem.tif.xml (ESRI format - unchanged)
  dem.tif.qmd (QGIS format - new)

QGIS reads: dem.tif.qmd
ArcGIS reads: dem.tif.xml
```

### Scenario 3: Shapefile with no metadata
```
Before:
  parcels.shp

After Metadata Manager:
  parcels.shp
  parcels.qmd (QGIS format - new)

QGIS reads: parcels.qmd
ArcGIS: No metadata found
```

## Advantages of Current Approach

1. **Non-destructive**: Never modifies or deletes existing metadata
2. **Interoperability**: Each software reads its preferred format
3. **Backward compatible**: ArcGIS users still see their metadata
4. **Forward compatible**: QGIS users get native QGIS metadata
5. **Simple**: Clear separation between formats

## Potential Issues

1. **Dual metadata**: Two metadata files for same layer
2. **Sync issues**: Changes to `.qmd` don't update `.xml` (and vice versa)
3. **Confusion**: Users may wonder which file is "correct"
4. **Disk space**: Minor (metadata files are small, typically <50KB)

## Proposed Enhancements (Future)

### Option A: User Choice (Recommended)
Add preference in plugin settings:
- **Mode 1: QGIS Only** (current behavior) - Always write `.qmd`
- **Mode 2: Preserve Legacy** - Check for `.xml`, backup, then replace with `.qmd`
- **Mode 3: Dual Export** - Write both `.qmd` AND update `.xml` (requires format conversion)

### Option B: Backup Existing
Before writing `.qmd`:
1. Check for existing `.xml` metadata
2. If found, create backup: `roads.shp.xml.backup`
3. Write new `.qmd` file
4. Show warning: "Existing FGDC metadata backed up to .xml.backup"

### Option C: Smart Detection
1. If `.xml` exists and is recent (modified < 30 days ago)
   → Ask user: "Replace existing FGDC metadata or create new QGIS metadata?"
2. If `.xml` exists and is old (modified > 30 days ago)
   → Automatically create `.qmd` without prompt

### Option D: Format Conversion (Complex)
- Convert QGIS metadata → FGDC/ESRI XML
- Requires complex XML template mapping
- May lose QGIS-specific fields
- High effort, limited benefit

## Recommendations

### For v0.6.0 (Next Release)
1. **Add warning when existing metadata detected**:
   ```
   "This layer has existing FGDC/ESRI metadata (.xml).
    Metadata Manager will create a new QGIS metadata file (.qmd).
    Both files will coexist. QGIS will use the .qmd file.
    [ ] Don't show this again"
   ```

2. **Add indicator in Layer Browser**:
   - Show icon if existing `.xml` metadata detected
   - Tooltip: "Has legacy FGDC/ESRI metadata"

3. **Add option to import from legacy metadata**:
   - Button in wizard: "Import from Legacy Metadata"
   - Reads `.xml` file directly using Inventory Miner parsing
   - Populates wizard fields

### For v1.0.0 (Future)
1. **Add plugin settings**:
   - Metadata file handling mode (QGIS only / Backup legacy / Dual export)
   - Warning behavior (always show / never show)

2. **Add metadata file manager**:
   - List all metadata files for layer (both `.xml` and `.qmd`)
   - Show which file QGIS is using
   - Option to delete legacy `.xml` files
   - Option to export QGIS metadata to FGDC/ESRI format

## Technical Notes

### Why QGIS Uses .qmd Instead of .shp.xml

**Historical context:**
- ArcGIS uses `.shp.xml` (shapefile + .xml)
- Other formats use `.tif.xml`, `.tab.xml`, etc.
- QGIS wanted distinct format to avoid conflicts
- Chosen `.qmd` (QGIS Metadata) to be explicit

**Benefits of .qmd:**
- Clear indication this is QGIS metadata
- No confusion with FGDC/ESRI XML
- Simpler naming (no double extensions)
- Future-proof for QGIS-specific extensions

### Metadata Extraction from Inventory

The inventory already contains extracted metadata:
```python
# These fields come from parsing .xml files
layer_title          # From FGDC <title>, ESRI <title>, or ISO <gmd:title>
layer_abstract       # From FGDC <abstract>, ESRI <abstract>, etc.
keywords             # From FGDC <themekey>, ESRI <searchKeys>, etc.
lineage              # From FGDC <lineage>, ESRI <lineage>, etc.
constraints          # From FGDC <useconst>, ESRI <useLimit>, etc.
contact_info         # From FGDC <cntinfo>, ESRI <idPoC>, etc.
metadata_standard    # "FGDC", "ESRI", "ISO 19115", etc.
```

Smart Defaults uses these fields to populate the wizard, so **users benefit from existing metadata** even without additional work.

## Conclusion

**Current approach is appropriate for v0.5.0**:
- Non-destructive ✅
- Preserves existing metadata ✅
- Provides QGIS-native metadata ✅
- No user confusion (clear file names) ✅

**Future enhancements** can add:
- User warnings about existing metadata
- Import from legacy metadata button
- Plugin settings for handling mode
- Metadata file management UI

The coexistence of `.xml` and `.qmd` files is intentional and beneficial for interoperability between QGIS and other GIS software.
