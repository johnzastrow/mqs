# Testing Guide: Flexible Database Selection (v0.3.1)

This guide tests the new flexible database selection feature that allows the plugin to load without a database and switch databases during runtime.

## Prerequisites
- QGIS 3.40+ installed
- Metadata Manager plugin installed (v0.3.1)
- At least one inventory database created by Inventory Miner
- Optionally, a second database for testing switching

---

## Test 1: Plugin Loads Without Database

**Objective**: Verify plugin can start without requiring database selection

### Steps:
1. In QGIS, go to Settings → Options → Advanced → find `MetadataManager/last_database`
2. Clear this setting (delete the value)
3. Open Metadata Manager plugin (Plugins → Metadata Manager)

### Expected Result:
✅ Plugin opens successfully
✅ Shows Dashboard tab with "No database selected" message in red background
✅ No error dialogs or forced database selection

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 2: Dashboard Shows Connection Status

**Objective**: Verify dashboard displays database connection status clearly

### Steps:
1. With plugin open (no database connected), go to Dashboard tab
2. Look at "Inventory Database" section

### Expected Result:
✅ Shows "Current Database: No database selected"
✅ Background is red (#ffcccc)
✅ "Select Database..." button is visible
✅ "Refresh Statistics" button is visible
✅ Statistics show "-" or empty

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 3: Select Database from Dashboard

**Objective**: Test selecting a database using the dashboard controls

### Steps:
1. Click "Select Database..." button
2. Navigate to your inventory database (.gpkg file)
3. Select the database and click Open

### Expected Result:
✅ File dialog opens filtered to .gpkg files
✅ After selection, validation checks run
✅ If database is valid, shows "Successfully connected" message
✅ Dashboard background changes to green (#ccffcc)
✅ Database path is displayed
✅ Statistics populate automatically

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 4: Auto-Connect to Last Database

**Objective**: Verify plugin remembers and auto-connects to last database

### Steps:
1. With a database connected, close the plugin
2. Reopen Metadata Manager plugin

### Expected Result:
✅ Plugin opens and automatically connects to last used database
✅ Dashboard shows green background with database path
✅ Statistics are populated
✅ No manual selection required

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 5: Wizard Blocked Without Database

**Objective**: Verify wizard prevents layer selection when not connected

### Steps:
1. Clear last_database setting (see Test 1)
2. Open plugin (no database connected)
3. Go to "Metadata Editor" tab
4. Click "Select Layer from Inventory" button

### Expected Result:
✅ Warning dialog appears:
   - Title: "No Database Connected"
   - Message: "Please select an inventory database from the Dashboard tab first."
   - Mentions "Go to Dashboard → Select Database..."
✅ Layer selector dialog does NOT open

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 6: Switch Databases During Session

**Objective**: Verify can change databases without restarting plugin

### Steps:
1. Connect to first database using dashboard
2. Select a layer and start editing metadata (fill in some fields)
3. Go back to Dashboard tab
4. Click "Select Database..." and choose a DIFFERENT database
5. Go back to Metadata Editor tab

### Expected Result:
✅ Database switch succeeds
✅ Dashboard updates to show new database path
✅ Statistics refresh for new database
✅ Wizard clears previous layer selection
✅ Shows "No layer selected" message
✅ All wizard fields are cleared

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 7: Validate Database on Selection

**Objective**: Verify only valid inventory databases can be selected

### Steps:
1. Click "Select Database..."
2. Navigate to any random .gpkg file that's NOT an inventory database
3. Select it

### Expected Result:
✅ Error dialog appears:
   - Title: "Invalid Database"
   - Message mentions it's not a valid Inventory Miner database
   - Suggests running Inventory Miner first
✅ Database connection fails
✅ Dashboard remains in "No database selected" state

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 8: Initialize Metadata Manager Tables

**Objective**: Verify can initialize tables on first use of inventory database

### Steps:
1. Use an inventory database that has never been used with Metadata Manager
2. Click "Select Database..." and choose it

### Expected Result:
✅ Dialog appears:
   - Title: "Initialize Database"
   - Asks if you want to initialize Metadata Manager tables
   - Has Yes/No buttons
✅ Clicking Yes initializes tables successfully
✅ Shows success message
✅ Database connects normally
✅ Clicking No cancels and returns to "No database selected"

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 9: Wizard Works After Database Selected

**Objective**: Verify complete workflow from no-database to editing

### Steps:
1. Start plugin with no database
2. Go to Dashboard → Select Database... → choose database
3. Go to Metadata Editor tab
4. Click "Select Layer from Inventory"
5. Choose a layer
6. Fill metadata and save

### Expected Result:
✅ Each step works smoothly
✅ Layer selector shows inventory layers
✅ Selected layer appears in wizard
✅ Can edit metadata normally
✅ Save succeeds
✅ Dashboard statistics update

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Test 10: Refresh Statistics Button

**Objective**: Verify manual refresh works

### Steps:
1. Connect to database with some metadata
2. Note current statistics
3. Click "Refresh Statistics" button

### Expected Result:
✅ Statistics update (even if same values)
✅ All drill-down tables refresh
✅ No errors

### Actual Result:
- [ ] Pass
- [ ] Fail - Describe: ___________

---

## Summary

**Tests Passed**: ___/10

**Overall Status**:
- [ ] All tests pass - Feature ready ✅
- [ ] Some tests fail - Issues need fixing ⚠️
- [ ] Many tests fail - Major problems ❌

**Notes**:

---

## Known Limitations

1. Plugin can only connect to one database at a time
2. Switching databases clears wizard state (by design - prevents data corruption)
3. Last database setting is stored in QGIS user settings

---

## Developer Notes

**Files Modified**:
- `MetadataManager.py` - Made database selection optional on startup
- `MetadataManager_dockwidget.py` - Only refresh if connected
- `dashboard_widget.py` - Added database selection UI and logic
- `metadata_wizard.py` - Added clear_layer() and clear_data() methods
- `metadata_wizard.py` - Added database connection check before layer selection

**Key Methods**:
- `dashboard_widget.select_database()` - Database selection with validation
- `dashboard_widget.update_database_display()` - Visual status update
- `metadata_wizard.clear_layer()` - Reset wizard state
- Step classes `.clear_data()` - Clear form fields
