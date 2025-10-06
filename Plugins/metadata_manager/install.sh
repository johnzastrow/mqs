#!/bin/bash
# Installation script for Metadata Manager plugin

echo ""
echo "========================================"
echo "Metadata Manager Plugin Installer"
echo "========================================"
echo ""

PLUGIN_NAME="metadatamanager"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS and set plugin directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    QGIS_PLUGIN_DIR="$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/$PLUGIN_NAME"
else
    # Linux
    QGIS_PLUGIN_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins/$PLUGIN_NAME"
fi

echo "Source: $SOURCE_DIR"
echo "Target: $QGIS_PLUGIN_DIR"
echo ""

# Remove old installation
if [ -d "$QGIS_PLUGIN_DIR" ]; then
    echo "Removing old plugin installation..."
    rm -rf "$QGIS_PLUGIN_DIR"
fi

# Create plugin directory
echo "Creating plugin directory..."
mkdir -p "$QGIS_PLUGIN_DIR"

echo "Copying plugin files..."

# Copy Python files
cp "$SOURCE_DIR"/*.py "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/*.txt "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/*.ui "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/*.qrc "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/*.png "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/*.cfg "$QGIS_PLUGIN_DIR/" 2>/dev/null || true
cp "$SOURCE_DIR"/Makefile "$QGIS_PLUGIN_DIR/" 2>/dev/null || true

# Copy directories
echo "Copying db module..."
cp -r "$SOURCE_DIR/db" "$QGIS_PLUGIN_DIR/"

echo "Copying widgets module..."
cp -r "$SOURCE_DIR/widgets" "$QGIS_PLUGIN_DIR/"

echo "Copying i18n..."
cp -r "$SOURCE_DIR/i18n" "$QGIS_PLUGIN_DIR/"

echo "Copying help..."
cp -r "$SOURCE_DIR/help" "$QGIS_PLUGIN_DIR/"

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "Plugin installed to:"
echo "$QGIS_PLUGIN_DIR"
echo ""
echo "Next steps:"
echo "1. Restart QGIS if it's running"
echo "2. Go to Plugins > Manage and Install Plugins"
echo "3. Enable 'Metadata Manager' in Installed tab"
echo "4. Click the Metadata Manager toolbar button"
echo ""
