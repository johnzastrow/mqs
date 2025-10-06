"""
Metadata Quality Dashboard Widget.

Displays metadata completion statistics with drill-down capabilities.

Author: John Zastrow
License: MIT
"""

__version__ = "0.2.0"

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.PyQt.QtCore import Qt
from typing import Optional, List, Dict


class DashboardWidget(QtWidgets.QWidget):
    """Dashboard showing metadata quality statistics."""

    def __init__(self, db_manager, parent=None):
        """
        Initialize dashboard widget.

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QtWidgets.QLabel("<h2>Metadata Quality Dashboard</h2>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Database selection section
        db_group = QtWidgets.QGroupBox("Inventory Database")
        db_layout = QtWidgets.QVBoxLayout()

        # Current database display
        db_info_layout = QtWidgets.QHBoxLayout()
        db_info_layout.addWidget(QtWidgets.QLabel("<b>Current Database:</b>"))

        self.db_path_label = QtWidgets.QLabel("No database selected")
        self.db_path_label.setWordWrap(True)
        self.db_path_label.setStyleSheet("padding: 5px; background: #f0f0f0; border: 1px solid #ccc;")
        db_info_layout.addWidget(self.db_path_label, 1)
        db_layout.addLayout(db_info_layout)

        # Database action buttons
        db_btn_layout = QtWidgets.QHBoxLayout()

        select_db_btn = QtWidgets.QPushButton("Select Database...")
        select_db_btn.clicked.connect(self.select_database)
        db_btn_layout.addWidget(select_db_btn)

        refresh_btn = QtWidgets.QPushButton("Refresh Statistics")
        refresh_btn.clicked.connect(self.refresh_statistics)
        db_btn_layout.addWidget(refresh_btn)

        db_btn_layout.addStretch()
        db_layout.addLayout(db_btn_layout)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Overall statistics group
        self.overall_group = self._create_overall_statistics_group()
        layout.addWidget(self.overall_group)

        # Tab widget for drill-down views
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.directory_tab = self._create_drill_down_tab("Directory")
        self.tab_widget.addTab(self.directory_tab, "By Directory")

        self.data_type_tab = self._create_drill_down_tab("Data Type")
        self.tab_widget.addTab(self.data_type_tab, "By Data Type")

        self.file_format_tab = self._create_drill_down_tab("File Format")
        self.tab_widget.addTab(self.file_format_tab, "By File Format")

        self.crs_tab = self._create_drill_down_tab("CRS")
        self.tab_widget.addTab(self.crs_tab, "By CRS")

        # Priority recommendations group
        self.recommendations_group = self._create_recommendations_group()
        layout.addWidget(self.recommendations_group)

        # Stretch to fill space
        layout.addStretch()

    def _create_overall_statistics_group(self) -> QtWidgets.QGroupBox:
        """Create overall statistics group box."""
        group = QtWidgets.QGroupBox("Overall Statistics")
        layout = QtWidgets.QVBoxLayout()

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFormat("%p% Complete")
        layout.addWidget(self.progress_bar)

        # Statistics labels
        self.total_label = QtWidgets.QLabel("Total Layers: -")
        self.complete_label = QtWidgets.QLabel("Complete: -")
        self.partial_label = QtWidgets.QLabel("Partial: -")
        self.none_label = QtWidgets.QLabel("No Metadata: -")

        # Apply styling
        self.complete_label.setStyleSheet("color: green; font-weight: bold;")
        self.partial_label.setStyleSheet("color: orange; font-weight: bold;")
        self.none_label.setStyleSheet("color: red; font-weight: bold;")

        layout.addWidget(self.total_label)
        layout.addWidget(self.complete_label)
        layout.addWidget(self.partial_label)
        layout.addWidget(self.none_label)

        group.setLayout(layout)
        return group

    def _create_drill_down_tab(self, label: str) -> QtWidgets.QWidget:
        """
        Create a drill-down tab widget.

        Args:
            label: Tab label

        Returns:
            QWidget containing table
        """
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Table
        table = QtWidgets.QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([label, "Total", "Complete", "Partial", "None", "% Complete"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        layout.addWidget(table)
        widget.setLayout(layout)

        # Store reference to table for later updates
        setattr(self, f"{label.lower().replace(' ', '_')}_table", table)

        return widget

    def _create_recommendations_group(self) -> QtWidgets.QGroupBox:
        """Create priority recommendations group box."""
        group = QtWidgets.QGroupBox("Priority Recommendations")
        layout = QtWidgets.QVBoxLayout()

        self.recommendations_list = QtWidgets.QListWidget()
        self.recommendations_list.setAlternatingRowColors(True)
        layout.addWidget(self.recommendations_list)

        group.setLayout(layout)
        return group

    def select_database(self):
        """Open file dialog to select inventory database."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Inventory Database (GeoPackage)",
            "",
            "GeoPackage (*.gpkg);;All Files (*.*)"
        )

        if not file_path:
            return

        # Try to connect to selected database
        if not self.db_manager.connect(file_path):
            QtWidgets.QMessageBox.critical(
                self,
                "Connection Failed",
                f"Failed to connect to database:\n{file_path}\n\nCheck the QGIS log for details."
            )
            return

        # Validate it's an inventory database
        is_valid, message = self.db_manager.validate_inventory_database()
        if not is_valid:
            QtWidgets.QMessageBox.critical(
                self,
                "Invalid Database",
                f"This database is not a valid Inventory Miner database:\n\n{message}\n\n"
                f"Please run Inventory Miner first to create the database."
            )
            self.db_manager.disconnect()
            return

        # Check/initialize Metadata Manager tables
        if not self.db_manager.check_metadata_manager_tables_exist():
            reply = QtWidgets.QMessageBox.question(
                self,
                "Initialize Tables",
                "This database doesn't have Metadata Manager tables yet.\n\n"
                "Do you want to initialize them now?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                success, msg = self.db_manager.initialize_metadata_manager_tables()
                if not success:
                    QtWidgets.QMessageBox.critical(
                        self,
                        "Initialization Failed",
                        f"Failed to initialize tables:\n\n{msg}"
                    )
                    self.db_manager.disconnect()
                    return
            else:
                self.db_manager.disconnect()
                return

        # Success! Update UI
        self.update_database_display(file_path)
        self.refresh_statistics()

        # Clear wizard state since database changed
        # (wizard is sibling widget in parent dockwidget)
        if self.parent() and hasattr(self.parent(), 'wizard_widget'):
            if hasattr(self.parent().wizard_widget, 'clear_layer'):
                self.parent().wizard_widget.clear_layer()

        QtWidgets.QMessageBox.information(
            self,
            "Database Connected",
            f"Successfully connected to:\n{file_path}"
        )

    def update_database_display(self, db_path: str = None):
        """
        Update the database path display.

        Args:
            db_path: Database path to display, or None to show current connection
        """
        if db_path is None:
            if self.db_manager and self.db_manager.is_connected and self.db_manager.db_path:
                db_path = self.db_manager.db_path
            else:
                self.db_path_label.setText("No database selected")
                self.db_path_label.setStyleSheet("padding: 5px; background: #ffcccc; border: 1px solid #cc0000;")
                return

        self.db_path_label.setText(db_path)
        self.db_path_label.setStyleSheet("padding: 5px; background: #ccffcc; border: 1px solid #00cc00;")

    def refresh_statistics(self):
        """Refresh all statistics from database."""
        if not self.db_manager or not self.db_manager.is_connected:
            QtWidgets.QMessageBox.warning(
                self,
                "Not Connected",
                "Not connected to database. Please select a database first."
            )
            return

        # Update overall statistics
        self._update_overall_statistics()

        # Update drill-down tables
        self._update_directory_statistics()
        self._update_data_type_statistics()
        self._update_file_format_statistics()
        self._update_crs_statistics()

        # Update recommendations
        self._update_recommendations()

    def _update_overall_statistics(self):
        """Update overall statistics display."""
        stats = self.db_manager.get_inventory_statistics()

        if not stats:
            return

        total = stats.get('total', 0)
        complete = stats.get('complete', 0)
        partial = stats.get('partial', 0)
        none = stats.get('none', 0)

        # Calculate completion percentage
        completion_pct = (complete / total * 100) if total > 0 else 0

        # Update labels
        self.total_label.setText(f"Total Layers: {total}")
        self.complete_label.setText(f"Complete: {complete}")
        self.partial_label.setText(f"Partial: {partial}")
        self.none_label.setText(f"No Metadata: {none}")

        # Update progress bar
        self.progress_bar.setValue(int(completion_pct))

    def _update_directory_statistics(self):
        """Update directory statistics table."""
        stats = self.db_manager.get_statistics_by_directory()
        if stats:
            self._populate_drill_down_table(self.directory_table, stats, 'directory')

    def _update_data_type_statistics(self):
        """Update data type statistics table."""
        stats = self.db_manager.get_statistics_by_data_type()
        if stats:
            self._populate_drill_down_table(self.data_type_table, stats, 'data_type')

    def _update_file_format_statistics(self):
        """Update file format statistics table."""
        stats = self.db_manager.get_statistics_by_file_format()
        if stats:
            self._populate_drill_down_table(self.file_format_table, stats, 'file_format')

    def _update_crs_statistics(self):
        """Update CRS statistics table."""
        stats = self.db_manager.get_statistics_by_crs()
        if stats:
            self._populate_drill_down_table(self.crs_table, stats, 'crs')

    def _populate_drill_down_table(self, table: QtWidgets.QTableWidget,
                                   stats: List[Dict], key_field: str):
        """
        Populate a drill-down table with statistics.

        Args:
            table: QTableWidget to populate
            stats: List of statistics dictionaries
            key_field: Field name for first column
        """
        table.setRowCount(len(stats))

        for row, item in enumerate(stats):
            # First column (category)
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item[key_field])))

            # Total
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item['total'])))

            # Complete
            complete_item = QtWidgets.QTableWidgetItem(str(item['complete']))
            complete_item.setForeground(QtGui.QColor('green'))
            table.setItem(row, 2, complete_item)

            # Partial
            partial_item = QtWidgets.QTableWidgetItem(str(item['partial']))
            partial_item.setForeground(QtGui.QColor('orange'))
            table.setItem(row, 3, partial_item)

            # None
            none_item = QtWidgets.QTableWidgetItem(str(item['none']))
            none_item.setForeground(QtGui.QColor('red'))
            table.setItem(row, 4, none_item)

            # Percentage
            pct_item = QtWidgets.QTableWidgetItem(f"{item['completion_pct']:.1f}%")
            table.setItem(row, 5, pct_item)

        # Resize columns to contents
        table.resizeColumnsToContents()

    def _update_recommendations(self):
        """Update priority recommendations list."""
        recommendations = self.db_manager.get_priority_recommendations()

        self.recommendations_list.clear()

        if not recommendations:
            self.recommendations_list.addItem("No recommendations available")
            return

        for rec in recommendations:
            item = QtWidgets.QListWidgetItem(rec['recommendation'])
            item.setIcon(self._get_priority_icon(rec['count']))
            self.recommendations_list.addItem(item)

    def _get_priority_icon(self, count: int) -> QtGui.QIcon:
        """
        Get priority icon based on count.

        Args:
            count: Number of items needing metadata

        Returns:
            QIcon for priority level
        """
        # Create a simple colored icon
        pixmap = QtGui.QPixmap(16, 16)

        if count > 50:
            pixmap.fill(QtGui.QColor('red'))
        elif count > 20:
            pixmap.fill(QtGui.QColor('orange'))
        else:
            pixmap.fill(QtGui.QColor('yellow'))

        return QtGui.QIcon(pixmap)
