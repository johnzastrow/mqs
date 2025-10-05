"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Raster Files to GeoPackage Converter

Recursively searches a directory for raster files (GeoTIFF, IMG, etc.) and loads them into a
GeoPackage with metadata preservation and optional style application.

Version: 0.1.0
"""

__version__ = "0.1.0"

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
    QgsProcessingParameterString,
    QgsRasterLayer,
    QgsProject,
    QgsDataSourceUri,
)


class Rasters2GpkgAlgorithm(QgsProcessingAlgorithm):
    """
    Loads raster files from a directory tree into a GeoPackage with
    metadata preservation and optional style application.
    """

    # Parameter constants
    INPUT_DIR = "INPUT_DIR"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    RASTER_TYPES = "RASTER_TYPES"
    APPLY_STYLES = "APPLY_STYLES"
    DIRECTORY_NAMING = "DIRECTORY_NAMING"
    DIRECTORY_DEPTH = "DIRECTORY_DEPTH"
    DIRECTORY_LEVELS = "DIRECTORY_LEVELS"
    DRY_RUN = "DRY_RUN"

    def createInstance(self):
        return Rasters2GpkgAlgorithm()

    def name(self):
        return "rasters2gpkg"

    def displayName(self):
        return "Load Raster Files to GeoPackage"

    def group(self):
        return "MQS Tools"

    def groupId(self):
        return "mqs_tools"

    def shortHelpString(self):
        return """
        <p>Recursively searches a directory for raster files and loads them into a GeoPackage.</p>

        <h3>Features:</h3>
        <ul>
        <li>Recursively processes all raster files in directory tree</li>
        <li>Supports multiple raster formats (GeoTIFF, IMG, ERDAS, ENVI, etc.)</li>
        <li>User-selectable raster file types to process</li>
        <li>Preserves metadata from original raster files</li>
        <li>Applies QML style files if found in same directory</li>
        <li>Smart layer naming with invalid character replacement and duplicate collision handling</li>
        <li>Directory-aware layer naming with multiple strategies</li>
        <li>Dry run mode for previewing layer names before processing data</li>
        </ul>

        <h3>Parameters:</h3>
        <ul>
        <li><b>Input Directory:</b> Top-level directory containing raster files</li>
        <li><b>Output GeoPackage:</b> Path for the output .gpkg file</li>
        <li><b>Raster File Types:</b> Select which raster file types to process</li>
        <li><b>Apply Styles:</b> Apply .qml style files found alongside raster files</li>
        <li><b>Dry Run:</b> Preview layer names without processing data (output path not required)</li>
        <li><b>Directory Naming Strategy:</b> Choose how directory names are incorporated into layer names</li>
        <li><b>Directory Depth:</b> When using 'Last N directories' or 'First N directories', specify how many directories to include</li>
        <li><b>Directory Levels:</b> When using 'Selected levels', specify comma-separated directory level numbers (e.g., '0,2,4')</li>
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
                "Input directory containing raster files",
                behavior=QgsProcessingParameterFile.Folder
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

        # Raster file types parameter (multi-select)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.RASTER_TYPES,
                "Raster file types to process",
                options=[
                    "GeoTIFF files (.tif/.tiff)",
                    "ERDAS IMAGINE files (.img)",
                    "ENVI files (.hdr)",
                    "ASCII Grid files (.asc)",
                    "ESRI Grid files",
                    "NetCDF files (.nc)",
                    "HDF files (.hdf/.h4/.h5)",
                    "JPEG2000 files (.jp2)",
                    "PNG files (.png)",
                    "JPEG files (.jpg/.jpeg)"
                ],
                allowMultiple=True,
                defaultValue=list(range(10))  # All types selected by default
            )
        )

        # Apply styles parameter
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APPLY_STYLES,
                "Apply QML styles if found alongside raster files",
                defaultValue=True
            )
        )

        # Dry run parameter
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
                    "First N directories + filename",
                    "Selected levels (specify directory levels)",
                    "Smart path (auto-detect important directories)",
                    "Full relative path (truncated if needed)"
                ],
                defaultValue=0  # Filename only as default (backward compatibility)
            )
        )

        # Directory depth parameter (for "Last N directories" and "First N directories" options)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIRECTORY_DEPTH,
                "Directory depth (when using 'Last N directories' or 'First N directories')",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=2,
                minValue=1,
                maxValue=5
            )
        )

        # Directory levels parameter (for "Selected levels" option)
        self.addParameter(
            QgsProcessingParameterString(
                self.DIRECTORY_LEVELS,
                "Directory levels (when using 'Selected levels' - comma-separated numbers, e.g., '0,2,4')",
                defaultValue="0,1",
                optional=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Main processing method."""

        # Extract parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIR, context)
        output_gpkg = self.parameterAsFileOutput(parameters, self.OUTPUT_GPKG, context)
        raster_types = self.parameterAsEnums(parameters, self.RASTER_TYPES, context)
        apply_styles = self.parameterAsBool(parameters, self.APPLY_STYLES, context)
        directory_naming = self.parameterAsEnum(parameters, self.DIRECTORY_NAMING, context)
        directory_depth = self.parameterAsInt(parameters, self.DIRECTORY_DEPTH, context)
        directory_levels = self.parameterAsString(parameters, self.DIRECTORY_LEVELS, context)
        dry_run = self.parameterAsBool(parameters, self.DRY_RUN, context)

        if not input_dir:
            raise QgsProcessingException("Input directory is required")

        if not dry_run and not output_gpkg:
            raise QgsProcessingException("Output GeoPackage is required when not in dry run mode")

        input_path = Path(input_dir)
        if not input_path.exists():
            raise QgsProcessingException(f"Input directory does not exist: {input_dir}")

        feedback.pushInfo(f"Searching for raster files in: {input_dir}")

        # Find all raster files
        raster_files = self._find_raster_files(input_path, raster_types, feedback)

        if not raster_files:
            feedback.pushInfo("No raster files found in the specified directory.")
            return {self.OUTPUT_GPKG: output_gpkg if not dry_run else None}

        feedback.pushInfo(f"Found {len(raster_files)} raster files to process")

        if dry_run:
            # Dry run mode - only generate and display layer names
            return self._perform_dry_run(raster_files, input_path, directory_naming, directory_depth, directory_levels, feedback)

        # TODO: Implement actual raster processing
        feedback.pushInfo("Raster processing implementation coming soon...")

        return {self.OUTPUT_GPKG: output_gpkg}

    def _find_raster_files(self, input_dir: Path, raster_types: list, feedback) -> list:
        """Find all raster files in the directory tree based on selected types."""

        # Define raster file patterns based on selected types
        type_patterns = {
            0: ["*.tif", "*.tiff"],           # GeoTIFF
            1: ["*.img"],                     # ERDAS IMAGINE
            2: ["*.hdr"],                     # ENVI (header files)
            3: ["*.asc"],                     # ASCII Grid
            4: ["*/w001001.adf"],            # ESRI Grid (look for grid directories)
            5: ["*.nc"],                      # NetCDF
            6: ["*.hdf", "*.h4", "*.h5"],    # HDF
            7: ["*.jp2"],                     # JPEG2000
            8: ["*.png"],                     # PNG
            9: ["*.jpg", "*.jpeg"]           # JPEG
        }

        patterns = []
        for raster_type in raster_types:
            if raster_type in type_patterns:
                patterns.extend(type_patterns[raster_type])

        if not patterns:
            return []

        raster_files = []

        # Search for files matching the patterns
        for pattern in patterns:
            if pattern.startswith("*/"):
                # Special case for ESRI Grid - look for specific files in directories
                grid_pattern = pattern[2:]  # Remove "*/"
                for path in input_dir.rglob(grid_pattern):
                    if path.is_file():
                        # For ESRI Grid, add the parent directory as the raster
                        grid_dir = path.parent
                        if grid_dir not in raster_files:
                            raster_files.append(grid_dir)
            else:
                # Regular file pattern matching
                for path in input_dir.rglob(pattern):
                    if path.is_file():
                        raster_files.append(path)

        # Sort by modification time (newest first)
        try:
            raster_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        except (OSError, AttributeError):
            # If we can't get modification time, just sort by path
            raster_files.sort()

        feedback.pushInfo(f"Found {len(raster_files)} raster files matching selected types")

        return raster_files

    def _perform_dry_run(self, raster_files: list, input_root: Path, directory_naming: int,
                        directory_depth: int, directory_levels: str, feedback) -> dict:
        """Perform dry run - generate layer names without processing data."""

        feedback.pushInfo("\n" + "="*80)
        feedback.pushInfo("DRY RUN RESULTS - Layer Name Preview")
        feedback.pushInfo("="*80)
        feedback.pushInfo(f"{'No.':<4} | {'Original Path':<50} | {'Layer Name'}")
        feedback.pushInfo("-" * 90)

        used_layer_names = set()

        for i, raster_file in enumerate(raster_files):
            try:
                # Generate layer name
                base_layer_name = self._generate_directory_aware_name(
                    raster_file, input_root, directory_naming, directory_depth, directory_levels)
                final_layer_name = self._ensure_unique_layer_name(base_layer_name, used_layer_names)

                # Format and display the result
                row_num = f"{i+1:>3}."
                path_display = str(raster_file)
                layer_display = f"{final_layer_name} (raster)"

                # Truncate path if too long
                if len(path_display) > 50:
                    path_display = path_display[:47] + "..."

                feedback.pushInfo(f"{row_num:<4} | {path_display:<50} | {layer_display}")

            except Exception as e:
                feedback.pushInfo(f"Error processing {raster_file}: {str(e)}")
                continue

        feedback.pushInfo("-" * 90)
        feedback.pushInfo(f"Total files that would be processed: {len(raster_files)}")
        feedback.pushInfo(f"Unique layer names generated: {len(used_layer_names)}")

        # Summary by directory naming strategy
        strategy_names = [
            "Filename only (current behavior)",
            "Parent directory + filename",
            "Last N directories + filename",
            "First N directories + filename",
            "Selected levels (specify directory levels)",
            "Smart path (auto-detect important directories)",
            "Full relative path (truncated if needed)"
        ]
        feedback.pushInfo(f"Directory naming strategy: {strategy_names[directory_naming]}")
        if directory_naming == 2 or directory_naming == 3:  # Last N directories or First N directories
            feedback.pushInfo(f"Directory depth: {directory_depth}")
        elif directory_naming == 4:  # Selected levels
            feedback.pushInfo(f"Directory levels: {directory_levels}")

        feedback.pushInfo("\nNote: This was a dry run. No data was processed.")
        feedback.pushInfo("="*80)

        return {self.OUTPUT_GPKG: None}

    def _generate_directory_aware_name(self, raster_path: Path, input_root: Path,
                                     naming_strategy: int, directory_depth: int, directory_levels: str) -> str:
        """Generate layer name incorporating directory structure based on strategy."""

        # Strategy 0: Filename only (current behavior)
        if naming_strategy == 0:
            return self._generate_layer_name(raster_path.stem)

        # Get relative path components for directory-aware naming
        try:
            relative_path = raster_path.relative_to(input_root)
            path_parts = relative_path.parts[:-1]  # Exclude the filename itself
        except ValueError:
            # Fallback if path is not relative to input_root
            path_parts = raster_path.parent.parts

        # Apply strategy-specific logic
        if naming_strategy == 1:  # Parent directory + filename
            return self._parent_directory_strategy(raster_path, path_parts)
        elif naming_strategy == 2:  # Last N directories + filename
            return self._last_n_directories_strategy(raster_path, path_parts, directory_depth)
        elif naming_strategy == 3:  # First N directories + filename
            return self._first_n_directories_strategy(raster_path, path_parts, directory_depth)
        elif naming_strategy == 4:  # Selected levels (specify directory levels)
            return self._selected_levels_strategy(raster_path, path_parts, directory_levels)
        elif naming_strategy == 5:  # Smart path (auto-detect important directories)
            return self._smart_path_strategy(raster_path, path_parts)
        elif naming_strategy == 6:  # Full relative path (truncated if needed)
            return self._full_relative_path_strategy(raster_path, path_parts)
        else:
            # Fallback to filename only
            return self._generate_layer_name(raster_path.stem)

    def _parent_directory_strategy(self, raster_path: Path, path_parts: tuple) -> str:
        """Strategy 1: Parent directory + filename."""
        if path_parts:
            parent_dir = self._sanitize_directory_name(path_parts[-1])
            filename = self._generate_layer_name(raster_path.stem)
            combined = f"{parent_dir}_{filename}"
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(raster_path.stem)

    def _last_n_directories_strategy(self, raster_path: Path, path_parts: tuple, depth: int) -> str:
        """Strategy 2: Last N directories + filename."""
        if path_parts:
            # Take the last N directories
            relevant_parts = path_parts[-depth:] if len(path_parts) >= depth else path_parts
            dir_parts = [self._sanitize_directory_name(part) for part in relevant_parts]
            filename = self._generate_layer_name(raster_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(raster_path.stem)

    def _first_n_directories_strategy(self, raster_path: Path, path_parts: tuple, depth: int) -> str:
        """Strategy 3: First N directories + filename."""
        if path_parts:
            # Take the first N directories from the top-level containing folder
            relevant_parts = path_parts[:depth] if len(path_parts) >= depth else path_parts
            dir_parts = [self._sanitize_directory_name(part) for part in relevant_parts]
            filename = self._generate_layer_name(raster_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(raster_path.stem)

    def _selected_levels_strategy(self, raster_path: Path, path_parts: tuple, directory_levels: str) -> str:
        """Strategy 4: Selected levels (specify directory levels)."""
        if not path_parts:
            return self._generate_layer_name(raster_path.stem)

        try:
            # Parse comma-separated level numbers
            levels = [int(level.strip()) for level in directory_levels.split(',') if level.strip()]
            if not levels:
                # Fallback to filename only if no valid levels provided
                return self._generate_layer_name(raster_path.stem)

            # Filter levels to only include valid indices (0-based)
            valid_levels = [level for level in levels if 0 <= level < len(path_parts)]

            if not valid_levels:
                # No valid levels, fallback to filename only
                return self._generate_layer_name(raster_path.stem)

            # Extract directories at specified levels
            selected_parts = [path_parts[level] for level in sorted(valid_levels)]
            dir_parts = [self._sanitize_directory_name(part) for part in selected_parts]
            filename = self._generate_layer_name(raster_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)

        except (ValueError, IndexError):
            # Fallback to filename only if parsing fails
            return self._generate_layer_name(raster_path.stem)

    def _smart_path_strategy(self, raster_path: Path, path_parts: tuple) -> str:
        """Strategy 5: Smart path (auto-detect important directories)."""
        if not path_parts:
            return self._generate_layer_name(raster_path.stem)

        # Define semantic filters
        skip_patterns = {
            'home', 'user', 'users', 'desktop', 'documents', 'downloads', 'temp', 'tmp',
            'data', 'gis', 'spatial', 'raster', 'rasters', 'files', 'images', 'imagery'
        }

        # Patterns that indicate important directories
        year_pattern = re.compile(r'^(19|20)\d{2}$')  # Years 1900-2099
        quarter_pattern = re.compile(r'^(Q[1-4]|quarter[1-4]|H[12]|half[12])$', re.IGNORECASE)

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
            if quarter_pattern.match(part):
                important_parts.append(part)
                continue

            # Include meaningful project names (length > 2, not just numbers)
            if len(part) > 2 and not part.isdigit():
                important_parts.append(part)

        if important_parts:
            dir_parts = [self._sanitize_directory_name(part) for part in important_parts]
            filename = self._generate_layer_name(raster_path.stem)
            combined = "_".join(dir_parts + [filename])
            return self._generate_layer_name(combined)
        else:
            return self._generate_layer_name(raster_path.stem)

    def _full_relative_path_strategy(self, raster_path: Path, path_parts: tuple) -> str:
        """Strategy 6: Full relative path (truncated if needed)."""
        if not path_parts:
            return self._generate_layer_name(raster_path.stem)

        # Combine all path parts with filename
        dir_parts = [self._sanitize_directory_name(part) for part in path_parts]
        filename = self._generate_layer_name(raster_path.stem)
        combined = "_".join(dir_parts + [filename])
        return self._generate_layer_name(combined)

    def _generate_layer_name(self, name: str) -> str:
        """Generate a clean layer name from input string."""
        # Remove file extensions if any
        clean_name = Path(name).stem

        # Replace invalid characters with underscores
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name)

        # Ensure it doesn't start with a number
        if clean_name and clean_name[0].isdigit():
            clean_name = f"layer_{clean_name}"

        # Remove excessive underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        clean_name = clean_name.strip('_')

        # Ensure minimum length
        if not clean_name:
            clean_name = "raster_layer"

        # Limit to SQLite identifier length (63 characters)
        if len(clean_name) > 63:
            clean_name = clean_name[:63].rstrip('_')

        return clean_name

    def _sanitize_directory_name(self, directory_name: str) -> str:
        """Sanitize directory name using same rules as layer names."""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', directory_name)
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_')

        if not sanitized or sanitized.isdigit():
            sanitized = "dir"

        return sanitized

    def _ensure_unique_layer_name(self, base_name: str, used_names: set) -> str:
        """Ensure layer name is unique by appending numbers if needed."""
        if base_name not in used_names:
            used_names.add(base_name)
            return base_name

        # Try appending incrementing numbers
        counter = 1
        max_attempts = 1000  # Prevent infinite loops

        while counter <= max_attempts:
            # Calculate available space for suffix
            suffix = f"_{counter}"
            max_base_length = 63 - len(suffix)

            if max_base_length <= 0:
                # Name is too long even with minimal suffix
                truncated_base = base_name[:59]  # Leave room for "_999" worst case
                candidate_name = f"{truncated_base}_{counter}"
            else:
                truncated_base = base_name[:max_base_length] if len(base_name) > max_base_length else base_name
                candidate_name = f"{truncated_base}{suffix}"

            if candidate_name not in used_names:
                used_names.add(candidate_name)
                return candidate_name

            counter += 1

        # Fallback if we somehow can't generate a unique name
        import uuid
        fallback_name = f"raster_{str(uuid.uuid4())[:8]}"
        used_names.add(fallback_name)
        return fallback_name