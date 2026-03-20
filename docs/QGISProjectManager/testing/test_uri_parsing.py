"""
Unit tests for QGIS PostGIS Project Manager
============================================
Tests the pure-logic functions (no database, no GUI).

Run with:
    python -m pytest docs/QGISProjectManager/testing/test_uri_parsing.py -v
or:
    python docs/QGISProjectManager/testing/test_uri_parsing.py
"""

import sys
import unittest
from pathlib import Path

# Make Scripts/ importable regardless of where pytest is invoked from
_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT / "Scripts"))

from qgis_project_manager import (   # noqa: E402
    LayerInfo,
    build_pg_uri,
    extract_layers,
    parse_pg_uri,
    serialise_xml,
)
import xml.etree.ElementTree as ET


# ─── parse_pg_uri ─────────────────────────────────────────────────────────────

class TestParsePgUri(unittest.TestCase):

    FULL_URI = (
        "dbname='gisdb' host=db.example.com port=5432 "
        "user='gisuser' password='s3cr3t' sslmode=require "
        "authcfg=abc1234 key='gid' estimatedmetadata=true "
        'table="public"."roads" (geom) sql='
    )

    def test_scalar_quoted(self):
        pg = parse_pg_uri(self.FULL_URI)
        self.assertEqual(pg["dbname"],   "gisdb")
        self.assertEqual(pg["user"],     "gisuser")
        self.assertEqual(pg["password"], "s3cr3t")
        self.assertEqual(pg["key"],      "gid")

    def test_scalar_unquoted(self):
        pg = parse_pg_uri(self.FULL_URI)
        self.assertEqual(pg["host"],    "db.example.com")
        self.assertEqual(pg["port"],    "5432")
        self.assertEqual(pg["sslmode"], "require")
        self.assertEqual(pg["authcfg"], "abc1234")

    def test_table_with_schema(self):
        pg = parse_pg_uri(self.FULL_URI)
        self.assertEqual(pg["schema"],  "public")
        self.assertEqual(pg["table"],   "roads")
        self.assertEqual(pg["geomcol"], "geom")

    def test_sql_empty(self):
        pg = parse_pg_uri(self.FULL_URI)
        self.assertEqual(pg["sql"], "")

    def test_sql_with_filter(self):
        uri = 'dbname=\'db\' host=h table="s"."t" (g) sql=active = 1'
        pg = parse_pg_uri(uri)
        self.assertEqual(pg["sql"], "active = 1")

    def test_no_schema(self):
        uri = 'dbname=\'db\' host=h port=5432 table="roads" (geom) sql='
        pg = parse_pg_uri(uri)
        self.assertEqual(pg["schema"],  "")
        self.assertEqual(pg["table"],   "roads")
        self.assertEqual(pg["geomcol"], "geom")

    def test_no_geomcol(self):
        uri = 'dbname=\'db\' host=h table="public"."roads" sql='
        pg = parse_pg_uri(uri)
        self.assertEqual(pg["geomcol"], "")

    def test_missing_keys_return_absent(self):
        pg = parse_pg_uri("dbname='db' host=h port=5432 table=\"s\".\"t\" sql=")
        self.assertNotIn("authcfg", pg)
        self.assertNotIn("user", pg)

    def test_optional_extra_keys(self):
        uri = (
            "dbname='db' host=h port=5432 srid=4326 type=MultiPolygon "
            'table="public"."poly" (geom) sql='
        )
        pg = parse_pg_uri(uri)
        self.assertEqual(pg["srid"], "4326")
        self.assertEqual(pg["type"], "MultiPolygon")


# ─── build_pg_uri ─────────────────────────────────────────────────────────────

class TestBuildPgUri(unittest.TestCase):

    def _roundtrip(self, uri: str) -> dict:
        return parse_pg_uri(build_pg_uri(parse_pg_uri(uri)))

    def test_roundtrip_basic(self):
        uri = (
            "dbname='gisdb' host=localhost port=5432 user='u' password='p' "
            'sslmode=disable key=\'gid\' table="public"."roads" (geom) sql='
        )
        rt = self._roundtrip(uri)
        self.assertEqual(rt["dbname"], "gisdb")
        self.assertEqual(rt["host"],   "localhost")
        self.assertEqual(rt["table"],  "roads")

    def test_authcfg_removes_credentials(self):
        pg = {
            "dbname": "db", "host": "h", "port": "5432",
            "user": "u", "password": "p", "authcfg": "abc1234",
            "schema": "public", "table": "roads", "geomcol": "geom", "sql": "",
        }
        uri = build_pg_uri(pg)
        self.assertIn("authcfg=abc1234", uri)
        self.assertNotIn("user=", uri)
        self.assertNotIn("password=", uri)

    def test_no_authcfg_includes_credentials(self):
        pg = {
            "dbname": "db", "host": "h", "port": "5432",
            "user": "myuser", "password": "mypass",
            "schema": "public", "table": "roads", "geomcol": "geom", "sql": "",
        }
        uri = build_pg_uri(pg)
        self.assertIn("user='myuser'", uri)
        self.assertIn("password='mypass'", uri)

    def test_table_double_quoted(self):
        pg = {"schema": "my schema", "table": "my table",
              "geomcol": "the_geom", "sql": ""}
        uri = build_pg_uri(pg)
        self.assertIn('"my schema"."my table"', uri)

    def test_no_schema(self):
        pg = {"dbname": "db", "host": "h", "schema": "", "table": "roads",
              "geomcol": "geom", "sql": ""}
        uri = build_pg_uri(pg)
        self.assertIn('"roads"', uri)
        self.assertNotIn('"".', uri)


# ─── extract_layers ───────────────────────────────────────────────────────────

SAMPLE_PROJECT_XML = """<?xml version="1.0"?>
<qgis version="3.34.0">
  <projectlayers>
    <maplayer type="vector">
      <id>roads_abc123</id>
      <layername>Roads</layername>
      <provider>postgres</provider>
      <datasource>dbname='gisdb' host=oldhost port=5432 user='u' sslmode=disable table="public"."roads" (geom) sql=</datasource>
    </maplayer>
    <maplayer type="raster">
      <id>imagery_xyz789</id>
      <layername>Aerial Imagery</layername>
      <provider>wms</provider>
      <datasource>crs=EPSG:4326&amp;format=image/png&amp;layers=imagery&amp;url=http://old.wms.example.com/wms</datasource>
    </maplayer>
    <maplayer type="vector">
      <id>no_datasource_111</id>
      <layername>No datasource layer</layername>
      <provider>memory</provider>
    </maplayer>
  </projectlayers>
</qgis>"""


class TestExtractLayers(unittest.TestCase):

    def setUp(self):
        self.root   = ET.fromstring(SAMPLE_PROJECT_XML)
        self.layers = extract_layers(self.root)

    def test_skips_element_without_datasource(self):
        # memory layer has no <datasource>; should be excluded
        ids = [l.layer_id for l in self.layers]
        self.assertNotIn("no_datasource_111", ids)

    def test_finds_all_layers_with_datasource(self):
        self.assertEqual(len(self.layers), 2)

    def test_postgres_layer_parsed(self):
        roads = next(l for l in self.layers if l.layer_id == "roads_abc123")
        self.assertEqual(roads.provider, "postgres")
        self.assertEqual(roads.pg["host"],   "oldhost")
        self.assertEqual(roads.pg["dbname"], "gisdb")
        self.assertEqual(roads.pg["table"],  "roads")

    def test_wms_layer_not_parsed_as_pg(self):
        img = next(l for l in self.layers if l.layer_id == "imagery_xyz789")
        self.assertEqual(img.provider, "wms")
        self.assertEqual(img.pg, {})


class TestApplyAndSerialise(unittest.TestCase):

    def test_modified_layer_written_back(self):
        from qgis_project_manager import apply_changes
        root   = ET.fromstring(SAMPLE_PROJECT_XML)
        layers = extract_layers(root)
        roads  = next(l for l in layers if l.layer_id == "roads_abc123")
        roads.pg["host"]      = "newhost"
        roads.new_datasource  = build_pg_uri(roads.pg)
        roads.modified        = True
        apply_changes(layers)
        # Re-extract from the mutated tree
        updated = extract_layers(root)
        updated_roads = next(l for l in updated if l.layer_id == "roads_abc123")
        self.assertIn("newhost", updated_roads.raw_datasource)

    def test_serialise_includes_declaration(self):
        root = ET.fromstring(SAMPLE_PROJECT_XML)
        xml  = serialise_xml(root)
        self.assertTrue(xml.startswith("<?xml"))


# ─── Runner ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
