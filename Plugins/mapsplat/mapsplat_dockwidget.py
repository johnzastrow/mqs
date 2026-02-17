"""
MapSplat - Dockable Widget

This module contains the dockable widget that provides the main UI
for layer selection, export options, and triggering exports.
"""

__version__ = "0.1.6"

import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QFileDialog,
    QProgressBar,
    QTextEdit,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSizePolicy,
)

from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsVectorLayer,
    QgsRasterLayer,
    Qgis,
)

from .exporter import MapSplatExporter

# Qt6 compatibility: handle scoped enums
try:
    # Qt6 style
    _ItemIsEnabled = Qt.ItemFlag.ItemIsEnabled
    _UserRole = Qt.ItemDataRole.UserRole
except AttributeError:
    # Qt5 style
    _ItemIsEnabled = Qt.ItemIsEnabled
    _UserRole = Qt.UserRole

try:
    # Qt6 style
    from qgis.PyQt.QtWidgets import QAbstractItemView
    _MultiSelection = QAbstractItemView.SelectionMode.MultiSelection
except (ImportError, AttributeError):
    # Qt5 style
    _MultiSelection = QListWidget.MultiSelection


class MapSplatDockWidget(QDockWidget):
    """Dockable widget for MapSplat plugin."""

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("MapSplat")
        self.setObjectName("MapSplatDockWidget")

        # Create main widget and layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self._setup_ui()
        self.setWidget(self.main_widget)

        # Connect to project layer changes
        QgsProject.instance().layersAdded.connect(self.refresh_layer_list)
        QgsProject.instance().layersRemoved.connect(self.refresh_layer_list)

        # Initial population
        self.refresh_layer_list()

    def _setup_ui(self):
        """Set up the user interface."""
        # ==================== Layer Selection ====================
        layer_group = QGroupBox("Layers to Export")
        layer_layout = QVBoxLayout(layer_group)

        self.layer_list = QListWidget()
        self.layer_list.setSelectionMode(_MultiSelection)
        layer_layout.addWidget(self.layer_list)

        # Select all / none buttons
        btn_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_none = QPushButton("Select None")
        self.btn_select_all.clicked.connect(self._select_all_layers)
        self.btn_select_none.clicked.connect(self._select_no_layers)
        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_select_none)
        layer_layout.addLayout(btn_layout)

        self.main_layout.addWidget(layer_group)

        # ==================== Export Options ====================
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)

        # Export mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("PMTiles mode:"))
        self.combo_export_mode = QComboBox()
        self.combo_export_mode.addItems([
            "Single file (all layers)",
            "Separate files per layer"
        ])
        mode_layout.addWidget(self.combo_export_mode)
        options_layout.addLayout(mode_layout)

        # Style options
        self.chk_export_style = QCheckBox("Export separate style.json")
        self.chk_export_style.setChecked(True)
        options_layout.addWidget(self.chk_export_style)

        # Import style button
        style_import_layout = QHBoxLayout()
        self.btn_import_style = QPushButton("Import style.json...")
        self.btn_import_style.clicked.connect(self._import_style)
        self.lbl_imported_style = QLabel("No style imported")
        self.lbl_imported_style.setStyleSheet("color: gray; font-style: italic;")
        style_import_layout.addWidget(self.btn_import_style)
        style_import_layout.addWidget(self.lbl_imported_style, 1)
        options_layout.addLayout(style_import_layout)

        self.main_layout.addWidget(options_group)

        # ==================== Output Settings ====================
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)

        # Project name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Project name:"))
        self.txt_project_name = QLineEdit()
        self.txt_project_name.setPlaceholderText("my_webmap")
        name_layout.addWidget(self.txt_project_name)
        output_layout.addLayout(name_layout)

        # Output folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Output folder:"))
        self.txt_output_folder = QLineEdit()
        self.txt_output_folder.setPlaceholderText("Select output folder...")
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_output_folder)
        folder_layout.addWidget(self.txt_output_folder, 1)
        folder_layout.addWidget(self.btn_browse)
        output_layout.addLayout(folder_layout)

        self.main_layout.addWidget(output_group)

        # ==================== Export Button ====================
        self.btn_export = QPushButton("Export Web Map")
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
            QPushButton:disabled {
                background-color: #a5d6a7;
            }
        """)
        self.btn_export.clicked.connect(self._do_export)
        self.main_layout.addWidget(self.btn_export)

        # ==================== Progress ====================
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # ==================== Log Area ====================
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(100)
        self.txt_log.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.txt_log)

        self.main_layout.addWidget(log_group)

        # Spacer at bottom
        self.main_layout.addStretch()

        # Store imported style path
        self.imported_style_path = None

    def refresh_layer_list(self):
        """Refresh the layer list from the current project."""
        self.layer_list.clear()

        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            item = QListWidgetItem()

            # Determine layer type icon/prefix
            if isinstance(layer, QgsVectorLayer):
                geom_type = layer.geometryType()
                if geom_type == 0:  # Point
                    prefix = "[Point]"
                elif geom_type == 1:  # Line
                    prefix = "[Line]"
                elif geom_type == 2:  # Polygon
                    prefix = "[Polygon]"
                else:
                    prefix = "[Vector]"
            elif isinstance(layer, QgsRasterLayer):
                prefix = "[Raster]"
            else:
                prefix = "[Other]"
                item.setFlags(item.flags() & ~_ItemIsEnabled)

            item.setText(f"{prefix} {layer.name()}")
            item.setData(_UserRole, layer.id())
            self.layer_list.addItem(item)

        # Auto-populate project name from QGIS project
        project_name = project.baseName()
        if project_name and not self.txt_project_name.text():
            # Clean up name for filesystem
            clean_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
            self.txt_project_name.setText(clean_name)

    def _select_all_layers(self):
        """Select all layers in the list."""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item.flags() & _ItemIsEnabled:
                item.setSelected(True)

    def _select_no_layers(self):
        """Deselect all layers."""
        self.layer_list.clearSelection()

    def _browse_output_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.txt_output_folder.text() or os.path.expanduser("~")
        )
        if folder:
            self.txt_output_folder.setText(folder)

    def _import_style(self):
        """Import an existing style.json file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import MapLibre Style JSON",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.imported_style_path = file_path
            basename = os.path.basename(file_path)
            self.lbl_imported_style.setText(f"Imported: {basename}")
            self.lbl_imported_style.setStyleSheet("color: green;")
            self._log(f"Imported style: {file_path}")

    def _log(self, message, level="info"):
        """Add a message to the log area.

        :param message: Message to log
        :param level: Log level (info, warning, error, success)
        """
        color_map = {
            "info": "black",
            "warning": "orange",
            "error": "red",
            "success": "green",
        }
        color = color_map.get(level, "black")
        self.txt_log.append(f'<span style="color:{color}">{message}</span>')

    def _validate_export(self):
        """Validate export settings before proceeding.

        :returns: True if valid, False otherwise
        """
        # Check layers selected
        selected_items = self.layer_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Layers", "Please select at least one layer to export.")
            return False

        # Check output folder
        output_folder = self.txt_output_folder.text().strip()
        if not output_folder:
            QMessageBox.warning(self, "No Output Folder", "Please select an output folder.")
            return False

        if not os.path.isdir(output_folder):
            QMessageBox.warning(self, "Invalid Folder", "The output folder does not exist.")
            return False

        # Check project name
        project_name = self.txt_project_name.text().strip()
        if not project_name:
            QMessageBox.warning(self, "No Project Name", "Please enter a project name.")
            return False

        return True

    def _do_export(self):
        """Perform the export."""
        if not self._validate_export():
            return

        self.txt_log.clear()
        self._log("Starting export...", "info")

        # Gather selected layers
        selected_layer_ids = []
        for item in self.layer_list.selectedItems():
            layer_id = item.data(_UserRole)
            selected_layer_ids.append(layer_id)

        # Gather settings
        settings = {
            "layer_ids": selected_layer_ids,
            "output_folder": self.txt_output_folder.text().strip(),
            "project_name": self.txt_project_name.text().strip(),
            "single_file": self.combo_export_mode.currentIndex() == 0,
            "export_style_json": self.chk_export_style.isChecked(),
            "imported_style_path": self.imported_style_path,
        }

        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_export.setEnabled(False)

        try:
            exporter = MapSplatExporter(self.iface, settings)
            exporter.progress.connect(self._on_progress)
            exporter.log_message.connect(self._on_log_message)
            exporter.finished.connect(self._on_export_finished)
            exporter.run()
        except Exception as e:
            self._log(f"Export failed: {str(e)}", "error")
            self.btn_export.setEnabled(True)
            self.progress_bar.setVisible(False)

    def _on_progress(self, value):
        """Handle progress updates."""
        self.progress_bar.setValue(value)

    def _on_log_message(self, message, level):
        """Handle log messages from exporter."""
        self._log(message, level)

    def _on_export_finished(self, success, output_path):
        """Handle export completion."""
        self.progress_bar.setVisible(False)
        self.btn_export.setEnabled(True)

        if success:
            self._log(f"Export complete: {output_path}", "success")
            QMessageBox.information(
                self,
                "Export Complete",
                f"Web map exported successfully to:\n{output_path}"
            )
        else:
            self._log("Export failed.", "error")

    def closeEvent(self, event):
        """Handle close event."""
        self.closingPlugin.emit()
        event.accept()
