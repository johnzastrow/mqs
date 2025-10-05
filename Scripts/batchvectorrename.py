"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Batch Vector Layer Rename Tool

Recursively scans directories for vector files and batch rename layers that support renaming.
Supports GeoPackage, SpatiaLite, Shapefiles, and container formats with comprehensive
logging and error handling.

Version: 0.2.0
"""

__version__ = "0.2.0"

import os
import re
import sqlite3
import shutil
import logging
from pathlib import Path
from typing import Any, Optional, List, Dict, Tuple, Union

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterString,
    QgsProcessingParameterNumber,
    QgsVectorLayer,
    QgsDataSourceUri,
    QgsProviderRegistry,
    QgsMessageLog,
    Qgis,
)


class BatchVectorRenameAlgorithm(QgsProcessingAlgorithm):
    """
    Recursively scan directories and batch rename layers in vector files and databases.
    """

    # Parameter constants
    INPUT_DIR = "INPUT_DIR"
    VECTOR_TYPES = "VECTOR_TYPES"
    RENAME_OPERATION = "RENAME_OPERATION"
    FIND_TEXT = "FIND_TEXT"
    REPLACE_TEXT = "REPLACE_TEXT"
    TRIM_POSITION = "TRIM_POSITION"
    TRIM_COUNT = "TRIM_COUNT"
    CUSTOM_PREFIX = "CUSTOM_PREFIX"
    CUSTOM_SUFFIX = "CUSTOM_SUFFIX"
    DRY_RUN = "DRY_RUN"
    BACKUP_FILES = "BACKUP_FILES"

    def createInstance(self):
        return BatchVectorRenameAlgorithm()

    def name(self):
        return "batchvectorrename"

    def displayName(self):
        return "Batch Vector Layer Rename (Recursive)"

    def group(self):
        return "MQS Tools"

    def groupId(self):
        return "mqs_tools"

    def shortHelpString(self):
        return """
        <p>Recursively scan directories for vector files and batch rename layers that support renaming.</p>

        <h3>Supported Formats:</h3>
        <ul>
        <li><b>GeoPackage (.gpkg):</b> Full layer renaming support via SQL</li>
        <li><b>SpatiaLite (.sqlite/.db):</b> Full layer renaming support via SQL</li>
        <li><b>Shapefiles (.shp):</b> Rename by renaming all component files</li>
        <li><b>File Geodatabase (.gdb):</b> Limited support (read-only in most cases)</li>
        <li><b>GeoJSON (.geojson/.json):</b> File renaming only</li>
        <li><b>KML/KMZ (.kml/.kmz):</b> File renaming only</li>
        <li><b>GPX (.gpx):</b> File renaming only</li>
        <li><b>GML (.gml):</b> File renaming only</li>
        <li><b>MapInfo (.tab/.mif):</b> File renaming only</li>
        </ul>

        <h3>Rename Operations:</h3>
        <ul>
        <li><b>Replace Text:</b> Find and replace text in layer/file names (can remove text by replacing with empty string)</li>
        <li><b>Trim Beginning:</b> Remove specified number of characters from the start of names</li>
        <li><b>Trim End:</b> Remove specified number of characters from the end of names</li>
        <li><b>Add Prefix:</b> Add text to the beginning of layer/file names</li>
        <li><b>Add Suffix:</b> Add text to the end of layer/file names</li>
        <li><b>Clean Names:</b> Remove invalid characters and standardize naming</li>
        <li><b>Convert to Lowercase:</b> Convert all names to lowercase</li>
        <li><b>Convert to Uppercase:</b> Convert all names to uppercase</li>
        <li><b>Convert to Title Case:</b> Convert names to Title Case</li>
        </ul>

        <h3>Parameters:</h3>
        <ul>
        <li><b>Input Directory:</b> Top-level directory to scan recursively</li>
        <li><b>Vector File Types:</b> Select which vector file types to process</li>
        <li><b>Rename Operation:</b> Choose the type of rename operation</li>
        <li><b>Find/Replace Text:</b> Text to find and replace (for Replace operation)</li>
        <li><b>Trim Position/Count:</b> Position and number of characters to trim</li>
        <li><b>Custom Prefix/Suffix:</b> Text to add (for prefix/suffix operations)</li>
        <li><b>Dry Run:</b> Preview changes without applying them</li>
        <li><b>Create Backups:</b> Create backup copies before making changes</li>
        </ul>

        <h3>Safety Features:</h3>
        <ul>
        <li><b>Dry Run Mode:</b> Preview all changes before applying them</li>
        <li><b>Automatic Backup:</b> Optional backup creation before renaming</li>
        <li><b>Comprehensive Logging:</b> Detailed operation and error logging</li>
        <li><b>Validation:</b> Check for naming conflicts and invalid characters</li>
        <li><b>Rollback Support:</b> Ability to restore from backups if needed</li>
        </ul>
        """

    def initAlgorithm(self, config=None):
        """Initialize the algorithm parameters."""

        # Input directory parameter
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DIR,
                "Input directory to scan recursively",
                behavior=QgsProcessingParameterFile.Folder
            )
        )

        # Vector file types parameter (multi-select)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VECTOR_TYPES,
                "Vector file types to process",
                options=[
                    "GeoPackage files (.gpkg)",
                    "SpatiaLite files (.sqlite/.db)",
                    "Shapefiles (.shp)",
                    "GeoJSON files (.geojson/.json)",
                    "KML/KMZ files (.kml/.kmz)",
                    "GPX files (.gpx)",
                    "GML files (.gml)",
                    "MapInfo files (.tab/.mif)",
                    "File Geodatabase (.gdb)"
                ],
                allowMultiple=True,
                defaultValue=list(range(9))  # All types selected by default
            )
        )

        # Rename operation parameter
        self.addParameter(
            QgsProcessingParameterEnum(
                self.RENAME_OPERATION,
                "Rename operation",
                options=[
                    "Replace text (find and replace)",
                    "Trim beginning (remove N characters from start)",
                    "Trim end (remove N characters from end)",
                    "Add prefix",
                    "Add suffix",
                    "Clean names (remove invalid characters)",
                    "Convert to lowercase",
                    "Convert to uppercase",
                    "Convert to Title Case"
                ],
                defaultValue=0
            )
        )

        # Find text parameter
        self.addParameter(
            QgsProcessingParameterString(
                self.FIND_TEXT,
                "Text to find (for 'Replace text' operation)",
                defaultValue="",
                optional=True
            )
        )

        # Replace text parameter
        self.addParameter(
            QgsProcessingParameterString(
                self.REPLACE_TEXT,
                "Text to replace with (for 'Replace text' operation - leave empty to remove text)",
                defaultValue="",
                optional=True
            )
        )

        # Trim position parameter
        self.addParameter(
            QgsProcessingParameterEnum(
                self.TRIM_POSITION,
                "Trim position (for trim operations)",
                options=[
                    "Beginning",
                    "End"
                ],
                defaultValue=0
            )
        )

        # Trim count parameter
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TRIM_COUNT,
                "Number of characters to trim (for trim operations)",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=1,
                maxValue=50
            )
        )

        # Custom prefix parameter
        self.addParameter(
            QgsProcessingParameterString(
                self.CUSTOM_PREFIX,
                "Custom prefix (for 'Add prefix' operation)",
                defaultValue="",
                optional=True
            )
        )

        # Custom suffix parameter
        self.addParameter(
            QgsProcessingParameterString(
                self.CUSTOM_SUFFIX,
                "Custom suffix (for 'Add suffix' operation)",
                defaultValue="",
                optional=True
            )
        )

        # Dry run parameter
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.DRY_RUN,
                "Dry run (preview changes without applying them)",
                defaultValue=True
            )
        )

        # Backup parameter
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BACKUP_FILES,
                "Create backup copies before renaming",
                defaultValue=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Main processing method."""

        # Setup logging
        self._setup_logging(feedback)

        # Extract parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIR, context)
        vector_types = self.parameterAsEnums(parameters, self.VECTOR_TYPES, context)
        rename_operation = self.parameterAsEnum(parameters, self.RENAME_OPERATION, context)
        find_text = self.parameterAsString(parameters, self.FIND_TEXT, context)
        replace_text = self.parameterAsString(parameters, self.REPLACE_TEXT, context)
        trim_position = self.parameterAsEnum(parameters, self.TRIM_POSITION, context)
        trim_count = self.parameterAsInt(parameters, self.TRIM_COUNT, context)
        custom_prefix = self.parameterAsString(parameters, self.CUSTOM_PREFIX, context)
        custom_suffix = self.parameterAsString(parameters, self.CUSTOM_SUFFIX, context)
        dry_run = self.parameterAsBool(parameters, self.DRY_RUN, context)
        backup_files = self.parameterAsBool(parameters, self.BACKUP_FILES, context)

        if not input_dir:
            raise QgsProcessingException("Input directory is required")

        input_path = Path(input_dir)
        if not input_path.exists():
            raise QgsProcessingException(f"Input directory does not exist: {input_dir}")

        self._log_info(f"Starting batch vector rename operation on directory: {input_dir}")
        feedback.pushInfo(f"Scanning directory recursively: {input_dir}")

        # Validate operation-specific parameters
        self._validate_parameters(rename_operation, find_text, custom_prefix, custom_suffix, feedback)

        # Find all vector files
        vector_files = self._find_vector_files(input_path, vector_types, feedback)

        if not vector_files:
            feedback.pushInfo("No vector files found matching the selected types.")
            return {}

        feedback.pushInfo(f"Found {len(vector_files)} vector files to process")

        # Process each file and collect layers
        all_layers = []
        for vector_file in vector_files:
            try:
                file_layers = self._process_vector_file(vector_file, feedback)
                all_layers.extend(file_layers)
            except Exception as e:
                self._log_error(f"Error processing file {vector_file}: {str(e)}")
                feedback.pushInfo(f"Warning: Could not process {vector_file}: {str(e)}")

        if not all_layers:
            feedback.pushInfo("No renameable layers found in the selected files.")
            return {}

        feedback.pushInfo(f"Found {len(all_layers)} renameable layers across all files")

        # Generate rename plan
        rename_plan = self._generate_rename_plan(
            all_layers, rename_operation, find_text, replace_text,
            trim_position, trim_count, custom_prefix, custom_suffix, feedback
        )

        # Display rename plan
        self._display_rename_plan(rename_plan, feedback)

        if dry_run:
            feedback.pushInfo("\nDry run mode - no changes were applied.")
            feedback.pushInfo("Set 'Dry run' to False to apply these changes.")
            return {}

        # Apply renames
        success_count = 0
        error_count = 0

        for layer_info in rename_plan:
            try:
                if backup_files:
                    self._create_backup_for_layer(layer_info, feedback)

                self._apply_layer_rename(layer_info, feedback)
                success_count += 1
            except Exception as e:
                error_count += 1
                self._log_error(f"Error renaming layer {layer_info.get('old_name', 'unknown')}: {str(e)}")
                feedback.pushInfo(f"Error: Failed to rename layer {layer_info.get('old_name', 'unknown')}: {str(e)}")

        feedback.pushInfo(f"\nRename operation completed!")
        feedback.pushInfo(f"Successfully renamed: {success_count} layers")
        if error_count > 0:
            feedback.pushInfo(f"Errors encountered: {error_count} layers")
            feedback.pushInfo("Check the QGIS log for detailed error information.")

        return {}

    def _setup_logging(self, feedback):
        """Setup comprehensive logging."""
        self.feedback = feedback

    def _log_info(self, message: str):
        """Log info message."""
        QgsMessageLog.logMessage(message, "BatchVectorRename", Qgis.Info)

    def _log_warning(self, message: str):
        """Log warning message."""
        QgsMessageLog.logMessage(message, "BatchVectorRename", Qgis.Warning)

    def _log_error(self, message: str):
        """Log error message."""
        QgsMessageLog.logMessage(message, "BatchVectorRename", Qgis.Critical)

    def _validate_parameters(self, operation: int, find_text: str, prefix: str, suffix: str, feedback):
        """Validate operation-specific parameters."""
        if operation == 0 and not find_text.strip():  # Replace text
            raise QgsProcessingException("Find text is required for 'Replace text' operation")
        elif operation == 3 and not prefix.strip():  # Add prefix
            raise QgsProcessingException("Custom prefix is required for 'Add prefix' operation")
        elif operation == 4 and not suffix.strip():  # Add suffix
            raise QgsProcessingException("Custom suffix is required for 'Add suffix' operation")

    def _find_vector_files(self, input_dir: Path, vector_types: List[int], feedback) -> List[Path]:
        """Find all vector files in the directory tree based on selected types."""

        # Define file patterns based on selected types
        type_patterns = {
            0: ["*.gpkg"],                           # GeoPackage
            1: ["*.sqlite", "*.db"],                 # SpatiaLite
            2: ["*.shp"],                            # Shapefiles
            3: ["*.geojson", "*.json"],              # GeoJSON
            4: ["*.kml", "*.kmz"],                   # KML/KMZ
            5: ["*.gpx"],                            # GPX
            6: ["*.gml"],                            # GML
            7: ["*.tab", "*.mif"],                   # MapInfo
            8: ["*.gdb"]                             # File Geodatabase (directories)
        }

        patterns = []
        for vector_type in vector_types:
            if vector_type in type_patterns:
                patterns.extend(type_patterns[vector_type])

        if not patterns:
            return []

        vector_files = []
        total_patterns = len(patterns)

        for i, pattern in enumerate(patterns):
            feedback.setProgress(int((i / total_patterns) * 50))  # Use first 50% for file discovery

            self._log_info(f"Searching for pattern: {pattern}")

            if pattern == "*.gdb":
                # Special handling for .gdb directories
                for path in input_dir.rglob("*.gdb"):
                    if path.is_dir():
                        vector_files.append(path)
                        self._log_info(f"Found .gdb directory: {path}")
            else:
                # Regular file pattern matching
                for path in input_dir.rglob(pattern):
                    if path.is_file():
                        vector_files.append(path)
                        self._log_info(f"Found vector file: {path}")

        # Remove duplicates and sort
        vector_files = list(set(vector_files))
        vector_files.sort()

        feedback.pushInfo(f"File discovery complete. Found {len(vector_files)} files.")
        return vector_files

    def _process_vector_file(self, file_path: Path, feedback) -> List[Dict]:
        """Process a vector file and extract layer information."""

        suffix = file_path.suffix.lower()
        layers = []

        try:
            if suffix == '.gpkg':
                layers = self._process_geopackage(file_path, feedback)
            elif suffix in ['.sqlite', '.db']:
                layers = self._process_spatialite(file_path, feedback)
            elif suffix == '.shp':
                layers = self._process_shapefile(file_path, feedback)
            elif suffix in ['.geojson', '.json', '.kml', '.kmz', '.gpx', '.gml']:
                layers = self._process_single_layer_file(file_path, feedback)
            elif suffix in ['.tab', '.mif']:
                layers = self._process_mapinfo_file(file_path, feedback)
            elif file_path.is_dir() and suffix == '.gdb':
                layers = self._process_geodatabase(file_path, feedback)
            else:
                self._log_warning(f"Unsupported file type: {file_path}")

        except Exception as e:
            self._log_error(f"Error processing {file_path}: {str(e)}")
            raise

        return layers

    def _process_geopackage(self, gpkg_path: Path, feedback) -> List[Dict]:
        """Process GeoPackage and extract layer information."""
        layers = []

        try:
            conn = sqlite3.connect(str(gpkg_path))
            cursor = conn.execute("""
                SELECT table_name FROM gpkg_contents
                WHERE data_type IN ('features', 'tiles')
                ORDER BY table_name
            """)

            for row in cursor.fetchall():
                layer_name = row[0]
                layers.append({
                    'file_path': gpkg_path,
                    'file_type': 'GeoPackage',
                    'layer_name': layer_name,
                    'old_name': layer_name,
                    'renameable': True,
                    'rename_method': 'database'
                })

            conn.close()
            self._log_info(f"Found {len(layers)} layers in GeoPackage: {gpkg_path}")

        except Exception as e:
            self._log_error(f"Error reading GeoPackage {gpkg_path}: {str(e)}")
            raise

        return layers

    def _process_spatialite(self, db_path: Path, feedback) -> List[Dict]:
        """Process SpatiaLite database and extract layer information."""
        layers = []

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'spatial_%' AND name NOT LIKE 'geometry_columns%'
                AND name NOT LIKE 'views_%' AND name NOT LIKE 'virts_%'
                ORDER BY name
            """)

            for row in cursor.fetchall():
                layer_name = row[0]
                layers.append({
                    'file_path': db_path,
                    'file_type': 'SpatiaLite',
                    'layer_name': layer_name,
                    'old_name': layer_name,
                    'renameable': True,
                    'rename_method': 'database'
                })

            conn.close()
            self._log_info(f"Found {len(layers)} layers in SpatiaLite: {db_path}")

        except Exception as e:
            self._log_error(f"Error reading SpatiaLite {db_path}: {str(e)}")
            raise

        return layers

    def _process_shapefile(self, shp_path: Path, feedback) -> List[Dict]:
        """Process Shapefile and extract layer information."""
        layer_name = shp_path.stem

        layer_info = {
            'file_path': shp_path,
            'file_type': 'Shapefile',
            'layer_name': layer_name,
            'old_name': layer_name,
            'renameable': True,
            'rename_method': 'file'
        }

        self._log_info(f"Found Shapefile layer: {layer_name} in {shp_path}")
        return [layer_info]

    def _process_single_layer_file(self, file_path: Path, feedback) -> List[Dict]:
        """Process single-layer file formats (GeoJSON, KML, GPX, GML)."""
        layer_name = file_path.stem
        file_type = file_path.suffix.upper().lstrip('.')

        layer_info = {
            'file_path': file_path,
            'file_type': file_type,
            'layer_name': layer_name,
            'old_name': layer_name,
            'renameable': True,
            'rename_method': 'file'
        }

        self._log_info(f"Found {file_type} layer: {layer_name} in {file_path}")
        return [layer_info]

    def _process_mapinfo_file(self, file_path: Path, feedback) -> List[Dict]:
        """Process MapInfo file and extract layer information."""
        layer_name = file_path.stem

        layer_info = {
            'file_path': file_path,
            'file_type': 'MapInfo',
            'layer_name': layer_name,
            'old_name': layer_name,
            'renameable': True,
            'rename_method': 'file'
        }

        self._log_info(f"Found MapInfo layer: {layer_name} in {file_path}")
        return [layer_info]

    def _process_geodatabase(self, gdb_path: Path, feedback) -> List[Dict]:
        """Process File Geodatabase and extract layer information."""
        # File Geodatabase support is limited - placeholder for now
        self._log_warning(f"File Geodatabase support is limited: {gdb_path}")
        feedback.pushInfo(f"WARNING: Limited support for File Geodatabase: {gdb_path.name}")
        return []

    def _generate_rename_plan(self, all_layers: List[Dict], operation: int, find_text: str,
                            replace_text: str, trim_position: int, trim_count: int,
                            prefix: str, suffix: str, feedback) -> List[Dict]:
        """Generate rename plan based on operation."""

        rename_plan = []
        used_names = set()

        for layer_info in all_layers:
            old_name = layer_info['old_name']
            new_name = self._apply_rename_operation(
                old_name, operation, find_text, replace_text, trim_position, trim_count, prefix, suffix
            )

            # Sanitize the new name
            new_name = self._sanitize_layer_name(new_name)

            # Only include in plan if name actually changed
            if new_name != old_name:
                # Check for duplicates
                if new_name in used_names:
                    self._log_warning(f"Duplicate name detected: {new_name}")
                    # Add a counter to make it unique
                    counter = 1
                    base_name = new_name
                    while new_name in used_names:
                        new_name = f"{base_name}_{counter}"
                        counter += 1

                used_names.add(new_name)

                # Create rename plan entry
                plan_entry = layer_info.copy()
                plan_entry['new_name'] = new_name
                rename_plan.append(plan_entry)

        self._log_info(f"Generated rename plan for {len(rename_plan)} layers")
        return rename_plan

    def _apply_rename_operation(self, name: str, operation: int, find_text: str, replace_text: str,
                              trim_position: int, trim_count: int, prefix: str, suffix: str) -> str:
        """Apply the specified rename operation to a name."""

        if operation == 0:  # Replace text
            return name.replace(find_text, replace_text)
        elif operation == 1:  # Trim beginning
            return name[trim_count:] if len(name) > trim_count else ""
        elif operation == 2:  # Trim end
            return name[:-trim_count] if len(name) > trim_count else ""
        elif operation == 3:  # Add prefix
            return f"{prefix}{name}"
        elif operation == 4:  # Add suffix
            return f"{name}{suffix}"
        elif operation == 5:  # Clean names
            return self._clean_layer_name(name)
        elif operation == 6:  # Lowercase
            return name.lower()
        elif operation == 7:  # Uppercase
            return name.upper()
        elif operation == 8:  # Title Case
            return name.title()
        else:
            return name

    def _clean_layer_name(self, name: str) -> str:
        """Clean layer name by removing invalid characters."""
        # Replace invalid characters with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Remove multiple consecutive underscores
        clean_name = re.sub(r'_+', '_', clean_name)

        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')

        # Ensure it doesn't start with a number
        if clean_name and clean_name[0].isdigit():
            clean_name = f"layer_{clean_name}"

        # Ensure minimum length
        if not clean_name:
            clean_name = "layer"

        return clean_name

    def _sanitize_layer_name(self, name: str) -> str:
        """Sanitize layer name for database compatibility."""
        # Limit to reasonable length
        if len(name) > 63:  # SQLite identifier limit
            name = name[:63]

        # Remove trailing underscores after truncation
        name = name.rstrip('_')

        # Ensure minimum length
        if not name:
            name = "layer"

        return name

    def _display_rename_plan(self, rename_plan: List[Dict], feedback):
        """Display the rename plan to the user."""

        if not rename_plan:
            feedback.pushInfo("\nNo layers need to be renamed.")
            return

        feedback.pushInfo(f"\n{'='*100}")
        feedback.pushInfo("RENAME PLAN - Layer Name Changes")
        feedback.pushInfo(f"{'='*100}")
        feedback.pushInfo(f"{'File':<40} | {'Original Name':<25} | {'New Name':<25}")
        feedback.pushInfo("-" * 100)

        for plan_entry in rename_plan:
            file_name = plan_entry['file_path'].name
            old_name = plan_entry['old_name']
            new_name = plan_entry['new_name']

            # Truncate long names for display
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."
            if len(old_name) > 25:
                old_name = old_name[:22] + "..."
            if len(new_name) > 25:
                new_name = new_name[:22] + "..."

            feedback.pushInfo(f"{file_name:<40} | {old_name:<25} | {new_name:<25}")

        feedback.pushInfo("-" * 100)
        feedback.pushInfo(f"Total layers to rename: {len(rename_plan)}")

    def _create_backup_for_layer(self, layer_info: Dict, feedback):
        """Create backup for a layer's file."""

        file_path = layer_info['file_path']
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")

        if layer_info['rename_method'] == 'file':
            # For file-based formats, backup the file(s)
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = file_path.parent / backup_name

            if file_path.is_dir():
                # Directory (like .gdb)
                shutil.copytree(file_path, backup_path)
            else:
                # Single file or shapefile
                shutil.copy2(file_path, backup_path)

                # For shapefiles, copy all component files
                if file_path.suffix.lower() == '.shp':
                    for ext in ['.shx', '.dbf', '.prj', '.cpg', '.qix', '.qpj', '.sbn', '.sbx']:
                        component_file = file_path.with_suffix(ext)
                        if component_file.exists():
                            backup_component = backup_path.with_suffix(ext)
                            shutil.copy2(component_file, backup_component)

            self._log_info(f"Created backup: {backup_path}")

        elif layer_info['rename_method'] == 'database':
            # For database formats, backup the entire database
            backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
            backup_path = file_path.parent / backup_name

            shutil.copy2(file_path, backup_path)
            self._log_info(f"Created database backup: {backup_path}")

    def _apply_layer_rename(self, layer_info: Dict, feedback):
        """Apply the rename operation to a layer."""

        old_name = layer_info['old_name']
        new_name = layer_info['new_name']
        file_path = layer_info['file_path']
        rename_method = layer_info['rename_method']

        self._log_info(f"Renaming layer '{old_name}' to '{new_name}' in {file_path}")
        feedback.pushInfo(f"Renaming '{old_name}' → '{new_name}' in {file_path.name}")

        try:
            if rename_method == 'database':
                self._apply_database_rename(file_path, old_name, new_name, layer_info['file_type'])
            elif rename_method == 'file':
                self._apply_file_rename(file_path, new_name, layer_info['file_type'])
            else:
                raise QgsProcessingException(f"Unknown rename method: {rename_method}")

            self._log_info(f"Successfully renamed layer '{old_name}' to '{new_name}'")

        except Exception as e:
            self._log_error(f"Failed to rename layer '{old_name}' to '{new_name}': {str(e)}")
            raise

    def _apply_database_rename(self, db_path: Path, old_name: str, new_name: str, file_type: str):
        """Apply rename to database layer (GeoPackage/SpatiaLite)."""

        conn = sqlite3.connect(str(db_path))

        try:
            # Rename the main table
            conn.execute(f"ALTER TABLE [{old_name}] RENAME TO [{new_name}]")

            # Update GeoPackage metadata if it's a GeoPackage
            if file_type == 'GeoPackage':
                # Update gpkg_contents table
                conn.execute("""
                    UPDATE gpkg_contents
                    SET table_name = ?, identifier = ?
                    WHERE table_name = ?
                """, (new_name, new_name, old_name))

                # Update gpkg_geometry_columns table
                conn.execute("""
                    UPDATE gpkg_geometry_columns
                    SET table_name = ?
                    WHERE table_name = ?
                """, (new_name, old_name))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _apply_file_rename(self, file_path: Path, new_name: str, file_type: str):
        """Apply rename to file-based layer."""

        # Get the directory and create new file path
        base_dir = file_path.parent
        new_file_path = base_dir / f"{new_name}{file_path.suffix}"

        if file_type == 'Shapefile':
            # Rename all shapefile components
            old_base = file_path.stem

            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qix', '.qpj', '.sbn', '.sbx']:
                old_file = base_dir / f"{old_base}{ext}"
                new_file = base_dir / f"{new_name}{ext}"

                if old_file.exists():
                    old_file.rename(new_file)
                    self._log_info(f"Renamed {old_file.name} to {new_file.name}")
        else:
            # Single file rename
            file_path.rename(new_file_path)
            self._log_info(f"Renamed {file_path.name} to {new_file_path.name}")