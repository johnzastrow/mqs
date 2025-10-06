# Metadata Wizard Testing Guide - Step 1

## Overview

This guide helps you test the Metadata Wizard (Phase 3, Step 1) functionality.

## Prerequisites

1. ✅ QGIS is running
2. ✅ Metadata Manager plugin installed (v0.2.0+)
3. ✅ Inventory database selected and initialized
4. ✅ Plugin enabled in Plugin Manager

## Testing Step 1: Essential Fields

### Test 1: Access the Wizard

**Steps:**
1. Open Metadata Manager plugin (toolbar button or menu)
2. Plugin should show two tabs: "Dashboard" and "Metadata Editor"
3. Click the "Metadata Editor" tab

**Expected Results:**
- ✅ Wizard interface appears
- ✅ Shows "Step 1 of 4"
- ✅ Progress bar shows 25% filled
- ✅ Layer label shows "No layer selected"
- ✅ Four fields visible: Title, Abstract, Keywords, Category

**Issues to Note:**
- [ ] Tabs don't appear
- [ ] Wizard tab is blank
- [ ] Error messages in QGIS message log

---

### Test 2: Required Field Validation

**Steps:**
1. Leave all fields empty
2. Click "Next →" button

**Expected Results:**
- ✅ Stays on Step 1 (doesn't advance)
- ✅ Red error message appears showing:
  - "Title is required"
  - "Abstract is required"
  - "Please select a category"
- ✅ Error text is readable and red

**Issues to Note:**
- [ ] Advances to Step 2 despite empty fields
- [ ] No error messages shown
- [ ] Error messages unclear or truncated

---

### Test 3: Title Field

**Steps:**
1. Enter a title: "Test Roads Layer"
2. Click "Next →"

**Expected Results:**
- ✅ Title error disappears
- ✅ Still shows Abstract and Category errors
- ✅ Stays on Step 1

**Issues to Note:**
- [ ] Title not accepted
- [ ] Error doesn't clear
- [ ] Field doesn't accept input

---

### Test 4: Abstract Field Validation

**Steps:**
1. Enter short text in Abstract: "Test"
2. Click "Next →"

**Expected Results:**
- ✅ Error changes to "Abstract must be at least 10 characters"
- ✅ Still stays on Step 1

**Steps (continued):**
3. Add more text: "Test road centerlines for the city"
4. Click "Next →"

**Expected Results:**
- ✅ Abstract error disappears
- ✅ Only Category error remains

**Issues to Note:**
- [ ] Minimum length not enforced
- [ ] Can't enter multiline text
- [ ] Field too small to read content

---

### Test 5: Keyword Functionality

**Steps:**
1. Type "transportation" in keyword field
2. Press Enter

**Expected Results:**
- ✅ Tag appears with "transportation" label
- ✅ Tag has blue background
- ✅ Tag has × remove button
- ✅ Input field clears

**Steps (continued):**
3. Add more keywords: "roads", "streets", "gis"
4. All should appear as tags

**Expected Results:**
- ✅ Multiple tags displayed
- ✅ Tags wrap to new line if needed
- ✅ Each tag removable independently

**Steps (continued):**
5. Click × on "roads" tag

**Expected Results:**
- ✅ "roads" tag disappears
- ✅ Other tags remain

**Issues to Note:**
- [ ] Tags don't appear when Enter pressed
- [ ] Can add duplicate keywords
- [ ] Remove button doesn't work
- [ ] Tags overlap or look broken

---

### Test 6: Category Selection

**Steps:**
1. Click Category dropdown
2. Select "Transportation"

**Expected Results:**
- ✅ "Transportation" shows in dropdown
- ✅ All errors should now be cleared

**Steps (continued):**
3. Click "Next →"

**Expected Results:**
- ✅ Advances to Step 2
- ✅ Shows "Step 2 of 4"
- ✅ Progress bar shows 50%
- ✅ Placeholder text: "Step 2: Common Fields (Coming next)"

**Issues to Note:**
- [ ] Dropdown doesn't open
- [ ] Selection doesn't stick
- [ ] Still shows errors after valid selection

---

### Test 7: Navigation Buttons

**Steps:**
1. Fill in valid data for all Step 1 fields
2. Click "Next →" to go to Step 2
3. Click "← Previous" button

**Expected Results:**
- ✅ Returns to Step 1
- ✅ All entered data still present (Title, Abstract, Keywords, Category)
- ✅ Progress bar back to 25%

**Issues to Note:**
- [ ] Data lost when returning to Step 1
- [ ] Previous button disabled or missing
- [ ] Can't navigate back

---

### Test 8: Skip Button

**Steps:**
1. Clear all Step 1 fields
2. Click "Skip →" button

**Expected Results:**
- ✅ Advances to Step 2 without validation
- ✅ No error messages

**Steps (continued):**
3. Click "← Previous"
4. Click "Next →" (with empty fields)

**Expected Results:**
- ✅ Shows validation errors
- ✅ Stays on Step 1

**Issues to Note:**
- [ ] Skip button doesn't work
- [ ] Skip still validates fields

---

### Test 9: Save Button (Basic)

**Steps:**
1. Fill in all required Step 1 fields
2. Click "Save" button

**Expected Results:**
- ✅ Message box appears: "Saved" or "No layer selected"
- ✅ No errors in QGIS message log

**Current Limitation:**
- Save doesn't persist to database yet (expected)
- Shows "No layer selected" message (expected - Phase 5 will add layer selection)

**Issues to Note:**
- [ ] Button does nothing
- [ ] Crashes plugin
- [ ] Error messages

---

### Test 10: Window Resize

**Steps:**
1. Resize QGIS window smaller
2. Make dockwidget narrower

**Expected Results:**
- ✅ Wizard interface adapts to size
- ✅ Keyword tags wrap properly
- ✅ Text fields remain usable
- ✅ Buttons stay visible

**Issues to Note:**
- [ ] Content gets cut off
- [ ] Fields overlap
- [ ] Can't access buttons

---

## Common Issues and Solutions

### Issue: Wizard Tab is Blank

**Cause**: Widget didn't initialize properly

**Solution:**
1. Check QGIS message log (View → Panels → Log Messages)
2. Look for Python errors
3. Try restarting QGIS
4. Verify plugin installation includes `widgets/metadata_wizard.py`

### Issue: Keywords Don't Appear

**Cause**: Flow layout not working

**Solution:**
- This is a known Qt layout issue
- May need to adjust QFlowLayout implementation
- Report as bug with screenshot

### Issue: Validation Doesn't Work

**Cause**: validate() method not being called

**Solution:**
1. Check that Next button is connected to next_step()
2. Verify Step1Essential has validate() method
3. Check for Python errors in log

### Issue: Can't Navigate Between Steps

**Cause**: Navigation buttons disabled

**Solution:**
- Previous button should be disabled on Step 1 (expected)
- Next/Skip should always be enabled
- Check button enable/disable logic in update_navigation()

---

## Testing Checklist

### Functional Tests
- [ ] Wizard tab appears and loads
- [ ] All Step 1 fields are visible
- [ ] Title field accepts input
- [ ] Abstract field accepts multiline input
- [ ] Keywords can be added
- [ ] Keywords can be removed
- [ ] Category dropdown works
- [ ] Validation prevents invalid Next
- [ ] Valid data allows Next
- [ ] Previous button returns to Step 1
- [ ] Skip bypasses validation
- [ ] Save button shows message
- [ ] Progress indicator updates

### UI/UX Tests
- [ ] Layout looks clean and organized
- [ ] Labels are clear and readable
- [ ] Required fields marked with *
- [ ] Error messages are helpful
- [ ] Fields are appropriate sizes
- [ ] Buttons are logically placed
- [ ] Color coding makes sense
- [ ] Keyword tags look good
- [ ] Resizing works properly

### Edge Cases
- [ ] Very long titles (100+ chars)
- [ ] Very long abstracts (1000+ chars)
- [ ] Many keywords (20+)
- [ ] Special characters in fields
- [ ] Unicode characters
- [ ] Copy/paste into fields
- [ ] Rapid clicking of buttons
- [ ] Switching tabs while editing

---

## Feedback Form

**Date Tested:** _______________
**QGIS Version:** _______________
**Plugin Version:** 0.2.0

### What Worked Well:


### Issues Found:


### Suggestions for Improvement:


### Priority Fixes Needed:


---

## Next Steps After Testing

Based on test results:

1. **If Step 1 works well**: Continue to implement Steps 2-4
2. **If issues found**: Create bug list and fix before continuing
3. **If UX problems**: Refine Step 1 UI before adding more steps

**Report issues to**: https://github.com/johnzastrow/mqs/issues
