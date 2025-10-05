# Raster Files to GeoPackage Converter

## ⚠️ PROJECT ABANDONED

**This subproject has been discontinued due to technical limitations of the GeoPackage specification for raster data storage.**

### Why This Project Was Abandoned

The GeoPackage specification's raster storage capabilities are designed primarily for **tile-based base layers** (like web map tiles), not for **analytical raster datasets**. Key limitations include:

1. **Tile-Focused Design**: GeoPackage rasters are stored as tiles optimized for web mapping and visualization, not scientific analysis
2. **Compression Limitations**: Limited support for lossless compression methods required for analytical datasets
3. **Bit-Depth Restrictions**: Poor support for high bit-depth rasters (16-bit, 32-bit floating point) commonly used in scientific analysis
4. **Performance Issues**: Inefficient for large analytical rasters that need to be processed as single continuous datasets
5. **Metadata Limitations**: Insufficient metadata support for complex scientific raster datasets

### Alternative Approaches

For consolidating and organizing raster datasets, consider these alternatives:

- **Keep original formats** (GeoTIFF, NetCDF, HDF) which are optimized for analytical workflows
- **Use SpatiaLite** for raster catalog management while keeping files in native formats
- **Implement file-based organization** with standardized directory structures and metadata files
- **Use dedicated raster databases** like PostGIS Raster for enterprise solutions

---

## Original Concept (Abandoned)

~~A QGIS Processing Toolbox script that recursively searches directories for raster files and loads them into a GeoPackage with metadata preservation and optional style application.~~

~~This tool simplifies the process of consolidating multiple raster files from complex directory structures into a single, well-organized GeoPackage file. It's particularly useful for:~~

- ~~Consolidating legacy raster file collections~~
- ~~Creating portable GIS datasets with raster data~~
- ~~Organizing scattered spatial imagery and surfaces~~
- ~~Migrating from file-based workflows to modern GeoPackage format~~

## Features

- **Recursive Processing**: Automatically finds all raster files in directory trees
- **Multiple Formats**: Supports 10 raster formats (GeoTIFF, ERDAS IMAGINE, ENVI, ASCII Grid, ESRI Grid, NetCDF, HDF, JPEG2000, PNG, JPEG)
- **User-Selectable Types**: Multi-select parameter for choosing which raster file types to process
- **Metadata Preservation**: Maintains original raster file metadata across all formats
- **Style Application**: Applies QML style files found alongside raster files (optional)
- **Smart Naming**: Generates clean layer names with invalid character replacement
- **Duplicate Handling**: Automatically resolves layer name collisions with incrementing numbers
- **Directory-Aware Layer Naming**: 7 configurable naming strategies for incorporating directory structure
- **Dry Run Mode**: Preview layer names without processing data
- **Error Handling**: Continues processing even if individual files fail
- **Progress Feedback**: Detailed progress reporting and error logging

## Installation

1. Copy `Scripts/rasters2gpkg.py` to your QGIS scripts directory
2. Restart QGIS or refresh the Processing Toolbox
3. Look for "Load Raster Files to GeoPackage" under "MQS Tools" in the Processing Toolbox

## Usage

### Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| **Input Directory** | Top-level directory containing raster files | Yes | - |
| **Output GeoPackage** | Path for the output .gpkg file | Yes | - |
| **Raster File Types** | Multi-select list of raster file types to process | No | All types |
| **Apply QML styles** | Apply .qml style files found alongside raster files | No | True |
| **Dry run** | Preview layer names without processing data (output path not required) | No | False |
| **Directory naming strategy** | Choose how directory names are incorporated into layer names | No | Filename only |
| **Directory depth** | Number of parent directories to include (for "Last N directories" and "First N directories" strategies) | No | 2 |
| **Directory levels** | Comma-separated directory level numbers (for "Selected levels" strategy) | No | "0,1" |

### Basic Workflow

1. Open QGIS and access the Processing Toolbox
2. Navigate to "MQS Tools" → "Load Raster Files to GeoPackage"
3. Select your input directory containing raster files
4. Choose which raster file types to process (or leave all selected)
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
   - Resulting layer names
   - File types
   - Naming strategy summary

**Example Dry Run Output:**
```
================================================================================
DRY RUN RESULTS - Layer Name Preview
================================================================================
No.  | Original Path                                      | Layer Name
------------------------------------------------------------------------------------------
  1. | /data/2023/imagery/landsat_composite.tif          | imagery_landsat_composite (raster)
  2. | /data/2023/surfaces/elevation.img                 | surfaces_elevation (raster)
  3. | /data/ecology/habitat_suitability.tif             | ecology_habitat_suitability (raster)
------------------------------------------------------------------------------------------
Total files that would be processed: 3
Unique layer names generated: 3
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
├── imagery/
│   ├── landsat_2023.tif
│   ├── landsat_2023.qml     # Optional style file
│   ├── sentinel_2023.tif
│   └── aerial_photo.jpg
├── surfaces/
│   ├── elevation.img
│   ├── slope.asc
│   └── aspect.hdr
└── climate/
    ├── temperature.nc
    └── precipitation.nc
```

**Result**: All raster files loaded into a single GeoPackage with clean layer names like `landsat_2023`, `sentinel_2023`, `elevation`, etc.

## Layer Naming

The script automatically generates clean layer names by:

1. Using the file name (without extension)
2. Replacing invalid characters with underscores
3. Ensuring names don't start with numbers
4. Removing excessive underscores
5. Limiting to 63 characters (SQLite identifier limit)
6. **Handling duplicates** by appending incrementing numbers

**Examples**:
- `my-data file.tif` → `my_data_file`
- `123elevation.img` → `layer_123elevation`
- `special$chars%.tif` → `special_chars_`

**Duplicate Handling**:
When multiple files would generate the same layer name, the script automatically handles this by appending incrementing numbers:
- First occurrence: `elevation` → `elevation`
- Second occurrence: `elevation` → `elevation_1`
- Third occurrence: `elevation` → `elevation_2`
- And so on...

This ensures no data is lost due to naming collisions and all layers are preserved in the final GeoPackage.

## Directory-Aware Layer Naming

The script offers flexible directory naming strategies to incorporate directory structure into layer names, providing better context and organization for your data.

### Naming Strategies

**1. Filename only (current behavior)**
- Default option for backward compatibility
- Uses only the file name without directory context
- Example: `/data/2023/imagery/landsat.tif` → `landsat`

**2. Parent directory + filename**
- Includes the immediate parent directory
- Good balance of context and brevity
- Example: `/data/2023/imagery/landsat.tif` → `imagery_landsat`

**3. Last N directories + filename**
- User-configurable depth (1-5 directories)
- Includes the last N directories in the path
- Example with depth=2: `/data/projects/watershed/2023/imagery/landsat.tif` → `2023_imagery_landsat`

**4. First N directories + filename**
- User-configurable depth (1-5 directories)
- Includes the first N directories from the top-level containing folder
- Example with depth=2: `/data/projects/watershed/2023/imagery/landsat.tif` → `data_projects_landsat`

**5. Selected levels (specify directory levels)**
- User-specified comma-separated directory level numbers
- Allows skipping levels and selecting non-contiguous directories
- Level 0 is the first directory after the input root, level 1 is the next, etc.
- Example with levels="0,3": `/data/projects/watershed/2023/imagery/landsat.tif` → `data_2023_landsat`

**6. Smart path (auto-detect important directories)**
- Automatically identifies meaningful directories
- Skips common non-semantic directories (`home`, `temp`, `data`, etc.)
- Prioritizes years (1900-2099), quarters (Q1-Q4), and project names
- Example: `/home/user/projects/satellite_study/2023/Q1/imagery/landsat.tif` → `satellite_study_2023_Q1_imagery_landsat`

**7. Full relative path (truncated if needed)**
- Includes complete path from input root directory
- Automatically truncated to respect SQLite 63-character limit
- Example: `/data/2023/projects/imagery/landsat.tif` → `2023_projects_imagery_landsat`

### Configuration Options

- **Directory Naming Strategy**: Choose from 7 naming approaches
- **Directory Depth**: When using "Last N directories" or "First N directories", specify how many directories to include (1-5)
- **Directory Levels**: When using "Selected levels", specify comma-separated directory level numbers (e.g., "0,2,4")
- **Automatic Sanitization**: Directory names are cleaned using the same rules as filenames
- **Length Management**: All strategies respect SQLite identifier limits

### Smart Path Detection Features

The smart path strategy includes intelligent filtering:

**Automatically Skipped Directories:**
- Common system paths: `home`, `user`, `users`, `desktop`, `documents`, `downloads`
- Generic data paths: `temp`, `tmp`, `data`, `gis`, `spatial`, `raster`, `files`
- Non-descriptive paths: `images`, `imagery`

**Automatically Prioritized Directories:**
- Years: `2023`, `2024`, `1995`, etc.
- Quarters/Periods: `Q1`, `Q2`, `quarter1`, `H1`, `half1`
- Meaningful project names (length > 2, not just numbers)

### Examples by Strategy

Given input file: `/projects/environmental_monitoring/2023/quarterly_reports/Q3/imagery/satellite_composite.tif`

| Strategy | Result |
|----------|---------|
| Filename only | `satellite_composite` |
| Parent directory | `imagery_satellite_composite` |
| Last 2 directories | `Q3_imagery_satellite_composite` |
| First 2 directories | `projects_environmental_satellite_composite` |
| Selected levels (0,2,4) | `projects_2023_imagery_satellite_composite` |
| Smart path | `environmental_monitoring_2023_Q3_imagery_satellite_composite` |
| Full relative path | `projects_environmental_monitoring_2023_quarterly_reports_Q3_imag...` |

## Style Application

When the "Apply QML styles" option is enabled, the script looks for `.qml` files with the same name as each raster file in the same directory. If found, the style is automatically applied to the corresponding layer in the GeoPackage.

**Example**:
- `landsat.tif` + `landsat.qml` → Style applied to `landsat` layer

## Raster File Type Selection

The script provides a multi-select parameter allowing you to choose which raster file types to process:

- **GeoTIFF files (.tif/.tiff)**: Industry standard raster format
- **ERDAS IMAGINE files (.img)**: ERDAS native format
- **ENVI files (.hdr)**: ENVI header/data file pairs
- **ASCII Grid files (.asc)**: Simple ASCII raster format
- **ESRI Grid files**: ESRI's native grid format (ArcInfo Binary Grid)
- **NetCDF files (.nc)**: Network Common Data Form, often used for climate data
- **HDF files (.hdf/.h4/.h5)**: Hierarchical Data Format
- **JPEG2000 files (.jp2)**: JPEG 2000 compressed format
- **PNG files (.png)**: Portable Network Graphics
- **JPEG files (.jpg/.jpeg)**: JPEG compressed images

By default, all types are selected. You can deselect specific types if you only want to process certain formats. This is useful when you have mixed directories and only want to consolidate specific file types.

**Example Use Cases**:
- Only process GeoTIFF and ERDAS IMAGINE files, ignoring JPEG images
- Extract only NetCDF climate data from a directory with mixed formats
- Process all formats except JPEG/PNG files to avoid loading photographs
- Load only scientific formats (NetCDF, HDF, ENVI) and exclude common image formats

## Error Handling and Data Safety

The script is designed to be robust and ensure no data loss:

- **Individual File Errors**: If one raster file fails to load, processing continues with the remaining files
- **Directory Access**: Warns about inaccessible directories but continues processing
- **Layer Name Conflicts**: Automatically resolves duplicate layer names without user intervention
- **Data Preservation**: Ensures all layers are preserved even when naming conflicts occur
- **Style Application**: Logs style application failures but doesn't stop processing
- **Detailed Logging**: All errors and warnings are reported in the QGIS log

## Performance Considerations

- **Large Files**: The script processes files sequentially to manage memory usage
- **Progress Updates**: Real-time progress reporting for long-running operations
- **Dry Run**: Use dry run mode to test configurations before processing large datasets

## Technical Requirements

- **QGIS Version**: 3.40 or higher
- **Dependencies**: PyQGIS (included with QGIS)
- **File Formats**: Input raster files (GeoTIFF, IMG, NetCDF, etc.), output GeoPackage
- **Operating System**: Cross-platform (Windows, macOS, Linux)

## Troubleshooting

### Common Issues

**No raster files found**
- Check that the input directory contains supported raster files (.tif, .img, .nc, etc.)
- Verify directory permissions
- Ensure the directory path is correct

**Write errors**
- Check output directory permissions
- Ensure sufficient disk space
- Verify the output path is valid

**Style application failures**
- Ensure QML files are valid
- Check that QML files match raster file names exactly
- Verify QML files are in the same directory as raster files

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