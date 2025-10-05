# Changelog

All notable changes to the mqs repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-10-04

### Added
- vectors2gpkg duplicate layer name handling (v0.6.0) - automatic resolution of naming collisions
- KMZ file support for compressed KML files (v0.5.1)
- Smart layer naming with incrementing numbers for duplicate names
- Enhanced documentation for duplicate handling across all formats

### Changed
- Updated vectors2gpkg subproject to v0.6.0 with comprehensive duplicate prevention
- Enhanced main README features list to include duplicate collision handling
- Updated REQUIREMENTS.md to reflect current multi-format capabilities

## [0.3.0] - 2025-10-04

### Added
- vectors2gpkg subproject (v0.5.0) - Vector Files to GeoPackage Converter
- Support for 10 vector file formats including container formats (GeoPackages, File Geodatabases, SpatiaLite)
- Non-spatial table handling and user-selectable file type processing
- Comprehensive documentation for vectors2gpkg in docs/vectors2gpkg/

### Changed
- Updated main README.md to include vectors2gpkg subproject overview
- Updated Scripts section to reference vectors2gpkg.py

## [0.2.0] - 2025-10-04

### Changed
- Reorganized repository to support multiple subprojects
- Moved ExtractStylesfromDirectoriesForStyleManager to docs/ExtractStylesfromDirectoriesForStyleManager/
- Moved executable scripts to Scripts/ directory
- Updated repository documentation to reflect subproject structure

### Added
- Repository structure documentation in CLAUDE.md
- Subproject overview in README.md
- Repository-level CHANGELOG.md

## [0.1.0] - 2025-10-04

### Added
- Initial repository setup
- CLAUDE.md with development rules for testing and versioning
- ExtractStylesfromDirectoriesForStyleManager subproject (see docs/ExtractStylesfromDirectoriesForStyleManager/CHANGELOG.md for details)
