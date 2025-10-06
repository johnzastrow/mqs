# Phase 3 Wizard - Potential Refinements

## Overview

This document tracks potential improvements to the Metadata Wizard based on testing feedback.

## Step 1 Refinements (Based on Expected Testing)

### High Priority

#### 1. Improve Keyword Input UX
**Current**: Simple text field with Enter to add

**Potential improvements**:
- [ ] Add autocomplete dropdown showing existing keywords from database
- [ ] Show keyword count under field ("3 keywords added")
- [ ] Allow clicking existing tag to edit it
- [ ] Support comma-separated batch input ("roads, streets, transportation")
- [ ] Add "Clear All" button for keywords

**Implementation**:
```python
# Add autocomplete
completer = QtWidgets.QCompleter(existing_keywords, self)
self.keyword_input.setCompleter(completer)
```

#### 2. Better Error Display
**Current**: Red text block with all errors

**Potential improvements**:
- [ ] Highlight invalid fields with red border
- [ ] Show error icon next to field label
- [ ] Inline error message under each field
- [ ] Summary error count at top
- [ ] Green checkmark for valid fields

**Implementation**:
```python
# Add error styling to field
self.title_edit.setStyleSheet("border: 2px solid red;")

# Add error label under field
self.title_error = QtWidgets.QLabel()
self.title_error.setStyleSheet("color: red; font-size: 10px;")
```

#### 3. Field Help Text
**Current**: Just placeholder text

**Potential improvements**:
- [ ] Tooltip on hover explaining field purpose
- [ ] Small "?" icon that shows help dialog
- [ ] Character count for Abstract (e.g., "45/10 characters")
- [ ] Examples of good titles/abstracts

**Implementation**:
```python
self.title_edit.setToolTip(
    "A brief, descriptive name for this dataset. "
    "Example: 'City Road Centerlines 2024'"
)
```

### Medium Priority

#### 4. Data Persistence
**Current**: No auto-save

**Potential improvements**:
- [ ] Auto-save draft every 30 seconds
- [ ] Save on step change
- [ ] Show "Unsaved changes" indicator
- [ ] Prompt before discarding changes
- [ ] Restore last draft when reopening

#### 5. Category Organization
**Current**: Flat alphabetical list

**Potential improvements**:
- [ ] Group related categories
- [ ] Show most-used categories at top
- [ ] Add search/filter for categories
- [ ] Show category descriptions

#### 6. Keyboard Shortcuts
**Current**: Tab/Enter basic navigation

**Potential improvements**:
- [ ] Ctrl+S to save
- [ ] Ctrl+Right/Left for Next/Previous
- [ ] Esc to cancel/close
- [ ] Alt+1,2,3,4 to jump to step

### Low Priority

#### 7. Visual Polish
**Current**: Basic Qt styling

**Potential improvements**:
- [ ] Custom stylesheet for modern look
- [ ] Better color scheme
- [ ] Icons for buttons
- [ ] Animated progress bar
- [ ] Step completion checkmarks

#### 8. Field Templates
**Current**: Empty fields

**Potential improvements**:
- [ ] "Load from similar layer" button
- [ ] Recent values dropdown
- [ ] Copy from clipboard detection
- [ ] Bulk keyword sets (e.g., "Common Transportation Keywords")

## Known Limitations (To Address in Later Steps)

### 1. No Layer Selection
**Current**: Shows "No layer selected"

**Solution**: Phase 5 will add inventory panel for layer selection

**Workaround**: Add temporary "Select Layer" button for testing:
```python
# Quick test: Select layer from inventory
def select_layer_for_testing(self):
    rows = self.db_manager.execute_query(
        "SELECT layer_path, layer_name FROM geospatial_inventory LIMIT 10"
    )
    # Show simple list dialog...
```

### 2. No Database Save
**Current**: Save button shows message but doesn't persist

**Solution**: Need to implement save_metadata_to_cache() in DatabaseManager

**Implementation needed**:
```python
def save_metadata_to_cache(self, layer_path: str, metadata: dict) -> bool:
    """Save metadata JSON to cache table."""
    try:
        metadata_json = json.dumps(metadata)
        self.execute_update(
            """
            INSERT OR REPLACE INTO metadata_cache
            (layer_path, layer_name, metadata_json, last_edited_date)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (layer_path, metadata.get('title', ''), metadata_json)
        )
        return True
    except Exception as e:
        return False
```

### 3. No Load from Cache
**Current**: Always starts with empty fields

**Solution**: Implement load_metadata_from_cache()

### 4. Steps 2-4 Not Implemented
**Current**: Placeholder text

**Solution**: Continue Phase 3 implementation

## Bug Fixes Needed (Based on Expected Issues)

### Potential Bug 1: Keyword Tags Layout
**Symptom**: Tags might overlap or not wrap properly

**Fix**:
```python
# In QFlowLayout.doLayout()
# Ensure proper spacing and wrapping
```

### Potential Bug 2: Long Text in Fields
**Symptom**: Very long titles or abstracts might overflow

**Fix**:
```python
# Add max length validation
if len(title) > 255:
    errors.append("Title must be less than 255 characters")
```

### Potential Bug 3: Special Characters
**Symptom**: Unicode or special chars might cause issues

**Fix**:
```python
# Ensure proper encoding in get_data()
return {
    'title': self.title_edit.text().strip(),  # Already handles Unicode
    ...
}
```

### Potential Bug 4: Tab Order
**Symptom**: Tab key might not move through fields logically

**Fix**:
```python
# Set explicit tab order
self.setTabOrder(self.title_edit, self.abstract_edit)
self.setTabOrder(self.abstract_edit, self.keyword_input)
self.setTabOrder(self.keyword_input, self.category_combo)
```

## Testing Feedback Template

```markdown
### Issue: [Brief description]

**Steps to reproduce:**
1.
2.
3.

**Expected behavior:**


**Actual behavior:**


**Priority:** High / Medium / Low

**Proposed solution:**

```

## Refinement Priorities After Testing

### If testing goes well:
1. Continue to Steps 2-4
2. Implement database save/load
3. Add basic refinements (autocomplete, better errors)

### If issues found:
1. Fix critical bugs first
2. Improve UX based on feedback
3. Refine Step 1 before continuing

### If UX is confusing:
1. Simplify interface
2. Add more help text
3. Consider redesign of flow

## Quick Wins (Can implement immediately if needed)

### 1. Add Character Counter
```python
def update_abstract_counter(self):
    count = len(self.abstract_edit.toPlainText())
    self.abstract_counter.setText(f"{count} characters")

self.abstract_edit.textChanged.connect(self.update_abstract_counter)
```

### 2. Add "Clear Form" Button
```python
def clear_form(self):
    if QtWidgets.QMessageBox.question(...) == Yes:
        self.title_edit.clear()
        self.abstract_edit.clear()
        # ... clear other fields
```

### 3. Add Field Tooltips
```python
HELP_TEXT = {
    'title': "Concise name for the dataset",
    'abstract': "Detailed description (minimum 10 characters)",
    'keywords': "Searchable terms that describe the data",
    'category': "ISO 19115 topic category"
}

for field, help_text in HELP_TEXT.items():
    widget = getattr(self, f"{field}_edit")
    widget.setToolTip(help_text)
```

---

**Status**: Awaiting testing feedback
**Date**: 2025-10-05
**Version**: 0.3.0 (Phase 3 in progress)
