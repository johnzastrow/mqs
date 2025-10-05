# Inventory Miner - Requirements

## Project Overview

Create a PyQGIS script for the QGIS Processing Toolbox that scans directory structures and generates comprehensive inventories of geospatial data files, providing detailed metadata and organizational insights.

## Core Functionality

### Input Processing
- **Directory Scanning**: Recursively search through all subdirectories starting from a user-specified top-level directory
- **Multi-Format Discovery**: Identify geospatial files in supported formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, rasters, etc.)
- **Container Format Support**: Enumerate individual layers within container formats (GeoPackages, File Geodatabases, SpatiaLite databases)
- **User Selection**: Allow users to select which file types to inventory via multi-select parameter
- **Validation**: Verify that each file/layer can be accessed and read

### Output Generation
- **Inventory Report**: Create comprehensive inventory of discovered geospatial data
- **Multiple Output Formats**: Support various output formats (CSV, Excel, JSON, GeoPackage attribute table)
- **Metadata Extraction**: Capture key metadata for each dataset
- **Hierarchical Structure**: Preserve directory hierarchy information in output

### Metadata Collection
- **File Information**:
  - File path (absolute and relative)
  - File name
  - File size
  - File type/format
  - Creation/modification dates
  - Directory depth and parent directories

- **Spatial Information**:
  - Geometry type
  - Feature count
  - Coordinate reference system (CRS/EPSG code)
  - Spatial extent (bounding box coordinates)
  - Layer dimensions (for rasters)

- **Attribute Information**:
  - Field/column names
  - Field data types
  - Field count
  - Sample attribute values (optional)

- **Layer Information** (for container formats):
  - Container file name
  - Layer name within container
  - Layer type (vector/raster/table)

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
   - Description: "Top-level directory to inventory"
   - Validation: Must be an existing, readable directory

2. **Output File** (`QgsProcessingParameterFileDestination`)
   - Description: "Path for the output inventory report"
   - File Filter: "CSV files (*.csv);;Excel files (*.xlsx);;JSON files (*.json);;GeoPackage files (*.gpkg)"
   - Validation: Must be a writable location

3. **File Types to Inventory** (`QgsProcessingParameterEnum` with `allowMultiple=True`)
   - Description: "Geospatial file types to include in inventory"
   - Options: Vectors, Rasters, All formats
   - Default: All types selected
   - Validation: At least one type must be selected

### Optional Parameters
4. **Include Metadata Details** (`QgsProcessingParameterBoolean`)
   - Description: "Include detailed metadata (CRS, extent, field names)"
   - Default: True

5. **Include Statistics** (`QgsProcessingParameterBoolean`)
   - Description: "Include summary statistics in output"
   - Default: True

6. **Check File Validity** (`QgsProcessingParameterBoolean`)
   - Description: "Validate each file can be opened (slower but more thorough)"
   - Default: True

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

### CSV/Excel Format
- Columns: File Path, File Name, Format, Geometry Type, Feature Count, CRS, Extent (xmin, ymin, xmax, ymax), Directory Depth, Parent Directory, File Size, Modified Date
- One row per layer/file
- Summary sheet/section with statistics

### JSON Format
- Hierarchical structure preserving directory organization
- Nested objects for metadata
- Summary section with statistics

### GeoPackage Format
- Attribute table with inventory data
- Optional spatial layer with extent polygons for each dataset
- Metadata table with summary statistics

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
