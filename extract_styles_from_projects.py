"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

QGIS Style Extractor from Project Files

Recursively searches directories for QGIS project files (.qgs, .qgz) and
extracts all styles into a single XML style database file.

Version: 0.1.0
"""

__version__ = "0.1.0"

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET
from collections import defaultdict

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean,
)


class StyleExtractorAlgorithm(QgsProcessingAlgorithm):
    """
    Extracts styles from QGIS project files and consolidates them into
    a single XML style database.
    """

    # Parameter constants
    INPUT_DIR = "INPUT_DIR"
    OUTPUT_FILE = "OUTPUT_FILE"
    STYLE_TYPES = "STYLE_TYPES"
    EXTRACT_EMBEDDED = "EXTRACT_EMBEDDED"

    # Style type options
    STYLE_TYPE_OPTIONS = [
        "Symbols",
        "Color Ramps",
        "Text Formats",
        "Label Settings",
        "Legend Patch Shapes",
        "3D Symbols",
    ]

    def name(self) -> str:
        """Algorithm name for identification."""
        return "extractstyles"

    def displayName(self) -> str:
        """User-visible algorithm name."""
        return "Extract Styles from Project Files"

    def group(self) -> str:
        """Group name for organization."""
        return "Style Management"

    def groupId(self) -> str:
        """Group ID for organization."""
        return "stylemanagement"

    def shortHelpString(self) -> str:
        """Short description of the algorithm."""
        return (
            "Recursively searches directories for QGIS project files (.qgs, .qgz) "
            "and extracts all styles into a single XML style database file.\n\n"
            "The output file follows the QGIS style XML format and can be imported "
            "into QGIS Style Manager.\n\n"
            "Parameters:\n"
            "- Input Directory: Top-level directory to search for project files\n"
            "- Output File: Path to save the consolidated styles XML\n"
            "- Style Types: Types of styles to extract (default: all)\n"
            "- Extract from Embedded DBs: Also extract from embedded style databases in .qgz files"
        )

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        """Define algorithm inputs and outputs."""

        # Input directory parameter
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DIR,
                "Input directory to search",
                behavior=QgsProcessingParameterFile.Behavior.Folder,
            )
        )

        # Output file parameter
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                "Output XML file",
                fileFilter="XML files (*.xml)",
            )
        )

        # Style types multi-select parameter
        self.addParameter(
            QgsProcessingParameterEnum(
                self.STYLE_TYPES,
                "Style types to include",
                options=self.STYLE_TYPE_OPTIONS,
                allowMultiple=True,
                defaultValue=list(range(len(self.STYLE_TYPE_OPTIONS))),  # All selected
            )
        )

        # Extract from embedded databases parameter
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.EXTRACT_EMBEDDED,
                "Extract from embedded style databases",
                defaultValue=True,
            )
        )

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        """Main processing logic."""

        # Get parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIR, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)
        style_type_indices = self.parameterAsEnums(parameters, self.STYLE_TYPES, context)
        extract_embedded = self.parameterAsBool(parameters, self.EXTRACT_EMBEDDED, context)

        # Map selected indices to style types
        selected_types = {self.STYLE_TYPE_OPTIONS[i] for i in style_type_indices}

        feedback.pushInfo(f"Searching for project files in: {input_dir}")
        feedback.pushInfo(f"Output file: {output_file}")
        feedback.pushInfo(f"Style types: {', '.join(selected_types)}")
        feedback.pushInfo(f"Extract embedded databases: {extract_embedded}")
        feedback.pushInfo("=" * 60)

        # Find all project files
        project_files = self._find_project_files(input_dir, feedback)

        if not project_files:
            feedback.pushWarning("No QGIS project files found in the specified directory.")
            return {self.OUTPUT_FILE: output_file}

        feedback.pushInfo(f"Found {len(project_files)} project file(s)")
        feedback.pushInfo("")

        # Storage for extracted styles
        extracted_styles = {
            "symbols": [],
            "colorramps": [],
            "textformats": [],
            "labelsettings": [],
            "legendpatchshapes": [],
            "symbols3d": [],
        }

        # Track names for duplicate handling
        name_counters = defaultdict(int)

        # Process each project file
        total_styles = 0
        for idx, project_file in enumerate(project_files):
            if feedback.isCanceled():
                break

            feedback.setProgress(int((idx / len(project_files)) * 100))
            feedback.pushInfo(f"Processing [{idx + 1}/{len(project_files)}]: {project_file}")

            try:
                file_styles = self._extract_from_project(
                    project_file,
                    selected_types,
                    extract_embedded,
                    name_counters,
                    feedback,
                )

                # Merge extracted styles
                for style_type, styles in file_styles.items():
                    extracted_styles[style_type].extend(styles)

                file_total = sum(len(styles) for styles in file_styles.values())
                total_styles += file_total
                feedback.pushInfo(f"  → Extracted {file_total} style(s)")

            except Exception as e:
                feedback.pushWarning(f"  ✗ Error processing file: {str(e)}")
                feedback.pushInfo(f"  → Continuing with next file...")

            feedback.pushInfo("")

        # Generate output XML
        feedback.pushInfo("=" * 60)
        feedback.pushInfo("Generating output XML...")
        self._write_output_xml(extracted_styles, output_file, selected_types, feedback)

        feedback.pushInfo("")
        feedback.pushInfo("=" * 60)
        feedback.pushInfo(f"SUMMARY:")
        feedback.pushInfo(f"  Files processed: {len(project_files)}")
        feedback.pushInfo(f"  Total styles extracted: {total_styles}")
        if "Symbols" in selected_types:
            feedback.pushInfo(f"    - Symbols: {len(extracted_styles['symbols'])}")
        if "Color Ramps" in selected_types:
            feedback.pushInfo(f"    - Color Ramps: {len(extracted_styles['colorramps'])}")
        if "Text Formats" in selected_types:
            feedback.pushInfo(f"    - Text Formats: {len(extracted_styles['textformats'])}")
        if "Label Settings" in selected_types:
            feedback.pushInfo(f"    - Label Settings: {len(extracted_styles['labelsettings'])}")
        if "Legend Patch Shapes" in selected_types:
            feedback.pushInfo(f"    - Legend Patch Shapes: {len(extracted_styles['legendpatchshapes'])}")
        if "3D Symbols" in selected_types:
            feedback.pushInfo(f"    - 3D Symbols: {len(extracted_styles['symbols3d'])}")
        feedback.pushInfo(f"  Output saved to: {output_file}")
        feedback.pushInfo("=" * 60)

        return {self.OUTPUT_FILE: output_file}

    def _find_project_files(self, directory: str, feedback: QgsProcessingFeedback) -> list[str]:
        """Recursively find all QGIS project files in directory."""
        project_files = []

        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.qgs', '.qgz')):
                    project_files.append(os.path.join(root, file))

        return sorted(project_files)

    def _extract_from_project(
        self,
        project_file: str,
        selected_types: set[str],
        extract_embedded: bool,
        name_counters: dict,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, list]:
        """Extract styles from a single project file."""

        styles = {
            "symbols": [],
            "colorramps": [],
            "textformats": [],
            "labelsettings": [],
            "legendpatchshapes": [],
            "symbols3d": [],
        }

        # Handle .qgz files (ZIP archives)
        if project_file.lower().endswith('.qgz'):
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(project_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                    # Find the .qgs file
                    qgs_files = list(Path(temp_dir).glob('*.qgs'))
                    if qgs_files:
                        qgs_file = str(qgs_files[0])
                        styles = self._extract_from_qgs(qgs_file, selected_types, name_counters, feedback)

                    # Extract from embedded .db files if requested
                    if extract_embedded:
                        db_files = list(Path(temp_dir).glob('*.db'))
                        for db_file in db_files:
                            feedback.pushInfo(f"  → Found embedded database: {db_file.name}")
                            # TODO: Extract from SQLite .db files
                            # This would require QgsStyle.importDatabase() or direct SQLite access
        else:
            # Direct .qgs file
            styles = self._extract_from_qgs(project_file, selected_types, name_counters, feedback)

        return styles

    def _extract_from_qgs(
        self,
        qgs_file: str,
        selected_types: set[str],
        name_counters: dict,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, list]:
        """Extract styles from a .qgs XML file."""

        styles = {
            "symbols": [],
            "colorramps": [],
            "textformats": [],
            "labelsettings": [],
            "legendpatchshapes": [],
            "symbols3d": [],
        }

        try:
            tree = ET.parse(qgs_file)
            root = tree.getroot()

            # Extract symbols from layers
            if "Symbols" in selected_types:
                symbols = self._extract_symbols_from_layers(root, name_counters)
                styles["symbols"].extend(symbols)

            # Extract color ramps
            if "Color Ramps" in selected_types:
                colorramps = self._extract_colorramps(root, name_counters)
                styles["colorramps"].extend(colorramps)

            # Extract text formats
            if "Text Formats" in selected_types:
                textformats = self._extract_textformats(root, name_counters)
                styles["textformats"].extend(textformats)

            # Extract label settings
            if "Label Settings" in selected_types:
                labelsettings = self._extract_labelsettings(root, name_counters)
                styles["labelsettings"].extend(labelsettings)

            # Extract legend patch shapes
            if "Legend Patch Shapes" in selected_types:
                legendpatchshapes = self._extract_legendpatchshapes(root, name_counters)
                styles["legendpatchshapes"].extend(legendpatchshapes)

            # Extract 3D symbols
            if "3D Symbols" in selected_types:
                symbols3d = self._extract_symbols3d(root, name_counters)
                styles["symbols3d"].extend(symbols3d)

        except ET.ParseError as e:
            raise QgsProcessingException(f"XML parsing error: {str(e)}")
        except Exception as e:
            raise QgsProcessingException(f"Unexpected error: {str(e)}")

        return styles

    def _extract_symbols_from_layers(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract symbol elements from map layers."""
        symbols = []

        # Find all map layers
        for maplayer in root.findall('.//maplayer'):
            layer_name = maplayer.get('name', 'UnknownLayer')

            # Extract from renderer-v2
            renderer = maplayer.find('.//renderer-v2')
            if renderer is not None:
                # Get symbols from renderer
                for symbol in renderer.findall('.//symbols/symbol'):
                    symbol_copy = self._copy_element(symbol)

                    # Generate meaningful name
                    original_name = symbol.get('name', '')
                    category_label = self._get_category_label(renderer, original_name)

                    if category_label:
                        new_name = f"{layer_name}_{category_label}"
                    else:
                        new_name = f"{layer_name}_{original_name}" if original_name else layer_name

                    # Handle duplicates
                    new_name = self._get_unique_name(new_name, name_counters)
                    symbol_copy.set('name', new_name)

                    symbols.append(symbol_copy)

                # Get source symbol if exists
                source_symbol = renderer.find('.//source-symbol/symbol')
                if source_symbol is not None:
                    symbol_copy = self._copy_element(source_symbol)
                    new_name = self._get_unique_name(f"{layer_name}_source", name_counters)
                    symbol_copy.set('name', new_name)
                    symbols.append(symbol_copy)

        return symbols

    def _get_category_label(self, renderer: ET.Element, symbol_name: str) -> Optional[str]:
        """Get category label for a symbol from categorized renderer."""
        for category in renderer.findall('.//categories/category'):
            if category.get('symbol') == symbol_name:
                label = category.get('label', category.get('value', ''))
                return label.replace(' ', '_') if label else None
        return None

    def _extract_colorramps(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract color ramp elements."""
        colorramps = []

        for colorramp in root.findall('.//colorramp'):
            ramp_copy = self._copy_element(colorramp)
            original_name = colorramp.get('name', 'ColorRamp')
            new_name = self._get_unique_name(original_name, name_counters)
            ramp_copy.set('name', new_name)
            colorramps.append(ramp_copy)

        return colorramps

    def _extract_textformats(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract text format elements."""
        # Text formats are typically embedded in label settings
        # This is a placeholder for future implementation
        return []

    def _extract_labelsettings(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract label settings elements."""
        # Label settings extraction - placeholder for future implementation
        return []

    def _extract_legendpatchshapes(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract legend patch shape elements."""
        # Legend patch shapes - placeholder for future implementation
        return []

    def _extract_symbols3d(self, root: ET.Element, name_counters: dict) -> list[ET.Element]:
        """Extract 3D symbol elements."""
        # 3D symbols - placeholder for future implementation
        return []

    def _copy_element(self, element: ET.Element) -> ET.Element:
        """Create a deep copy of an XML element."""
        return ET.fromstring(ET.tostring(element))

    def _get_unique_name(self, base_name: str, name_counters: dict) -> str:
        """Generate a unique name by appending counter if needed."""
        if base_name not in name_counters:
            name_counters[base_name] = 0
            return base_name
        else:
            name_counters[base_name] += 1
            return f"{base_name}_{name_counters[base_name]}"

    def _write_output_xml(
        self,
        styles: dict[str, list],
        output_file: str,
        selected_types: set[str],
        feedback: QgsProcessingFeedback,
    ):
        """Write extracted styles to output XML file."""

        # Create root element
        root = ET.Element('qgis_style')
        root.set('version', '2')

        # Add DOCTYPE (will be added manually to file)

        # Add symbols section
        if "Symbols" in selected_types:
            if styles["symbols"]:
                symbols_elem = ET.SubElement(root, 'symbols')
                for symbol in styles["symbols"]:
                    symbols_elem.append(symbol)
            else:
                ET.SubElement(root, 'symbols')

        # Add colorramps section
        if "Color Ramps" in selected_types:
            if styles["colorramps"]:
                colorramps_elem = ET.SubElement(root, 'colorramps')
                for ramp in styles["colorramps"]:
                    colorramps_elem.append(ramp)
            else:
                ET.SubElement(root, 'colorramps')

        # Add other sections (empty for now)
        if "Text Formats" in selected_types:
            ET.SubElement(root, 'textformats')

        if "Label Settings" in selected_types:
            ET.SubElement(root, 'labelsettings')

        if "Legend Patch Shapes" in selected_types:
            ET.SubElement(root, 'legendpatchshapes')

        if "3D Symbols" in selected_types:
            ET.SubElement(root, 'symbols3d')

        # Write to file with proper formatting
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE qgis_style>\n')
            tree.write(f, encoding='unicode', xml_declaration=False)

        feedback.pushInfo(f"  ✓ Output written successfully")

    def createInstance(self):
        """Create a new instance of the algorithm."""
        return self.__class__()
