"""
Inventory Widget - Create and update geospatial data inventory.

Provides full inventory_miner functionality within the plugin:
- Directory scanning for all geospatial files
- Metadata extraction from multiple sources
- GeoPackage database creation/update
- Progress monitoring and logging

Author: John Zastrow
License: MIT
"""

__version__ = "0.6.0"

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt, pyqtSignal, QThread
from qgis.core import QgsMessageLog, Qgis
from pathlib import Path


class InventoryWidget(QtWidgets.QWidget):
    """
    Widget for creating and updating geospatial data inventory.

    Features:
    - Directory selection and scanning
    - Full inventory_miner algorithm integration
    - Metadata parsing from all sources (FGDC, ESRI, ISO, .qmd, embedded)
    - Progress monitoring with log display
    - Update mode to preserve metadata status
    - Integration with database manager
    """

    # Signals
    inventory_created = pyqtSignal(str, str)  # gpkg_path, layer_name
    inventory_updated = pyqtSignal(str, str)  # gpkg_path, layer_name

    def __init__(self, db_manager, parent=None):
        """Initialize inventory widget."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.runner_thread = None
        self.inventory_runner = None
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Header
        header = QtWidgets.QLabel("Inventory Integration")
        header.setStyleSheet("font-weight: bold; font-size: 14pt; padding: 5px;")
        layout.addWidget(header)

        # Description
        desc = QtWidgets.QLabel(
            "Scan directories for geospatial data and create/update inventory database.\n"
            "This database is used by all other tabs (Dashboard, Layer Browser, Metadata Editor)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("padding: 5px; background-color: #E3F2FD; border-radius: 3px;")
        layout.addWidget(desc)

        # Settings group
        settings_group = QtWidgets.QGroupBox("Inventory Settings")
        settings_layout = QtWidgets.QFormLayout()

        # Directory selection
        dir_layout = QtWidgets.QHBoxLayout()
        self.directory_edit = QtWidgets.QLineEdit()
        self.directory_edit.setPlaceholderText("Select directory to scan...")
        dir_layout.addWidget(self.directory_edit)

        browse_btn = QtWidgets.QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(browse_btn)
        settings_layout.addRow("Scan Directory:", dir_layout)

        # Output database
        db_layout = QtWidgets.QHBoxLayout()
        self.database_edit = QtWidgets.QLineEdit()
        self.database_edit.setPlaceholderText("Output GeoPackage database...")
        db_layout.addWidget(self.database_edit)

        browse_db_btn = QtWidgets.QPushButton("Browse...")
        browse_db_btn.clicked.connect(self.browse_database)
        db_layout.addWidget(browse_db_btn)
        settings_layout.addRow("Output Database:", db_layout)

        # Layer name
        self.layer_name_edit = QtWidgets.QLineEdit("geospatial_inventory")
        settings_layout.addRow("Inventory Layer Name:", self.layer_name_edit)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Options group
        options_group = QtWidgets.QGroupBox("Scan Options")
        options_layout = QtWidgets.QVBoxLayout()

        # Mode selection
        mode_layout = QtWidgets.QHBoxLayout()
        self.create_mode_radio = QtWidgets.QRadioButton("Create New Inventory")
        self.create_mode_radio.setChecked(True)
        mode_layout.addWidget(self.create_mode_radio)

        self.update_mode_radio = QtWidgets.QRadioButton("Update Existing (preserve metadata status)")
        mode_layout.addWidget(self.update_mode_radio)
        options_layout.addLayout(mode_layout)

        # Data type checkboxes
        data_types_layout = QtWidgets.QHBoxLayout()
        self.include_vectors_check = QtWidgets.QCheckBox("Include Vectors")
        self.include_vectors_check.setChecked(True)
        data_types_layout.addWidget(self.include_vectors_check)

        self.include_rasters_check = QtWidgets.QCheckBox("Include Rasters")
        self.include_rasters_check.setChecked(True)
        data_types_layout.addWidget(self.include_rasters_check)

        self.include_tables_check = QtWidgets.QCheckBox("Include Non-Spatial Tables")
        self.include_tables_check.setChecked(True)
        data_types_layout.addWidget(self.include_tables_check)
        options_layout.addLayout(data_types_layout)

        # Processing options
        processing_layout = QtWidgets.QHBoxLayout()
        self.parse_metadata_check = QtWidgets.QCheckBox("Parse GIS Metadata (FGDC, ESRI, ISO, .qmd)")
        self.parse_metadata_check.setChecked(True)
        self.parse_metadata_check.setToolTip(
            "Extract metadata from:\n"
            "- FGDC XML files\n"
            "- ESRI ArcGIS metadata\n"
            "- ISO 19115/19139 XML\n"
            "- QGIS .qmd files\n"
            "- Embedded GeoPackage metadata"
        )
        processing_layout.addWidget(self.parse_metadata_check)

        self.include_sidecar_check = QtWidgets.QCheckBox("Track Sidecar Files")
        self.include_sidecar_check.setChecked(True)
        self.include_sidecar_check.setToolTip(
            "Report presence of:\n"
            "- .prj files\n"
            "- World files (.tfw, .jgw, etc.)\n"
            "- .aux.xml files\n"
            "- Metadata .xml files"
        )
        processing_layout.addWidget(self.include_sidecar_check)

        self.validate_files_check = QtWidgets.QCheckBox("Validate Files (slower)")
        self.validate_files_check.setChecked(False)
        self.validate_files_check.setToolTip(
            "Test that each file can be opened and read.\n"
            "This is slower but catches corrupted files."
        )
        processing_layout.addWidget(self.validate_files_check)
        options_layout.addLayout(processing_layout)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Control buttons
        control_layout = QtWidgets.QHBoxLayout()

        self.run_btn = QtWidgets.QPushButton("▶ Run Inventory Scan")
        self.run_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.run_btn.clicked.connect(self.run_inventory)
        control_layout.addWidget(self.run_btn)

        self.stop_btn = QtWidgets.QPushButton("■ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_inventory)
        control_layout.addWidget(self.stop_btn)

        control_layout.addStretch()

        self.use_current_btn = QtWidgets.QPushButton("Use Current Database")
        self.use_current_btn.setToolTip("Use the currently connected database")
        self.use_current_btn.clicked.connect(self.use_current_database)
        control_layout.addWidget(self.use_current_btn)

        layout.addLayout(control_layout)

        # Progress group
        progress_group = QtWidgets.QGroupBox("Progress")
        progress_layout = QtWidgets.QVBoxLayout()

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QtWidgets.QLabel("Ready to scan")
        self.status_label.setStyleSheet("font-weight: bold;")
        progress_layout.addWidget(self.status_label)

        # Statistics display
        self.stats_label = QtWidgets.QLabel("")
        progress_layout.addWidget(self.stats_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Log display
        log_group = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout()

        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        log_layout.addWidget(self.log_text)

        log_buttons = QtWidgets.QHBoxLayout()
        clear_log_btn = QtWidgets.QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_text.clear)
        log_buttons.addWidget(clear_log_btn)
        log_buttons.addStretch()
        log_layout.addLayout(log_buttons)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()

    def browse_directory(self):
        """Browse for directory to scan."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            self.directory_edit.text() or str(Path.home())
        )
        if directory:
            self.directory_edit.setText(directory)

    def browse_database(self):
        """Browse for output GeoPackage database."""
        database, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Select Output GeoPackage",
            self.database_edit.text() or str(Path.home() / "geospatial_catalog.gpkg"),
            "GeoPackage (*.gpkg)"
        )
        if database:
            self.database_edit.setText(database)

    def use_current_database(self):
        """Use the currently connected database."""
        if self.db_manager and self.db_manager.is_connected:
            self.database_edit.setText(self.db_manager.db_path)
            QtWidgets.QMessageBox.information(
                self,
                "Database Selected",
                f"Using current database:\n{self.db_manager.db_path}"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "No Database Connected",
                "Please connect to a database first in the Dashboard tab."
            )

    def run_inventory(self):
        """Run inventory scan."""
        # Validate inputs
        directory = self.directory_edit.text()
        database = self.database_edit.text()
        layer_name = self.layer_name_edit.text()

        if not directory:
            QtWidgets.QMessageBox.warning(self, "Missing Input", "Please select a directory to scan.")
            return

        if not database:
            QtWidgets.QMessageBox.warning(self, "Missing Input", "Please select an output database.")
            return

        if not layer_name:
            QtWidgets.QMessageBox.warning(self, "Missing Input", "Please enter a layer name.")
            return

        # Check if directory exists
        if not Path(directory).exists():
            QtWidgets.QMessageBox.warning(self, "Invalid Directory", f"Directory does not exist:\n{directory}")
            return

        # Prepare parameters
        params = {
            'directory': directory,
            'output_gpkg': database,
            'layer_name': layer_name,
            'update_mode': self.update_mode_radio.isChecked(),
            'include_vectors': self.include_vectors_check.isChecked(),
            'include_rasters': self.include_rasters_check.isChecked(),
            'include_tables': self.include_tables_check.isChecked(),
            'parse_metadata': self.parse_metadata_check.isChecked(),
            'include_sidecar': self.include_sidecar_check.isChecked(),
            'validate_files': self.validate_files_check.isChecked()
        }

        # Update UI
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        self.log_message("INFO", "Starting inventory scan...")
        self.log_message("INFO", f"Directory: {directory}")
        self.log_message("INFO", f"Database: {database}")
        self.log_message("INFO", f"Mode: {'Update' if params['update_mode'] else 'Create New'}")

        # Import and start inventory runner
        from ..processors.inventory_runner import InventoryRunner

        self.runner_thread = QThread()
        self.inventory_runner = InventoryRunner(params)
        self.inventory_runner.moveToThread(self.runner_thread)

        # Connect signals
        self.runner_thread.started.connect(self.inventory_runner.run)
        self.inventory_runner.progress_updated.connect(self.on_progress_updated)
        self.inventory_runner.status_updated.connect(self.on_status_updated)
        self.inventory_runner.log_message.connect(self.log_message)
        self.inventory_runner.finished.connect(self.on_inventory_finished)
        self.inventory_runner.error.connect(self.on_inventory_error)
        self.inventory_runner.finished.connect(self.runner_thread.quit)
        self.inventory_runner.finished.connect(self.inventory_runner.deleteLater)
        self.runner_thread.finished.connect(self.runner_thread.deleteLater)

        # Start thread
        self.runner_thread.start()

    def stop_inventory(self):
        """Stop inventory scan."""
        if self.inventory_runner:
            self.log_message("WARNING", "Stopping inventory scan...")
            self.inventory_runner.stop()

    def on_progress_updated(self, percent: int):
        """Handle progress update."""
        self.progress_bar.setValue(percent)

    def on_status_updated(self, status: str, stats: dict):
        """Handle status update."""
        self.status_label.setText(status)

        if stats:
            stats_text = f"Files discovered: {stats.get('total', 0)}"
            if stats.get('vectors'):
                stats_text += f" | Vectors: {stats['vectors']}"
            if stats.get('rasters'):
                stats_text += f" | Rasters: {stats['rasters']}"
            if stats.get('tables'):
                stats_text += f" | Tables: {stats['tables']}"
            self.stats_label.setText(stats_text)

    def log_message(self, level: str, message: str):
        """Add message to log display."""
        # Color code by level
        if level == "ERROR" or level == "CRITICAL":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:
            color = "black"

        # Add to log
        timestamp = QtCore.QTime.currentTime().toString("hh:mm:ss")
        html = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{level}:</span> {message}'
        self.log_text.append(html)

        # Also log to QGIS
        qgis_level = Qgis.Info
        if level in ["ERROR", "CRITICAL"]:
            qgis_level = Qgis.Critical
        elif level == "WARNING":
            qgis_level = Qgis.Warning
        QgsMessageLog.logMessage(message, "Metadata Manager - Inventory", qgis_level)

    def on_inventory_finished(self, gpkg_path: str, layer_name: str, stats: dict):
        """Handle inventory completion."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("✓ Inventory complete!")

        # Show summary
        summary = f"Inventory scan complete!\n\n"
        summary += f"Database: {gpkg_path}\n"
        summary += f"Layer: {layer_name}\n\n"
        summary += f"Total records: {stats.get('total', 0)}\n"
        summary += f"Vectors: {stats.get('vectors', 0)}\n"
        summary += f"Rasters: {stats.get('rasters', 0)}\n"
        summary += f"Tables: {stats.get('tables', 0)}\n"

        self.log_message("SUCCESS", "Inventory scan completed successfully!")
        self.log_message("INFO", f"Total records: {stats.get('total', 0)}")

        QtWidgets.QMessageBox.information(self, "Inventory Complete", summary)

        # Emit signal
        self.inventory_created.emit(gpkg_path, layer_name)

    def on_inventory_error(self, error_message: str):
        """Handle inventory error."""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("✗ Error occurred")

        self.log_message("ERROR", f"Inventory scan failed: {error_message}")

        QtWidgets.QMessageBox.critical(
            self,
            "Inventory Error",
            f"An error occurred during inventory scan:\n\n{error_message}"
        )

    def set_database(self, db_manager):
        """
        Set database manager.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        if db_manager and db_manager.is_connected:
            self.database_edit.setText(db_manager.db_path)
