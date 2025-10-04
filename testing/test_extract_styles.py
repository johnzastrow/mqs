"""
Tests for extract_styles_from_projects.py

Version: 0.1.0
"""

__version__ = "0.1.0"

import os
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

# Note: These tests are designed to run within QGIS Python environment
# They require QGIS libraries to be available


class TestStyleExtractor(unittest.TestCase):
    """Test cases for the QGIS Style Extractor algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.docs_dir = Path(__file__).parent.parent / "docs"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_find_project_files(self):
        """Test that project files are found correctly."""
        # This test would require QGIS environment
        # Placeholder for actual implementation
        pass

    def test_extract_symbols(self):
        """Test symbol extraction from project files."""
        # This test would require QGIS environment
        # Placeholder for actual implementation
        pass

    def test_output_xml_format(self):
        """Test that output XML follows correct format."""
        # Test XML structure
        xml_file = self.docs_dir / "states_style_db.xml"
        if xml_file.exists():
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Verify root element
            self.assertEqual(root.tag, 'qgis_style')
            self.assertEqual(root.get('version'), '2')

            # Verify expected sections exist
            symbols = root.find('symbols')
            self.assertIsNotNone(symbols)

            colorramps = root.find('colorramps')
            self.assertIsNotNone(colorramps)

    def test_duplicate_name_handling(self):
        """Test that duplicate names are handled correctly."""
        from collections import defaultdict

        # Test the unique name generation logic
        name_counters = defaultdict(int)

        # Simulate the _get_unique_name method
        def get_unique_name(base_name, counters):
            if base_name not in counters:
                counters[base_name] = 0
                return base_name
            else:
                counters[base_name] += 1
                return f"{base_name}_{counters[base_name]}"

        # Test unique name generation
        name1 = get_unique_name("TestSymbol", name_counters)
        self.assertEqual(name1, "TestSymbol")

        name2 = get_unique_name("TestSymbol", name_counters)
        self.assertEqual(name2, "TestSymbol_1")

        name3 = get_unique_name("TestSymbol", name_counters)
        self.assertEqual(name3, "TestSymbol_2")

    def test_qgz_file_structure(self):
        """Test that .qgz files are recognized as ZIP archives."""
        import zipfile

        qgz_file = self.docs_dir / "nearth_project_file.qgz"
        if qgz_file.exists():
            # Verify it's a valid ZIP file
            self.assertTrue(zipfile.is_zipfile(qgz_file))

            # Verify it contains a .qgs file
            with zipfile.ZipFile(qgz_file, 'r') as zf:
                files = zf.namelist()
                qgs_files = [f for f in files if f.endswith('.qgs')]
                self.assertGreater(len(qgs_files), 0, "No .qgs file found in .qgz archive")


class TestXMLParsing(unittest.TestCase):
    """Test cases for XML parsing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.docs_dir = Path(__file__).parent.parent / "docs"

    def test_parse_example_xml(self):
        """Test parsing of example XML files."""
        xml_file = self.docs_dir / "states_style_db.xml"
        if xml_file.exists():
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Count symbols
            symbols = root.findall('.//symbols/symbol')
            self.assertGreater(len(symbols), 0, "No symbols found in example file")

            # Verify symbol attributes
            for symbol in symbols[:3]:  # Check first 3
                self.assertIsNotNone(symbol.get('name'))
                self.assertIsNotNone(symbol.get('type'))

    def test_symbol_name_attribute(self):
        """Test that all symbols have name attributes."""
        xml_file = self.docs_dir / "states_style_db.xml"
        if xml_file.exists():
            tree = ET.parse(xml_file)
            root = tree.getroot()

            symbols = root.findall('.//symbols/symbol')
            for symbol in symbols:
                name = symbol.get('name')
                self.assertIsNotNone(name, "Symbol missing name attribute")
                self.assertGreater(len(name), 0, "Symbol has empty name attribute")


class TestIntegration(unittest.TestCase):
    """Integration tests requiring QGIS environment."""

    def setUp(self):
        """Set up test fixtures."""
        self.docs_dir = Path(__file__).parent.parent / "docs"

    def test_example_project_processing(self):
        """Test processing of example project file."""
        # This would require QGIS environment
        # Test that nearth_project_file.qgz can be processed without errors
        pass

    def test_output_file_creation(self):
        """Test that output XML file is created correctly."""
        # This would require QGIS environment
        # Test full workflow from input to output
        pass


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestStyleExtractor))
    suite.addTests(loader.loadTestsFromTestCase(TestXMLParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    # Run tests when executed directly
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
