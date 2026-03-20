"""
QGIS PostGIS Project Manager
=============================
Standalone GUI tool that connects to a PostGIS database, reads QGIS project
files stored in the ``qgis_projects`` table, analyses every layer's datasource
URI and authentication configuration, lets you batch-correct them, and writes
the updated project back to PostGIS – all without opening QGIS.

Why standalone?  Opening a stale project in QGIS triggers connection timeouts
for every broken layer reference.  This tool edits the raw XML directly.

Requirements
------------
    pip install psycopg2-binary   # PostgreSQL driver (only non-stdlib dep)

Usage
-----
    python qgis_project_manager.py

Author: MQS Tools
License: MIT
"""

from __future__ import annotations

__version__ = "0.1.0"

import re
import sys
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# GUI imports are optional so the pure-logic functions can be imported and
# tested without a display (e.g. in headless CI or WSL).
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.sql as pgsql
except ImportError:
    psycopg2 = None   # type: ignore[assignment]
    pgsql     = None  # type: ignore[assignment]

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

# Keys whose values are single-quoted in a QGIS PostgreSQL datasource URI
_PG_QUOTED = ("dbname", "user", "password", "key")

# Keys whose values are bare (unquoted)
_PG_UNQUOTED = (
    "host", "port", "sslmode", "authcfg",
    "estimatedmetadata", "checkPrimaryKeyUnicity", "srid", "type",
)

PROVIDER_LABELS: Dict[str, str] = {
    "postgres": "PostGIS",
    "wms":      "WMS/WMTS",
    "wcs":      "WCS",
    "wfs":      "WFS",
    "ogr":      "OGR/File",
    "gdal":     "GDAL/Raster",
    "memory":   "Memory",
}


def _provider_label(p: str) -> str:
    return PROVIDER_LABELS.get((p or "").lower(), p or "—")


# ═══════════════════════════════════════════════════════════════════════════════
# Data model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class LayerInfo:
    """Represents one <maplayer> entry from a QGIS project."""
    layer_id:      str
    name:          str
    provider:      str
    raw_datasource: str        # original, never mutated
    ds_element:    object      # ET.Element ref to <datasource>

    # Parsed PostGIS URI components (postgres provider only)
    pg: Dict[str, str] = field(default_factory=dict)

    # Working copy – edit this; raw_datasource stays for diff / reset
    new_datasource: str = ""
    modified:       bool = False

    def __post_init__(self) -> None:
        if not self.new_datasource:
            self.new_datasource = self.raw_datasource


# ═══════════════════════════════════════════════════════════════════════════════
# PostgreSQL datasource URI  ·  parse & build
# ═══════════════════════════════════════════════════════════════════════════════

def parse_pg_uri(uri: str) -> Dict[str, str]:
    """
    Decompose a QGIS PostgreSQL datasource URI into a plain dict.

    Example URI::

        dbname='gisdb' host=db.example.com port=5432 user='gisuser'
        password='s3cr3t' sslmode=require authcfg=abc1234 key='gid'
        estimatedmetadata=true table="public"."roads" (geom) sql=

    """
    result: Dict[str, str] = {}

    for key in _PG_QUOTED + _PG_UNQUOTED:
        # Try quoted form first: key='value'
        m = re.search(rf"\b{re.escape(key)}='([^']*)'", uri)
        if m:
            result[key] = m.group(1)
            continue
        # Fall back to bare form: key=value (stops at whitespace)
        m = re.search(rf"\b{re.escape(key)}=(\S+)", uri)
        if m:
            val = m.group(1)
            # Exclude table= captures that start with a double-quote
            if not val.startswith('"'):
                result[key] = val

    # table="schema"."table" (geometry_column)
    m = re.search(r'\btable="([^"]+)"\."([^"]+)"\s*(?:\((\w+)\))?', uri)
    if m:
        result["schema"]  = m.group(1)
        result["table"]   = m.group(2)
        result["geomcol"] = m.group(3) or ""
    else:
        # No explicit schema
        m = re.search(r'\btable="([^"]+)"\s*(?:\((\w+)\))?', uri)
        if m:
            result["schema"]  = ""
            result["table"]   = m.group(1)
            result["geomcol"] = m.group(2) or ""

    # sql= is almost always last and may be empty
    m = re.search(r'\bsql=(.*)', uri)
    result["sql"] = m.group(1).strip() if m else ""

    return result


def build_pg_uri(pg: Dict[str, str]) -> str:
    """
    Reconstruct a QGIS PostgreSQL datasource URI from the parsed dict.

    If ``authcfg`` is present and non-empty, ``user`` and ``password``
    are omitted so the URI is clean and unambiguous.
    """
    parts: List[str] = []

    def _q(key: str) -> None:           # single-quoted
        v = pg.get(key, "").strip()
        if v:
            parts.append(f"{key}='{v}'")

    def _r(key: str) -> None:           # raw / unquoted
        v = pg.get(key, "").strip()
        if v:
            parts.append(f"{key}={v}")

    _q("dbname")
    _r("host")
    _r("port")

    has_authcfg = bool(pg.get("authcfg", "").strip())
    if not has_authcfg:
        _q("user")
        _q("password")

    _r("sslmode")
    if has_authcfg:
        parts.append(f"authcfg={pg['authcfg'].strip()}")

    _q("key")
    for extra in ("estimatedmetadata", "checkPrimaryKeyUnicity", "srid", "type"):
        _r(extra)

    schema  = pg.get("schema", "").strip()
    table   = pg.get("table",  "").strip()
    geomcol = pg.get("geomcol", "").strip()
    if table:
        tbl = f'table="{schema}"."{table}"' if schema else f'table="{table}"'
        if geomcol:
            tbl += f" ({geomcol})"
        parts.append(tbl)

    parts.append(f"sql={pg.get('sql', '').strip()}")
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# QGIS project XML helpers
# ═══════════════════════════════════════════════════════════════════════════════

def extract_layers(root: ET.Element) -> List[LayerInfo]:
    """Walk project XML and return one LayerInfo per <maplayer>."""
    layers: List[LayerInfo] = []
    for ml in root.iter("maplayer"):
        id_el   = ml.find("id")
        name_el = ml.find("layername")
        prov_el = ml.find("provider")
        ds_el   = ml.find("datasource")

        if ds_el is None:
            continue  # nothing useful without a datasource element

        layer_id = (id_el.text   or "unknown") if id_el   is not None else "unknown"
        name     = (name_el.text or "unnamed") if name_el is not None else "unnamed"
        provider = (prov_el.text or "")        if prov_el is not None else ""
        ds       = (ds_el.text   or "")

        info = LayerInfo(
            layer_id=layer_id, name=name, provider=provider,
            raw_datasource=ds, ds_element=ds_el,
        )
        if provider.lower() == "postgres":
            info.pg = parse_pg_uri(ds)
        layers.append(info)
    return layers


def apply_changes(layers: List[LayerInfo]) -> None:
    """Write new_datasource back into each modified layer's XML element."""
    for layer in layers:
        if layer.modified:
            layer.ds_element.text = layer.new_datasource


def serialise_xml(root: ET.Element) -> str:
    """Return the project XML as a UTF-8 string with declaration."""
    try:
        ET.indent(root, space="  ")   # Python 3.9+
    except AttributeError:
        pass
    body = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body


# ═══════════════════════════════════════════════════════════════════════════════
# GUI base-class stubs — allow module import without a display for testing
# ═══════════════════════════════════════════════════════════════════════════════

if _GUI_AVAILABLE:
    _AppBase:      type = tk.Tk
    _DialogBase:   type = tk.Toplevel
else:
    class _AppBase:     pass   # type: ignore[no-redef]
    class _DialogBase:  pass   # type: ignore[no-redef]


# ═══════════════════════════════════════════════════════════════════════════════
# Main application window
# ═══════════════════════════════════════════════════════════════════════════════

class App(_AppBase):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"QGIS PostGIS Project Manager  v{__version__}")
        self.geometry("1160x760")
        self.minsize(900, 600)

        # Runtime state
        self.conn:            Optional[psycopg2.extensions.connection] = None
        self._db_schema:      str = "public"
        self._db_table:       str = "qgis_projects"
        self._content_col:    str = "metadata"
        self.current_root:    Optional[ET.Element] = None
        self.layers:          List[LayerInfo] = []
        self._loaded_project: str = ""

        self._build_ui()

    # ── UI skeleton ───────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_conn_bar()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self._build_projects_tab()
        self._build_layers_tab()
        self._build_save_tab()
        self._status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self._status_var, anchor="w",
                  relief="sunken", padding=(4, 2)).pack(fill="x", side="bottom")

    # Connection bar

    def _build_conn_bar(self) -> None:
        bar = ttk.LabelFrame(self, text="PostGIS Connection", padding=6)
        bar.pack(fill="x", padx=8, pady=(6, 2))
        self._cv: Dict[str, tk.StringVar] = {}
        spec = [
            ("Host",     "host",   "localhost", 14, ""),
            ("Port",     "port",   "5432",       5, ""),
            ("Database", "dbname", "",          14, ""),
            ("Schema",   "schema", "public",     9, ""),
            ("User",     "user",   "",          12, ""),
            ("Password", "pass",   "",          12, "*"),
        ]
        for col, (lbl, key, default, w, show) in enumerate(spec):
            ttk.Label(bar, text=lbl + ":").grid(
                row=0, column=col * 2, sticky="e", padx=(6, 2))
            v = tk.StringVar(value=default)
            self._cv[key] = v
            ttk.Entry(bar, textvariable=v, width=w, show=show).grid(
                row=0, column=col * 2 + 1, sticky="ew", padx=(0, 4))
        ttk.Button(bar, text="Connect", command=self._connect).grid(
            row=0, column=len(spec) * 2, padx=6)
        self._conn_lbl = ttk.Label(bar, text="● Not connected", foreground="red")
        self._conn_lbl.grid(row=0, column=len(spec) * 2 + 1, padx=6)

    # Tab 1 – Projects

    def _build_projects_tab(self) -> None:
        f = ttk.Frame(self.nb, padding=6)
        self.nb.add(f, text="1 · Projects")

        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 4))
        ttk.Label(top, text="Projects table:").pack(side="left")
        self._table_var = tk.StringVar(value="qgis_projects")
        ttk.Entry(top, textvariable=self._table_var, width=28).pack(side="left", padx=4)
        ttk.Button(top, text="↺  Refresh", command=self._refresh_projects).pack(side="left")

        lf = ttk.LabelFrame(f, text="Available projects  (double-click to load)", padding=4)
        lf.pack(fill="both", expand=True)
        ysb = ttk.Scrollbar(lf, orient="vertical")
        self._project_lb = tk.Listbox(
            lf, yscrollcommand=ysb.set, selectmode="single", font=("Consolas", 10))
        ysb.config(command=self._project_lb.yview)
        ysb.pack(side="right", fill="y")
        self._project_lb.pack(fill="both", expand=True)
        self._project_lb.bind("<Double-Button-1>", lambda _: self._load_project())

        ttk.Button(f, text="Load selected project  →",
                   command=self._load_project).pack(pady=6, anchor="e")

    # Tab 2 – Layers

    def _build_layers_tab(self) -> None:
        f = ttk.Frame(self.nb, padding=6)
        self.nb.add(f, text="2 · Layers")
        f.rowconfigure(1, weight=1)
        f.columnconfigure(0, weight=1)

        # Filter / select row
        flt = ttk.Frame(f)
        flt.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        ttk.Label(flt, text="Filter:").pack(side="left")
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._refresh_tree())
        ttk.Entry(flt, textvariable=self._filter_var, width=30).pack(side="left", padx=4)
        ttk.Button(flt, text="Select All",   command=self._sel_all).pack(side="left", padx=2)
        ttk.Button(flt, text="Deselect All", command=self._sel_none).pack(side="left", padx=2)
        self._count_lbl = ttk.Label(flt, text="No project loaded")
        self._count_lbl.pack(side="right", padx=6)

        # Layer table
        cols = ("name", "provider", "host", "dbname", "schema_table",
                "authcfg", "changed", "status")
        self._tree = ttk.Treeview(f, columns=cols, show="headings",
                                   selectmode="extended")
        spec = {
            "name":         ("Layer Name",      190),
            "provider":     ("Type",             70),
            "host":         ("Host",            130),
            "dbname":       ("Database",        110),
            "schema_table": ("Schema . Table",  200),
            "authcfg":      ("Auth Config",      82),
            "changed":      ("Modified",         62),
            "status":       ("Connection",       84),
        }
        for col, (heading, w) in spec.items():
            self._tree.heading(col, text=heading,
                               command=lambda c=col: self._sort_tree(c))
            self._tree.column(col, width=w, minwidth=50, anchor="w")

        ysb = ttk.Scrollbar(f, orient="vertical",   command=self._tree.yview)
        xsb = ttk.Scrollbar(f, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscroll=ysb.set, xscroll=xsb.set)
        self._tree.grid(row=1, column=0, sticky="nsew")
        ysb.grid(row=1, column=1, sticky="ns")
        xsb.grid(row=2, column=0, sticky="ew")

        # Action buttons
        bf = ttk.Frame(f)
        bf.grid(row=3, column=0, columnspan=2, sticky="ew", pady=6)
        ttk.Button(bf, text="Edit Layer…",
                   command=self._edit_layer).pack(side="left", padx=4)
        ttk.Button(bf, text="Batch Edit Selected…",
                   command=self._batch_edit).pack(side="left", padx=4)
        ttk.Button(bf, text="Reset Selected",
                   command=self._reset_selected).pack(side="left", padx=4)
        ttk.Separator(bf, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(bf, text="Test Connections",
                   command=self._test_connections).pack(side="left", padx=4)
        ttk.Button(bf, text="→  Go to Save",
                   command=lambda: self.nb.select(2)).pack(side="right", padx=4)

        # Visual tags
        self._tree.tag_configure("modified", background="#fffacd")
        self._tree.tag_configure("ok",       foreground="#006400")
        self._tree.tag_configure("fail",     foreground="#bb0000")

    # Tab 3 – Save

    def _build_save_tab(self) -> None:
        f = ttk.Frame(self.nb, padding=12)
        self.nb.add(f, text="3 · Save")
        f.columnconfigure(1, weight=1)

        # Save to PostGIS
        ttk.Label(f, text="Save to PostGIS", font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(f, text="Project name:").grid(row=1, column=0, sticky="e", padx=(0, 6))
        self._save_name = tk.StringVar()
        ttk.Entry(f, textvariable=self._save_name, width=46).grid(
            row=1, column=1, sticky="ew")
        ttk.Button(f, text="Save to PostGIS",
                   command=self._save_to_postgis).grid(row=1, column=2, padx=4)
        ttk.Label(f, text="(blank = overwrite original name)",
                  foreground="gray").grid(row=2, column=1, sticky="w")

        ttk.Separator(f, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # Export to .qgs
        ttk.Label(f, text="Export as .qgs file", font=("", 10, "bold")).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(f, text="File path:").grid(row=5, column=0, sticky="e", padx=(0, 6))
        self._export_path = tk.StringVar()
        ttk.Entry(f, textvariable=self._export_path, width=46).grid(
            row=5, column=1, sticky="ew")
        ebf = ttk.Frame(f)
        ebf.grid(row=5, column=2, padx=4)
        ttk.Button(ebf, text="Browse…", command=self._browse_export).pack(side="left", padx=2)
        ttk.Button(ebf, text="Export",  command=self._export_qgs).pack(side="left", padx=2)

        ttk.Separator(f, orient="horizontal").grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=10)

        # Change summary
        ttk.Label(f, text="Pending changes", font=("", 10, "bold")).grid(
            row=7, column=0, columnspan=3, sticky="w")
        self._change_text = scrolledtext.ScrolledText(
            f, height=16, font=("Consolas", 9), state="disabled", wrap="none")
        self._change_text.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(4, 0))
        f.rowconfigure(8, weight=1)
        ttk.Button(f, text="↺  Refresh summary",
                   command=self._refresh_summary).grid(
            row=9, column=2, sticky="e", pady=4, padx=4)

    # ── Database connection ───────────────────────────────────────────────────

    def _connect(self) -> None:
        cv = self._cv
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
            self.conn = psycopg2.connect(
                host=cv["host"].get(),
                port=int(cv["port"].get() or 5432),
                dbname=cv["dbname"].get(),
                user=cv["user"].get(),
                password=cv["pass"].get(),
                connect_timeout=10,
            )
            self.conn.autocommit = True
            self._db_schema = cv["schema"].get() or "public"
            self._db_table  = self._table_var.get().strip() or "qgis_projects"

            # Detect whether the content column is named 'metadata' or 'content'
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT column_name
                         FROM information_schema.columns
                        WHERE table_schema = %s
                          AND table_name   = %s
                          AND column_name IN ('metadata', 'content')
                        LIMIT 1""",
                    (self._db_schema, self._db_table),
                )
                row = cur.fetchone()
                self._content_col = row[0] if row else "metadata"

            self._conn_lbl.config(text="● Connected", foreground="green")
            self._status(
                f"Connected to '{cv['dbname'].get()}' on {cv['host'].get()}. "
                f"Content column: '{self._content_col}'."
            )
            self._refresh_projects()
        except Exception as exc:
            messagebox.showerror("Connection failed", str(exc))
            self._conn_lbl.config(text="● Failed", foreground="red")

    # ── Project list ──────────────────────────────────────────────────────────

    def _refresh_projects(self) -> None:
        if not self._need_conn():
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    pgsql.SQL("SELECT name FROM {}.{} ORDER BY name").format(
                        pgsql.Identifier(self._db_schema),
                        pgsql.Identifier(self._db_table),
                    )
                )
                rows = cur.fetchall()
            self._project_lb.delete(0, "end")
            for (name,) in rows:
                self._project_lb.insert("end", name)
            self._status(
                f"{len(rows)} project(s) in "
                f"{self._db_schema}.{self._db_table}."
            )
        except Exception as exc:
            messagebox.showerror("Error listing projects", str(exc))

    def _load_project(self) -> None:
        if not self._need_conn():
            return
        sel = self._project_lb.curselection()
        if not sel:
            messagebox.showwarning("Select a project", "Click a project name first.")
            return
        name = self._project_lb.get(sel[0])
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    pgsql.SQL("SELECT {} FROM {}.{} WHERE name = %s").format(
                        pgsql.Identifier(self._content_col),
                        pgsql.Identifier(self._db_schema),
                        pgsql.Identifier(self._db_table),
                    ),
                    (name,),
                )
                row = cur.fetchone()
            if not row:
                messagebox.showerror("Not found", f"No project named '{name}'.")
                return
            xml_str = row[0]
            if isinstance(xml_str, memoryview):
                xml_str = bytes(xml_str).decode("utf-8")

            self.current_root = ET.fromstring(xml_str)
            self.layers = extract_layers(self.current_root)
            self._loaded_project = name
            self._save_name.set(name)
            self._refresh_tree()
            self.nb.select(1)
            self._status(
                f"Loaded '{name}'  —  {len(self.layers)} layer(s) found."
            )
        except ET.ParseError as exc:
            messagebox.showerror("XML parse error",
                                 f"Could not parse project XML:\n{exc}")
        except Exception as exc:
            messagebox.showerror("Load error", str(exc))

    # ── Layer tree ────────────────────────────────────────────────────────────

    def _layer_row(self, layer: LayerInfo) -> Tuple:
        pg = layer.pg
        if layer.provider.lower() == "postgres":
            host = pg.get("host", "")
            db   = pg.get("dbname", "")
            st   = f"{pg.get('schema', '')}.{pg.get('table', '')}"
            auth = pg.get("authcfg", "") or (
                "user/pass" if (pg.get("user") or pg.get("password")) else "—"
            )
        else:
            host = db = ""
            st   = (layer.new_datasource or "")[:90]
            auth = "—"
        changed = "✎ yes" if layer.modified else ""
        return (layer.name, _provider_label(layer.provider),
                host, db, st, auth, changed, "")

    def _refresh_tree(self) -> None:
        flt = self._filter_var.get().lower()
        self._tree.delete(*self._tree.get_children())
        shown = 0
        for layer in self.layers:
            row = self._layer_row(layer)
            if flt and not any(flt in str(v).lower() for v in row):
                continue
            tags = ("modified",) if layer.modified else ()
            self._tree.insert("", "end", iid=layer.layer_id, values=row, tags=tags)
            shown += 1
        total = len(self.layers)
        self._count_lbl.config(
            text=f"{shown} of {total} layer(s) shown"
            if flt else f"{total} layer(s)"
        )

    def _selected_layers(self) -> List[LayerInfo]:
        ids = set(self._tree.selection())
        return [l for l in self.layers if l.layer_id in ids]

    def _sel_all(self)  -> None: self._tree.selection_set(self._tree.get_children())
    def _sel_none(self) -> None: self._tree.selection_remove(self._tree.get_children())

    def _sort_tree(self, col: str) -> None:
        rows = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        rows.sort(key=lambda x: x[0].lower())
        for i, (_, k) in enumerate(rows):
            self._tree.move(k, "", i)

    # ── Edit actions ──────────────────────────────────────────────────────────

    def _edit_layer(self) -> None:
        sel = self._selected_layers()
        if len(sel) != 1:
            messagebox.showinfo("Select one layer",
                                "Select exactly one layer to edit individually.")
            return
        LayerEditDialog(self, sel[0], self._refresh_tree)

    def _batch_edit(self) -> None:
        sel = self._selected_layers()
        if not sel:
            messagebox.showinfo("No selection", "Select one or more layers first.")
            return
        BatchEditDialog(self, sel, self._refresh_tree)

    def _reset_selected(self) -> None:
        for layer in self._selected_layers():
            layer.new_datasource = layer.raw_datasource
            layer.pg = (parse_pg_uri(layer.raw_datasource)
                        if layer.provider.lower() == "postgres" else {})
            layer.modified = False
        self._refresh_tree()

    def _test_connections(self) -> None:
        pg_layers = [l for l in self.layers if l.provider.lower() == "postgres"]
        if not pg_layers:
            messagebox.showinfo("No PostGIS layers", "No PostGIS layers to test.")
            return

        # Deduplicate connection attempts by (host, port, dbname, user, password)
        cache: Dict[Tuple, bool] = {}
        results: Dict[str, bool] = {}
        for layer in pg_layers:
            pg  = layer.pg
            key = (pg.get("host",""), pg.get("port","5432"),
                   pg.get("dbname",""), pg.get("user",""), pg.get("password",""))
            if key not in cache:
                try:
                    c = psycopg2.connect(
                        host=pg.get("host",""),
                        port=int(pg.get("port") or 5432),
                        dbname=pg.get("dbname",""),
                        user=pg.get("user",""),
                        password=pg.get("password",""),
                        connect_timeout=3,
                    )
                    c.close()
                    cache[key] = True
                except Exception:
                    cache[key] = False
            results[layer.layer_id] = cache[key]

        for layer in pg_layers:
            ok   = results.get(layer.layer_id, False)
            vals = list(self._layer_row(layer))
            vals[7] = "✓ OK" if ok else "✗ Fail"
            tags = (("modified",) if layer.modified else ()) + \
                   (("ok",) if ok else ("fail",))
            if self._tree.exists(layer.layer_id):
                self._tree.item(layer.layer_id, values=tuple(vals), tags=tags)
        self._status("Connection tests complete.")

    # ── Save / export ─────────────────────────────────────────────────────────

    def _updated_xml(self) -> str:
        apply_changes(self.layers)
        return serialise_xml(self.current_root)

    def _refresh_summary(self) -> None:
        modified = [l for l in self.layers if l.modified]
        if not modified:
            text = "No layers have been modified.\n"
        else:
            lines = [f"{len(modified)} layer(s) modified:\n", "=" * 80]
            for layer in modified:
                lines += [
                    f"\nLayer : {layer.name}",
                    f"ID    : {layer.layer_id}",
                    f"  OLD : {layer.raw_datasource}",
                    f"  NEW : {layer.new_datasource}",
                ]
            text = "\n".join(lines)
        self._change_text.config(state="normal")
        self._change_text.delete("1.0", "end")
        self._change_text.insert("end", text)
        self._change_text.config(state="disabled")

    def _save_to_postgis(self) -> None:
        if not self._need_conn():
            return
        if self.current_root is None:
            messagebox.showwarning("No project loaded", "Load a project first.")
            return
        name = self._save_name.get().strip() or self._loaded_project
        if not name:
            messagebox.showwarning("Name required", "Enter a project name to save.")
            return
        try:
            xml_str = self._updated_xml()
            with self.conn.cursor() as cur:
                cur.execute(
                    pgsql.SQL(
                        "INSERT INTO {}.{} (name, {}) VALUES (%s, %s) "
                        "ON CONFLICT (name) DO UPDATE SET {} = EXCLUDED.{}"
                    ).format(
                        pgsql.Identifier(self._db_schema),
                        pgsql.Identifier(self._db_table),
                        pgsql.Identifier(self._content_col),
                        pgsql.Identifier(self._content_col),
                        pgsql.Identifier(self._content_col),
                    ),
                    (name, xml_str),
                )
            self._status(f"Saved as '{name}' in "
                         f"{self._db_schema}.{self._db_table}.")
            messagebox.showinfo("Saved", f"Project saved as '{name}'.")
            self._refresh_projects()
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def _browse_export(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".qgs",
            filetypes=[("QGIS Project", "*.qgs"), ("All files", "*.*")],
        )
        if path:
            self._export_path.set(path)

    def _export_qgs(self) -> None:
        if self.current_root is None:
            messagebox.showwarning("No project", "Load a project first.")
            return
        path = self._export_path.get().strip()
        if not path:
            messagebox.showwarning("No path", "Choose a file path first.")
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._updated_xml())
            self._status(f"Exported to {path}")
            messagebox.showinfo("Exported", f"Exported to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _need_conn(self) -> bool:
        if self.conn is None or self.conn.closed:
            messagebox.showwarning("Not connected",
                                   "Connect to a PostGIS database first.")
            return False
        return True

    def _status(self, msg: str) -> None:
        self._status_var.set(msg)


# ═══════════════════════════════════════════════════════════════════════════════
# Dialog: single-layer editor
# ═══════════════════════════════════════════════════════════════════════════════

class LayerEditDialog(_DialogBase):
    """Edit one layer's datasource URI — structured form for PostGIS,
    raw text editor for all other providers."""

    _PG_FIELDS = [
        ("Host",            "host"),
        ("Port",            "port"),
        ("Database",        "dbname"),
        ("Schema",          "schema"),
        ("Table",           "table"),
        ("Geometry column", "geomcol"),
        ("User",            "user"),
        ("Password",        "password"),
        ("Auth Config ID",  "authcfg"),
        ("SSL mode",        "sslmode"),
        ("SQL filter",      "sql"),
    ]

    def __init__(self, parent: App, layer: LayerInfo,
                 callback: Callable) -> None:
        super().__init__(parent)
        self._layer    = layer
        self._callback = callback
        self.title(f"Edit Layer  —  {layer.name}")
        self.geometry("720x520")
        self.grab_set()
        self._build()

    def _build(self) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        # Structured tab (PostGIS only)
        if self._layer.provider.lower() == "postgres":
            self._pg_vars: Dict[str, tk.StringVar] = {}
            sf = ttk.Frame(nb, padding=12)
            nb.add(sf, text="Connection Parameters")
            sf.columnconfigure(1, weight=1)
            for row, (lbl, key) in enumerate(self._PG_FIELDS):
                ttk.Label(sf, text=lbl + ":").grid(
                    row=row, column=0, sticky="e", padx=(0, 6), pady=2)
                v = tk.StringVar(value=self._layer.pg.get(key, ""))
                self._pg_vars[key] = v
                ttk.Entry(sf, textvariable=v, width=54).grid(
                    row=row, column=1, sticky="ew", pady=2)
            ttk.Label(
                sf,
                text="If Auth Config ID is set, user/password will be "
                     "omitted from the URI automatically.",
                foreground="gray", wraplength=460,
            ).grid(row=len(self._PG_FIELDS), column=1, sticky="w", pady=(8, 0))

        # Raw URI tab
        rf = ttk.Frame(nb, padding=10)
        nb.add(rf, text="Raw Datasource URI")
        ttk.Label(
            rf,
            text="Edit the raw datasource URI directly.  "
                 "For PostGIS layers this syncs back to the structured form on focus-out.",
            foreground="gray", wraplength=560,
        ).pack(anchor="w")
        self._raw = tk.Text(rf, wrap="word", height=10, font=("Consolas", 9))
        self._raw.pack(fill="both", expand=True, pady=4)
        self._raw.insert("end", self._layer.new_datasource)
        self._raw.bind("<FocusOut>", self._sync_raw_to_pg)

        # Buttons
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=8, pady=6)
        ttk.Button(bf, text="Apply & Close", command=self._apply).pack(side="right", padx=4)
        ttk.Button(bf, text="Cancel",        command=self.destroy).pack(side="right")

    def _sync_raw_to_pg(self, _event=None) -> None:
        if self._layer.provider.lower() != "postgres":
            return
        raw = self._raw.get("1.0", "end").strip()
        pg  = parse_pg_uri(raw)
        for key, var in self._pg_vars.items():
            var.set(pg.get(key, ""))

    def _apply(self) -> None:
        if self._layer.provider.lower() == "postgres":
            new_pg = {k: v.get() for k, v in self._pg_vars.items()}
            merged = {**self._layer.pg, **new_pg}
            self._layer.pg = merged
            self._layer.new_datasource = build_pg_uri(merged)
        else:
            self._layer.new_datasource = self._raw.get("1.0", "end").strip()
        self._layer.modified = (
            self._layer.new_datasource != self._layer.raw_datasource
        )
        self._callback()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Dialog: batch editor
# ═══════════════════════════════════════════════════════════════════════════════

class BatchEditDialog(_DialogBase):
    """
    Two operations, both applied when the user clicks 'Apply All':

    1. **PostGIS param override** – overwrite specific URI keys for all
       selected PostGIS layers (blank field = keep current value).
    2. **Find & replace** – text substitution in the raw datasource URI
       of *all* selected layers (any provider type).

    A Preview tab lets you see the diff before committing.
    """

    _PG_FIELDS = [
        ("New Host",           "host"),
        ("New Port",           "port"),
        ("New Database",       "dbname"),
        ("New Schema",         "schema"),
        ("New User",           "user"),
        ("New Password",       "password"),
        ("New Auth Config ID", "authcfg"),
        ("New SSL Mode",       "sslmode"),
    ]

    def __init__(self, parent: App, layers: List[LayerInfo],
                 callback: Callable) -> None:
        super().__init__(parent)
        self._layers   = layers
        self._callback = callback
        pg_n = sum(1 for l in layers if l.provider.lower() == "postgres")
        self.title(
            f"Batch Edit  —  {len(layers)} layer(s) selected, {pg_n} PostGIS"
        )
        self.geometry("680x560")
        self.grab_set()
        self._build(pg_n)

    def _build(self, pg_count: int) -> None:
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)

        # ── PostGIS parameter override ────────────────────────────────────────
        pf = ttk.Frame(nb, padding=12)
        nb.add(pf, text=f"PostGIS Params  ({pg_count} layers)")
        pf.columnconfigure(1, weight=1)
        ttk.Label(
            pf,
            text="Override connection parameters for all selected PostGIS "
                 "layers.  Leave a field blank to keep the current value.",
            wraplength=560, justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._pg_vars: Dict[str, tk.StringVar] = {}
        for row, (lbl, key) in enumerate(self._PG_FIELDS, start=1):
            ttk.Label(pf, text=lbl + ":").grid(
                row=row, column=0, sticky="e", padx=(0, 6), pady=2)
            v = tk.StringVar()
            self._pg_vars[key] = v
            ttk.Entry(pf, textvariable=v, width=48).grid(
                row=row, column=1, sticky="ew", pady=2)
        ttk.Label(
            pf,
            text="Setting Auth Config ID will remove user/password from the URI.",
            foreground="gray", wraplength=500,
        ).grid(row=len(self._PG_FIELDS)+1, column=1, sticky="w", pady=(8, 0))

        # ── Find & replace ────────────────────────────────────────────────────
        ff = ttk.Frame(nb, padding=12)
        nb.add(ff, text="Find & Replace in URI")
        ff.columnconfigure(1, weight=1)
        ttk.Label(
            ff,
            text="Substitute text in the raw datasource URI of ALL selected "
                 "layers (any provider type).  Applied after PostGIS param overrides.",
            wraplength=560, justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self._find_var    = tk.StringVar()
        self._replace_var = tk.StringVar()
        self._regex_var   = tk.BooleanVar(value=False)
        for row, (lbl, var) in enumerate(
            [("Find:", self._find_var), ("Replace with:", self._replace_var)], start=1
        ):
            ttk.Label(ff, text=lbl).grid(row=row, column=0, sticky="e", padx=(0, 6), pady=2)
            ttk.Entry(ff, textvariable=var, width=52).grid(
                row=row, column=1, sticky="ew", pady=2)
        ttk.Checkbutton(
            ff, text="Use regular expressions  (Python re syntax)",
            variable=self._regex_var,
        ).grid(row=3, column=1, sticky="w", pady=(4, 0))

        # ── Preview ───────────────────────────────────────────────────────────
        pv = ttk.Frame(nb, padding=8)
        nb.add(pv, text="Preview")
        ttk.Label(pv, text="Click 'Preview' to see what will change before applying.",
                  foreground="gray").pack(anchor="w")
        self._preview_text = scrolledtext.ScrolledText(
            pv, font=("Consolas", 8), state="disabled", wrap="none")
        self._preview_text.pack(fill="both", expand=True, pady=4)
        ttk.Button(pv, text="↺  Preview changes",
                   command=self._preview).pack(anchor="e")

        # ── Buttons ───────────────────────────────────────────────────────────
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=8, pady=6)
        ttk.Button(bf, text="Apply All Operations",
                   command=self._apply).pack(side="right", padx=4)
        ttk.Button(bf, text="Cancel", command=self.destroy).pack(side="right")

    # ── Core logic shared by preview and apply ────────────────────────────────

    def _compute_new_ds(self, layer: LayerInfo) -> str:
        """Return what the new datasource would be without mutating the layer."""
        new_pg = dict(layer.pg)
        new_ds = layer.new_datasource

        # Apply PostGIS overrides
        if layer.provider.lower() == "postgres":
            for key, var in self._pg_vars.items():
                val = var.get().strip()
                if val:
                    new_pg[key] = val
            if self._pg_vars.get("authcfg", tk.StringVar()).get().strip():
                new_pg.pop("user", None)
                new_pg.pop("password", None)
            new_ds = build_pg_uri(new_pg)

        # Apply find & replace
        find    = self._find_var.get()
        replace = self._replace_var.get()
        if find:
            try:
                if self._regex_var.get():
                    new_ds = re.sub(find, replace, new_ds)
                else:
                    new_ds = new_ds.replace(find, replace)
            except re.error as exc:
                messagebox.showerror("Regex error", str(exc))

        return new_ds

    def _preview(self) -> None:
        lines: List[str] = []
        for layer in self._layers:
            new_ds = self._compute_new_ds(layer)
            if new_ds != layer.new_datasource:
                lines += [
                    f"▶ {layer.name}  [{layer.layer_id}]",
                    f"  OLD: {layer.new_datasource}",
                    f"  NEW: {new_ds}",
                    "",
                ]
        if not lines:
            lines = ["No changes detected with current settings."]
        self._preview_text.config(state="normal")
        self._preview_text.delete("1.0", "end")
        self._preview_text.insert("end", "\n".join(lines))
        self._preview_text.config(state="disabled")

    def _apply(self) -> None:
        for layer in self._layers:
            new_ds = self._compute_new_ds(layer)
            if new_ds != layer.new_datasource:
                layer.new_datasource = new_ds
                # Keep the parsed pg dict in sync
                if layer.provider.lower() == "postgres":
                    for key, var in self._pg_vars.items():
                        val = var.get().strip()
                        if val:
                            layer.pg[key] = val
                    if self._pg_vars.get("authcfg", tk.StringVar()).get().strip():
                        layer.pg.pop("user", None)
                        layer.pg.pop("password", None)
                layer.modified = (new_ds != layer.raw_datasource)
        self._callback()
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not _GUI_AVAILABLE:
        print("ERROR: tkinter is not available. Install the python3-tk package.")
        sys.exit(1)
    if psycopg2 is None:
        print("ERROR: psycopg2 is not installed.\n"
              "Install it with:  pip install psycopg2-binary")
        sys.exit(1)
    App().mainloop()
