# Inventory Miner - Requirements

## Project Overview

Create a PyQGIS script for the QGIS Processing Toolbox that recursively scans directories and subdirectories for all supported geospatial data files (vectors, rasters, and any files with georeference information) to create a comprehensive inventory stored in a GeoPackage database. The tool leverages PyQGIS and GDAL/OGR to automatically recognize georeferenced files and extract detailed metadata, creating a spatial catalog with extent polygons for each discovered layer.

## Core Functionality

### Input Processing
- **Directory Scanning**: Recursively search through all subdirectories starting from a user-specified top-level directory
- **Automatic Format Recognition**: Use PyQGIS and GDAL/OGR to automatically identify all georeferenced files
- **Georeference Detection**: Recognize files with coordinate information in:
  - File headers (GeoTIFF, NetCDF, HDF, etc.)
  - Data body (shapefiles, GeoJSON, KML, GPX, GML, etc.)
  - Sidecar files (world files .tfw/.jgw/.pgw, .prj files, .aux.xml, etc.)
- **Multi-Format Discovery**: Identify all GDAL/OGR-supported formats:
  - **Vector formats**: Shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, DXF, DWG, etc.
  - **Raster formats**: GeoTIFF, JPEG with world file, PNG with world file, IMG, ECW, MrSID, NetCDF, HDF, GRIB, etc.
  - **Container formats**: GeoPackages (vectors and rasters), File Geodatabases, SpatiaLite databases
- **Container Format Support**: Enumerate individual layers within container formats
- **Supporting Table Detection**: Identify non-spatial tables associated with spatial layers (attribute tables, lookup tables, relationship classes)
- **Metadata File Detection**: Discover and parse GIS metadata files:
  - ISO 19115/19139 XML metadata
  - FGDC metadata (.xml)
  - ESRI metadata (.xml)
  - User-created metadata files
  - Software-generated metadata

### Output Generation
- **GeoPackage Database**: Create or append to an existing GeoPackage database
- **Spatial Inventory Layer**: Generate a polygon layer representing extent bounding boxes for all discovered layers
- **Extent Transformation**: Transform all extents to EPSG:4326 (WGS 84) for consistent spatial representation
- **Rich Attribute Table**: Store comprehensive metadata for each layer as attributes
- **One Record Per Layer**: Create individual records for each discovered layer, including layers within container formats

### Metadata Collection

#### File System Metadata
- **File Information**:
  - File path (absolute and relative)
  - File name
  - File size (bytes)
  - File type/format (detected by GDAL/OGR)
  - Driver name (GDAL/OGR driver used)
  - Creation/modification dates
  - Directory depth and parent directories
  - Directory path components

#### Spatial Metadata
- **Georeference Information**:
  - Coordinate reference system (CRS/EPSG code, WKT)
  - Native CRS of the layer
  - Spatial extent in native CRS (xmin, ymin, xmax, ymax)
  - Spatial extent transformed to EPSG:4326
  - Extent polygon geometry for visualization
  - Georeference method (header, sidecar file, embedded)

- **Vector-Specific Metadata**:
  - Geometry type (point, line, polygon, multi*, etc.)
  - Feature/record count
  - Has Z dimension (3D)
  - Has M dimension (measures)
  - Spatial index present

- **Raster-Specific Metadata**:
  - Pixel dimensions (width x height)
  - Band count
  - Data type per band
  - NoData values
  - Pixel size (resolution)
  - Compression type
  - Color interpretation

#### Attribute Metadata
- **Field Information**:
  - Field/column names (comma-separated list)
  - Field data types (comma-separated list)
  - Field count
  - Primary key fields
  - Foreign key relationships

#### GIS Metadata
- **Embedded Metadata**:
  - Layer title/description from metadata
  - Abstract/purpose
  - Keywords/tags
  - Author/creator
  - Creation date from metadata
  - Update frequency
  - Data quality statements
  - Lineage information
  - Constraints (access, use)
  - Contact information

- **Metadata File Information**:
  - Metadata file path (if separate file exists)
  - Metadata standard (ISO 19115, FGDC, ESRI)
  - Metadata date
  - Full metadata content (as text or XML)

#### Layer/Container Metadata
- **Container Information** (for layers within databases):
  - Container file path
  - Layer name within container
  - Layer type (vector/raster/table/non-spatial)
  - Is supporting table (non-spatial)
  - Related spatial layer (if supporting table)

#### Quality Indicators
- **Validation Flags**:
  - File is valid (can be opened)
  - Has CRS defined
  - Has extent defined
  - Has features/pixels
  - Metadata present
  - Sidecar files present (.prj, world file, .xml)
  - Potential issues flagged

### Data Organization
- **Directory Structure**: Capture and represent directory hierarchy
- **Categorization**: Group datasets by type, format, CRS, or custom criteria
- **Statistics**: Generate summary statistics (total files, total features, formats distribution)
- **Quality Checks**: Flag potential issues (missing CRS, empty datasets, corrupted files)

## Technical Requirements

### QGIS Integration
- **Processing Framework**: Implement as a QgsProcessingAlgorithm for integration with QGIS Processing Toolbox
- **Parameter Definition**: Provide user-configurable parameters through the Processing interface
- **Progress Reporting**: Implement progress callbacks and user feedback
- **Error Handling**: Graceful error handling with informative error messages

### Dependencies
- **QGIS Version**: Compatible with QGIS 3.40 or higher
- **PyQGIS**: Use only PyQGIS libraries for geospatial operations
- **Standard Library**: Use Python standard library for file operations and report generation
- **Cross-Platform**: Work on Windows, macOS, and Linux

### Performance Requirements
- **Memory Management**: Process files sequentially to manage memory usage
- **Large Directory Support**: Handle directories with thousands of files efficiently
- **Progress Reporting**: Provide real-time progress updates for long-running operations
- **Caching**: Optional caching mechanism for re-scanning large directories

## User Interface Parameters

### Required Parameters
1. **Input Directory** (`QgsProcessingParameterFile` with `Folder` behavior)
   - Description: "Top-level directory to scan for geospatial data"
   - Validation: Must be an existing, readable directory

2. **Output GeoPackage** (`QgsProcessingParameterFileDestination` OR `QgsProcessingParameterVectorDestination`)
   - Description: "Output GeoPackage database (new or existing)"
   - File Filter: "GeoPackage files (*.gpkg)"
   - Behavior: Create new GeoPackage or append to existing
   - Validation: Must be a writable location

3. **Inventory Layer Name** (`QgsProcessingParameterString`)
   - Description: "Name for the inventory layer in the GeoPackage"
   - Default: "geospatial_inventory"
   - Validation: Must be valid layer name (sanitized automatically)

### Optional Parameters
4. **Include Raster Files** (`QgsProcessingParameterBoolean`)
   - Description: "Include raster datasets in inventory"
   - Default: True

5. **Include Vector Files** (`QgsProcessingParameterBoolean`)
   - Description: "Include vector datasets in inventory"
   - Default: True

6. **Include Non-Spatial Tables** (`QgsProcessingParameterBoolean`)
   - Description: "Include non-spatial tables associated with spatial layers"
   - Default: True

7. **Parse GIS Metadata** (`QgsProcessingParameterBoolean`)
   - Description: "Extract and parse GIS metadata files (ISO 19115, FGDC, ESRI)"
   - Default: True

8. **Include Sidecar Files** (`QgsProcessingParameterBoolean`)
   - Description: "Report presence of sidecar files (.prj, world files, .xml)"
   - Default: True

9. **Validate Files** (`QgsProcessingParameterBoolean`)
   - Description: "Validate each file can be opened (slower but more thorough)"
   - Default: False

## Error Handling Requirements

### File-Level Errors
- **Invalid Files**: Log errors for corrupted or unreadable files and continue processing
- **Missing Components**: Handle files with missing auxiliary components gracefully
- **Container Access**: Handle inaccessible layers within container formats
- **Access Permissions**: Handle permission-denied errors gracefully

### Directory-Level Errors
- **Access Issues**: Log warnings for inaccessible subdirectories but continue processing
- **Empty Directories**: Handle directories with no geospatial files appropriately
- **Mixed Content**: Process available files when some are inaccessible

### Output Errors
- **Write Permissions**: Clear error messages for output directory permission issues
- **Disk Space**: Handle insufficient disk space errors
- **File Conflicts**: Proper handling of existing output files

## Logging and Feedback

### Progress Reporting
- **File Discovery**: Report number of geospatial files found
- **Processing Progress**: Real-time progress updates showing current file being processed
- **Success/Error Counts**: Running tally of successfully inventoried vs. failed files

### Detailed Logging
- **Debug Information**: File paths, metadata extraction status
- **Container Enumeration**: Success/failure of layer discovery within container formats
- **Error Details**: Specific error messages for troubleshooting
- **Validation Results**: Report files that failed validation checks

### Final Summary
- **Processing Statistics**: Total files processed, errors encountered
- **Output Information**: Final report location and summary statistics

## Implementation Requirements

### Code Structure
- **Class-Based**: Implement as a class inheriting from QgsProcessingAlgorithm
- **Modular Design**: Separate methods for file discovery, metadata extraction, and reporting
- **Version Control**: Include version information in the script header

### Testing Requirements
- **Unit Tests**: Create tests for core functionality
- **Integration Tests**: Test with various file configurations and container formats
- **Error Condition Tests**: Test error handling scenarios
- **Performance Tests**: Verify performance with large datasets

### Documentation Requirements
- **Inline Documentation**: Comprehensive docstrings and comments
- **User Documentation**: Clear help text in the algorithm description
- **Technical Documentation**: README with usage examples and troubleshooting

## Output Format Specifications

### GeoPackage Inventory Layer

#### Layer Configuration
- **Layer Name**: User-specified (default: "geospatial_inventory")
- **Geometry Type**: Polygon
- **CRS**: EPSG:4326 (WGS 84)
- **Geometry Column**: Contains extent bounding box polygon for each layer
- **Mode**: Create new GeoPackage or append to existing

#### Attribute Fields

**ID and Timestamp Fields:**
- `id` (INTEGER, Primary Key, Auto-increment) - Unique record identifier
- `record_created` (TEXT/DATETIME) - Timestamp when inventory record was created
- `file_created` (TEXT/DATETIME) - File creation date from filesystem

**File System Fields:**
- `file_path` (TEXT) - Absolute path to file
- `relative_path` (TEXT) - Path relative to scan root
- `file_name` (TEXT) - File name with extension
- `file_size_bytes` (INTEGER) - File size in bytes
- `file_modified` (TEXT/DATETIME) - Last modification timestamp
- `directory_depth` (INTEGER) - Depth from scan root
- `parent_directory` (TEXT) - Immediate parent directory name

**Format/Driver Fields:**
- `data_type` (TEXT) - "vector", "raster", "table", "unknown"
- `format` (TEXT) - File format (e.g., "GeoTIFF", "Shapefile", "GeoJSON")
- `driver_name` (TEXT) - GDAL/OGR driver name
- `container_file` (TEXT) - Container path (for layers in GeoPackage/FileGDB)
- `layer_name` (TEXT) - Layer name within container (if applicable)
- `is_supporting_table` (BOOLEAN) - Is non-spatial table

**Spatial Fields:**
- `crs_authid` (TEXT) - CRS authority ID (e.g., "EPSG:4326")
- `crs_wkt` (TEXT) - Well-Known Text CRS definition
- `native_extent` (TEXT) - Extent in native CRS (xmin,ymin,xmax,ymax)
- `wgs84_extent` (TEXT) - Extent in EPSG:4326 (xmin,ymin,xmax,ymax)
- `has_crs` (BOOLEAN) - CRS is defined
- `georeference_method` (TEXT) - "header", "sidecar", "embedded", "none"

**Vector-Specific Fields:**
- `geometry_type` (TEXT) - Point, LineString, Polygon, etc.
- `feature_count` (INTEGER) - Number of features
- `has_z` (BOOLEAN) - Has Z dimension
- `has_m` (BOOLEAN) - Has M dimension
- `has_spatial_index` (BOOLEAN) - Spatial index present

**Raster-Specific Fields:**
- `raster_width` (INTEGER) - Pixel width
- `raster_height` (INTEGER) - Pixel height
- `band_count` (INTEGER) - Number of bands
- `pixel_size_x` (REAL) - Pixel size X
- `pixel_size_y` (REAL) - Pixel size Y
- `data_types` (TEXT) - Band data types (comma-separated)
- `nodata_values` (TEXT) - NoData values (comma-separated)
- `compression` (TEXT) - Compression type

**Attribute Fields:**
- `field_count` (INTEGER) - Number of attribute fields
- `field_names` (TEXT) - Field names (comma-separated)
- `field_types` (TEXT) - Field data types (comma-separated)

**Metadata Fields:**
- `metadata_present` (BOOLEAN) - Has GIS metadata
- `metadata_file_path` (TEXT) - Path to metadata file
- `metadata_standard` (TEXT) - "ISO 19115", "FGDC", "ESRI", etc.
- `layer_title` (TEXT) - Title from metadata
- `layer_abstract` (TEXT) - Abstract/description from metadata
- `keywords` (TEXT) - Keywords (comma-separated)
- `metadata_author` (TEXT) - Creator/author
- `metadata_date` (TEXT/DATETIME) - Metadata date
- `lineage` (TEXT) - Lineage information
- `constraints` (TEXT) - Use/access constraints
- `url` (TEXT) - URL/online resource from metadata
- `iso_categories` (TEXT) - ISO 19115 topic categories (comma-separated)
- `contact_info` (TEXT) - Contact information from metadata (name, organization, email, phone)
- `links` (TEXT) - Related links and references (comma-separated)

**Sidecar Files:**
- `has_prj_file` (BOOLEAN) - .prj file present
- `has_world_file` (BOOLEAN) - World file present (.tfw, etc.)
- `has_aux_xml` (BOOLEAN) - .aux.xml file present
- `has_metadata_xml` (BOOLEAN) - Metadata .xml file present

**Quality Fields:**
- `is_valid` (BOOLEAN) - File can be opened
- `has_extent` (BOOLEAN) - Extent is defined
- `has_data` (BOOLEAN) - Contains features/pixels
- `issues` (TEXT) - Flagged issues (comma-separated)
- `scan_timestamp` (TEXT/DATETIME) - When inventory was created

#### Geometry Column
- **Field**: `extent_geom` (POLYGON)
- **Content**: Rectangular polygon representing bounding box
- **CRS**: EPSG:4326 (all extents transformed to this CRS)
- **Construction**: Create polygon from extent coordinates

## Quality Assurance

### Data Integrity
- **Metadata Accuracy**: Verify extracted metadata is correct
- **Completeness**: Ensure all discoverable files are included
- **Error Reporting**: Accurate reporting of issues and errors

### Performance Validation
- **Processing Speed**: Reasonable processing times for various directory sizes
- **Memory Usage**: Efficient memory management for large inventories
- **Output Size**: Verify output file sizes are reasonable

This implementation follows the same technical standards as other subprojects in the mqs repository, using only PyQGIS and Python standard library components.
