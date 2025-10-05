# Changelog

All notable changes to the batchvectorrename subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-10-05

### Added
- **Recursive directory scanning** - automatically processes entire directory trees
- **Multi-format vector file support** - handles 9 different vector file formats
- **Selective file type processing** - user can choose which vector formats to process
- **Enhanced rename operations**:
  - **Replace Text** operation with find/replace functionality (can remove text by replacing with empty string)
  - **Trim Beginning** operation to remove N characters from start of names
  - **Trim End** operation to remove N characters from end of names
- **Comprehensive logging system** using QgsMessageLog with Info, Warning, and Critical levels
- **Extended format support**:
  - GeoJSON (.geojson/.json) file renaming
  - KML/KMZ (.kml/.kmz) file renaming
  - GPX (.gpx) file renaming
  - GML (.gml) file renaming
  - MapInfo (.tab/.mif) file renaming
- **Enhanced dry run display** with formatted table showing file, original name, and new name
- **Automatic duplicate resolution** with incremental numbering for conflicting names
- **Progress reporting** during file discovery and processing phases

### Changed
- **Complete interface redesign** - now takes directory input instead of single file
- **Enhanced parameter validation** - specific validation for each rename operation
- **Improved error handling** - continues processing even if individual files fail
- **Better user feedback** - detailed progress reporting and operation summaries
- **Updated help documentation** - comprehensive operation descriptions and examples

### Technical
- Added `_find_vector_files()` method for recursive directory scanning with pattern matching
- Added format-specific processing methods for each supported vector type
- Added comprehensive logging methods (`_log_info()`, `_log_warning()`, `_log_error()`)
- Enhanced `_generate_rename_plan()` with duplicate detection and resolution
- Added operation-specific parameter validation in `_validate_parameters()`
- Improved `_display_rename_plan()` with formatted table output showing file context
- Added progress tracking during file discovery phase
- Enhanced error handling with individual layer processing isolation

### Performance
- **Efficient file discovery** - uses Path.rglob() for fast recursive scanning
- **Batch processing** - processes hundreds of files and layers in single operation
- **Progress reporting** - real-time feedback for long-running operations
- **Memory efficient** - processes layers individually to handle large datasets

## [0.1.0] - 2025-10-05

### Added
- Initial project structure for batchvectorrename subproject
- Complete QGIS Processing Toolbox script for batch renaming vector layers
- Support for multiple vector formats with layer renaming capabilities:
  - **GeoPackage (.gpkg)**: Full SQL-based layer renaming with metadata updates
  - **SpatiaLite (.sqlite/.db)**: Full SQL-based layer renaming for spatial tables
  - **Shapefiles (.shp)**: File-based renaming of all component files
  - **File Geodatabase (.gdb)**: Limited support (framework ready)
- **7 rename strategies** for different use cases:
  - Add prefix to layer names
  - Add suffix to layer names
  - Find and replace text in layer names
  - Clean names (remove invalid characters and standardize)
  - Convert to lowercase
  - Convert to uppercase
  - Convert to Title Case
- **Comprehensive safety features**:
  - Dry run mode for previewing changes before applying
  - Automatic backup creation with timestamped filenames
  - Conflict detection to prevent duplicate layer names
  - Name validation for database compatibility
  - Atomic transactions with rollback capability for databases
- **Robust error handling and recovery**:
  - Transaction-based database operations
  - Backup restoration guidance
  - Detailed error reporting and logging
  - Graceful handling of edge cases

### Technical
- Created `batchvectorrename.py` Processing Toolbox algorithm
- Implemented format detection and layer discovery for multiple vector types
- Added database operations using sqlite3 for GeoPackage and SpatiaLite renaming
- Implemented file operations for shapefile component renaming
- Added comprehensive parameter validation and strategy-specific logic
- Created backup system for safe operation rollback
- Implemented rename plan generation and validation
- Added detailed progress feedback and result reporting

### Safety and Validation
- Pre-flight validation of rename strategies and parameters
- Duplicate name detection before applying changes
- SQLite identifier length compliance (63 character limit)
- Invalid character sanitization for database compatibility
- Atomic database transactions with automatic rollback on failure
- Comprehensive backup system for all supported file types

### User Experience
- Intuitive parameter interface with strategy-specific parameter visibility
- Detailed dry run output showing before/after layer names
- Clear error messages and recovery guidance
- Progress feedback during all operations
- Comprehensive help documentation with examples

### Documentation
- Created comprehensive README.md with feature overview and usage instructions
- Added detailed parameter descriptions and rename strategy explanations
- Included examples for all rename strategies and file types
- Created troubleshooting section with common issues and solutions
- Added technical details for database and file operations
- Created CHANGELOG.md for version tracking