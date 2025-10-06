# Testing Guide for Metadata Manager

## Overview

This directory contains test scripts for the Metadata Manager plugin.

## Prerequisites

1. **QGIS Installation**: QGIS 3.40+ must be installed
2. **Test Database**: A valid inventory database created by Inventory Miner v0.2.0+
3. **Python Environment**: Access to QGIS Python environment

## Test Files

### `test_dashboard.py`

Tests the dashboard widget statistics methods.

**What it tests:**
- Overall inventory statistics
- Statistics by directory
- Statistics by data type
- Statistics by file format
- Statistics by CRS
- Priority recommendations

**How to run:**

```bash
# Set environment variable to your test database
export TEST_INVENTORY_DB=/path/to/geospatial_catalog.gpkg

# Run from QGIS Python Console or terminal with QGIS Python
python3 test_dashboard.py
```

**Expected output:**
- Test results showing pass/fail for each test
- Sample statistics printed to console
- Verification that statistics calculations are correct

## Creating a Test Database

To create a test database for testing:

1. **Run Inventory Miner** on a directory with some geospatial files:
   ```python
   # In QGIS Python Console
   import sys
   sys.path.append('/path/to/mqs/Scripts')
   from inventory_miner import InventoryMiner

   miner = InventoryMiner()
   miner.scan_directory('/path/to/test/data', '/path/to/test_catalog.gpkg')
   ```

2. **Verify the database** has the geospatial_inventory table with metadata fields

3. **Set the environment variable**:
   ```bash
   export TEST_INVENTORY_DB=/path/to/test_catalog.gpkg
   ```

## Manual Testing in QGIS

### Test Dashboard Display

1. **Install Plugin**:
   - Copy `Plugins/metadata_manager` to your QGIS plugins directory
   - Enable "Metadata Manager" in Plugin Manager

2. **Open Plugin**:
   - Click the Metadata Manager toolbar button
   - Select your test inventory database

3. **Verify Dashboard**:
   - Overall statistics should display correctly
   - Progress bar should show completion percentage
   - All tabs should populate with data
   - Recommendations should appear

4. **Test Refresh**:
   - Click "Refresh Statistics" button
   - Verify data updates

5. **Test Drill-Down**:
   - Click each tab (Directory, Data Type, File Format, CRS)
   - Verify tables populate with correct data
   - Check that percentages calculate correctly

## Common Issues

### "Test database not available"
- Ensure TEST_INVENTORY_DB environment variable is set
- Verify the path is correct and database exists

### "Invalid test database"
- Database must be created by Inventory Miner v0.2.0+
- Verify geospatial_inventory table exists
- Check that metadata tracking fields are present

### Import errors
- Ensure QGIS Python environment is active
- Check that plugin directory is in Python path
- Verify all dependencies are available

## Test Coverage

Current test coverage:

- ✅ Database connection and validation
- ✅ Overall statistics calculation
- ✅ Directory-based drill-down
- ✅ Data type drill-down
- ✅ File format drill-down
- ✅ CRS drill-down
- ✅ Priority recommendations
- ⏳ Dashboard widget UI (manual testing)
- ⏳ Refresh functionality (manual testing)
- ⏳ Integration with main plugin (manual testing)

## Future Test Additions

Tests to be added in future versions:

- Widget interaction tests
- Performance tests with large databases
- Edge case handling (empty database, missing fields)
- Export functionality tests
- User interaction simulations
