# Multi-User Tracking Features

**Version:** 0.6.0
**Date:** October 7, 2025
**Purpose:** Prepare for PostGIS sync in future versions

## Overview

The inventory now captures comprehensive tracking information to support multi-user organizations that will sync local GeoPackage inventories to a central PostGIS database.

## New Tracking Fields

### User & Machine Tracking

**Who scanned this data?**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `scanned_by_user` | String | Username who ran the scan | "jzastrow" |
| `scanned_by_machine` | String | Computer hostname | "GIS-WORKSTATION-01" |
| `scanned_from_os` | String | Operating system | "Windows", "Linux", "Darwin" |
| `scanned_from_os_version` | String | OS version details | "10.0.19045" |

**Use Cases:**
- Track which team member cataloged which data
- Identify duplicate scans from different users
- Contact person if questions about data location
- Audit trail for data discovery

### Storage Location Tracking

**Where is this data stored?**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `storage_location` | String | 'local' or 'network' | "network" |
| `network_server` | String | Server name if UNC path | "FILESERVER01" |
| `drive_or_mount` | String | Drive letter or mount point | "C:", "S:", "/mnt/gisdata" |

**Detection Logic:**
```python
# UNC paths: \\server\share\data
if path.startswith('\\\\') or path.startswith('//'):
    storage_location = 'network'
    network_server = extract_server_name(path)
else:
    storage_location = 'local'
    drive_or_mount = 'C:' or '/mnt/gisdata'
```

**Use Cases:**
- Identify data on network shares vs local drives
- Find all data on specific server
- Migration planning (move data to new server)
- Storage cost allocation by server

### PostGIS Sync Tracking

**Synchronization with central database**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `sync_status` | String | 'not_synced', 'synced', 'conflict' | "synced" |
| `last_sync_date` | String | ISO timestamp of last sync | "2025-10-07T14:30:00" |
| `postgis_id` | Integer | ID in central PostGIS database | 12345 |

**Workflow (Future Version):**
1. User runs inventory scan → Creates local GeoPackage
2. `sync_status` = 'not_synced' for all records
3. User clicks "Sync to PostGIS" button
4. Plugin uploads new/changed records to central database
5. `sync_status` = 'synced', `postgis_id` assigned
6. If conflicts detected → `sync_status` = 'conflict'

**Use Cases:**
- Know which records need to be uploaded
- Resolve conflicts when multiple users scan same data
- Track central database IDs for updates
- Incremental sync (only upload changes)

### Organizational Fields

**Data governance and management**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `organization` | String | Department/org that owns data | "Planning Department" |
| `data_steward` | String | Person responsible for data | "Jane Smith" |
| `project_name` | String | Project this data belongs to | "2024 Zoning Update" |
| `data_classification` | String | Sensitivity level | "public", "internal", "confidential" |
| `retention_policy` | String | How long to keep | "7 years", "permanent" |

**Use Cases:**
- Organize inventory by department
- Contact data steward with questions
- Filter data by project
- Apply access controls based on classification
- Automate deletion per retention policy

### Quality Score

**Automated data quality assessment**

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `quality_score` | Double | Automated quality score | 0.0 - 100.0 |

**Calculation Formula:**
```
Points:
+ 20: Has CRS defined
+ 20: Has extent defined
+ 20: Has metadata (FGDC/ESRI/ISO/.qmd)
+ 15: Has field info (vectors) or band info (rasters)
+ 15: Valid data (no corruption)
+ 10: No validation issues
────
100: Maximum score
```

**Quality Tiers:**
- **90-100**: Excellent - Complete documentation
- **70-89**: Good - Minor gaps
- **50-69**: Fair - Missing key info
- **0-49**: Poor - Needs attention

**Use Cases:**
- Prioritize metadata creation (focus on low scores)
- Dashboard visualization (quality heatmap)
- Quality metrics reporting
- Identify problematic datasets

## Database Schema

### New Fields Added to `geospatial_inventory` Table

```sql
-- User & Machine Tracking
scanned_by_user TEXT,          -- Username
scanned_by_machine TEXT,       -- Hostname
scanned_from_os TEXT,          -- OS name
scanned_from_os_version TEXT,  -- OS version

-- Storage Location
storage_location TEXT,         -- 'local' or 'network'
network_server TEXT,           -- Server name if network
drive_or_mount TEXT,           -- Drive letter or mount point

-- PostGIS Sync
sync_status TEXT,              -- 'not_synced', 'synced', 'conflict'
last_sync_date TEXT,           -- ISO timestamp
postgis_id INTEGER,            -- Central DB ID

-- Organization
organization TEXT,             -- Department/org
data_steward TEXT,             -- Responsible person
project_name TEXT,             -- Project name
data_classification TEXT,      -- Sensitivity
retention_policy TEXT,         -- Retention period
quality_score REAL             -- 0-100 score
```

## Example Data

### Sample Record
```
File: \\FILESERVER01\GISData\projects\zoning\parcels.shp

scanned_by_user:        jzastrow
scanned_by_machine:     GIS-WORKSTATION-01
scanned_from_os:        Windows
scanned_from_os_version: 10.0.19045
storage_location:       network
network_server:         FILESERVER01
drive_or_mount:         S:
sync_status:            not_synced
last_sync_date:         null
postgis_id:             null
organization:           Planning Department
data_steward:           Jane Smith
project_name:           2024 Zoning Update
data_classification:    internal
retention_policy:       7 years
quality_score:          85.0
```

## Multi-User Scenarios

### Scenario 1: Department Scans
**Setup:** Planning, Engineering, and Parks departments each scan their data

**Result:**
```
Record 1: scanned_by_user="jsmith"  machine="PLANNING-PC"   server="FILESERVER01"
Record 2: scanned_by_user="bjones"  machine="ENGINEER-WS"   server="FILESERVER02"
Record 3: scanned_by_user="mwilson" machine="PARKS-LAPTOP"  server="FILESERVER01"
```

**Queries:**
- All data scanned by Planning: `WHERE scanned_by_machine LIKE 'PLANNING%'`
- All data on FILESERVER01: `WHERE network_server = 'FILESERVER01'`
- Who scanned this data?: `SELECT scanned_by_user, scanned_by_machine`

### Scenario 2: Duplicate Detection
**Problem:** Two users scan the same network share

**Detection:**
```sql
SELECT file_path, layer_name, COUNT(*) as scan_count,
       STRING_AGG(scanned_by_user, ', ') as users,
       STRING_AGG(scanned_by_machine, ', ') as machines
FROM geospatial_inventory
WHERE retired_datetime IS NULL
GROUP BY file_path, layer_name
HAVING COUNT(*) > 1
```

**Resolution:**
- Keep most recent scan
- Retire older duplicates
- Notify users of duplicate scans

### Scenario 3: PostGIS Sync Workflow
**Step 1:** Local scans
```
User A: Scans \\SERVER1\data → Creates local_catalog_userA.gpkg
User B: Scans \\SERVER2\data → Creates local_catalog_userB.gpkg
User C: Scans C:\localdata → Creates local_catalog_userC.gpkg
```

**Step 2:** Sync to PostGIS (Future)
```sql
-- User A syncs
INSERT INTO postgis.geospatial_inventory (...)
SELECT * FROM local_catalog_userA.geospatial_inventory
WHERE sync_status = 'not_synced';

UPDATE local_catalog_userA.geospatial_inventory
SET sync_status = 'synced',
    postgis_id = <new_id>,
    last_sync_date = NOW();
```

**Step 3:** Conflict Resolution
```
User A and User B both scanned \\SERVER1\data\roads.shp

Conflict Detection:
- Same file_path
- Different scanned_by_machine
- Different scan_timestamp

Resolution Options:
1. Keep most recent (highest scan_timestamp)
2. Merge metadata (union of extracted info)
3. Flag as conflict for manual review
```

## Future Features (v0.7.0+)

### PostGIS Sync Plugin
- Connect to central PostGIS database
- Upload new/changed records
- Download updates from other users
- Resolve conflicts automatically
- Incremental sync (only changes)

### Organization Management UI
- Dropdown to select organization/department
- Auto-populate data_steward from user list
- Project name autocomplete
- Classification templates

### Quality Dashboard Enhancements
- Quality score histogram
- Lowest quality datasets report
- Quality trends over time
- Department quality comparison

### Network Path Mapping
- Map network drives to UNC paths
- Resolve DFS paths to actual servers
- Track path changes over time
- Alert on moved/renamed files

## Benefits

### For Organizations
- **Centralized catalog** - All users contribute to single inventory
- **Attribution** - Know who scanned what
- **Accountability** - Track data stewards and owners
- **Governance** - Enforce classification and retention
- **Quality metrics** - Measure and improve data quality

### For Users
- **Avoid duplicates** - See what others already scanned
- **Collaboration** - Share inventory with team
- **Offline work** - Scan locally, sync later
- **Audit trail** - Track who did what when

### For IT/GIS Admins
- **Server inventory** - Find all data on each server
- **Migration planning** - Identify data to move
- **License compliance** - Track data by organization
- **Disaster recovery** - Know where critical data lives
- **Cost allocation** - Storage costs by department

## Backward Compatibility

**Important:** All new fields are optional and nullable. Existing inventories will work fine:
- Old inventories don't have these fields → No problem
- New scans populate these fields automatically
- Update mode preserves existing values
- PostGIS sync is opt-in (future feature)

**Migration:** No action needed. When you run a new scan, the new fields are created automatically.

## Conclusion

These multi-user tracking features prepare Metadata Manager for enterprise deployment with central PostGIS databases, while remaining fully functional for single-user local GeoPackage workflows.

**Current (v0.6.0):** Captures tracking data during scan
**Future (v0.7.0+):** Sync to PostGIS, conflict resolution, organization management

The foundation is laid! 🎯
