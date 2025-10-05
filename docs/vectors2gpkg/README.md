# Vector Files to GeoPackage Converter

A QGIS Processing Toolbox script that recursively searches directories for vector files and loads them into a GeoPackage with metadata preservation and optional style application.

## Overview

This tool simplifies the process of consolidating multiple vector files from complex directory structures into a single, well-organized GeoPackage file. It's particularly useful for:

- Consolidating legacy vector file collections
- Creating portable GIS datasets
- Organizing scattered spatial data
- Migrating from file-based workflows to modern GeoPackage format

## Features

- **Recursive Processing**: Automatically finds all vector files in directory trees
- **Multiple Formats**: Supports 10 vector formats (shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, standalone dBase)
- **Container Format Support**: Extracts individual layers from GeoPackages, File Geodatabases, and SpatiaLite databases
- **Non-Spatial Tables**: Loads attribute-only tables from container formats and standalone dBase files
- **User-Selectable Types**: Multi-select parameter for choosing which vector file types to process
- **Spatial Indexing**: Creates spatial indexes for optimal performance (optional)
- **Metadata Preservation**: Maintains original vector file metadata across all formats
- **Style Application**: Applies QML style files found alongside vector files (optional)
- **Smart Naming**: Generates clean layer names with invalid character replacement
- **Duplicate Handling**: Automatically resolves layer name collisions with incrementing numbers
- **Error Handling**: Continues processing even if individual files fail
- **Progress Feedback**: Detailed progress reporting and error logging

## Installation

1. Copy `Scripts/vectors2gpkg.py` to your QGIS scripts directory
2. Restart QGIS or refresh the Processing Toolbox
3. Look for "Load Vector Files to GeoPackage" under "MQS Tools" in the Processing Toolbox

## Usage

### Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| **Input Directory** | Top-level directory containing vector files | Yes | - |
| **Output GeoPackage** | Path for the output .gpkg file | Yes | - |
| **Vector File Types** | Multi-select list of vector file types to process | No | All types |
| **Apply QML styles** | Apply .qml style files found alongside vector files | No | True |
| **Create spatial indexes** | Create spatial indexes for each layer | No | True |
| **Dry run** | Preview layer names without processing data (output path not required) | No | False |
| **Directory naming strategy** | Choose how directory names are incorporated into layer names | No | Filename only |
| **Directory depth** | Number of parent directories to include (for "Last N directories" strategy) | No | 2 |

### Basic Workflow

1. Open QGIS and access the Processing Toolbox
2. Navigate to "MQS Tools" → "Load Vector Files to GeoPackage"
3. Select your input directory containing vector files
4. Choose which vector file types to process (or leave all selected)
5. Choose output location for the GeoPackage
6. Configure other options as needed
7. Click "Run"

### Dry Run Mode

Before processing large datasets, use dry run mode to preview the layer names that would be generated:

1. **Enable dry run**: Check the "Dry run" option in the parameters
2. **Optional output**: Output GeoPackage path is not required in dry run mode
3. **Configure naming**: Set your preferred directory naming strategy and depth
4. **Preview results**: The script will display a formatted table showing:
   - Original file paths
   - Resulting layer/table names
   - File/layer types
   - Naming strategy summary

**Example Dry Run Output:**
```
================================================================================
DRY RUN RESULTS - Layer Name Preview
================================================================================
No.  Original Path                                      Layer/Table Name
--------------------------------------------------------------------------------
  1. /data/2023/boundaries/counties.shp                boundaries_counties (vector file)
  2. /data/2023/boundaries/states.geojson              boundaries_states (vector file)
  3. /data/2023/admin.gpkg:districts                   2023_admin_districts (container layer)
  4. /data/ecology/standalone_codes.dbf                ecology_standalone_codes (dBase table)
--------------------------------------------------------------------------------
Total files that would be processed: 4
Unique layer names generated: 4
Directory naming strategy: Parent directory + filename
Note: This was a dry run. No data was processed.
================================================================================
```

**Dry Run Benefits:**
- **Test naming strategies** before processing
- **Identify potential conflicts** in layer names
- **Preview results** for complex directory structures
- **No data processing** - fast execution
- **Refine settings** based on preview results

### Example Directory Structure

```
my_data/
├── boundaries/
│   ├── counties.shp
│   ├── counties.qml     # Optional style file
│   ├── states.geojson
│   ├── districts.kml
│   ├── legacy_data.gpkg # Existing GeoPackage with multiple layers
│   └── codes.dbf        # Standalone dBase table
├── ecology/
│   ├── wetlands.shp
│   ├── habitats.gpx
│   └── spatial_data.gdb/ # File Geodatabase directory
│       ├── species.gdb
│       └── [other gdb files]
└── infrastructure/
    ├── roads.shp
    ├── roads.dbf        # Part of shapefile (ignored)
    └── utilities.gml
```

**Result**: All vector files loaded into a single GeoPackage with clean layer names like `counties`, `states`, `districts`, `wetlands`, etc. Layers from containers are copied with prefixed names:
- `legacy_data.gpkg` layers → `legacy_data_roads`, `legacy_data_buildings`
- `spatial_data.gdb` features → `spatial_data_species`, `spatial_data_habitats`
- Standalone `codes.dbf` → `codes` (non-spatial table)

## Layer Naming

The script automatically generates clean layer names by:

1. Using the file name (without extension)
2. Replacing invalid characters with underscores
3. Ensuring names don't start with numbers
4. Removing excessive underscores
5. Limiting to 63 characters (SQLite identifier limit)
6. **Handling duplicates** by appending incrementing numbers

**Examples**:
- `my-data file.shp` → `my_data_file`
- `123roads.shp` → `layer_123roads`
- `special$chars%.shp` → `special_chars_`

**Duplicate Handling**:
When multiple files would generate the same layer name, the script automatically handles this by appending incrementing numbers:
- First occurrence: `roads` → `roads`
- Second occurrence: `roads` → `roads_1`
- Third occurrence: `roads` → `roads_2`
- And so on...

This ensures no data is lost due to naming collisions and all layers are preserved in the final GeoPackage.

## Directory-Aware Layer Naming

The script offers flexible directory naming strategies to incorporate directory structure into layer names, providing better context and organization for your data.

### Naming Strategies

**1. Filename only (current behavior)**
- Default option for backward compatibility
- Uses only the file name without directory context
- Example: `/data/2023/boundaries/counties.shp` → `counties`

**2. Parent directory + filename**
- Includes the immediate parent directory
- Good balance of context and brevity
- Example: `/data/2023/boundaries/counties.shp` → `boundaries_counties`

**3. Last N directories + filename**
- User-configurable depth (1-5 directories)
- Includes the last N directories in the path
- Example with depth=2: `/data/projects/watershed/2023/hydrology/streams.shp` → `2023_hydrology_streams`

**4. Smart path (auto-detect important directories)**
- Automatically identifies meaningful directories
- Skips common non-semantic directories (`home`, `temp`, `data`, etc.)
- Prioritizes years (1900-2099), quarters (Q1-Q4), and project names
- Example: `/home/user/projects/watershed_study/2023/Q1/boundaries/counties.shp` → `watershed_study_2023_Q1_boundaries_counties`

**5. Full relative path (truncated if needed)**
- Includes complete path from input root directory
- Automatically truncated to respect SQLite 63-character limit
- Example: `/data/2023/admin/boundaries/counties.shp` → `2023_admin_boundaries_counties`

### Configuration Options

- **Directory Naming Strategy**: Choose from 5 naming approaches
- **Directory Depth**: When using "Last N directories", specify how many parent directories to include (1-5)
- **Automatic Sanitization**: Directory names are cleaned using the same rules as filenames
- **Length Management**: All strategies respect SQLite identifier limits

### Smart Path Detection Features

The smart path strategy includes intelligent filtering:

**Automatically Skipped Directories:**
- Common system paths: `home`, `user`, `users`, `desktop`, `documents`, `downloads`
- Generic data paths: `temp`, `tmp`, `data`, `gis`, `spatial`, `vector`, `files`
- Non-descriptive paths: `shapefiles`, `geodata`

**Automatically Prioritized Directories:**
- Years: `2023`, `2024`, `1995`, etc.
- Quarters/Periods: `Q1`, `Q2`, `quarter1`, `H1`, `half1`
- Meaningful project names (length > 2, not just numbers)

### Examples by Strategy

Given input file: `/projects/environmental_monitoring/2023/quarterly_reports/Q3/water_quality/monitoring_stations.shp`

| Strategy | Result |
|----------|---------|
| Filename only | `monitoring_stations` |
| Parent directory | `water_quality_monitoring_stations` |
| Last 2 directories | `Q3_water_quality_monitoring_stations` |
| Smart path | `environmental_monitoring_2023_Q3_water_quality_monitoring_stations` |
| Full relative path | `projects_environmental_monitoring_2023_quarterly_reports_Q3_water_q...` |

### Container Format Support

Directory naming works with all container formats:

**GeoPackage Example:**
- Input: `/data/2023/admin/boundaries.gpkg:counties`
- Parent directory strategy: `admin_boundaries_counties`

**File Geodatabase Example:**
- Input: `/projects/hydrology/watersheds.gdb:stream_network`
- Smart path strategy: `hydrology_watersheds_stream_network`

## Style Application

When the "Apply QML styles" option is enabled, the script looks for `.qml` files with the same name as each vector file in the same directory. If found, the style is automatically applied to the corresponding layer in the GeoPackage.

**Example**:
- `counties.shp` + `counties.qml` → Style applied to `counties` layer

## Vector File Type Selection

The script provides a multi-select parameter allowing you to choose which vector file types to process:

- **Shapefiles (.shp)**: Traditional ESRI shapefiles
- **GeoJSON (.geojson/.json)**: JSON-based vector format
- **KML files (.kml/.kmz)**: Google Earth format (including compressed KMZ)
- **GPX files (.gpx)**: GPS exchange format
- **GML files (.gml)**: Geography Markup Language
- **GeoPackage files (.gpkg)**: OGC GeoPackage format
- **File Geodatabases (.gdb)**: ESRI File Geodatabase format
- **SpatiaLite databases (.sqlite/.db)**: SQLite spatial database format
- **MapInfo files (.tab/.mif)**: MapInfo native formats
- **Standalone dBase files (.dbf)**: dBase tables without corresponding shapefiles

By default, all types are selected. You can deselect specific types if you only want to process certain formats. This is useful when you have mixed directories and only want to consolidate specific file types.

**Example Use Cases**:
- Only process shapefiles and GeoJSON files, ignoring KML files
- Extract only GeoPackage layers from a directory with mixed formats
- Process all formats except GPX files
- Load only File Geodatabase layers and standalone dBase tables
- Exclude dBase files to avoid loading attribute-only data

## GeoPackage Input Support

When GeoPackage files are found in the input directory, the script will:

1. **Enumerate All Tables**: Detect both spatial layers and non-spatial tables within each GeoPackage
2. **Copy All Content**: Copy each layer and table individually to the output GeoPackage
3. **Preserve Data Types**: Maintain spatial geometry for layers and attribute-only structure for tables
4. **Preserve Layer Names**: Maintain original layer/table names with source file prefix
5. **Handle Errors**: Continue processing if some layers cannot be accessed

**Layer Naming for GeoPackage Sources**:
- Input: `legacy_data.gpkg` with spatial layers `roads`, `buildings` and non-spatial table `codes`
- Output: `legacy_data_roads` (spatial), `legacy_data_buildings` (spatial), `legacy_data_codes` (non-spatial table)

## File Geodatabase Input Support

When File Geodatabase (.gdb) directories are found in the input directory, the script will:

1. **Enumerate All Content**: Detect both feature classes (spatial) and tables (non-spatial) within each File Geodatabase
2. **Copy All Content**: Copy each feature class and table individually to the output GeoPackage
3. **Preserve Data Types**: Maintain spatial geometry for feature classes and attribute-only structure for tables
4. **Preserve Names**: Maintain original feature class/table names with source database prefix
5. **Handle Errors**: Continue processing if some feature classes or tables cannot be accessed

**Layer Naming for File Geodatabase Sources**:
- Input: `spatial_data.gdb` with feature classes `parcels`, `utilities` and table `lookup_codes`
- Output: `spatial_data_parcels` (spatial), `spatial_data_utilities` (spatial), `spatial_data_lookup_codes` (non-spatial table)

## SpatiaLite Database Input Support

When SpatiaLite database files (.sqlite/.db) are found in the input directory, the script will:

1. **Enumerate All Tables**: Detect both spatial tables and non-spatial tables within each SpatiaLite database
2. **Copy All Content**: Copy each spatial table and attribute table individually to the output GeoPackage
3. **Preserve Data Types**: Maintain spatial geometry for tables with geometry and attribute-only structure for non-spatial tables
4. **Preserve Table Names**: Maintain original table names with source database prefix
5. **Handle Errors**: Continue processing if some tables cannot be accessed

**Layer Naming for SpatiaLite Sources**:
- Input: `survey_data.sqlite` with spatial tables `points`, `boundaries` and non-spatial table `metadata`
- Output: `survey_data_points` (spatial), `survey_data_boundaries` (spatial), `survey_data_metadata` (non-spatial table)

## Standalone dBase File Support

The script automatically detects and processes standalone dBase (.dbf) files - those that exist without a corresponding shapefile (.shp) of the same name in the same directory.

**Key Features**:
1. **Automatic Detection**: Identifies dBase files that are not part of a shapefile set
2. **Non-Spatial Loading**: Loads as attribute-only tables (no geometry column)
3. **Table Preservation**: Maintains all field definitions and data types
4. **Proper Integration**: Tables are properly integrated into the GeoPackage structure

**Use Cases**:
- Lookup tables and reference data
- Attribute tables from legacy systems
- Statistical data without spatial component
- Supplementary data for joining with spatial layers

**Example**:
- Directory contains: `roads.shp`, `roads.dbf`, `codes.dbf`
- Result: `roads` layer (spatial) and `codes` table (non-spatial) in GeoPackage
- The `roads.dbf` is ignored as it's part of the shapefile set

## Error Handling and Data Safety

The script is designed to be robust and ensure no data loss:

- **Individual File Errors**: If one vector file fails to load, processing continues with the remaining files
- **Directory Access**: Warns about inaccessible directories but continues processing
- **Layer Name Conflicts**: Automatically resolves duplicate layer names without user intervention
- **Data Preservation**: Ensures all layers are preserved even when naming conflicts occur
- **Style Application**: Logs style application failures but doesn't stop processing
- **Detailed Logging**: All errors and warnings are reported in the QGIS log

## Performance Considerations

- **Spatial Indexes**: Enabled by default for optimal query performance
- **Large Files**: The script processes files sequentially to manage memory usage
- **Progress Updates**: Real-time progress reporting for long-running operations

## Technical Requirements

- **QGIS Version**: 3.40 or higher
- **Dependencies**: PyQGIS (included with QGIS)
- **File Formats**: Input vector files (shapefiles, GeoJSON, KML, etc.), output GeoPackage
- **Operating System**: Cross-platform (Windows, macOS, Linux)

## Troubleshooting

### Common Issues

**No vector files found**
- Check that the input directory contains supported vector files (.shp, .geojson, .kml, etc.)
- Verify directory permissions
- Ensure the directory path is correct

**Write errors**
- Check output directory permissions
- Ensure sufficient disk space
- Verify the output path is valid

**Style application failures**
- Ensure QML files are valid
- Check that QML files match vector file names exactly
- Verify QML files are in the same directory as vector files

### Debug Information

Enable debug logging in QGIS Processing options to see detailed information about:
- Files being processed
- Layer loading details
- Style application attempts
- Error details

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## License

This project is licensed under the MIT License - see the main repository license for details.

## Contributing

This is part of the MQS (My QGIS Stuff) collection. See the main repository documentation for contribution guidelines.