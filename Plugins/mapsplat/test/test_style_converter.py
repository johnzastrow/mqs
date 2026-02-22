"""
MapSplat - Style Converter Tests

Tests for the QGIS to MapLibre style conversion.
"""

__version__ = "0.2.0"

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




class TestComputeSpriteLayout(unittest.TestCase):
    """Test atlas layout computation — pure Python, no QGIS required."""

    def _layout(self, sizes):
        from style_converter import StyleConverter
        return StyleConverter([], {})._compute_sprite_layout(sizes)

    def test_empty_input(self):
        manifest, w, h = self._layout({})
        self.assertEqual(manifest, {})
        self.assertEqual(w, 0)
        self.assertEqual(h, 0)

    def test_single_image(self):
        manifest, w, h = self._layout({"icon_a": (32, 32)})
        self.assertEqual(w, 32)
        self.assertEqual(h, 32)
        self.assertEqual(manifest["icon_a"], {
            "x": 0, "y": 0, "width": 32, "height": 32, "pixelRatio": 1
        })

    def test_two_images_placed_side_by_side(self):
        manifest, w, h = self._layout({"a": (32, 32), "b": (16, 16)})
        self.assertEqual(manifest["a"]["x"], 0)
        self.assertEqual(manifest["b"]["x"], 32)
        self.assertEqual(w, 48)
        self.assertEqual(h, 32)  # tallest image height

    def test_manifest_has_required_maplibre_fields(self):
        manifest, _, _ = self._layout({"x": (64, 64)})
        for field in ("x", "y", "width", "height", "pixelRatio"):
            self.assertIn(field, manifest["x"])

    def test_pixel_ratio_is_one(self):
        manifest, _, _ = self._layout({"z": (48, 48)})
        self.assertEqual(manifest["z"]["pixelRatio"], 1)



class TestBuildSymbolLayerForSprite(unittest.TestCase):
    """Test _build_symbol_layer_for_sprite — pure Python, no QGIS required."""

    def _make_converter(self):
        from style_converter import StyleConverter
        c = StyleConverter([], {})
        c._svg_sprite_map = {}
        c._single_file = True
        return c

    def _call(self, sprite_key="my_layer", source_layer="my_layer",
              source_name="mapsplat", layer_id="my_layer", size_px=30.0):
        c = self._make_converter()
        return c._build_symbol_layer_for_sprite(layer_id, sprite_key, source_name, source_layer, size_px)

    def test_layer_type_is_symbol(self):
        result = self._call()
        self.assertEqual(result["type"], "symbol")

    def test_icon_image_matches_sprite_key(self):
        result = self._call(sprite_key="my_layer")
        self.assertEqual(result["layout"]["icon-image"], "my_layer")

    def test_required_maplibre_fields_present(self):
        result = self._call()
        for field in ("id", "type", "source", "source-layer", "layout"):
            self.assertIn(field, result)

    def test_icon_size_is_one(self):
        result = self._call()
        self.assertEqual(result["layout"]["icon-size"], 1.0)

    def test_icon_allow_overlap_true(self):
        result = self._call()
        self.assertTrue(result["layout"]["icon-allow-overlap"])

    def test_source_and_source_layer_set_correctly(self):
        result = self._call(source_name="mapsplat", source_layer="my_layer")
        self.assertEqual(result["source"], "mapsplat")
        self.assertEqual(result["source-layer"], "my_layer")



class TestMultiSpriteBasemapMerge(unittest.TestCase):
    """Test sprite handling in basemap merge — pure Python logic, no QGIS import."""

    def _run_sprite_merge(self, basemap_sprite, business_sprite, overlay_layers=None):
        """Replicate the sprite-handling portion of _merge_business_into_basemap."""
        basemap = (
            {"sources": {}, "layers": [], "sprite": basemap_sprite}
            if basemap_sprite
            else {"sources": {}, "layers": []}
        )
        business = (
            {"sources": {}, "layers": overlay_layers or [], "sprite": business_sprite}
            if business_sprite
            else {"sources": {}, "layers": overlay_layers or []}
        )

        overlay = [l for l in business.get("layers", []) if l.get("id") != "background"]

        b_sprite = business.get("sprite")
        bm_sprite = basemap.get("sprite")

        if b_sprite and bm_sprite:
            if isinstance(bm_sprite, str):
                basemap["sprite"] = [
                    {"id": "default", "url": bm_sprite},
                    {"id": "biz", "url": b_sprite},
                ]
            elif isinstance(bm_sprite, list):
                if not any(e.get("id") == "biz" for e in bm_sprite):
                    bm_sprite.append({"id": "biz", "url": b_sprite})
            for layer in overlay:
                layout = layer.get("layout", {})
                if "icon-image" in layout and not str(layout["icon-image"]).startswith("biz:"):
                    layout["icon-image"] = "biz:" + layout["icon-image"]
        elif b_sprite and not bm_sprite:
            basemap["sprite"] = b_sprite

        return basemap

    def test_no_sprites_no_sprite_key(self):
        result = self._run_sprite_merge(None, None)
        self.assertNotIn("sprite", result)

    def test_only_business_sprite_sets_sprite_directly(self):
        result = self._run_sprite_merge(None, "./sprites")
        self.assertEqual(result["sprite"], "./sprites")

    def test_both_sprites_produces_array(self):
        result = self._run_sprite_merge(
            "https://example.com/basemap/sprites", "./sprites"
        )
        self.assertIsInstance(result["sprite"], list)
        self.assertEqual(len(result["sprite"]), 2)

    def test_multi_sprite_array_has_default_and_biz_ids(self):
        result = self._run_sprite_merge(
            "https://example.com/basemap/sprites", "./sprites"
        )
        ids = {e["id"] for e in result["sprite"]}
        self.assertIn("default", ids)
        self.assertIn("biz", ids)

    def test_multi_sprite_default_url_preserved(self):
        result = self._run_sprite_merge(
            "https://example.com/basemap/sprites", "./sprites"
        )
        default = next(e for e in result["sprite"] if e["id"] == "default")
        self.assertEqual(default["url"], "https://example.com/basemap/sprites")

    def test_icon_image_prefixed_with_biz(self):
        overlay = [{"id": "icon_layer", "type": "symbol",
                    "layout": {"icon-image": "my_icon"}}]
        self._run_sprite_merge(
            "https://example.com/basemap/sprites", "./sprites",
            overlay_layers=overlay,
        )
        # overlay dicts are mutated in-place
        self.assertEqual(overlay[0]["layout"]["icon-image"], "biz:my_icon")

    def test_icon_image_not_double_prefixed(self):
        overlay = [{"id": "icon_layer", "type": "symbol",
                    "layout": {"icon-image": "biz:already_prefixed"}}]
        self._run_sprite_merge(
            "https://example.com/basemap/sprites", "./sprites",
            overlay_layers=overlay,
        )
        self.assertEqual(overlay[0]["layout"]["icon-image"], "biz:already_prefixed")

    def test_basemap_array_sprite_gets_biz_appended(self):
        existing_array = [{"id": "default", "url": "https://example.com/sprites"}]
        result = self._run_sprite_merge(existing_array, "./sprites")
        self.assertEqual(len(result["sprite"]), 2)
        self.assertEqual(result["sprite"][1]["id"], "biz")

    def test_only_basemap_sprite_left_unchanged(self):
        result = self._run_sprite_merge("https://example.com/basemap/sprites", None)
        self.assertEqual(result.get("sprite"), "https://example.com/basemap/sprites")


if __name__ == "__main__":
    unittest.main()
