"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Vector Files to GeoPackage Converter

Recursively searches a directory for vector files (shapefiles, GeoJSON, etc.) and loads them into a
GeoPackage with metadata preservation and optional style application.

Version: 0.8.0
"""

__version__ = "0.8.0"

import os
import re
from pathlib import Path
from typing import Any, Optional

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsDataSourceUri,
    QgsWkbTypes,
)


class Vectors2GpkgAlgorithm(QgsProcessingAlgorithm):
    """
    Loads vector files from a directory tree into a GeoPackage with
    metadata preservation and optional style application.
    """

    # Parameter constants
    INPUT_DIR = "INPUT_DIR"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    VECTOR_TYPES = "VECTOR_TYPES"
    APPLY_STYLES = "APPLY_STYLES"
    CREATE_SPATIAL_INDEX = "CREATE_SPATIAL_INDEX"
    DIRECTORY_NAMING = "DIRECTORY_NAMING"
    DIRECTORY_DEPTH = "DIRECTORY_DEPTH"
    DRY_RUN = "DRY_RUN"

    def createInstance(self):
        return Vectors2GpkgAlgorithm()

    def name(self):
        return "vectors2gpkg"

    def displayName(self):
        return "Load Vector Files to GeoPackage"

    def group(self):
        return "MQS Tools"

    def groupId(self):
        return "mqs_tools"

    def shortHelpString(self):
        return """
        <p>Recursively searches a directory for vector files and loads them into a GeoPackage.</p>

        <h3>Features:</h3>
        <ul>
        <li>Recursively processes all vector files in directory tree</li>
        <li>Supports multiple vector formats (shapefiles, GeoJSON, KML/KMZ, GPX, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, etc.)</li>
        <li>Copies both spatial and non-spatial layers from container formats (GeoPackages, File Geodatabases, SpatiaLite)</li>
        <li>Loads standalone dBase files as non-spatial tables</li>
        <li>User-selectable vector file types to process</li>
        <li>Creates spatial indexes for each layer</li>
        <li>Preserves metadata from original vector files</li>
        <li>Applies QML style files if found in same directory</li>
        <li>Smart layer naming with invalid character replacement and duplicate collision handling</li>
        <li>Directory-aware layer naming with multiple strategies (parent directory, smart path detection, configurable depth)</li>
        <li>Flexible naming options: filename only, directory + filename, or intelligent directory detection</li>
        <li>Dry run mode for previewing layer names before processing data</li>
        </ul>

        <h3>Parameters:</h3>
        <ul>
        <li><b>Input Directory:</b> Top-level directory containing vector files</li>
        <li><b>Output GeoPackage:</b> Path for the output .gpkg file</li>
        <li><b>Vector File Types:</b> Select which vector file types to process</li>
        <li><b>Apply Styles:</b> Apply .qml style files found alongside vector files</li>
        <li><b>Create Spatial Index:</b> Create spatial indexes for each layer (recommended)</li>
        <li><b>Dry Run:</b> Preview layer names without processing data (output path not required)</li>
        <li><b>Directory Naming Strategy:</b> Choose how directory names are incorporated into layer names</li>
        <li><b>Directory Depth:</b> When using 'Last N directories', specify how many directories to include</li>
        </ul>

        <h3>Dry Run Mode:</h3>
        <p>Enable dry run to preview the layer names that would be generated without processing any data.
        This is useful for testing directory naming strategies and seeing the results before committing to
        processing large datasets. In dry run mode, the output GeoPackage path is not required.</p>
        """

    def initAlgorithm(self, config=None):
        """Initialize the algorithm parameters."""

        # Input directory parameter
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DIR,
                "Input Directory",
                behavior=QgsProcessingParameterFile.Folder,
                defaultValue=None
            )
        )

        # Output GeoPackage parameter
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_GPKG,
                "Output GeoPackage",
                fileFilter="GeoPackage files (*.gpkg)"
            )
        )

        # Vector file types parameter
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VECTOR_TYPES,
                "Vector file types to process",
                options=[
                    "Shapefiles (.shp)",
                    "GeoJSON (.geojson/.json)",
                    "KML files (.kml/.kmz)",
                    "GPX files (.gpx)",
                    "GML files (.gml)",
                    "GeoPackage files (.gpkg)",
                    "File Geodatabases (.gdb)",
                    "SpatiaLite databases (.sqlite/.db)",
                    "MapInfo files (.tab/.mif)",
                    "Standalone dBase files (.dbf)"
                ],
                allowMultiple=True,
                defaultValue=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # All types selected by default
            )
        )

        # Apply styles option
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APPLY_STYLES,
                "Apply QML styles if found",
                defaultValue=True
            )
        )

        # Create spatial index option
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CREATE_SPATIAL_INDEX,
                "Create spatial indexes",
                defaultValue=True
            )
        )

        # Dry run option
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.DRY_RUN,
                "Dry run (preview layer names without processing data)",
                defaultValue=False
            )
        )

        # Directory naming strategy parameter
        self.addParameter(
            QgsProcessingParameterEnum(
                self.DIRECTORY_NAMING,
                "Directory naming strategy",
                options=[
                    "Filename only (current behavior)",
                    "Parent directory + filename",
                    "Last N directories + filename",
                    "Smart path (auto-detect important directories)",
                    "Full relative path (truncated if needed)"
                ],
                defaultValue=0  # Filename only as default (backward compatibility)
            )
        )

        # Directory depth parameter (for "Last N directories" option)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIRECTORY_DEPTH,
                "Directory depth (when using 'Last N directories')",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=2,
                minValue=1,
                maxValue=5
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Main processing method."""

        # Get parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIR, context)
        output_gpkg = self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context)
        vector_types = self.parameterAsEnums(parameters, self.VECTOR_TYPES, context)
        apply_styles = self.parameterAsBool(parameters, self.APPLY_STYLES, context)
        create_spatial_index = self.parameterAsBool(parameters, self.CREATE_SPATIAL_INDEX, context)
        directory_naming = self.parameterAsEnum(parameters, self.DIRECTORY_NAMING, context)
        directory_depth = self.parameterAsInt(parameters, self.DIRECTORY_DEPTH, context)
        dry_run = self.parameterAsBool(parameters, self.DRY_RUN, context)

        if not input_dir:
            raise QgsProcessingException("Input directory is required")

        if not dry_run and not output_gpkg:
            raise QgsProcessingException("Output GeoPackage path is required (unless using dry run mode)")

        # Validate input directory
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            raise QgsProcessingException(f"Input directory does not exist: {input_dir}")

        feedback.pushInfo(f"Processing vector files in: {input_dir}")
        if dry_run:
            feedback.pushInfo("DRY RUN MODE - No data will be processed, only layer names will be generated")
        else:
            feedback.pushInfo(f"Output GeoPackage: {output_gpkg}")

        # Find all vector files
        vector_files = self._find_vector_files(input_path, vector_types, feedback)

        if not vector_files:
            feedback.pushWarning("No vector files found in the specified directory")
            return {self.OUTPUT_GPKG: output_gpkg if not dry_run else None}

        feedback.pushInfo(f"Found {len(vector_files)} vector files to process")

        if dry_run:
            # Dry run mode - only generate and display layer names
            return self._perform_dry_run(vector_files, input_path, directory_naming, directory_depth, feedback)

        # Process each vector file
        total_files = len(vector_files)
        processed_count = 0
        error_count = 0
        is_first_layer = True
        used_layer_names = set()  # Track used layer names to handle duplicates

        for i, vector_item in enumerate(vector_files):
            if feedback.isCanceled():
                break

            # Update progress
            progress = int((i / total_files) * 100)
            feedback.setProgress(progress)

            # Get display name for the vector item
            if isinstance(vector_item, tuple):
                if vector_item[0] == "dbf_standalone":
                    # Standalone dBase file
                    _, dbf_path = vector_item
                    display_name = f"dBase: {dbf_path.name}"
                else:
                    # GeoPackage or File Geodatabase layer
                    container_path, layer_name = vector_item
                    if layer_name:
                        display_name = f"{container_path.name}:{layer_name}"
                    else:
                        display_name = container_path.name
            else:
                display_name = vector_item.name

            try:
                layer_name = self._process_vector_file(
                    vector_item,
                    output_gpkg,
                    apply_styles,
                    create_spatial_index,
                    is_first_layer,
                    used_layer_names,
                    input_path,
                    directory_naming,
                    directory_depth,
                    feedback
                )
                processed_count += 1
                is_first_layer = False
                feedback.pushInfo(f"✓ Processed: {display_name} → {layer_name}")

            except Exception as e:
                error_count += 1
                feedback.pushWarning(f"✗ Error processing {display_name}: {str(e)}")
                continue

        # Final summary
        feedback.pushInfo(f"\nSummary:")
        feedback.pushInfo(f"  Processed: {processed_count} vector files")
        if error_count > 0:
            feedback.pushInfo(f"  Errors: {error_count} vector files")
        feedback.pushInfo(f"  Output: {output_gpkg}")

        return {self.OUTPUT_GPKG: output_gpkg}

    def _find_vector_files(self, directory: Path, selected_types: list, feedback) -> list:
        """Recursively find all vector files in directory tree based on selected types."""
        vector_files = []

        # Map of type indices to file patterns
        type_patterns = {
            0: ["*.shp"],  # Shapefiles
            1: ["*.geojson", "*.json"],  # GeoJSON
            2: ["*.kml", "*.kmz"],  # KML/KMZ
            3: ["*.gpx"],  # GPX
            4: ["*.gml"],  # GML
            5: ["*.gpkg"],  # GeoPackage
            6: ["*.gdb"],  # File Geodatabase
            7: ["*.sqlite", "*.db"],  # SpatiaLite
            8: ["*.tab", "*.mif"],  # MapInfo
            9: ["*.dbf"]   # Standalone dBase files (will be filtered later)
        }

        # Build list of patterns to search for based on selected types
        patterns_to_search = []
        for type_index in selected_types:
            if type_index in type_patterns:
                patterns_to_search.extend(type_patterns[type_index])

        if not patterns_to_search:
            feedback.pushWarning("No vector file types selected")
            return []

        try:
            for pattern in patterns_to_search:
                if pattern == "*.gdb":
                    # Handle File Geodatabases as directories
                    for gdb_dir in directory.rglob(pattern):
                        if gdb_dir.is_dir():
                            # For File Geodatabases, we need to find the layers inside them
                            gdb_layers = self._get_gdb_layers(gdb_dir, feedback)
                            vector_files.extend(gdb_layers)
                            feedback.pushDebugInfo(f"Found File Geodatabase: {gdb_dir}")
                elif pattern in ["*.sqlite", "*.db"]:
                    # Handle SpatiaLite databases (container format like GeoPackage)
                    for spatialite_file in directory.rglob(pattern):
                        if spatialite_file.is_file():
                            # For SpatiaLite files, we need to find the layers inside them
                            spatialite_layers = self._get_spatialite_layers(spatialite_file, feedback)
                            vector_files.extend(spatialite_layers)
                            feedback.pushDebugInfo(f"Found SpatiaLite database: {spatialite_file}")
                elif pattern == "*.dbf":
                    # Handle standalone dBase files (those without corresponding .shp files)
                    for dbf_file in directory.rglob(pattern):
                        if dbf_file.is_file():
                            if self._is_standalone_dbf(dbf_file):
                                # Mark as standalone dBase file
                                vector_files.append(("dbf_standalone", dbf_file))
                                feedback.pushDebugInfo(f"Found standalone dBase file: {dbf_file}")
                else:
                    for vector_file in directory.rglob(pattern):
                        if vector_file.is_file():
                            if pattern == "*.gpkg":
                                # For GeoPackage files, we need to find the layers inside them
                                gpkg_layers = self._get_gpkg_layers(vector_file, feedback)
                                vector_files.extend(gpkg_layers)
                            else:
                                vector_files.append(vector_file)
                            feedback.pushDebugInfo(f"Found vector file: {vector_file}")
        except Exception as e:
            feedback.pushWarning(f"Error scanning directory {directory}: {str(e)}")

        # Sort vector files using a custom key function to handle mixed types
        def sort_key(item):
            if isinstance(item, tuple):
                if item[0] == "dbf_standalone":
                    # Standalone dBase file: ("dbf_standalone", dbf_path)
                    return str(item[1])
                else:
                    # GeoPackage or File Geodatabase layer: (container_path, layer_name)
                    container_path, layer_name = item
                    if layer_name:
                        return f"{container_path}:{layer_name}"
                    else:
                        return str(container_path)
            else:
                # Regular Path object
                return str(item)

        return sorted(vector_files, key=sort_key)

    def _get_gpkg_layers(self, gpkg_path: Path, feedback) -> list:
        """Get list of layers from a GeoPackage file."""
        gpkg_layers = []

        try:
            from qgis.core import QgsProviderRegistry

            # Get the OGR provider
            provider_metadata = QgsProviderRegistry.instance().providerMetadata('ogr')
            if not provider_metadata:
                feedback.pushWarning(f"OGR provider not available for {gpkg_path}")
                return gpkg_layers

            # Get sublayers from the GeoPackage
            conn = provider_metadata.createConnection(str(gpkg_path), {})
            if conn:
                try:
                    # Get table names from the GeoPackage
                    tables = conn.tables()
                    for table in tables:
                        if hasattr(table, 'tableName'):
                            layer_name = table.tableName()
                        else:
                            layer_name = str(table)

                        if layer_name:
                            # Try to determine if this is a spatial or non-spatial table
                            table_type = "unknown"
                            try:
                                # Test load the layer to check geometry type
                                test_layer = QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", "test", "ogr")
                                if test_layer.isValid():
                                    if test_layer.geometryType() == QgsWkbTypes.NullGeometry:
                                        table_type = "non-spatial table"
                                    else:
                                        table_type = "spatial layer"
                            except Exception:
                                table_type = "layer/table"

                            # Create a tuple with (gpkg_path, layer_name) to identify GeoPackage layers
                            gpkg_layers.append((gpkg_path, layer_name))
                            feedback.pushDebugInfo(f"Found GeoPackage {table_type}: {gpkg_path}:{layer_name}")

                except Exception as e:
                    feedback.pushDebugInfo(f"Could not enumerate layers in {gpkg_path}: {str(e)}")
                    # Fallback: add the GeoPackage file itself
                    gpkg_layers.append((gpkg_path, None))
                    feedback.pushDebugInfo(f"Added GeoPackage as single file: {gpkg_path}")

        except Exception as e:
            feedback.pushWarning(f"Error processing GeoPackage {gpkg_path}: {str(e)}")
            # Fallback: add the GeoPackage file itself
            gpkg_layers.append((gpkg_path, None))

        return gpkg_layers

    def _get_gdb_layers(self, gdb_path: Path, feedback) -> list:
        """Get list of layers from a File Geodatabase."""
        gdb_layers = []

        try:
            from qgis.core import QgsProviderRegistry

            # Get the OGR provider
            provider_metadata = QgsProviderRegistry.instance().providerMetadata('ogr')
            if not provider_metadata:
                feedback.pushWarning(f"OGR provider not available for {gdb_path}")
                return gdb_layers

            # Get sublayers from the File Geodatabase
            conn = provider_metadata.createConnection(str(gdb_path), {})
            if conn:
                try:
                    # Get table names from the File Geodatabase
                    tables = conn.tables()
                    for table in tables:
                        if hasattr(table, 'tableName'):
                            layer_name = table.tableName()
                        else:
                            layer_name = str(table)

                        if layer_name:
                            # Try to determine if this is a spatial feature class or non-spatial table
                            table_type = "unknown"
                            try:
                                # Test load the layer to check geometry type
                                test_layer = QgsVectorLayer(f"{gdb_path}|layername={layer_name}", "test", "ogr")
                                if test_layer.isValid():
                                    if test_layer.geometryType() == QgsWkbTypes.NullGeometry:
                                        table_type = "non-spatial table"
                                    else:
                                        table_type = "feature class"
                            except Exception:
                                table_type = "feature class/table"

                            # Create a tuple with (gdb_path, layer_name) to identify GDB layers
                            gdb_layers.append((gdb_path, layer_name))
                            feedback.pushDebugInfo(f"Found File Geodatabase {table_type}: {gdb_path}:{layer_name}")

                except Exception as e:
                    feedback.pushDebugInfo(f"Could not enumerate layers in {gdb_path}: {str(e)}")
                    # Fallback: add the File Geodatabase itself
                    gdb_layers.append((gdb_path, None))
                    feedback.pushDebugInfo(f"Added File Geodatabase as single file: {gdb_path}")

        except Exception as e:
            feedback.pushWarning(f"Error processing File Geodatabase {gdb_path}: {str(e)}")
            # Fallback: add the File Geodatabase itself
            gdb_layers.append((gdb_path, None))

        return gdb_layers

    def _get_spatialite_layers(self, spatialite_path: Path, feedback) -> list:
        """Get list of layers from a SpatiaLite database."""
        spatialite_layers = []

        try:
            from qgis.core import QgsProviderRegistry

            # Get the OGR provider
            provider_metadata = QgsProviderRegistry.instance().providerMetadata('ogr')
            if not provider_metadata:
                feedback.pushWarning(f"OGR provider not available for {spatialite_path}")
                return spatialite_layers

            # Get sublayers from the SpatiaLite database
            conn = provider_metadata.createConnection(str(spatialite_path), {})
            if conn:
                try:
                    # Get table names from the SpatiaLite database
                    tables = conn.tables()
                    for table in tables:
                        if hasattr(table, 'tableName'):
                            layer_name = table.tableName()
                        else:
                            layer_name = str(table)

                        if layer_name:
                            # Try to determine if this is a spatial table or non-spatial table
                            table_type = "unknown"
                            try:
                                # Test load the layer to check geometry type
                                test_layer = QgsVectorLayer(f"{spatialite_path}|layername={layer_name}", "test", "ogr")
                                if test_layer.isValid():
                                    if test_layer.geometryType() == QgsWkbTypes.NullGeometry:
                                        table_type = "non-spatial table"
                                    else:
                                        table_type = "spatial table"
                            except Exception:
                                table_type = "table"

                            # Create a tuple with (spatialite_path, layer_name) to identify SpatiaLite layers
                            spatialite_layers.append((spatialite_path, layer_name))
                            feedback.pushDebugInfo(f"Found SpatiaLite {table_type}: {spatialite_path}:{layer_name}")

                except Exception as e:
                    feedback.pushDebugInfo(f"Could not enumerate layers in {spatialite_path}: {str(e)}")
                    # Fallback: add the SpatiaLite database itself
                    spatialite_layers.append((spatialite_path, None))
                    feedback.pushDebugInfo(f"Added SpatiaLite database as single file: {spatialite_path}")

        except Exception as e:
            feedback.pushWarning(f"Error processing SpatiaLite database {spatialite_path}: {str(e)}")
            # Fallback: add the SpatiaLite database itself
            spatialite_layers.append((spatialite_path, None))

        return spatialite_layers

    def _is_standalone_dbf(self, dbf_path: Path) -> bool:
        """Check if a dBase file is standalone (no corresponding .shp file)."""
        try:
            # Get the base name without extension
            base_name = dbf_path.stem

            # Check if there's a corresponding .shp file in the same directory
            shp_path = dbf_path.parent / f"{base_name}.shp"

            # Return True if standalone (no .shp file exists)
            return not shp_path.exists()

        except Exception:
            # If we can't determine, assume it's not standalone to be safe
            return False

    def _process_vector_file(self, vector_item, output_gpkg: str,
                          apply_styles: bool, create_spatial_index: bool,
                          is_first_layer: bool, used_layer_names: set, input_root: Path,
                          directory_naming: int, directory_depth: int, feedback) -> str:
        """Process a single vector file or GeoPackage layer into the GeoPackage."""

        # Check the type of vector item and handle accordingly
        is_non_spatial = False

        if isinstance(vector_item, tuple):
            if vector_item[0] == "dbf_standalone":
                # Standalone dBase file: ("dbf_standalone", dbf_path)
                _, dbf_path = vector_item
                layer_uri = str(dbf_path)
                base_layer_name = self._generate_directory_aware_name(
                    dbf_path, input_root, directory_naming, directory_depth)
                layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)
                source_description = f"dBase table: {dbf_path.name}"
                style_source_path = dbf_path
                is_non_spatial = True
            else:
                # GeoPackage or File Geodatabase layer: (gdb_path/gpkg_path, layer_name)
                container_path, container_layer_name = vector_item

                if container_layer_name:
                    # Load specific layer from container (GeoPackage or File Geodatabase)
                    layer_uri = f"{container_path}|layername={container_layer_name}"
                    # For container layers, use container path for directory naming
                    container_base_name = self._generate_directory_aware_name(
                        container_path, input_root, directory_naming, directory_depth)
                    base_layer_name = self._generate_layer_name(f"{container_base_name}_{container_layer_name}")
                    layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)

                    if container_path.suffix.lower() == '.gdb':
                        source_description = f"{container_path.name}:{container_layer_name}"
                    else:
                        source_description = f"{container_path.name}:{container_layer_name}"
                else:
                    # Load container as single file
                    layer_uri = str(container_path)
                    base_layer_name = self._generate_directory_aware_name(
                        container_path, input_root, directory_naming, directory_depth)
                    layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)
                    source_description = str(container_path.name)

                style_source_path = container_path
        else:
            # Regular vector file
            vector_path = vector_item
            layer_uri = str(vector_path)
            base_layer_name = self._generate_directory_aware_name(
                vector_path, input_root, directory_naming, directory_depth)
            layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)
            source_description = str(vector_path.name)
            style_source_path = vector_path

        # Load the vector file or layer
        layer = QgsVectorLayer(layer_uri, layer_name, "ogr")
        if not layer.isValid():
            raise QgsProcessingException(f"Failed to load vector source: {source_description}")

        # Check if layer has geometry
        if is_non_spatial or layer.geometryType() == QgsWkbTypes.NullGeometry:
            feedback.pushDebugInfo(f"Loaded non-spatial table: {layer_name} ({layer.featureCount()} records)")
            is_non_spatial = True
        else:
            feedback.pushDebugInfo(f"Loaded layer: {layer_name} ({layer.featureCount()} features)")

        # Write to GeoPackage
        writer_options = QgsVectorFileWriter.SaveVectorOptions()
        writer_options.driverName = "GPKG"
        writer_options.layerName = layer_name

        # Set action based on whether this is the first layer or not
        if is_first_layer:
            writer_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        else:
            writer_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # Set up spatial index option - only for spatial layers
        if create_spatial_index and not is_non_spatial:
            writer_options.layerOptions = ["SPATIAL_INDEX=YES"]

        # For non-spatial tables, ensure no geometry is written
        if is_non_spatial:
            writer_options.layerOptions = writer_options.layerOptions or []
            writer_options.layerOptions.append("ASPATIAL_VARIANT=GPKG_ATTRIBUTES")
            writer_options.symbologyExport = QgsVectorFileWriter.NoSymbology

        error, error_message = QgsVectorFileWriter.writeAsVectorFormat(
            layer,
            output_gpkg,
            writer_options
        )

        if error != QgsVectorFileWriter.NoError:
            raise QgsProcessingException(f"Failed to write layer to GeoPackage: {error_message}")

        # Apply style if requested and available
        if apply_styles:
            self._apply_style_if_available(style_source_path, layer_name, output_gpkg, feedback)

        return layer_name

    def _generate_layer_name(self, file_name: str) -> str:
        """Generate a clean layer name from file name."""
        # Replace invalid characters with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', file_name)

        # Ensure it doesn't start with a number
        if clean_name[0].isdigit():
            clean_name = f"layer_{clean_name}"

        # Limit length and remove multiple consecutive underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        clean_name = clean_name.strip('_')

        # Ensure minimum length
        if not clean_name:
            clean_name = "unnamed_layer"

        return clean_name[:63]  # SQLite identifier limit

    def _ensure_unique_layer_name(self, base_name: str, used_names: set) -> str:
        """Ensure layer name is unique by appending incrementing numbers if needed."""
        # If base name is not used, return it
        if base_name not in used_names:
            used_names.add(base_name)
            return base_name

        # Try incrementing numbers until we find an unused name
        counter = 1
        while True:
            # Calculate available space for counter suffix
            suffix = f"_{counter}"
            max_base_length = 63 - len(suffix)  # SQLite identifier limit

            # Truncate base name if needed to fit with suffix
            truncated_base = base_name[:max_base_length]
            candidate_name = f"{truncated_base}{suffix}"

            if candidate_name not in used_names:
                used_names.add(candidate_name)
                return candidate_name

            counter += 1

            # Safety check to prevent infinite loop (very unlikely)
            if counter > 9999:
                import uuid
                unique_suffix = str(uuid.uuid4())[:8]
                fallback_name = f"layer_{unique_suffix}"
                used_names.add(fallback_name)
                return fallback_name

    def _generate_directory_aware_name(self, vector_path: Path, input_root: Path,
                                     naming_strategy: int, directory_depth: int) -> str:
        """Generate layer name incorporating directory structure based on strategy."""

        # Strategy 0: Filename only (current behavior)
        if naming_strategy == 0:
            return self._generate_layer_name(vector_path.stem)

        # Get relative path from input root
        try:
            relative_path = vector_path.relative_to(input_root)
            path_parts = relative_path.parts[:-1]  # Exclude the filename itself
        except ValueError:
            # Fallback if path is not relative to input_root
            path_parts = vector_path.parent.parts

        # Apply strategy-specific logic
        if naming_strategy == 1:  # Parent directory + filename
            return self._parent_directory_strategy(vector_path, path_parts)
        elif naming_strategy == 2:  # Last N directories + filename
            return self._last_n_directories_strategy(vector_path, path_parts, directory_depth)
        elif naming_strategy == 3:  # Smart path (auto-detect important directories)
            return self._smart_path_strategy(vector_path, path_parts)
        elif naming_strategy == 4:  # Full relative path (truncated if needed)
            return self._full_relative_path_strategy(vector_path, path_parts)
        else:
            # Fallback to filename only
            return self._generate_layer_name(vector_path.stem)

    def _parent_directory_strategy(self, vector_path: Path, path_parts: tuple) -> str:
        """Strategy 1: Parent directory + filename."""
        if path_parts:
            parent_dir = self._sanitize_directory_name(path_parts[-1])
            filename = self._generate_layer_name(vector_path.stem)
            combined = f"{parent_dir}_{filename}"
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(vector_path.stem)

    def _last_n_directories_strategy(self, vector_path: Path, path_parts: tuple, depth: int) -> str:
        """Strategy 2: Last N directories + filename."""
        if path_parts:
            # Take the last N directories
            relevant_parts = path_parts[-depth:] if len(path_parts) >= depth else path_parts
            dir_parts = [self._sanitize_directory_name(part) for part in relevant_parts]
            filename = self._generate_layer_name(vector_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(vector_path.stem)

    def _smart_path_strategy(self, vector_path: Path, path_parts: tuple) -> str:
        """Strategy 3: Smart path (auto-detect important directories)."""
        if not path_parts:
            return self._generate_layer_name(vector_path.stem)

        # Define semantic filters
        skip_patterns = {
            'home', 'user', 'users', 'desktop', 'documents', 'downloads', 'temp', 'tmp',
            'data', 'gis', 'spatial', 'vector', 'files', 'shapefiles', 'geodata'
        }

        # Year patterns (1900-2099)
        year_pattern = re.compile(r'^(19|20)\d{2}$')

        # Quarter/period patterns
        period_pattern = re.compile(r'^(q[1-4]|quarter[1-4]|h[12]|half[12])$', re.IGNORECASE)

        important_parts = []
        for part in path_parts:
            part_lower = part.lower()

            # Skip common non-semantic directories
            if part_lower in skip_patterns:
                continue

            # Always include years
            if year_pattern.match(part):
                important_parts.append(part)
                continue

            # Always include quarters/periods
            if period_pattern.match(part):
                important_parts.append(part)
                continue

            # Include meaningful directory names (not too generic)
            if len(part) > 2 and not part.isdigit():
                important_parts.append(part)

        # Limit to last 3 important parts to avoid very long names
        important_parts = important_parts[-3:]

        if important_parts:
            dir_parts = [self._sanitize_directory_name(part) for part in important_parts]
            filename = self._generate_layer_name(vector_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(vector_path.stem)

    def _full_relative_path_strategy(self, vector_path: Path, path_parts: tuple) -> str:
        """Strategy 4: Full relative path (truncated if needed)."""
        if not path_parts:
            return self._generate_layer_name(vector_path.stem)

        # Combine all path parts with filename
        dir_parts = [self._sanitize_directory_name(part) for part in path_parts]
        filename = self._generate_layer_name(vector_path.stem)
        combined = "_".join(dir_parts + [filename])

        # Apply standard layer name generation (which includes length limits)
        return self._generate_layer_name(combined)

    def _sanitize_directory_name(self, directory_name: str) -> str:
        """Sanitize directory name for use in layer names."""
        # Basic sanitization - replace invalid characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', directory_name)

        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)

        # Strip leading/trailing underscores
        sanitized = sanitized.strip('_')

        # Ensure not empty
        if not sanitized:
            sanitized = "dir"

        return sanitized

    def _perform_dry_run(self, vector_files: list, input_root: Path, directory_naming: int,
                        directory_depth: int, feedback) -> dict:
        """Perform dry run - generate layer names without processing data."""

        feedback.pushInfo("\n" + "="*80)
        feedback.pushInfo("DRY RUN RESULTS - Layer Name Preview")
        feedback.pushInfo("="*80)

        used_layer_names = set()  # Track used layer names to handle duplicates
        total_files = len(vector_files)

        # Headers for the output table
        feedback.pushInfo(f"{'No.':<4} {'Original Path':<50} {'Layer/Table Name':<30}")
        feedback.pushInfo("-" * 84)

        for i, vector_item in enumerate(vector_files):
            if feedback.isCanceled():
                break

            # Update progress
            progress = int((i / total_files) * 100)
            feedback.setProgress(progress)

            try:
                # Generate the original path and layer name
                original_path, layer_type = self._get_original_path_and_type(vector_item)

                # Generate the final layer name that would be used
                final_layer_name = self._generate_dry_run_layer_name(
                    vector_item, input_root, directory_naming, directory_depth, used_layer_names)

                # Format and display the result
                row_num = f"{i+1:>3}."
                path_display = str(original_path)
                if len(path_display) > 47:
                    path_display = "..." + path_display[-44:]

                layer_display = f"{final_layer_name} ({layer_type})"

                feedback.pushInfo(f"{row_num:<4} {path_display:<50} {layer_display:<30}")

            except Exception as e:
                feedback.pushWarning(f"Error processing {vector_item}: {str(e)}")
                continue

        feedback.pushInfo("-" * 84)
        feedback.pushInfo(f"Total files that would be processed: {len(vector_files)}")
        feedback.pushInfo(f"Unique layer names generated: {len(used_layer_names)}")

        # Summary by directory naming strategy
        strategy_names = [
            "Filename only (current behavior)",
            "Parent directory + filename",
            "Last N directories + filename",
            "Smart path (auto-detect important directories)",
            "Full relative path (truncated if needed)"
        ]
        feedback.pushInfo(f"Directory naming strategy: {strategy_names[directory_naming]}")
        if directory_naming == 2:  # Last N directories
            feedback.pushInfo(f"Directory depth: {directory_depth}")

        feedback.pushInfo("\nNote: This was a dry run. No data was processed.")
        feedback.pushInfo("="*80)

        return {self.OUTPUT_GPKG: None}

    def _get_original_path_and_type(self, vector_item) -> tuple:
        """Get the original path and type description for dry run display."""
        if isinstance(vector_item, tuple):
            if vector_item[0] == "dbf_standalone":
                # Standalone dBase file: ("dbf_standalone", dbf_path)
                _, dbf_path = vector_item
                return dbf_path, "dBase table"
            else:
                # Container layer: (container_path, layer_name)
                container_path, layer_name = vector_item
                if layer_name:
                    return f"{container_path}:{layer_name}", "container layer"
                else:
                    return container_path, "container file"
        else:
            # Regular vector file
            return vector_item, "vector file"

    def _generate_dry_run_layer_name(self, vector_item, input_root: Path, directory_naming: int,
                                   directory_depth: int, used_layer_names: set) -> str:
        """Generate layer name for dry run preview."""

        # Generate base layer name using the same logic as actual processing
        if isinstance(vector_item, tuple):
            if vector_item[0] == "dbf_standalone":
                # Standalone dBase file
                _, dbf_path = vector_item
                base_layer_name = self._generate_directory_aware_name(
                    dbf_path, input_root, directory_naming, directory_depth)
            else:
                # Container layer
                container_path, container_layer_name = vector_item
                if container_layer_name:
                    # Specific layer from container
                    container_base_name = self._generate_directory_aware_name(
                        container_path, input_root, directory_naming, directory_depth)
                    base_layer_name = self._generate_layer_name(f"{container_base_name}_{container_layer_name}")
                else:
                    # Container as single file
                    base_layer_name = self._generate_directory_aware_name(
                        container_path, input_root, directory_naming, directory_depth)
        else:
            # Regular vector file
            base_layer_name = self._generate_directory_aware_name(
                vector_item, input_root, directory_naming, directory_depth)

        # Apply duplicate handling
        final_layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)

        return final_layer_name

    def _apply_style_if_available(self, vector_path: Path, layer_name: str,
                                 output_gpkg: str, feedback):
        """Apply QML style file if found alongside the vector file."""

        # Look for QML file with same name as vector file
        qml_path = vector_path.with_suffix('.qml')

        if qml_path.exists() and qml_path.is_file():
            try:
                # Load the layer from GeoPackage
                gpkg_layer = QgsVectorLayer(f"{output_gpkg}|layername={layer_name}", layer_name, "ogr")

                if gpkg_layer.isValid():
                    # Load and apply style
                    result, error_msg = gpkg_layer.loadNamedStyle(str(qml_path))
                    if result:
                        feedback.pushInfo(f"  ✓ Applied style: {qml_path.name}")
                    else:
                        feedback.pushWarning(f"  ✗ Failed to apply style {qml_path.name}: {error_msg}")
                else:
                    feedback.pushWarning(f"  ✗ Could not reload layer {layer_name} for styling")

            except Exception as e:
                feedback.pushWarning(f"  ✗ Error applying style {qml_path.name}: {str(e)}")
        else:
            feedback.pushDebugInfo(f"  No QML style found for {vector_path.name}")