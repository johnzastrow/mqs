"""
Layer List Widget - Browse and navigate layers from inventory.

Embedded widget (not dialog) with filtering, sorting, and Next/Previous navigation.

Author: John Zastrow
License: MIT
"""

__version__ = "0.4.0"

from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtCore import Qt, pyqtSignal


class LayerListWidget(QtWidgets.QWidget):
    """
    Widget for browsing layers from inventory with navigation.

    Features:
    - Filter by metadata status
    - Search by name/path
    - Next/Previous navigation
    - Position indicator
    - Auto-save before navigation
    """

    # Signals
    layer_selected = pyqtSignal(str, str, str)  # layer_path, layer_name, format
    next_layer_requested = pyqtSignal()  # Triggers save before moving to next
    previous_layer_requested = pyqtSignal()  # Triggers save before moving to previous

    def __init__(self, db_manager, parent=None):
        """Initialize layer list widget."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.all_layers = []
        self.filtered_layers = []
        self.current_layer_index = -1
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header - compact
        header = QtWidgets.QLabel("<b>Layer Browser</b>")
        layout.addWidget(header)

        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()

        filter_label = QtWidgets.QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.addItems([
            "All Layers",
            "Needs Metadata",
            "Partial Metadata",
            "Complete Metadata"
        ])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_combo)

        # Search box
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search...")
        self.search_box.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.search_box)

        refresh_btn = QtWidgets.QPushButton("↻")
        refresh_btn.setMaximumWidth(30)
        refresh_btn.setToolTip("Refresh layer list")
        refresh_btn.clicked.connect(self.load_layers)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Layers table
        self.layers_table = QtWidgets.QTableWidget(0, 5)
        self.layers_table.setHorizontalHeaderLabels([
            "Layer Name", "Status", "Data Type", "Format", "Directory"
        ])
        self.layers_table.horizontalHeader().setStretchLastSection(True)
        self.layers_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.layers_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.layers_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.layers_table.setSortingEnabled(True)

        # Compact rows
        self.layers_table.verticalHeader().setDefaultSectionSize(18)
        self.layers_table.verticalHeader().setVisible(False)

        # Selection change
        self.layers_table.itemSelectionChanged.connect(self.on_selection_changed)

        # Double-click to select
        self.layers_table.doubleClicked.connect(self.emit_layer_selected)

        layout.addWidget(self.layers_table)

        # Navigation controls
        nav_layout = QtWidgets.QHBoxLayout()

        # Position indicator
        self.position_label = QtWidgets.QLabel("No layer selected")
        self.position_label.setStyleSheet("font-weight: bold;")
        nav_layout.addWidget(self.position_label)

        nav_layout.addStretch()

        # Previous button
        self.prev_btn = QtWidgets.QPushButton("← Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.previous_layer)
        nav_layout.addWidget(self.prev_btn)

        # Next button
        self.next_btn = QtWidgets.QPushButton("Next →")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_layer)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # Status label
        self.status_label = QtWidgets.QLabel("Click 'Refresh' to load layers")
        layout.addWidget(self.status_label)

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

            # Store all rows
            self.all_layers = []
            for row in rows:
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
        if filter_text == "Needs Metadata":
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

        self.filtered_layers = filtered

        # Update table
        self.update_table()

        # Update status
        total = len(self.all_layers)
        showing = len(filtered)
        none_count = sum(1 for l in self.all_layers if l['status'] == 'none')

        self.status_label.setText(
            f"Showing {showing} of {total} layers  |  {none_count} need metadata"
        )

    def update_table(self):
        """Update table with filtered layers."""
        self.layers_table.setSortingEnabled(False)
        self.layers_table.setRowCount(len(self.filtered_layers))

        for i, layer in enumerate(self.filtered_layers):
            # Layer name
            self.layers_table.setItem(i, 0, QtWidgets.QTableWidgetItem(layer['name']))

            # Status with color coding
            status_item = QtWidgets.QTableWidgetItem(layer['status'].title())
            if layer['status'] == 'complete':
                status_item.setForeground(QtCore.Qt.darkGreen)
            elif layer['status'] == 'partial':
                status_item.setForeground(QtCore.Qt.darkYellow)
            else:
                status_item.setForeground(QtCore.Qt.red)
            self.layers_table.setItem(i, 1, status_item)

            # Data type
            self.layers_table.setItem(i, 2, QtWidgets.QTableWidgetItem(layer['data_type']))

            # Format
            self.layers_table.setItem(i, 3, QtWidgets.QTableWidgetItem(layer['format']))

            # Directory
            self.layers_table.setItem(i, 4, QtWidgets.QTableWidgetItem(layer['directory']))

            # Store full path and format in row data
            self.layers_table.item(i, 0).setData(Qt.UserRole, layer['path'])
            self.layers_table.item(i, 0).setData(Qt.UserRole + 1, layer['format'])

        self.layers_table.setSortingEnabled(True)

        # Clear selection and index
        self.current_layer_index = -1
        self.update_navigation_buttons()

    def on_selection_changed(self):
        """Handle selection change in table."""
        current_row = self.layers_table.currentRow()
        if current_row >= 0:
            self.current_layer_index = current_row
            self.update_navigation_buttons()
            # Don't auto-emit on selection, wait for user action

    def emit_layer_selected(self):
        """Emit signal for selected layer."""
        current_row = self.layers_table.currentRow()
        if current_row < 0:
            return

        # Get layer info from selected row
        name_item = self.layers_table.item(current_row, 0)
        layer_name = name_item.text()
        layer_path = name_item.data(Qt.UserRole)
        layer_format = name_item.data(Qt.UserRole + 1)

        self.current_layer_index = current_row
        self.update_navigation_buttons()

        # Emit signal
        self.layer_selected.emit(layer_path, layer_name, layer_format)

    def next_layer(self):
        """Navigate to next layer in filtered list."""
        if self.current_layer_index < len(self.filtered_layers) - 1:
            # Emit signal to trigger save before navigation
            self.next_layer_requested.emit()

            # Move to next layer
            self.current_layer_index += 1
            self.select_layer_at_index(self.current_layer_index)

    def previous_layer(self):
        """Navigate to previous layer in filtered list."""
        if self.current_layer_index > 0:
            # Emit signal to trigger save before navigation
            self.previous_layer_requested.emit()

            # Move to previous layer
            self.current_layer_index -= 1
            self.select_layer_at_index(self.current_layer_index)

    def select_layer_at_index(self, index: int):
        """
        Select layer at given index in filtered list.

        Args:
            index: Index in filtered_layers list
        """
        if 0 <= index < len(self.filtered_layers):
            # Select row in table
            self.layers_table.selectRow(index)

            # Get layer info
            layer = self.filtered_layers[index]

            # Emit signal
            self.layer_selected.emit(layer['path'], layer['name'], layer['format'])

            # Update navigation
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        """Update navigation buttons and position label."""
        if self.current_layer_index >= 0 and self.filtered_layers:
            # Enable/disable buttons
            self.prev_btn.setEnabled(self.current_layer_index > 0)
            self.next_btn.setEnabled(self.current_layer_index < len(self.filtered_layers) - 1)

            # Update position label
            position = self.current_layer_index + 1
            total = len(self.filtered_layers)
            self.position_label.setText(f"Layer {position} of {total}")
        else:
            # No selection
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.position_label.setText("No layer selected")

    def get_current_layer(self):
        """
        Get currently selected layer.

        Returns:
            Tuple of (layer_path, layer_name, layer_format) or (None, None, None)
        """
        if 0 <= self.current_layer_index < len(self.filtered_layers):
            layer = self.filtered_layers[self.current_layer_index]
            return layer['path'], layer['name'], layer['format']
        return None, None, None

    def set_database(self, db_manager):
        """
        Set database manager and refresh layer list.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        if db_manager and db_manager.is_connected:
            self.load_layers()
        else:
            self.all_layers = []
            self.filtered_layers = []
            self.update_table()
            self.status_label.setText("⚠ Database not connected")
