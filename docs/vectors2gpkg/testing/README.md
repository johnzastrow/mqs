# Testing Documentation for vectors2gpkg

This directory contains testing resources and documentation for the vectors2gpkg subproject.

## Test Data Structure

The testing directory contains sample vector files organized in a realistic directory structure to test the recursive processing capabilities of the script:

```
testing/
├── Biota_Ecological/
│   └── 2022/
│       └── Ecological/
│           ├── communities.shp (+ .dbf, .shx, .prj)
│           ├── Core.shp (+ .dbf, .shx, .prj)
│           ├── management concerns.shp (+ .dbf, .shx, .prj)
│           ├── monitor points.shp (+ .dbf, .shx, .prj)
│           ├── nwi.shp (+ .dbf, .shx, .prj)
│           ├── reserve1.shp (+ .dbf, .shx, .prj)
│           ├── Sensitive Plants.shp (+ .dbf, .shx, .prj)
│           └── spec.mgmt.zone.shp (+ .dbf, .shx, .prj)
├── Boundaries/
│   ├── 2023/
│   │   └── property_100m_grid.shp (+ .dbf, .shx, .prj)
│   ├── 2022/
│   │   ├── GPMCT/
│   │   │   ├── gpmct_area_of_interest.shp (+ .dbf, .shx, .prj)
│   │   │   ├── property_hatchery_poly.shp (+ .dbf, .shx, .prj)
│   │   │   ├── property_wildlands_line.shp (+ .dbf, .shx, .prj)
│   │   │   ├── property_wildlands_poly.shp (+ .dbf, .shx, .prj)
│   │   │   └── ARCHIVE/
│   │   │       ├── Bounds_GPMCT-2014.shp (+ .dbf, .shx, .prj)
│   │   │       ├── property_boyle_poly.shp (+ .dbf, .shx, .prj)
│   │   │       ├── property_dead_river_west_poly.shp (+ .dbf, .shx, .prj)
│   │   │       ├── property_hatchery_line.shp (+ .dbf, .shx, .prj)
│   │   │       ├── property_mercer_poly.shp (+ .dbf, .shx, .prj)
│   │   │       └── property_wildlands_polybowtie.shp (+ .dbf, .shx, .prj)
│   │   └── State/
│   │       ├── boundary_maine_no_coast_line.shp (+ .dbf, .shx, .prj)
│   │       ├── boundary_maine_poly.shp (+ .dbf, .shx, .prj)
│   │       ├── county_maine_poly.shp (+ .dbf, .shx, .prj)
│   │       └── state_province_northeast_poly.shp (+ .dbf, .shx, .prj)
└── Cadastre/
    └── 2022/
        ├── Parcels2017.shp (+ .dbf, .shx, .prj)
        └── towns_wildlands_poly.shp (+ .dbf, .shx, .prj)
```

## Test Scenarios

### Basic Functionality Tests

1. **Recursive Directory Processing**
   - Tests the script's ability to find shapefiles in nested directories
   - Verifies all 25 test shapefiles are discovered

2. **Layer Naming Tests**
   - Tests name sanitization for files with special characters
   - Examples:
     - `management concerns.shp` → `management_concerns`
     - `Bounds_GPMCT-2014.shp` → `Bounds_GPMCT_2014`
     - `spec.mgmt.zone.shp` → `spec_mgmt_zone`

3. **GeoPackage Creation**
   - Tests creation of a single GeoPackage file
   - Verifies all layers are properly added
   - Tests spatial index creation

4. **Feature Count Verification**
   - Verifies feature counts are preserved during conversion
   - Test data includes:
     - Small datasets (1-3 features)
     - Medium datasets (19-111 features)
     - Large datasets (6,942-666,211 features)

### Error Handling Tests

1. **Empty Geometry Tests**
   - `gpmct_area_of_interest.shp` contains 0 features (tests empty layer handling)

2. **Special Character Handling**
   - Files with spaces in names
   - Files with special characters (dots, hyphens)

3. **Nested Directory Tests**
   - Files in deeply nested directory structures
   - Mixed directory levels

### Performance Tests

1. **Large Dataset Processing**
   - `Parcels2017.shp` with 666,211 features
   - `county_maine_poly.shp` with 6,890 features
   - `nwi.shp` with 32,951 features

2. **Memory Management**
   - Processing multiple large files sequentially
   - Verifying memory usage remains reasonable

## Test Execution

### Manual Testing

1. **Basic Test Run**:
   ```
   Input Directory: [path_to]/docs/shapefiles2gpkg/testing
   Output GeoPackage: test_output.gpkg
   Apply Styles: True
   Create Spatial Index: True
   ```

2. **Expected Results**:
   - 25 shapefiles should be processed
   - 0 errors (all files should process successfully)
   - Output GeoPackage should contain 25 layers
   - Layer names should be properly sanitized

### Automated Testing

Future automated tests should verify:

1. **Layer Count**: Verify exactly 25 layers are created
2. **Feature Counts**: Compare input vs output feature counts
3. **Geometry Types**: Verify geometry types are preserved
4. **Attribute Tables**: Verify all attributes are transferred correctly
5. **Coordinate Systems**: Verify CRS information is preserved

## Expected Output Layers

When processing the test data, the following layers should be created in the GeoPackage:

| Original Filename | Expected Layer Name | Feature Count | Geometry Type |
|-------------------|-------------------|---------------|---------------|
| communities.shp | communities | 111 | Polygon |
| Core.shp | Core | 3 | Polygon |
| management concerns.shp | management_concerns | 28 | Polygon |
| monitor points.shp | monitor_points | 72 | Point |
| nwi.shp | nwi | 32,951 | Polygon |
| reserve1.shp | reserve1 | 3 | Polygon |
| Sensitive Plants.shp | Sensitive_Plants | 19 | Point |
| spec.mgmt.zone.shp | spec_mgmt_zone | 1 | Polygon |
| property_100m_grid.shp | property_100m_grid | 6,942 | Polygon |
| gpmct_area_of_interest.shp | gpmct_area_of_interest | 0 | Polygon |
| property_hatchery_poly.shp | property_hatchery_poly | 1 | Polygon |
| property_wildlands_line.shp | property_wildlands_line | 4 | LineString |
| property_wildlands_poly.shp | property_wildlands_poly | 3 | Polygon |
| boundary_maine_no_coast_line.shp | boundary_maine_no_coast_line | 32 | LineString |
| boundary_maine_poly.shp | boundary_maine_poly | 96 | Polygon |
| county_maine_poly.shp | county_maine_poly | 6,890 | Polygon |
| state_province_northeast_poly.shp | state_province_northeast_poly | 2,055 | Polygon |
| Bounds_GPMCT-2014.shp | Bounds_GPMCT_2014 | 2 | Polygon |
| property_boyle_poly.shp | property_boyle_poly | 1 | Polygon |
| property_dead_river_west_poly.shp | property_dead_river_west_poly | 1 | Polygon |
| property_hatchery_line.shp | property_hatchery_line | 2 | LineString |
| property_mercer_poly.shp | property_mercer_poly | 1 | Polygon |
| property_wildlands_polybowtie.shp | property_wildlands_polybowtie | 3 | Polygon |
| Parcels2017.shp | Parcels2017 | 666,211 | Polygon |
| towns_wildlands_poly.shp | towns_wildlands_poly | 10 | Polygon |

**Total Expected**: 25 layers, 715,471 total features

## Performance Benchmarks

When testing on the provided dataset, expect:

- **Processing Time**: 10-60 seconds depending on system performance
- **Memory Usage**: Peak memory usage should remain reasonable (< 1GB)
- **Output File Size**: Approximately 200-500 MB depending on compression

## Troubleshooting Test Issues

### Common Issues

1. **Permission Errors**: Ensure read access to test data directory
2. **Output Path Issues**: Verify write permissions for output location
3. **Memory Issues**: Close other applications when testing large datasets
4. **File Locks**: Ensure test shapefiles aren't open in other applications

### Validation Steps

1. **Verify Input Data**: Check that all expected shapefiles are present
2. **Check File Completeness**: Ensure .shp, .dbf, .shx files exist for each shapefile
3. **Validate Output**: Open resulting GeoPackage in QGIS to verify layers load correctly

This test suite provides comprehensive validation of the shapefiles2gpkg functionality across various real-world scenarios.