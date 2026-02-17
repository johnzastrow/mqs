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


if __name__ == "__main__":
    unittest.main()
