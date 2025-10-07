"""
Test script to fix metadata status using QGIS Python console.

Run this from the QGIS Python console to fix the metadata status in your database.

Usage:
    1. Open QGIS
    2. Open Python Console (Ctrl+Alt+P)
    3. Copy and paste this script
    4. Update the db_path variable to point to your database
    5. Run the script
"""

from db.manager import DatabaseManager

# Update this path to your database
db_path = r"C:\Users\br8kw\Downloads\geo_inv.gpkg"

# Create database manager and connect
db_manager = DatabaseManager()

if db_manager.connect(db_path):
    print(f"Connected to: {db_path}")

    # Fix the incorrect metadata status
    success, message = db_manager.fix_incorrect_metadata_status()

    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")

    # Show updated statistics
    stats = db_manager.get_inventory_statistics()
    if stats:
        print("\nUpdated Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Complete: {stats['complete']}")
        print(f"  Partial: {stats['partial']}")
        print(f"  None: {stats['none']}")

    db_manager.disconnect()
else:
    print(f"Failed to connect to: {db_path}")
