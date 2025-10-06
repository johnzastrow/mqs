# Testing Guide: Save & Load Workflow

**Version**: 0.3.0
**Date**: 2025-10-06

## Overview

Test the complete save and load workflow for metadata caching and inventory updates.

## Prerequisites

1. Database created by Inventory Miner (geospatial_catalog.gpkg)
2. Database contains at least one layer in geospatial_inventory
3. Metadata Manager plugin installed and connected to database

## Test Cases

### TC1: Save Complete Metadata
**Steps**:
1. Open Metadata Manager
2. Go to Metadata Editor tab
3. Select a layer (or use test layer path)
4. Fill in all required fields:
   - Step 1: Title, Abstract (10+ chars), Category
   - Step 2: Contact, License
5. Click "Save" button

**Expected**:
- Success message: "Metadata saved to cache (complete): [path]"
- Check metadata_cache table: New entry with layer_path and metadata_json
- Check geospatial_inventory: metadata_status = 'complete', metadata_cached = 1

**SQL to verify**:
```sql
SELECT * FROM metadata_cache WHERE layer_path = '[your_layer_path]';
SELECT metadata_status, metadata_cached, metadata_last_updated
FROM geospatial_inventory WHERE layer_path = '[your_layer_path]';
```

**Status**: [ ]

### TC2: Save Partial Metadata
**Steps**:
1. Start new metadata entry
2. Fill only Step 1 required fields (skip contact and license)
3. Click "Save"

**Expected**:
- Success message: "Metadata saved to cache (partial): [path]"
- metadata_status = 'partial' in inventory

**Status**: [ ]

### TC3: Load Metadata from Cache
**Steps**:
1. After TC1, close and reopen Metadata Manager
2. Select the same layer used in TC1
3. Go to Metadata Editor tab

**Expected**:
- All fields automatically populated with saved data
- Step 1: Title, Abstract, Keywords, Category loaded
- Step 2: Contacts, License, Constraints loaded
- Step 3: Links, Lineage, etc. loaded if filled

**Status**: [ ]

### TC4: Update Existing Metadata
**Steps**:
1. Load metadata (TC3)
2. Modify Abstract text
3. Add another contact
4. Save

**Expected**:
- Success message shown
- metadata_cache updated (modified_datetime changes)
- created_datetime remains the same
- Updated data loads correctly on next open

**SQL to verify**:
```sql
SELECT created_datetime, modified_datetime
FROM metadata_cache WHERE layer_path = '[your_layer_path]';
```

**Status**: [ ]

### TC5: Save from Different Steps
**Steps**:
1. Fill metadata
2. Navigate to Step 2 (not Step 4)
3. Click "Save"

**Expected**: Save works from any step (Save button always visible)

**Status**: [ ]

### TC6: Metadata JSON Structure
**Steps**:
1. Save metadata with all fields filled
2. Query metadata_cache table
3. Examine metadata_json field

**Expected**: JSON contains all fields:
```json
{
  "title": "...",
  "abstract": "...",
  "keywords": [...],
  "category": "...",
  "contacts": [...],
  "license": "...",
  "use_constraints": "...",
  "access_constraints": "...",
  "language": "...",
  "attribution": "...",
  "lineage": "...",
  "purpose": "...",
  "supplemental_info": "...",
  "links": [...],
  "update_frequency": "...",
  "spatial_resolution": "..."
}
```

**Status**: [ ]

### TC7: Multiple Contacts and Links
**Steps**:
1. Add 3 contacts
2. Add 2 links
3. Save and reload

**Expected**: All contacts and links preserved

**Status**: [ ]

### TC8: Empty Optional Fields
**Steps**:
1. Fill required fields only
2. Leave all Step 3 fields empty
3. Save and reload

**Expected**:
- Required fields loaded
- Optional fields remain empty (not "null" or error)

**Status**: [ ]

### TC9: Special Characters in Text
**Steps**:
1. Enter Abstract with special chars: `Data with <tags> & "quotes"`
2. Save and reload

**Expected**: Text preserved exactly (properly escaped in JSON)

**Status**: [ ]

### TC10: Inventory Status Update
**Steps**:
1. Save complete metadata
2. Check Dashboard tab

**Expected**:
- Statistics show 1 more "complete" layer
- Layer no longer in "needs metadata" recommendations

**Status**: [ ]

### TC11: No Layer Selected
**Steps**:
1. Open fresh Metadata Editor (no layer selected)
2. Fill fields
3. Click "Save"

**Expected**: Warning: "Please select a layer first"

**Status**: [ ]

### TC12: Database Connection Required
**Steps**:
1. Disconnect from database
2. Try to save metadata

**Expected**: Save fails gracefully, error logged

**Status**: [ ]

### TC13: Dashboard Refresh After Save
**Steps**:
1. Note current statistics on Dashboard
2. Save complete metadata for a layer
3. Return to Dashboard tab

**Expected**: Statistics update (may need manual refresh)

**Status**: [ ]

## Database Schema Verification

Check these tables exist and have correct structure:

### metadata_cache
- layer_path (TEXT PRIMARY KEY)
- metadata_json (TEXT)
- created_datetime (TEXT)
- modified_datetime (TEXT)
- in_sync (INTEGER)

### geospatial_inventory (updated fields)
- metadata_status (TEXT: 'complete', 'partial', 'none', NULL)
- metadata_last_updated (TEXT)
- metadata_target (TEXT: 'cache', 'file', 'database', 'sidecar')
- metadata_cached (INTEGER: 0 or 1)

## Expected Behavior

### Save Operation:
1. Collect metadata from all steps
2. Determine completeness (required + recommended fields)
3. Save JSON to metadata_cache (INSERT OR REPLACE)
4. Update geospatial_inventory metadata tracking fields
5. Show success/failure message

### Load Operation:
1. Query metadata_cache by layer_path
2. Parse JSON to dictionary
3. Call set_data() on each step widget
4. All fields populated automatically

### Status Logic:
- **Complete**: Title + Abstract (10+) + Category + Contact + License
- **Partial**: Missing any recommended field
- **None**: No metadata cached

## Notes

- Save is non-destructive (INSERT OR REPLACE preserves created_datetime)
- in_sync defaults to 0 (not written to file yet)
- metadata_target = 'cache' until file writing implemented
- QGIS Message Log shows save/load operations (View → Panels → Log Messages)

## Issues Found

*Document any issues discovered during testing*

---

**Tester**: _______________
**Date**: _______________
**Result**: PASS / FAIL
