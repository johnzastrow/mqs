# Changelog

All notable changes to the metadata_manager subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- SQLite multi-statement error during table initialization
  - Fixed `get_metadata_cache_schema()` to return list of statements instead of multi-statement string
  - Database initialization now works correctly without "You can only execute one statement at a time" error
- QFlowLayout import error in metadata wizard
  - Moved QFlowLayout class definition before classes that use it
  - Changed reference from QtWidgets.QFlowLayout to QFlowLayout
  - Removed duplicate class definition
- Keyword tags layout - only one tag visible at a time
  - Separated keyword input and tags display into separate rows
  - Added scrollable area for tags with proper wrapping
  - Improved QFlowLayout spacing and wrapping logic

### Added
- **Metadata Quality Dashboard** (Phase 2 - v0.2.0 COMPLETE):
  - Dashboard widget showing metadata completion statistics with progress bar
  - Color-coded visual feedback (green/orange/red)
  - Four drill-down views: by Directory, Data Type, File Format, and CRS
  - Priority recommendations showing highest-impact areas needing metadata
  - Refresh functionality for real-time updates
  - Five new statistics methods in DatabaseManager
  - Test infrastructure with unit tests and testing guide
  - Comprehensive Phase 2 documentation

- **Metadata Wizard** (Phase 3 - v0.3.0 in development):
  - Progressive disclosure wizard architecture
  - Step 1: Essential fields (COMPLETE)
    * Title field (required)
    * Abstract field (required, minimum 10 characters)
    * Keywords with tag-based input and removal
    * Category dropdown (ISO 19115 topic categories)
  - Navigation system (Next/Previous/Skip/Save buttons)
  - Validation with error messages
  - Progress indicator showing current step
  - Tab-based interface (Dashboard + Metadata Editor)
  - Steps 2-4 placeholders (pending implementation)

- **Installation Scripts**:
  - install.bat for Windows
  - install.sh for Linux/Mac
  - INSTALL.md installation guide

- **Unified Database Architecture** (v0.2.0 in development):
  - Database management module (`db/manager.py`) with connection, validation, and initialization
  - Database schema definitions (`db/schema.py`) for all Metadata Manager tables
  - Migration system (`db/migrations.py`) for schema upgrades
  - Automatic database selection on plugin startup
  - Validates inventory database created by Inventory Miner
  - Initializes Metadata Manager tables in existing database
  - Dual version tracking (inventory_schema_version + metadata_schema_version)
  - Automatic schema upgrade detection and execution
  - Database connection persistence via QSettings

- **Metadata Quality Dashboard** (Phase 2 - v0.2.0):
  - Dashboard widget (`widgets/dashboard_widget.py`) showing metadata completion statistics
  - Overall completion percentage with progress bar
  - Color-coded statistics (complete=green, partial=orange, none=red)
  - Drill-down views by:
    - Directory (sorted by most needing metadata)
    - Data type (vector, raster, etc.)
    - File format (shapefile, GeoPackage, etc.)
    - CRS (coordinate reference system)
  - Priority recommendations showing highest-impact areas needing metadata
  - Refresh button to update statistics on demand
  - Extended DatabaseManager with 5 new statistics methods:
    - `get_statistics_by_directory()` - Directory-level breakdown
    - `get_statistics_by_data_type()` - Data type analysis
    - `get_statistics_by_file_format()` - Format analysis
    - `get_statistics_by_crs()` - CRS distribution
    - `get_priority_recommendations()` - Top priority items
  - Test script (`testing/test_dashboard.py`) for statistics validation
  - Testing documentation (`testing/README.md`)

### Changed
- Updated main plugin class to integrate database management
- Modified dockwidget to receive database manager instance and display dashboard
- Plugin now requires Inventory Miner database before use
- Dockwidget now shows dashboard on startup with automatic statistics refresh

## [0.1.0] - 2025-10-05

### Added
- Initial plugin structure using QGIS Plugin Builder
- Dockable widget interface (MetadataManager_dockwidget.ui)
- Standard QGIS plugin architecture with:
  - `__init__.py` - Plugin entry point
  - `MetadataManager.py` - Main plugin class
  - `MetadataManager_dockwidget.py` - Dockable widget implementation
  - `metadata.txt` - Plugin metadata
  - `resources.py` and `resources.qrc` - Qt resources
- Development infrastructure:
  - Makefile for compilation and deployment
  - pb_tool.cfg for pb_tool support
  - pylintrc for code quality
  - test/ directory for unit tests
  - i18n/ directory for translations
  - help/ directory for documentation
- REQUIREMENTS.md with comprehensive specifications
- CHANGELOG.md for version tracking
- Testing directory structure in `docs/metadata_manager/testing/`
- Plugin directory in `Plugins/metadata_manager/`

### Planned Features (Future Releases)

#### Unified Database Architecture
- **Shared GeoPackage Database**:
  - Same database as Inventory Miner (e.g., `geospatial_catalog.gpkg`)
  - Inventory Miner creates database with geospatial_inventory table
  - Metadata Manager adds its tables to existing database
  - Dual version tracking (inventory_schema_version + metadata_schema_version)
  - Independent schema upgrades for each tool

#### Inventory Integration
- **Direct Database Integration**:
  - Read layers from geospatial_inventory table
  - Write metadata status updates to inventory.metadata_status
  - Filter layers by metadata status (none, partial, complete)
  - Real-time progress tracking
- **Run Inventory Miner from Plugin**:
  - Launch Inventory Miner to scan/update without leaving plugin
  - Check for Inventory Miner script availability
  - Update mode preserves metadata status

#### Time-Saving Features
- **Metadata Quality Dashboard**:
  - Summary statistics with overall completion percentage
  - Drill-down by directory, data type, file format, age, CRS
  - Priority recommendations ("40 shapefiles in /project_a/ need metadata")
  - Visual progress tracking
  - Export statistics as CSV or PDF reports
- **Progressive Disclosure Wizard**:
  - Step 1: Required fields (title, abstract, keywords)
  - Step 2: Common fields (contacts, constraints, purpose)
  - Step 3: Optional fields (detailed lineage, links)
  - Step 4: Review and save
  - Skip navigation to bypass optional sections
  - Expert mode for power users (all fields at once)
- **Smart Defaults from Inventory**:
  - Auto-populate title, CRS, extent, geometry type from inventory
  - Import feature count, field list, file paths
  - Load existing GIS metadata if present
  - User confirms/refines instead of entering from scratch

#### Core Features
- Reusable metadata component libraries (organizations, contacts, keywords)
- Metadata template system for bulk application
- Validation and completeness checking
- Export to QGIS XML format and .qmd sidecar files
- Associate metadata with GeoPackage layers
- Next/Previous navigation through inventory list with auto-save
