"""
Test script for Dashboard Widget.

This script tests the dashboard widget functionality with a sample database.

Author: John Zastrow
License: MIT
"""

__version__ = "0.2.0"

import sys
import os
import unittest
from pathlib import Path

# Add plugin directory to path
plugin_dir = Path(__file__).parent.parent.parent.parent / 'Plugins' / 'metadata_manager'
sys.path.insert(0, str(plugin_dir))

from db.manager import DatabaseManager


class TestDashboardStatistics(unittest.TestCase):
    """Test dashboard statistics methods."""

    def setUp(self):
        """Set up test database connection."""
        # This requires a real test database created by Inventory Miner
        self.test_db_path = os.environ.get('TEST_INVENTORY_DB')

        if not self.test_db_path or not os.path.exists(self.test_db_path):
            self.skipTest("Test database not available. Set TEST_INVENTORY_DB environment variable.")

        self.db_manager = DatabaseManager()
        self.db_manager.connect(self.test_db_path)

        # Validate and initialize
        is_valid, _ = self.db_manager.validate_inventory_database()
        if not is_valid:
            self.skipTest("Invalid test database")

        if not self.db_manager.check_metadata_manager_tables_exist():
            self.db_manager.initialize_metadata_manager_tables()

    def tearDown(self):
        """Clean up after test."""
        if self.db_manager:
            self.db_manager.disconnect()

    def test_get_inventory_statistics(self):
        """Test getting overall inventory statistics."""
        stats = self.db_manager.get_inventory_statistics()

        self.assertIsNotNone(stats)
        self.assertIn('total', stats)
        self.assertIn('complete', stats)
        self.assertIn('partial', stats)
        self.assertIn('none', stats)

        # Verify counts add up
        total = stats['total']
        sum_of_parts = stats['complete'] + stats['partial'] + stats['none']
        self.assertEqual(total, sum_of_parts,
                        f"Total {total} should equal sum {sum_of_parts}")

        print(f"\nOverall Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Complete: {stats['complete']}")
        print(f"  Partial: {stats['partial']}")
        print(f"  None: {stats['none']}")

    def test_get_statistics_by_directory(self):
        """Test getting statistics by directory."""
        stats = self.db_manager.get_statistics_by_directory()

        self.assertIsNotNone(stats)
        if len(stats) > 0:
            first_stat = stats[0]
            self.assertIn('directory', first_stat)
            self.assertIn('total', first_stat)
            self.assertIn('completion_pct', first_stat)

            print(f"\nDirectory Statistics (top 5):")
            for i, stat in enumerate(stats[:5]):
                print(f"  {stat['directory']}: {stat['total']} total, {stat['completion_pct']:.1f}% complete")

    def test_get_statistics_by_data_type(self):
        """Test getting statistics by data type."""
        stats = self.db_manager.get_statistics_by_data_type()

        self.assertIsNotNone(stats)
        if len(stats) > 0:
            first_stat = stats[0]
            self.assertIn('data_type', first_stat)
            self.assertIn('total', first_stat)

            print(f"\nData Type Statistics:")
            for stat in stats:
                print(f"  {stat['data_type']}: {stat['total']} total, {stat['completion_pct']:.1f}% complete")

    def test_get_statistics_by_file_format(self):
        """Test getting statistics by file format."""
        stats = self.db_manager.get_statistics_by_file_format()

        self.assertIsNotNone(stats)
        if len(stats) > 0:
            first_stat = stats[0]
            self.assertIn('file_format', first_stat)
            self.assertIn('total', first_stat)

            print(f"\nFile Format Statistics:")
            for stat in stats:
                print(f"  {stat['file_format']}: {stat['total']} total, {stat['completion_pct']:.1f}% complete")

    def test_get_statistics_by_crs(self):
        """Test getting statistics by CRS."""
        stats = self.db_manager.get_statistics_by_crs()

        self.assertIsNotNone(stats)
        if len(stats) > 0:
            first_stat = stats[0]
            self.assertIn('crs', first_stat)
            self.assertIn('total', first_stat)

            print(f"\nCRS Statistics (top 5):")
            for i, stat in enumerate(stats[:5]):
                print(f"  {stat['crs']}: {stat['total']} total, {stat['completion_pct']:.1f}% complete")

    def test_get_priority_recommendations(self):
        """Test getting priority recommendations."""
        recommendations = self.db_manager.get_priority_recommendations(limit=5)

        self.assertIsNotNone(recommendations)
        if len(recommendations) > 0:
            first_rec = recommendations[0]
            self.assertIn('recommendation', first_rec)
            self.assertIn('count', first_rec)

            print(f"\nPriority Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec['recommendation']}")


if __name__ == '__main__':
    # Run tests with verbose output
    print("=" * 70)
    print("Testing Dashboard Statistics Methods")
    print("=" * 70)
    print("\nTo run this test, set the TEST_INVENTORY_DB environment variable:")
    print("  export TEST_INVENTORY_DB=/path/to/geospatial_catalog.gpkg")
    print("  python test_dashboard.py")
    print("=" * 70)

    unittest.main(verbosity=2)
