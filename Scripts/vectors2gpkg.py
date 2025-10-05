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

Version: 0.5.0
"""

__version__ = "0.5.0"

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
        <li>Supports multiple vector formats (shapefiles, GeoJSON, KML, GPX, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, etc.)</li>
        <li>Copies both spatial and non-spatial layers from container formats (GeoPackages, File Geodatabases, SpatiaLite)</li>
        <li>Loads standalone dBase files as non-spatial tables</li>
        <li>User-selectable vector file types to process</li>
        <li>Creates spatial indexes for each layer</li>
        <li>Preserves metadata from original vector files</li>
        <li>Applies QML style files if found in same directory</li>
        <li>Layer names derived from file names with invalid characters replaced</li>
        </ul>

        <h3>Parameters:</h3>
        <ul>
        <li><b>Input Directory:</b> Top-level directory containing vector files</li>
        <li><b>Output GeoPackage:</b> Path for the output .gpkg file</li>
        <li><b>Vector File Types:</b> Select which vector file types to process</li>
        <li><b>Apply Styles:</b> Apply .qml style files found alongside vector files</li>
        <li><b>Create Spatial Index:</b> Create spatial indexes for each layer (recommended)</li>
        </ul>
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
                    "KML files (.kml)",
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

    def processAlgorithm(self, parameters, context, feedback):
        """Main processing method."""

        # Get parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIR, context)
        output_gpkg = self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context)
        vector_types = self.parameterAsEnums(parameters, self.VECTOR_TYPES, context)
        apply_styles = self.parameterAsBool(parameters, self.APPLY_STYLES, context)
        create_spatial_index = self.parameterAsBool(parameters, self.CREATE_SPATIAL_INDEX, context)

        if not input_dir:
            raise QgsProcessingException("Input directory is required")

        if not output_gpkg:
            raise QgsProcessingException("Output GeoPackage path is required")

        # Validate input directory
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            raise QgsProcessingException(f"Input directory does not exist: {input_dir}")

        feedback.pushInfo(f"Processing vector files in: {input_dir}")
        feedback.pushInfo(f"Output GeoPackage: {output_gpkg}")

        # Find all vector files
        vector_files = self._find_vector_files(input_path, vector_types, feedback)

        if not vector_files:
            feedback.pushWarning("No vector files found in the specified directory")
            return {self.OUTPUT_GPKG: output_gpkg}

        feedback.pushInfo(f"Found {len(vector_files)} vector files to process")

        # Process each vector file
        total_files = len(vector_files)
        processed_count = 0
        error_count = 0
        is_first_layer = True

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
            2: ["*.kml"],  # KML
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
                          is_first_layer: bool, feedback) -> str:
        """Process a single vector file or GeoPackage layer into the GeoPackage."""

        # Check the type of vector item and handle accordingly
        is_non_spatial = False

        if isinstance(vector_item, tuple):
            if vector_item[0] == "dbf_standalone":
                # Standalone dBase file: ("dbf_standalone", dbf_path)
                _, dbf_path = vector_item
                layer_uri = str(dbf_path)
                layer_name = self._generate_layer_name(dbf_path.stem)
                source_description = f"dBase table: {dbf_path.name}"
                style_source_path = dbf_path
                is_non_spatial = True
            else:
                # GeoPackage or File Geodatabase layer: (gdb_path/gpkg_path, layer_name)
                container_path, container_layer_name = vector_item

                if container_layer_name:
                    # Load specific layer from container (GeoPackage or File Geodatabase)
                    layer_uri = f"{container_path}|layername={container_layer_name}"
                    layer_name = self._generate_layer_name(f"{container_path.stem}_{container_layer_name}")

                    if container_path.suffix.lower() == '.gdb':
                        source_description = f"{container_path.name}:{container_layer_name}"
                    else:
                        source_description = f"{container_path.name}:{container_layer_name}"
                else:
                    # Load container as single file
                    layer_uri = str(container_path)
                    layer_name = self._generate_layer_name(container_path.stem)
                    source_description = str(container_path.name)

                style_source_path = container_path
        else:
            # Regular vector file
            vector_path = vector_item
            layer_uri = str(vector_path)
            layer_name = self._generate_layer_name(vector_path.stem)
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