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

This repository contains multiple QGIS-related subprojects in two categories:

```
mqs/
├── Scripts/                    # QGIS Processing Toolbox scripts
│   ├── extract_styles_from_projects.py
│   ├── vectors2gpkg.py
│   ├── batchvectorrename.py
│   └── inventory_miner.py
├── Plugins/                    # QGIS Plugins
│   └── metadata_manager/
│       ├── __init__.py
│       ├── MetadataManager.py
│       ├── metadata.txt
│       ├── resources.qrc
│       ├── Makefile
│       └── [plugin files]
├── docs/                       # Subproject documentation
│   ├── [SubprojectName]/
│   │   ├── README.md
│   │   ├── REQUIREMENTS.md
│   │   ├── CHANGELOG.md
│   │   └── testing/
│   └── metadata_manager/
│       ├── README.md
│       ├── REQUIREMENTS.md
│       ├── CHANGELOG.md
│       └── testing/
└── testing/                    # Repository-level tests
```

### Subproject Organization

#### Processing Toolbox Scripts
Each script-based subproject should have:
- Documentation in `docs/[SubprojectName]/`
  - `README.md` - User documentation and usage guide
  - `REQUIREMENTS.md` - Technical specifications
  - `CHANGELOG.md` - Version history
  - `testing/` - Test files and data
- Executable script in `Scripts/[scriptname].py`
- Version info in script header (`__version__ = "x.y.z"`)
- Script group: "MQS Tools" (for consistency in QGIS)

#### QGIS Plugins
Each plugin-based subproject should have:
- Plugin code in `Plugins/[plugin_name]/`
  - Standard QGIS plugin structure (use Plugin Builder)
  - `metadata.txt` - Plugin metadata
  - `__init__.py` - Plugin entry point with `classFactory()`
  - Main plugin class (e.g., `MetadataManager.py`)
  - Resources (`resources.qrc`, compiled to `resources.py`)
  - Build infrastructure (`Makefile`, `pb_tool.cfg`)
  - Tests in `test/` directory within plugin
- Documentation in `docs/[plugin_name]/`
  - `README.md` - Installation and usage
  - `REQUIREMENTS.md` - Technical specifications
  - `CHANGELOG.md` - Version history
  - `testing/` - Additional test data if needed

### Current Subprojects

#### Processing Toolbox Scripts

1. **ExtractStylesfromDirectoriesForStyleManager** (v0.2.0)
   - Type: Processing Script
   - Script: `Scripts/extract_styles_from_projects.py`
   - Docs: `docs/ExtractStylesfromDirectoriesForStyleManager/`
   - Purpose: Extract styles from QGIS project files into XML format

2. **vectors2gpkg** (v0.8.3)
   - Type: Processing Script
   - Script: `Scripts/vectors2gpkg.py`
   - Docs: `docs/vectors2gpkg/`
   - Purpose: Load vector files from directory trees into GeoPackage with metadata preservation

3. **batchvectorrename**
   - Type: Processing Script
   - Script: `Scripts/batchvectorrename.py`
   - Docs: `docs/batchvectorrename/`
   - Purpose: Batch rename layers in vector files and databases

4. **inventory_miner** (v0.1.0)
   - Type: Processing Script
   - Script: `Scripts/inventory_miner.py`
   - Docs: `docs/inventory_miner/`
   - Purpose: Scan directories and create spatial inventory of geospatial data in GeoPackage

#### QGIS Plugins

5. **metadata_manager** (v0.1.0) - IN DEVELOPMENT
   - Type: QGIS Plugin
   - Plugin: `Plugins/metadata_manager/`
   - Docs: `docs/metadata_manager/`
   - Purpose: Create and manage QGIS layer metadata with reusable templates and inventory integration

## Technical Details

### Common Requirements
- Primary language: Python (PyQGIS)
- QGIS version: 3.40+
- Testing framework: unittest (Python standard library)

### Processing Toolbox Scripts
- Must work within QGIS Processing Toolbox environment
- Inherit from `QgsProcessingAlgorithm`
- Use group "MQS Tools" for consistency
- Include `__version__` in script header

### QGIS Plugins
- Follow standard QGIS plugin structure (use Plugin Builder)
- Must compile resources: `pyrcc5 -o resources.py resources.qrc`
- Include `metadata.txt` with proper metadata
- Provide `Makefile` and/or `pb_tool.cfg` for builds
- Tests in `test/` directory within plugin
- Must have `classFactory()` in `__init__.py`

## Creating New Subprojects

When creating a new subproject, follow these steps:

### For Processing Toolbox Scripts:

1. Create directory structure:
   ```
   mkdir -p docs/[SubprojectName]/testing
   ```

2. Create essential files:
   - `docs/[SubprojectName]/README.md` - User documentation
   - `docs/[SubprojectName]/REQUIREMENTS.md` - Technical specs
   - `docs/[SubprojectName]/CHANGELOG.md` - Version history (start with v0.1.0)
   - `Scripts/[scriptname].py` - Main script with `__version__ = "0.1.0"`

3. Update main README.md with new subproject section

4. Script must:
   - Inherit from `QgsProcessingAlgorithm`
   - Set group to "MQS Tools"
   - Include comprehensive help text
   - Have version info in header

### For QGIS Plugins:

1. Use QGIS Plugin Builder to create initial structure in temp location

2. Move to repository:
   ```
   cp -r /temp/plugin_output Plugins/[plugin_name]
   mkdir -p docs/[plugin_name]/testing
   ```

3. Create documentation files:
   - `docs/[plugin_name]/README.md` - Installation and usage
   - `docs/[plugin_name]/REQUIREMENTS.md` - Technical specs
   - `docs/[plugin_name]/CHANGELOG.md` - Version history

4. Update `metadata.txt`:
   - Set proper name, version (0.1.0), description
   - Set `qgisMinimumVersion=3.40`
   - Add repository and tracker URLs
   - Set `experimental=True` for initial releases

5. Update main README.md with new plugin section

6. Compile resources before first use:
   ```
   cd Plugins/[plugin_name]
   make
   ```
