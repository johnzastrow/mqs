# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-04

### Added
- Initial repository setup
- CLAUDE.md with development rules for testing and versioning
- CHANGELOG.md for tracking project changes
- `extract_styles_from_projects.py` - QGIS Processing algorithm to extract styles from project files
  - Recursively searches directories for .qgs and .qgz project files
  - Extracts symbols, color ramps, and other style types
  - Consolidates styles into single XML output file compatible with QGIS Style Manager
  - Multi-select parameter for choosing which style types to extract
  - Handles duplicate names by incrementing counters
  - Provides detailed progress feedback and error handling
  - Option to extract from embedded style databases in .qgz files
- `testing/test_extract_styles.py` - Comprehensive test suite for style extraction
  - XML parsing validation tests
  - Duplicate name handling tests
  - .qgz file structure validation
  - Integration test placeholders for QGIS environment
- `docs/REQUIREMENTS.md` - Detailed requirements and technical documentation
  - Complete enumeration of QGIS 3.40 style types
  - XML output format specifications
  - Project file structure analysis
  - Extraction strategy documentation
