"""
Metadata Wizard Widget - Progressive Disclosure Interface.

Guides users through metadata creation step-by-step.

Author: John Zastrow
License: MIT
"""

__version__ = "0.3.0"

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.PyQt.QtCore import Qt, pyqtSignal
from typing import Optional, Dict, List
import json


class QFlowLayout(QtWidgets.QLayout):
    """Flow layout for keyword tags."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_list = []

    def addItem(self, item):
        self.item_list.append(item)

    def count(self):
        return len(self.item_list)

    def itemAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        return size

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect)

    def doLayout(self, rect):
        """Arrange items in a flow layout."""
        x = rect.x()
        y = rect.y()
        line_height = 0
        space_x = 5
        space_y = 5

        for item in self.item_list:
            if not item.widget():
                continue

            widget_size = item.sizeHint()
            next_x = x + widget_size.width() + space_x

            # Wrap to next line if needed
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + widget_size.width() + space_x
                line_height = 0

            # Place the item
            item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), widget_size))

            x = next_x
            line_height = max(line_height, widget_size.height())


class StepWidget(QtWidgets.QWidget):
    """Base class for wizard steps."""

    def __init__(self, parent=None):
        """Initialize step widget."""
        super().__init__(parent)

    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate step fields.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        return True, []

    def get_data(self) -> Dict:
        """
        Get data from this step.

        Returns:
            Dictionary of field values
        """
        return {}

    def set_data(self, data: Dict):
        """
        Populate step fields from data.

        Args:
            data: Dictionary of field values
        """
        pass

    def is_complete(self) -> bool:
        """
        Check if step has all recommended fields filled.

        Returns:
            True if complete
        """
        is_valid, _ = self.validate()
        return is_valid


class Step1Essential(StepWidget):
    """Step 1: Essential metadata fields."""

    def __init__(self, db_manager, parent=None):
        """Initialize essential fields step."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title_group = QtWidgets.QGroupBox("Step 1: Essential Fields")
        title_layout = QtWidgets.QFormLayout()

        # Title field
        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("e.g., Road Centerlines")
        title_layout.addRow("Title *:", self.title_edit)

        # Abstract field
        self.abstract_edit = QtWidgets.QPlainTextEdit()
        self.abstract_edit.setPlaceholderText(
            "Brief description of the dataset (minimum 10 characters)"
        )
        self.abstract_edit.setMaximumHeight(100)
        title_layout.addRow("Abstract *:", self.abstract_edit)

        # Keywords
        keyword_label = QtWidgets.QLabel("Keywords:")

        # Keyword input
        self.keyword_input = QtWidgets.QLineEdit()
        self.keyword_input.setPlaceholderText("Type keyword and press Enter")
        self.keyword_input.returnPressed.connect(self.add_keyword)
        title_layout.addRow(keyword_label, self.keyword_input)

        # Keyword tags display (separate row for better layout)
        self.keyword_tags = QtWidgets.QWidget()
        self.keyword_tags.setMinimumHeight(40)
        self.keyword_tags.setMaximumHeight(120)  # Limit height with scroll
        self.keyword_tags_layout = QFlowLayout(self.keyword_tags)
        self.keyword_tags_layout.setContentsMargins(5, 5, 5, 5)

        # Scroll area for tags
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(self.keyword_tags)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(50)
        scroll_area.setMaximumHeight(120)
        scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ccc; background: white; }")

        tags_label = QtWidgets.QLabel("  ")  # Indent to align with other fields
        title_layout.addRow(tags_label, scroll_area)

        # Category dropdown
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems([
            "-- Select Category --",
            "Boundaries",
            "Climatology/Meteorology/Atmosphere",
            "Economy",
            "Elevation",
            "Environment",
            "Farming",
            "Geoscientific Information",
            "Health",
            "Imagery/Base Maps/Earth Cover",
            "Intelligence/Military",
            "Inland Waters",
            "Location",
            "Oceans",
            "Planning/Cadastre",
            "Society",
            "Structure",
            "Transportation",
            "Utilities/Communication"
        ])
        title_layout.addRow("Category *:", self.category_combo)

        title_group.setLayout(title_layout)
        layout.addWidget(title_group)

        # Error display
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        layout.addStretch()

        # Store keywords
        self.keywords = []

    def add_keyword(self):
        """Add keyword from input field."""
        keyword = self.keyword_input.text().strip()
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
            self.create_keyword_tag(keyword)
            self.keyword_input.clear()

    def create_keyword_tag(self, keyword: str):
        """Create a removable tag widget for keyword."""
        tag = QtWidgets.QFrame()
        tag.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        tag.setStyleSheet("background-color: lightblue; border-radius: 3px; padding: 2px;")

        tag_layout = QtWidgets.QHBoxLayout(tag)
        tag_layout.setContentsMargins(5, 2, 5, 2)

        label = QtWidgets.QLabel(keyword)
        tag_layout.addWidget(label)

        remove_btn = QtWidgets.QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setStyleSheet("border: none; font-weight: bold;")
        remove_btn.clicked.connect(lambda: self.remove_keyword(keyword, tag))
        tag_layout.addWidget(remove_btn)

        self.keyword_tags_layout.addWidget(tag)

    def remove_keyword(self, keyword: str, tag: QtWidgets.QWidget):
        """Remove keyword tag."""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
        self.keyword_tags_layout.removeWidget(tag)
        tag.deleteLater()

    def validate(self) -> tuple[bool, List[str]]:
        """Validate essential fields."""
        errors = []

        title = self.title_edit.text().strip()
        if not title:
            errors.append("Title is required")

        abstract = self.abstract_edit.toPlainText().strip()
        if not abstract:
            errors.append("Abstract is required")
        elif len(abstract) < 10:
            errors.append("Abstract must be at least 10 characters")

        category = self.category_combo.currentText()
        if category == "-- Select Category --":
            errors.append("Please select a category")

        # Show/hide errors
        if errors:
            self.error_label.setText("Errors:\n• " + "\n• ".join(errors))
            self.error_label.show()
        else:
            self.error_label.hide()

        return len(errors) == 0, errors

    def get_data(self) -> Dict:
        """Get data from essential fields."""
        return {
            'title': self.title_edit.text().strip(),
            'abstract': self.abstract_edit.toPlainText().strip(),
            'keywords': self.keywords.copy(),
            'category': self.category_combo.currentText()
        }

    def set_data(self, data: Dict):
        """Populate essential fields from data."""
        self.title_edit.setText(data.get('title', ''))
        self.abstract_edit.setPlainText(data.get('abstract', ''))

        # Clear and reload keywords
        self.keywords.clear()
        while self.keyword_tags_layout.count():
            item = self.keyword_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for keyword in data.get('keywords', []):
            self.keywords.append(keyword)
            self.create_keyword_tag(keyword)

        category = data.get('category', '')
        index = self.category_combo.findText(category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)


class Step2Common(StepWidget):
    """Step 2: Common metadata fields (contacts, license, constraints)."""

    def __init__(self, db_manager, parent=None):
        """Initialize common fields step."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.contacts = []  # List of contact dicts
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Main scroll area for all fields
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        # Title
        title_group = QtWidgets.QGroupBox("Step 2: Common Fields")
        main_layout = QtWidgets.QVBoxLayout()

        # Contacts section
        contacts_label = QtWidgets.QLabel("<b>Contacts</b> (recommended)")
        main_layout.addWidget(contacts_label)

        # Contacts table
        self.contacts_table = QtWidgets.QTableWidget(0, 3)
        self.contacts_table.setHorizontalHeaderLabels(["Role", "Name", "Organization"])
        self.contacts_table.horizontalHeader().setStretchLastSection(True)
        self.contacts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.contacts_table.setMaximumHeight(150)
        main_layout.addWidget(self.contacts_table)

        # Contact buttons
        contact_btn_layout = QtWidgets.QHBoxLayout()
        self.add_contact_btn = QtWidgets.QPushButton("Add Contact")
        self.add_contact_btn.clicked.connect(self.add_contact)
        contact_btn_layout.addWidget(self.add_contact_btn)

        self.edit_contact_btn = QtWidgets.QPushButton("Edit")
        self.edit_contact_btn.clicked.connect(self.edit_contact)
        self.edit_contact_btn.setEnabled(False)
        contact_btn_layout.addWidget(self.edit_contact_btn)

        self.remove_contact_btn = QtWidgets.QPushButton("Remove")
        self.remove_contact_btn.clicked.connect(self.remove_contact)
        self.remove_contact_btn.setEnabled(False)
        contact_btn_layout.addWidget(self.remove_contact_btn)

        contact_btn_layout.addStretch()
        main_layout.addLayout(contact_btn_layout)

        # Enable/disable edit/remove buttons based on selection
        self.contacts_table.itemSelectionChanged.connect(self.update_contact_buttons)

        main_layout.addSpacing(10)

        # License section
        form_layout = QtWidgets.QFormLayout()

        self.license_combo = QtWidgets.QComboBox()
        self.license_combo.addItems([
            "-- Select License --",
            "Public Domain",
            "CC0-1.0 (Creative Commons Zero)",
            "CC-BY-4.0 (Attribution)",
            "CC-BY-SA-4.0 (Attribution-ShareAlike)",
            "ODbL (Open Database License)",
            "Proprietary",
            "Custom (specify below)"
        ])
        self.license_combo.currentTextChanged.connect(self.license_changed)
        form_layout.addRow("License:", self.license_combo)

        # Custom license text
        self.custom_license_edit = QtWidgets.QLineEdit()
        self.custom_license_edit.setPlaceholderText("Enter custom license text")
        self.custom_license_edit.setEnabled(False)
        form_layout.addRow("  Custom:", self.custom_license_edit)

        # Use constraints
        self.use_constraints_edit = QtWidgets.QPlainTextEdit()
        self.use_constraints_edit.setPlaceholderText(
            "Describe any limitations on use (e.g., 'Attribute City GIS when using this data')"
        )
        self.use_constraints_edit.setMaximumHeight(60)
        form_layout.addRow("Use Constraints:", self.use_constraints_edit)

        # Access constraints
        self.access_constraints_edit = QtWidgets.QPlainTextEdit()
        self.access_constraints_edit.setPlaceholderText(
            "Describe any access restrictions (e.g., 'Public', 'Internal use only')"
        )
        self.access_constraints_edit.setMaximumHeight(60)
        form_layout.addRow("Access Constraints:", self.access_constraints_edit)

        # Language
        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItems([
            "English",
            "Spanish",
            "French",
            "German",
            "Italian",
            "Portuguese",
            "Chinese",
            "Japanese",
            "Other"
        ])
        form_layout.addRow("Language:", self.language_combo)

        # Attribution
        self.attribution_edit = QtWidgets.QLineEdit()
        self.attribution_edit.setPlaceholderText("How to cite this data (e.g., 'City GIS Department, 2025')")
        form_layout.addRow("Attribution:", self.attribution_edit)

        main_layout.addLayout(form_layout)

        title_group.setLayout(main_layout)
        scroll_layout.addWidget(title_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Error display
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: red; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

    def license_changed(self, text):
        """Enable custom license field if Custom is selected."""
        self.custom_license_edit.setEnabled("Custom" in text)

    def update_contact_buttons(self):
        """Enable/disable edit and remove buttons based on selection."""
        has_selection = len(self.contacts_table.selectedItems()) > 0
        self.edit_contact_btn.setEnabled(has_selection)
        self.remove_contact_btn.setEnabled(has_selection)

    def add_contact(self):
        """Show dialog to add a contact."""
        dialog = ContactDialog(self.db_manager, self)
        if dialog.exec_():
            contact = dialog.get_contact()
            self.contacts.append(contact)
            self.refresh_contacts_table()

    def edit_contact(self):
        """Edit selected contact."""
        row = self.contacts_table.currentRow()
        if row < 0:
            return

        contact = self.contacts[row]
        dialog = ContactDialog(self.db_manager, self, contact)
        if dialog.exec_():
            updated_contact = dialog.get_contact()
            self.contacts[row] = updated_contact
            self.refresh_contacts_table()

    def remove_contact(self):
        """Remove selected contact."""
        row = self.contacts_table.currentRow()
        if row < 0:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Remove Contact",
            "Remove this contact?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            del self.contacts[row]
            self.refresh_contacts_table()

    def refresh_contacts_table(self):
        """Refresh the contacts table display."""
        self.contacts_table.setRowCount(len(self.contacts))
        for i, contact in enumerate(self.contacts):
            self.contacts_table.setItem(i, 0, QtWidgets.QTableWidgetItem(contact.get('role', '')))
            self.contacts_table.setItem(i, 1, QtWidgets.QTableWidgetItem(contact.get('name', '')))
            self.contacts_table.setItem(i, 2, QtWidgets.QTableWidgetItem(contact.get('organization', '')))

    def validate(self) -> tuple[bool, List[str]]:
        """Validate common fields."""
        errors = []
        warnings = []

        # Contacts are recommended but not required
        if len(self.contacts) == 0:
            warnings.append("At least one contact is recommended")

        # License is recommended but not required
        license_text = self.license_combo.currentText()
        if license_text == "-- Select License --":
            warnings.append("License information is recommended")

        # Show warnings as info (not blocking)
        if warnings:
            self.error_label.setText("Recommendations:\n• " + "\n• ".join(warnings))
            self.error_label.setStyleSheet("color: orange; font-weight: bold;")
            self.error_label.show()
        else:
            self.error_label.hide()

        return True, errors  # Step 2 has no required fields

    def get_data(self) -> Dict:
        """Get data from common fields."""
        license_text = self.license_combo.currentText()
        if "Custom" in license_text:
            license_text = self.custom_license_edit.text().strip()

        return {
            'contacts': self.contacts.copy(),
            'license': license_text if license_text != "-- Select License --" else "",
            'use_constraints': self.use_constraints_edit.toPlainText().strip(),
            'access_constraints': self.access_constraints_edit.toPlainText().strip(),
            'language': self.language_combo.currentText(),
            'attribution': self.attribution_edit.text().strip()
        }

    def set_data(self, data: Dict):
        """Populate common fields from data."""
        # Contacts
        self.contacts = data.get('contacts', []).copy()
        self.refresh_contacts_table()

        # License
        license_text = data.get('license', '')
        index = self.license_combo.findText(license_text)
        if index >= 0:
            self.license_combo.setCurrentIndex(index)
        elif license_text:
            # Custom license
            self.license_combo.setCurrentText("Custom (specify below)")
            self.custom_license_edit.setText(license_text)

        # Constraints
        self.use_constraints_edit.setPlainText(data.get('use_constraints', ''))
        self.access_constraints_edit.setPlainText(data.get('access_constraints', ''))

        # Language
        language = data.get('language', 'English')
        index = self.language_combo.findText(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        # Attribution
        self.attribution_edit.setText(data.get('attribution', ''))


class ContactDialog(QtWidgets.QDialog):
    """Dialog for adding/editing contact information."""

    def __init__(self, db_manager, parent=None, contact=None):
        """Initialize contact dialog."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.contact = contact or {}
        self.setWindowTitle("Contact Information")
        self.setMinimumWidth(400)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()

        # Role
        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems([
            "Point of Contact",
            "Author",
            "Custodian",
            "Distributor",
            "Originator",
            "Owner",
            "Publisher",
            "User"
        ])
        form_layout.addRow("Role *:", self.role_combo)

        # Name
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Contact name")
        form_layout.addRow("Name *:", self.name_edit)

        # Organization
        self.org_edit = QtWidgets.QLineEdit()
        self.org_edit.setPlaceholderText("Organization name")
        form_layout.addRow("Organization:", self.org_edit)

        # Email
        self.email_edit = QtWidgets.QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.email_edit)

        # Phone
        self.phone_edit = QtWidgets.QLineEdit()
        self.phone_edit.setPlaceholderText("Phone number")
        form_layout.addRow("Phone:", self.phone_edit)

        layout.addLayout(form_layout)

        # Load existing contact data
        if self.contact:
            role = self.contact.get('role', '')
            index = self.role_combo.findText(role)
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
            self.name_edit.setText(self.contact.get('name', ''))
            self.org_edit.setText(self.contact.get('organization', ''))
            self.email_edit.setText(self.contact.get('email', ''))
            self.phone_edit.setText(self.contact.get('phone', ''))

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        """Validate and accept dialog."""
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Required", "Contact name is required")
            return

        super().accept()

    def get_contact(self) -> Dict:
        """Get contact data from dialog."""
        return {
            'role': self.role_combo.currentText(),
            'name': self.name_edit.text().strip(),
            'organization': self.org_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'phone': self.phone_edit.text().strip()
        }


class MetadataWizard(QtWidgets.QWidget):
    """Main metadata wizard widget with progressive disclosure."""

    # Signals
    metadata_saved = pyqtSignal(str, dict)  # layer_path, metadata_dict

    def __init__(self, db_manager, parent=None):
        """
        Initialize metadata wizard.

        Args:
            db_manager: DatabaseManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_layer_path = None
        self.current_step = 0
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Header
        header = QtWidgets.QLabel("<h2>Metadata Editor</h2>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Layer info
        self.layer_label = QtWidgets.QLabel("No layer selected")
        self.layer_label.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(self.layer_label)

        # Progress indicator
        self.progress_widget = self.create_progress_indicator()
        layout.addWidget(self.progress_widget)

        # Step container (stacked widget)
        self.step_container = QtWidgets.QStackedWidget()

        # Create steps
        self.step1 = Step1Essential(self.db_manager, self)
        self.step_container.addWidget(self.step1)

        self.step2 = Step2Common(self.db_manager, self)
        self.step_container.addWidget(self.step2)

        self.step3 = QtWidgets.QLabel("Step 3: Optional Fields\n(Coming next)")
        self.step3.setAlignment(Qt.AlignCenter)
        self.step_container.addWidget(self.step3)

        self.step4 = QtWidgets.QLabel("Step 4: Review & Save\n(Coming next)")
        self.step4.setAlignment(Qt.AlignCenter)
        self.step_container.addWidget(self.step4)

        layout.addWidget(self.step_container)

        # Navigation buttons
        nav_layout = QtWidgets.QHBoxLayout()

        self.skip_btn = QtWidgets.QPushButton("Skip →")
        self.skip_btn.clicked.connect(self.skip_step)
        nav_layout.addWidget(self.skip_btn)

        nav_layout.addStretch()

        self.prev_btn = QtWidgets.QPushButton("← Previous")
        self.prev_btn.clicked.connect(self.previous_step)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QtWidgets.QPushButton("Next →")
        self.next_btn.clicked.connect(self.next_step)
        nav_layout.addWidget(self.next_btn)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save_metadata)
        self.save_btn.setStyleSheet("font-weight: bold;")
        nav_layout.addWidget(self.save_btn)

        layout.addLayout(nav_layout)

    def create_progress_indicator(self) -> QtWidgets.QWidget:
        """Create progress indicator widget."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)

        self.progress_label = QtWidgets.QLabel("Step 1 of 4")
        layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(4)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(10)
        layout.addWidget(self.progress_bar)

        return widget

    def set_layer(self, layer_path: str, layer_name: str):
        """
        Set the layer to edit metadata for.

        Args:
            layer_path: Full path to layer file
            layer_name: Display name of layer
        """
        self.current_layer_path = layer_path
        self.layer_label.setText(f"Layer: {layer_name}")

        # Load existing metadata if available
        self.load_metadata(layer_path)

    def load_metadata(self, layer_path: str):
        """Load existing metadata from cache."""
        # TODO: Query metadata_cache table
        # For now, start with empty fields
        pass

    def next_step(self):
        """Go to next step."""
        # Validate current step
        current_widget = self.step_container.currentWidget()
        if hasattr(current_widget, 'validate'):
            is_valid, errors = current_widget.validate()
            if not is_valid:
                return  # Stay on current step

        # Move to next step
        if self.current_step < 3:
            self.current_step += 1
            self.step_container.setCurrentIndex(self.current_step)
            self.update_navigation()

    def previous_step(self):
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self.step_container.setCurrentIndex(self.current_step)
            self.update_navigation()

    def skip_step(self):
        """Skip current step without validation."""
        if self.current_step < 3:
            self.current_step += 1
            self.step_container.setCurrentIndex(self.current_step)
            self.update_navigation()

    def update_navigation(self):
        """Update navigation button states."""
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < 3)
        self.skip_btn.setEnabled(self.current_step < 3)

        self.progress_label.setText(f"Step {self.current_step + 1} of 4")
        self.progress_bar.setValue(self.current_step + 1)

    def save_metadata(self):
        """Save metadata to cache and target location."""
        if not self.current_layer_path:
            QtWidgets.QMessageBox.warning(
                self,
                "No Layer",
                "Please select a layer first"
            )
            return

        # Collect data from all steps
        metadata = {}
        if hasattr(self.step1, 'get_data'):
            metadata.update(self.step1.get_data())
        if hasattr(self.step2, 'get_data'):
            metadata.update(self.step2.get_data())

        # TODO: Collect from step3 and step4 when implemented

        # Save to database
        # TODO: Implement save_metadata_to_cache method in DatabaseManager

        QtWidgets.QMessageBox.information(
            self,
            "Saved",
            f"Metadata saved for {self.current_layer_path}"
        )

        self.metadata_saved.emit(self.current_layer_path, metadata)
