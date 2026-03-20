# QGIS PostGIS Project Manager — Design

## Problem Statement

QGIS can store project files as XML in a PostGIS database (`qgis_projects`
table).  When infrastructure changes — new database hosts, migrated schemas,
rotated authentication configurations — every layer reference in every affected
project becomes stale.

The natural fix is to open the project in QGIS and edit each layer.  This is
impractical because:

1. **QGIS tries to connect to every layer on load.**  Each broken reference
   triggers a TCP timeout (often 30 s).  A project with 40 layers and 10 broken
   ones wastes 5+ minutes just opening.
2. **Edits must be repeated for each layer.**  There is no built-in batch
   connection editor.
3. **There is no diff / audit trail.**  You cannot preview what will change
   before saving.

---

## Goals

| Goal | Description |
|------|-------------|
| G-1 | Read and write QGIS project XML stored in PostGIS without opening QGIS |
| G-2 | Surface all layer datasource URIs and auth configs in one view |
| G-3 | Allow batch correction across any number of layers at once |
| G-4 | Validate corrected credentials before saving |
| G-5 | Preserve the original project; allow saving under a new name |
| G-6 | Minimal install burden — no QGIS, no compiled extensions |

---

## Architecture

```
Scripts/qgis_project_manager.py   ← single-file application
│
├── Pure logic layer (importable without display)
│   ├── parse_pg_uri(uri)         – decompose datasource URI → dict
│   ├── build_pg_uri(dict)        – reconstruct URI from dict
│   ├── extract_layers(root)      – walk ET tree → List[LayerInfo]
│   ├── apply_changes(layers)     – write new_datasource back to ET elements
│   └── serialise_xml(root)       – ET tree → UTF-8 string with declaration
│
└── GUI layer (requires tkinter)
    ├── App (tk.Tk)               – main window, connection, project list
    ├── LayerEditDialog           – single-layer structured / raw URI editor
    └── BatchEditDialog           – multi-layer param override + find-replace
```

The pure logic layer has **no GUI or database dependency** and is fully
unit-tested without a display or network connection.

---

## Key Design Decisions

### 1. No PyQGIS dependency

The entire tool uses only `psycopg2-binary` (PostgreSQL driver) and Python
stdlib (`tkinter`, `xml.etree`, `re`, `dataclasses`).

**Why:** Importing PyQGIS requires a full QGIS installation and initialises the
QGIS application object — which would immediately start attempting to connect
to layers, recreating the exact timeout problem we are trying to avoid.

The QGIS project XML format is stable and well-documented; parsing it with
`xml.etree.ElementTree` is straightforward.

### 2. Parse → edit dict → rebuild URI (not string-patching)

When a user changes the host of a PostGIS layer, the tool:
1. Parses the URI into a plain dict (`parse_pg_uri`)
2. Updates the relevant key in the dict
3. Rebuilds the full URI from the dict (`build_pg_uri`)

It does **not** do `uri.replace("oldhost", "newhost")`.

**Why:** String replacement is fragile — the old hostname might appear in a
password, database name, table name, or SQL filter.  Structured parse/build
guarantees only the intended field changes.  The Find & Replace operation is
still available for cases where string substitution is genuinely what is needed
(e.g. updating a WMS URL).

### 3. `raw_datasource` is immutable; `new_datasource` is the working copy

Every `LayerInfo` keeps:
- `raw_datasource`: the original string, never touched after load
- `new_datasource`: the mutable working copy
- `modified`: True when the two differ

**Why:** This enables:
- Reset to original at any time without reloading the project
- Accurate before/after diff in the pending-changes summary
- The "modified" visual tag in the layer table

### 4. Auth Config ID clears embedded credentials

If `authcfg` is set in the rebuilt URI, `build_pg_uri` omits `user=` and
`password=` entirely.

**Why:** A URI with both `authcfg` and embedded credentials is ambiguous.
QGIS resolves this by preferring `authcfg`, but leaving stale credentials in
the URI is confusing and a minor security concern.  The tool enforces the
unambiguous form.

### 5. `psycopg2.sql.Identifier` for dynamic table and column names

All SQL that references the project table or content column uses
`psycopg2.sql.Identifier`, not f-string interpolation.

```python
cur.execute(
    pgsql.SQL("SELECT {} FROM {}.{} WHERE name = %s").format(
        pgsql.Identifier(self._content_col),
        pgsql.Identifier(self._db_schema),
        pgsql.Identifier(self._db_table),
    ),
    (name,),
)
```

**Why:** Direct interpolation of user-supplied schema/table names into SQL
strings is a SQL-injection vector.  `Identifier` correctly quotes the names
and escapes any special characters.

### 6. Auto-detect content column name

The tool queries `information_schema.columns` at connection time to determine
whether the content column is named `metadata` or `content`.

**Why:** The column name changed between QGIS versions.  Hard-coding one name
would silently fail on installations using the other.

### 7. Deduplication in connection testing

The connection tester groups PostGIS layers by `(host, port, dbname, user,
password)` and opens at most one test connection per unique tuple.

**Why:** A project with 30 layers all pointing at the same server should
produce one connection attempt, not 30.  This keeps the test fast and avoids
rate-limiting on the server side.

### 8. Batch operations apply PostGIS overrides first, then find-and-replace

In `BatchEditDialog._compute_new_ds`, the order is:
1. Apply PostGIS parameter overrides (structured)
2. Apply find-and-replace on the resulting URI (raw)

**Why:** This allows workflows like "update the host via the structured form,
then use find-replace to fix the schema prefix in the table name" in a single
pass.

### 9. GUI base-class stubs for headless import

```python
if _GUI_AVAILABLE:
    _AppBase    = tk.Tk
    _DialogBase = tk.Toplevel
else:
    class _AppBase:   pass
    class _DialogBase: pass

class App(_AppBase): ...
```

**Why:** The pure logic functions need to be importable by the test suite
without a display.  The stub base classes allow module-level class definitions
to succeed; the tkinter method bodies only fail at runtime if someone actually
tries to instantiate the GUI without tkinter present.

---

## Data Flow

```
PostGIS DB
    │
    │  SELECT metadata FROM qgis_projects WHERE name = ?
    ▼
Raw XML string
    │
    │  ET.fromstring()
    ▼
ET Element tree  ◄──────────────────────────────────────┐
    │                                                    │
    │  extract_layers()                                  │ apply_changes()
    ▼                                                    │
List[LayerInfo]                                          │
  ├── raw_datasource  (immutable)                        │
  ├── new_datasource  (mutable working copy)  ───────────┤
  ├── pg dict         (parsed params)         ───────────┤  build_pg_uri()
  └── ds_element      (ET.Element ref)   ────────────────┘

User edits via LayerEditDialog or BatchEditDialog
    │
    │  serialise_xml()
    ▼
Updated XML string
    │
    │  INSERT … ON CONFLICT DO UPDATE
    ▼
PostGIS DB  (or exported to .qgs file)
```

---

## PostgreSQL URI Format Reference

```
dbname='gisdb' host=db.example.com port=5432 user='gisuser'
password='s3cr3t' sslmode=require authcfg=abc1234 key='gid'
estimatedmetadata=true checkPrimaryKeyUnicity=0 srid=4326
type=MultiPolygon table="public"."roads" (geom) sql=active=1
```

| Component | Quoting | Notes |
|-----------|---------|-------|
| `dbname`, `user`, `password`, `key` | Single-quoted | May contain spaces |
| `host`, `port`, `sslmode`, `authcfg` | Bare | Simple values |
| `estimatedmetadata`, `checkPrimaryKeyUnicity`, `srid`, `type` | Bare | Optional metadata |
| `table=` | Double-quoted schema and table | Followed by `(geomcol)` if present |
| `sql=` | Bare, rest of string | Always last; may be empty |

When `authcfg` is set, `user` and `password` are omitted entirely.

---

## Limitations and Future Work

| Item | Notes |
|------|-------|
| Auth database entries | The tool updates the `authcfg` ID in the project XML but cannot create or modify the corresponding entry in QGIS's `qgis-auth.db` |
| WMS / WCS / WFS structured editor | Currently only find-and-replace; a URL-aware structured editor could be added |
| `.qgz` compressed projects | Not applicable — QGIS stores uncompressed XML in PostgreSQL |
| Table existence validation | The tool trusts user input; it does not verify schema/table exist before saving |
| Multi-project batch | Currently one project at a time; could be extended to scan all projects in a table |
