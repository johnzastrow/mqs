# MapSplat Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
