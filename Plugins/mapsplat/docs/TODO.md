# MapSplat TODO List

**Version:** 0.1.1
**Last Updated:** 2026-02-16

---

## Priority Legend

- 🔴 **Critical** - Blocks basic functionality
- 🟠 **High** - Important for usability
- 🟡 **Medium** - Nice to have
- 🟢 **Low** - Future enhancement

---

## v0.1.x - Proof of Concept

### Critical (Must Complete)

- [x] 🔴 **Validate ogr2ogr PMTiles generation**
  - Test with GDAL 3.8+ on Linux/Windows ✅
  - Handle ogr2ogr path detection ✅
  - Verify output PMTiles are valid ✅
  - File: `exporter.py`

- [ ] 🔴 **Bundle MapLibre GL JS assets for offline use**
  - Currently using CDN (works online)
  - Option 1: Download at runtime during export
    - Fetch maplibre-gl.js (v4.x) from unpkg
    - Fetch maplibre-gl.css
    - Fetch pmtiles.js (v3.x)
    - Save to `lib/` directory
    - Update HTML to use local paths when bundled
  - Option 2: Ship pre-bundled assets with plugin
  - Add checkbox: "Bundle for offline use"
  - File: `exporter.py:_copy_maplibre_assets()`, `mapsplat_dockwidget.py`

### High Priority

- [x] 🟠 **GDAL version check**
  - Check GDAL version before conversion ✅
  - Warn if PMTiles driver not available ✅
  - Provide helpful error message ✅
  - File: `exporter.py:_check_gdal_version()`

- [x] 🟠 **Test with real QGIS project**
  - Tested with Natural Earth data ✅
  - Single symbol works ✅
  - Categorized, graduated need more testing
  - Document any issues found

- [x] 🟠 **Handle export errors gracefully**
  - Catch ogr2ogr failures ✅
  - Show meaningful error messages ✅
  - Cancel button to abort long exports ✅
  - File: `exporter.py`

### Medium Priority

- [ ] 🟡 **Add layer count to UI**
  - Show "X layers selected" summary
  - Update on selection change
  - File: `mapsplat_dockwidget.py`

- [ ] 🟡 **Remember last output folder**
  - Store in QSettings
  - Restore on plugin open
  - File: `mapsplat_dockwidget.py`

- [ ] 🟡 **Validate output folder is writable**
  - Check write permissions before export
  - Show error if not writable
  - File: `mapsplat_dockwidget.py:_validate_export()`

---

## v0.2.x - Symbology Completeness

### High Priority

- [ ] 🟠 **Extract symbol opacity**
  - Fill opacity from QgsSimpleFillSymbolLayer
  - Line opacity from QgsSimpleLineSymbolLayer
  - Apply to MapLibre paint properties
  - File: `style_converter.py`

- [ ] 🟠 **Extract line width properly**
  - Handle unit conversion (mm to px)
  - Scale appropriately for web
  - File: `style_converter.py:_extract_line_width()`

- [ ] 🟠 **Handle null category values**
  - Categorized renderer can have NULL category
  - MapLibre uses different null handling
  - File: `style_converter.py:_convert_categorized()`

- [ ] 🟠 **Handle "all other values" category**
  - QGIS has catch-all category
  - Map to MapLibre default in match expression
  - File: `style_converter.py:_convert_categorized()`

### Medium Priority

- [ ] 🟡 **Support graduated color ramps**
  - Extract colors from QgsGraduatedSymbolRenderer
  - Generate interpolate expression for smooth transitions
  - File: `style_converter.py:_convert_graduated()`

- [ ] 🟡 **Support graduated size**
  - Point size based on attribute value
  - Line width based on attribute value
  - File: `style_converter.py`

- [ ] 🟡 **Add minzoom/maxzoom per layer**
  - Extract from QGIS scale-dependent visibility
  - Apply to MapLibre layer definition
  - File: `style_converter.py`

---

## v0.3.x - Multi-Layer & Options

### High Priority

- [ ] 🟠 **Separate PMTiles per layer**
  - Export each layer to own PMTiles file
  - Update sources in style.json
  - Update HTML template
  - File: `exporter.py`

- [ ] 🟠 **Layer ordering control**
  - Respect QGIS layer order
  - Or allow user to reorder in UI
  - File: `mapsplat_dockwidget.py`, `style_converter.py`

### Medium Priority

- [x] 🟡 **Configurable zoom range**
  - Add max zoom spinbox to UI ✅
  - Pass to ogr2ogr MAXZOOM ✅
  - Default: 6 (reasonable for most data)
  - File: `mapsplat_dockwidget.py`, `exporter.py`

- [ ] 🟡 **Layer visibility toggles in viewer**
  - Add checkbox per layer in HTML
  - Toggle visibility via MapLibre API
  - File: `exporter.py:_get_html_template()`

---

## v0.4.x - Raster Support

- [ ] 🟠 **Detect raster layers**
  - Show in layer list with [Raster] prefix
  - Already partially implemented
  - File: `mapsplat_dockwidget.py`

- [ ] 🟠 **Export raster to PMTiles**
  - Use ogr2ogr/gdal_translate for rasters
  - Generate raster PMTiles
  - File: `exporter.py`

- [ ] 🟡 **Raster/vector layer ordering**
  - Rasters typically go below vectors
  - Handle in style.json generation
  - File: `style_converter.py`

---

## v0.5.x - External Basemaps

- [ ] 🟡 **External basemap URL configuration**
  - Add input field for basemap tile URL
  - Support OSM, Stadia, MapTiler patterns
  - File: `mapsplat_dockwidget.py`

- [ ] 🟡 **Basemap switcher in viewer**
  - Dropdown to switch between basemaps
  - Remember selection in localStorage
  - File: `exporter.py:_get_html_template()`

---

## v0.6.x - Style Roundtripping

- [ ] 🟡 **Robust style.json import**
  - Validate imported JSON structure
  - Handle malformed files gracefully
  - File: `mapsplat_dockwidget.py:_import_style()`

- [ ] 🟡 **Style merge strategies**
  - Option: Replace all layers
  - Option: Merge (imported wins)
  - Option: Merge (generated wins)
  - File: `exporter.py:_merge_imported_style()`

---

## v0.7.x - Viewer Enhancements

- [ ] 🟡 **Legend generation**
  - Generate legend from style.json
  - Show colors and labels
  - File: `exporter.py:_get_html_template()`

- [ ] 🟡 **Fullscreen toggle**
  - Add fullscreen button to viewer
  - Use browser Fullscreen API
  - File: `exporter.py:_get_html_template()`

- [ ] 🟢 **Share/embed code**
  - Generate iframe embed code
  - Copy-to-clipboard button
  - File: `exporter.py:_get_html_template()`

---

## Documentation

- [x] 🟠 Create PLAN.md
- [x] 🟠 Create TODO.md
- [x] 🟠 Create CHANGELOG.md
- [x] 🟠 Create README.md
- [x] 🟠 Create REQUIREMENTS.md
- [ ] 🟡 Add inline code documentation
- [ ] 🟡 Create user guide with screenshots
- [ ] 🟢 Create video tutorial

---

## Testing

- [ ] 🟠 **Unit tests for style_converter.py**
  - Test color extraction
  - Test name sanitization
  - Test expression generation
  - File: `test/test_style_converter.py`

- [ ] 🟠 **Integration test with sample data**
  - Create test GeoPackage
  - Run full export
  - Validate output structure
  - File: `test/test_exporter.py`

- [ ] 🟡 **Cross-browser testing**
  - Test viewer in Chrome, Firefox, Safari
  - Document any compatibility issues

---

## Bugs

*(None known yet - add issues here as discovered)*

---

## Ideas / Future

- [ ] 🟢 Label support (complex - different engines)
- [ ] 🟢 Rule-based renderer support
- [ ] 🟢 SVG marker support
- [ ] 🟢 Heatmap layer support
- [ ] 🟢 3D terrain integration
- [ ] 🟢 Time-based animations
- [ ] 🟢 Direct S3/R2 upload
- [ ] 🟢 SFTP upload
- [ ] 🟢 Preview in plugin before export
- [ ] 🟢 Diff viewer for style changes


## user entered
- [x] add checkbox to also write the export log to a file in the output folder (e.g. export.log) for easier debugging and record keeping. Log file should include timestamps and log levels (INFO, ERROR, etc.) for each message and append to the file if it already exists rather than overwriting it. This would allow users to review the export process in detail after the fact and help with troubleshooting any issues that arise during export. File: `mapsplat_dockwidget.py`, `log_utils.py` ✅ v0.5.1
- add a lot of additional map controls to the HTML viewer (e.g. scale bar, geolocate, navigation, etc.)
- add extensive comments to the HTML template to explain how it works and how to customize it
- add controls to the plugin to allow user to select which map controls are included in the generated HTML viewer (e.g. zoom, rotation, fullscreen, etc.)
- add support for exporting to other formats besides PMTiles (e.g. GeoJSON, Shapefile, etc.)
- add support for exporting to cloud storage services (e.g. AWS S3, Google Cloud Storage, etc.)
- bring all assets locally for offline use, including MapLibre GL JS and PMTiles JS libraries, to ensure the generated HTML viewer works without an internet connection when deploying to environments with limited connectivity. This would involve downloading the necessary JavaScript and CSS files during the export process and referencing them locally in the generated HTML file. File: `exporter.py`, `mapsplat_dockwidget.py`
- 
-