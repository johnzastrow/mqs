"""
Inventory Processor - Core inventory scanning logic.

Refactored from inventory_miner.py to work directly within plugin.
Scans directories for geospatial files and creates/updates GeoPackage inventory.

Author: John Zastrow
License: MIT
"""

__version__ = "0.6.0"

from pathlib import Path
from datetime import datetime
from osgeo import gdal, ogr
import xml.etree.ElementTree as ET
import sqlite3

from qgis.core import (
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsRectangle,
    QgsPointXY,
    QgsVectorFileWriter,
    QgsWkbTypes,
    QgsMessageLog,
    Qgis
)
from qgis.PyQt.QtCore import QVariant


class InventoryProcessor:
    """
    Process directory scanning and inventory creation.

    This is a refactored version of inventory_miner.py that works
    directly within the plugin without Processing framework dependency.
    """

    def __init__(self, params, feedback=None):
        """
        Initialize processor.

        Args:
            params: Dictionary with:
                - directory: Root directory to scan
                - output_gpkg: Output GeoPackage path
                - layer_name: Name for inventory layer
                - update_mode: Boolean
                - include_vectors: Boolean
                - include_rasters: Boolean
                - include_tables: Boolean
                - parse_metadata: Boolean
                - include_sidecar: Boolean
                - validate_files: Boolean
            feedback: Optional feedback object for progress/logging
        """
        self.params = params
        self.feedback = feedback
        self.wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        self.stats = {
            'total': 0,
            'vectors': 0,
            'rasters': 0,
            'tables': 0,
            'errors': 0
        }

    def process(self):
        """
        Run the inventory process.

        Returns:
            Dictionary with results or raises exception on error
        """
        try:
            root_path = Path(self.params['directory'])
            output_gpkg = self.params['output_gpkg']
            layer_name = self.params['layer_name']

            self.log_info(f"Starting inventory scan of: {root_path}")
            self.log_info(f"Output database: {output_gpkg}")

            # Load existing inventory if update mode
            existing_inventory = {}
            if self.params['update_mode'] and Path(output_gpkg).exists():
                self.log_info("Update mode: Loading existing inventory...")
                existing_inventory = self._load_existing_inventory(output_gpkg, layer_name)
                self.log_info(f"Loaded {len(existing_inventory)} existing records")

            # Discover geospatial files
            self.log_info("Discovering geospatial files...")
            self.set_progress(10)

            data_sources = self._discover_geospatial_files(root_path)
            self.log_info(f"Found {len(data_sources)} geospatial files/layers")

            if not data_sources:
                self.log_warning("No geospatial files found in directory")
                return {'output': output_gpkg, 'stats': self.stats}

            # Extract metadata from each file
            self.log_info("Extracting metadata...")
            self.set_progress(30)

            features = []
            current_file_paths = set()

            for i, ds_info in enumerate(data_sources):
                if self.is_canceled():
                    break

                progress = 30 + int((i / len(data_sources)) * 50)  # 30-80%
                self.set_progress(progress)

                try:
                    feature = self._extract_metadata(ds_info, root_path, existing_inventory)
                    if feature:
                        features.append(feature)
                        current_file_paths.add(feature['file_path'])

                        # Update stats
                        self.stats['total'] += 1
                        data_type = feature.get('data_type', '')
                        if data_type == 'vector':
                            self.stats['vectors'] += 1
                        elif data_type == 'raster':
                            self.stats['rasters'] += 1
                        elif data_type == 'table':
                            self.stats['tables'] += 1

                except Exception as e:
                    self.log_error(f"Error processing {ds_info.get('path', 'unknown')}: {str(e)}")
                    self.stats['errors'] += 1

            self.log_info(f"Extracted metadata for {len(features)} layers")

            # Handle retired records in update mode
            if self.params['update_mode'] and existing_inventory:
                self.log_info("Checking for retired records...")
                retired_count = self._retire_old_records(
                    existing_inventory,
                    current_file_paths,
                    output_gpkg,
                    layer_name
                )
                if retired_count > 0:
                    self.log_info(f"Retired {retired_count} missing records")

            # Write to GeoPackage
            self.log_info("Writing to GeoPackage...")
            self.set_progress(90)

            self._write_geopackage(output_gpkg, layer_name, features)

            self.set_progress(100)
            self.log_info(f"✓ Inventory complete: {self.stats['total']} layers")

            return {'output': output_gpkg, 'stats': self.stats}

        except Exception as e:
            self.log_error(f"Fatal error: {str(e)}")
            raise

    def _discover_geospatial_files(self, root_path):
        """
        Discover all geospatial files using GDAL/OGR.

        Returns:
            List of dictionaries with file info
        """
        data_sources = []

        for item_path in root_path.rglob("*"):
            if self.is_canceled():
                break

            if not item_path.is_file():
                continue

            file_str = str(item_path)

            # Try as vector (OGR)
            if self.params['include_vectors'] or self.params['include_tables']:
                try:
                    ds = ogr.Open(file_str)
                    if ds:
                        for layer_idx in range(ds.GetLayerCount()):
                            layer = ds.GetLayer(layer_idx)
                            if layer:
                                is_spatial = layer.GetGeomType() != ogr.wkbNone

                                if (is_spatial and self.params['include_vectors']) or \
                                   (not is_spatial and self.params['include_tables']):
                                    data_sources.append({
                                        'path': file_str,
                                        'type': 'vector' if is_spatial else 'table',
                                        'layer_name': layer.GetName(),
                                        'layer_index': layer_idx
                                    })
                        ds = None
                        continue
                except:
                    pass

            # Try as raster (GDAL)
            if self.params['include_rasters']:
                try:
                    ds = gdal.Open(file_str, gdal.GA_ReadOnly)
                    if ds:
                        data_sources.append({
                            'path': file_str,
                            'type': 'raster',
                            'layer_name': item_path.stem,
                            'layer_index': 0
                        })
                        ds = None
                except:
                    pass

        return data_sources

    def _extract_metadata(self, ds_info, root_path, existing_inventory):
        """Extract comprehensive metadata from a data source."""
        feature_data = {}

        file_path = Path(ds_info['path'])
        data_type = ds_info['type']
        layer_name = ds_info['layer_name']

        # Basic file info
        feature_data['file_path'] = str(file_path)
        feature_data['relative_path'] = str(file_path.relative_to(root_path))
        feature_data['file_name'] = file_path.name
        feature_data['parent_directory'] = str(file_path.parent)
        feature_data['layer_name'] = layer_name
        feature_data['data_type'] = data_type
        feature_data['record_created'] = datetime.now().isoformat()
        feature_data['scan_timestamp'] = datetime.now().isoformat()

        # Multi-user tracking info (for PostGIS sync in future versions)
        import platform
        import socket
        import getpass

        feature_data['scanned_by_user'] = getpass.getuser()  # Username
        feature_data['scanned_by_machine'] = socket.gethostname()  # Computer name
        feature_data['scanned_from_os'] = platform.system()  # Windows, Linux, Darwin
        feature_data['scanned_from_os_version'] = platform.version()  # OS version details

        # Network path detection (UNC path vs local)
        file_path_str = str(file_path)
        if file_path_str.startswith('\\\\') or file_path_str.startswith('//'):
            feature_data['storage_location'] = 'network'
            # Extract network server name if UNC path
            try:
                parts = file_path_str.replace('\\\\', '').replace('//', '').split('\\')[0].split('/')[0]
                feature_data['network_server'] = parts
            except:
                feature_data['network_server'] = 'unknown'
        else:
            feature_data['storage_location'] = 'local'
            feature_data['network_server'] = None

        # Drive letter (Windows) or mount point (Unix)
        try:
            if platform.system() == 'Windows':
                import os
                drive = os.path.splitdrive(file_path_str)[0]
                feature_data['drive_or_mount'] = drive if drive else None
            else:
                # Unix - get mount point
                import subprocess
                result = subprocess.run(['df', file_path_str], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        mount_point = lines[1].split()[-1]
                        feature_data['drive_or_mount'] = mount_point
        except:
            feature_data['drive_or_mount'] = None

        try:
            stat = file_path.stat()
            feature_data['file_size_bytes'] = stat.st_size
            feature_data['file_size_mb'] = round(stat.st_size / (1024*1024), 2)
            feature_data['file_created'] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            feature_data['file_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except:
            pass

        # Extract type-specific metadata
        if data_type in ['vector', 'table']:
            self._extract_vector_metadata(feature_data, ds_info)
        elif data_type == 'raster':
            self._extract_raster_metadata(feature_data, ds_info)

        # Parse GIS metadata files
        if self.params['parse_metadata']:
            self._parse_gis_metadata(feature_data, file_path)

        # Check sidecar files
        if self.params['include_sidecar']:
            self._check_sidecar_files(feature_data, file_path)

        # Preserve metadata status if updating
        if self.params['update_mode']:
            self._apply_preserved_metadata_status(feature_data, existing_inventory)
        else:
            feature_data['metadata_status'] = 'none'
            feature_data['metadata_cached'] = False

        # Initialize PostGIS sync fields
        feature_data['sync_status'] = 'not_synced'
        feature_data['last_sync_date'] = None
        feature_data['postgis_id'] = None

        # Organization fields (can be populated by user later)
        feature_data['organization'] = None
        feature_data['data_steward'] = None
        feature_data['project_name'] = None
        feature_data['data_classification'] = None
        feature_data['retention_policy'] = None

        # Calculate basic quality score
        feature_data['quality_score'] = self._calculate_quality_score(feature_data)

        # Create extent geometry
        feature_data['geometry'] = self._create_extent_geometry(feature_data)

        return feature_data

    def _calculate_quality_score(self, feature_data):
        """
        Calculate automated quality score (0-100) based on completeness.

        Factors:
        - Has CRS: 20 points
        - Has extent: 20 points
        - Has metadata: 20 points
        - Has field info (vectors): 15 points
        - Has valid geometry/raster: 15 points
        - No validation issues: 10 points
        """
        score = 0.0

        # CRS defined (20 points)
        if feature_data.get('has_crs'):
            score += 20

        # Extent defined (20 points)
        if feature_data.get('has_extent'):
            score += 20

        # Metadata present (20 points)
        if feature_data.get('metadata_present'):
            score += 20

        # Field information for vectors (15 points)
        if feature_data.get('data_type') == 'vector':
            if feature_data.get('field_count', 0) > 0:
                score += 15
        elif feature_data.get('data_type') == 'raster':
            if feature_data.get('band_count', 0) > 0:
                score += 15

        # Valid data (15 points)
        if feature_data.get('is_valid', True):  # Default to True if not checked
            score += 15

        # No issues (10 points)
        if not feature_data.get('issues'):
            score += 10

        return round(score, 1)

    def _extract_vector_metadata(self, feature_data, ds_info):
        """Extract vector-specific metadata."""
        try:
            ds = ogr.Open(ds_info['path'])
            if ds:
                layer = ds.GetLayer(ds_info['layer_index'])
                if layer:
                    feature_data['driver_name'] = ds.GetDriver().GetName()
                    feature_data['format'] = ds.GetDriver().GetName()
                    feature_data['feature_count'] = layer.GetFeatureCount()
                    feature_data['geometry_type'] = ogr.GeometryTypeToName(layer.GetGeomType())

                    # CRS
                    srs = layer.GetSpatialRef()
                    if srs:
                        feature_data['crs_authid'] = srs.GetAuthorityName(None) + ':' + srs.GetAuthorityCode(None) if srs.GetAuthorityCode(None) else ''
                        feature_data['crs_wkt'] = srs.ExportToWkt()
                        feature_data['has_crs'] = True

                    # Extent
                    extent = layer.GetExtent()
                    if extent:
                        feature_data['native_extent'] = f"{extent[0]},{extent[2]},{extent[1]},{extent[3]}"
                        feature_data['has_extent'] = True

                        # Transform to WGS84
                        if srs:
                            self._transform_extent_to_wgs84(feature_data, extent, srs)

                    # Fields
                    layer_def = layer.GetLayerDefn()
                    field_count = layer_def.GetFieldCount()
                    feature_data['field_count'] = field_count
                    feature_data['field_names'] = ','.join([layer_def.GetFieldDefn(i).GetName() for i in range(field_count)])
                    feature_data['field_types'] = ','.join([layer_def.GetFieldDefn(i).GetTypeName() for i in range(field_count)])

                ds = None
        except Exception as e:
            feature_data['issues'] = str(e)

    def _extract_raster_metadata(self, feature_data, ds_info):
        """Extract raster-specific metadata."""
        try:
            ds = gdal.Open(ds_info['path'], gdal.GA_ReadOnly)
            if ds:
                feature_data['driver_name'] = ds.GetDriver().ShortName
                feature_data['format'] = ds.GetDriver().ShortName
                feature_data['raster_width'] = ds.RasterXSize
                feature_data['raster_height'] = ds.RasterYSize
                feature_data['band_count'] = ds.RasterCount

                # Geotransform and extent
                gt = ds.GetGeoTransform()
                if gt:
                    feature_data['pixel_width'] = abs(gt[1])
                    feature_data['pixel_height'] = abs(gt[5])

                    xmin = gt[0]
                    ymax = gt[3]
                    xmax = xmin + gt[1] * ds.RasterXSize
                    ymin = ymax + gt[5] * ds.RasterYSize

                    feature_data['native_extent'] = f"{xmin},{ymin},{xmax},{ymax}"
                    feature_data['has_extent'] = True

                    # CRS
                    srs_wkt = ds.GetProjection()
                    if srs_wkt:
                        from osgeo import osr
                        srs = osr.SpatialReference()
                        srs.ImportFromWkt(srs_wkt)
                        feature_data['crs_authid'] = srs.GetAuthorityName(None) + ':' + srs.GetAuthorityCode(None) if srs.GetAuthorityCode(None) else ''
                        feature_data['crs_wkt'] = srs_wkt
                        feature_data['has_crs'] = True

                        # Transform to WGS84
                        self._transform_extent_to_wgs84(feature_data, (xmin, xmax, ymin, ymax), srs)

                # Band info
                if ds.RasterCount > 0:
                    band = ds.GetRasterBand(1)
                    feature_data['data_types'] = gdal.GetDataTypeName(band.DataType)
                    nodata = band.GetNoDataValue()
                    if nodata is not None:
                        feature_data['nodata_value'] = str(nodata)

                ds = None
        except Exception as e:
            feature_data['issues'] = str(e)

    def _transform_extent_to_wgs84(self, feature_data, extent, source_srs):
        """Transform extent to WGS84."""
        try:
            from osgeo import osr
            target_srs = osr.SpatialReference()
            target_srs.ImportFromEPSG(4326)

            transform = osr.CoordinateTransformation(source_srs, target_srs)

            xmin, xmax, ymin, ymax = extent
            p1 = transform.TransformPoint(xmin, ymin)
            p2 = transform.TransformPoint(xmax, ymax)

            feature_data['wgs84_extent'] = f"{p1[0]},{p1[1]},{p2[0]},{p2[1]}"
        except:
            pass

    def _parse_gis_metadata(self, feature_data, file_path):
        """Parse metadata from XML files."""
        # Look for metadata XML file
        xml_candidates = [
            file_path.with_suffix('.xml'),  # same name
            Path(str(file_path) + '.xml'),  # appended
        ]

        for xml_path in xml_candidates:
            if xml_path.exists():
                try:
                    tree = ET.parse(xml_path)
                    root = tree.getroot()

                    feature_data['has_metadata_xml'] = True
                    feature_data['metadata_file_path'] = str(xml_path)
                    feature_data['metadata_present'] = True

                    # Detect standard
                    if 'metadata' in root.tag.lower():
                        if 'fgdc' in root.tag.lower() or any('idinfo' == child.tag for child in root):
                            feature_data['metadata_standard'] = 'FGDC'
                            self._parse_fgdc_metadata(feature_data, root)
                        elif any('Esri' in child.tag for child in root):
                            feature_data['metadata_standard'] = 'ESRI'
                            self._parse_esri_metadata(feature_data, root)
                        elif 'MD_Metadata' in root.tag:
                            feature_data['metadata_standard'] = 'ISO 19115'
                            self._parse_iso_metadata(feature_data, root)
                    elif 'qgis' in root.tag.lower():
                        feature_data['metadata_standard'] = 'QGIS'
                        self._parse_qgis_metadata(feature_data, root)

                    break  # Found metadata, stop looking
                except:
                    pass

    def _parse_fgdc_metadata(self, feature_data, root):
        """Parse FGDC metadata."""
        try:
            # Title
            title_elem = root.find('.//title')
            if title_elem is not None and title_elem.text:
                feature_data['layer_title'] = title_elem.text.strip()

            # Abstract
            abstract_elem = root.find('.//abstract')
            if abstract_elem is not None and abstract_elem.text:
                feature_data['layer_abstract'] = abstract_elem.text.strip()

            # Keywords
            keywords = []
            for theme in root.findall('.//themekey'):
                if theme.text:
                    keywords.append(theme.text.strip())
            if keywords:
                feature_data['keywords'] = ','.join(keywords)

            # Lineage
            lineage_elem = root.find('.//lineage')
            if lineage_elem is not None and lineage_elem.text:
                feature_data['lineage'] = lineage_elem.text.strip()

            # Constraints
            useconst_elem = root.find('.//useconst')
            if useconst_elem is not None and useconst_elem.text:
                feature_data['constraints'] = useconst_elem.text.strip()
        except:
            pass

    def _parse_esri_metadata(self, feature_data, root):
        """Parse ESRI metadata."""
        try:
            # Similar to FGDC but with ESRI-specific paths
            for elem in root.iter():
                if 'title' in elem.tag.lower() and elem.text:
                    feature_data['layer_title'] = elem.text.strip()
                    break
        except:
            pass

    def _parse_iso_metadata(self, feature_data, root):
        """Parse ISO 19115 metadata."""
        pass  # Implement if needed

    def _parse_qgis_metadata(self, feature_data, root):
        """Parse QGIS .qmd metadata."""
        try:
            title_elem = root.find('.//title')
            if title_elem is not None and title_elem.text:
                feature_data['layer_title'] = title_elem.text.strip()

            abstract_elem = root.find('.//abstract')
            if abstract_elem is not None and abstract_elem.text:
                feature_data['layer_abstract'] = abstract_elem.text.strip()
        except:
            pass

    def _check_sidecar_files(self, feature_data, file_path):
        """Check for sidecar files."""
        feature_data['has_prj_file'] = file_path.with_suffix('.prj').exists()
        feature_data['has_aux_xml'] = (file_path.parent / f"{file_path.name}.aux.xml").exists()

    def _apply_preserved_metadata_status(self, feature_data, existing_inventory):
        """Apply preserved metadata status from existing inventory."""
        key = (feature_data['file_path'], feature_data['layer_name'])
        if key in existing_inventory:
            old = existing_inventory[key]
            feature_data['metadata_status'] = old.get('metadata_status', 'none')
            feature_data['metadata_cached'] = old.get('metadata_cached', False)
            feature_data['metadata_last_updated'] = old.get('metadata_last_updated')
            feature_data['metadata_target'] = old.get('metadata_target')
        else:
            feature_data['metadata_status'] = 'none'
            feature_data['metadata_cached'] = False

    def _create_extent_geometry(self, feature_data):
        """Create WGS84 extent polygon geometry."""
        wgs84_extent = feature_data.get('wgs84_extent')
        if not wgs84_extent:
            return None

        try:
            coords = [float(x) for x in wgs84_extent.split(',')]
            xmin, ymin, xmax, ymax = coords

            points = [
                QgsPointXY(xmin, ymin),
                QgsPointXY(xmax, ymin),
                QgsPointXY(xmax, ymax),
                QgsPointXY(xmin, ymax),
                QgsPointXY(xmin, ymin)
            ]

            return QgsGeometry.fromPolygonXY([points])
        except:
            return None

    def _load_existing_inventory(self, gpkg_path, layer_name):
        """Load existing inventory for update mode."""
        inventory = {}
        try:
            conn = sqlite3.connect(gpkg_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT file_path, layer_name, metadata_status, metadata_cached,
                       metadata_last_updated, metadata_target
                FROM {layer_name}
                WHERE retired_datetime IS NULL
            """)

            for row in cursor.fetchall():
                key = (row['file_path'], row['layer_name'])
                inventory[key] = dict(row)

            conn.close()
        except:
            pass

        return inventory

    def _retire_old_records(self, existing_inventory, current_file_paths, output_gpkg, layer_name):
        """Mark missing files as retired."""
        retired_count = 0
        try:
            conn = sqlite3.connect(output_gpkg)
            cursor = conn.cursor()

            for (file_path, layer_name_val), data in existing_inventory.items():
                if file_path not in current_file_paths:
                    cursor.execute(f"""
                        UPDATE {layer_name}
                        SET retired_datetime = ?
                        WHERE file_path = ? AND layer_name = ? AND retired_datetime IS NULL
                    """, (datetime.now().isoformat(), file_path, layer_name_val))
                    retired_count += 1

            conn.commit()
            conn.close()
        except Exception as e:
            self.log_error(f"Error retiring records: {str(e)}")

        return retired_count

    def _write_geopackage(self, output_path, layer_name, features):
        """Write features to GeoPackage."""
        if not features:
            self.log_warning("No features to write")
            return

        # Create fields
        fields = self._create_fields()

        # Create memory layer
        mem_layer = QgsVectorLayer(f"Polygon?crs=EPSG:4326", layer_name, "memory")
        mem_provider = mem_layer.dataProvider()
        mem_provider.addAttributes(fields.toList())
        mem_layer.updateFields()

        # Add features
        qgs_features = []
        for feat_data in features:
            feat = QgsFeature(fields)

            # Set attributes
            for field in fields:
                field_name = field.name()
                if field_name in feat_data:
                    feat.setAttribute(field_name, feat_data[field_name])

            # Set geometry
            if feat_data.get('geometry'):
                feat.setGeometry(feat_data['geometry'])

            qgs_features.append(feat)

        mem_provider.addFeatures(qgs_features)

        # Write to GeoPackage - use direct GDAL approach for better control
        import os

        # Determine write mode
        db_exists = os.path.exists(output_path)

        if db_exists:
            # Database exists - need to check if layer exists and remove it first
            self.log_info(f"Database exists, removing old {layer_name} layer if present...")

            # Remove existing layer using ogr
            try:
                from osgeo import ogr
                ds = ogr.Open(output_path, 1)  # 1 = update mode
                if ds:
                    # Find and delete layer if it exists
                    for i in range(ds.GetLayerCount()):
                        layer = ds.GetLayer(i)
                        if layer.GetName() == layer_name:
                            ds.DeleteLayer(i)
                            self.log_info(f"Removed existing {layer_name} layer")
                            break
                    ds = None
            except Exception as e:
                self.log_warning(f"Could not remove existing layer: {str(e)}")

        # Now write the new layer
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.layerName = layer_name

        if db_exists:
            # Append to existing database
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
        else:
            # Create new database
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

        self.log_info(f"Writing {len(qgs_features)} features to {layer_name}...")

        writer = QgsVectorFileWriter.create(
            output_path,
            mem_layer.fields(),
            mem_layer.wkbType(),
            mem_layer.crs(),
            QgsProject.instance().transformContext(),
            options
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            error_msg = writer.errorMessage() if writer.errorMessage() else "Unknown OGR error"
            raise Exception(f"Error writing GeoPackage: {error_msg}\n"
                          f"Output path: {output_path}\n"
                          f"Layer name: {layer_name}\n"
                          f"Database exists: {db_exists}")

        # Write features
        for feature in qgs_features:
            if not writer.addFeature(feature):
                self.log_warning(f"Failed to write feature: {feature.id()}")

        # Finalize and close writer
        del writer

        self.log_info(f"✓ Wrote {len(features)} features to {output_path}")

    def _create_fields(self):
        """Create field schema."""
        fields = QgsFields()

        # All the fields from inventory_miner (simplified list for space)
        field_defs = [
            ("file_path", QVariant.String),
            ("relative_path", QVariant.String),
            ("file_name", QVariant.String),
            ("parent_directory", QVariant.String),
            ("layer_name", QVariant.String),
            ("data_type", QVariant.String),
            ("format", QVariant.String),
            ("driver_name", QVariant.String),
            ("file_size_bytes", QVariant.LongLong),
            ("file_size_mb", QVariant.Double),
            ("file_created", QVariant.String),
            ("file_modified", QVariant.String),
            # Multi-user tracking fields (for PostGIS sync)
            ("scanned_by_user", QVariant.String),
            ("scanned_by_machine", QVariant.String),
            ("scanned_from_os", QVariant.String),
            ("scanned_from_os_version", QVariant.String),
            ("storage_location", QVariant.String),  # 'local' or 'network'
            ("network_server", QVariant.String),  # Server name if UNC path
            ("drive_or_mount", QVariant.String),  # Drive letter or mount point
            ("crs_authid", QVariant.String),
            ("crs_wkt", QVariant.String),
            ("native_extent", QVariant.String),
            ("wgs84_extent", QVariant.String),
            ("has_crs", QVariant.Bool),
            ("has_extent", QVariant.Bool),
            ("geometry_type", QVariant.String),
            ("feature_count", QVariant.LongLong),
            ("field_count", QVariant.Int),
            ("field_names", QVariant.String),
            ("field_types", QVariant.String),
            ("raster_width", QVariant.Int),
            ("raster_height", QVariant.Int),
            ("band_count", QVariant.Int),
            ("pixel_width", QVariant.Double),
            ("pixel_height", QVariant.Double),
            ("data_types", QVariant.String),
            ("nodata_value", QVariant.String),
            ("metadata_present", QVariant.Bool),
            ("metadata_file_path", QVariant.String),
            ("metadata_standard", QVariant.String),
            ("layer_title", QVariant.String),
            ("layer_abstract", QVariant.String),
            ("keywords", QVariant.String),
            ("lineage", QVariant.String),
            ("constraints", QVariant.String),
            ("url", QVariant.String),
            ("contact_info", QVariant.String),
            ("has_prj_file", QVariant.Bool),
            ("has_aux_xml", QVariant.Bool),
            ("has_metadata_xml", QVariant.Bool),
            ("issues", QVariant.String),
            ("record_created", QVariant.String),
            ("scan_timestamp", QVariant.String),
            ("metadata_status", QVariant.String),
            ("metadata_last_updated", QVariant.String),
            ("metadata_target", QVariant.String),
            ("metadata_cached", QVariant.Bool),
            ("retired_datetime", QVariant.String),
            # PostGIS sync tracking (for future multi-user/central database)
            ("sync_status", QVariant.String),  # 'not_synced', 'synced', 'conflict'
            ("last_sync_date", QVariant.String),  # When last synced to PostGIS
            ("postgis_id", QVariant.Int),  # ID in central PostGIS database
            ("organization", QVariant.String),  # Department/org that owns data
            ("data_steward", QVariant.String),  # Person responsible for data
            ("project_name", QVariant.String),  # Project this data belongs to
            ("data_classification", QVariant.String),  # public, internal, confidential
            ("retention_policy", QVariant.String),  # How long to keep
            ("quality_score", QVariant.Double),  # Automated quality score 0-100
        ]

        for name, type_val in field_defs:
            # Create QgsField with type and typename parameters
            # This approach works across QGIS 3.x versions
            if type_val == QVariant.String:
                field = QgsField(name, type_val, typename="text", len=255)
            elif type_val == QVariant.Int:
                field = QgsField(name, type_val, typename="integer")
            elif type_val == QVariant.LongLong:
                field = QgsField(name, type_val, typename="integer64")
            elif type_val == QVariant.Double:
                field = QgsField(name, type_val, typename="double", prec=10)
            elif type_val == QVariant.Bool:
                field = QgsField(name, type_val, typename="boolean")
            else:
                # Fallback for unknown types
                field = QgsField(name, QVariant.String, typename="text", len=255)
            fields.append(field)

        return fields

    # Utility methods for feedback
    def log_info(self, message):
        if self.feedback:
            self.feedback.pushInfo(message)

    def log_warning(self, message):
        if self.feedback:
            self.feedback.reportError(message, False)

    def log_error(self, message):
        if self.feedback:
            self.feedback.reportError(message, False)

    def set_progress(self, percent):
        if self.feedback:
            self.feedback.setProgress(percent)

    def is_canceled(self):
        return self.feedback and self.feedback.isCanceled()
