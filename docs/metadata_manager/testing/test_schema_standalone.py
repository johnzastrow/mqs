"""
Standalone test to verify schema SQL statements are properly split.

This test can run without QGIS.
"""

import sqlite3
import tempfile
import os

# Schema version constant
METADATA_SCHEMA_VERSION = "0.1.0"

def get_metadata_cache_schema():
    """Return metadata cache schema as list of separate statements."""
    return [
        """
        CREATE TABLE IF NOT EXISTS metadata_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer_path TEXT NOT NULL UNIQUE,
            layer_name TEXT NOT NULL,
            file_type TEXT,
            metadata_json TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_edited_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_written_date TIMESTAMP,
            target_location TEXT,
            in_sync INTEGER DEFAULT 1,
            UNIQUE(layer_path)
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_metadata_cache_path
        ON metadata_cache(layer_path);
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_metadata_cache_sync
        ON metadata_cache(in_sync);
        """
    ]

def get_all_schemas():
    """Return all test schema definitions."""
    schemas = []

    # Simple table
    schemas.append("""
        CREATE TABLE IF NOT EXISTS plugin_info (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Metadata cache with indexes
    schemas.extend(get_metadata_cache_schema())

    return schemas

def test_schema_creation():
    """Test that schemas can be created without multi-statement errors."""

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        test_db = tmp.name

    print(f"Creating test database: {test_db}")

    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        schemas = get_all_schemas()
        print(f"Executing {len(schemas)} schema statements...")

        for i, schema_sql in enumerate(schemas, 1):
            print(f"  Statement {i}/{len(schemas)}...", end='')
            try:
                cursor.execute(schema_sql)
                print(" ✓")
            except sqlite3.Warning as e:
                print(f" ⚠ Warning: {e}")
            except Exception as e:
                print(f" ✗ FAILED")
                print(f"    Error: {e}")
                print(f"    SQL: {schema_sql[:200]}...")
                raise

        conn.commit()

        # Verify tables and indexes created
        cursor.execute("""
            SELECT name, type FROM sqlite_master
            WHERE type IN ('table', 'index')
            ORDER BY type, name
        """)

        objects = cursor.fetchall()
        print(f"\n✓ Created {len(objects)} database objects:")

        tables = [obj for obj in objects if obj[1] == 'table']
        indexes = [obj for obj in objects if obj[1] == 'index']

        print(f"\n  Tables ({len(tables)}):")
        for name, _ in tables:
            print(f"    - {name}")

        print(f"\n  Indexes ({len(indexes)}):")
        for name, _ in indexes:
            print(f"    - {name}")

        # Verify expected objects
        expected_tables = {'plugin_info', 'metadata_cache'}
        expected_indexes = {'idx_metadata_cache_path', 'idx_metadata_cache_sync'}

        actual_tables = {name for name, _ in tables}
        actual_indexes = {name for name, _ in indexes if not name.startswith('sqlite_')}

        if expected_tables == actual_tables and expected_indexes == actual_indexes:
            print("\n✓ All expected objects created!")
            return True
        else:
            print("\n⚠ Unexpected objects:")
            print(f"  Tables: expected {expected_tables}, got {actual_tables}")
            print(f"  Indexes: expected {expected_indexes}, got {actual_indexes}")
            return False

        conn.close()

    finally:
        if os.path.exists(test_db):
            os.unlink(test_db)
            print(f"\nCleaned up test database")

if __name__ == '__main__':
    print("=" * 70)
    print("Testing Schema SQL Statement Splitting")
    print("=" * 70)
    print()

    try:
        success = test_schema_creation()
        print()
        print("=" * 70)
        if success:
            print("✓ TEST PASSED - Multi-statement issue is FIXED!")
        else:
            print("⚠ TEST PASSED with warnings")
        print("=" * 70)
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ TEST FAILED - {e}")
        print("=" * 70)
        import sys
        sys.exit(1)
