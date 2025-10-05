# Changelog

All notable changes to the inventory_miner subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Implemented full validation functionality for "Validate Files" option
- Enhanced vector validation: attempts to read first feature, checks geometry validity, detects missing CRS and empty datasets
- Enhanced raster validation: reads sample pixel data, validates bands, checks for missing CRS and geotransforms
- Validation results populate `is_valid` and `issues` fields with detailed problem descriptions
- Validation is optional (default: False) to maintain fast scanning performance

## [0.1.0] - 2025-10-05

### Added
- Initial implementation of inventory_miner QGIS Processing algorithm
- Automatic discovery of all GDAL/OGR-supported geospatial files through directory recursion
- Georeference detection in file headers, data bodies, and sidecar files (.prj, world files, .aux.xml)
- Support for vector formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, etc.)
- Support for raster formats (GeoTIFF, JPEG with world file, PNG with world file, IMG, etc.)
- Support for container formats (GeoPackage, File Geodatabase, SpatiaLite) with layer enumeration
- Non-spatial table detection and inventory
- GeoPackage output with spatial extent polygon layer in EPSG:4326
- **61 comprehensive metadata fields** including:
  - **ID and timestamps**: Auto-incrementing ID, record creation timestamp, file creation date
  - **File system metadata**: Path, size, modification date, directory structure
  - **Spatial metadata**: CRS, extent, georeference method
  - **Vector-specific metadata**: Geometry type, feature count, Z/M dimensions, field information
  - **Raster-specific metadata**: Dimensions, band count, pixel size, data types, NoData values, compression
  - **GIS metadata from XML files**: Title, abstract, keywords, author, lineage, constraints
  - **Enhanced metadata fields**: URL, ISO 19115 topic categories, contact information, related links
- GIS metadata parsing from XML files (ISO 19115, FGDC, ESRI standards)
- Advanced metadata extraction:
  - URL/online resource extraction
  - ISO 19115 topic category parsing
  - Comprehensive contact information (name, organization, email, phone)
  - Related links and references
- Sidecar file detection (.prj, world files, .aux.xml, metadata .xml)
- Extent transformation to EPSG:4326 for all layers
- Extent bounding box polygon geometry for each layer
- Quality indicators (validity, CRS presence, extent presence, data presence)
- User-configurable options for including/excluding vectors, rasters, and tables
- Optional GIS metadata parsing
- Optional sidecar file information
- Optional file validation
- Progress reporting and error handling
- REQUIREMENTS.md with comprehensive specifications
- CHANGELOG.md for version tracking
- Testing directory structure
