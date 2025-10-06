# Testing Guide: Step 3 - Optional Fields

**Version**: 0.3.0
**Date**: 2025-10-06

## Test Setup

1. Restart QGIS
2. Open Metadata Manager plugin
3. Go to "Metadata Editor" tab
4. Navigate to Step 3 using "Next" buttons from Steps 1 and 2

## Test Cases

### TC1: UI Layout
**Expected**: Step 3 displays with:
- Lineage multiline text field
- Purpose multiline text field
- Supplemental info multiline text field
- Links table (Name, URL, Type columns)
- Add/Edit/Remove link buttons
- Update frequency dropdown
- Spatial resolution text field
- Blue info message: "All fields in this step are optional"

**Status**: [ ]

### TC2: Text Fields
**Steps**:
1. Enter lineage: "Digitized from 2024 aerial imagery at 1:2400 scale"
2. Enter purpose: "Support emergency services routing"
3. Enter supplemental: "Updated quarterly"

**Expected**: All text fields accept multiline input

**Status**: [ ]

### TC3: Add Link
**Steps**:
1. Click "Add Link" button
2. Dialog opens with: Name, URL, Type, Description
3. Fill in Name: "City GIS Portal", URL: "https://city.gov/gis"
4. Select Type: "Homepage"
5. Click OK

**Expected**: Link appears in table

**Status**: [ ]

### TC4: Edit Link
**Steps**:
1. Select link in table
2. Click "Edit" button
3. Modify Description to "Official city GIS portal"
4. Click OK

**Expected**: Link updated in table

**Status**: [ ]

### TC5: Remove Link
**Steps**:
1. Select link in table
2. Click "Remove" button
3. Confirm removal

**Expected**: Link removed from table

**Status**: [ ]

### TC6: Link Dialog Validation
**Steps**:
1. Click "Add Link"
2. Leave Name empty, click OK

**Expected**: Warning message "Link name is required"

**Steps**:
1. Enter Name but leave URL empty, click OK

**Expected**: Warning message "URL is required"

**Status**: [ ]

### TC7: Update Frequency
**Steps**:
1. Select "Monthly" from dropdown

**Expected**: Value selected successfully

**Status**: [ ]

### TC8: Spatial Resolution
**Steps**:
1. Enter "1:24000"

**Expected**: Text accepted

**Status**: [ ]

### TC9: Validation (All Optional)
**Steps**:
1. Leave all fields empty
2. Click "Next" button

**Expected**: Navigation succeeds (all fields optional)

**Status**: [ ]

### TC10: Data Persistence
**Steps**:
1. Fill in all Step 3 fields
2. Add 2 links
3. Go to Step 2 (Previous)
4. Return to Step 3 (Next)

**Expected**: All data retained including both links

**Status**: [ ]

### TC11: Compact Table Rows
**Expected**: Links table rows are 18px high (same as contacts in Step 2)

**Status**: [ ]

### TC12: Get Data
**Steps**:
1. Fill all fields
2. Add link with type "Download"
3. Click Save

**Expected**: Metadata saved with all Step 3 data

**Status**: [ ]

## Expected Data Structure

```json
{
  "lineage": "Digitized from 2024 aerial imagery at 1:2400 scale",
  "purpose": "Support emergency services routing and planning",
  "supplemental_info": "Updated quarterly with new construction",
  "links": [
    {
      "name": "City GIS Portal",
      "url": "https://city.gov/gis",
      "type": "Homepage",
      "description": "Official city GIS portal"
    },
    {
      "name": "Download Data",
      "url": "https://city.gov/gis/downloads",
      "type": "Download",
      "description": ""
    }
  ],
  "update_frequency": "Monthly",
  "spatial_resolution": "1:24000"
}
```

## Link Type Options

- Homepage
- Download
- Documentation
- Web Service
- REST API
- WMS Service
- WFS Service
- Metadata
- Related
- Other

## Update Frequency Options

- Unknown (default)
- As Needed
- Continually
- Daily
- Weekly
- Fortnightly
- Monthly
- Quarterly
- Biannually
- Annually
- Not Planned

## Notes

- All fields in Step 3 are optional
- Link name and URL are required in link dialog
- Edit/Remove buttons disabled when no link selected
- Links table uses compact 18px rows
- No validation errors - info message shows fields are optional
- All text fields support copy/paste

## Issues Found

*Document any issues discovered during testing*

---

**Tester**: _______________
**Date**: _______________
**Result**: PASS / FAIL
