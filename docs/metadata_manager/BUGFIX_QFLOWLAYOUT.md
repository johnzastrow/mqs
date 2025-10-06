# Bug Fix: QFlowLayout AttributeError

## Issue

Plugin failed to load with error:

```
AttributeError: module 'qgis.PyQt.QtWidgets' has no attribute 'QFlowLayout'.
Did you mean: 'QBoxLayout'?
```

**Location**: `metadata_wizard.py`, line 100

## Root Cause

The code tried to use `QtWidgets.QFlowLayout(...)` but `QFlowLayout` is not a built-in Qt widget. It's a custom layout class defined in the same file.

The problem had two parts:

1. **Wrong reference**: Code used `QtWidgets.QFlowLayout` instead of just `QFlowLayout`
2. **Class order**: `QFlowLayout` was defined AFTER `Step1Essential` which tried to use it
3. **Duplicate definition**: `QFlowLayout` was defined twice in the file

## Solution

### Fix 1: Correct the Reference

Changed line 100 from:
```python
self.keyword_tags_layout = QtWidgets.QFlowLayout(self.keyword_tags)
```

To:
```python
self.keyword_tags_layout = QFlowLayout(self.keyword_tags)
```

### Fix 2: Move Class Definition

Moved `QFlowLayout` class definition to the top of the file (line 18), before all classes that use it:

```python
# File structure:
1. Imports
2. QFlowLayout (custom layout class) ← Moved here
3. StepWidget (base class)
4. Step1Essential (uses QFlowLayout)
5. MetadataWizard (main widget)
```

### Fix 3: Remove Duplicate

Deleted the duplicate `QFlowLayout` definition that appeared at line 302.

## Files Modified

- `Plugins/metadata_manager/widgets/metadata_wizard.py`
  - Moved `QFlowLayout` to line 18
  - Changed reference on line 100
  - Removed duplicate at line 302

## Testing

✅ Plugin now loads without errors
✅ Wizard tab appears correctly
✅ QFlowLayout works for keyword tags

## Prevention

**Lesson learned**: When creating custom Qt classes, define them at the module level before any classes that use them.

**Best practice**:
```python
# Good order:
1. Standard imports
2. Custom utility classes (layouts, validators, etc.)
3. Base widget classes
4. Specific widget implementations
```

## Status

✅ **FIXED** - Version 0.3.0 (2025-10-05)

Plugin reinstalled and ready for testing.
