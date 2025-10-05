# Vector Files to GeoPackage Converter - Requirements

## Project Overview

Create a PyQGIS script for the QGIS Processing Toolbox that recursively searches a directory tree for vector files and consolidates them into a single GeoPackage with metadata preservation, duplicate name handling, and optional style application.

## Core Functionality

### Input Processing
- **Directory Scanning**: Recursively search through all subdirectories starting from a user-specified top-level directory
- **Multi-Format Discovery**: Identify vector files in 10 supported formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, standalone dBase)
- **Container Format Support**: Extract individual layers from container formats (GeoPackages, File Geodatabases, SpatiaLite databases)
- **User Selection**: Allow users to select which vector file types to process via multi-select parameter
- **Validation**: Verify that each vector file/layer is valid and can be loaded

### Output Generation
- **GeoPackage Creation**: Create a single `.gpkg` file containing all processed vector data as separate layers
- **Layer Management**: Handle multiple layers within a single GeoPackage file with intelligent naming
- **Duplicate Prevention**: Automatically resolve layer name collisions with incrementing numbers
- **Spatial Indexing**: Create spatial indexes for each layer to optimize query performance
- **Non-Spatial Tables**: Support for attribute-only tables from container formats and standalone dBase files

### Data Preservation
- **Geometry Preservation**: Maintain all geometric data from source vector files
- **Attribute Preservation**: Preserve all attribute data and field types
- **Metadata Preservation**: Retain coordinate reference systems and other spatial metadata
- **Feature Integrity**: Ensure no data loss during the conversion process
- **Layer Integrity**: Prevent layer overwrites through smart duplicate name handling

### Layer Naming
- **Name Derivation**: Generate layer names from vector file names (without file extension)
- **Character Sanitization**: Replace invalid characters with underscores
- **Duplicate Handling**: Automatically resolve naming collisions by appending incrementing numbers
- **Naming Rules**:
  - Replace any non-alphanumeric characters (except underscores) with underscores
  - Ensure layer names don't start with numbers (prefix with "layer_" if needed)
  - Remove consecutive underscores and leading/trailing underscores
  - Limit names to 63 characters (SQLite identifier limit)
  - Handle empty names with fallback to "unnamed_layer"
  - Resolve duplicate names by appending _1, _2, _3, etc.
  - Track all used names across the entire processing session

### Style Application
- **QML Detection**: Look for `.qml` style files in the same directory as each shapefile
- **Naming Convention**: QML files must have the same base name as the corresponding shapefile
- **Style Application**: Apply found QML styles to the corresponding layers in the GeoPackage
- **Error Handling**: Continue processing if style application fails, with appropriate logging

## Technical Requirements

### QGIS Integration
- **Processing Framework**: Implement as a QgsProcessingAlgorithm for integration with QGIS Processing Toolbox
- **Parameter Definition**: Provide user-configurable parameters through the Processing interface
- **Progress Reporting**: Implement progress callbacks and user feedback
- **Error Handling**: Graceful error handling with informative error messages

### Dependencies
- **QGIS Version**: Compatible with QGIS 3.40 or higher
- **PyQGIS**: Use only PyQGIS libraries (no external dependencies)
- **Standard Library**: Use Python standard library for file operations
- **Cross-Platform**: Work on Windows, macOS, and Linux

### Performance Requirements
- **Memory Management**: Process files sequentially to manage memory usage
- **Large File Support**: Handle large shapefiles efficiently
- **Spatial Indexing**: Create spatial indexes by default for optimal query performance
- **Progress Reporting**: Provide real-time progress updates for long-running operations

## User Interface Parameters

### Required Parameters
1. **Input Directory** (`QgsProcessingParameterFile` with `Folder` behavior)
   - Description: "Top-level directory containing vector files"
   - Validation: Must be an existing, readable directory

2. **Output GeoPackage** (`QgsProcessingParameterFileDestination`)
   - Description: "Path for the output .gpkg file"
   - File Filter: "GeoPackage files (*.gpkg)"
   - Validation: Must be a writable location

3. **Vector File Types** (`QgsProcessingParameterEnum` with `allowMultiple=True`)
   - Description: "Vector file types to process"
   - Options: 10 supported formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, standalone dBase)
   - Default: All types selected
   - Validation: At least one type must be selected

### Optional Parameters
4. **Apply QML Styles** (`QgsProcessingParameterBoolean`)
   - Description: "Apply QML style files if found alongside vector files"
   - Default: True

5. **Create Spatial Indexes** (`QgsProcessingParameterBoolean`)
   - Description: "Create spatial indexes for each layer"
   - Default: True

## Error Handling Requirements

### File-Level Errors
- **Invalid Vector Files**: Log errors for corrupted or unreadable vector files and continue processing
- **Missing Components**: Handle vector files with missing auxiliary files gracefully
- **Container Access**: Handle inaccessible layers within container formats (GeoPackages, File Geodatabases, SpatiaLite)
- **Access Permissions**: Handle permission-denied errors gracefully

### Directory-Level Errors
- **Access Issues**: Log warnings for inaccessible subdirectories but continue processing
- **Empty Directories**: Handle directories with no vector files appropriately
- **Mixed Content**: Process available files when some are inaccessible

### Output Errors
- **Write Permissions**: Clear error messages for output directory permission issues
- **Disk Space**: Handle insufficient disk space errors
- **File Conflicts**: Proper handling of existing output files
- **Layer Name Conflicts**: Automatic resolution through duplicate handling

## Logging and Feedback

### Progress Reporting
- **File Discovery**: Report number of vector files found across all selected formats
- **Processing Progress**: Real-time progress updates showing current file/layer being processed
- **Success/Error Counts**: Running tally of successfully processed vs. failed files/layers
- **Duplicate Resolution**: Report when layer names are automatically adjusted for uniqueness

### Detailed Logging
- **Debug Information**: File paths, layer names, feature counts, table types (spatial vs non-spatial)
- **Container Enumeration**: Success/failure of layer discovery within container formats
- **Style Application**: Success/failure of QML style application
- **Duplicate Handling**: Log when layer names are modified to resolve conflicts
- **Error Details**: Specific error messages for troubleshooting

### Final Summary
- **Processing Statistics**: Total files/layers processed, errors encountered, duplicates resolved
- **Output Information**: Final GeoPackage location and layer count

## Implementation Requirements

### Code Structure
- **Class-Based**: Implement as a class inheriting from QgsProcessingAlgorithm
- **Modular Design**: Separate methods for file discovery, processing, and error handling
- **Version Control**: Include version information in the script header

### Testing Requirements
- **Unit Tests**: Create tests for core functionality including duplicate name handling
- **Integration Tests**: Test with various vector file configurations and container formats
- **Error Condition Tests**: Test error handling scenarios including layer name conflicts
- **Performance Tests**: Verify performance with large datasets and many duplicate names
- **Duplicate Handling Tests**: Verify correct behavior with multiple layers having identical base names

### Documentation Requirements
- **Inline Documentation**: Comprehensive docstrings and comments
- **User Documentation**: Clear help text in the algorithm description
- **Technical Documentation**: README with usage examples, troubleshooting, and duplicate handling behavior

## File Format Specifications

### Input Requirements
- **Multi-Format Support**: Support 10 vector formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, standalone dBase)
- **Container Formats**: Extract individual layers from GeoPackages, File Geodatabases, and SpatiaLite databases
- **Non-Spatial Tables**: Support attribute-only tables from container formats and standalone dBase files
- **Coordinate Systems**: Handle various coordinate reference systems across all formats
- **Geometry Types**: Support all OGR-supported geometry types

### Output Specifications
- **GeoPackage Standard**: Conform to OGC GeoPackage specification
- **SQLite Format**: Use SQLite database format with spatial extensions
- **Layer Organization**: Each vector source becomes a separate layer with unique naming
- **Duplicate Resolution**: Automatically resolve layer name conflicts with incrementing suffixes
- **Mixed Content**: Support both spatial layers and non-spatial tables in single output

## Quality Assurance

### Data Integrity
- **Geometry Validation**: Verify geometry preservation during conversion
- **Attribute Validation**: Ensure all attributes are correctly transferred
- **CRS Validation**: Verify coordinate reference system preservation

### Performance Validation
- **Processing Speed**: Reasonable processing times for various dataset sizes
- **Memory Usage**: Efficient memory management for large datasets
- **Output Size**: Verify GeoPackage file sizes are reasonable

This implementation follows the same technical standards as the ExtractStylesfromDirectoriesForStyleManager subproject, using only PyQGIS and Python standard library components.
