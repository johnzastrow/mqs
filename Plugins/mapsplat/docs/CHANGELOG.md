# MapSplat Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## v0.5.3 — 2026-02-23

### Fixed
- **Basemap overlay mode: business layer icons now render** — replaced the
  MapLibre multi-sprite array (remote basemap sprite + local biz sprite) with
  a single local sprite. The multi-sprite approach silently failed when the
  remote Protomaps sprite was slow or unavailable, preventing all `biz:*`
  icon-image lookups. Now only the local `./sprites` file is used; basemap
  icon layers (road shields, arrows, POIs) will silently show no icon, but all
  fill/line/water/label layers and all business icons render correctly.

---

## v0.5.2 — 2026-02-22

### Added
- **Viewer tab** in the dockwidget with 7 map control checkboxes (all enabled by default)
- Map controls: scale bar, geolocate, fullscreen, coordinate display, zoom display, reset-view, north-up reset
- `generate_html_viewer()` module-level function in `exporter.py` (testable without Qt)
- Plugin `.gitignore` to exclude `__pycache__/`, `*.pyc`, `.pytest_cache/`, `resources.py`

---

## v0.5.1 — 2026-02-22

### Added
- Export log saved to `export.log` in the output folder (opt-in checkbox)
- `log_utils.py` with `format_log_line()` for timestamped log lines (INFO/WARNING/ERROR/SUCCESS)
- Log file appends across runs for persistent history

---

## v0.5.0 — 2026-02-22

### Changed
- **Tabbed dockwidget:** The panel now has two tabs — "Export" (all settings and controls) and "Log" (output log)
- Log auto-shown when export starts (UI switches to Log tab automatically)
- Removed expand/collapse toggle from the log area; log fills the tab naturally

---

## v0.4.0 — 2026-02-22

### New features

- **SVG sprite rendering (Option D):** Point layers using a single-symbol renderer with `QgsSvgMarkerSymbolLayer` now export as MapLibre `symbol` layers backed by a raster sprite atlas (`sprites.png` + `sprites.json`). The SVG icon renders with full fidelity instead of a generic circle.
- **Sprite fallback for other point types:** Categorized/graduated SVG layers, simple marker shapes, and font marker layers continue to render as color-correct MapLibre `circle` layers. A log message notes when an SVG layer is approximated as a circle.
- **Multi-sprite basemap support:** When basemap overlay mode is active and business layers include sprites, the style uses the MapLibre 4.x multi-sprite array format (`"sprite": [{"id": "default", ...}, {"id": "biz", ...}]`). Business icon references are automatically prefixed with `"biz:"`.
- **`StyleConverter` log callback:** `StyleConverter.__init__()` now accepts an optional `log_callback` parameter for routing sprite generation messages to the QGIS log panel.

### Internal

- `StyleConverter.convert()` accepts a new optional `output_dir` parameter; when provided, sprite generation runs before style conversion.
- New pure-Python helpers: `_compute_sprite_layout()`, `_build_symbol_layer_for_sprite()`.
- New QGIS-dependent helpers: `_is_svg_single_symbol()`, `_render_svg_to_qimage()`, `_generate_sprites()`.

---

## [0.3.0] - 2026-02-20

### Added
- **Basemap overlay mode** — combine a Protomaps basemap with QGIS business layers
  - New "Basemap Overlay" group box in the dockwidget (checkable; disabled by default)
  - Source type toggle: Remote URL or Local file (with Browse button)
  - Basemap style.json picker to load a Protomaps-compatible style
  - `_check_pmtiles_cli()` in exporter: verifies `pmtiles` CLI is available before extraction
  - `_extract_basemap()` in exporter: runs `pmtiles extract` (with bbox + maxzoom) using the
    same QProcess polling pattern as ogr2ogr; keeps UI responsive; supports cancellation
  - `_merge_business_into_basemap()` in exporter: loads basemap style, redirects remote tile
    source URL to `pmtiles://data/basemap.pmtiles`, injects business sources, appends overlay
    layers (excluding background)
- New settings keys: `use_basemap`, `basemap_source_type`, `basemap_source`, `basemap_style_path`

### Changed
- Style merge logic: when `use_basemap` is set, `_merge_business_into_basemap()` is used
  instead of `_merge_imported_style()`
- Standalone mode (basemap unchecked) is fully backward-compatible with all previous settings

### Output structure in basemap mode
```
output_dir/
├── index.html
├── style.json          (basemap style + business layers merged)
├── data/
│   ├── basemap.pmtiles (extracted from Protomaps)
│   └── layers.pmtiles  (business data)
├── lib/
├── README.txt
└── serve.py
```

## [0.2.2] - 2026-02-17

### Changed
- **HTML references external style.json** when "Export separate style.json" is enabled
  - Previously embedded full style inline AND exported separate file
  - Now HTML uses `style: './style.json'` for cleaner separation
  - Enables faster style iteration workflow: edit style.json, refresh browser
  - Self-contained mode (no style.json export) still embeds inline

## [0.2.1] - 2026-02-17

### Added
- **Style-only export option** - new checkbox to skip data conversion
  - Generates only style.json and HTML viewer
  - Much faster for iterating on styles
  - Use when PMTiles data already exists

### Fixed
- **Label rendering** - improved text field extraction
  - Use `to-string` expression to ensure values are strings
  - Standard Open Sans/Arial Unicode fonts for glyph compatibility
  - Default halo for better readability
  - Better label placement with padding and spacing
  - Point labels offset below markers

## [0.2.0] - 2026-02-17

### Added
- **Labels support** - extracts QGIS labels and converts to MapLibre symbol layers
  - Text field, font family, size, color
  - Halo/buffer settings (color, width)
  - Line placement for linear features
- **Rule-based renderer support** - converts filter expressions to MapLibre filters
  - Supports =, !=, <, >, <=, >= operators
  - Supports IS NULL, IS NOT NULL checks
  - Nested rules processed recursively
- **Opacity extraction** - reads actual alpha values from QGIS symbols
  - Fill opacity, line opacity, circle opacity
  - Stroke opacity for markers
- **Line dash patterns** - converts custom dash patterns to MapLibre line-dasharray
- **Line cap/join styles** - extracts pen cap (flat/square/round) and join (miter/bevel/round)
- **Multiple symbol layers** - processes all symbol layers, not just the first
  - Creates separate MapLibre layers for each symbol layer
- **Proper unit conversion** - handles mm, pixels, points, inches
- **Glyphs URL** - added default MapLibre font glyphs for label rendering

### Changed
- Categorized renderer now extracts opacity and line width per category
- Graduated renderer now extracts opacity and line width per range
- Marker symbols now extract stroke width and opacity

### Known Limitations
- SVG markers fall back to circles (sprite sheets not yet implemented)
- Font markers fall back to circles
- Fill patterns fall back to solid fills (needs sprite images)
- Complex QGIS expressions (AND/OR, functions) not converted
- Blend modes not supported by MapLibre

## [0.1.9] - 2026-02-17

### Added
- **Separate PMTiles per layer option** - new "PMTiles mode" dropdown in UI
  - "Single file (all layers)" - default, combines all layers into one PMTiles
  - "Separate files per layer" - creates individual PMTiles files for each layer
- Separate sources in style.json when using separate files mode

### Changed
- StyleConverter now accepts `single_file` parameter to control source generation
- Each layer references its own source when exporting separately

## [0.1.8] - 2026-02-17

### Added
- **Legend swatches** in layer controls panel
  - Color swatches show layer fill/line/circle colors
  - Swatch shape adapts to geometry type (square for fill, line for lines, circle for points)
  - Outline color shown on fill swatches when different from fill

### Fixed
- **serve.py Ctrl+C handling on Windows** - server now shuts down cleanly
  - Uses daemon thread approach instead of blocking serve_forever()
  - Proper shutdown sequence on keyboard interrupt
- **Layer control order** - layers now listed top-to-bottom matching map stacking
  - Top-most (visually on top) layers appear first in the legend

## [0.1.7] - 2026-02-17

### Added
- **Cancel button** to abort long-running exports
- **Max zoom control** in UI (spinbox, range 4-18, default 6)
- **serve.py** script in export output for local viewing
  - Custom HTTP server with Range request support (required for PMTiles)
  - Auto-opens browser on startup
- GDAL version check before conversion
- PMTiles driver availability check
- Layer listing before conversion (shows which layers will be processed)
- Progress updates during ogr2ogr conversion (elapsed time, output file size)
- Expandable log panel (Expand/Collapse button)

### Changed
- **Switched from QThread to QProcess** for ogr2ogr execution
  - UI now stays responsive during long exports
  - Proper cancellation support
- HTML viewer now uses **CDN for MapLibre assets** (unpkg.com)
  - maplibre-gl.js v4.7.1
  - maplibre-gl.css v4.7.1
  - pmtiles.js v3.2.0
- Default max zoom reduced from 14 to 6 (much faster exports)
- Removed maxBounds from map initialization (was causing errors)

### Fixed
- **QgsCoordinateTransformContext error** - was passing wrong type to options.ct
- **QGIS hanging during export** - replaced blocking subprocess with QProcess + processEvents
- **Console windows appearing on Windows** - added CREATE_NO_WINDOW flags
- **PMTiles "no content-length" error** - serve.py now supports HTTP Range requests
- **serve.py "read of closed file" error** - fixed file wrapper to keep file open

### Updated
- TODO.md with completed items and offline bundling feature description

## [0.1.6] - 2026-02-17

### Added
- `deploy.bat` for Windows Command Prompt deployment
- `deploy.ps1` for Windows PowerShell deployment
- Windows deployment instructions in README

### Changed
- README now includes platform-specific installation instructions (Linux/macOS/Windows)

## [0.1.5] - 2026-02-16

### Added
- Local viewing instructions in README
- Explanation of why `file://` protocol doesn't work with PMTiles
- Quick start commands for local servers:
  - Python (`python -m http.server`)
  - Node.js (`npx serve`)
  - PHP (`php -S`)
  - VS Code Live Server
  - PowerShell one-liner for Windows

## [0.1.4] - 2026-02-16

### Changed
- Consolidated duplicate README files into single top-level README.md
- Removed docs/README.md (redundant)

## [0.1.3] - 2026-02-16

### Added
- Comprehensive README.md in plugin root directory
- Detailed deployment instructions for multiple platforms:
  - GitHub Pages
  - Netlify / Vercel
  - AWS S3
  - nginx / Apache
- CORS configuration examples for nginx, Apache, and S3
- Troubleshooting guide for common issues
- Development and build instructions
- Project structure documentation

## [0.1.2] - 2026-02-16

### Added
- Qt6/QGIS 4.0 compatibility shims
- Try/except blocks for Qt5/Qt6 enum differences

### Fixed
- `QAction` import location (moved from QtWidgets to QtGui in Qt6)
- `Qt.RightDockWidgetArea` enum scoping for Qt6
- `Qt.ItemIsEnabled` enum scoping for Qt6
- `Qt.UserRole` enum scoping for Qt6
- `QListWidget.MultiSelection` enum scoping for Qt6

### Changed
- Plugin now compatible with both QGIS 3.x (Qt5) and QGIS 4.x (Qt6)

## [0.1.1] - 2026-02-16

### Added
- PLAN.md with development roadmap and architecture decisions
- TODO.md with prioritized task list
- Updated CHANGELOG.md with version tracking

### Changed
- Renamed plugin from "po" to "mapsplat"
- Updated all version references to 0.1.1

## [0.1.0] - 2026-02-16

### Added
- Initial plugin scaffold
- Dockable widget UI with layer selection
- Layer export to GeoPackage
- PMTiles generation via ogr2ogr
- Basic style conversion for:
  - Single symbol renderers (fill, line, circle)
  - Categorized renderers
  - Graduated renderers
- HTML viewer generation with MapLibre GL JS
- Feature click-to-identify popups
- Auto-reprojection to EPSG:3857 (Web Mercator)
- Style.json export option
- Style.json import for Maputnik roundtripping
- README generation with deployment instructions

### Known Limitations
- Labels not yet supported
- Rule-based renderers fall back to default style
- Complex symbology (SVG markers, patterns) not supported
- Raster export not yet implemented
- MapLibre assets not bundled (CDN fallback)
