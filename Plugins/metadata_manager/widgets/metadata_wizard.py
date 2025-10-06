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

from .layer_selector_dialog import LayerSelectorDialog


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

    def clear_data(self):
        """Clear all fields."""
        self.title_edit.clear()
        self.abstract_edit.clear()
        self.keywords.clear()

        # Remove all keyword tags
        while self.keyword_tags_layout.count():
            item = self.keyword_tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Reset category to first item (usually empty/Select)
        self.category_combo.setCurrentIndex(0)


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
        # Make rows more compact
        self.contacts_table.verticalHeader().setDefaultSectionSize(18)
        self.contacts_table.verticalHeader().setVisible(False)
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

    def clear_data(self):
        """Clear all fields."""
        self.contacts.clear()
        self.refresh_contacts_table()
        self.license_combo.setCurrentIndex(0)
        self.custom_license_edit.clear()
        self.use_constraints_edit.clear()
        self.access_constraints_edit.clear()
        # Reset language to English (index 0)
        self.language_combo.setCurrentIndex(0)
        self.attribution_edit.clear()


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


class Step3Optional(StepWidget):
    """Step 3: Optional metadata fields (lineage, links, updates)."""

    def __init__(self, db_manager, parent=None):
        """Initialize optional fields step."""
        super().__init__(parent)
        self.db_manager = db_manager
        self.links = []  # List of link dicts
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
        title_group = QtWidgets.QGroupBox("Step 3: Optional Fields")
        main_layout = QtWidgets.QVBoxLayout()

        form_layout = QtWidgets.QFormLayout()

        # Lineage
        self.lineage_edit = QtWidgets.QPlainTextEdit()
        self.lineage_edit.setPlaceholderText(
            "Describe the data processing history and sources (e.g., 'Digitized from 2024 aerial imagery at 1:2400 scale')"
        )
        self.lineage_edit.setMaximumHeight(70)
        form_layout.addRow("Lineage:", self.lineage_edit)

        # Purpose
        self.purpose_edit = QtWidgets.QPlainTextEdit()
        self.purpose_edit.setPlaceholderText(
            "Why was this data created? (e.g., 'Support emergency services routing and planning')"
        )
        self.purpose_edit.setMaximumHeight(60)
        form_layout.addRow("Purpose:", self.purpose_edit)

        # Supplemental info
        self.supplemental_edit = QtWidgets.QPlainTextEdit()
        self.supplemental_edit.setPlaceholderText(
            "Any additional information about the dataset"
        )
        self.supplemental_edit.setMaximumHeight(60)
        form_layout.addRow("Supplemental Info:", self.supplemental_edit)

        main_layout.addLayout(form_layout)
        main_layout.addSpacing(10)

        # Links section
        links_label = QtWidgets.QLabel("<b>Links</b> (optional)")
        main_layout.addWidget(links_label)

        # Links table
        self.links_table = QtWidgets.QTableWidget(0, 3)
        self.links_table.setHorizontalHeaderLabels(["Name", "URL", "Type"])
        self.links_table.horizontalHeader().setStretchLastSection(True)
        self.links_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.links_table.setMaximumHeight(120)
        # Make rows compact
        self.links_table.verticalHeader().setDefaultSectionSize(18)
        self.links_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.links_table)

        # Link buttons
        link_btn_layout = QtWidgets.QHBoxLayout()
        self.add_link_btn = QtWidgets.QPushButton("Add Link")
        self.add_link_btn.clicked.connect(self.add_link)
        link_btn_layout.addWidget(self.add_link_btn)

        self.edit_link_btn = QtWidgets.QPushButton("Edit")
        self.edit_link_btn.clicked.connect(self.edit_link)
        self.edit_link_btn.setEnabled(False)
        link_btn_layout.addWidget(self.edit_link_btn)

        self.remove_link_btn = QtWidgets.QPushButton("Remove")
        self.remove_link_btn.clicked.connect(self.remove_link)
        self.remove_link_btn.setEnabled(False)
        link_btn_layout.addWidget(self.remove_link_btn)

        link_btn_layout.addStretch()
        main_layout.addLayout(link_btn_layout)

        # Enable/disable edit/remove buttons based on selection
        self.links_table.itemSelectionChanged.connect(self.update_link_buttons)

        main_layout.addSpacing(10)

        # Additional metadata
        form_layout2 = QtWidgets.QFormLayout()

        # Update frequency
        self.update_freq_combo = QtWidgets.QComboBox()
        self.update_freq_combo.addItems([
            "Unknown",
            "As Needed",
            "Continually",
            "Daily",
            "Weekly",
            "Fortnightly",
            "Monthly",
            "Quarterly",
            "Biannually",
            "Annually",
            "Not Planned"
        ])
        form_layout2.addRow("Update Frequency:", self.update_freq_combo)

        # Spatial resolution
        self.spatial_res_edit = QtWidgets.QLineEdit()
        self.spatial_res_edit.setPlaceholderText("e.g., '1:24000' or '10 meters'")
        form_layout2.addRow("Spatial Resolution:", self.spatial_res_edit)

        main_layout.addLayout(form_layout2)

        title_group.setLayout(main_layout)
        scroll_layout.addWidget(title_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Error display (optional fields have no errors)
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("color: blue; font-weight: bold;")
        self.error_label.setWordWrap(True)
        self.error_label.setText("All fields in this step are optional")
        layout.addWidget(self.error_label)

    def update_link_buttons(self):
        """Enable/disable edit and remove buttons based on selection."""
        has_selection = len(self.links_table.selectedItems()) > 0
        self.edit_link_btn.setEnabled(has_selection)
        self.remove_link_btn.setEnabled(has_selection)

    def add_link(self):
        """Show dialog to add a link."""
        dialog = LinkDialog(self)
        if dialog.exec_():
            link = dialog.get_link()
            self.links.append(link)
            self.refresh_links_table()

    def edit_link(self):
        """Edit selected link."""
        row = self.links_table.currentRow()
        if row < 0:
            return

        link = self.links[row]
        dialog = LinkDialog(self, link)
        if dialog.exec_():
            updated_link = dialog.get_link()
            self.links[row] = updated_link
            self.refresh_links_table()

    def remove_link(self):
        """Remove selected link."""
        row = self.links_table.currentRow()
        if row < 0:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Remove Link",
            "Remove this link?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            del self.links[row]
            self.refresh_links_table()

    def refresh_links_table(self):
        """Refresh the links table display."""
        self.links_table.setRowCount(len(self.links))
        for i, link in enumerate(self.links):
            self.links_table.setItem(i, 0, QtWidgets.QTableWidgetItem(link.get('name', '')))
            self.links_table.setItem(i, 1, QtWidgets.QTableWidgetItem(link.get('url', '')))
            self.links_table.setItem(i, 2, QtWidgets.QTableWidgetItem(link.get('type', '')))

    def validate(self) -> tuple[bool, List[str]]:
        """Validate optional fields."""
        # All fields are optional, so always valid
        return True, []

    def get_data(self) -> Dict:
        """Get data from optional fields."""
        return {
            'lineage': self.lineage_edit.toPlainText().strip(),
            'purpose': self.purpose_edit.toPlainText().strip(),
            'supplemental_info': self.supplemental_edit.toPlainText().strip(),
            'links': self.links.copy(),
            'update_frequency': self.update_freq_combo.currentText(),
            'spatial_resolution': self.spatial_res_edit.text().strip()
        }

    def set_data(self, data: Dict):
        """Populate optional fields from data."""
        # Text fields
        self.lineage_edit.setPlainText(data.get('lineage', ''))
        self.purpose_edit.setPlainText(data.get('purpose', ''))
        self.supplemental_edit.setPlainText(data.get('supplemental_info', ''))

        # Links
        self.links = data.get('links', []).copy()
        self.refresh_links_table()

        # Update frequency
        update_freq = data.get('update_frequency', 'Unknown')
        index = self.update_freq_combo.findText(update_freq)
        if index >= 0:
            self.update_freq_combo.setCurrentIndex(index)

        # Spatial resolution
        self.spatial_res_edit.setText(data.get('spatial_resolution', ''))

    def clear_data(self):
        """Clear all fields."""
        self.lineage_edit.clear()
        self.purpose_edit.clear()
        self.supplemental_edit.clear()
        self.links.clear()
        self.refresh_links_table()
        # Reset to Unknown (index 0)
        self.update_freq_combo.setCurrentIndex(0)
        self.spatial_res_edit.clear()


class LinkDialog(QtWidgets.QDialog):
    """Dialog for adding/editing link information."""

    def __init__(self, parent=None, link=None):
        """Initialize link dialog."""
        super().__init__(parent)
        self.link = link or {}
        self.setWindowTitle("Link Information")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QFormLayout()

        # Name
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Descriptive name for the link")
        form_layout.addRow("Name *:", self.name_edit)

        # URL
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        form_layout.addRow("URL *:", self.url_edit)

        # Type
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems([
            "Homepage",
            "Download",
            "Documentation",
            "Web Service",
            "REST API",
            "WMS Service",
            "WFS Service",
            "Metadata",
            "Related",
            "Other"
        ])
        form_layout.addRow("Type:", self.type_combo)

        # Description
        self.description_edit = QtWidgets.QPlainTextEdit()
        self.description_edit.setPlaceholderText("Brief description of this link")
        self.description_edit.setMaximumHeight(60)
        form_layout.addRow("Description:", self.description_edit)

        layout.addLayout(form_layout)

        # Load existing link data
        if self.link:
            self.name_edit.setText(self.link.get('name', ''))
            self.url_edit.setText(self.link.get('url', ''))
            link_type = self.link.get('type', 'Homepage')
            index = self.type_combo.findText(link_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
            self.description_edit.setPlainText(self.link.get('description', ''))

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
        url = self.url_edit.text().strip()

        if not name:
            QtWidgets.QMessageBox.warning(self, "Required", "Link name is required")
            return
        if not url:
            QtWidgets.QMessageBox.warning(self, "Required", "URL is required")
            return

        super().accept()

    def get_link(self) -> Dict:
        """Get link data from dialog."""
        return {
            'name': self.name_edit.text().strip(),
            'url': self.url_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'description': self.description_edit.toPlainText().strip()
        }


class Step4Review(StepWidget):
    """Step 4: Review and save metadata."""

    def __init__(self, wizard, parent=None):
        """Initialize review step."""
        super().__init__(parent)
        self.wizard = wizard
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title_group = QtWidgets.QGroupBox("Step 4: Review & Save")
        main_layout = QtWidgets.QVBoxLayout()

        # Status indicator
        self.status_label = QtWidgets.QLabel()
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Summary display (scrollable)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)

        self.summary_text = QtWidgets.QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("background-color: #f5f5f5; font-family: monospace;")

        scroll.setWidget(self.summary_text)
        main_layout.addWidget(scroll)

        # Instructions
        instructions = QtWidgets.QLabel(
            "<i>Review your metadata below. Click 'Save' to write metadata to the cache, "
            "or click 'Previous' to make changes.</i>"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; padding: 10px;")
        main_layout.addWidget(instructions)

        title_group.setLayout(main_layout)
        layout.addWidget(title_group)

    def refresh_summary(self, metadata: Dict):
        """
        Refresh the summary display with current metadata.

        Args:
            metadata: Dictionary of all metadata from steps 1-3
        """
        # Determine completeness
        is_complete = self.check_completeness(metadata)

        if is_complete:
            self.status_label.setText("✓ Metadata Complete")
            self.status_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #d4edda; color: #155724; border-radius: 5px;"
            )
        else:
            self.status_label.setText("⚠ Metadata Partial")
            self.status_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #fff3cd; color: #856404; border-radius: 5px;"
            )

        # Build summary text
        summary = self.build_summary(metadata)
        self.summary_text.setHtml(summary)

    def check_completeness(self, metadata: Dict) -> bool:
        """
        Check if metadata is complete.

        Args:
            metadata: Dictionary of all metadata

        Returns:
            True if complete (required + recommended fields filled)
        """
        # Required fields (Step 1)
        if not metadata.get('title'):
            return False
        if not metadata.get('abstract') or len(metadata.get('abstract', '')) < 10:
            return False
        if not metadata.get('category') or metadata.get('category') == "-- Select Category --":
            return False

        # Recommended fields (Step 2)
        if not metadata.get('contacts') or len(metadata.get('contacts', [])) == 0:
            return False
        if not metadata.get('license'):
            return False

        return True

    def build_summary(self, metadata: Dict) -> str:
        """
        Build HTML summary of metadata.

        Args:
            metadata: Dictionary of all metadata

        Returns:
            HTML string for display
        """
        html = "<html><body style='font-family: sans-serif;'>"

        # Step 1: Essential Fields
        html += "<h3 style='color: #0066cc; border-bottom: 2px solid #0066cc;'>Essential Fields</h3>"
        html += f"<p><b>Title:</b> {self._escape(metadata.get('title', '<i>Not provided</i>'))}</p>"
        html += f"<p><b>Abstract:</b><br>{self._escape(metadata.get('abstract', '<i>Not provided</i>'))}</p>"

        keywords = metadata.get('keywords', [])
        if keywords:
            html += f"<p><b>Keywords:</b> {', '.join(self._escape(k) for k in keywords)}</p>"
        else:
            html += "<p><b>Keywords:</b> <i>None</i></p>"

        html += f"<p><b>Category:</b> {self._escape(metadata.get('category', '<i>Not selected</i>'))}</p>"

        # Step 2: Common Fields
        html += "<h3 style='color: #0066cc; border-bottom: 2px solid #0066cc; margin-top: 20px;'>Common Fields</h3>"

        contacts = metadata.get('contacts', [])
        if contacts:
            html += "<p><b>Contacts:</b></p><ul>"
            for contact in contacts:
                role = contact.get('role', '')
                name = contact.get('name', '')
                org = contact.get('organization', '')
                html += f"<li>{self._escape(role)}: {self._escape(name)}"
                if org:
                    html += f" ({self._escape(org)})"
                html += "</li>"
            html += "</ul>"
        else:
            html += "<p><b>Contacts:</b> <i>None</i></p>"

        html += f"<p><b>License:</b> {self._escape(metadata.get('license', '<i>Not specified</i>'))}</p>"

        if metadata.get('use_constraints'):
            html += f"<p><b>Use Constraints:</b><br>{self._escape(metadata.get('use_constraints'))}</p>"

        if metadata.get('access_constraints'):
            html += f"<p><b>Access Constraints:</b><br>{self._escape(metadata.get('access_constraints'))}</p>"

        html += f"<p><b>Language:</b> {self._escape(metadata.get('language', 'English'))}</p>"

        if metadata.get('attribution'):
            html += f"<p><b>Attribution:</b> {self._escape(metadata.get('attribution'))}</p>"

        # Step 3: Optional Fields
        has_optional = (metadata.get('lineage') or metadata.get('purpose') or
                       metadata.get('supplemental_info') or metadata.get('links') or
                       metadata.get('spatial_resolution'))

        if has_optional:
            html += "<h3 style='color: #0066cc; border-bottom: 2px solid #0066cc; margin-top: 20px;'>Optional Fields</h3>"

            if metadata.get('lineage'):
                html += f"<p><b>Lineage:</b><br>{self._escape(metadata.get('lineage'))}</p>"

            if metadata.get('purpose'):
                html += f"<p><b>Purpose:</b><br>{self._escape(metadata.get('purpose'))}</p>"

            if metadata.get('supplemental_info'):
                html += f"<p><b>Supplemental Info:</b><br>{self._escape(metadata.get('supplemental_info'))}</p>"

            links = metadata.get('links', [])
            if links:
                html += "<p><b>Links:</b></p><ul>"
                for link in links:
                    name = link.get('name', '')
                    url = link.get('url', '')
                    link_type = link.get('type', '')
                    html += f"<li><b>{self._escape(name)}</b> ({self._escape(link_type)})<br>"
                    html += f"<a href='{self._escape(url)}'>{self._escape(url)}</a></li>"
                html += "</ul>"

            update_freq = metadata.get('update_frequency', 'Unknown')
            if update_freq != 'Unknown':
                html += f"<p><b>Update Frequency:</b> {self._escape(update_freq)}</p>"

            if metadata.get('spatial_resolution'):
                html += f"<p><b>Spatial Resolution:</b> {self._escape(metadata.get('spatial_resolution'))}</p>"

        html += "</body></html>"
        return html

    def _escape(self, text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            HTML-safe text
        """
        if not text:
            return ""
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def validate(self) -> tuple[bool, List[str]]:
        """Validate review step (always valid)."""
        return True, []

    def get_data(self) -> Dict:
        """Review step doesn't contribute new data."""
        return {}

    def set_data(self, data: Dict):
        """Review step doesn't need to set data."""
        pass

    def clear_data(self):
        """Clear the summary display."""
        self.summary_display.clear()


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

        # Layer selection
        layer_select_layout = QtWidgets.QHBoxLayout()

        layer_label = QtWidgets.QLabel("Selected Layer:")
        layer_select_layout.addWidget(layer_label)

        self.layer_display = QtWidgets.QLabel("No layer selected - Click 'Select Layer' below")
        self.layer_display.setStyleSheet("padding: 5px; background: #f0f0f0; border: 1px solid #ccc;")
        self.layer_display.setWordWrap(True)
        layer_select_layout.addWidget(self.layer_display, 1)

        select_btn = QtWidgets.QPushButton("Select Layer from Inventory")
        select_btn.clicked.connect(self.select_layer_from_inventory)
        select_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        layer_select_layout.addWidget(select_btn)

        layout.addLayout(layer_select_layout)

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

        self.step3 = Step3Optional(self.db_manager, self)
        self.step_container.addWidget(self.step3)

        self.step4 = Step4Review(self, self)
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

    def select_layer_from_inventory(self):
        """Open dialog to select layer from inventory database."""
        # Check database connection first
        if not self.db_manager or not self.db_manager.is_connected:
            QtWidgets.QMessageBox.warning(
                self,
                "No Database Connected",
                "Please select an inventory database from the Dashboard tab first.\n\n"
                "Go to Dashboard → Select Database... to choose your inventory database."
            )
            return

        dialog = LayerSelectorDialog(self.db_manager, self)

        if dialog.exec_():
            layer_path, layer_name = dialog.get_selected_layer()
            if layer_path:
                self.current_layer_path = layer_path
                self.layer_display.setText(f"{layer_name}\n({layer_path})")
                # Auto-load metadata if exists
                self.load_metadata(layer_path)

    def set_layer(self, layer_path: str, layer_name: str = None):
        """
        Set the layer to edit metadata for.

        Args:
            layer_path: Full path to layer file
            layer_name: Display name of layer (optional)
        """
        self.current_layer_path = layer_path
        if layer_name:
            self.layer_display.setText(f"{layer_name}\n({layer_path})")
        else:
            self.layer_display.setText(layer_path)

        # Load existing metadata if available
        self.load_metadata(layer_path)

    def load_metadata(self, layer_path: str):
        """Load existing metadata from cache."""
        metadata = self.db_manager.load_metadata_from_cache(layer_path)

        if metadata:
            # Populate all steps with loaded data
            if hasattr(self.step1, 'set_data'):
                self.step1.set_data(metadata)
            if hasattr(self.step2, 'set_data'):
                self.step2.set_data(metadata)
            if hasattr(self.step3, 'set_data'):
                self.step3.set_data(metadata)

    def clear_layer(self):
        """
        Clear currently selected layer and reset wizard.

        Called when database changes to ensure clean state.
        """
        # Clear layer selection
        self.current_layer_path = None
        self.layer_display.setText("No layer selected - Click 'Select Layer' below")

        # Clear all step data
        if hasattr(self.step1, 'clear_data'):
            self.step1.clear_data()
        if hasattr(self.step2, 'clear_data'):
            self.step2.clear_data()
        if hasattr(self.step3, 'clear_data'):
            self.step3.clear_data()

        # Reset to first step
        self.current_step = 0
        self.step_container.setCurrentIndex(0)
        self.update_navigation()

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

            # Refresh Step 4 summary when navigating to it
            if self.current_step == 3 and hasattr(self.step4, 'refresh_summary'):
                metadata = self.collect_metadata()
                self.step4.refresh_summary(metadata)

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

            # Refresh Step 4 summary when navigating to it
            if self.current_step == 3 and hasattr(self.step4, 'refresh_summary'):
                metadata = self.collect_metadata()
                self.step4.refresh_summary(metadata)

    def update_navigation(self):
        """Update navigation button states."""
        self.prev_btn.setEnabled(self.current_step > 0)
        self.next_btn.setEnabled(self.current_step < 3)
        self.skip_btn.setEnabled(self.current_step < 3)

        self.progress_label.setText(f"Step {self.current_step + 1} of 4")
        self.progress_bar.setValue(self.current_step + 1)

    def collect_metadata(self) -> Dict:
        """
        Collect metadata from all steps.

        Returns:
            Dictionary containing all metadata
        """
        metadata = {}
        if hasattr(self.step1, 'get_data'):
            metadata.update(self.step1.get_data())
        if hasattr(self.step2, 'get_data'):
            metadata.update(self.step2.get_data())
        if hasattr(self.step3, 'get_data'):
            metadata.update(self.step3.get_data())
        return metadata

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
        metadata = self.collect_metadata()

        # Determine completeness status
        is_complete = self.step4.check_completeness(metadata) if hasattr(self.step4, 'check_completeness') else False
        status = 'complete' if is_complete else 'partial'

        # Save to database cache
        success = self.db_manager.save_metadata_to_cache(
            self.current_layer_path,
            metadata,
            in_sync=False  # Not yet written to file
        )

        if not success:
            QtWidgets.QMessageBox.critical(
                self,
                "Save Failed",
                "Failed to save metadata to cache. Check the log for details."
            )
            return

        # Update inventory status
        self.db_manager.update_inventory_metadata_status(
            self.current_layer_path,
            status=status,
            target='cache',  # Will be 'file' when we implement file writing
            cached=True
        )

        QtWidgets.QMessageBox.information(
            self,
            "Saved",
            f"Metadata saved to cache ({status}):\n{self.current_layer_path}"
        )

        self.metadata_saved.emit(self.current_layer_path, metadata)
