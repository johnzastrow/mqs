# QGIS PostGIS Project Manager

**Version:** 0.1.0
**Type:** Standalone Python GUI
**Script:** `Scripts/qgis_project_manager.py`

---

## Problem

QGIS stores project files in PostGIS as plain XML in a `qgis_projects` table.
When server hostnames change, databases are migrated, or authentication
configurations are rotated, every layer in every affected project accumulates
stale connection strings.

Opening the project in QGIS to fix this triggers a timeout for each broken
layer — which can mean minutes of waiting for a single project with dozens of
layers, and worse for a portfolio of projects.

## Solution

This tool reads and rewrites the project XML **directly in the database**,
bypassing QGIS entirely.  It provides:

- A structured editor for each PostGIS layer's connection parameters
- Batch overrides across any number of selected layers at once
- Find-and-replace across all datasource URIs (plain text or regex)
- Connection testing to validate new credentials before saving
- Save back to PostGIS (overwrite or new name) or export as a `.qgs` file

---

## Installation

```bash
pip install psycopg2-binary   # only external dependency
```

Python 3.8+ and `tkinter` (included with CPython on all platforms) are required.

---

## Usage

```bash
python Scripts/qgis_project_manager.py
```

### Step 1 — Connect

Fill in the **PostGIS Connection** bar at the top and click **Connect**.
The tool detects the content column name (`metadata` or `content`) automatically.

### Step 2 — Load a project

On the **1 · Projects** tab, select a project from the list and click
**Load selected project**.  Double-clicking the name works too.

### Step 3 — Inspect layers

The **2 · Layers** tab shows every layer with:

| Column | Description |
|--------|-------------|
| Layer Name | As stored in the project |
| Type | PostGIS, WMS/WMTS, OGR/File, etc. |
| Host | Extracted from the datasource URI (PostGIS only) |
| Database | Database name (PostGIS only) |
| Schema.Table | Parsed schema and table (PostGIS only) |
| Auth Config | `authcfg` ID, or `user/pass` if credentials are embedded |
| Modified | `✎ yes` if this session has changed the layer |
| Connection | `✓ OK` / `✗ Fail` after running **Test Connections** |

Use the **Filter** box to narrow the list.  Click column headers to sort.

### Step 4 — Edit

**Edit Layer…** — opens a structured form for a single selected layer.

**Batch Edit Selected…** — opens a dialog with three tabs:

- *PostGIS Params* — override specific URI keys for all selected PostGIS
  layers.  Leave a field blank to keep the current value.  Setting
  **Auth Config ID** automatically removes embedded user/password.
- *Find & Replace in URI* — text substitution across all selected layers
  (any provider type), with optional Python regex support.
- *Preview* — review the diff before committing.

**Reset Selected** — revert to the original datasource.

**Test Connections** — attempt a live psycopg2 connection (3-second timeout)
to each unique host/port/database combination and annotate each row.

### Step 5 — Save

On the **3 · Save** tab:

- **Save to PostGIS** — writes the corrected XML back.  Leave the name blank
  to overwrite the original; enter a new name to create a copy.
- **Export as .qgs** — saves the corrected project as a local file
  (useful as a backup before overwriting).
- **Refresh summary** — shows a before/after diff of all modified layers.

---

## How QGIS stores projects in PostGIS

QGIS uses a table (default `public.qgis_projects`) with two columns:

| Column | Type | Content |
|--------|------|---------|
| `name` | text PK | Project name / path |
| `metadata` (or `content`) | text | Full project XML |

The XML is identical to a `.qgs` file.  Each layer's connection string lives
in a `<datasource>` element inside a `<maplayer>` block.

### PostGIS datasource URI format

```
dbname='gisdb' host=db.example.com port=5432 user='gisuser'
password='s3cr3t' sslmode=require authcfg=abc1234 key='gid'
estimatedmetadata=true table="public"."roads" (geom) sql=
```

Key rules the parser and builder both follow:

- `dbname`, `user`, `password`, `key` are single-quoted
- `host`, `port`, `sslmode`, `authcfg` are unquoted
- `table=` uses double-quoted schema and table names
- If `authcfg` is set, `user` and `password` are omitted

---

## Limitations

- **Auth Config IDs** are references into QGIS's local authentication database
  (`~/.local/share/QGIS/QGIS3/profiles/default/qgis-auth.db`).  This tool
  can update the ID stored in the project XML, but it cannot create or manage
  the corresponding entry in the auth database.
- **WMS / WCS / WFS / file-based layers** are displayed in the table and
  support find-and-replace, but have no structured field editor.
- **Compressed projects** (`.qgz`) are not supported; QGIS stores uncompressed
  XML when using PostgreSQL project storage.
- The tool does not validate whether a schema or table actually exists — it
  trusts the values you enter.

---

## Testing

Unit tests for the URI parsing and building functions live in:

```
docs/QGISProjectManager/testing/test_uri_parsing.py
```

Run with:

```bash
python -m pytest docs/QGISProjectManager/testing/
# or without pytest:
python docs/QGISProjectManager/testing/test_uri_parsing.py
```
