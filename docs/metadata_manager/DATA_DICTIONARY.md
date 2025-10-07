# Metadata Manager GeoPackage Data Dictionary

**Version:** 0.6.0
**Date:** October 7, 2025
**Database Type:** SQLite GeoPackage (.gpkg)
**Purpose:** Unified database for geospatial inventory and metadata management

---

## Table of Contents

1. [Overview](#overview)
2. [Table Relationships](#table-relationships)
3. [Table Definitions](#table-definitions)
   - [geospatial_inventory](#geospatial_inventory) (Created by Inventory Scanner)
   - [metadata_cache](#metadata_cache) (Metadata Manager)
   - [organizations](#organizations) (Metadata Manager)
   - [contacts](#contacts) (Metadata Manager)
   - [keywords](#keywords) (Metadata Manager)
   - [keyword_sets](#keyword_sets) (Metadata Manager)
   - [keyword_set_members](#keyword_set_members) (Metadata Manager)
   - [templates](#templates) (Metadata Manager)
   - [settings](#settings) (Metadata Manager)
   - [plugin_info](#plugin_info) (Shared)
   - [upgrade_history](#upgrade_history) (Metadata Manager)

---

## Overview

The Metadata Manager GeoPackage is a unified database containing:

1. **Geospatial Inventory** - Comprehensive catalog of discovered geospatial files
2. **Metadata Cache** - Working metadata for layers being edited
3. **Reusable Resources** - Organizations, contacts, keywords, templates
4. **System Tables** - Version tracking, settings, upgrade history

**Key Design Principles:**
- Single database for both inventory and metadata management
- Non-destructive workflow (preserves existing metadata files)
- Multi-user tracking for future PostGIS synchronization
- Automated quality scoring
- Full audit trail

---

## Table Relationships

```
geospatial_inventory (independent spatial table)
    ↓
metadata_cache (links via layer_path)

organizations ← contacts (many contacts per org)

keywords ← keyword_set_members → keyword_sets

templates (independent)
settings (independent)
plugin_info (independent)
upgrade_history (independent)
```

---

## Table Definitions

---

### geospatial_inventory

**Purpose:** Comprehensive catalog of all discovered geospatial data files

**Created By:** Inventory Scanner (processors/inventory_processor.py)

**Geometry:** POLYGON (bounding box of layer extent)

**Spatial Index:** Yes

**Primary Key:** Integer rowid (SQLite/GeoPackage default)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| **Core Identification** |
| `file_path` | TEXT | No | Full absolute path to file | `/data/parcels.shp` | Unique identifier |
| `relative_path` | TEXT | Yes | Path relative to scan root | `county/parcels.shp` | For portability |
| `file_name` | TEXT | No | Filename with extension | `parcels.shp` | |
| `parent_directory` | TEXT | Yes | Parent directory name | `county` | |
| `layer_name` | TEXT | No | Layer/feature class name | `parcels` | May differ from file_name for GDB |
| **File Characteristics** |
| `data_type` | TEXT | Yes | `vector`, `raster`, or `table` | `vector` | |
| `format` | TEXT | Yes | File format | `ESRI Shapefile` | Human-readable |
| `driver_name` | TEXT | Yes | GDAL/OGR driver | `ESRI Shapefile` | Technical name |
| `file_size_bytes` | INTEGER | Yes | File size in bytes | `1048576` | |
| `file_size_mb` | REAL | Yes | File size in megabytes | `1.0` | Computed |
| `file_created` | TEXT | Yes | File creation timestamp | `2024-01-15T10:30:00` | ISO 8601 |
| `file_modified` | TEXT | Yes | File modification timestamp | `2024-06-20T14:15:00` | ISO 8601 |
| **Multi-User Tracking** |
| `scanned_by_user` | TEXT | Yes | Username who ran scan | `jzastrow` | `getpass.getuser()` |
| `scanned_by_machine` | TEXT | Yes | Computer hostname | `GIS-WORKSTATION-01` | `socket.gethostname()` |
| `scanned_from_os` | TEXT | Yes | Operating system | `Windows`, `Linux`, `Darwin` | `platform.system()` |
| `scanned_from_os_version` | TEXT | Yes | OS version | `10.0.19045` | `platform.version()` |
| `storage_location` | TEXT | Yes | Storage type | `local`, `network` | Detected from path |
| `network_server` | TEXT | Yes | Server name (UNC paths) | `FILESERVER01` | Parsed from `\\SERVER\share` |
| `drive_or_mount` | TEXT | Yes | Drive letter or mount point | `C:`, `S:`, `/mnt/gisdata` | |
| **Spatial Reference** |
| `crs_authid` | TEXT | Yes | CRS authority ID | `EPSG:4326` | |
| `crs_wkt` | TEXT | Yes | CRS as WKT | `GEOGCS["WGS 84"...]` | Full definition |
| `native_extent` | TEXT | Yes | Bounding box in native CRS | `xmin,ymin,xmax,ymax` | CSV format |
| `wgs84_extent` | TEXT | Yes | Bounding box in WGS84 | `-180,-90,180,90` | CSV format |
| `has_crs` | BOOLEAN | Yes | Has defined CRS | `1` | |
| `has_extent` | BOOLEAN | Yes | Has extent defined | `1` | |
| **Vector Characteristics** |
| `geometry_type` | TEXT | Yes | Geometry type | `Polygon`, `Point`, `LineString` | OGR wkbGeometryType |
| `feature_count` | INTEGER | Yes | Number of features | `5432` | -1 if unknown |
| `field_count` | INTEGER | Yes | Number of attributes | `12` | |
| `field_names` | TEXT | Yes | Comma-separated field names | `OBJECTID,NAME,AREA` | |
| `field_types` | TEXT | Yes | Comma-separated field types | `Integer,String,Real` | |
| **Raster Characteristics** |
| `raster_width` | INTEGER | Yes | Pixel width | `1024` | |
| `raster_height` | INTEGER | Yes | Pixel height | `768` | |
| `band_count` | INTEGER | Yes | Number of bands | `3` | RGB = 3 |
| `pixel_width` | REAL | Yes | Pixel size X | `30.0` | In native CRS units |
| `pixel_height` | REAL | Yes | Pixel size Y | `30.0` | In native CRS units |
| `data_types` | TEXT | Yes | Band data types | `Byte,Byte,Byte` | CSV format |
| `nodata_value` | TEXT | Yes | NoData value(s) | `-9999` | CSV if multi-band |
| **Metadata Extraction** |
| `metadata_present` | BOOLEAN | Yes | Metadata found | `1` | Any format |
| `metadata_file_path` | TEXT | Yes | Path to metadata file | `/data/parcels.xml` | External sidecar |
| `metadata_standard` | TEXT | Yes | Metadata standard | `FGDC`, `ISO 19115`, `ESRI`, `.qmd` | |
| `layer_title` | TEXT | Yes | Title from metadata | `County Parcel Boundaries` | |
| `layer_abstract` | TEXT | Yes | Abstract/summary | `Tax parcel polygons...` | |
| `keywords` | TEXT | Yes | Comma-separated keywords | `parcels,cadastral,property` | |
| `lineage` | TEXT | Yes | Data lineage/history | `Digitized from surveys...` | |
| `constraints` | TEXT | Yes | Use constraints | `Public domain` | |
| `url` | TEXT | Yes | Related URL | `https://gis.county.gov` | |
| `contact_info` | TEXT | Yes | Contact information | `GIS Dept, 555-1234` | |
| **Sidecar Files** |
| `has_prj_file` | BOOLEAN | Yes | Has .prj file | `1` | Shapefiles |
| `has_aux_xml` | BOOLEAN | Yes | Has .aux.xml file | `1` | GDAL auxiliary |
| `has_metadata_xml` | BOOLEAN | Yes | Has .xml metadata | `1` | FGDC/ISO sidecar |
| **Validation** |
| `issues` | TEXT | Yes | Validation issues | `Missing CRS` | Comma-separated |
| **Audit Trail** |
| `record_created` | TEXT | Yes | Record creation date | `2025-10-07T10:00:00` | ISO 8601 |
| `scan_timestamp` | TEXT | Yes | When this file was scanned | `2025-10-07T10:05:30` | ISO 8601 |
| `metadata_status` | TEXT | Yes | Metadata workflow status | `complete`, `needs_metadata`, `in_progress` | Updated by Metadata Manager |
| `metadata_last_updated` | TEXT | Yes | Last metadata edit | `2025-10-07T11:30:00` | ISO 8601 |
| `metadata_target` | TEXT | Yes | Where to write metadata | `embedded`, `sidecar`, `qmd` | User choice |
| `metadata_cached` | BOOLEAN | Yes | In metadata_cache table | `1` | Link to metadata_cache |
| `retired_datetime` | TEXT | Yes | Soft-delete timestamp | `2025-10-07T15:00:00` | NULL = active |
| **PostGIS Synchronization** |
| `sync_status` | TEXT | Yes | Sync state | `not_synced`, `synced`, `conflict` | For future PostGIS sync |
| `last_sync_date` | TEXT | Yes | Last sync to PostGIS | `2025-10-07T16:00:00` | ISO 8601 |
| `postgis_id` | INTEGER | Yes | Central database ID | `12345` | Foreign key to PostGIS |
| **Organization** |
| `organization` | TEXT | Yes | Owning department | `Planning Department` | |
| `data_steward` | TEXT | Yes | Responsible person | `Jane Smith` | |
| `project_name` | TEXT | Yes | Related project | `2024 Zoning Update` | |
| `data_classification` | TEXT | Yes | Sensitivity level | `public`, `internal`, `confidential` | |
| `retention_policy` | TEXT | Yes | Retention period | `7 years`, `permanent` | |
| **Quality Metrics** |
| `quality_score` | REAL | Yes | Automated quality score | `85.0` | 0-100 scale |
| **Geometry** |
| `geom` | GEOMETRY | No | Bounding box polygon | POLYGON(...) | EPSG:4326, spatially indexed |

#### Quality Score Calculation

```python
score = 0.0
if has_crs: score += 20
if has_extent: score += 20
if metadata_present: score += 20
if (field_count > 0 or band_count > 0): score += 15
if valid_data: score += 15
if not issues: score += 10
# Total: 100 possible points
```

**Quality Tiers:**
- **90-100**: Excellent - Complete documentation
- **70-89**: Good - Minor gaps
- **50-69**: Fair - Missing key information
- **0-49**: Poor - Needs attention

#### Update Mode Behavior

When running inventory scan in **Update Mode**:

**Preserved Fields:**
- `metadata_status`
- `metadata_last_updated`
- `metadata_target`
- `metadata_cached`

**Refreshed Fields:**
- All file characteristics (size, modified date)
- Spatial reference
- Feature/band counts
- Scan metadata (timestamp, user, machine)

**Retired Records:**
- Files deleted from disk → `retired_datetime` set to current timestamp
- NOT deleted from database (soft delete for audit trail)

---

### metadata_cache

**Purpose:** Working storage for metadata being created/edited in Metadata Manager

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

**Indexes:**
- `idx_metadata_cache_path` on `layer_path`
- `idx_metadata_cache_sync` on `in_sync`

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `layer_path` | TEXT | No | Full path to layer file | `/data/parcels.shp` | UNIQUE |
| `layer_name` | TEXT | No | Display name | `parcels` | |
| `file_type` | TEXT | Yes | File format | `ESRI Shapefile` | |
| `metadata_json` | TEXT | No | Full metadata structure | `{"title": "...", ...}` | JSON format |
| `created_date` | TIMESTAMP | No | First cached | `2025-10-07 10:00:00` | SQLite timestamp |
| `last_edited_date` | TIMESTAMP | No | Last edited in UI | `2025-10-07 11:30:00` | Auto-updated |
| `last_written_date` | TIMESTAMP | Yes | Last written to file | `2025-10-07 11:35:00` | NULL if not written |
| `target_location` | TEXT | Yes | Where to write | `embedded`, `sidecar`, `qmd` | User preference |
| `in_sync` | INTEGER | No | Cache matches file | `1` | 1=synced, 0=dirty |

#### Metadata JSON Structure

The `metadata_json` field contains a JSON object with the following structure:

```json
{
  "title": "Layer Title",
  "abstract": "Description of the layer...",
  "keywords": ["keyword1", "keyword2"],
  "categories": ["category1"],
  "language": "ENG",
  "encoding": "UTF-8",
  "crs": "EPSG:4326",
  "extent": {
    "xmin": -180.0,
    "ymin": -90.0,
    "xmax": 180.0,
    "ymax": 90.0
  },
  "contacts": [
    {
      "name": "Jane Smith",
      "organization": "Planning Department",
      "position": "GIS Coordinator",
      "email": "jsmith@county.gov",
      "role": "pointOfContact"
    }
  ],
  "links": [
    {
      "name": "Website",
      "type": "WWW:LINK",
      "url": "https://gis.county.gov",
      "description": "GIS Portal"
    }
  ],
  "history": ["Created 2024-01-15", "Updated 2024-06-20"],
  "constraints": {
    "access": "Public",
    "use": "No restrictions",
    "other": []
  },
  "fees": "",
  "licenses": ["CC-BY-4.0"]
}
```

#### Sync Status

**`in_sync = 1`**: Cache matches written file
**`in_sync = 0`**: Cache has unsaved changes

Workflow:
1. User edits metadata in wizard → `last_edited_date` updated, `in_sync = 0`
2. User clicks "Save" → Metadata written to file, `last_written_date` updated, `in_sync = 1`
3. User edits again → `in_sync = 0`

---

### organizations

**Purpose:** Reusable organization profiles for metadata contacts

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `name` | TEXT | No | Organization name | `County Planning Department` | |
| `abbreviation` | TEXT | Yes | Short name | `CPD` | |
| `address` | TEXT | Yes | Street address | `123 Main St` | |
| `city` | TEXT | Yes | City | `Anytown` | |
| `state` | TEXT | Yes | State/province | `CA` | |
| `postal_code` | TEXT | Yes | ZIP/postal code | `12345` | |
| `country` | TEXT | Yes | Country | `USA` | |
| `website` | TEXT | Yes | URL | `https://planning.county.gov` | |
| `email` | TEXT | Yes | Contact email | `info@county.gov` | |
| `phone` | TEXT | Yes | Phone number | `555-1234` | |
| `fax` | TEXT | Yes | Fax number | `555-1235` | |
| `logo_path` | TEXT | Yes | Path to logo image | `/logos/county.png` | |
| `created` | TIMESTAMP | No | Record created | `2025-10-07 10:00:00` | Auto |
| `modified` | TIMESTAMP | No | Last modified | `2025-10-07 11:00:00` | Auto-updated |

**Usage:** Select organization from dropdown when adding contacts to metadata

---

### contacts

**Purpose:** Contact information with roles for metadata attribution

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

**Foreign Keys:** `organization_id` → `organizations.id`

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `organization_id` | INTEGER | Yes | Link to organization | `1` | NULL = no org |
| `name` | TEXT | No | Contact name | `Jane Smith` | |
| `position` | TEXT | Yes | Job title | `GIS Coordinator` | |
| `email` | TEXT | Yes | Email address | `jsmith@county.gov` | |
| `phone` | TEXT | Yes | Phone number | `555-1234 x100` | |
| `role` | TEXT | Yes | Metadata role | `pointOfContact`, `originator`, `custodian` | ISO 19115 roles |
| `created` | TIMESTAMP | No | Record created | `2025-10-07 10:00:00` | Auto |
| `modified` | TIMESTAMP | No | Last modified | `2025-10-07 11:00:00` | Auto-updated |

**ISO 19115 Roles:**
- `author` - Creator of the data
- `custodian` - Data steward/maintainer
- `distributor` - Distributes the data
- `originator` - Original source
- `owner` - Legal owner
- `pointOfContact` - General contact
- `principalInvestigator` - Research PI
- `processor` - Processed the data
- `publisher` - Published the data
- `resourceProvider` - Provides the resource

---

### keywords

**Purpose:** Hierarchical keyword library for consistent tagging

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

**Unique Constraint:** `keyword` (no duplicates)

**Foreign Keys:** `parent_id` → `keywords.id` (self-referential)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `keyword` | TEXT | No | Keyword term | `parcels` | UNIQUE |
| `category` | TEXT | Yes | Grouping category | `cadastral`, `environment`, `transportation` | |
| `parent_id` | INTEGER | Yes | Parent keyword ID | `5` | For hierarchies |
| `vocabulary` | TEXT | Yes | Controlled vocabulary | `GCMD`, `ISO 19115`, `Custom` | |
| `created` | TIMESTAMP | No | Record created | `2025-10-07 10:00:00` | Auto |

**Hierarchy Example:**
```
Land Use (id=1, parent_id=NULL)
  ├─ Residential (id=2, parent_id=1)
  ├─ Commercial (id=3, parent_id=1)
  └─ Agricultural (id=4, parent_id=1)
```

---

### keyword_sets

**Purpose:** Predefined collections of keywords for common data themes

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `name` | TEXT | No | Set name | `Cadastral Data` | |
| `description` | TEXT | Yes | Purpose | `Keywords for parcel/ownership data` | |
| `created` | TIMESTAMP | No | Record created | `2025-10-07 10:00:00` | Auto |
| `modified` | TIMESTAMP | No | Last modified | `2025-10-07 11:00:00` | Auto-updated |

**Example Sets:**
- "Cadastral Data" → parcels, property, ownership, tax
- "Transportation" → roads, streets, highways, routes
- "Environmental" → wetlands, habitat, conservation, ecology

---

### keyword_set_members

**Purpose:** Junction table linking keywords to keyword sets (many-to-many)

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** Composite (`set_id`, `keyword_id`)

**Foreign Keys:**
- `set_id` → `keyword_sets.id` (CASCADE DELETE)
- `keyword_id` → `keywords.id` (CASCADE DELETE)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `set_id` | INTEGER | No | Keyword set ID | `1` | |
| `keyword_id` | INTEGER | No | Keyword ID | `5` | |

**Example:**
```sql
-- "Cadastral Data" keyword set (id=1) contains:
INSERT INTO keyword_set_members VALUES (1, 10); -- parcels
INSERT INTO keyword_set_members VALUES (1, 11); -- property
INSERT INTO keyword_set_members VALUES (1, 12); -- ownership
```

---

### templates

**Purpose:** Reusable metadata templates for common data types

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `name` | TEXT | No | Template name | `County Parcel Template` | |
| `description` | TEXT | Yes | Purpose | `Standard metadata for parcel layers` | |
| `metadata_json` | TEXT | No | Template metadata | `{"title": "...", ...}` | Same structure as metadata_cache |
| `created` | TIMESTAMP | No | Record created | `2025-10-07 10:00:00` | Auto |
| `modified` | TIMESTAMP | No | Last modified | `2025-10-07 11:00:00` | Auto-updated |

**Usage:** User selects template → Pre-populates wizard fields → User customizes

---

### settings

**Purpose:** User preferences and plugin defaults

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `key` (TEXT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `key` | TEXT | No | Setting name | `default_contact_id` | Primary key |
| `value` | TEXT | Yes | Setting value | `5` | JSON for complex values |
| `modified` | TIMESTAMP | No | Last modified | `2025-10-07 11:00:00` | Auto-updated |

**Common Settings:**
```sql
INSERT INTO settings VALUES ('default_contact_id', '5', CURRENT_TIMESTAMP);
INSERT INTO settings VALUES ('default_organization_id', '1', CURRENT_TIMESTAMP);
INSERT INTO settings VALUES ('metadata_target', 'qmd', CURRENT_TIMESTAMP);
INSERT INTO settings VALUES ('auto_apply_templates', '1', CURRENT_TIMESTAMP);
```

---

### plugin_info

**Purpose:** Version tracking for both Inventory Scanner and Metadata Manager

**Created By:** Both tools (shared table)

**Primary Key:** `key` (TEXT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `key` | TEXT | No | Info key | `inventory_schema_version` | Primary key |
| `value` | TEXT | Yes | Info value | `0.1.0` | |
| `updated` | TIMESTAMP | No | Last updated | `2025-10-07 10:00:00` | Auto-updated |

**Standard Keys:**
```sql
INSERT INTO plugin_info VALUES
  ('inventory_schema_version', '0.1.0', CURRENT_TIMESTAMP),
  ('inventory_miner_installed', '2025-10-05 09:00:00', CURRENT_TIMESTAMP),
  ('metadata_schema_version', '0.1.0', CURRENT_TIMESTAMP),
  ('metadata_manager_installed', '2025-10-07 10:00:00', CURRENT_TIMESTAMP);
```

---

### upgrade_history

**Purpose:** Track schema upgrades and migrations

**Created By:** Metadata Manager (db/schema.py)

**Primary Key:** `id` (INTEGER AUTOINCREMENT)

#### Fields

| Field Name | Type | Nullable | Description | Example | Notes |
|------------|------|----------|-------------|---------|-------|
| `id` | INTEGER | No | Primary key | `1` | Auto-increment |
| `from_version` | TEXT | Yes | Previous version | `0.5.0` | NULL for initial |
| `to_version` | TEXT | Yes | New version | `0.6.0` | |
| `tool` | TEXT | Yes | Which tool upgraded | `Metadata Manager` | Or "Inventory Scanner" |
| `upgrade_date` | TIMESTAMP | No | When upgraded | `2025-10-07 10:00:00` | Auto |
| `success` | INTEGER | No | Success flag | `1` | 1=success, 0=failed |
| `notes` | TEXT | Yes | Upgrade details | `Added multi-user tracking fields` | |

**Example:**
```sql
INSERT INTO upgrade_history (from_version, to_version, tool, success, notes)
VALUES ('0.5.0', '0.6.0', 'Inventory Scanner', 1,
        'Added 16 multi-user tracking fields for PostGIS sync');
```

---

## Schema Versioning

**Two Independent Version Tracks:**

1. **Inventory Schema** (`plugin_info.inventory_schema_version`)
   - Tracks `geospatial_inventory` table structure
   - Updated by Inventory Scanner
   - Current: 0.1.0

2. **Metadata Schema** (`plugin_info.metadata_schema_version`)
   - Tracks Metadata Manager tables
   - Updated by Metadata Manager
   - Current: 0.1.0

**Upgrade Strategy:**
- Check version on connection
- Apply migrations if needed
- Log in `upgrade_history`
- Update `plugin_info`

---

## Indexes

### geospatial_inventory
- Spatial index on `geom` (automatic for GeoPackage)
- Suggested: `CREATE INDEX idx_inventory_status ON geospatial_inventory(metadata_status);`
- Suggested: `CREATE INDEX idx_inventory_format ON geospatial_inventory(format);`

### metadata_cache
- `idx_metadata_cache_path` on `layer_path` (for lookups)
- `idx_metadata_cache_sync` on `in_sync` (for finding dirty records)

---

## Data Flow

### Inventory → Metadata Workflow

1. **Scan Directory**
   ```
   User: Select directory → Click "Create Inventory"
   System: Scan files → Write to geospatial_inventory
   ```

2. **Browse Inventory**
   ```
   User: View Dashboard → See statistics
   User: View Layer Browser → See all layers
   ```

3. **Select Layer**
   ```
   User: Click layer in browser
   System: Query geospatial_inventory for smart defaults
   System: Check metadata_cache for existing edits
   ```

4. **Edit Metadata**
   ```
   User: Fill wizard fields
   System: Save to metadata_cache (in_sync=0)
   ```

5. **Write Metadata**
   ```
   User: Click "Save and Write"
   System: Write to .qmd/.xml file
   System: Update metadata_cache (in_sync=1)
   System: Update geospatial_inventory (metadata_status='complete')
   ```

---

## Query Examples

### Find all unmetadataed layers
```sql
SELECT file_path, layer_name, format, quality_score
FROM geospatial_inventory
WHERE metadata_status = 'needs_metadata'
  AND retired_datetime IS NULL
ORDER BY quality_score ASC;
```

### Find all layers scanned by specific user
```sql
SELECT file_path, layer_name, scan_timestamp
FROM geospatial_inventory
WHERE scanned_by_user = 'jzastrow'
  AND retired_datetime IS NULL;
```

### Find all data on specific network server
```sql
SELECT file_path, layer_name, file_size_mb
FROM geospatial_inventory
WHERE network_server = 'FILESERVER01'
  AND retired_datetime IS NULL;
```

### Find layers with unsaved metadata changes
```sql
SELECT layer_path, layer_name, last_edited_date
FROM metadata_cache
WHERE in_sync = 0
ORDER BY last_edited_date DESC;
```

### Get complete layer info with metadata status
```sql
SELECT
  i.layer_name,
  i.format,
  i.quality_score,
  i.metadata_status,
  CASE WHEN m.id IS NOT NULL THEN 'Yes' ELSE 'No' END as has_cached_metadata,
  m.last_edited_date
FROM geospatial_inventory i
LEFT JOIN metadata_cache m ON i.file_path = m.layer_path
WHERE i.retired_datetime IS NULL
ORDER BY i.quality_score ASC;
```

### Find duplicate scans (same file, different users)
```sql
SELECT file_path, layer_name,
       COUNT(*) as scan_count,
       GROUP_CONCAT(scanned_by_user) as users
FROM geospatial_inventory
WHERE retired_datetime IS NULL
GROUP BY file_path, layer_name
HAVING COUNT(*) > 1;
```

---

## Maintenance

### Soft Delete Cleanup
```sql
-- View retired records
SELECT file_path, layer_name, retired_datetime
FROM geospatial_inventory
WHERE retired_datetime IS NOT NULL;

-- Permanently delete old retired records (e.g., >1 year)
DELETE FROM geospatial_inventory
WHERE retired_datetime < date('now', '-1 year');
```

### Metadata Cache Cleanup
```sql
-- Find stale cache entries (no recent edits, not written)
SELECT layer_path, last_edited_date
FROM metadata_cache
WHERE last_written_date IS NULL
  AND last_edited_date < date('now', '-30 days');

-- Delete stale cache
DELETE FROM metadata_cache
WHERE last_written_date IS NULL
  AND last_edited_date < date('now', '-30 days');
```

### Vacuum Database
```sql
-- Reclaim space after deletions
VACUUM;
```

---

## Backup Recommendations

**Critical Tables:**
- `geospatial_inventory` - Hours of scanning work
- `metadata_cache` - Unsaved metadata edits
- `organizations`, `contacts`, `keywords` - Reusable resources

**Backup Strategy:**
```bash
# Full database backup
cp geospatial_catalog.gpkg geospatial_catalog_backup_2025-10-07.gpkg

# Export specific tables
ogr2ogr -f GPKG backup.gpkg original.gpkg geospatial_inventory
sqlite3 original.gpkg ".dump metadata_cache" > metadata_cache_backup.sql
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.6.0 | 2025-10-07 | Added multi-user tracking fields (16 new fields), quality scoring |
| 0.5.0 | 2025-10-06 | Added smart defaults support |
| 0.1.0 | 2025-10-05 | Initial schema |

---

## References

- **QGIS Metadata Specification**: https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/vector_properties.html#metadata-properties
- **ISO 19115 Geographic Metadata**: https://www.iso.org/standard/53798.html
- **FGDC CSDGM**: https://www.fgdc.gov/metadata/csdgm-standard
- **OGC GeoPackage**: https://www.geopackage.org/spec/

---

**Document Maintained By:** Metadata Manager Plugin
**Last Updated:** October 7, 2025
