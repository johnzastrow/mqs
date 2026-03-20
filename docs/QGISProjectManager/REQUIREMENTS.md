# QGIS PostGIS Project Manager — Requirements

## Functional Requirements

### FR-1  Database connection
- Connect to any PostgreSQL / PostGIS host with standard credentials
- Support configurable schema and table names (default: `public.qgis_projects`)
- Auto-detect whether the content column is named `metadata` or `content`

### FR-2  Project listing
- List all projects stored in the configured table
- Allow the user to select and load one project without opening QGIS

### FR-3  Layer analysis
- Parse every `<maplayer>` element in the project XML
- Display layer name, provider type, host, database, schema.table, auth config
- Support all provider types in the table; structured editing for `postgres` only

### FR-4  Individual layer editing
- Provide a structured form for PostGIS connection parameters:
  host, port, database, schema, table, geometry column, user, password,
  auth config ID, SSL mode, SQL filter
- Provide a raw text editor for all other provider types
- Syncing the raw editor back to the structured form on focus-out

### FR-5  Batch editing
- Override one or more PostGIS connection parameters across all selected layers
- A blank override field must leave the layer's current value unchanged
- Setting Auth Config ID must remove `user` and `password` from the URI
- Find-and-replace across raw datasource strings (plain text and Python regex)
- Apply both operations together in a single action
- Preview diff before applying

### FR-6  Connection testing
- Attempt a direct psycopg2 connection to each unique (host, port, dbname) tuple
- Deduplicate: do not try the same credentials more than once
- Timeout: 3 seconds per connection attempt
- Annotate each row in the layer table with ✓ OK or ✗ Fail

### FR-7  Reset
- Allow selected layers to be reset to their original (unedited) datasource

### FR-8  Save to PostGIS
- Write the corrected project XML back using INSERT … ON CONFLICT DO UPDATE
- Allow saving under a different name (creates new record)

### FR-9  Export to file
- Write the corrected project as a `.qgs` file to a user-chosen path

### FR-10  Change summary
- Display a human-readable diff of all pending OLD → NEW datasource changes

## Non-functional Requirements

| ID    | Requirement |
|-------|-------------|
| NF-1  | No PyQGIS / QGIS installation required |
| NF-2  | Single Python file; only external dependency is `psycopg2-binary` |
| NF-3  | Runs on Python 3.8+ (ET.indent degrades gracefully on 3.8) |
| NF-4  | Cross-platform: Linux, macOS, Windows (wherever tkinter is available) |
| NF-5  | Does **not** open or connect to QGIS at any point |
| NF-6  | Uses `psycopg2.sql.Identifier` for dynamic table/column names (SQL-injection safe) |

## Dependencies

| Package           | Purpose                  | Install                          |
|-------------------|--------------------------|----------------------------------|
| `psycopg2-binary` | PostgreSQL driver        | `pip install psycopg2-binary`    |
| `tkinter`         | GUI framework            | Included with CPython            |
| `xml.etree`       | XML parse / serialise    | Python standard library          |
| `re`              | URI parsing, find/replace| Python standard library          |
