# Phase 3: Progressive Disclosure Wizard - Design Document

## Overview

Create a step-by-step wizard interface that guides users through metadata creation without overwhelming them with all fields at once.

## Wizard Steps

### Step 1: Essential Fields (Required)
**Purpose**: Get the minimum viable metadata quickly

Fields:
- **Title** (text, required) - Layer name
- **Abstract** (multiline text, required) - Brief description of the layer
- **Keywords** (tag selector) - Searchable terms
  - Autocomplete from keywords table
  - Add new keywords on-the-fly
  - Support for themed keywords (place, theme, temporal)
- **Category** (dropdown) - ISO 19115 topic category
  - Options: Boundaries, Elevation, Environment, Imagery, etc.

**Validation**: Title and Abstract must be filled

### Step 2: Common Fields (Recommended)
**Purpose**: Add provenance and legal info

Fields:
- **Contacts** (table with add/edit/delete)
  - Point of Contact
  - Author
  - Custodian
  - Select from contacts table or create new
- **License** (dropdown + text)
  - Common licenses: Public Domain, CC-BY, CC-BY-SA, Proprietary
  - Custom license text
- **Constraints** (multiline text)
  - Use constraints
  - Access constraints
- **Language** (dropdown) - Default: English
- **Attribution** (text) - How to cite this data

**Validation**: At least one contact recommended

### Step 3: Optional Fields (Advanced)
**Purpose**: Complete metadata for data professionals

Fields:
- **Lineage** (multiline text) - Data processing history
- **Purpose** (multiline text) - Why this data was created
- **Supplemental Information** (multiline text)
- **Links** (table with add/edit/delete)
  - URL
  - Name
  - Description
  - Type (Homepage, Download, Service, etc.)
- **Update Frequency** (dropdown)
  - As needed, Daily, Weekly, Monthly, Annually, etc.
- **Spatial Resolution** (text) - e.g., "1:24000" or "10 meters"

**Validation**: All optional

### Step 4: Review & Save
**Purpose**: Confirm and save metadata

Display:
- Summary of all entered fields
- Validation status (✓ Complete / ⚠ Partial)
- Preview of where metadata will be written

Actions:
- **Save**: Write to metadata_cache and target location
- **Save & Next**: Save and load next layer from inventory
- **Cancel**: Discard changes

## UI Layout

```
┌────────────────────────────────────────────────┐
│  Metadata Editor                          [X]  │
├────────────────────────────────────────────────┤
│  Layer: roads.shp                              │
│  [●━━━━━○━━━━━○━━━━━○] Step 1 of 4           │
├────────────────────────────────────────────────┤
│                                                │
│  Step 1: Essential Fields                     │
│                                                │
│  Title *                                       │
│  [_____________________________________]       │
│                                                │
│  Abstract *                                    │
│  [_____________________________________]       │
│  [                                     ]       │
│  [                                     ]       │
│                                                │
│  Keywords                                      │
│  [tag1] [tag2] [+ Add]                        │
│                                                │
│  Category *                                    │
│  [Transportation ▼]                            │
│                                                │
├────────────────────────────────────────────────┤
│  [Skip →] [← Previous]  [Next →] [Expert Mode]│
└────────────────────────────────────────────────┘
```

## Expert Mode

Toggle to show all fields on one page:
- Collapsible sections for each step
- All fields visible at once
- Same validation rules apply
- For experienced users who know what they need

## Navigation Rules

1. **Next**:
   - Validate current step
   - If valid, move to next step
   - If invalid, show errors and stay

2. **Previous**:
   - Always allowed
   - No validation
   - Preserves entered data

3. **Skip**:
   - Jump to next step without validation
   - Mark step as "skipped" (can return later)

4. **Save** (available on all steps):
   - Validate all required fields
   - Save to metadata_cache
   - Update inventory.metadata_status
   - Show success message

## Data Storage

### metadata_cache Table
Stores complete metadata as JSON:

```json
{
  "title": "Road Centerlines",
  "abstract": "Street centerlines for City of...",
  "keywords": ["transportation", "roads", "streets"],
  "category": "transportation",
  "contacts": [
    {
      "role": "pointOfContact",
      "name": "John Doe",
      "organization": "City GIS"
    }
  ],
  "license": "CC-BY-4.0",
  "constraints": {
    "use": "Attribute City GIS",
    "access": "Public"
  },
  "language": "eng",
  "lineage": "Digitized from aerial imagery...",
  "links": [
    {
      "url": "https://city.gov/gis",
      "name": "City GIS Portal",
      "type": "homepage"
    }
  ]
}
```

### Update inventory Table
When saving:
```sql
UPDATE geospatial_inventory
SET
  metadata_status = 'complete', -- or 'partial'
  metadata_last_updated = datetime('now'),
  metadata_cached = 1
WHERE layer_path = ?
```

## Widget Architecture

```
wizard_widget.py
├── MetadataWizard (main widget)
│   ├── progress_indicator (custom widget)
│   ├── layer_info_label
│   ├── step_container (QStackedWidget)
│   │   ├── Step1Widget (essential fields)
│   │   ├── Step2Widget (common fields)
│   │   ├── Step3Widget (optional fields)
│   │   └── Step4Widget (review & save)
│   └── navigation_buttons
│
├── StepWidget (base class)
│   ├── validate() -> bool
│   ├── get_data() -> dict
│   ├── set_data(dict)
│   └── is_complete() -> bool
│
├── KeywordSelector (reusable widget)
│   ├── tag display
│   ├── autocomplete
│   └── add/remove functionality
│
└── ContactSelector (reusable widget)
    ├── contact table
    ├── add/edit/delete buttons
    └── dialog for contact details
```

## Integration with Dockwidget

Add tab to main dockwidget:

```python
# In MetadataManager_dockwidget.py
self.tab_widget = QTabWidget()
self.tab_widget.addTab(self.dashboard_widget, "Dashboard")
self.tab_widget.addTab(self.wizard_widget, "Metadata Editor")
```

## Validation Rules

### Required Fields (Step 1)
- Title: Must not be empty
- Abstract: Must be at least 10 characters
- Category: Must be selected

### Recommended Fields (Step 2)
- At least 1 contact: Warning if missing
- License: Warning if missing

### Completeness Status
- **Complete**: All required + all recommended fields filled
- **Partial**: Only required fields filled
- **None**: No metadata or missing required fields

## Keyboard Shortcuts

- `Tab` / `Shift+Tab`: Navigate between fields
- `Ctrl+Enter`: Save and continue
- `Ctrl+Right`: Next step
- `Ctrl+Left`: Previous step
- `Escape`: Cancel/close

## Error Handling

- Red border around invalid fields
- Error message below field
- Summary of errors at top of step
- Prevent navigation to next step if invalid

## Auto-save

- Save draft to metadata_cache every 30 seconds
- Mark as `in_sync = 0` (not written to file yet)
- Restore draft if user returns to same layer

## Next Phase Integration Points

**Phase 4 (Smart Defaults)** will:
- Pre-populate title from layer_name
- Load CRS, extent, geometry type from inventory
- Import existing metadata if present

**Phase 5 (Layer List)** will:
- Provide layer selection for wizard
- Show "Edit" button that opens wizard
- Update list when metadata saved

## Implementation Order

1. ✅ Create base wizard widget with navigation
2. ✅ Implement Step 1 (essential fields)
3. ✅ Implement Step 2 (common fields)
4. ✅ Implement Step 3 (optional fields)
5. ✅ Implement Step 4 (review & save)
6. ✅ Add validation logic
7. ✅ Add save/load from metadata_cache
8. ✅ Integrate with dockwidget
9. ✅ Testing

---

**Status**: Design complete, ready for implementation
**Target**: Phase 3 complete
