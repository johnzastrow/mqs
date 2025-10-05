# Inventory Miner

A QGIS Processing Toolbox script that recursively scans directories for all GDAL/OGR-supported geospatial files and creates a comprehensive spatial inventory stored in a GeoPackage database with extent polygons in EPSG:4326.

## Overview

This tool creates a searchable, spatial catalog of your geospatial data holdings by automatically discovering and inventorying all georeferenced files. It's particularly useful for:

- **Data discovery and cataloging**: Understanding what geospatial data you have and where it is
- **Collection management**: Tracking large collections of geospatial data across directories
- **Quality assessment**: Identifying missing CRS, empty datasets, corrupted files
- **Metadata harvesting**: Extracting GIS metadata from ISO 19115, FGDC, and ESRI metadata files
- **Spatial visualization**: Creating a map of your data extents in a common CRS (EPSG:4326)
- **Data migration planning**: Assessing data before consolidation or migration projects

## Features

### Automatic Discovery
- **GDAL/OGR-based detection**: Automatically identifies all geospatial files that GDAL/OGR can open
- **Georeference detection**: Recognizes coordinate information in:
  - File headers (GeoTIFF, NetCDF, HDF, etc.)
  - Data bodies (shapefiles, GeoJSON, KML, GPX, GML, etc.)
  - Sidecar files (world files .tfw/.jgw/.pgw, .prj files, .aux.xml)
- **Container enumeration**: Lists all layers within GeoPackage, File Geodatabase, and SpatiaLite databases
- **Non-spatial tables**: Identifies attribute-only tables associated with spatial layers

### Comprehensive Metadata Extraction (61+ fields)

**File System Metadata:**
- File paths (absolute and relative), file names, sizes, dates
- Directory structure and depth
- File creation and modification timestamps

**Spatial Metadata:**
- Coordinate Reference System (CRS/EPSG, WKT)
- Spatial extent in native CRS and EPSG:4326
- Georeference method (header, sidecar, embedded)
- Extent bounding box polygon geometry

**Vector-Specific Metadata:**
- Geometry type (Point, LineString, Polygon, Multi*, etc.)
- Feature count
- Z/M dimensions (3D, measured)
- Field names and data types
- Spatial index presence

**Raster-Specific Metadata:**
- Dimensions (width × height)
- Band count and data types
- Pixel size (resolution)
- NoData values
- Compression type

**GIS Metadata (from XML files):**
- Title, abstract, keywords
- Author/creator information
- ISO 19115 topic categories
- Contact information (name, organization, email, phone)
- URLs and related links
- Lineage and constraints
- Metadata standard (ISO 19115, FGDC, ESRI)

**Quality Indicators:**
- File validity (can be opened)
- CRS presence
- Extent presence
- Data presence (features/pixels)
- Issues flagged (missing CRS, empty datasets, corrupted files, invalid geometries)

### Output

**GeoPackage Database:**
- Creates a polygon layer with extent bounding boxes in EPSG:4326
- One record per discovered layer (including layers within containers)
- Rich attribute table with 61+ metadata fields
- Can append to existing GeoPackage or create new

**Spatial Visualization:**
- Each polygon represents the extent bounding box of a layer
- All extents transformed to EPSG:4326 for consistent mapping
- Visualize your data coverage on a map

## Installation

1. Copy `Scripts/inventory_miner.py` to your QGIS scripts directory:
   - Windows: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\<profile>\processing\scripts\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/<profile>/processing/scripts/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/<profile>/processing/scripts/`

2. Restart QGIS or refresh the Processing Toolbox (click the refresh icon)

3. Look for "Inventory Miner" under "Scripts" → "Data Management" in the Processing Toolbox

## Usage

### Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| **Input Directory** | Top-level directory to scan recursively | Yes | - |
| **Output GeoPackage** | GeoPackage database (new or existing) | Yes | - |
| **Inventory Layer Name** | Name for the inventory layer in the GeoPackage | No | geospatial_inventory |
| **Include Raster Files** | Include raster datasets in inventory | No | True |
| **Include Vector Files** | Include vector datasets in inventory | No | True |
| **Include Non-Spatial Tables** | Include attribute-only tables | No | True |
| **Parse GIS Metadata Files** | Extract metadata from XML files (ISO 19115, FGDC, ESRI) | No | True |
| **Include Sidecar File Information** | Report presence of .prj, world files, .xml | No | True |
| **Validate Files** | Thorough data integrity checking (slower but more thorough) | No | False |

### Basic Workflow

1. **Open QGIS** and access the Processing Toolbox (Processing menu → Toolbox)
2. Navigate to **Scripts** → **Data Management** → **Inventory Miner**
3. **Select input directory** containing geospatial data
4. **Choose output GeoPackage** path (can be new or existing)
5. **Configure options** as needed
6. Click **Run**

### Example Use Cases

#### Use Case 1: Quick Data Discovery
Scan a directory to find all geospatial files:

```
Input Directory: /data/projects/watershed_study/
Output GeoPackage: /data/inventory_watershed.gpkg
Include Rasters: Yes
Include Vectors: Yes
Validate Files: No (fast scan)
```

#### Use Case 2: Comprehensive Quality Assessment
Full validation with metadata parsing:

```
Input Directory: /data/legacy_collections/
Output GeoPackage: /data/inventory_full.gpkg
Parse GIS Metadata: Yes
Include Sidecar Files: Yes
Validate Files: Yes (thorough checking)
```

#### Use Case 3: Raster-Only Inventory
Catalog just raster datasets:

```
Input Directory: /data/imagery/
Output GeoPackage: /data/raster_inventory.gpkg
Include Rasters: Yes
Include Vectors: No
Include Tables: No
```

### Validation Option

The **Validate Files** option provides thorough data integrity checking but is slower:

**When Disabled (Default - Fast):**
- Only attempts to open each file
- Quick scanning
- Basic validity check

**When Enabled (Thorough):**
- **For Vectors**: Reads first feature, checks geometry validity, detects missing CRS and empty datasets
- **For Rasters**: Reads sample pixel data, validates bands, checks for missing CRS and geotransforms
- **Issues Flagged**:
  - "Cannot read features/data"
  - "Missing geometries"
  - "Invalid geometries detected"
  - "Missing CRS"
  - "Missing geotransform"
  - "Empty dataset"
  - "Band {n} is invalid"

**Recommendation**: Use validation for quality assessment projects or when troubleshooting data issues. Skip for quick discovery scans.

## Output Fields

The inventory GeoPackage layer contains **61 attribute fields** organized into categories:

### ID and Timestamps (3 fields)
- `id` - Auto-incrementing unique identifier
- `record_created` - When inventory record was created
- `file_created` - File creation date

### File System (7 fields)
- `file_path`, `relative_path`, `file_name`
- `file_size_bytes`, `file_modified`
- `directory_depth`, `parent_directory`

### Format/Driver (6 fields)
- `data_type`, `format`, `driver_name`
- `container_file`, `layer_name`, `is_supporting_table`

### Spatial (6 fields)
- `crs_authid`, `crs_wkt`
- `native_extent`, `wgs84_extent`
- `has_crs`, `georeference_method`

### Vector-Specific (5 fields)
- `geometry_type`, `feature_count`
- `has_z`, `has_m`, `has_spatial_index`

### Raster-Specific (8 fields)
- `raster_width`, `raster_height`, `band_count`
- `pixel_size_x`, `pixel_size_y`
- `data_types`, `nodata_values`, `compression`

### Attributes (3 fields)
- `field_count`, `field_names`, `field_types`

### GIS Metadata (14 fields)
- `metadata_present`, `metadata_file_path`, `metadata_standard`
- `layer_title`, `layer_abstract`, `keywords`
- `metadata_author`, `metadata_date`
- `lineage`, `constraints`
- `url`, `iso_categories`, `contact_info`, `links`

### Sidecar Files (4 fields)
- `has_prj_file`, `has_world_file`
- `has_aux_xml`, `has_metadata_xml`

### Quality (5 fields)
- `is_valid`, `has_extent`, `has_data`
- `issues`, `scan_timestamp`

### Geometry
- `extent_geom` - Polygon representing bounding box in EPSG:4326

## Supported Formats

**Vector Formats:**
- Shapefiles (.shp)
- GeoJSON (.geojson, .json)
- KML/KMZ (.kml, .kmz)
- GPX (.gpx)
- GML (.gml)
- MapInfo (.tab, .mif)
- DXF, DWG (AutoCAD)
- And all other OGR-supported vector formats

**Raster Formats:**
- GeoTIFF (.tif, .tiff)
- JPEG with world file (.jpg + .jgw)
- PNG with world file (.png + .pgw)
- Erdas Imagine (.img)
- ECW, MrSID
- NetCDF, HDF, GRIB
- And all other GDAL-supported raster formats

**Container Formats:**
- GeoPackage (.gpkg) - vectors and rasters
- File Geodatabase (.gdb)
- SpatiaLite (.sqlite, .db)

**Non-Spatial:**
- Standalone dBase files (.dbf)
- Attribute tables from container formats

## Example Scenarios

### Scenario 1: Legacy Data Assessment
You inherit a collection of geospatial data spread across hundreds of directories. Use Inventory Miner to:

1. **Discover** all geospatial files automatically
2. **Visualize** data coverage on a map using extent polygons
3. **Identify** missing CRS, empty datasets, or corrupted files
4. **Extract** metadata from old ISO 19115/FGDC metadata files
5. **Plan** data consolidation or migration

### Scenario 2: Project Data Management
During a long-running project, data accumulates in various formats. Use Inventory Miner to:

1. **Catalog** all project data in one searchable database
2. **Track** what data exists and where it's located
3. **Monitor** data quality with validation checks
4. **Document** data holdings for project reporting

### Scenario 3: Archive Preparation
Before archiving or migrating data, use Inventory Miner to:

1. **Document** complete data inventory with metadata
2. **Verify** data integrity with validation
3. **Export** inventory for archival documentation
4. **Map** spatial coverage of collections

## Tips and Best Practices

### Performance
- **Disable validation** for initial discovery scans (much faster)
- **Enable validation** only when assessing data quality
- **Large collections**: Process in batches by subdirectory
- **Network drives**: Copy data locally first for better performance

### Metadata Extraction
- Works best with properly formatted ISO 19115, FGDC, or ESRI metadata XML files
- Metadata files should have same name as data file with .xml extension
- Alternatively, shapefile metadata can be in .shp.xml format

### Quality Checks
- Review the `issues` field to identify problematic files
- Filter by `is_valid = False` to find corrupted files
- Filter by `has_crs = False` to find files missing coordinate systems
- Filter by `has_data = False` to find empty datasets

### Querying the Inventory
Use QGIS attribute table or SQL queries to find specific data:

```sql
-- Find all data in a specific CRS
SELECT * FROM geospatial_inventory WHERE crs_authid = 'EPSG:4326'

-- Find all GeoTIFFs
SELECT * FROM geospatial_inventory WHERE format LIKE '%GeoTIFF%'

-- Find files with issues
SELECT * FROM geospatial_inventory WHERE issues IS NOT NULL

-- Find data from a specific project
SELECT * FROM geospatial_inventory WHERE relative_path LIKE '%watershed_study%'
```

## Troubleshooting

**Problem**: Script doesn't find expected files

**Solution**:
- Verify files can be opened in QGIS
- Check if GDAL/OGR supports the format
- Ensure files have proper extensions
- For rasters without georeference, ensure sidecar files exist

**Problem**: Validation is very slow

**Solution**:
- Disable "Validate Files" option for faster scanning
- Validation reads actual data, which is slow for large files
- Use validation only for quality assessment, not routine discovery

**Problem**: Missing metadata fields

**Solution**:
- Ensure metadata XML files exist alongside data files
- Check metadata file naming (.xml or .shp.xml)
- Verify XML is valid ISO 19115, FGDC, or ESRI format
- Enable "Parse GIS Metadata Files" option

## Version History

See `CHANGELOG.md` for detailed version history.

## Requirements

- QGIS 3.40 or higher
- PyQGIS libraries (included with QGIS)
- GDAL/OGR (included with QGIS)

## Technical Details

See `REQUIREMENTS.md` for detailed technical specifications.

## License

MIT License - See repository root for details.

## Author

Part of the MQS (My QGIS Stuff) collection.
