# Changelog

All notable changes to the mqs repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Metadata Manager Plugin**: SQLite multi-statement error during database initialization
  - Fixed schema.py to properly split CREATE TABLE and CREATE INDEX statements
  - Plugin now initializes tables successfully without errors

### Added
- **Metadata Manager Plugin - Phase 2: Metadata Quality Dashboard** (v0.2.0 in development)
  - Dashboard widget showing metadata completion statistics with progress bar
  - Four drill-down views: by Directory, Data Type, File Format, and CRS
  - Priority recommendations for high-impact metadata work
  - Five new statistics methods in DatabaseManager
  - Color-coded visual feedback (green/orange/red)
  - Refresh functionality for real-time updates
  - Test infrastructure with unit tests and testing guide
  - Comprehensive Phase 2 documentation

### Changed
- Extended Metadata Manager DatabaseManager with 240+ lines of statistics methods
- Updated MetadataManager dockwidget to display dashboard on startup
- Enhanced plugin with automatic dashboard initialization and refresh

## [0.8.0] - 2025-10-05

### Added
- batchvectorrename subproject (v0.2.0) - Batch Vector Layer Rename Tool
- **Recursive directory scanning** - automatically processes entire directory trees
- **Multi-format vector file support** - handles 9 different vector file formats
- **Selective file type processing** - user can choose which vector formats to process
- **9 rename operations**: Replace Text (find/replace with text removal), Trim Beginning, Trim End, Add Prefix, Add Suffix, Clean Names, Convert to Lowercase, Convert to Uppercase, Convert to Title Case
- **Comprehensive logging system** using QgsMessageLog with Info, Warning, and Critical levels
- **Enhanced dry run display** with formatted table showing file, original name, and new name
- **Automatic duplicate resolution** with incremental numbering for conflicting names
- **Progress reporting** during file discovery and processing phases
- Comprehensive safety features: dry run mode, automatic backups, conflict detection
- Atomic transactions with rollback capability for database operations
- Comprehensive documentation for batchvectorrename in docs/batchvectorrename/

### Changed
- Updated main README.md to include batchvectorrename subproject overview
- Updated Scripts section to reference batchvectorrename.py

## [0.7.0] - 2025-10-05

### Added
- rasters2gpkg subproject (v0.1.0) - Raster Files to GeoPackage Converter
- Support for 10 raster formats including GeoTIFF, ERDAS IMAGINE, ENVI, ASCII Grid, ESRI Grid, NetCDF, HDF, JPEG2000, PNG, JPEG
- Complete directory-aware layer naming system with 7 configurable strategies
- Dry run mode for previewing raster layer names before processing
- Comprehensive documentation for rasters2gpkg in docs/rasters2gpkg/

### Changed
- Updated main README.md to include rasters2gpkg subproject overview
- Updated Scripts section to reference rasters2gpkg.py

### Abandoned
- **rasters2gpkg subproject discontinued** due to GeoPackage specification limitations for analytical raster data
- GeoPackage raster storage is designed for tile-based base layers, not analytical datasets requiring lossless compression, high bit-depths, and continuous data access
- Alternative approaches recommended: keep native raster formats (GeoTIFF, NetCDF, HDF) optimized for analytical workflows

## [0.6.2] - 2025-10-05

### Changed
- vectors2gpkg enhanced with "Selected levels" naming strategy (v0.8.2) - allows users to specify comma-separated directory level numbers for custom directory selection
- Updated vectors2gpkg with 7 total directory naming strategies including non-contiguous directory level selection
- Enhanced flexibility for precise control over which directory levels are included in layer names

## [0.6.1] - 2025-10-05

### Changed
- vectors2gpkg enhanced with "First N directories" naming strategy (v0.8.1) - complements existing "Last N directories" with top-level directory selection
- Updated vectors2gpkg with 6 total directory naming strategies for improved workflow flexibility

## [0.6.0] - 2025-10-04

### Added
- vectors2gpkg dry run mode (v0.8.0) - preview layer names without processing data
- Comprehensive dry run output with formatted table display
- Enhanced workflow for testing directory naming strategies before processing

### Changed
- Updated vectors2gpkg with optional output path when using dry run mode
- Enhanced main README features to include dry run capabilities

## [0.5.0] - 2025-10-04

### Added
- vectors2gpkg directory-aware layer naming (v0.7.0) - 5 configurable naming strategies
- Smart path detection with automatic year and project directory recognition
- User-configurable directory depth and intelligent semantic filtering
- Backward compatible "filename only" option maintains existing behavior

### Changed
- Enhanced vectors2gpkg with comprehensive directory structure incorporation
- Updated main README features to include directory-aware naming capabilities

## [0.4.0] - 2025-10-04

### Added
- vectors2gpkg duplicate layer name handling (v0.6.0) - automatic resolution of naming collisions
- KMZ file support for compressed KML files (v0.5.1)
- Smart layer naming with incrementing numbers for duplicate names
- Enhanced documentation for duplicate handling across all formats

### Changed
- Updated vectors2gpkg subproject to v0.6.0 with comprehensive duplicate prevention
- Enhanced main README features list to include duplicate collision handling
- Updated REQUIREMENTS.md to reflect current multi-format capabilities

## [0.3.0] - 2025-10-04

### Added
- vectors2gpkg subproject (v0.5.0) - Vector Files to GeoPackage Converter
- Support for 10 vector file formats including container formats (GeoPackages, File Geodatabases, SpatiaLite)
- Non-spatial table handling and user-selectable file type processing
- Comprehensive documentation for vectors2gpkg in docs/vectors2gpkg/

### Changed
- Updated main README.md to include vectors2gpkg subproject overview
- Updated Scripts section to reference vectors2gpkg.py

## [0.2.0] - 2025-10-04

### Changed
- Reorganized repository to support multiple subprojects
- Moved ExtractStylesfromDirectoriesForStyleManager to docs/ExtractStylesfromDirectoriesForStyleManager/
- Moved executable scripts to Scripts/ directory
- Updated repository documentation to reflect subproject structure

### Added
- Repository structure documentation in CLAUDE.md
- Subproject overview in README.md
- Repository-level CHANGELOG.md

## [0.1.0] - 2025-10-04

### Added
- Initial repository setup
- CLAUDE.md with development rules for testing and versioning
- ExtractStylesfromDirectoriesForStyleManager subproject (see docs/ExtractStylesfromDirectoriesForStyleManager/CHANGELOG.md for details)
