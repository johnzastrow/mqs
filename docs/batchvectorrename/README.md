# Batch Vector Layer Rename Tool

A QGIS Processing Toolbox script that recursively scans directories for vector files and allows batch renaming of layers in vector files and databases that support layer renaming.

## Overview

This tool provides a comprehensive solution for batch renaming vector layers across entire directory structures. It recursively scans directories, processes multiple vector file formats, and applies consistent renaming operations across all found layers. It's particularly useful for:

- Standardizing layer naming conventions across entire directory trees
- Adding organizational prefixes or suffixes to layer names
- Cleaning up layer names by removing invalid characters
- Applying consistent case formatting to layer names
- Bulk find-and-replace operations on layer names
- Trimming unwanted characters from the beginning or end of layer names
- Processing mixed collections of vector file types with selective filtering
- Migrating legacy datasets with inconsistent naming schemes

## Supported Formats

### 🟢 **Full Layer Renaming Support**

#### **GeoPackage (.gpkg)**
- **Method**: Direct SQL table renaming with metadata updates
- **Features**: Full rename support, preserves all metadata and indexes
- **Safety**: Atomic transactions with rollback capability

#### **SpatiaLite (.sqlite/.db)**
- **Method**: Direct SQL table renaming
- **Features**: Full rename support for spatial tables
- **Safety**: Atomic transactions with rollback capability

### 🟡 **File-Based Renaming**

#### **Shapefiles (.shp)**
- **Method**: Rename all component files (.shp, .shx, .dbf, .prj, etc.)
- **Features**: Renames the entire shapefile set
- **Limitation**: Single layer per file (filename becomes layer name)

#### **Single-Layer File Formats**
- **GeoJSON (.geojson/.json)**: File renaming (filename becomes layer name)
- **KML/KMZ (.kml/.kmz)**: File renaming with support for compressed KMZ
- **GPX (.gpx)**: File renaming for GPS exchange format
- **GML (.gml)**: File renaming for Geography Markup Language
- **MapInfo (.tab/.mif)**: File renaming for MapInfo formats

### 🔴 **Limited/Unsupported**

#### **File Geodatabase (.gdb)**
- **Status**: Limited support (mostly read-only without ESRI tools)
- **Recommendation**: Export to GeoPackage for renaming, then reimport if needed

## Features

- **Recursive Directory Scanning**: Automatically processes entire directory trees
- **Multi-Format Support**: Handles 9 different vector file formats
- **Selective File Type Processing**: Choose which vector formats to process
- **9 Rename Operations**: Comprehensive set of rename strategies including Replace and Trim
- **Dry Run Mode**: Preview all changes before applying them
- **Automatic Backup**: Optional backup creation before making changes
- **Conflict Detection**: Prevents duplicate layer names with automatic resolution
- **Name Validation**: Ensures database-compatible layer names
- **Comprehensive Logging**: Detailed operation and error logging via QgsMessageLog
- **Progress Feedback**: Real-time progress reporting with detailed operation status
- **Error Recovery**: Rollback capability and backup restoration guidance
- **Batch Processing**: Process hundreds of files and layers in a single operation

## Installation

1. Copy `Scripts/batchvectorrename.py` to your QGIS scripts directory
2. Restart QGIS or refresh the Processing Toolbox
3. Look for "Batch Vector Layer Rename" under "MQS Tools" in the Processing Toolbox

## Usage

### Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| **Input Directory** | Directory to scan recursively for vector files | Yes | - |
| **Vector File Types** | Multi-select list of vector file types to process | No | All types |
| **Rename Operation** | Choose the type of rename operation to apply | Yes | Replace text |
| **Find Text** | Text to find in layer names (for Replace operation) | No* | - |
| **Replace Text** | Text to replace with (leave empty to remove text) | No* | - |
| **Trim Position** | Position to trim from (Beginning or End) | No* | Beginning |
| **Trim Count** | Number of characters to trim | No* | 1 |
| **Custom Prefix** | Text to add to beginning of layer names | No* | - |
| **Custom Suffix** | Text to add to end of layer names | No* | - |
| **Dry Run** | Preview changes without applying them | No | True |
| **Create Backups** | Create backup copies before renaming | No | True |

*Required for specific operations

### Rename Operations

#### **1. Replace Text (Find and Replace)**
- Finds and replaces specific text in layer names
- **Special Feature**: Leave "Replace Text" empty to remove text completely
- Example: `old_data_layer` → `new_data_layer` (find "old", replace with "new")
- Example: `temp_layer_name` → `layer_name` (find "temp_", replace with empty)
- **Required Parameters**: Find Text

#### **2. Trim Beginning**
- Removes specified number of characters from the start of layer names
- Example: `prefix_layer_name` → `layer_name` (trim 7 characters)
- **Required Parameters**: Trim Count

#### **3. Trim End**
- Removes specified number of characters from the end of layer names
- Example: `layer_name_suffix` → `layer_name` (trim 7 characters)
- **Required Parameters**: Trim Count

#### **4. Add Prefix**
- Adds custom text to the beginning of all layer names
- Example: `counties` → `2023_counties` (with prefix "2023_")
- **Required Parameter**: Custom Prefix

#### **5. Add Suffix**
- Adds custom text to the end of all layer names
- Example: `roads` → `roads_final` (with suffix "_final")
- **Required Parameter**: Custom Suffix

#### **6. Clean Names**
- Removes invalid characters and standardizes naming
- Replaces special characters with underscores
- Ensures names don't start with numbers
- Example: `my-layer name!` → `my_layer_name`

#### **7. Convert to Lowercase**
- Converts all layer names to lowercase
- Example: `MyLayer` → `mylayer`

#### **8. Convert to Uppercase**
- Converts all layer names to uppercase
- Example: `MyLayer` → `MYLAYER`

#### **9. Convert to Title Case**
- Converts layer names to Title Case
- Example: `my_layer_name` → `My_Layer_Name`

### Basic Workflow

1. Open QGIS and access the Processing Toolbox
2. Navigate to "MQS Tools" → "Batch Vector Layer Rename (Recursive)"
3. Select your input directory to scan recursively
4. Choose which vector file types to process (or leave all selected)
5. Select a rename operation
6. Configure operation-specific parameters (find/replace text, trim count, prefix, suffix)
7. **Enable dry run** to preview changes (recommended)
8. Click "Run" to see the rename plan for all found layers
9. If satisfied, **disable dry run** and run again to apply changes

### Dry Run Mode (Recommended)

Always use dry run mode first to preview changes:

**Example Dry Run Output:**
```
Scanning directory recursively: C:\GIS_Data\Projects
Found 25 vector files to process
Found 47 renameable layers across all files

====================================================================================================
RENAME PLAN - Layer Name Changes
====================================================================================================
File                                     | Original Name             | New Name
----------------------------------------------------------------------------------------------------
data_2023.gpkg                          | temp_counties             | counties
data_2023.gpkg                          | temp_roads                | roads
legacy_shapefiles.shp                   | temp_boundaries           | boundaries
project_data.sqlite                     | temp_hydrology            | hydrology
----------------------------------------------------------------------------------------------------
Total layers to rename: 4

Dry run mode - no changes were applied.
Set 'Dry run' to False to apply these changes.
```

### Safety Features

#### **Automatic Backup**
- Creates timestamped backup before making changes
- Backup naming: `filename_backup_YYYYMMDD_HHMMSS.ext`
- For shapefiles: backs up all component files
- For directories (like .gdb): creates complete directory copy

#### **Validation and Conflict Detection**
- **Automatic duplicate resolution**: Prevents creation of duplicate layer names with incremental numbering
- **Conflict resolution system**: When rename operations would create duplicates, automatically appends `_1`, `_2`, `_3`, etc.
- **Database constraint compliance**: GeoPackage and SpatiaLite require unique layer names - conflicts would cause SQL errors
- **Predictable naming pattern**: Uses consistent incremental numbering for reliable results
- **Dry run conflict preview**: Shows potential conflicts before applying changes, allowing strategy adjustment
- Validates layer names for database compatibility
- Limits names to 63 characters (SQLite identifier limit)
- Sanitizes invalid characters

#### **Error Recovery**
- Database operations use atomic transactions
- Rollback capability if any operation fails
- Backup files available for manual restoration

## Examples

### Example 1: Removing Temporary Prefixes from Multiple Files

**Directory Structure:**
```
C:\GIS_Data\
├── project_data.gpkg (layers: temp_counties, temp_roads)
├── legacy\
│   ├── temp_boundaries.shp
│   └── temp_hydrology.geojson
└── archives\
    └── spatial.sqlite (layers: temp_utilities, temp_zones)
```

**Operation**: Replace Text
**Find**: `temp_`
**Replace**: `` (empty - removes the text)

**Result:** All "temp_" prefixes removed from all layers across all files
- `temp_counties` → `counties`
- `temp_roads` → `roads`
- `temp_boundaries.shp` → `boundaries.shp`
- `temp_hydrology.geojson` → `hydrology.geojson`
- `temp_utilities` → `utilities`
- `temp_zones` → `zones`

### Example 2: Trimming Unwanted Characters

**Input layers with 8-character date prefixes to remove:**
- `20231015_counties`
- `20231015_roads`
- `20231015_boundaries`

**Operation**: Trim Beginning
**Trim Count**: `9` (8 digits + underscore)

**Result:**
- `counties`
- `roads`
- `boundaries`

### Example 3: Adding Project Prefixes to Mixed File Types

**Directory with mixed vector formats:**
```
C:\ProjectAlpha\
├── data.gpkg (layers: counties, roads)
├── boundaries.shp
├── points.geojson
└── tracks.gpx
```

**Operation**: Add Prefix
**Prefix**: `alpha_`
**File Types**: Select only GeoPackage and Shapefile

**Result:** Only selected file types processed
- GeoPackage layers: `alpha_counties`, `alpha_roads`
- Shapefile: `alpha_boundaries.shp`
- GeoJSON and GPX files ignored

### Example 4: Comprehensive Directory Processing

**Large directory structure with 200+ files:**
```
C:\GIS_Archive\
├── 2020\projects\*.gpkg (50 files, 200 layers)
├── 2021\data\*.shp (75 files)
├── 2022\exports\*.geojson (80 files)
└── legacy\*.sqlite (25 files, 150 layers)
```

**Operation**: Replace Text
**Find**: `legacy_data_`
**Replace**: `` (remove)
**Vector Types**: All selected
**Dry Run**: Enabled first, then disabled

**Result:**
- Scanned 230 files recursively
- Found 580 renameable layers
- Removed "legacy_data_" prefix from 180 layers
- Created timestamped backups for all modified files
- Completed in under 2 minutes with comprehensive logging

### Example 5: Automatic Duplicate Resolution

**Scenario with potential naming conflicts:**
```
Input layers in project.gpkg:
- roads_main
- roads_temp
- temp_roads
- utilities_temp
```

**Operation**: Replace Text
**Find**: `temp_`
**Replace**: `` (remove completely)

**Without conflict resolution (would fail):**
- `roads_main` → `roads_main` ✓
- `roads_temp` → `roads` ✓
- `temp_roads` → `roads` ❌ (duplicate!)
- `utilities_temp` → `utilities` ✓

**With automatic conflict resolution (succeeds):**
- `roads_main` → `roads_main` ✓
- `roads_temp` → `roads` ✓ (first occurrence)
- `temp_roads` → `roads_1` ✓ (automatically numbered)
- `utilities_temp` → `utilities` ✓

**Dry Run Output:**
```
====================================================================================================
RENAME PLAN - Layer Name Changes
====================================================================================================
File                                     | Original Name             | New Name
----------------------------------------------------------------------------------------------------
project.gpkg                            | roads_main                | roads_main
project.gpkg                            | roads_temp                | roads
project.gpkg                            | temp_roads                | roads_1
project.gpkg                            | utilities_temp            | utilities
----------------------------------------------------------------------------------------------------
Total layers to rename: 4
Note: 1 conflict resolved with automatic numbering

Dry run mode - no changes were applied.
```

**Benefits:**
- **No manual intervention required**: Conflicts resolved automatically
- **Predictable numbering**: Always uses `_1`, `_2`, `_3` pattern
- **Database safety**: Prevents SQL constraint violations
- **Dry run preview**: See conflicts before applying changes
- **Strategy adjustment**: Modify parameters if numbering isn't desired

## Technical Details

### Database Renaming (GeoPackage/SpatiaLite)

For database formats, the tool performs SQL operations:

```sql
-- Rename the main table
ALTER TABLE [old_name] RENAME TO [new_name];

-- Update GeoPackage metadata (for .gpkg files)
UPDATE gpkg_contents
SET table_name = 'new_name', identifier = 'new_name'
WHERE table_name = 'old_name';

UPDATE gpkg_geometry_columns
SET table_name = 'new_name'
WHERE table_name = 'old_name';
```

### File Renaming (Shapefiles)

For shapefiles, the tool renames all component files:
- `.shp` (geometry)
- `.shx` (index)
- `.dbf` (attributes)
- `.prj` (projection)
- `.cpg` (code page)
- `.qix` (QGIS index)
- Other associated files if present

### Automatic Duplicate Resolution Algorithm

The tool implements a sophisticated conflict resolution system to ensure unique layer names:

```python
def _generate_rename_plan(self, layers_info, operation, **params):
    """Generate rename plan with duplicate detection and resolution."""
    rename_plan = []
    used_names = set()

    for layer_info in layers_info:
        new_name = self._apply_rename_operation(layer_info['name'], operation, **params)

        # Handle duplicate names with incremental numbering
        if new_name in used_names:
            counter = 1
            while f"{new_name}_{counter}" in used_names:
                counter += 1
            new_name = f"{new_name}_{counter}"

        used_names.add(new_name)
        # Add to rename plan...
```

**Key features:**
- **First occurrence wins**: Original name gets priority, duplicates get numbered
- **Incremental numbering**: Uses `_1`, `_2`, `_3` pattern consistently
- **Collision checking**: Ensures even numbered versions don't conflict
- **Cross-file awareness**: Tracks names across all files in the operation
- **Dry run visibility**: Shows all conflicts before applying changes

**Why this is necessary:**
- **GeoPackage constraint**: UNIQUE constraint on layer names in `gpkg_contents` table
- **SpatiaLite constraint**: Table names must be unique within the database
- **SQL compliance**: Prevents `UNIQUE constraint failed` errors
- **Data integrity**: Ensures all layers are successfully renamed

## Error Handling and Safety

### Transaction Safety
- **Database operations**: Wrapped in transactions with rollback capability
- **File operations**: Backup created before any changes
- **Validation**: Pre-flight checks for naming conflicts and invalid characters

### Common Issues and Solutions

**"Rename strategy would create duplicate layer names"**
- Modify your strategy parameters to ensure unique names
- Use dry run mode to identify conflicts before applying

**"Error reading GeoPackage/SpatiaLite"**
- Check file permissions and ensure file is not locked by another application
- Verify the file is a valid database format

**"Unsupported file type"**
- Ensure the input file is a supported format (.gpkg, .sqlite, .db, .shp)
- For other formats, consider converting to GeoPackage first

### Best Practices

1. **Always use dry run first** to preview changes
2. **Enable backup creation** for important datasets
3. **Test on copies** of critical data before applying to originals
4. **Validate naming conventions** before bulk operations
5. **Keep backups** until you're sure the rename was successful

## Performance Considerations

- **Database operations**: Very fast (SQL-based renaming)
- **File operations**: Dependent on file size and disk speed
- **Large shapefiles**: May take time to copy all component files
- **Network storage**: Slower for backup creation and file operations

## Technical Requirements

- **QGIS Version**: 3.40 or higher
- **Dependencies**: PyQGIS (included with QGIS), sqlite3 (Python standard library)
- **File Formats**: Supported vector formats with layer renaming capability
- **Operating System**: Cross-platform (Windows, macOS, Linux)

## Troubleshooting

### Debug Information

Enable debug logging in QGIS Processing options to see detailed information about:
- Layer discovery and validation
- Rename operation details
- SQL execution for database operations
- File operation details for shapefiles

### Recovery from Errors

If a rename operation fails:
1. **Check the backup**: Look for timestamped backup files in the same directory
2. **Restore manually**: Copy backup over the modified file
3. **Verify integrity**: Load the restored file in QGIS to ensure it's working
4. **Adjust parameters**: Modify rename strategy and try again

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## License

This project is licensed under the MIT License - see the main repository license for details.

## Contributing

This is part of the MQS (My QGIS Stuff) collection. See the main repository documentation for contribution guidelines.