#!/usr/bin/env python3
"""
Fix incorrect metadata_status in geospatial_inventory.

This script corrects the metadata_status for layers that are marked as 'complete'
but don't actually have metadata in the metadata_cache table.

This bug occurred because update_inventory_metadata_status was matching only on
file_path, which caused all layers in a container file (SQLite, GeoPackage) to
be marked as complete when only one layer had metadata.

Usage:
    python fix_metadata_status.py <path_to_database.gpkg>
"""

__version__ = "0.1.0"

import sqlite3
import sys


def fix_metadata_status(db_path: str):
    """
    Fix incorrect metadata status in the database.

    Args:
        db_path: Path to the GeoPackage database
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Enable extension loading
    conn.enable_load_extension(True)

    # Try to load SpatiaLite extension (needed for geospatial triggers)
    try:
        # Try different possible extension names/paths
        try:
            conn.load_extension('mod_spatialite')
        except:
            try:
                conn.load_extension('libspatialite')
            except:
                try:
                    conn.load_extension('spatialite')
                except:
                    print("Warning: Could not load SpatiaLite extension. Trying anyway...")
    except Exception as e:
        print(f"Warning: Extension loading not available: {e}")

    cursor = conn.cursor()

    try:
        # First, check how many layers are incorrectly marked as complete
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM geospatial_inventory
            WHERE metadata_status = 'complete'
            AND NOT EXISTS (
                SELECT 1 FROM metadata_cache
                WHERE metadata_cache.layer_path = geospatial_inventory.file_path
                AND metadata_cache.layer_name = geospatial_inventory.layer_name
            )
        """)

        incorrect_count = cursor.fetchone()['count']

        if incorrect_count == 0:
            print("✓ No incorrect metadata status found. Database is correct.")
            return

        print(f"Found {incorrect_count} layers incorrectly marked as 'complete'")

        # Get some examples to show the user
        cursor.execute("""
            SELECT file_path, layer_name, metadata_status
            FROM geospatial_inventory
            WHERE metadata_status = 'complete'
            AND NOT EXISTS (
                SELECT 1 FROM metadata_cache
                WHERE metadata_cache.layer_path = geospatial_inventory.file_path
                AND metadata_cache.layer_name = geospatial_inventory.layer_name
            )
            LIMIT 5
        """)

        print("\nExamples of layers that will be fixed:")
        for row in cursor.fetchall():
            print(f"  - {row['file_path']} / {row['layer_name']}")

        # Fix the incorrect status
        cursor.execute("""
            UPDATE geospatial_inventory
            SET metadata_status = 'none',
                metadata_cached = 0,
                metadata_last_updated = datetime('now')
            WHERE metadata_status = 'complete'
            AND NOT EXISTS (
                SELECT 1 FROM metadata_cache
                WHERE metadata_cache.layer_path = geospatial_inventory.file_path
                AND metadata_cache.layer_name = geospatial_inventory.layer_name
            )
        """)

        conn.commit()

        print(f"\n✓ Fixed {cursor.rowcount} layers")

        # Show updated statistics
        cursor.execute("""
            SELECT metadata_status, COUNT(*) as count
            FROM geospatial_inventory
            WHERE retired_datetime IS NULL
            GROUP BY metadata_status
        """)

        print("\nUpdated statistics:")
        for row in cursor.fetchall():
            status = row['metadata_status'] or 'none'
            count = row['count']
            print(f"  {status}: {count}")

    except Exception as e:
        conn.rollback()
        print(f"✗ Error fixing metadata status: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    db_path = sys.argv[1]
    fix_metadata_status(db_path)
