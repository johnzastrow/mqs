# Metadata Manager - Requirements

## Project Overview

Create a QGIS Plugin that helps users create, manage, and apply metadata to layers following QGIS metadata standards. The plugin uses a unified GeoPackage database (created by Inventory Miner) that serves as both the file catalog AND the metadata management backend. The plugin persists reusable metadata information (organizations, contacts, keywords, etc.), guides users through creating layer-specific metadata, and integrates directly with the inventory to identify layers lacking metadata.

## Unified Database Architecture

**Key Concept**: The same GeoPackage database (e.g., `geospatial_catalog.gpkg`) is used by BOTH tools:
- **Inventory Miner** (Processing script): Creates/updates the file catalog (inventory table)
- **Metadata Manager** (Plugin): Adds metadata management tables and updates metadata status in inventory

This eliminates dual-database sync issues and provides a single source of truth.

## Core Functionality

### Metadata Standards Compliance
- **QGIS Metadata Standard**: Follow QGIS layer metadata structure and schema
- **Export Format**: Export to QGIS native XML format only
- **GeoPackage Association**: Associate metadata with layers in GeoPackage files
- **Import Existing**: Import metadata from existing QGIS layers or XML files

### Reusable Metadata Components

#### Organizations/Contacts Library
- **Organization Profiles**: Store reusable organization information
  - Name, abbreviation
  - Address, city, state/province, postal code, country
  - Website URL
  - Email, phone, fax
  - Logo/identifier
- **Contact Roles**: Author, publisher, custodian, owner, point of contact, processor, etc.
- **Quick Selection**: Dropdown/autocomplete for selecting from saved organizations

#### Keywords Library
- **Keyword Sets**: Organized collections of keywords by theme
  - Project keywords
  - Subject matter keywords
  - Place keywords
  - ISO 19115 topic categories
- **Tagging System**: Tag-based keyword selection with autocomplete
- **Bulk Application**: Apply keyword sets to multiple layers

#### Common Metadata Templates
- **Template Library**: Save complete or partial metadata templates
  - Project-level templates (same lineage, constraints, etc.)
  - Organization templates (standard contact info, constraints)
  - Data type templates (vector/raster specific fields)
- **Template Application**: Apply templates to new layers with layer-specific overrides
- **Template Management**: Create, edit, delete, import/export templates

### Metadata Creation Interface

#### Guided Workflow with Progressive Disclosure
- **Wizard Mode**: Step-by-step guided metadata creation with progressive disclosure
  - **Step 1: Required Fields** (must complete to proceed)
    - Title (auto-populated from inventory, user confirms/edits)
    - Abstract (user provides 2-3 sentences)
    - Keywords (select from library or add new)
  - **Step 2: Common Fields** (recommended)
    - Contacts and roles (select from organization library)
    - Constraints and access rights
    - Purpose (why was this created)
  - **Step 3: Optional/Detailed Fields** (can skip)
    - Detailed lineage and processing history
    - Online resources and links
    - Additional ISO 19115 fields
  - **Step 4: Review and Save**
    - Preview all entered metadata
    - Validation check (completeness indicator)
    - Write to target (.qmd or GeoPackage)
- **Expert Mode**: Single form with all fields accessible (for power users)
  - Skip wizard, go directly to full form
  - All fields visible and editable
  - Collapsible sections for organization
- **Quick Switch**: Button to switch between Wizard and Expert mode at any time
- **Progress Indicator**: Visual progress through wizard steps
- **Skip Navigation**: "Skip to review" button to bypass optional fields

#### Auto-Population from Layer and Inventory
- **Smart Defaults from Inventory**: Automatically import comprehensive data when user selects layer from inventory
  - Title from inventory.layer_name (converted to Title Case with cleanup)
  - CRS from inventory.crs_authid
  - Spatial extent from inventory.wgs84_extent
  - Native extent from inventory.native_extent
  - Geometry type from inventory.geometry_type (for vectors)
  - Feature count from inventory.feature_count
  - Band count from inventory.band_count (for rasters)
  - Raster dimensions from inventory.raster_width, inventory.raster_height
  - Field list from inventory.field_names and inventory.field_types
  - File path from inventory.file_path
  - File format from inventory.format
  - Data type from inventory.data_type
  - Creation date from inventory.file_created
  - Last modified from inventory.file_modified
  - Existing GIS metadata from inventory (layer_title, layer_abstract, keywords, lineage, constraints, url, contact_info)
- **User Confirmation Workflow**: User reviews auto-populated data and refines rather than entering from scratch
- **Title Case Conversion**: Automatically convert layer names to Title Case (e.g., "roads_2024" → "Roads 2024")
- **Fallback to Layer Properties**: If not using inventory, fall back to reading directly from layer properties

#### Validation and Quality Checks
- **Required Fields**: Highlight missing required fields (title, abstract, keywords)
- **Field Validation**: Check format of URLs, emails, dates
- **Completeness Indicator**: Visual indicator of metadata completeness (percentage)
- **Warning System**: Warn about potential issues (missing CRS, no lineage, etc.)

### Inventory Integration

#### Connect to Inventory Database
- **Database Connection**: Connect to inventory GeoPackage (from inventory_miner)
- **Layer Discovery**: List all layers from inventory lacking metadata
- **Batch Processing**: Process multiple layers from inventory
- **Status Tracking**: Track which layers have completed metadata

#### Metadata Gap Analysis
- **Identify Missing Metadata**: Query inventory for layers without:
  - No metadata files
  - Incomplete metadata (missing critical fields)
  - Outdated metadata
- **Priority Ranking**: Suggest priority order for metadata creation
- **Filtering**: Filter by directory, CRS, data type, organization

#### Batch Metadata Application
- **Bulk Template Application**: Apply templates to multiple layers from inventory
- **Shared Metadata**: Apply common fields (organization, constraints, keywords) to multiple layers
- **Layer-Specific Override**: Allow per-layer customization of specific fields
- **Progress Tracking**: Visual progress for batch operations

### Metadata Management

#### Edit Existing Metadata
- **Load from Layer**: Load and edit metadata from QGIS layer
- **Load from File**: Load and edit metadata from .qmd XML file or GeoPackage layer
- **Load from Cache**: Retrieve previously created metadata from metadatamanager.gpkg cache
- **Update Multiple Layers**: Update metadata across multiple layers
- **Edit History**: View when metadata was created, last edited, and last written to target
- **Version History**: Track metadata changes in cache with timestamps

#### Export/Import
- **Export Format**:
  - QGIS native XML format
  - Associate with GeoPackage layers
  - Plain text summary (for review)
- **Export Options**: Export single layer or batch export from inventory
- **Import Sources**: Import from QGIS layers, GeoPackage metadata, XML files

#### Metadata Profiles
- **User Profiles**: Store user-specific settings and defaults
- **Project Profiles**: Different profiles for different projects
- **Default Values**: Set defaults for frequently used values

### Storage and Persistence

#### Unified GeoPackage Database
- **Shared Database**: Uses same GeoPackage created by Inventory Miner (e.g., `geospatial_catalog.gpkg`)
- **User-Selected Location**: Plugin prompts user to select existing inventory database on first run
- **Database Creation**: Inventory Miner MUST run first to create database and inventory table
- **Metadata Manager adds tables**: Plugin creates its own tables in the existing database
- **Portable**: Users can move, copy, or share their unified database file
- **QGIS-Compatible**: Users can open and browse the database directly in QGIS
- **SQLite Backend**: Standard SQLite database with spatial extensions

#### Database Tables

**From Inventory Miner (existing):**
- **geospatial_inventory** (spatial layer): File catalog with 66 fields including:
  - All file system, spatial, vector, raster metadata
  - **metadata_status**: 'none', 'partial', 'complete'
  - **metadata_last_updated**: Timestamp of last metadata edit
  - **metadata_target**: Path to .qmd or "embedded in gpkg"
  - **metadata_cached**: Boolean if metadata in metadata_cache
  - **retired_datetime**: Versioning timestamp for deleted files

**Added by Metadata Manager (new):**
- **plugin_info**: Plugin versions (inventory_schema_version, metadata_schema_version), upgrade history
- **organizations**: Reusable organization profiles
- **contacts**: Contact information with roles
- **keywords**: Keyword library with hierarchical organization
- **keyword_sets**: Predefined keyword collections
- **templates**: Metadata templates for bulk application
- **settings**: User preferences and defaults
- **metadata_cache**: Detailed metadata JSON for all layers
  - Stores complete QgsLayerMetadata as JSON
  - Records when metadata was created and last edited
  - Records when metadata was written to target (GeoPackage or .qmd file)
  - Links to inventory via file_path
  - Backup/recovery if .qmd files lost

#### Version Management
- **Dual Version Tracking**: plugin_info table tracks BOTH tool versions separately
  - `inventory_schema_version`: Schema version from Inventory Miner
  - `metadata_schema_version`: Schema version from Metadata Manager
- **Independent Upgrades**: Each tool upgrades only its own tables/fields
- **Automatic Upgrades**: Detect older database versions and upgrade schema automatically
- **Upgrade History**: Log all schema upgrades with timestamps and tool name
- **Backward Compatibility**: Warn if database created by newer plugin version
- **Migration Scripts**: Built-in migration logic for schema changes
- **Shared Table Management**: Inventory table owned by Inventory Miner, Metadata Manager only updates metadata_status fields

#### Template Storage
- **Database Storage**: Templates stored as records in templates table
- **Export/Import**: Export templates to JSON/XML for sharing
- **Share Templates**: Users can share entire `metadatamanager.gpkg` or export individual templates
- **Import Templates**: Import templates from JSON/XML files or other `metadatamanager.gpkg` databases

## User Interface Requirements

### Main Plugin Window
- **Dockable Panel**: Can be docked in QGIS interface or floating
- **Database Selection**: Toolbar button to select existing inventory database (e.g., `geospatial_catalog.gpkg`)
- **Database Status**: Visual indicator showing connected database path and both tool versions
- **Inventory Miner Integration**: Button to run Inventory Miner from within plugin to create/update inventory
- **Inventory Miner Check**: Warn if Inventory Miner script not found, provide installation instructions
- **Tab-Based Interface**:
  - Tab 1: Create/Edit Metadata
  - Tab 2: Libraries (Organizations, Keywords, Templates)
  - Tab 3: Inventory Integration (reads from geospatial_inventory table)
  - Tab 4: Settings
- **Layer Selection**: Quick layer selector with active layer default

### Libraries Panel
- **Organizations Tab**:
  - List of saved organizations
  - Add/Edit/Delete buttons
  - Search/filter functionality
  - Import/export organization list
- **Keywords Tab**:
  - Keyword sets and individual keywords
  - Hierarchical tree view
  - Add/Edit/Delete keywords and sets
  - Import standard keyword vocabularies
- **Templates Tab**:
  - List of saved templates
  - Preview template contents
  - Apply/Edit/Delete buttons
  - Import/export templates

### Metadata Editor
- **Form-Based Input**: Clear, organized form with logical grouping
- **Field Descriptions**: Tooltips explaining each field
- **Rich Text Editor**: For abstract, lineage, and other long text fields
- **Date Pickers**: Calendar widgets for date fields
- **Dropdowns**: For standard values (CRS, topic categories, roles)
- **Multi-Select**: For keywords, contacts, constraints
- **Navigation Controls**: Next/Previous buttons to move through layer list
- **Auto-Save**: Automatically save to cache and write to target before navigation
- **Status Indicator**: Show save status (unsaved changes, saving, saved)

### Inventory Integration Panel

#### Metadata Quality Dashboard
- **Summary Statistics** (top of panel):
  - Total layers in inventory: 150
  - Complete metadata: 42 (28%)
  - Partial metadata: 18 (12%)
  - No metadata: 90 (60%)
  - Last updated: [timestamp]
- **Visual Progress Bar**: Shows overall completion percentage
- **Drill-Down Statistics**:
  - **By Directory**: Tree view showing completion by directory path
    - `/project_a/`: 20 of 50 complete (40%)
    - `/project_b/`: 15 of 60 complete (25%)
    - `/reference/`: 7 of 40 complete (18%)
  - **By Data Type**: Completion by vector/raster/table
    - Vectors: 30 of 100 complete (30%)
    - Rasters: 10 of 40 complete (25%)
    - Tables: 2 of 10 complete (20%)
  - **By File Format**: Completion by format
    - Shapefiles: 25 of 80 complete (31%)
    - GeoPackages: 12 of 30 complete (40%)
    - GeoTIFFs: 5 of 40 complete (13%)
  - **By Age**: Metadata freshness
    - Updated today: 5 layers
    - Updated this week: 12 layers
    - Updated this month: 25 layers
    - Older than 1 month: 15 layers
    - Never updated: 90 layers
  - **By CRS**: Completion by coordinate system
    - EPSG:4326: 18 of 50 complete (36%)
    - EPSG:3857: 12 of 45 complete (27%)
    - Others: 12 of 55 complete (22%)
- **Priority Recommendations**: Intelligent suggestions
  - "40 shapefiles in /project_a/ have no metadata"
  - "15 layers created this month lack metadata"
  - "All GeoTIFFs in /imagery/ need metadata"
- **Export Dashboard**: Export statistics as CSV or PDF report

#### Layer List and Filtering
- **Database Already Selected**: Uses same database selected on plugin startup
- **Run/Update Inventory Button**: Launch Inventory Miner to scan directories and update inventory table
- **Layer List**: Filterable/sortable list from geospatial_inventory table (WHERE retired_datetime IS NULL)
- **Columns**:
  - Metadata Status: ✓ complete, ⚠ partial, ✗ none (from inventory.metadata_status)
  - Layer Name (from inventory.layer_name)
  - File Path (from inventory.file_path)
  - Format (from inventory.format)
  - CRS (from inventory.crs_authid)
  - Last Updated (from inventory.metadata_last_updated)
  - Directory (from inventory.parent_directory)
- **Filter Options**:
  - **Status Filter**: Show only layers needing metadata (metadata_status != 'complete')
  - **Directory Filter**: Multi-select tree of directories from inventory
  - **File Type Filter**: Filter by format (shapefile, GeoPackage, GeoTIFF, etc.)
  - **CRS Filter**: Filter by coordinate system
  - **Date Filter**: Filter by file creation or metadata update date
  - **Show/hide retired records**: Toggle display of retired_datetime IS NOT NULL
  - **Saved Filter Sets**: Save common filter combinations
- **Sorting**: Click column headers to sort by any column
- **Search**: Quick text search across layer names and paths
- **Bulk Actions**:
  - Select multiple layers (checkbox column)
  - Apply template to selected → updates inventory.metadata_status for all
  - Export metadata for selected
  - Mark as partial/complete manually
- **Context Menu**: Right-click layer for quick actions
  - Edit metadata
  - View in QGIS
  - Open file location
  - Copy file path
- **Next/Previous Navigation**:
  - Navigate through filtered layer list
  - Auto-save current metadata before moving to next/previous layer
  - Updates inventory.metadata_status and inventory.metadata_last_updated automatically
  - Quick workflow for processing multiple layers sequentially
  - Visual indicator showing position in list (e.g., "Layer 5 of 42")

## Technical Requirements

### QGIS Plugin Structure
- **Plugin Type**: QGIS Python plugin (PyQGIS)
- **Minimum QGIS Version**: QGIS 3.40 or higher
- **Plugin Category**: Metadata/Documentation
- **Dependencies**: Only PyQGIS and Qt (no external dependencies)

### Data Storage
- **Unified GeoPackage Database**: Single database (e.g., `geospatial_catalog.gpkg`) shared with Inventory Miner
- **User-Selectable Location**: User chooses existing inventory database created by Inventory Miner
- **QGIS Settings**: Only for last-used database path and window preferences
- **Layer Metadata**: Direct integration with QGIS layer metadata API
- **Inventory Table Access**: Read-only access to geospatial_inventory table, write access to metadata_status fields only

### QGIS Integration
- **Layer Metadata API**: Use `QgsLayerMetadata` for metadata handling
- **GeoPackage Integration**: Write metadata directly to GeoPackage layer metadata
- **Layer Tree Integration**: Context menu item for "Edit Metadata with Manager"
- **Processing Integration**: Optional processing algorithms for batch operations
- **Project Save Integration**: Metadata saved with QGIS project and GeoPackage files

### Performance
- **Fast Loading**: Plugin loads without delay
- **Responsive UI**: Forms and lists update immediately
- **Efficient Storage**: Minimal database size
- **Background Processing**: Long operations (batch) don't block UI

## Metadata Fields (QGIS Standard)

### Identification
- **Title** (required)
- **Abstract** (required)
- **Type** (dataset, service, etc.)
- **Language**
- **Categories** (ISO 19115 topic categories)
- **Keywords** (with thesaurus/vocabulary)

### Contacts
- **Contact Information**: Multiple contacts with roles
  - Name, organization, position
  - Email, phone, address
  - Role (author, publisher, custodian, etc.)

### Extent
- **Spatial Extent**: Bounding box coordinates
- **Temporal Extent**: Start/end dates
- **CRS**: Coordinate Reference System

### Access and Constraints
- **Licenses**: License information
- **Rights**: Copyright and usage rights
- **Constraints**: Access constraints, use constraints
- **Fees**: Access fees if applicable

### Lineage
- **Statement**: Description of data lineage and processing history
- **Source**: Information about source data

### History
- **Creation Date**
- **Publication Date**
- **Revision Date**

### Links
- **Online Resources**: URLs to related resources, documentation, services

## Metadata Writing Workflow

### Individual Layer Workflow
1. User selects layer from inventory list (reads from geospatial_inventory table WHERE retired_datetime IS NULL)
2. Plugin auto-populates from layer properties AND inventory data (CRS, extent, geometry type, etc.)
3. User edits/adds required fields (abstract, purpose, keywords)
4. User clicks Save or Next
5. Plugin performs:
   - Save metadata to metadata_cache table with current timestamp
   - Determine target file type (GeoPackage vs other) from inventory.format
   - If GeoPackage: Write metadata to layer metadata in .gpkg using QgsLayerMetadata API
   - If non-GeoPackage: Write metadata to .qmd sidecar file in same directory as source
   - Update metadata_cache: last_written_date, target_location, in_sync=1
   - **UPDATE geospatial_inventory table**:
     - SET metadata_status = 'complete' (or 'partial' based on validation)
     - SET metadata_last_updated = current timestamp
     - SET metadata_target = .qmd path or "embedded in gpkg"
     - SET metadata_cached = TRUE
6. If Next clicked: Move to next layer in filtered list and repeat

### Batch Template Application Workflow
1. User selects multiple layers from inventory (geospatial_inventory table)
2. User selects template to apply
3. Plugin performs for each layer:
   - Apply template metadata
   - Auto-populate layer-specific fields (title from layer_name in Title Case, CRS, extent, etc. from inventory)
   - Save to metadata_cache
   - Write to appropriate target (GeoPackage or .qmd) based on inventory.format
   - **UPDATE geospatial_inventory**:
     - SET metadata_status = 'complete' or 'partial'
     - SET metadata_last_updated = current timestamp
     - SET metadata_target = target location
     - SET metadata_cached = TRUE
4. Show completion summary (X of Y layers processed)
5. Refresh inventory list to show updated metadata_status

### Metadata Sync Detection
- **Out of Sync**: If user edits cached metadata but hasn't written to target
- **Missing Target**: If .qmd file deleted or GeoPackage replaced
- **Modified Target**: If target metadata modified outside plugin (optional detection)
- **Sync Action**: Offer to write cached metadata to target

## Testing Requirements

### Unit Tests
- Metadata field validation
- Template application logic
- Organization/keyword CRUD operations
- Import/export functionality
- Title Case conversion logic
- Metadata destination detection (GeoPackage vs .qmd)
- Metadata cache operations

### Integration Tests
- QGIS layer metadata integration
- GeoPackage metadata writing/reading
- .qmd file creation and parsing
- Database persistence
- UI interaction tests
- Next/Previous navigation with auto-save

### User Acceptance Tests
- Complete metadata creation workflow with Next/Previous navigation
- Template creation and application
- Inventory integration workflow
- Batch operations
- Metadata recovery from cache
- Sync detection and resolution

## Documentation Requirements

### User Documentation
- Plugin installation guide
- Quick start tutorial
- Workflow examples (guided vs. expert mode)
- Template creation guide
- Inventory integration guide

### Technical Documentation
- Architecture documentation
- Database schema
- API documentation for reusable components

## Workflow Summary - Least Effort Path

### One-Time Setup (5-10 minutes)
1. Run Inventory Miner to catalog all geospatial data → creates `geospatial_catalog.gpkg`
2. Open Metadata Manager plugin, select `geospatial_catalog.gpkg`
3. Plugin creates its tables in the existing database
4. Add organization(s) with contact details to library
5. Add common keywords to library
6. Create 2-3 templates for common data types

### Bulk Processing (Minimal Effort)
1. Plugin already connected to inventory (same database)
2. View inventory tab, filter for layers needing metadata (metadata_status != 'complete')
3. Select multiple related layers
4. Apply appropriate template
5. Plugin auto-populates from inventory fields and writes to all targets
6. Inventory table automatically updated with metadata_status = 'complete'

### Individual Refinement (30 seconds per layer)
1. **Dashboard Analysis**: View metadata quality dashboard to identify priorities
   - See "40 shapefiles in /project_a/ have no metadata"
   - Filter for that directory and shapefile format
2. **Apply Template to Batch**: Select all 40 shapefiles, apply appropriate template
   - Dashboard now shows "0 of 40 need metadata" for that directory
3. **Refine Individual Layers** (for layers needing custom details):
   - Open first layer from filtered list
   - **Progressive Disclosure Wizard - Step 1 (Required)**:
     - Title: Auto-populated "Project A Roads" ✓ (from inventory.layer_name, Title Case)
     - Abstract: User types 2-3 sentences
     - Keywords: Select from library (pre-populated with common project keywords)
   - **Step 2 (Common)**:
     - Contacts: Select organization from library ✓ (auto-selected from template)
     - Purpose: User types brief purpose
     - Constraints: Already filled from template ✓
   - **Step 3 (Optional)**: Skip (or fill detailed lineage if needed)
   - **Step 4 (Review)**: Confirm, click Next
4. Plugin auto-saves to metadata_cache, writes to target, updates inventory.metadata_status = 'complete'
5. Next layer automatically loads with same smart defaults
6. Dashboard updates in real-time - watch completion percentage rise

### Maintenance (Ongoing)
1. Run Inventory Miner in Update Mode to find new files
2. New files appear in inventory with metadata_status = 'none'
3. Apply existing templates to new layers
4. Quick refinement with Next/Previous workflow
5. All metadata cached in metadata_cache and status tracked in inventory

## Implemented Time-Saving Features

### Smart Defaults from Inventory ✅
- Automatically imports comprehensive data from inventory table
- User confirms/refines rather than entering from scratch
- Includes: title, CRS, extent, geometry type, feature count, field list, file paths, existing GIS metadata
- Saves significant time per layer

### Progressive Disclosure Wizard ✅
- Required fields first (title, abstract, keywords)
- Common fields second (contacts, constraints, purpose)
- Optional fields last (detailed lineage, links)
- Expert mode for power users who want all fields at once
- Skip navigation to bypass optional sections

### Metadata Quality Dashboard ✅
- Summary statistics with overall completion percentage
- Drill-down by directory, data type, file format, age, CRS
- Priority recommendations for efficient workflow
- Visual progress tracking
- Export statistics as reports

## Future Enhancements (Post v1.0)

- **Batch abstract generation**: Generate basic abstracts from available data
- **Metadata inheritance**: Copy metadata from similar layers
- **Metadata Validation Services**: Online validation against standards
- **Harvest from Services**: Import metadata from CSW/WMS/WFS services
- **Metadata Synchronization**: Sync with external metadata catalogs
- **Advanced Templates**: Conditional fields based on data type
- **Metadata Reports**: Generate metadata summary reports
- **Team Collaboration**: Shared template repositories
- **Automated Metadata**: AI-assisted metadata generation from layer analysis

## Quality Assurance

### Metadata Quality
- Ensure compliance with QGIS metadata standard
- Validate against ISO 19115/19139 schemas
- Test export/import round-trips

### Usability
- User testing with target audience
- Intuitive workflow for beginners
- Efficient workflow for power users
- Accessible interface (keyboard navigation, screen readers)

### Code Quality
- Follow QGIS plugin development best practices
- Comprehensive error handling
- Logging for debugging
- Code documentation

## Target Layer Metadata Storage

### Smart Metadata Destination
Plugin automatically determines appropriate metadata storage based on target layer file type:

#### GeoPackage Layers
- **Direct Metadata Writing**: Write QGIS metadata directly to GeoPackage layer metadata storage using QGIS API
- **Metadata Retrieval**: Read existing metadata from GeoPackage layers
- **Batch Processing**: Apply metadata to multiple GeoPackage layers
- **Metadata Persistence**: Metadata stored within GeoPackage file, travels with data
- **Target**: Metadata embedded in .gpkg file for each layer

#### Non-GeoPackage Layers (Shapefiles, GeoTIFF, etc.)
- **Sidecar .qmd Files**: Write QGIS metadata to .qmd XML sidecar files
- **File Naming**: .qmd file matches layer name (e.g., roads.shp → roads.qmd)
- **File Location**: .qmd file created in same directory as source layer
- **QGIS Recognition**: QGIS automatically loads .qmd metadata when layer is opened
- **Batch Operations**: Create .qmd files for multiple layers

### Metadata Caching in metadatamanager.gpkg
- **Backup Storage**: All created/edited metadata stored in metadata_cache table
- **Timestamps**: Record creation time, last edit time, last write time
- **Layer Linking**: Link cached metadata to source layer path from inventory
- **Recovery**: Recover metadata if target .qmd file is lost or GeoPackage is replaced
- **History**: Track metadata evolution over time
- **Sync Status**: Track if cached metadata is in sync with target file

## Database Schema

### plugin_info Table
```sql
CREATE TABLE plugin_info (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Records: plugin_version, schema_version, created_date
```

### organizations Table
```sql
CREATE TABLE organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    abbreviation TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    country TEXT,
    website TEXT,
    email TEXT,
    phone TEXT,
    fax TEXT,
    logo_path TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### contacts Table
```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER,
    name TEXT NOT NULL,
    position TEXT,
    email TEXT,
    phone TEXT,
    role TEXT, -- author, publisher, custodian, owner, point_of_contact, processor
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);
```

### keywords Table
```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT, -- subject, place, theme, temporal
    parent_id INTEGER, -- for hierarchical organization
    vocabulary TEXT, -- thesaurus/vocabulary name
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES keywords(id)
);
```

### keyword_sets Table
```sql
CREATE TABLE keyword_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE keyword_set_members (
    set_id INTEGER,
    keyword_id INTEGER,
    PRIMARY KEY (set_id, keyword_id),
    FOREIGN KEY (set_id) REFERENCES keyword_sets(id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id)
);
```

### templates Table
```sql
CREATE TABLE templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    metadata_json TEXT NOT NULL, -- JSON representation of QgsLayerMetadata
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### settings Table
```sql
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### metadata_cache Table
```sql
CREATE TABLE metadata_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_path TEXT NOT NULL, -- Full path from inventory
    layer_name TEXT NOT NULL,
    file_type TEXT, -- gpkg, shp, tif, etc.
    metadata_json TEXT NOT NULL, -- JSON representation of QgsLayerMetadata
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_written_date TIMESTAMP, -- When metadata was written to target file
    target_location TEXT, -- Path to .qmd file or GeoPackage
    in_sync INTEGER DEFAULT 1, -- 1 if cache matches target, 0 if edited but not written
    UNIQUE(layer_path)
);

-- Index for faster lookups
CREATE INDEX idx_metadata_cache_path ON metadata_cache(layer_path);
CREATE INDEX idx_metadata_cache_sync ON metadata_cache(in_sync);
```

### upgrade_history Table
```sql
CREATE TABLE upgrade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_version TEXT,
    to_version TEXT,
    upgrade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success INTEGER DEFAULT 1,
    notes TEXT
);
```

## Initialization and Upgrade Workflow

### First Run - Database Selection
1. Plugin starts, checks QGIS settings for last used database path
2. If no path or file doesn't exist, show "Select Inventory Database" dialog:
   - **Option 1**: Browse for existing inventory database (created by Inventory Miner)
   - **Option 2**: Run Inventory Miner first to create database
   - **No create option**: Database MUST be created by Inventory Miner first
3. Validate selected database:
   - Check for `geospatial_inventory` table (confirms Inventory Miner created it)
   - If missing, show error: "This database was not created by Inventory Miner. Please run Inventory Miner first or select a different database."
4. Check for Metadata Manager tables (plugin_info, organizations, etc.)
5. If Metadata Manager tables missing, initialize them with current schema
6. Update plugin_info with metadata_schema_version
7. Save database path to QGIS settings

### Subsequent Runs
1. Load database path from QGIS settings
2. Open database and check `plugin_info` table
3. Verify `geospatial_inventory` table still exists (inventory schema intact)
4. Compare stored `metadata_schema_version` with current plugin version
5. If versions match, proceed normally
6. If stored version is older, run Metadata Manager upgrade migrations (only Metadata Manager tables)
7. If stored version is newer, warn user and offer read-only mode

### Upgrade Process (Metadata Manager Only)
1. Detect metadata_schema_version mismatch (stored < current)
2. Show upgrade dialog: "Metadata Manager schema will be upgraded from vX to vY"
3. Create backup recommendation
4. Run migration scripts in transaction (only affects Metadata Manager tables)
5. Record upgrade in `upgrade_history` table with tool='metadata_manager'
6. Update `metadata_schema_version` in `plugin_info`
7. Show success message

### Inventory Miner Updates
- When Inventory Miner runs in update mode, it preserves Metadata Manager tables
- Inventory Miner only upgrades `inventory_schema_version`
- Each tool maintains its own version independently

This implementation will be the first QGIS plugin in the mqs repository, complementing the existing Processing Toolbox scripts by providing a full GUI-based metadata management solution focused on QGIS native metadata format and GeoPackage integration.
