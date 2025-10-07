"""
Layer Selector Dialog - Select layer from inventory database.

Author: John Zastrow
License: MIT
"""

__version__ = "0.3.0"

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt


class LayerSelectorDialog(QtWidgets.QDialog):
    """Dialog for selecting a layer from the inventory database."""

    def __init__(self, db_manager, parent=None):
        """Initialize layer selector dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.selected_layer_path = None
        self.selected_layer_name = None
        self.selected_layer_format = None
        self.setWindowTitle("Select Layer from Inventory")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setup_ui()
        self.load_layers()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Info label
        info = QtWidgets.QLabel(
            "Select a layer from your inventory database to edit metadata:"
        )
        info.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(info)

        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()

        filter_label = QtWidgets.QLabel("Filter by status:")
        filter_layout.addWidget(filter_label)

        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems([
            "All Layers",
            "Needs Metadata (None)",
            "Partial Metadata",
            "Complete Metadata"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_combo)

        filter_layout.addSpacing(20)

        # Search box
        search_label = QtWidgets.QLabel("Search:")
        filter_layout.addWidget(search_label)

        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search by layer name or path...")
        self.search_box.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.search_box)

        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_layers)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Layers table
        self.layers_table = QtWidgets.QTableWidget(0, 6)
        self.layers_table.setHorizontalHeaderLabels([
            "Layer Name", "File Name", "Status", "Data Type", "Format", "Directory"
        ])
        self.layers_table.horizontalHeader().setStretchLastSection(True)
        self.layers_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.layers_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.layers_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.layers_table.setSortingEnabled(True)

        # Make rows compact
        self.layers_table.verticalHeader().setDefaultSectionSize(20)
        self.layers_table.verticalHeader().setVisible(False)

        # Double-click to select
        self.layers_table.doubleClicked.connect(self.accept)

        layout.addWidget(self.layers_table)

        # Status label
        self.status_label = QtWidgets.QLabel("Loading layers...")
        layout.addWidget(self.status_label)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_layers(self):
        """Load layers from inventory database."""
        if not self.db_manager or not self.db_manager.is_connected:
            self.status_label.setText("⚠ Database not connected")
            return

        try:
            # Query all layers from inventory
            query = """
                SELECT
                    layer_name,
                    file_path,
                    COALESCE(metadata_status, 'none') as status,
                    data_type,
                    format,
                    parent_directory
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                ORDER BY layer_name
            """

            rows = self.db_manager.execute_query(query)

            if rows is None:
                self.status_label.setText("⚠ Error loading layers from inventory")
                return

            # Store all rows for filtering
            self.all_layers = []
            for row in rows:
                # Extract full directory path and file name from file_path
                import os
                file_path = row['file_path']
                directory = os.path.dirname(file_path) if file_path else 'Unknown'
                file_name = os.path.basename(file_path) if file_path else 'Unknown'

                self.all_layers.append({
                    'name': row['layer_name'] or 'Unknown',
                    'path': file_path,
                    'file_name': file_name,
                    'status': row['status'],
                    'data_type': row['data_type'] or 'Unknown',
                    'format': row['format'] or 'Unknown',
                    'directory': directory
                })

            self.apply_filter()

        except Exception as e:
            self.status_label.setText(f"⚠ Error: {str(e)}")

    def apply_filter(self):
        """Apply status filter and search to the table."""
        if not hasattr(self, 'all_layers'):
            return

        filter_text = self.filter_combo.currentText()
        search_text = self.search_box.text().lower()

        # Filter by status
        if filter_text == "Needs Metadata (None)":
            filtered = [l for l in self.all_layers if l['status'] == 'none']
        elif filter_text == "Partial Metadata":
            filtered = [l for l in self.all_layers if l['status'] == 'partial']
        elif filter_text == "Complete Metadata":
            filtered = [l for l in self.all_layers if l['status'] == 'complete']
        else:
            filtered = self.all_layers

        # Filter by search text
        if search_text:
            filtered = [l for l in filtered
                       if search_text in l['name'].lower()
                       or search_text in l['path'].lower()]

        # Update table
        self.layers_table.setSortingEnabled(False)
        self.layers_table.setRowCount(len(filtered))

        for i, layer in enumerate(filtered):
            # Layer name
            self.layers_table.setItem(i, 0, QtWidgets.QTableWidgetItem(layer['name']))

            # File name
            self.layers_table.setItem(i, 1, QtWidgets.QTableWidgetItem(layer['file_name']))

            # Status with color coding
            status_item = QtWidgets.QTableWidgetItem(layer['status'].title())
            if layer['status'] == 'complete':
                status_item.setForeground(QtCore.Qt.darkGreen)
            elif layer['status'] == 'partial':
                status_item.setForeground(QtCore.Qt.darkYellow)
            else:
                status_item.setForeground(QtCore.Qt.red)
            self.layers_table.setItem(i, 2, status_item)

            # Data type
            self.layers_table.setItem(i, 3, QtWidgets.QTableWidgetItem(layer['data_type']))

            # Format
            self.layers_table.setItem(i, 4, QtWidgets.QTableWidgetItem(layer['format']))

            # Directory
            self.layers_table.setItem(i, 5, QtWidgets.QTableWidgetItem(layer['directory']))

            # Store full path and format in row data
            self.layers_table.item(i, 0).setData(Qt.UserRole, layer['path'])
            self.layers_table.item(i, 0).setData(Qt.UserRole + 1, layer['format'])

        self.layers_table.setSortingEnabled(True)

        # Update status
        total = len(self.all_layers)
        showing = len(filtered)
        none_count = sum(1 for l in self.all_layers if l['status'] == 'none')

        self.status_label.setText(
            f"Showing {showing} of {total} layers  |  {none_count} need metadata"
        )

    def accept(self):
        """Accept dialog and store selected layer."""
        current_row = self.layers_table.currentRow()
        if current_row < 0:
            QtWidgets.QMessageBox.warning(
                self,
                "No Selection",
                "Please select a layer from the table"
            )
            return

        # Get layer path and format from selected row
        name_item = self.layers_table.item(current_row, 0)
        self.selected_layer_name = name_item.text()
        self.selected_layer_path = name_item.data(Qt.UserRole)
        self.selected_layer_format = name_item.data(Qt.UserRole + 1)

        super().accept()

    def get_selected_layer(self):
        """
        Get the selected layer.

        Returns:
            Tuple of (layer_path, layer_name, layer_format) or (None, None, None)
        """
        return self.selected_layer_path, self.selected_layer_name, self.selected_layer_format
