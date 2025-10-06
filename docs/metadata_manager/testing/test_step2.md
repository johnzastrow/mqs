# Testing Guide: Step 2 - Common Fields

**Version**: 0.3.0
**Date**: 2025-10-06

## Test Setup

1. Restart QGIS
2. Open Metadata Manager plugin
3. Go to "Metadata Editor" tab
4. Navigate to Step 2 using "Next" button from Step 1

## Test Cases

### TC1: UI Layout
**Expected**: Step 2 displays with:
- Contacts table (Role, Name, Organization columns)
- Add/Edit/Remove contact buttons
- License dropdown with common licenses
- Custom license text field (disabled by default)
- Use constraints multiline text
- Access constraints multiline text
- Language dropdown (default: English)
- Attribution text field

**Status**: [ ]

### TC2: Add Contact
**Steps**:
1. Click "Add Contact" button
2. Dialog opens with fields: Role, Name, Organization, Email, Phone
3. Fill in Name: "John Doe", Role: "Point of Contact"
4. Click OK

**Expected**: Contact appears in table

**Status**: [ ]

### TC3: Edit Contact
**Steps**:
1. Select contact in table
2. Click "Edit" button
3. Modify Organization to "City GIS"
4. Click OK

**Expected**: Contact updated in table

**Status**: [ ]

### TC4: Remove Contact
**Steps**:
1. Select contact in table
2. Click "Remove" button
3. Confirm removal

**Expected**: Contact removed from table

**Status**: [ ]

### TC5: License Selection
**Steps**:
1. Select "CC-BY-4.0 (Attribution)" from dropdown

**Expected**: Custom license field remains disabled

**Status**: [ ]

### TC6: Custom License
**Steps**:
1. Select "Custom (specify below)" from dropdown
2. Enter custom license text

**Expected**: Custom license field enabled and accepts text

**Status**: [ ]

### TC7: Constraints Fields
**Steps**:
1. Enter use constraints: "Attribute City GIS when using this data"
2. Enter access constraints: "Public access"

**Expected**: Both fields accept multiline text

**Status**: [ ]

### TC8: Validation
**Steps**:
1. Leave all fields empty
2. Click "Next" button

**Expected**:
- Navigation succeeds (no required fields in Step 2)
- Shows orange warning about recommended fields

**Status**: [ ]

### TC9: Data Persistence
**Steps**:
1. Fill in all Step 2 fields
2. Go to Step 1 (Previous)
3. Return to Step 2 (Next)

**Expected**: All data retained

**Status**: [ ]

### TC10: Get Data
**Steps**:
1. Add contact: "Jane Smith", "Author", "University"
2. Select license: "Public Domain"
3. Fill constraints and attribution
4. Save metadata

**Expected**: Metadata saved with all Step 2 data

**Status**: [ ]

## Expected Data Structure

```json
{
  "contacts": [
    {
      "role": "Point of Contact",
      "name": "John Doe",
      "organization": "City GIS",
      "email": "john@city.gov",
      "phone": "555-1234"
    }
  ],
  "license": "CC-BY-4.0 (Attribution)",
  "use_constraints": "Attribute City GIS when using this data",
  "access_constraints": "Public access",
  "language": "English",
  "attribution": "City GIS Department, 2025"
}
```

## Notes

- Step 2 has no required fields (all recommended)
- Contact name is required in contact dialog
- Edit/Remove buttons disabled when no contact selected
- Custom license field only enabled when "Custom" selected
- Validation shows orange warnings, not red errors
- All fields should work with copy/paste

## Issues Found

*Document any issues discovered during testing*

---

**Tester**: _______________
**Date**: _______________
**Result**: PASS / FAIL
