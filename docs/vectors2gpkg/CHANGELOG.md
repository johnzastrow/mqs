# Changelog

All notable changes to the vectors2gpkg subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.3] - 2025-10-05

### Fixed
- **Critical bug fix**: Fixed `directory_levels` undefined error in `_process_vector_file()` method
- Added missing `directory_levels` parameter to function signature and function call
- Resolves processing failures when using directory-aware naming strategies

### Technical
- Updated `_process_vector_file()` method signature to include `directory_levels: str` parameter
- Fixed parameter passing in main processing loop to include `directory_levels` variable

## [0.8.2] - 2025-10-05

### Added
- **Selected levels naming strategy** - allows users to specify comma-separated directory level numbers for custom directory selection
- Directory levels parameter for precise control over which directory levels to include in layer names
- Support for non-contiguous directory selection (e.g., "0,2,4" to skip levels 1 and 3)
- Robust error handling for invalid level specifications with fallback to filename-only naming

### Changed
- Updated directory naming strategy options from 6 to 7 total strategies
- Enhanced parameter interface with directory levels string input for flexible level specification
- Updated dry run output to display directory levels configuration when using Selected levels strategy
- Updated help text and parameter descriptions to include the new Selected levels option

### Technical
- Added `_selected_levels_strategy()` method with comma-separated level parsing and validation
- Enhanced strategy dispatch logic to handle new strategy index positions
- Added comprehensive error handling for level parsing with graceful fallbacks
- Updated all method signatures to pass directory_levels parameter throughout the processing chain

## [0.8.1] - 2025-10-05

### Added
- **First N directories + filename** naming strategy - includes the first N directories from the top-level containing folder
- Enhanced directory depth parameter to support both "Last N directories" and "First N directories" strategies
- Complementary naming option to the existing "Last N directories" strategy for different directory naming needs

### Changed
- Updated directory naming strategy options from 5 to 6 total strategies
- Enhanced dry run output to show directory depth for both Last N and First N directory strategies
- Updated help text and parameter descriptions to include the new First N directories option

### Technical
- Added `_first_n_directories_strategy()` method with configurable depth (1-5 directories)
- Updated strategy dispatch logic to handle new strategy index positions
- Enhanced strategy name arrays and conditional logic for dry run output

## [0.8.0] - 2025-10-04

### Added
- **Dry run mode** - Preview layer names without processing any data
- Comprehensive dry run output showing original paths and resulting layer names
- Formatted table display with file numbering and type indicators
- Strategy summary in dry run results
- Progress tracking during dry run execution

### Changed
- Output GeoPackage path no longer required when using dry run mode
- Enhanced user interface with dry run parameter prominently positioned
- Improved validation logic to handle dry run vs normal processing modes
- Updated help text with dry run mode documentation and use cases

### Technical
- Added `_perform_dry_run()` method for dry run processing
- Added `_get_original_path_and_type()` for path and type extraction
- Added `_generate_dry_run_layer_name()` for consistent layer name generation
- Enhanced parameter validation with conditional requirement logic

## [0.7.0] - 2025-10-04

### Added
- Directory-aware layer naming with 5 configurable strategies
- **Filename only** (current behavior) - maintains backward compatibility
- **Parent directory + filename** - includes immediate parent directory
- **Last N directories + filename** - includes configurable number of parent directories
- **Smart path detection** - automatically detects important directories (years, projects, etc.)
- **Full relative path** - includes complete path from input root (truncated if needed)
- User-configurable directory depth parameter for "Last N directories" strategy
- Intelligent directory filtering that skips common non-semantic directories (home, temp, data, etc.)
- Automatic year and period detection (2023, Q1, etc.) in smart path strategy

### Changed
- Enhanced layer naming system with directory context preservation
- Default naming strategy remains "Filename only" for backward compatibility
- All naming strategies respect SQLite 63-character identifier limits
- Directory names are sanitized using same rules as filenames
- Container formats (GeoPackages, File Geodatabases, SpatiaLite) now support directory-aware naming

### Technical
- Added `_generate_directory_aware_name()` method with strategy dispatch
- Added individual strategy methods for each naming approach
- Added `_sanitize_directory_name()` for directory name cleaning
- Enhanced parameter handling with directory naming and depth options
- Comprehensive regex patterns for semantic directory detection

## [0.6.0] - 2025-10-04

### Added
- Duplicate layer name handling with automatic incrementing numbers
- Smart layer name collision detection across all processed layers and tables
- Comprehensive duplicate name resolution with fallback mechanisms

### Changed
- Enhanced layer naming system to prevent overwrites when duplicate names occur
- Layer names now automatically append incrementing numbers (e.g., layer_1, layer_2) when collisions are detected
- Improved processing to track all used layer names throughout the entire operation

### Technical
- Added `_ensure_unique_layer_name()` method with SQLite identifier length handling
- Integrated duplicate tracking into the main processing loop
- Enhanced error handling for extreme edge cases (safety fallback with UUID)

## [0.5.1] - 2025-10-04

### Added
- KMZ file support (.kmz) - compressed KML files are now supported alongside KML files
- Enhanced KML/KMZ pattern recognition in file discovery

### Changed
- Updated vector file type parameter to show "KML files (.kml/.kmz)" instead of just ".kml"
- Updated help text to mention KML/KMZ support

## [0.5.0] - 2025-10-04

### Added
- KML file support (.kml) - loads KML files with full metadata preservation
- SpatiaLite database support (.sqlite/.db) - can now copy layers from SpatiaLite databases
- MapInfo file support (.tab/.mif) - loads MapInfo files with metadata and style preservation
- Enhanced container format detection for SpatiaLite databases (spatial vs non-spatial tables)
- Additional vector file types in multi-select parameter (now supports 10 total formats)

### Changed
- Updated vector file discovery to handle KML files, SpatiaLite databases, and MapInfo files
- Enhanced layer naming for SpatiaLite sources (includes source database name)
- Improved processing logic to handle all new container and file formats
- Updated user interface with additional file type options for the new formats

## [0.4.2] - 2025-10-04

### Enhanced
- Enhanced non-spatial table detection from GeoPackages and File Geodatabases
- Improved debug feedback to distinguish between spatial layers and non-spatial tables
- Better identification of feature classes vs. attribute tables in File Geodatabases
- More comprehensive support for all table types within container formats

## [0.4.1] - 2025-10-04

### Fixed
- Fixed TypeError when sorting mixed file types (Path objects and tuples) in vector file discovery
- Improved custom sorting logic to handle all supported data source types correctly

## [0.4.0] - 2025-10-04

### Added
- File Geodatabase (.gdb) support - can now copy layers from ESRI File Geodatabases
- Standalone dBase (.dbf) file support - loads dBase files without corresponding shapefiles as non-spatial tables
- Non-spatial table handling - properly loads attribute-only data into GeoPackage
- Enhanced file type selection with 8 total supported formats

### Changed
- Updated vector file discovery to distinguish between shapefile-associated and standalone dBase files
- Improved layer naming for File Geodatabase sources
- Enhanced processing logic to handle both spatial and non-spatial data
- Updated user interface with additional file type options

## [0.3.0] - 2025-10-04

### Added
- GeoPackage input support - can now copy layers from existing GeoPackage files
- Multi-select parameter for choosing which vector file types to process
- Support for selectively processing only desired vector formats
- Enhanced layer naming for GeoPackage sources (includes source file name)

### Changed
- Vector file discovery now respects user-selected file types
- Improved error handling for GeoPackage layer enumeration
- Updated processing logic to handle both regular files and GeoPackage layers

## [0.2.0] - 2025-10-04

### Changed
- Renamed subproject from "shapefiles2gpkg" to "vectors2gpkg"
- Expanded support to multiple vector formats (GeoJSON, KML, GPX, GML) in addition to shapefiles
- Updated all documentation and script names to reflect broader vector file support
- Updated script class name from `Shapefiles2GpkgAlgorithm` to `Vectors2GpkgAlgorithm`

## [0.1.1] - 2025-10-04

### Fixed
- Fixed GeoPackage writing logic to properly handle first layer creation vs subsequent layer appends
- Resolved "Opening of data source in update mode failed" error when writing multiple layers

## [0.1.0] - 2025-10-04

### Added
- Initial project structure for vectors2gpkg subproject
- REQUIREMENTS.md outlining functionality to load vector files into GeoPackage
- CHANGELOG.md for version tracking
- Testing directory structure
- Complete QGIS Processing Toolbox script for converting vector files to GeoPackage