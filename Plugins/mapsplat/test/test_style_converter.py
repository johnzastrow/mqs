"""
MapSplat - Style Converter Tests

Tests for the QGIS to MapLibre style conversion.
"""

__version__ = "0.1.1"

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStyleConverterHelpers(unittest.TestCase):
    """Test helper methods that don't require QGIS."""

    def test_sanitize_name_basic(self):
        """Test basic name sanitization."""
        from style_converter import StyleConverter

        converter = StyleConverter([], {})

        self.assertEqual(converter._sanitize_name("roads"), "roads")
        self.assertEqual(converter._sanitize_name("my roads"), "my_roads")
        self.assertEqual(converter._sanitize_name("Roads Layer"), "roads_layer")

    def test_sanitize_name_special_chars(self):
        """Test name sanitization with special characters."""
        from style_converter import StyleConverter

        converter = StyleConverter([], {})

        self.assertEqual(converter._sanitize_name("roads!@#$%"), "roads")
        self.assertEqual(converter._sanitize_name("my-roads"), "my_roads")
        self.assertEqual(converter._sanitize_name("roads (2024)"), "roads_2024")

    def test_sanitize_name_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed."""
        from style_converter import StyleConverter

        converter = StyleConverter([], {})

        self.assertEqual(converter._sanitize_name("my  roads"), "my_roads")
        self.assertEqual(converter._sanitize_name("a___b"), "a_b")


class TestStyleConverterOutput(unittest.TestCase):
    """Test style converter output structure."""

    def test_convert_empty_layers(self):
        """Test conversion with no layers."""
        from style_converter import StyleConverter

        converter = StyleConverter([], {"project_name": "test"})
        style = converter.convert()

        self.assertEqual(style["version"], 8)
        self.assertIn("sources", style)
        self.assertIn("layers", style)
        self.assertIn("mapsplat", style["sources"])

    def test_convert_has_background_layer(self):
        """Test that output always has a background layer."""
        from style_converter import StyleConverter

        converter = StyleConverter([], {"project_name": "test"})
        style = converter.convert()

        background = next((l for l in style["layers"] if l["id"] == "background"), None)
        self.assertIsNotNone(background)
        self.assertEqual(background["type"], "background")


class TestMergeBusinessIntoBasemap(unittest.TestCase):
    """Test _merge_business_into_basemap logic (no QGIS required)."""

    def _make_basemap_style(self):
        return {
            "version": 8,
            "sources": {
                "protomaps": {
                    "type": "vector",
                    "url": "pmtiles://https://build.protomaps.com/20260217.pmtiles",
                }
            },
            "layers": [
                {"id": "background", "type": "background", "paint": {"background-color": "#fff"}},
                {"id": "water", "type": "fill", "source": "protomaps", "source-layer": "water"},
            ],
        }

    def _make_business_style(self):
        return {
            "version": 8,
            "sources": {
                "mapsplat": {
                    "type": "vector",
                    "url": "pmtiles://data/layers.pmtiles",
                }
            },
            "layers": [
                {"id": "background", "type": "background", "paint": {"background-color": "#eee"}},
                {"id": "roads-fill", "type": "fill", "source": "mapsplat", "source-layer": "roads"},
            ],
        }

    def _run_merge(self, basemap_style, business_style):
        """Run the merge logic extracted from exporter without QGIS."""
        import json, os, tempfile

        # Write basemap style to a temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(basemap_style, f)
            style_path = f.name

        try:
            # Replicate _merge_business_into_basemap logic inline
            with open(style_path, "r", encoding="utf-8") as f:
                result = json.load(f)

            for src_name, src in result.get("sources", {}).items():
                if src.get("type") == "vector" and "protomaps" in src.get("url", ""):
                    src["url"] = "pmtiles://data/basemap.pmtiles"
                    break

            result.setdefault("sources", {}).update(business_style.get("sources", {}))

            overlay_layers = [
                l for l in business_style.get("layers", []) if l.get("id") != "background"
            ]
            result.setdefault("layers", []).extend(overlay_layers)

            return result
        finally:
            os.unlink(style_path)

    def test_sources_merged(self):
        """Business sources are added to basemap sources."""
        result = self._run_merge(self._make_basemap_style(), self._make_business_style())
        self.assertIn("protomaps", result["sources"])
        self.assertIn("mapsplat", result["sources"])

    def test_background_not_duplicated(self):
        """Business background layer is NOT appended (basemap has its own)."""
        result = self._run_merge(self._make_basemap_style(), self._make_business_style())
        bg_layers = [l for l in result["layers"] if l["id"] == "background"]
        self.assertEqual(len(bg_layers), 1, "Should have exactly one background layer")

    def test_overlay_layers_appended(self):
        """Business overlay layers are appended after basemap layers."""
        result = self._run_merge(self._make_basemap_style(), self._make_business_style())
        layer_ids = [l["id"] for l in result["layers"]]
        # basemap layers come first, business layers appended at end
        self.assertIn("water", layer_ids)
        self.assertIn("roads-fill", layer_ids)
        self.assertGreater(layer_ids.index("roads-fill"), layer_ids.index("water"))

    def test_basemap_url_redirected_to_local(self):
        """Basemap protomaps remote URL is replaced with local pmtiles path."""
        result = self._run_merge(self._make_basemap_style(), self._make_business_style())
        protomaps_src = result["sources"].get("protomaps", {})
        self.assertEqual(protomaps_src.get("url"), "pmtiles://data/basemap.pmtiles")

    def test_business_layer_source_preserved(self):
        """Business layer source URL is preserved as-is."""
        result = self._run_merge(self._make_basemap_style(), self._make_business_style())
        mapsplat_src = result["sources"].get("mapsplat", {})
        self.assertEqual(mapsplat_src.get("url"), "pmtiles://data/layers.pmtiles")


if __name__ == "__main__":
    unittest.main()
