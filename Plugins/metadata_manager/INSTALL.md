# Metadata Manager - Installation Guide

## Quick Installation

### Windows

1. **Run the installer**:
   ```cmd
   cd C:\Users\br8kw\Github\mqs\Plugins\metadata_manager
   install.bat
   ```

2. **Restart QGIS** (if running)

3. **Enable the plugin**:
   - Open QGIS
   - Go to `Plugins` → `Manage and Install Plugins`
   - Click `Installed` tab
   - Check the box next to `Metadata Manager`

4. **Launch the plugin**:
   - Click the Metadata Manager toolbar button
   - OR go to `Plugins` → `Metadata Manager` → `MetadataManager`

### Linux / macOS

1. **Run the installer**:
   ```bash
   cd ~/Github/mqs/Plugins/metadata_manager
   ./install.sh
   ```

2. **Restart QGIS** (if running)

3. **Enable the plugin** (same as Windows steps 3-4)

## Manual Installation

If the install scripts don't work, you can manually copy the plugin:

### Step 1: Find Your QGIS Plugin Directory

**Windows:**
```
C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\<profile>\python\plugins\
```

**Linux:**
```
~/.local/share/QGIS/QGIS3/profiles/<profile>/python/plugins/
```

**macOS:**
```
~/Library/Application Support/QGIS/QGIS3/profiles/<profile>/python/plugins/
```

Replace `<profile>` with your profile name (usually `default` or `AdvancedUser`)

### Step 2: Copy Plugin Files

1. Create directory: `metadatamanager` (all lowercase, no underscore)
2. Copy ALL files and folders from `Plugins/metadata_manager/` to the new directory
3. Make sure you copy:
   - All `.py` files
   - `metadata.txt`
   - `db/` directory (with all its contents)
   - `widgets/` directory (with all its contents)
   - `i18n/` directory
   - `help/` directory
   - `icon.png`
   - `*.ui` files
   - `resources.py` and `resources.qrc`

### Step 3: Verify Installation

Your plugin directory should look like:
```
metadatamanager/
├── db/
│   ├── __init__.py
│   ├── manager.py
│   ├── migrations.py
│   └── schema.py
├── widgets/
│   ├── __init__.py
│   └── dashboard_widget.py
├── i18n/
├── help/
├── __init__.py
├── MetadataManager.py
├── MetadataManager_dockwidget.py
├── MetadataManager_dockwidget_base.ui
├── metadata.txt
├── icon.png
├── resources.py
└── resources.qrc
```

**IMPORTANT**: The `db/` and `widgets/` directories are critical! If they're missing, the plugin will fail to load.

## First Use

1. **Prerequisites**:
   - Install and run Inventory Miner script first to create a catalog database
   - See `Scripts/inventory_miner.py`

2. **Launch plugin**:
   - Click toolbar button or menu item
   - You'll be prompted to select an inventory database

3. **Select database**:
   - Browse to your `geospatial_catalog.gpkg` (created by Inventory Miner)
   - Plugin will validate the database
   - Click "Yes" when asked to initialize Metadata Manager tables

4. **View dashboard**:
   - Dashboard appears automatically
   - Shows metadata completion statistics
   - Click tabs to see different drill-down views
   - Click "Refresh Statistics" to update

## Troubleshooting

### "This plugin is broken" error

**Cause**: Old version installed or missing `db`/`widgets` directories

**Fix**:
1. Delete old plugin: `rm -rf <plugin_dir>/metadatamanager`
2. Run `install.bat` or `install.sh` again
3. Restart QGIS

### "Not connected to database" error

**Cause**: No inventory database selected

**Fix**:
1. Run Inventory Miner script first
2. Select the created `.gpkg` file when plugin prompts

### "Invalid Database" error

**Cause**: Selected database was not created by Inventory Miner v0.2.0+

**Fix**:
1. Update Inventory Miner to v0.2.0 or higher
2. Re-run Inventory Miner to recreate database with required fields

### Import errors about `db` or `widgets`

**Cause**: Directories not copied during installation

**Fix**:
1. Check that `db/` and `widgets/` directories exist in plugin folder
2. Re-run installation script
3. Or manually copy these directories

### Plugin doesn't appear in menu

**Cause**: Not enabled in Plugin Manager

**Fix**:
1. `Plugins` → `Manage and Install Plugins`
2. Click `Installed` tab
3. Find `Metadata Manager`
4. Check the box to enable it

## Uninstallation

1. Disable plugin in Plugin Manager
2. Close QGIS
3. Delete plugin directory:
   - Windows: `rmdir /s %APPDATA%\QGIS\QGIS3\profiles\<profile>\python\plugins\metadatamanager`
   - Linux/Mac: `rm -rf ~/.local/share/QGIS/QGIS3/profiles/<profile>/python/plugins/metadatamanager`

## Version Information

- **Current Version**: 0.2.0
- **QGIS Minimum**: 3.40
- **Status**: In Development (Phase 1 & 2 Complete)

## Support

For issues, see: https://github.com/johnzastrow/mqs/issues
