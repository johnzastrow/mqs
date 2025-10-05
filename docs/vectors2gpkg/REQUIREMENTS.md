# Vector Files to GeoPackage Converter - Requirements

## Project Overview

Create a PyQGIS script for the QGIS Processing Toolbox that recursively searches a directory tree for vector files and consolidates them into a single GeoPackage with metadata preservation and optional style application.

## Core Functionality

### Input Processing
- **Directory Scanning**: Recursively search through all subdirectories starting from a user-specified top-level directory
- **File Discovery**: Identify all `.shp` files in the directory tree
- **Validation**: Verify that each shapefile is valid and can be loaded

### Output Generation
- **GeoPackage Creation**: Create a single `.gpkg` file containing all processed shapefiles as separate layers
- **Layer Management**: Handle multiple layers within a single GeoPackage file
- **Spatial Indexing**: Create spatial indexes for each layer to optimize query performance

### Data Preservation
- **Geometry Preservation**: Maintain all geometric data from source shapefiles
- **Attribute Preservation**: Preserve all attribute data and field types
- **Metadata Preservation**: Retain coordinate reference systems and other spatial metadata
- **Feature Integrity**: Ensure no data loss during the conversion process

### Layer Naming
- **Name Derivation**: Generate layer names from shapefile names (without file extension)
- **Character Sanitization**: Replace invalid characters with underscores
- **Naming Rules**:
  - Replace any non-alphanumeric characters (except underscores) with underscores
  - Ensure layer names don't start with numbers (prefix with "layer_" if needed)
  - Remove consecutive underscores and leading/trailing underscores
  - Limit names to 63 characters (SQLite identifier limit)
  - Handle empty names with fallback to "unnamed_layer"

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
   - Description: "Top-level directory containing shapefiles"
   - Validation: Must be an existing, readable directory

2. **Output GeoPackage** (`QgsProcessingParameterFileDestination`)
   - Description: "Path for the output .gpkg file"
   - File Filter: "GeoPackage files (*.gpkg)"
   - Validation: Must be a writable location

### Optional Parameters
3. **Apply QML Styles** (`QgsProcessingParameterBoolean`)
   - Description: "Apply QML style files if found alongside shapefiles"
   - Default: True

4. **Create Spatial Indexes** (`QgsProcessingParameterBoolean`)
   - Description: "Create spatial indexes for each layer"
   - Default: True

## Error Handling Requirements

### File-Level Errors
- **Invalid Shapefiles**: Log errors for corrupted or unreadable shapefiles and continue processing
- **Missing Components**: Handle shapefiles with missing .dbf, .shx, or .prj files
- **Access Permissions**: Handle permission-denied errors gracefully

### Directory-Level Errors
- **Access Issues**: Log warnings for inaccessible subdirectories but continue processing
- **Empty Directories**: Handle directories with no shapefiles appropriately

### Output Errors
- **Write Permissions**: Clear error messages for output directory permission issues
- **Disk Space**: Handle insufficient disk space errors
- **File Conflicts**: Proper handling of existing output files

## Logging and Feedback

### Progress Reporting
- **File Discovery**: Report number of shapefiles found
- **Processing Progress**: Real-time progress updates showing current file being processed
- **Success/Error Counts**: Running tally of successfully processed vs. failed files

### Detailed Logging
- **Debug Information**: File paths, layer names, feature counts
- **Style Application**: Success/failure of QML style application
- **Error Details**: Specific error messages for troubleshooting

### Final Summary
- **Processing Statistics**: Total files processed, errors encountered
- **Output Information**: Final GeoPackage location and layer count

## Implementation Requirements

### Code Structure
- **Class-Based**: Implement as a class inheriting from QgsProcessingAlgorithm
- **Modular Design**: Separate methods for file discovery, processing, and error handling
- **Version Control**: Include version information in the script header

### Testing Requirements
- **Unit Tests**: Create tests for core functionality
- **Integration Tests**: Test with various shapefile configurations
- **Error Condition Tests**: Test error handling scenarios
- **Performance Tests**: Verify performance with large datasets

### Documentation Requirements
- **Inline Documentation**: Comprehensive docstrings and comments
- **User Documentation**: Clear help text in the algorithm description
- **Technical Documentation**: README with usage examples and troubleshooting

## File Format Specifications

### Input Requirements
- **Shapefile Components**: Support complete shapefiles (.shp, .dbf, .shx, .prj)
- **Coordinate Systems**: Handle various coordinate reference systems
- **Geometry Types**: Support all OGR-supported shapefile geometry types

### Output Specifications
- **GeoPackage Standard**: Conform to OGC GeoPackage specification
- **SQLite Format**: Use SQLite database format with spatial extensions
- **Layer Organization**: Each shapefile becomes a separate layer in the GeoPackage

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
