"""
Metadata Writer Module.

Handles writing QGIS metadata to various target formats:
- .qmd sidecar files for shapefiles, GeoTIFFs, etc.
- GeoPackage embedded metadata using QGIS API

Author: John Zastrow
License: MIT
"""

__version__ = "0.1.0"

import os
from typing import Dict, Tuple, Optional
from qgis.core import (
    QgsLayerMetadata,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProviderRegistry,
    QgsMessageLog,
    Qgis
)


class MetadataWriter:
    """Write QGIS metadata to various target formats."""

    def __init__(self):
        """Initialize metadata writer."""
        pass

    def dict_to_qgs_metadata(self, metadata_dict: Dict) -> QgsLayerMetadata:
        """
        Convert metadata dictionary to QgsLayerMetadata object.

        Args:
            metadata_dict: Dictionary containing metadata fields

        Returns:
            QgsLayerMetadata object
        """
        metadata = QgsLayerMetadata()

        # Identification
        if 'title' in metadata_dict:
            metadata.setTitle(metadata_dict['title'])
        if 'abstract' in metadata_dict:
            metadata.setAbstract(metadata_dict['abstract'])
        if 'type' in metadata_dict:
            metadata.setType(metadata_dict['type'])
        if 'language' in metadata_dict:
            metadata.setLanguage(metadata_dict['language'])

        # Keywords
        if 'keywords' in metadata_dict:
            # Keywords can be a list of strings or dict with vocabulary
            keywords = metadata_dict['keywords']
            if isinstance(keywords, list):
                metadata.setKeywords({'keywords': keywords})
            elif isinstance(keywords, dict):
                metadata.setKeywords(keywords)

        # Categories
        if 'categories' in metadata_dict and isinstance(metadata_dict['categories'], list):
            metadata.setCategories(metadata_dict['categories'])

        # Contacts
        if 'contacts' in metadata_dict and isinstance(metadata_dict['contacts'], list):
            contacts = []
            for contact_dict in metadata_dict['contacts']:
                contact = QgsLayerMetadata.Contact()
                if 'name' in contact_dict:
                    contact.name = contact_dict['name']
                if 'organization' in contact_dict:
                    contact.organization = contact_dict['organization']
                if 'position' in contact_dict:
                    contact.position = contact_dict['position']
                if 'email' in contact_dict:
                    contact.email = contact_dict['email']
                if 'role' in contact_dict:
                    contact.role = contact_dict['role']
                if 'voice' in contact_dict:
                    contact.voice = contact_dict['voice']
                if 'fax' in contact_dict:
                    contact.fax = contact_dict['fax']
                contacts.append(contact)
            metadata.setContacts(contacts)

        # Links
        if 'links' in metadata_dict and isinstance(metadata_dict['links'], list):
            links = []
            for link_dict in metadata_dict['links']:
                link = QgsLayerMetadata.Link()
                if 'name' in link_dict:
                    link.name = link_dict['name']
                if 'type' in link_dict:
                    link.type = link_dict['type']
                if 'url' in link_dict:
                    link.url = link_dict['url']
                if 'description' in link_dict:
                    link.description = link_dict['description']
                if 'format' in link_dict:
                    link.format = link_dict['format']
                if 'mimeType' in link_dict:
                    link.mimeType = link_dict['mimeType']
                if 'size' in link_dict:
                    link.size = link_dict['size']
                links.append(link)
            metadata.setLinks(links)

        # Rights
        if 'rights' in metadata_dict and isinstance(metadata_dict['rights'], list):
            metadata.setRights(metadata_dict['rights'])

        # Licenses
        if 'licenses' in metadata_dict and isinstance(metadata_dict['licenses'], list):
            metadata.setLicenses(metadata_dict['licenses'])

        # History
        if 'history' in metadata_dict and isinstance(metadata_dict['history'], list):
            metadata.setHistory(metadata_dict['history'])

        # Encoding
        if 'encoding' in metadata_dict:
            metadata.setEncoding(metadata_dict['encoding'])

        # CRS
        if 'crs' in metadata_dict:
            from qgis.core import QgsCoordinateReferenceSystem
            crs = QgsCoordinateReferenceSystem(metadata_dict['crs'])
            metadata.setCrs(crs)

        # Extent
        if 'extent' in metadata_dict:
            extent = QgsLayerMetadata.Extent()
            extent_dict = metadata_dict['extent']

            # Spatial extent
            if 'spatial' in extent_dict and isinstance(extent_dict['spatial'], list):
                spatial_extents = []
                for spatial_dict in extent_dict['spatial']:
                    spatial = QgsLayerMetadata.SpatialExtent()
                    if 'extentCrs' in spatial_dict:
                        from qgis.core import QgsCoordinateReferenceSystem
                        spatial.extentCrs = QgsCoordinateReferenceSystem(spatial_dict['extentCrs'])
                    if 'bounds' in spatial_dict:
                        from qgis.core import QgsBox3d
                        bounds = spatial_dict['bounds']
                        if isinstance(bounds, dict) and 'xMinimum' in bounds:
                            spatial.bounds = QgsBox3d(
                                bounds.get('xMinimum', 0),
                                bounds.get('yMinimum', 0),
                                bounds.get('zMinimum', 0),
                                bounds.get('xMaximum', 0),
                                bounds.get('yMaximum', 0),
                                bounds.get('zMaximum', 0)
                            )
                    spatial_extents.append(spatial)
                extent.setSpatialExtents(spatial_extents)

            # Temporal extent
            if 'temporal' in extent_dict and isinstance(extent_dict['temporal'], list):
                temporal_extents = []
                for temporal_dict in extent_dict['temporal']:
                    temporal = QgsLayerMetadata.TemporalExtent()
                    if 'begin' in temporal_dict:
                        from qgis.core import QgsDateTimeRange
                        from PyQt5.QtCore import QDateTime
                        begin = QDateTime.fromString(temporal_dict['begin'], 'yyyy-MM-dd')
                        end = QDateTime.fromString(temporal_dict.get('end', temporal_dict['begin']), 'yyyy-MM-dd')
                        temporal.range = QgsDateTimeRange(begin, end)
                    temporal_extents.append(temporal)
                extent.setTemporalExtents(temporal_extents)

            metadata.setExtent(extent)

        return metadata

    def write_to_qmd_file(self, layer_path: str, layer_name: str, metadata_dict: Dict) -> Tuple[bool, str]:
        """
        Write metadata to .qmd sidecar file.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer (for containers, use layer name; for files, use base name)
            metadata_dict: Dictionary containing metadata fields

        Returns:
            Tuple of (success, message/error)
        """
        try:
            # Convert dict to QgsLayerMetadata
            metadata = self.dict_to_qgs_metadata(metadata_dict)

            # Determine .qmd file path
            # For container files (gpkg, sqlite), use layer_name
            # For standalone files (shp, tif), use file base name
            file_ext = os.path.splitext(layer_path)[1].lower()
            if file_ext in ['.gpkg', '.sqlite', '.db']:
                # Container file: create .qmd with layer name
                directory = os.path.dirname(layer_path)
                base_name = os.path.splitext(os.path.basename(layer_path))[0]
                qmd_path = os.path.join(directory, f"{base_name}_{layer_name}.qmd")
            else:
                # Standalone file: create .qmd with same base name
                qmd_path = os.path.splitext(layer_path)[0] + '.qmd'

            # Write metadata to XML
            xml_content = metadata.toXml()

            # Ensure directory exists
            os.makedirs(os.path.dirname(qmd_path), exist_ok=True)

            # Write to file
            with open(qmd_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            QgsMessageLog.logMessage(
                f"Metadata written to .qmd file: {qmd_path}",
                "Metadata Manager",
                Qgis.Success
            )

            return True, qmd_path

        except Exception as e:
            error_msg = f"Error writing .qmd file: {str(e)}"
            QgsMessageLog.logMessage(
                error_msg,
                "Metadata Manager",
                Qgis.Critical
            )
            return False, error_msg

    def write_to_geopackage(self, layer_path: str, layer_name: str, metadata_dict: Dict) -> Tuple[bool, str]:
        """
        Write metadata directly to GeoPackage layer.

        Args:
            layer_path: Full path to the GeoPackage file
            layer_name: Name of the layer within the GeoPackage
            metadata_dict: Dictionary containing metadata fields

        Returns:
            Tuple of (success, message/error)
        """
        try:
            # Convert dict to QgsLayerMetadata
            metadata = self.dict_to_qgs_metadata(metadata_dict)

            # Construct layer URI
            # Format: path/to/file.gpkg|layername=layer_name
            layer_uri = f"{layer_path}|layername={layer_name}"

            # Try to load as vector first
            layer = QgsVectorLayer(layer_uri, "temp", "ogr")

            if not layer.isValid():
                # Try as raster
                layer = QgsRasterLayer(layer_uri, "temp")

            if not layer.isValid():
                return False, f"Could not load layer: {layer_name} from {layer_path}"

            # Set metadata
            layer.setMetadata(metadata)

            # Save metadata to the layer
            # For GeoPackage, metadata is stored in the gpkg_metadata table
            error = layer.saveMetadata()

            if error:
                QgsMessageLog.logMessage(
                    f"Error saving metadata to GeoPackage: {error}",
                    "Metadata Manager",
                    Qgis.Warning
                )
                return False, error

            QgsMessageLog.logMessage(
                f"Metadata written to GeoPackage layer: {layer_path} / {layer_name}",
                "Metadata Manager",
                Qgis.Success
            )

            return True, f"embedded in {layer_path}"

        except Exception as e:
            error_msg = f"Error writing to GeoPackage: {str(e)}"
            QgsMessageLog.logMessage(
                error_msg,
                "Metadata Manager",
                Qgis.Critical
            )
            return False, error_msg

    def write_metadata(self, layer_path: str, layer_name: str, metadata_dict: Dict,
                       file_format: str = None) -> Tuple[bool, str, str]:
        """
        Write metadata to appropriate target based on file format.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer
            metadata_dict: Dictionary containing metadata fields
            file_format: File format (e.g., 'GPKG', 'ESRI Shapefile', 'GeoTIFF')

        Returns:
            Tuple of (success, target_location, message/error)
        """
        # Determine file format from extension if not provided
        if not file_format:
            ext = os.path.splitext(layer_path)[1].lower()
            file_format = ext

        # Determine if this is a GeoPackage
        is_geopackage = False
        if file_format:
            format_lower = file_format.lower()
            is_geopackage = (
                'gpkg' in format_lower or
                'geopackage' in format_lower or
                layer_path.lower().endswith('.gpkg')
            )

        if is_geopackage:
            # Write to GeoPackage embedded metadata
            success, result = self.write_to_geopackage(layer_path, layer_name, metadata_dict)
            target = f"embedded:{layer_path}" if success else "none"
            return success, target, result
        else:
            # Write to .qmd sidecar file
            success, result = self.write_to_qmd_file(layer_path, layer_name, metadata_dict)
            target = result if success else "none"
            return success, target, result
