# Changelog

All notable changes to the rasters2gpkg subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [ABANDONED] - 2025-10-05

### Discontinued
- **Project abandoned due to GeoPackage specification limitations for analytical raster data**
- GeoPackage raster storage is designed for tile-based base layers, not analytical datasets
- Key limitations include:
  - Tile-focused design unsuitable for continuous analytical rasters
  - Limited lossless compression support for scientific data
  - Poor support for high bit-depth rasters (16-bit, 32-bit floating point)
  - Performance issues with large analytical datasets
  - Insufficient metadata support for complex scientific rasters
- Alternative approaches recommended: keep native formats (GeoTIFF, NetCDF, HDF) optimized for analysis

## [0.1.0] - 2025-10-05

### Added
- Initial project structure for rasters2gpkg subproject
- QGIS Processing Toolbox script foundation for converting raster files to GeoPackage
- Support for 10 raster formats: GeoTIFF, ERDAS IMAGINE, ENVI, ASCII Grid, ESRI Grid, NetCDF, HDF, JPEG2000, PNG, JPEG
- User-selectable raster file types with multi-select controls
- Directory-aware layer naming with 7 configurable strategies:
  - Filename only (backward compatibility)
  - Parent directory + filename
  - Last N directories + filename
  - First N directories + filename
  - Selected levels (specify directory levels)
  - Smart path (auto-detect important directories)
  - Full relative path (truncated if needed)
- Dry run mode to preview layer names before processing data
- Smart layer naming with invalid character replacement and duplicate collision handling
- Automatic duplicate resolution with incrementing numbers
- QML style file application support
- Comprehensive error handling and logging
- Detailed progress feedback and reporting

### Technical
- Created `rasters2gpkg.py` Processing Toolbox algorithm
- Implemented raster file discovery with pattern matching for multiple formats
- Added directory naming strategy system (inherited from vectors2gpkg)
- Added `_find_raster_files()` method with format-specific pattern matching
- Implemented `_perform_dry_run()` for layer name preview functionality
- Added layer naming methods for all 7 directory strategies
- Created robust duplicate name handling with SQLite identifier compliance
- Added comprehensive parameter validation and error handling

### Documentation
- Created comprehensive README.md with feature overview and usage instructions
- Added detailed parameter descriptions and configuration options
- Included examples for all directory naming strategies
- Created CHANGELOG.md for version tracking
- Added troubleshooting section and technical requirements

### Notes
- This initial version provides the foundation and dry run functionality
- Actual raster processing implementation is planned for future versions
- All directory naming strategies are fully functional in dry run mode
- Framework is established for seamless transition to full raster processing