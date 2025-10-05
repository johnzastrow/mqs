# Requirements: Raster Files to GeoPackage Converter

## Core Functionality

### Primary Objective
Create a QGIS Processing Toolbox script that recursively searches directories for raster files and loads them into a GeoPackage with metadata preservation and optional style application.

### Supported Raster Formats
1. **GeoTIFF files** (.tif/.tiff) - Industry standard geospatial raster format
2. **ERDAS IMAGINE files** (.img) - ERDAS native raster format
3. **ENVI files** (.hdr) - ENVI header/data file pairs
4. **ASCII Grid files** (.asc) - Simple ASCII raster format
5. **ESRI Grid files** - ESRI's native grid format (ArcInfo Binary Grid)
6. **NetCDF files** (.nc) - Network Common Data Form, commonly used for climate data
7. **HDF files** (.hdf/.h4/.h5) - Hierarchical Data Format
8. **JPEG2000 files** (.jp2) - JPEG 2000 compressed format
9. **PNG files** (.png) - Portable Network Graphics
10. **JPEG files** (.jpg/.jpeg) - JPEG compressed images

### Key Features

#### File Discovery and Processing
- **Recursive Directory Search**: Automatically traverse directory trees to find all raster files
- **Format Selection**: Multi-select parameter allowing users to choose which raster file types to process
- **Pattern Matching**: Intelligent file discovery based on file extensions and format-specific patterns
- **Special Format Handling**: Support for complex formats like ESRI Grid (directory-based) and ENVI (header/data pairs)

#### Layer Naming System
- **Clean Name Generation**: Remove invalid characters, handle numbering, ensure SQLite compliance
- **Directory-Aware Naming**: 7 configurable strategies for incorporating directory structure:
  1. Filename only (backward compatibility)
  2. Parent directory + filename
  3. Last N directories + filename
  4. First N directories + filename
  5. Selected levels (comma-separated directory levels)
  6. Smart path (auto-detect important directories)
  7. Full relative path (truncated if needed)
- **Duplicate Resolution**: Automatic handling of naming conflicts with incrementing numbers
- **Length Management**: Respect SQLite 63-character identifier limits

#### Data Processing
- **Metadata Preservation**: Maintain original raster metadata during import
- **Coordinate System Handling**: Preserve projection and spatial reference information
- **Style Application**: Optional QML style file application for rasters with accompanying style files
- **Error Resilience**: Continue processing if individual files fail, with detailed error reporting

#### User Interface
- **QGIS Integration**: Native Processing Toolbox algorithm with standard QGIS parameter types
- **Multi-Select Controls**: Intuitive selection of raster file types and naming strategies
- **Dry Run Mode**: Preview layer names and configuration before actual processing
- **Progress Feedback**: Real-time processing updates and detailed logging

### Parameters Specification

#### Required Parameters
- **Input Directory**: Top-level directory containing raster files (Folder selection)
- **Output GeoPackage**: Path for output .gpkg file (File destination, optional in dry run mode)

#### Optional Parameters
- **Raster File Types**: Multi-select enum for choosing which formats to process (default: all selected)
- **Apply QML Styles**: Boolean for style file application (default: True)
- **Dry Run**: Boolean for preview mode without data processing (default: False)
- **Directory Naming Strategy**: Enum for layer naming approach (default: Filename only)
- **Directory Depth**: Integer for N-directory strategies (default: 2, range: 1-5)
- **Directory Levels**: String for selected levels strategy (default: "0,1")

### Processing Logic

#### File Discovery Algorithm
1. **Pattern Definition**: Create format-specific search patterns based on selected raster types
2. **Recursive Search**: Use Path.rglob() for efficient directory traversal
3. **Special Cases**: Handle ESRI Grid (look for w001001.adf in directories) and other complex formats
4. **Sorting**: Order by modification time (newest first) with fallback to alphabetical

#### Layer Name Generation
1. **Strategy Selection**: Apply chosen directory naming strategy
2. **Path Analysis**: Extract relevant directory components based on strategy
3. **Name Sanitization**: Clean invalid characters, handle edge cases
4. **Uniqueness**: Ensure no duplicate layer names within the GeoPackage
5. **Length Compliance**: Truncate if necessary while maintaining readability

#### Error Handling
- **File Access Errors**: Log and continue with remaining files
- **Invalid Formats**: Skip unreadable files with detailed error messages
- **Naming Conflicts**: Automatic resolution with fallback mechanisms
- **Style Failures**: Log style application issues without stopping processing

### Dry Run Functionality

#### Preview Capabilities
- **Layer Name Generation**: Show exactly what layer names would be created
- **Format Detection**: Display file types and processing approach
- **Strategy Summary**: Report selected naming strategy and configuration
- **Conflict Detection**: Identify potential duplicate names before processing

#### Output Format
```
================================================================================
DRY RUN RESULTS - Layer Name Preview
================================================================================
No.  | Original Path                                      | Layer Name
------------------------------------------------------------------------------------------
  1. | /data/2023/imagery/landsat_composite.tif          | imagery_landsat_composite (raster)
  2. | /data/2023/surfaces/elevation.img                 | surfaces_elevation (raster)
------------------------------------------------------------------------------------------
Total files that would be processed: 2
Unique layer names generated: 2
Directory naming strategy: Parent directory + filename
Note: This was a dry run. No data was processed.
================================================================================
```

### Technical Requirements

#### QGIS Integration
- **Version Compatibility**: QGIS 3.40 or higher
- **Processing Framework**: Native QgsProcessingAlgorithm implementation
- **Parameter Types**: Standard QGIS parameter classes (File, FileDestination, Boolean, Enum, Number, String)
- **Progress Reporting**: QgsProcessingFeedback integration

#### Dependencies
- **Core Libraries**: PyQGIS (included with QGIS installation)
- **Python Standard Library**: os, re, pathlib, typing
- **QGIS Classes**: QgsRasterLayer, QgsProject, QgsDataSourceUri

#### Performance Considerations
- **Memory Management**: Sequential file processing to handle large datasets
- **Progress Updates**: Regular feedback for long-running operations
- **Efficient Discovery**: Optimized file search patterns
- **Error Recovery**: Graceful handling of problematic files

### Future Enhancements

#### Planned Features
- **Raster Processing Implementation**: Complete the actual raster import functionality
- **Pyramid Generation**: Optional pyramid creation for large rasters
- **Compression Options**: User-configurable compression settings
- **Band Selection**: Support for multi-band raster processing
- **Resampling Options**: Configurable resampling methods
- **Nodata Handling**: Advanced nodata value management

#### Integration Possibilities
- **Batch Processing**: Support for multiple input directories
- **Template Styles**: Pre-defined style templates for common raster types
- **Statistics Generation**: Automatic raster statistics calculation
- **Validation Tools**: Raster integrity checking

### Success Criteria

#### Functional Requirements
- ✅ Discover all supported raster formats in directory trees
- ✅ Generate clean, unique layer names using configurable strategies
- ✅ Provide comprehensive dry run preview functionality
- ✅ Handle errors gracefully without stopping processing
- ✅ Integrate seamlessly with QGIS Processing Toolbox

#### Quality Requirements
- **Reliability**: Process hundreds of files without failure
- **Performance**: Handle large directories efficiently
- **Usability**: Intuitive interface with helpful parameter descriptions
- **Maintainability**: Clear code structure following QGIS patterns
- **Documentation**: Comprehensive user and developer documentation

#### User Experience
- **Clear Feedback**: Detailed progress and result reporting
- **Flexible Configuration**: Multiple naming strategies for different workflows
- **Preview Capability**: Test configurations before processing
- **Error Transparency**: Clear error messages and recovery suggestions