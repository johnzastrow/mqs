"""
Quick test to verify schema creation works without multi-statement errors.

Run this to test if the schema fix resolves the SQLite error.
"""

import sys
import os
import sqlite3
import tempfile
from pathlib import Path

# Add plugin directory to path
plugin_dir = Path(__file__).parent.parent.parent.parent / 'Plugins' / 'metadata_manager'
sys.path.insert(0, str(plugin_dir))

from db.schema import DatabaseSchema

def test_schema_creation():
    """Test that all schemas can be created without errors."""

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.gpkg', delete=False) as tmp:
        test_db = tmp.name

    print(f"Creating test database: {test_db}")

    try:
        # Connect to database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # Get all schemas
        schemas = DatabaseSchema.get_all_schemas()
        print(f"Found {len(schemas)} schema statements to execute")

        # Execute each schema
        for i, schema_sql in enumerate(schemas, 1):
            print(f"  Executing schema {i}/{len(schemas)}...", end='')
            try:
                cursor.execute(schema_sql)
                print(" ✓")
            except Exception as e:
                print(f" ✗ FAILED")
                print(f"    Error: {e}")
                print(f"    SQL: {schema_sql[:100]}...")
                raise

        # Get initial data
        initial_data = DatabaseSchema.get_initial_data()
        print(f"\nInserting {len(initial_data)} initial data statements")

        for i, data_sql in enumerate(initial_data, 1):
            print(f"  Executing insert {i}/{len(initial_data)}...", end='')
            try:
                cursor.execute(data_sql)
                print(" ✓")
            except Exception as e:
                print(f" ✗ FAILED")
                print(f"    Error: {e}")
                raise

        conn.commit()

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"\n✓ Success! Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Expected tables
        expected_tables = [
            'contacts',
            'keyword_set_members',
            'keyword_sets',
            'keywords',
            'metadata_cache',
            'organizations',
            'plugin_info',
            'settings',
            'templates',
            'upgrade_history'
        ]

        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n⚠ WARNING: Missing tables: {missing}")
        else:
            print(f"\n✓ All expected tables created successfully!")

        conn.close()

    finally:
        # Clean up
        if os.path.exists(test_db):
            os.unlink(test_db)
            print(f"\nCleaned up test database")

if __name__ == '__main__':
    print("=" * 70)
    print("Testing Schema Creation (SQLite Multi-Statement Fix)")
    print("=" * 70)
    print()

    try:
        test_schema_creation()
        print()
        print("=" * 70)
        print("✓ TEST PASSED - Schema creation works correctly!")
        print("=" * 70)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ TEST FAILED - {e}")
        print("=" * 70)
        sys.exit(1)
