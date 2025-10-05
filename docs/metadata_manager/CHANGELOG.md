# Changelog

All notable changes to the metadata_manager subproject will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-05

### Added
- Initial plugin structure using QGIS Plugin Builder
- Dockable widget interface (MetadataManager_dockwidget.ui)
- Standard QGIS plugin architecture with:
  - `__init__.py` - Plugin entry point
  - `MetadataManager.py` - Main plugin class
  - `MetadataManager_dockwidget.py` - Dockable widget implementation
  - `metadata.txt` - Plugin metadata
  - `resources.py` and `resources.qrc` - Qt resources
- Development infrastructure:
  - Makefile for compilation and deployment
  - pb_tool.cfg for pb_tool support
  - pylintrc for code quality
  - test/ directory for unit tests
  - i18n/ directory for translations
  - help/ directory for documentation
- REQUIREMENTS.md with comprehensive specifications
- CHANGELOG.md for version tracking
- Testing directory structure in `docs/metadata_manager/testing/`
- Plugin directory in `Plugins/metadata_manager/`

### Planned Features (Future Releases)
- Reusable metadata component libraries (organizations, contacts, keywords)
- Metadata template system for bulk application
- Integration with inventory_miner GeoPackage databases
- Wizard and expert modes for metadata creation
- Auto-population from layer properties
- Validation and completeness checking
- Export to QGIS XML, ISO 19115/19139, and FGDC formats
- SQLite-based persistence for libraries and templates
