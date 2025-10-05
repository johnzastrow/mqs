# Changelog

All notable changes to the vectors2gpkg subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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