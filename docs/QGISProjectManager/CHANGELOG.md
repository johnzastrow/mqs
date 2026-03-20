# QGIS PostGIS Project Manager — Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) / Semantic Versioning.

## [0.1.0] - 2026-03-19

### Added
- Initial release
- Connect to any PostGIS database containing a `qgis_projects` table
- Auto-detect content column (`metadata` vs `content`) across QGIS versions
- List all stored projects and load one for inspection
- Parse every layer's datasource URI without opening QGIS
- Structured form editor for individual PostGIS layer connection parameters
- Batch edit dialog: override connection parameters across multiple layers at once
- Find & Replace across raw datasource URIs (plain text or Python regex)
- Preview tab in batch editor — see the diff before applying
- Connection tester: verify new credentials reach the database (timeout 3 s)
- Reset selected layers to original datasource
- Save corrected project to PostGIS with the same name or a new name
- Export corrected project as a local `.qgs` file
- Pending-changes summary on the Save tab
- Column sort in layer table
- Filter bar to narrow the layer table by any text
- No PyQGIS dependency — runs outside QGIS with only `psycopg2-binary`
