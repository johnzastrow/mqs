# Testing Guide: Step 4 - Review & Save

**Version**: 0.3.0
**Date**: 2025-10-06

## Test Setup

1. Restart QGIS
2. Open Metadata Manager plugin
3. Go to "Metadata Editor" tab
4. Fill in metadata in Steps 1-3
5. Navigate to Step 4 using "Next" button

## Test Cases

### TC1: UI Layout
**Expected**: Step 4 displays with:
- Title: "Step 4: Review & Save"
- Status indicator (green for complete, yellow for partial)
- Read-only summary text area with formatted metadata
- Instructions at bottom
- "Previous" and "Save" buttons enabled
- "Next" and "Skip" buttons disabled (last step)

**Status**: [ ]

### TC2: Complete Metadata Status
**Steps**:
1. Go back to Steps 1-2
2. Fill in all required fields:
   - Step 1: Title, Abstract (10+ chars), Category
   - Step 2: At least one contact, License
3. Navigate to Step 4

**Expected**:
- Green status banner: "✓ Metadata Complete"
- All filled fields displayed in summary

**Status**: [ ]

### TC3: Partial Metadata Status
**Steps**:
1. Go back to Steps 1-2
2. Fill only Step 1 required fields
3. Skip Step 2 (no contacts, no license)
4. Navigate to Step 4

**Expected**:
- Yellow status banner: "⚠ Metadata Partial"
- Step 1 fields shown
- Step 2 fields shown as "None" or "Not specified"

**Status**: [ ]

### TC4: Summary Display - Essential Fields
**Steps**:
1. Fill Step 1:
   - Title: "Road Centerlines"
   - Abstract: "Street centerlines for emergency services"
   - Keywords: "roads", "transportation"
   - Category: "Transportation"
2. Navigate to Step 4

**Expected**: Summary shows section "Essential Fields" with:
- Title: Road Centerlines
- Abstract: Street centerlines for emergency services
- Keywords: roads, transportation
- Category: Transportation

**Status**: [ ]

### TC5: Summary Display - Common Fields
**Steps**:
1. Fill Step 2:
   - Contact: "John Doe", "Point of Contact", "City GIS"
   - License: "CC-BY-4.0 (Attribution)"
   - Use Constraints: "Attribute City GIS"
   - Language: "English"
   - Attribution: "City GIS, 2025"
2. Navigate to Step 4

**Expected**: Summary shows section "Common Fields" with:
- Contacts listed with role, name, org
- License shown
- Constraints shown
- Language shown
- Attribution shown

**Status**: [ ]

### TC6: Summary Display - Optional Fields
**Steps**:
1. Fill Step 3:
   - Lineage: "Digitized from aerial imagery"
   - Purpose: "Emergency services routing"
   - Link: "City Portal", "https://city.gov/gis", "Homepage"
   - Update Frequency: "Monthly"
   - Spatial Resolution: "1:24000"
2. Navigate to Step 4

**Expected**: Summary shows section "Optional Fields" with all data

**Status**: [ ]

### TC7: No Optional Fields
**Steps**:
1. Skip Step 3 (leave all fields empty)
2. Navigate to Step 4

**Expected**: No "Optional Fields" section displayed

**Status**: [ ]

### TC8: HTML Special Characters
**Steps**:
1. In Step 1, enter Abstract: "Data with <tags> & special chars"
2. Navigate to Step 4

**Expected**: Text displayed safely (< > & properly escaped)

**Status**: [ ]

### TC9: Navigation from Step 4
**Steps**:
1. On Step 4, click "Previous"

**Expected**: Returns to Step 3, all data retained

**Status**: [ ]

### TC10: Save Functionality
**Steps**:
1. Fill metadata in all steps
2. Navigate to Step 4
3. Click "Save" button

**Expected**:
- Message box: "Metadata saved for [layer_path]"
- metadata_saved signal emitted

**Status**: [ ]

### TC11: Refresh on Navigation
**Steps**:
1. Fill Step 1 completely
2. Navigate to Step 4 (shows partial)
3. Go back to Step 2
4. Add contact and license
5. Navigate to Step 4 again

**Expected**: Status changes from "Partial" to "Complete", summary updates

**Status**: [ ]

### TC12: Multiple Contacts Display
**Steps**:
1. Add 3 contacts in Step 2
2. Navigate to Step 4

**Expected**: All contacts listed with bullet points

**Status**: [ ]

### TC13: Multiple Links Display
**Steps**:
1. Add 3 links in Step 3
2. Navigate to Step 4

**Expected**: All links listed with names, types, and URLs

**Status**: [ ]

## Completeness Requirements

**Complete Status** requires:
- Title (not empty)
- Abstract (10+ characters)
- Category (selected)
- At least one contact
- License specified

**Partial Status**: Missing any of the above

## Expected Summary Format

```
Essential Fields
────────────────
Title: Road Centerlines
Abstract: Street centerlines for emergency services
Keywords: roads, transportation
Category: Transportation

Common Fields
────────────
Contacts:
  • Point of Contact: John Doe (City GIS)
License: CC-BY-4.0 (Attribution)
Use Constraints: Attribute City GIS
Language: English
Attribution: City GIS, 2025

Optional Fields
──────────────
Lineage: Digitized from aerial imagery
Links:
  • City Portal (Homepage)
    https://city.gov/gis
Update Frequency: Monthly
Spatial Resolution: 1:24000
```

## Notes

- Summary is read-only (QTextEdit with readonly=True)
- Summary uses HTML formatting with sections
- Status indicator has colored background
- No validation errors on Step 4 (always valid)
- Summary refreshes automatically when navigating to Step 4
- Can navigate back to any previous step
- Save button works from any step (not just Step 4)

## Issues Found

*Document any issues discovered during testing*

---

**Tester**: _______________
**Date**: _______________
**Result**: PASS / FAIL
