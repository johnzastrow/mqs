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


Discussion Points on incorporating directory structure into layer names:

> Give the script the ability to include directory names containing geodata into the table or layer names. suggest
ways in which this could happen.

● I'll analyze the current naming structure and suggest several approaches for incorporating directory names into
  layer/table names. Let me first examine the current implementation and then propose various strategies.

● Read(Scripts/vectors2gpkg.py)
  ⎿  Read 40 lines (ctrl+o to expand)

● Let me also look at the parameters to understand the current input structure:

● Read(Scripts/vectors2gpkg.py)
  ⎿  Read 15 lines (ctrl+o to expand)

● Now let me analyze the current structure and propose comprehensive strategies for incorporating directory names
  into layer names.

  📋 Analysis: Directory Name Incorporation Strategies

  Based on the current implementation, here are several comprehensive approaches for incorporating directory names
  into layer/table names:

  Current Naming Structure:

  - Regular files: filename → filename
  - Container layers: container_layername → container_layername
  - Current path context: Each file has full path available via Path objects

  ---
  Strategy 1: Immediate Parent Directory Prefix

  Approach: Add the immediate parent directory name as a prefix.

  Examples:
  Input: /data/boundaries/counties.shp
  Output: boundaries_counties

  Input: /data/ecology/wetlands/habitat.shp
  Output: wetlands_habitat

  Input: /data/2023/roads.gpkg:highways
  Output: 2023_roads_highways

  Implementation:
  - Extract vector_path.parent.name
  - Combine: f"{parent_dir}_{filename}"

  Pros:
  - Simple and predictable
  - Preserves immediate context
  - Short names

  Cons:
  - May lose broader context
  - Single parent may not be descriptive enough

  ---
  Strategy 2: Full Relative Path Integration

  Approach: Include the full relative path from the input root directory.

  Examples:
  Input Root: /data/
  File: /data/boundaries/admin/counties.shp
  Output: boundaries_admin_counties

  Input Root: /project/
  File: /project/2023/ecology/wetlands/species.gpx
  Output: 2023_ecology_wetlands_species

  Implementation:
  - Calculate relative path from input root
  - Replace path separators with underscores
  - Sanitize the full path

  Pros:
  - Preserves complete hierarchical context
  - Maintains organizational structure
  - Highly descriptive

  Cons:
  - Can create very long layer names
  - May exceed SQLite 63-character limit
  - Complex names for deeply nested files

  ---
  Strategy 3: Intelligent Path Truncation

  Approach: Include relevant path components but intelligently truncate to stay within limits.

  Examples:
  Input: /data/projects/watershed_study/2023/hydrology/streams.shp
  Options:
  - Last 2 dirs: 2023_hydrology_streams
  - Last 3 dirs: watershed_study_2023_hydrology_streams
  - Key terms: watershed_hydrology_streams

  Implementation:
  - Configurable depth (1, 2, 3+ directories)
  - Smart truncation at word boundaries
  - Priority to most specific directories

  Pros:
  - Balances context with brevity
  - User-configurable
  - Respects name length limits

  Cons:
  - Requires configuration decisions
  - May still lose important context

  ---
  Strategy 4: Semantic Directory Filtering

  Approach: Only include directories that appear to contain meaningful geodata context.

  Examples:
  Input: /home/user/Desktop/temp/projects/boundaries/counties.shp
  Filtered: boundaries_counties (skip /home/user/Desktop/temp/projects)

  Input: /data/gis/2023/Q1/ecology/wetlands.shp
  Filtered: 2023_ecology_wetlands (skip /data/gis, include meaningful dirs)

  Implementation:
  - Skip common non-semantic directories: home, user, Desktop, temp, data, gis, etc.
  - Include directories with meaningful names: years, project names, data types
  - Configurable skip/include patterns

  Pros:
  - Removes noise directories
  - Focuses on meaningful context
  - Produces cleaner names

  Cons:
  - Requires heuristics that may not always work
  - Complex logic
  - May skip important context

  ---
  Strategy 5: User-Configurable Naming Patterns

  Approach: Provide multiple naming pattern options via user interface.

  Options:
  1. Filename Only (current): roads
  2. Parent + Filename: boundaries_roads
  3. Last N Directories: admin_boundaries_roads
  4. Full Relative Path: data_2023_admin_boundaries_roads
  5. Smart Truncation: 2023_boundaries_roads

  Implementation:
  - Add new parameter: QgsProcessingParameterEnum for naming pattern
  - Implement multiple naming methods
  - Let user choose preferred approach

  Pros:
  - Maximum flexibility
  - Accommodates different use cases
  - User maintains control

  Cons:
  - More complex UI
  - Requires user decision-making
  - Multiple code paths to maintain

  ---
  Strategy 6: Year/Date Detection with Context

  Approach: Automatically detect and prioritize temporal and categorical directories.

  Examples:
  Input: /projects/environmental/2023/quarterly/Q3/boundaries/watersheds.shp
  Output: 2023_Q3_boundaries_watersheds

  Input: /legacy/shapefiles/historical/1990s/roads/highways.shp
  Output: 1990s_roads_highways

  Input: /current/admin/census/2020/demographics/population.gpkg:blocks
  Output: 2020_demographics_census_blocks

  Implementation:
  - Detect year patterns (1900-2099, "Q1", "2023-01", etc.)
  - Identify category terms (admin, ecology, infrastructure, etc.)
  - Prioritize temporal and categorical context

  Pros:
  - Automatically identifies important context
  - Handles temporal data well
  - Produces meaningful names

  Cons:
  - Complex pattern matching
  - May miss non-standard naming conventions
  - Heuristic-based approach

  ---
  Strategy 7: Hybrid Approach with Smart Defaults

  Approach: Combine multiple strategies with intelligent defaults and user override.

  Default Logic:
  1. Try semantic filtering first
  2. Fall back to last N directories (configurable)
  3. Ensure names stay under length limits
  4. Apply duplicate resolution

  User Options:
  - Directory Depth: 0 (none), 1, 2, 3, or "auto"
  - Include Patterns: Custom regex for important directories
  - Exclude Patterns: Custom regex for directories to skip
  - Max Length: Configurable limit (default 40, max 63)

  Examples:
  Auto mode: /data/projects/watershed/2023/hydrology/streams.shp
  → watershed_2023_hydrology_streams

  Depth=1: boundaries_counties
  Depth=2: admin_boundaries_counties
  Depth=3: 2023_admin_boundaries_counties

  Pros:
  - Flexible and powerful
  - Good defaults for most cases
  - Advanced users can customize
  - Handles edge cases

  Cons:
  - Most complex to implement
  - Requires extensive testing
  - More parameters to maintain

  ---
  Strategy 8: Container-Aware Hierarchical Naming

  Approach: Special handling for container formats to preserve both directory and internal structure.

  Examples:
  Regular file:
  /data/2023/boundaries/counties.shp → 2023_boundaries_counties

  GeoPackage:
  /data/2023/admin.gpkg:counties → 2023_admin_counties
  /data/2023/admin.gpkg:boundaries → 2023_admin_boundaries

  File Geodatabase:
  /data/ecology/wetlands.gdb:habitat → ecology_wetlands_habitat
  /data/ecology/wetlands.gdb:species → ecology_wetlands_species

  Implementation:
  - Different logic for regular files vs containers
  - Preserve container name + directory context
  - Maintain internal layer naming for containers

  Pros:
  - Respects different data source types
  - Preserves container organization
  - Maintains clarity between file and layer names

  Cons:
  - Requires format-specific logic
  - More complex naming rules
  - Different behaviors for different formats

  ---
  📊 Recommendation Summary

  I recommend implementing Strategy 7: Hybrid Approach with Smart Defaults because it:

  1. Provides flexibility for different user needs and directory structures
  2. Offers sensible defaults that work for most common scenarios
  3. Allows customization for advanced users with specific requirements
  4. Handles edge cases through multiple fallback mechanisms
  5. Maintains backward compatibility by making directory inclusion optional

  Proposed Implementation Parameters:

  # New parameters to add:
  DIRECTORY_NAMING = "DIRECTORY_NAMING"
  DIRECTORY_DEPTH = "DIRECTORY_DEPTH"
  DIRECTORY_MAX_LENGTH = "DIRECTORY_MAX_LENGTH"

  # In initParameters():
  self.addParameter(QgsProcessingParameterEnum(
      self.DIRECTORY_NAMING,
      "Directory naming strategy",
      options=[
          "Filename only (current behavior)",
          "Parent directory + filename",
          "Smart path (auto-detect important directories)",
          "Last N directories (configurable depth)",
          "Full relative path (truncated if needed)"
      ],
      defaultValue=1  # Parent directory + filename as sensible default
  ))

  self.addParameter(QgsProcessingParameterNumber(
      self.DIRECTORY_DEPTH,
      "Directory depth (when using 'Last N directories')",
      type=QgsProcessingParameterNumber.Integer,
      defaultValue=2,
      minValue=1,
      maxValue=5
  ))

  Would you like me to proceed with implementing this hybrid approach, or would you prefer to explore one of the
  other strategies in more detail?