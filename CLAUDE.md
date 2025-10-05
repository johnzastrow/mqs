# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**mqs** (My QGIS Stuff) - A collection of reusable QGIS-related utilities, scripts, and tools.

**License:** MIT

## Development Rules

### Testing Requirements

**CRITICAL:** When creating or modifying functionality, always:
1. Write tests alongside the implementation
2. Run tests before considering the work complete
3. Ensure all tests pass before moving to the next task

Never implement features without corresponding tests.

**Test file location:** All test-related files must be stored in the `testing/` directory.

### Versioning Requirements

**CRITICAL:** When creating or modifying code:
1. Add version information to all code files (e.g., `__version__ = "0.1.0"` for Python)
2. Increment the version following semantic versioning (MAJOR.MINOR.PATCH):
   - PATCH: Bug fixes and minor changes
   - MINOR: New features, backward compatible
   - MAJOR: Breaking changes
3. Update `CHANGELOG.md` with a description of changes for each version bump
4. Include version number and date in CHANGELOG entries

## Repository Structure

This repository contains multiple QGIS-related subprojects, each organized in its own directory:

```
mqs/
├── Scripts/                    # Executable QGIS scripts
│   ├── extract_styles_from_projects.py
│   └── vectors2gpkg.py
├── docs/                       # Subproject documentation
│   ├── ExtractStylesfromDirectoriesForStyleManager/
│   │   ├── REQUIREMENTS.md
│   │   ├── CHANGELOG.md
│   │   ├── testing/
│   │   └── [example files]
│   └── vectors2gpkg/
│       ├── REQUIREMENTS.md
│       ├── CHANGELOG.md
│       └── testing/
└── testing/                    # Repository-level tests
```

### Subproject Organization

Each subproject should have:
- Documentation in `docs/[SubprojectName]/`
- Executable scripts in `Scripts/`
- Tests in `docs/[SubprojectName]/testing/`
- Its own CHANGELOG.md and REQUIREMENTS.md

### Current Subprojects

1. **ExtractStylesfromDirectoriesForStyleManager** (v0.2.0)
   - Script: `Scripts/extract_styles_from_projects.py`
   - Docs: `docs/ExtractStylesfromDirectoriesForStyleManager/`
   - Purpose: Extract styles from QGIS project files into XML format

2. **vectors2gpkg** (v0.8.0)
   - Script: `Scripts/vectors2gpkg.py`
   - Docs: `docs/vectors2gpkg/`
   - Purpose: Load vector files from directory trees into GeoPackage with metadata preservation

## Technical Details

- Primary language: Python (PyQGIS)
- QGIS version: 3.40+
- Testing framework: unittest (Python standard library)
- All scripts must work within QGIS Processing Toolbox environment
