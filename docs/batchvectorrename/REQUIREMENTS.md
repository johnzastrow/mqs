# Requirements: Batch Vector Layer Rename Tool

## Core Functionality

### Primary Objective
Create a QGIS Processing Toolbox script that allows safe and efficient batch renaming of layers in vector files and databases that support layer renaming operations.

### Supported Vector Formats

#### **Primary Formats (Full Support)**
1. **GeoPackage (.gpkg)** - SQLite-based with full layer renaming support
2. **SpatiaLite (.sqlite/.db)** - Spatial SQLite databases with table renaming capability
3. **Shapefiles (.shp)** - File-based renaming by renaming component files

#### **Secondary Formats (Limited Support)**
4. **File Geodatabase (.gdb)** - Framework ready, limited by ESRI proprietary restrictions

### Key Features

#### Rename Strategies
1. **Add Prefix** - Prepend custom text to all layer names
2. **Add Suffix** - Append custom text to all layer names
3. **Find and Replace** - Replace specific text patterns in layer names
4. **Clean Names** - Remove invalid characters and standardize naming
5. **Case Conversion** - Convert to lowercase, uppercase, or Title Case

#### Safety and Validation
- **Dry Run Mode** - Preview all changes before applying them
- **Automatic Backup** - Create timestamped backups before making changes
- **Conflict Detection** - Prevent creation of duplicate layer names
- **Name Validation** - Ensure database-compatible layer names
- **Transaction Safety** - Atomic operations with rollback capability

#### Error Handling
- **Graceful Failures** - Continue operation even if individual layers fail
- **Recovery Guidance** - Clear instructions for restoring from backups
- **Detailed Logging** - Comprehensive error reporting and progress feedback

## Technical Requirements

### QGIS Integration
- **Version Compatibility**: QGIS 3.40 or higher
- **Processing Framework**: Native QgsProcessingAlgorithm implementation
- **Parameter Types**: Standard QGIS parameter classes (File, Boolean, Enum, String)
- **Progress Reporting**: QgsProcessingFeedback integration

### Dependencies
- **Core Libraries**: PyQGIS (included with QGIS installation)
- **Python Standard Library**: sqlite3, os, re, shutil, pathlib, typing
- **Database Support**: sqlite3 for GeoPackage and SpatiaLite operations

### Parameter Specifications

#### Required Parameters
- **Input File**: Vector file or database containing layers to rename (File selection)

#### Strategy Parameters
- **Rename Strategy**: Enum selection of available rename strategies (default: Add prefix)
- **Custom Prefix**: String for prefix strategy (required when using Add Prefix)
- **Custom Suffix**: String for suffix strategy (required when using Add Suffix)
- **Find Text**: String for find/replace strategy (required when using Find and Replace)
- **Replace Text**: String for find/replace strategy (optional, defaults to empty)

#### Safety Parameters
- **Dry Run**: Boolean for preview mode (default: True)
- **Create Backup**: Boolean for backup creation (default: True)

## Functional Requirements

### Layer Discovery
1. **Format Detection**: Automatically detect vector file format and capabilities
2. **Layer Enumeration**: Extract all layer names from the input file/database
3. **Validation**: Verify file accessibility and format compatibility

### Rename Operations

#### Database Operations (GeoPackage/SpatiaLite)
```sql
-- Core rename operation
ALTER TABLE [old_name] RENAME TO [new_name];

-- GeoPackage metadata updates
UPDATE gpkg_contents SET table_name = 'new_name', identifier = 'new_name' WHERE table_name = 'old_name';
UPDATE gpkg_geometry_columns SET table_name = 'new_name' WHERE table_name = 'old_name';
```

#### File Operations (Shapefiles)
- Rename all component files: .shp, .shx, .dbf, .prj, .cpg, .qix, etc.
- Maintain file associations and integrity
- Handle missing optional components gracefully

### Validation Logic

#### Name Sanitization
- Replace invalid characters with underscores: `[^a-zA-Z0-9_]` → `_`
- Remove consecutive underscores: `__+` → `_`
- Remove leading/trailing underscores
- Handle names starting with numbers: prefix with "layer_"
- Enforce SQLite identifier limits (63 characters)

#### Conflict Detection
- Check for duplicate names in rename plan
- Validate against existing layer names not being renamed
- Ensure all new names are unique and valid

### Backup System

#### File Backup
- Create timestamped copies: `filename_backup_YYYYMMDD_HHMMSS.ext`
- For shapefiles: backup all component files
- For directories: create complete directory copies

#### Database Backup
- SQLite databases: file-level copying before modifications
- Atomic transactions: all-or-nothing rename operations
- Rollback capability: automatic transaction reversal on failure

## User Experience Requirements

### Interface Design
- **Clear Parameter Layout**: Logical grouping of strategy-specific parameters
- **Validation Feedback**: Immediate validation of required parameters
- **Strategy Descriptions**: Helpful text explaining each rename strategy

### Dry Run Output
```
================================================================================
RENAME PLAN
================================================================================
Original Name                  | New Name
-----------------------------------------------------------------
counties                       | 2023_counties
roads                          | 2023_roads
boundaries                     | 2023_boundaries
-----------------------------------------------------------------
Total layers to rename: 3

Dry run mode - no changes were applied.
Set 'Dry run' to False to apply these changes.
```

### Progress Reporting
- **Operation Start**: Confirmation of input file and strategy
- **Layer Discovery**: Count and list of discovered layers
- **Rename Plan**: Detailed before/after comparison
- **Operation Progress**: Step-by-step rename confirmation
- **Completion Status**: Success/failure summary with backup location

### Error Messages
- **Parameter Validation**: Clear messages for missing required parameters
- **File Access**: Helpful guidance for permission and file lock issues
- **Naming Conflicts**: Detailed explanation of duplicate name issues
- **Recovery Instructions**: Step-by-step backup restoration guidance

## Performance Requirements

### Efficiency
- **Database Operations**: Leverage SQL efficiency for large layer counts
- **File Operations**: Optimize file copying for large shapefiles
- **Memory Usage**: Process layers sequentially to manage memory

### Scalability
- **Layer Count**: Support databases with 100+ layers
- **File Size**: Handle large shapefiles (GB+) efficiently
- **Progress Updates**: Regular feedback for long-running operations

## Safety and Reliability Requirements

### Data Protection
- **No Data Loss**: Ensure all rename operations preserve data integrity
- **Backup Verification**: Validate backup creation before proceeding
- **Transaction Atomicity**: All database changes succeed or fail together

### Error Recovery
- **Graceful Degradation**: Continue with remaining layers if one fails
- **Clear Recovery Path**: Document exactly how to restore from backup
- **State Preservation**: Leave system in consistent state after any failure

### Testing Requirements
- **Dry Run Accuracy**: Ensure dry run exactly matches actual operation
- **Backup Integrity**: Verify backup files are complete and valid
- **Rollback Testing**: Confirm transaction rollback works correctly

## Success Criteria

### Functional Success
- ✅ Successfully rename layers in all supported formats
- ✅ Provide safe dry run preview functionality
- ✅ Create reliable backups for all file types
- ✅ Handle naming conflicts and invalid characters
- ✅ Maintain data integrity throughout all operations

### Usability Success
- **Intuitive Interface**: Users can understand and use without extensive documentation
- **Clear Feedback**: Always clear what will happen and what did happen
- **Error Recovery**: Users can easily recover from any issues
- **Flexible Strategies**: Multiple approaches to meet different naming needs

### Reliability Success
- **Zero Data Loss**: No cases where data is lost or corrupted
- **Consistent Behavior**: Predictable results across different file types
- **Error Resilience**: Graceful handling of edge cases and errors
- **Performance**: Reasonable execution time for typical datasets

## Integration Requirements

### QGIS Ecosystem
- **Processing Toolbox**: Seamless integration with standard QGIS workflows
- **Layer Management**: Respect QGIS layer naming conventions
- **Project Compatibility**: Renamed layers work correctly in QGIS projects

### File System Integration
- **Path Handling**: Robust handling of different path formats and lengths
- **Permission Respect**: Proper handling of read-only files and permission issues
- **Network Storage**: Compatible with network drives and cloud storage