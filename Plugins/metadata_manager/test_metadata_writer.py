"""
Test script for metadata writing functionality.

This script tests writing metadata to both .qmd files and GeoPackage layers.

Run this from the QGIS Python console.
"""

from db.metadata_writer import MetadataWriter

# Sample metadata dictionary
sample_metadata = {
    'title': 'Test Layer',
    'abstract': 'This is a test layer for metadata writing',
    'keywords': ['test', 'sample', 'demo'],
    'type': 'dataset',
    'language': 'en',
    'categories': ['geoscientificInformation'],
    'contacts': [
        {
            'name': 'Test User',
            'organization': 'Test Organization',
            'position': 'Data Manager',
            'email': 'test@example.com',
            'role': 'author'
        }
    ],
    'rights': ['Copyright 2025 Test Organization'],
    'licenses': ['MIT License'],
}

# Initialize writer
writer = MetadataWriter()

print("=" * 60)
print("Metadata Writer Test")
print("=" * 60)

# Test 1: Write to .qmd file for a shapefile
print("\n1. Testing .qmd file write (Shapefile)...")
shapefile_path = r"C:\test\data\roads.shp"
layer_name = "roads"
success, target, message = writer.write_metadata(
    shapefile_path,
    layer_name,
    sample_metadata,
    file_format="ESRI Shapefile"
)

if success:
    print(f"   ✓ Success: {target}")
else:
    print(f"   ✗ Failed: {message}")

# Test 2: Write to GeoPackage layer
print("\n2. Testing GeoPackage write...")
gpkg_path = r"C:\test\data\test.gpkg"
gpkg_layer = "test_layer"
success, target, message = writer.write_metadata(
    gpkg_path,
    gpkg_layer,
    sample_metadata,
    file_format="GPKG"
)

if success:
    print(f"   ✓ Success: {target}")
else:
    print(f"   ✗ Failed: {message}")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nNote: The paths above are examples. Update them to match")
print("actual files on your system before running this test.")
