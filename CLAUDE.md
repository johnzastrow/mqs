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

## Repository Status

This is a nascent repository. As QGIS-related code, scripts, and utilities are added, this document should be updated to reflect:

- Primary programming languages used (likely Python for QGIS plugins/scripts)
- Build/installation procedures
- QGIS version compatibility requirements
- Any QGIS plugin development conventions
- Testing framework and commands (e.g., pytest)
