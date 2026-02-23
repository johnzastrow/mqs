# Changelog

All notable changes to the metadata_manager subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.1] - 2026-02-23

### Fixed
- Release ZIP no longer contains `__pycache__` directories from plugin subdirectories.

## [0.5.0] - 2025-10-07

### Added
- **Phase 4: Smart Defaults and Layer Browser** (COMPLETE):
  - **Smart Defaults from Inventory**:
    * `get_smart_defaults()` method in DatabaseManager
    * Auto-populate title (Title Case conversion: "roads_2024" → "Roads 2024")
    * Auto-populate CRS, extents, geometry type, feature count
    * Auto-populate field list, raster dimensions in supplemental info
    * Uses existing GIS metadata if available (title, abstract, keywords, lineage, etc.)
    * Priority: cached metadata → smart defaults → empty fields
    * Saves significant time - user refines instead of entering from scratch
  - **Layer Browser Widget** (new widget):
    * Embedded layer list with filtering (All, Needs Metadata, Partial, Complete)
    * Search by layer name or path
    * Sortable table with 5 columns (Name, Status, Type, Format, Directory)
    * Next/Previous navigation buttons
    * Position indicator ("Layer X of Y")
    * Auto-save before navigation
    * Color-coded status (green/yellow/red)
    * Double-click or button to load in wizard
  - **Enhanced Workflow Integration**:
    * Three-tab interface: Dashboard, Layer Browser, Metadata Editor
    * Layer selection loads smart defaults if no cached metadata
    * Wizard save triggers Dashboard + Layer List refresh
    * Next/Previous navigation through filtered layers with auto-save
    * Seamless workflow for processing multiple layers
  - **Title Case Conversion**:
    * Smart conversion with abbreviation handling
    * Handles common GIS terms: GPS, GIS, DEM, DSM, DTM, CRS, UTM, WGS, NAD, etc.
    * Cleans underscores, hyphens, file extensions

### Changed
- MetadataWizard v0.4.0: Enhanced `load_metadata()` to use smart defaults
- MetadataWizard: Added `_convert_smart_defaults_to_metadata()` method
- MetadataManagerDockWidget: Added `layer_list_widget` and signal connections
- DatabaseManager: Added `get_smart_defaults()` and `_convert_to_title_case()` methods
- widgets/__init__.py: Export LayerListWidget

### Impact
- **Time Savings**: Users no longer start with empty fields for new layers
- **Efficiency**: Next/Previous navigation eliminates tab switching
- **Visibility**: Layer Browser shows what needs metadata at a glance
- **Workflow**: Complete metadata for 50+ layers in single session

## [0.3.6] - 2025-10-06

### Fixed
- **CRITICAL: "no such function: ST_IsEmpty" error** - Database connection now loads SpatiaLite extension
  - GeoPackage tables have triggers that use spatial functions (ST_IsEmpty, etc.)
  - Plain sqlite3 connection doesn't have these functions by default
  - Now attempts to load SpatiaLite extension on connection:
    - Tries `mod_spatialite` (common on Linux/Mac)
    - Falls back to `libspatialite`
    - On Windows, checks QGIS install path
  - **Result**: Inventory status updates now work, dashboard statistics update correctly
  - Graceful warning if extension can't be loaded (logs to console)

### Impact
- **Before**: All metadata saves appeared to succeed, but inventory status never updated (ERROR: "no such function: ST_IsEmpty")
- **After**: Inventory status updates correctly, dashboard shows complete/partial counts

## [0.3.5] - 2025-10-06

### Added
- **Auto-refresh dashboard after save** - Dashboard statistics now update immediately when metadata is saved
  - Connected wizard's `metadata_saved` signal to dashboard `refresh_statistics()` method
  - No need to manually click "Refresh Statistics" button after saving
  - Complete/Partial status changes appear instantly in dashboard

### Changed
- **Enhanced inventory update logging** for better debugging
  - Success messages now use `Qgis.Success` level with ✅ emoji
  - Failure messages show similar paths from inventory to help diagnose path mismatches
  - Clearer indication of what status was set (complete/partial)

### Fixed
- Dashboard not showing updated statistics after metadata save (user had to manually refresh)

## [0.3.4] - 2025-10-06

### Fixed
- **CRITICAL: Metadata save failure** - Fixed column name mismatches in `metadata_cache` table INSERT statement
  - Schema uses `created_date` and `last_edited_date`
  - Save method was incorrectly using `created_datetime` and `modified_datetime`
  - Added `layer_name` column to INSERT (was missing, schema requires it)
  - **Result**: Metadata now saves successfully to cache

- **Priority recommendations column names** - Fixed `get_priority_recommendations()` query
  - Changed `directory_path` → `parent_directory`
  - Changed `file_format` → `format`
  - **Result**: Recommendations widget now displays correctly

### Impact
- **Before Fix**: All metadata saves failed with "table metadata_cache has no column named created_datetime" error
- **After Fix**: Metadata saves successfully, recommendations display correctly

## [0.3.3] - 2025-10-06

### Changed
- **Dashboard table row height reduced to 16px** for more compact display
  - All drill-down tables (Directory, Data Type, Format, CRS) now use 16px rows
  - Vertical header hidden for cleaner appearance
  - Consistent with wizard table styling (contacts/links use 18px)
  - Allows more data visible without scrolling

## [0.3.2] - 2025-10-06

### Fixed
- **Critical: Dashboard statistics tabs now work** - Fixed database column name mismatches that prevented drill-down tabs from displaying data
  - `parent_directory` (was incorrectly querying `directory_path`) - **By Directory tab now works**
  - `format` (was incorrectly querying `file_format`) - **By File Format tab now works**
  - `crs_authid` (was incorrectly querying `crs`) - **By CRS tab now works**
  - `file_path` in WHERE clause (was incorrectly using `layer_path`) - **Metadata status updates now work correctly**
- Layer selector dialog now uses correct column names (`file_path`, `format`, `parent_directory`)
- Inventory metadata status updates now correctly identify layers in database

### Impact
- Dashboard drill-down views now populate correctly for all tabs (previously only Data Type worked)
- Metadata saves now properly update the inventory table tracking fields
- Layer selection dialog displays correct format and directory information

## [0.3.1] - 2025-10-06

### Added
- **Flexible Database Selection**:
  - Dashboard now has "Select Database..." button with file dialog
  - Visual connection status display (green background when connected, red when disconnected)
  - Ability to change databases during active session without restarting plugin
  - Auto-connect to last used database on startup (optional, not required)

- **Wizard State Management**:
  - Added `clear_layer()` method to wizard to reset when database changes
  - Added `clear_data()` methods to all wizard steps (Step1-4) for proper cleanup
  - Wizard auto-clears when database is changed in dashboard

### Changed
- Plugin now **loads without requiring database selection** (was blocking before)
  - Shows "No database selected" message on dashboard
  - User can work with plugin and select database when ready
  - Prevents forced workflow interruption on startup

- **Improved User Experience**:
  - Wizard shows helpful message when trying to select layer without database connection
  - Message directs user to Dashboard → Select Database...
  - Prevents confusing error states

### Fixed
- Database selection workflow was backwards (required on startup, couldn't change)
- Wizard could hold stale data when database was changed
- No visual indication of which database was currently connected

## [0.3.0] - 2025-10-06

### Added
- **Metadata Wizard - All Steps Complete** (Phase 3 COMPLETE):
  - **Step 1: Essential Fields**
    * Title field (required)
    * Abstract field (required, minimum 10 characters)
    * Keywords with tag-based input and removal
    * Category dropdown (ISO 19115 topic categories)
    * Validation with error messages
  - **Step 2: Common Fields**
    * Contacts management (add/edit/remove with dialog)
    * Contact table with Role, Name, Organization columns
    * License dropdown with common licenses + custom option
    * Use constraints and access constraints (multiline)
    * Language dropdown (default: English)
    * Attribution text field
    * Validation with warnings for recommended fields
  - **Step 3: Optional Fields**
    * Lineage, purpose, and supplemental info (multiline)
    * Links management (add/edit/remove with dialog)
    * Links table with Name, URL, Type columns
    * Update frequency dropdown
    * Spatial resolution text field
    * All fields optional
  - **Step 4: Review & Save**
    * HTML-formatted summary of all metadata
    * Completeness status indicator (Complete/Partial)
    * Auto-refresh summary when navigating to step
    * Three sections: Essential, Common, Optional fields
    * Read-only review interface
  - **Navigation System**
    * Next/Previous/Skip/Save buttons on all steps
    * Progress indicator (step X of 4)
    * Progress bar visualization
    * Validation before Next (skip validation with Skip button)
    * Save works from any step
  - **UI Polish**
    * Compact table rows (18px) for contacts and links
    * Scrollable areas for all steps
    * Color-coded status (green=complete, yellow=partial, orange=warnings)
    * Tab-based interface (Dashboard + Metadata Editor)

- **Database Persistence** (Phase 3):
  - `save_metadata_to_cache()` method in DatabaseManager
    * Saves metadata as JSON to metadata_cache table
    * Preserves created_datetime on updates
    * Tracks in_sync status (whether written to file)
  - `load_metadata_from_cache()` method in DatabaseManager
    * Loads metadata JSON from cache
    * Automatically populates all wizard steps
  - `update_inventory_metadata_status()` method in DatabaseManager
    * Updates geospatial_inventory tracking fields
    * Sets metadata_status (complete/partial/none)
    * Updates metadata_last_updated timestamp
    * Tracks metadata_target location (cache/file/database)
  - **Automatic Load on Layer Selection**
    * Wizard automatically loads cached metadata when layer selected
    * All fields populated across all steps
  - **Status Determination**
    * Complete: Title + Abstract (10+) + Category + Contact + License
    * Partial: Missing any recommended fields
    * Status shown in Step 4 review

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

### Changed
- Wizard now fully functional with save/load capability
- Dashboard statistics update when metadata is saved
- metadata_wizard.py version updated to 0.3.0

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
