# TODO - Metadata Manager

**Current Version:** 0.4.1
**Last Updated:** October 6, 2025

---

 📚 File Roles Summary

  | File                       | Purpose              | You Should            |
  |----------------------------|----------------------|-----------------------|
  | TODO.md                    | Active task tracking | ✅ Add to this!        |
  | REQUIREMENTS.md            | Spec document        | 📖 Read for reference |
  | NEXT_SESSION_START_HERE.md | Session startup      | 📖 Read each session  |
  | QUICK_REFERENCE.md         | Commands/cheat sheet | 📖 Quick lookup       |
  | SESSION_SUMMARY_*.md       | Session history      | 📖 Review if needed   |
  

## 🐛 Bugs / Issues

### High Priority
- [ ] Test GeoPackage embedded metadata writing (not fully tested yet)
- [ ] Verify QGIS can read written .qmd files
- [ ] Test with multi-layer GeoPackage containers

### Medium Priority
- [ ] Add write retry UI (if file write fails, retry from cache)
- [ ] Improve error messages when layer not found in inventory

### Low Priority
- [ ] Add undo/redo for metadata edits
- [ ] Detect external changes to .qmd files
- [ ] Better handling of very large metadata JSON

---

## ✨ Features - In Progress

### Libraries Management (v0.5.0 target)
- [ ] Organizations CRUD UI
  - [ ] Table showing all organizations
  - [ ] Add organization dialog
  - [ ] Edit organization dialog
  - [ ] Delete organization (with confirmation)
  - [ ] Import/export organization list
- [ ] Contacts CRUD UI
  - [ ] Link contacts to organizations
  - [ ] Add/edit/delete contacts
  - [ ] Contact roles dropdown
- [ ] Keywords Management
  - [ ] Keyword library table
  - [ ] Hierarchical keyword tree view
  - [ ] Keyword sets/collections
  - [ ] Import standard vocabularies (ISO 19115, GCMD, etc.)
- [ ] Integration with Wizard
  - [ ] Organizations dropdown in Step 2
  - [ ] Keywords autocomplete in Step 1
  - [ ] Save contact selections

### Templates System (v0.6.0 target)
- [ ] Create template from current metadata
- [ ] Template library UI
- [ ] Apply template to layer
- [ ] Edit template
- [ ] Delete template
- [ ] Import/export templates (JSON/XML)
- [ ] Template preview

### Batch Operations (v0.7.0 target)
- [ ] Select multiple layers from inventory
- [ ] Apply template to selected layers
- [ ] Bulk update specific fields
- [ ] Progress dialog for batch operations
- [ ] Batch export to .qmd files

---

## 🚀 Features - Planned

### Import/Export
- [ ] Import metadata from existing .qmd files
- [ ] Import from ISO 19115 XML
- [ ] Export templates to share with others
- [ ] Export metadata summary as CSV/PDF

### Expert Mode
- [ ] Single-page form (alternative to wizard)
- [ ] Toggle between Wizard ↔ Expert mode
- [ ] All fields visible and editable
- [ ] Collapsible sections

### Smart Features
- [ ] Auto-generate abstract from layer properties
- [ ] Suggest keywords based on title/abstract
- [ ] Copy metadata from similar layers
- [ ] Metadata completeness suggestions

### Advanced
- [ ] Metadata diff/comparison viewer
- [ ] Version history for metadata edits
- [ ] Sync detection (check if target modified externally)
- [ ] Metadata validation against standards
- [ ] Multi-language metadata support

---

## 💡 Enhancement Ideas

### UI/UX Improvements
- [ ] Keyboard shortcuts for wizard navigation
- [ ] Dark mode support
- [ ] Customizable wizard step order
- [ ] Save drafts (metadata not yet complete)
- [ ] Recent layers list

### Performance
- [ ] Cache layer list for faster loading
- [ ] Lazy-load inventory (paginate if >1000 layers)
- [ ] Background processing for batch operations
- [ ] Optimize dashboard statistics queries

### Integration
- [ ] Context menu: "Edit Metadata" in QGIS layer tree
- [ ] Processing algorithm for batch metadata creation
- [ ] Integration with QGIS Browser panel
- [ ] Web service integration (CSW catalog upload)

### Documentation
- [ ] User guide with screenshots
- [ ] Video tutorials
- [ ] API documentation for developers
- [ ] Common workflows guide

---

## 📝 User Feature Requests

### Add your requests here!

**Format:**
```
- [ ] Feature description
  - Why: Reason/use case
  - Priority: High/Medium/Low
  - Added by: Your name
  - Date: YYYY-MM-DD
```

**Example:**
- [ ] Add "Copy from existing layer" button
  - Why: Save time by copying metadata from similar layers
  - Priority: Medium
  - Added by: John
  - Date: 2025-10-06

---

## ✅ Recently Completed

### v0.4.1 (Oct 6, 2025)
- [x] Fixed XML serialization bug (toXml → writeMetadataXml)
- [x] Added file name column to layer selector

### v0.4.0 (Oct 6, 2025)
- [x] Write metadata to .qmd sidecar files
- [x] Write metadata to GeoPackage embedded
- [x] Auto-detect file format
- [x] Handle container files (multi-layer .gpkg)
- [x] Track write status in cache
- [x] Fixed container file bug (all layers marked complete)

### v0.3.6 (Oct 6, 2025)
- [x] Load SpatiaLite extension automatically
- [x] Fix "ST_IsEmpty" error

### v0.3.5 (Oct 6, 2025)
- [x] Auto-refresh dashboard after save

### v0.3.0 (Oct 5, 2025)
- [x] 4-step wizard complete
- [x] Save to cache
- [x] Load from cache
- [x] Status tracking

---

## 🎯 Next Session Focus

**Immediate (Next Session):**
1. Test file writing with Shapefile
2. Test GeoPackage embedded metadata
3. Start Libraries Management UI (if tests pass)

**This Week:**
1. Organizations CRUD
2. Contacts CRUD
3. Keywords management

**This Month:**
1. Templates system
2. Batch operations
3. Import/export

---

## 📋 Reference Documents

- **REQUIREMENTS.md** - Complete feature specification (read-only reference)
- **NEXT_SESSION_START_HERE.md** - Quick start for next session
- **QUICK_REFERENCE.md** - Commands and cheat sheet
- **METADATA_WRITING_IMPLEMENTATION.md** - Technical details

---

## 🏷️ Labels/Tags

Use these for organizing:
- `bug` - Something broken
- `enhancement` - Improvement to existing feature
- `feature` - New functionality
- `ui` - User interface
- `performance` - Speed/optimization
- `documentation` - Docs/guides
- `testing` - Test cases
- `user-request` - Requested by user

---

## 📊 Progress Tracking

**Overall Completion:** ~65%

| Component | Status | Version |
|-----------|--------|---------|
| Database Architecture | ✅ Done | 0.2.0 |
| Dashboard | ✅ Done | 0.2.0 |
| Metadata Wizard | ✅ Done | 0.3.0 |
| File Writing | ✅ Done | 0.4.0 |
| Libraries Management | 🚧 In Progress | 0.5.0 |
| Templates | 📋 Planned | 0.6.0 |
| Batch Operations | 📋 Planned | 0.7.0 |
| Import/Export | 📋 Planned | 0.8.0 |
| Expert Mode | 📋 Planned | 0.9.0 |
| v1.0 Release | 📋 Planned | 1.0.0 |

---

## 💬 Notes

- Keep this file updated as you work
- Move completed items to "Recently Completed" section
- Add user requests as they come up
- Link to GitHub issues if you create them
- Use checkboxes for easy tracking

---

**How to use this file:**
1. Add your feature requests/ideas in "User Feature Requests" section
2. Bugs go in "Bugs / Issues" section
3. Check items as completed
4. Review before each session
5. Keep it simple and actionable!
