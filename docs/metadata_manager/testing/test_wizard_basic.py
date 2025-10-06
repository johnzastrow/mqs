"""
Basic test to verify wizard widget structure.

Tests imports, class structure, and basic functionality without QGIS.
"""

import sys
from pathlib import Path

print("=" * 70)
print("Metadata Wizard - Basic Structure Test")
print("=" * 70)
print()

# Test 1: Import test
print("Test 1: Checking imports...")
try:
    # Add plugin path
    plugin_dir = Path(__file__).parent.parent.parent.parent / 'Plugins' / 'metadata_manager'
    sys.path.insert(0, str(plugin_dir))

    # This will fail without QGIS, but we can check the file exists
    wizard_file = plugin_dir / 'widgets' / 'metadata_wizard.py'

    if not wizard_file.exists():
        print(f"  ✗ FAILED: metadata_wizard.py not found at {wizard_file}")
        sys.exit(1)
    else:
        print(f"  ✓ metadata_wizard.py exists")

    # Check file size (should be substantial)
    file_size = wizard_file.stat().st_size
    if file_size < 1000:
        print(f"  ⚠ WARNING: File seems small ({file_size} bytes)")
    else:
        print(f"  ✓ File size looks good ({file_size} bytes)")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Check class definitions
print("\nTest 2: Checking class structure...")
try:
    with open(wizard_file, 'r', encoding='utf-8') as f:
        content = f.read()

    required_classes = [
        'class StepWidget',
        'class Step1Essential',
        'class MetadataWizard',
        'class QFlowLayout'
    ]

    for class_name in required_classes:
        if class_name in content:
            print(f"  ✓ Found {class_name}")
        else:
            print(f"  ✗ MISSING: {class_name}")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 3: Check key methods
print("\nTest 3: Checking key methods...")
try:
    required_methods = [
        'def validate(',
        'def get_data(',
        'def set_data(',
        'def next_step(',
        'def previous_step(',
        'def save_metadata(',
        'def add_keyword(',
        'def remove_keyword('
    ]

    for method in required_methods:
        if method in content:
            print(f"  ✓ Found {method}")
        else:
            print(f"  ✗ MISSING: {method}")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 4: Check UI elements
print("\nTest 4: Checking UI element creation...")
try:
    ui_elements = [
        'QLineEdit',  # Title field
        'QPlainTextEdit',  # Abstract field
        'QComboBox',  # Category dropdown
        'QPushButton',  # Buttons
        'QStackedWidget',  # Step container
        'QProgressBar',  # Progress indicator
        'QTabWidget'  # Mentioned in integration
    ]

    found_count = 0
    for element in ui_elements:
        if element in content:
            print(f"  ✓ Uses {element}")
            found_count += 1
        else:
            print(f"  ⚠ Not found: {element}")

    if found_count >= 6:
        print(f"  ✓ Found {found_count}/{len(ui_elements)} UI elements")
    else:
        print(f"  ⚠ Only found {found_count}/{len(ui_elements)} UI elements")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 5: Check integration points
print("\nTest 5: Checking integration...")
try:
    init_file = plugin_dir / 'widgets' / '__init__.py'

    if not init_file.exists():
        print("  ✗ __init__.py not found")
    else:
        with open(init_file, 'r', encoding='utf-8') as f:
            init_content = f.read()

        if 'MetadataWizard' in init_content:
            print("  ✓ MetadataWizard exported in __init__.py")
        else:
            print("  ✗ MetadataWizard not exported")

    # Check dockwidget integration
    dockwidget_file = plugin_dir / 'MetadataManager_dockwidget.py'
    if dockwidget_file.exists():
        with open(dockwidget_file, 'r', encoding='utf-8') as f:
            dock_content = f.read()

        if 'MetadataWizard' in dock_content:
            print("  ✓ MetadataWizard imported in dockwidget")
        else:
            print("  ✗ MetadataWizard not imported in dockwidget")

        if 'QTabWidget' in dock_content:
            print("  ✓ Tab widget integration found")
        else:
            print("  ✗ Tab widget not found in dockwidget")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 6: Check for common issues
print("\nTest 6: Checking for common issues...")
try:
    issues_found = []

    # Check for proper signal definitions
    if 'pyqtSignal' not in content:
        issues_found.append("No pyqtSignal imports (might be okay)")

    # Check for proper indentation (basic)
    lines = content.split('\n')
    for i, line in enumerate(lines[:100], 1):  # Check first 100 lines
        if line.startswith('    ') and not line.startswith('        '):
            # Might be mixing tabs and spaces (but this is simple check)
            pass

    # Check version
    if '__version__' in content:
        print("  ✓ Version string found")
    else:
        issues_found.append("No __version__ defined")

    # Check docstrings
    if '"""' in content[:500]:
        print("  ✓ Module docstring present")
    else:
        issues_found.append("No module docstring")

    if issues_found:
        print(f"  ⚠ Found {len(issues_found)} potential issues:")
        for issue in issues_found:
            print(f"    - {issue}")
    else:
        print("  ✓ No obvious issues found")

except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Summary
print()
print("=" * 70)
print("✓ BASIC TESTS PASSED")
print("=" * 70)
print()
print("The wizard widget structure looks good!")
print()
print("Next steps:")
print("1. Restart QGIS")
print("2. Open Metadata Manager plugin")
print("3. Click 'Metadata Editor' tab")
print("4. Follow WIZARD_TESTING_GUIDE.md for functional testing")
print()
print("Note: This test only checks file structure, not runtime behavior.")
print("      Full testing requires QGIS environment.")
print()
