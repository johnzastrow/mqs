# Metadata Manager - Requirements

## Project Overview

Create a QGIS Plugin that helps users create, manage, and apply metadata to layers following QGIS metadata standards. The plugin will persist reusable metadata information (organizations, contacts, keywords, etc.), guide users through creating layer-specific metadata, and integrate with inventory databases to identify layers lacking metadata.

## Core Functionality

### Metadata Standards Compliance
- **QGIS Metadata Standard**: Follow QGIS layer metadata structure and schema
- **ISO 19115/19139 Support**: Support ISO metadata standards used by QGIS
- **Export Formats**: Support exporting to XML (QGIS native, ISO 19115, FGDC)
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

#### Guided Workflow
- **Wizard Mode**: Step-by-step guided metadata creation
  - Step 1: Identification (title, abstract, purpose)
  - Step 2: Contacts (roles and organizations)
  - Step 3: Keywords and categories
  - Step 4: Constraints and access
  - Step 5: Spatial/temporal extent
  - Step 6: Lineage and quality
  - Step 7: Review and save
- **Expert Mode**: Single form with all fields accessible
- **Progress Indicator**: Visual progress through wizard steps

#### Auto-Population from Layer
- **Automatic Detection**: Pre-fill metadata from layer properties
  - Title from layer name
  - CRS from layer CRS
  - Spatial extent from layer extent
  - Geometry type for vectors
  - Band count for rasters
  - Field list for attribute information
  - File path and format

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
- **Load from File**: Load and edit metadata from XML file
- **Update Multiple Layers**: Update metadata across multiple layers
- **Version History**: Track metadata changes (optional)

#### Export/Import
- **Export Formats**:
  - QGIS native XML
  - ISO 19115/19139 XML
  - FGDC XML
  - Plain text summary
- **Export Options**: Export single layer or batch export from inventory
- **Import Sources**: Import from files, other QGIS projects, existing layers

#### Metadata Profiles
- **User Profiles**: Store user-specific settings and defaults
- **Project Profiles**: Different profiles for different projects
- **Default Values**: Set defaults for frequently used values

### Storage and Persistence

#### Local Storage
- **SQLite Database**: Store reusable components in SQLite database
  - Organizations table
  - Keywords table
  - Templates table
  - Settings table
- **User Data Directory**: Store in QGIS user profile directory
- **Backup/Restore**: Export/import entire library

#### Template Storage
- **JSON/XML Format**: Store templates in portable format
- **Share Templates**: Export templates for sharing with team
- **Import Templates**: Import templates from colleagues

## User Interface Requirements

### Main Plugin Window
- **Dockable Panel**: Can be docked in QGIS interface or floating
- **Tab-Based Interface**:
  - Tab 1: Create/Edit Metadata
  - Tab 2: Libraries (Organizations, Keywords, Templates)
  - Tab 3: Inventory Integration
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

### Inventory Integration Panel
- **Database Selector**: Browse for inventory GeoPackage
- **Layer List**: Filterable/sortable list of layers from inventory
- **Metadata Status Column**: Visual indicator of metadata presence
- **Bulk Actions**:
  - Select multiple layers
  - Apply template to selected
  - Export metadata for selected
- **Progress View**: Show completion status

## Technical Requirements

### QGIS Plugin Structure
- **Plugin Type**: QGIS Python plugin (PyQGIS)
- **Minimum QGIS Version**: QGIS 3.40 or higher
- **Plugin Category**: Metadata/Documentation
- **Dependencies**: Only PyQGIS and Qt (no external dependencies)

### Data Storage
- **SQLite Database**: For organizations, keywords, templates
- **QGIS Settings**: For user preferences and defaults
- **Layer Metadata**: Direct integration with QGIS layer metadata API

### QGIS Integration
- **Layer Metadata API**: Use `QgsLayerMetadata` for metadata handling
- **Layer Tree Integration**: Context menu item for "Edit Metadata with Manager"
- **Processing Integration**: Optional processing algorithms for batch operations
- **Project Save Integration**: Metadata saved with QGIS project

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

## Testing Requirements

### Unit Tests
- Metadata field validation
- Template application logic
- Organization/keyword CRUD operations
- Import/export functionality

### Integration Tests
- QGIS layer metadata integration
- Database persistence
- UI interaction tests

### User Acceptance Tests
- Complete metadata creation workflow
- Template creation and application
- Inventory integration workflow
- Batch operations

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

## Future Enhancements (Post v1.0)

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

This implementation will be the first QGIS plugin in the mqs repository, complementing the existing Processing Toolbox scripts by providing a full GUI-based metadata management solution.
