# MapSplat Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
