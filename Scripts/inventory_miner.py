"""
Inventory Miner - QGIS Processing Algorithm

Recursively scans directories for all geospatial data files (vectors, rasters, and files
with georeference information) to create a comprehensive inventory stored in a GeoPackage
database with extent polygons in EPSG:4326.

Author: QGIS User
License: MIT
"""

__version__ = "0.1.0"

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFile,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterString,
    QgsProcessingParameterBoolean,
    QgsProcessingException,
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
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from pathlib import Path
from datetime import datetime
from osgeo import gdal, ogr
import xml.etree.ElementTree as ET


class InventoryMinerAlgorithm(QgsProcessingAlgorithm):
    """
    QGIS Processing Algorithm to inventory geospatial data files and store
    results in a GeoPackage with extent polygons.
    """

    # Parameter names
    INPUT_DIRECTORY = "INPUT_DIRECTORY"
    OUTPUT_GPKG = "OUTPUT_GPKG"
    LAYER_NAME = "LAYER_NAME"
    INCLUDE_RASTERS = "INCLUDE_RASTERS"
    INCLUDE_VECTORS = "INCLUDE_VECTORS"
    INCLUDE_TABLES = "INCLUDE_TABLES"
    PARSE_METADATA = "PARSE_METADATA"
    INCLUDE_SIDECAR = "INCLUDE_SIDECAR"
    VALIDATE_FILES = "VALIDATE_FILES"

    def tr(self, string):
        """Return a translatable string with the self.tr() function."""
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        """Create a new instance of the algorithm."""
        return InventoryMinerAlgorithm()

    def name(self):
        """Return the algorithm name."""
        return "inventory_miner"

    def displayName(self):
        """Return the translated algorithm name."""
        return self.tr("Inventory Miner")

    def group(self):
        """Return the name of the group this algorithm belongs to."""
        return self.tr("MQS Tools")

    def groupId(self):
        """Return the unique ID of the group this algorithm belongs to."""
        return "mqstools"

    def shortHelpString(self):
        """Return a short help string for the algorithm."""
        return self.tr(
            """
            <p>Recursively scans directories for all geospatial data files and creates a comprehensive
            inventory in a GeoPackage database with extent polygons in EPSG:4326.</p>

            <h3>Features</h3>
            <ul>
                <li>Automatic detection of all GDAL/OGR-supported georeferenced files</li>
                <li>Recognizes georeference information in headers, data, and sidecar files</li>
                <li>Extracts comprehensive metadata (CRS, extent, attributes, etc.)</li>
                <li>Creates spatial catalog with extent bounding box polygons</li>
                <li>Supports vectors, rasters, and container formats (GeoPackage, FileGDB, etc.)</li>
                <li>Identifies non-spatial tables and supporting data</li>
                <li>Parses GIS metadata files (ISO 19115, FGDC, ESRI)</li>
                <li>All extents transformed to EPSG:4326 for consistent visualization</li>
            </ul>

            <h3>Parameters</h3>
            <ul>
                <li><b>Input Directory:</b> Top-level directory to scan recursively</li>
                <li><b>Output GeoPackage:</b> GeoPackage database (new or existing)</li>
                <li><b>Layer Name:</b> Name for inventory layer (default: geospatial_inventory)</li>
                <li><b>Include Rasters:</b> Include raster datasets in inventory</li>
                <li><b>Include Vectors:</b> Include vector datasets in inventory</li>
                <li><b>Include Non-Spatial Tables:</b> Include attribute-only tables</li>
                <li><b>Parse GIS Metadata:</b> Extract metadata from XML files</li>
                <li><b>Include Sidecar Files:</b> Report .prj, world files, .xml presence</li>
                <li><b>Validate Files:</b> Test each file can be opened (slower)</li>
            </ul>

            <h3>Output</h3>
            <p>Creates a polygon layer in the GeoPackage with one record per discovered layer.
            Each polygon represents the extent bounding box in EPSG:4326, with comprehensive
            attributes including file paths, formats, CRS, metadata, and quality indicators.</p>

            <p><b>Version:</b> {}</p>
            """.format(__version__)
        )

    def initAlgorithm(self, config=None):
        """Define the inputs and outputs of the algorithm."""

        # Input directory parameter
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DIRECTORY,
                self.tr("Input Directory"),
                behavior=QgsProcessingParameterFile.Folder,
            )
        )

        # Output GeoPackage parameter
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_GPKG,
                self.tr("Output GeoPackage"),
                type=QgsProcessing.TypeVectorPolygon,
                createByDefault=True,
            )
        )

        # Layer name parameter
        self.addParameter(
            QgsProcessingParameterString(
                self.LAYER_NAME,
                self.tr("Inventory Layer Name"),
                defaultValue="geospatial_inventory",
            )
        )

        # Optional parameters
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INCLUDE_RASTERS,
                self.tr("Include Raster Files"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INCLUDE_VECTORS,
                self.tr("Include Vector Files"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INCLUDE_TABLES,
                self.tr("Include Non-Spatial Tables"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PARSE_METADATA,
                self.tr("Parse GIS Metadata Files"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INCLUDE_SIDECAR,
                self.tr("Include Sidecar File Information"),
                defaultValue=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.VALIDATE_FILES,
                self.tr("Validate Files (slower but thorough)"),
                defaultValue=False,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """Execute the algorithm."""

        # Get parameters
        input_dir = self.parameterAsFile(parameters, self.INPUT_DIRECTORY, context)
        output_gpkg = self.parameterAsOutputLayer(parameters, self.OUTPUT_GPKG, context)
        layer_name = self.parameterAsString(parameters, self.LAYER_NAME, context)
        include_rasters = self.parameterAsBoolean(parameters, self.INCLUDE_RASTERS, context)
        include_vectors = self.parameterAsBoolean(parameters, self.INCLUDE_VECTORS, context)
        include_tables = self.parameterAsBoolean(parameters, self.INCLUDE_TABLES, context)
        parse_metadata = self.parameterAsBoolean(parameters, self.PARSE_METADATA, context)
        include_sidecar = self.parameterAsBoolean(parameters, self.INCLUDE_SIDECAR, context)
        validate_files = self.parameterAsBoolean(parameters, self.VALIDATE_FILES, context)

        # Validate input directory
        input_path = Path(input_dir)
        if not input_path.exists():
            raise QgsProcessingException(self.tr(f"Input directory does not exist: {input_dir}"))
        if not input_path.is_dir():
            raise QgsProcessingException(self.tr(f"Input path is not a directory: {input_dir}"))

        feedback.pushInfo(self.tr(f"Scanning directory: {input_dir}"))
        feedback.pushInfo(self.tr(f"Output GeoPackage: {output_gpkg}"))

        # Create field structure for inventory layer
        fields = self._create_fields()

        # Create WGS84 CRS for output
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")

        # Initialize feature list
        features = []
        stats = {
            "total_layers": 0,
            "total_errors": 0,
            "vectors": 0,
            "rasters": 0,
            "tables": 0,
        }

        # Scan directory for geospatial files
        feedback.pushInfo(self.tr("Discovering geospatial files..."))
        scan_timestamp = datetime.now().isoformat()

        # Use GDAL to recursively find all geospatial data
        data_sources = self._discover_geospatial_files(
            input_path,
            include_vectors,
            include_rasters,
            include_tables,
            feedback
        )

        if not data_sources:
            feedback.pushWarning(self.tr("No geospatial files found in directory"))
            # Still create empty layer
            self._write_geopackage(output_gpkg, layer_name, fields, [], wgs84_crs, feedback)
            return {self.OUTPUT_GPKG: output_gpkg}

        feedback.pushInfo(self.tr(f"Found {len(data_sources)} data sources to inventory"))

        # Process each data source
        total = len(data_sources)
        for i, data_source in enumerate(data_sources):
            if feedback.isCanceled():
                break

            progress = int((i / total) * 100)
            feedback.setProgress(progress)

            # Extract metadata for this data source
            feature = self._extract_layer_metadata(
                data_source,
                input_path,
                fields,
                wgs84_crs,
                scan_timestamp,
                validate_files,
                parse_metadata,
                include_sidecar,
                feedback
            )

            if feature:
                features.append(feature)
                stats["total_layers"] += 1

                # Update type counts
                data_type = feature.attribute("data_type")
                if data_type == "vector":
                    stats["vectors"] += 1
                elif data_type == "raster":
                    stats["rasters"] += 1
                elif data_type == "table":
                    stats["tables"] += 1
            else:
                stats["total_errors"] += 1

        # Write GeoPackage
        feedback.pushInfo(self.tr("Writing GeoPackage..."))
        self._write_geopackage(output_gpkg, layer_name, fields, features, wgs84_crs, feedback)

        feedback.pushInfo(self.tr(
            f"Inventory complete: {stats['total_layers']} layers "
            f"({stats['vectors']} vectors, {stats['rasters']} rasters, {stats['tables']} tables), "
            f"{stats['total_errors']} errors"
        ))

        return {self.OUTPUT_GPKG: output_gpkg}

    def _create_fields(self):
        """Create the field structure for the inventory layer."""
        fields = QgsFields()

        # ID and Timestamp Fields
        fields.append(QgsField("id", QVariant.Int))  # Will be auto-incremented by GeoPackage
        fields.append(QgsField("record_created", QVariant.String))  # DateTime when record was created
        fields.append(QgsField("file_created", QVariant.String))  # File creation date from filesystem

        # File System Fields
        fields.append(QgsField("file_path", QVariant.String))
        fields.append(QgsField("relative_path", QVariant.String))
        fields.append(QgsField("file_name", QVariant.String))
        fields.append(QgsField("file_size_bytes", QVariant.LongLong))
        fields.append(QgsField("file_modified", QVariant.String))
        fields.append(QgsField("directory_depth", QVariant.Int))
        fields.append(QgsField("parent_directory", QVariant.String))

        # Format/Driver Fields
        fields.append(QgsField("data_type", QVariant.String))
        fields.append(QgsField("format", QVariant.String))
        fields.append(QgsField("driver_name", QVariant.String))
        fields.append(QgsField("container_file", QVariant.String))
        fields.append(QgsField("layer_name", QVariant.String))
        fields.append(QgsField("is_supporting_table", QVariant.Bool))

        # Spatial Fields
        fields.append(QgsField("crs_authid", QVariant.String))
        fields.append(QgsField("crs_wkt", QVariant.String))
        fields.append(QgsField("native_extent", QVariant.String))
        fields.append(QgsField("wgs84_extent", QVariant.String))
        fields.append(QgsField("has_crs", QVariant.Bool))
        fields.append(QgsField("georeference_method", QVariant.String))

        # Vector-Specific Fields
        fields.append(QgsField("geometry_type", QVariant.String))
        fields.append(QgsField("feature_count", QVariant.LongLong))
        fields.append(QgsField("has_z", QVariant.Bool))
        fields.append(QgsField("has_m", QVariant.Bool))
        fields.append(QgsField("has_spatial_index", QVariant.Bool))

        # Raster-Specific Fields
        fields.append(QgsField("raster_width", QVariant.Int))
        fields.append(QgsField("raster_height", QVariant.Int))
        fields.append(QgsField("band_count", QVariant.Int))
        fields.append(QgsField("pixel_size_x", QVariant.Double))
        fields.append(QgsField("pixel_size_y", QVariant.Double))
        fields.append(QgsField("data_types", QVariant.String))
        fields.append(QgsField("nodata_values", QVariant.String))
        fields.append(QgsField("compression", QVariant.String))

        # Attribute Fields
        fields.append(QgsField("field_count", QVariant.Int))
        fields.append(QgsField("field_names", QVariant.String))
        fields.append(QgsField("field_types", QVariant.String))

        # Metadata Fields
        fields.append(QgsField("metadata_present", QVariant.Bool))
        fields.append(QgsField("metadata_file_path", QVariant.String))
        fields.append(QgsField("metadata_standard", QVariant.String))
        fields.append(QgsField("layer_title", QVariant.String))
        fields.append(QgsField("layer_abstract", QVariant.String))
        fields.append(QgsField("keywords", QVariant.String))
        fields.append(QgsField("metadata_author", QVariant.String))
        fields.append(QgsField("metadata_date", QVariant.String))
        fields.append(QgsField("lineage", QVariant.String))
        fields.append(QgsField("constraints", QVariant.String))
        fields.append(QgsField("url", QVariant.String))  # URL from metadata
        fields.append(QgsField("iso_categories", QVariant.String))  # ISO 19115 topic categories
        fields.append(QgsField("contact_info", QVariant.String))  # Contact information (all in one field)
        fields.append(QgsField("links", QVariant.String))  # Related links (comma-separated)

        # Sidecar Files
        fields.append(QgsField("has_prj_file", QVariant.Bool))
        fields.append(QgsField("has_world_file", QVariant.Bool))
        fields.append(QgsField("has_aux_xml", QVariant.Bool))
        fields.append(QgsField("has_metadata_xml", QVariant.Bool))

        # Quality Fields
        fields.append(QgsField("is_valid", QVariant.Bool))
        fields.append(QgsField("has_extent", QVariant.Bool))
        fields.append(QgsField("has_data", QVariant.Bool))
        fields.append(QgsField("issues", QVariant.String))
        fields.append(QgsField("scan_timestamp", QVariant.String))

        return fields

    def _discover_geospatial_files(self, root_path, include_vectors, include_rasters, include_tables, feedback):
        """Discover all geospatial files using GDAL/OGR recursive scanning."""
        data_sources = []

        # Walk through directory tree
        for item_path in root_path.rglob("*"):
            if feedback.isCanceled():
                break

            if not item_path.is_file():
                continue

            # Try to open with GDAL/OGR to see if it's geospatial
            file_str = str(item_path)

            # Try as vector first (OGR)
            if include_vectors or include_tables:
                try:
                    ds = ogr.Open(file_str)
                    if ds is not None:
                        # Check each layer in the data source
                        for i in range(ds.GetLayerCount()):
                            layer = ds.GetLayer(i)
                            layer_name = layer.GetName()
                            has_geom = layer.GetGeomType() != ogr.wkbNone

                            if (has_geom and include_vectors) or (not has_geom and include_tables):
                                data_sources.append({
                                    "path": item_path,
                                    "type": "vector" if has_geom else "table",
                                    "layer_index": i,
                                    "layer_name": layer_name,
                                })
                        ds = None
                        continue
                except:
                    pass

            # Try as raster (GDAL)
            if include_rasters:
                try:
                    ds = gdal.Open(file_str, gdal.GA_ReadOnly)
                    if ds is not None:
                        data_sources.append({
                            "path": item_path,
                            "type": "raster",
                            "layer_index": None,
                            "layer_name": None,
                        })
                        ds = None
                        continue
                except:
                    pass

        return data_sources

    def _extract_layer_metadata(self, data_source, root_path, fields, wgs84_crs,
                                 scan_timestamp, validate, parse_metadata,
                                 include_sidecar, feedback):
        """Extract comprehensive metadata for a data source."""
        try:
            feature = QgsFeature(fields)
            file_path = data_source["path"]
            data_type = data_source["type"]

            feedback.pushInfo(self.tr(f"Processing: {file_path.name}"))

            # Record creation timestamp
            feature.setAttribute("record_created", datetime.now().isoformat())

            # File system metadata
            file_stat = file_path.stat()
            feature.setAttribute("file_path", str(file_path))
            feature.setAttribute("relative_path", str(file_path.relative_to(root_path)))
            feature.setAttribute("file_name", file_path.name)
            feature.setAttribute("file_size_bytes", file_stat.st_size)
            feature.setAttribute("file_modified", datetime.fromtimestamp(file_stat.st_mtime).isoformat())

            # Try to get file creation time (platform-dependent)
            try:
                # st_ctime on Windows is creation time, on Unix it's metadata change time
                # st_birthtime exists on some platforms for true creation time
                if hasattr(file_stat, 'st_birthtime'):
                    feature.setAttribute("file_created", datetime.fromtimestamp(file_stat.st_birthtime).isoformat())
                else:
                    feature.setAttribute("file_created", datetime.fromtimestamp(file_stat.st_ctime).isoformat())
            except:
                feature.setAttribute("file_created", None)

            feature.setAttribute("parent_directory", file_path.parent.name)
            feature.setAttribute("data_type", data_type)
            feature.setAttribute("scan_timestamp", scan_timestamp)

            # Calculate directory depth
            try:
                depth = len(file_path.relative_to(root_path).parts) - 1
                feature.setAttribute("directory_depth", depth)
            except:
                feature.setAttribute("directory_depth", 0)

            # Extract metadata based on type
            if data_type in ["vector", "table"]:
                self._extract_vector_metadata(feature, data_source, wgs84_crs, validate, feedback)
            elif data_type == "raster":
                self._extract_raster_metadata(feature, data_source, wgs84_crs, validate, feedback)

            # Check for sidecar files if requested
            if include_sidecar:
                self._check_sidecar_files(feature, file_path)

            # Parse GIS metadata if requested
            if parse_metadata:
                self._parse_gis_metadata(feature, file_path, feedback)

            return feature

        except Exception as e:
            feedback.reportError(self.tr(f"Error processing {file_path.name}: {str(e)}"))
            return None

    def _extract_vector_metadata(self, feature, data_source, wgs84_crs, validate, feedback):
        """Extract metadata from vector data source using OGR."""
        try:
            file_path = data_source["path"]
            layer_index = data_source["layer_index"]

            ds = ogr.Open(str(file_path))
            if ds is None:
                feature.setAttribute("is_valid", False)
                return

            layer = ds.GetLayer(layer_index)
            if layer is None:
                feature.setAttribute("is_valid", False)
                ds = None
                return

            # Driver info
            driver = ds.GetDriver()
            feature.setAttribute("driver_name", driver.GetName())
            feature.setAttribute("format", driver.GetName())

            # Layer info
            if data_source["layer_name"]:
                feature.setAttribute("layer_name", data_source["layer_name"])
                feature.setAttribute("container_file", str(file_path))

            # Check if table or vector
            geom_type = layer.GetGeomType()
            is_table = geom_type == ogr.wkbNone
            feature.setAttribute("is_supporting_table", is_table)

            if not is_table:
                # Geometry metadata
                geom_type_name = ogr.GeometryTypeToName(geom_type)
                feature.setAttribute("geometry_type", geom_type_name)
                feature.setAttribute("has_z", ogr.GT_HasZ(geom_type))
                feature.setAttribute("has_m", ogr.GT_HasM(geom_type))

                # CRS
                srs = layer.GetSpatialRef()
                if srs:
                    feature.setAttribute("has_crs", True)
                    feature.setAttribute("crs_authid", srs.GetAuthorityCode(None))
                    feature.setAttribute("crs_wkt", srs.ExportToWkt())
                    feature.setAttribute("georeference_method", "embedded")
                else:
                    feature.setAttribute("has_crs", False)

                # Extent
                extent = layer.GetExtent()
                if extent:
                    feature.setAttribute("has_extent", True)
                    xmin, xmax, ymin, ymax = extent
                    feature.setAttribute("native_extent", f"{xmin},{ymin},{xmax},{ymax}")

                    # Transform extent to WGS84 and create polygon
                    if srs:
                        source_crs = QgsCoordinateReferenceSystem()
                        source_crs.createFromWkt(srs.ExportToWkt())
                        transform = QgsCoordinateTransform(source_crs, wgs84_crs, QgsProject.instance())

                        try:
                            rect = QgsRectangle(xmin, ymin, xmax, ymax)
                            rect_transformed = transform.transformBoundingBox(rect)

                            feature.setAttribute("wgs84_extent",
                                f"{rect_transformed.xMinimum()},{rect_transformed.yMinimum()},"
                                f"{rect_transformed.xMaximum()},{rect_transformed.yMaximum()}")

                            # Create extent polygon geometry
                            extent_geom = QgsGeometry.fromRect(rect_transformed)
                            feature.setGeometry(extent_geom)
                        except Exception as e:
                            feedback.pushWarning(self.tr(f"Could not transform extent: {str(e)}"))
                            # Use native extent as fallback
                            rect = QgsRectangle(xmin, ymin, xmax, ymax)
                            extent_geom = QgsGeometry.fromRect(rect)
                            feature.setGeometry(extent_geom)

            # Feature count
            feature_count = layer.GetFeatureCount()
            feature.setAttribute("feature_count", feature_count)
            feature.setAttribute("has_data", feature_count > 0)

            # Field information
            layer_defn = layer.GetLayerDefn()
            field_count = layer_defn.GetFieldCount()
            feature.setAttribute("field_count", field_count)

            if field_count > 0:
                field_names = []
                field_types = []
                for i in range(field_count):
                    field_defn = layer_defn.GetFieldDefn(i)
                    field_names.append(field_defn.GetName())
                    field_types.append(field_defn.GetTypeName())

                feature.setAttribute("field_names", ",".join(field_names))
                feature.setAttribute("field_types", ",".join(field_types))

            # Validation checks if requested
            is_valid = True
            issues = []

            if validate:
                # Thorough validation - attempt to read actual features
                try:
                    if not is_table and feature_count > 0:
                        # Try to read the first feature to verify data integrity
                        layer.ResetReading()
                        test_feature = layer.GetNextFeature()
                        if test_feature is None:
                            is_valid = False
                            issues.append("Cannot read features")
                        else:
                            # Try to read geometry if it's a spatial layer
                            geom = test_feature.GetGeometryRef()
                            if geom is None and not is_table:
                                issues.append("Missing geometries")
                            elif geom is not None and not geom.IsValid():
                                issues.append("Invalid geometries detected")
                    elif is_table and feature_count > 0:
                        # For tables, just try to read first record
                        layer.ResetReading()
                        test_feature = layer.GetNextFeature()
                        if test_feature is None:
                            is_valid = False
                            issues.append("Cannot read records")

                    # Check for common issues
                    if not is_table and not srs:
                        issues.append("Missing CRS")
                    if feature_count == 0:
                        issues.append("Empty dataset")

                except Exception as e:
                    is_valid = False
                    issues.append(f"Validation error: {str(e)}")

            feature.setAttribute("is_valid", is_valid)
            if issues:
                feature.setAttribute("issues", ",".join(issues))

            ds = None

        except Exception as e:
            feedback.reportError(self.tr(f"Error extracting vector metadata: {str(e)}"))
            feature.setAttribute("is_valid", False)

    def _extract_raster_metadata(self, feature, data_source, wgs84_crs, validate, feedback):
        """Extract metadata from raster data source using GDAL."""
        try:
            file_path = data_source["path"]

            ds = gdal.Open(str(file_path), gdal.GA_ReadOnly)
            if ds is None:
                feature.setAttribute("is_valid", False)
                return

            # Driver info
            driver = ds.GetDriver()
            feature.setAttribute("driver_name", driver.ShortName)
            feature.setAttribute("format", driver.LongName)

            # Raster dimensions
            feature.setAttribute("raster_width", ds.RasterXSize)
            feature.setAttribute("raster_height", ds.RasterYSize)
            feature.setAttribute("band_count", ds.RasterCount)

            # Geotransform and pixel size
            geotransform = ds.GetGeoTransform()
            if geotransform:
                feature.setAttribute("pixel_size_x", abs(geotransform[1]))
                feature.setAttribute("pixel_size_y", abs(geotransform[5]))

            # CRS
            projection = ds.GetProjection()
            if projection:
                feature.setAttribute("has_crs", True)
                srs = ogr.osr.SpatialReference(wkt=projection)
                feature.setAttribute("crs_authid", srs.GetAuthorityCode(None))
                feature.setAttribute("crs_wkt", projection)

                # Determine georeference method
                if geotransform and geotransform != (0, 1, 0, 0, 0, 1):
                    feature.setAttribute("georeference_method", "header")
                else:
                    # Check for world file
                    world_file = self._find_world_file(file_path)
                    if world_file:
                        feature.setAttribute("georeference_method", "sidecar")
                    else:
                        feature.setAttribute("georeference_method", "none")
            else:
                feature.setAttribute("has_crs", False)

            # Extent
            if geotransform and projection:
                xmin = geotransform[0]
                ymax = geotransform[3]
                xmax = xmin + geotransform[1] * ds.RasterXSize
                ymin = ymax + geotransform[5] * ds.RasterYSize

                feature.setAttribute("has_extent", True)
                feature.setAttribute("native_extent", f"{xmin},{ymin},{xmax},{ymax}")

                # Transform to WGS84
                source_crs = QgsCoordinateReferenceSystem()
                source_crs.createFromWkt(projection)
                transform = QgsCoordinateTransform(source_crs, wgs84_crs, QgsProject.instance())

                try:
                    rect = QgsRectangle(xmin, ymin, xmax, ymax)
                    rect_transformed = transform.transformBoundingBox(rect)

                    feature.setAttribute("wgs84_extent",
                        f"{rect_transformed.xMinimum()},{rect_transformed.yMinimum()},"
                        f"{rect_transformed.xMaximum()},{rect_transformed.yMaximum()}")

                    # Create extent polygon geometry
                    extent_geom = QgsGeometry.fromRect(rect_transformed)
                    feature.setGeometry(extent_geom)
                except Exception as e:
                    feedback.pushWarning(self.tr(f"Could not transform raster extent: {str(e)}"))
                    rect = QgsRectangle(xmin, ymin, xmax, ymax)
                    extent_geom = QgsGeometry.fromRect(rect)
                    feature.setGeometry(extent_geom)

            # Band information
            if ds.RasterCount > 0:
                data_types = []
                nodata_values = []

                for i in range(1, min(ds.RasterCount + 1, 10)):  # Limit to first 10 bands
                    band = ds.GetRasterBand(i)
                    data_types.append(gdal.GetDataTypeName(band.DataType))
                    nodata = band.GetNoDataValue()
                    nodata_values.append(str(nodata) if nodata is not None else "None")

                feature.setAttribute("data_types", ",".join(data_types))
                feature.setAttribute("nodata_values", ",".join(nodata_values))

            # Compression
            metadata = ds.GetMetadata()
            if "COMPRESSION" in metadata:
                feature.setAttribute("compression", metadata["COMPRESSION"])

            feature.setAttribute("has_data", ds.RasterCount > 0)

            # Validation checks if requested
            is_valid = True
            issues = []

            if validate:
                # Thorough validation - attempt to read actual raster data
                try:
                    if ds.RasterCount > 0:
                        # Try to read a small sample from the first band to verify data integrity
                        band = ds.GetRasterBand(1)

                        # Read a small window (1x1 pixel from center)
                        x_center = ds.RasterXSize // 2
                        y_center = ds.RasterYSize // 2

                        try:
                            sample = band.ReadAsArray(x_center, y_center, 1, 1)
                            if sample is None:
                                is_valid = False
                                issues.append("Cannot read raster data")
                        except Exception as read_err:
                            is_valid = False
                            issues.append(f"Data read error: {str(read_err)}")

                        # Check for common issues
                        if not projection:
                            issues.append("Missing CRS")
                        if not geotransform or geotransform == (0, 1, 0, 0, 0, 1):
                            issues.append("Missing geotransform")

                        # Check band validity
                        for i in range(1, min(ds.RasterCount + 1, 5)):  # Check first 5 bands
                            test_band = ds.GetRasterBand(i)
                            if test_band is None:
                                issues.append(f"Band {i} is invalid")
                                is_valid = False
                                break
                    else:
                        issues.append("No raster bands")
                        is_valid = False

                except Exception as e:
                    is_valid = False
                    issues.append(f"Validation error: {str(e)}")

            feature.setAttribute("is_valid", is_valid)
            if issues:
                feature.setAttribute("issues", ",".join(issues))

            ds = None

        except Exception as e:
            feedback.reportError(self.tr(f"Error extracting raster metadata: {str(e)}"))
            feature.setAttribute("is_valid", False)
            feature.setAttribute("issues", f"Extraction error: {str(e)}")

    def _find_world_file(self, file_path):
        """Find world file for raster."""
        # Common world file extensions
        world_extensions = {
            ".tif": ".tfw", ".tiff": ".tfw",
            ".jpg": ".jgw", ".jpeg": ".jgw",
            ".png": ".pgw",
            ".gif": ".gfw",
            ".bmp": ".bpw",
        }

        ext = file_path.suffix.lower()
        if ext in world_extensions:
            world_file = file_path.with_suffix(world_extensions[ext])
            if world_file.exists():
                return world_file

        return None

    def _check_sidecar_files(self, feature, file_path):
        """Check for presence of sidecar files."""
        # Check for .prj file
        prj_file = file_path.with_suffix(".prj")
        feature.setAttribute("has_prj_file", prj_file.exists())

        # Check for world file
        world_file = self._find_world_file(file_path)
        feature.setAttribute("has_world_file", world_file is not None)

        # Check for .aux.xml
        aux_xml = Path(str(file_path) + ".aux.xml")
        feature.setAttribute("has_aux_xml", aux_xml.exists())

        # Check for metadata .xml
        metadata_xml = file_path.with_suffix(".xml")
        if metadata_xml.exists() and metadata_xml != aux_xml:
            feature.setAttribute("has_metadata_xml", True)
            feature.setAttribute("metadata_file_path", str(metadata_xml))
        else:
            feature.setAttribute("has_metadata_xml", False)

    def _parse_gis_metadata(self, feature, file_path, feedback):
        """Parse GIS metadata from XML files."""
        try:
            # Look for metadata XML file
            metadata_xml = file_path.with_suffix(".xml")

            # Also check for .shp.xml pattern
            if not metadata_xml.exists() and file_path.suffix.lower() == ".shp":
                metadata_xml = Path(str(file_path) + ".xml")

            if not metadata_xml.exists():
                feature.setAttribute("metadata_present", False)
                return

            # Try to parse XML
            tree = ET.parse(metadata_xml)
            root = tree.getroot()

            feature.setAttribute("metadata_present", True)

            # Detect metadata standard based on root element
            if "metadata" in root.tag.lower():
                if "gmd" in root.tag or "MD_Metadata" in root.tag:
                    feature.setAttribute("metadata_standard", "ISO 19115")
                elif "fgdc" in root.tag or "idinfo" in [child.tag for child in root]:
                    feature.setAttribute("metadata_standard", "FGDC")
                else:
                    feature.setAttribute("metadata_standard", "ESRI")

            # Try to extract common fields (simplified - would need full parsers for each standard)
            # This is a basic implementation that looks for common element names
            contact_parts = []
            iso_cats = []
            url_links = []

            for elem in root.iter():
                tag_lower = elem.tag.lower()

                # Basic fields
                if "title" in tag_lower and not feature.attribute("layer_title"):
                    if elem.text:
                        feature.setAttribute("layer_title", elem.text)
                elif "abstract" in tag_lower and not feature.attribute("layer_abstract"):
                    if elem.text:
                        feature.setAttribute("layer_abstract", elem.text)
                elif "keyword" in tag_lower:
                    keywords = feature.attribute("keywords") or ""
                    if elem.text:
                        keywords += ("," if keywords else "") + elem.text
                        feature.setAttribute("keywords", keywords)

                # URL/Online resource
                elif "url" in tag_lower or "linkage" in tag_lower or "onlineres" in tag_lower:
                    if elem.text and not feature.attribute("url"):
                        feature.setAttribute("url", elem.text)
                    elif elem.text:
                        url_links.append(elem.text)

                # ISO Topic Categories
                elif "topiccategory" in tag_lower or "md_topiccategorycode" in tag_lower:
                    if elem.text:
                        iso_cats.append(elem.text)

                # Contact Information - collect various contact fields
                elif "contact" in tag_lower or "responsible" in tag_lower:
                    # Look for name, organization, email, phone
                    if "name" in tag_lower or "individualname" in tag_lower or "organisationname" in tag_lower:
                        if elem.text:
                            contact_parts.append(elem.text)
                    elif "email" in tag_lower or "electronicmailaddress" in tag_lower:
                        if elem.text:
                            contact_parts.append(f"Email: {elem.text}")
                    elif "phone" in tag_lower or "voice" in tag_lower:
                        if elem.text:
                            contact_parts.append(f"Phone: {elem.text}")

                # Additional links/references
                elif "link" in tag_lower or "reference" in tag_lower:
                    if elem.text and elem.text.startswith(("http://", "https://", "ftp://")):
                        url_links.append(elem.text)

            # Set compiled fields
            if iso_cats:
                feature.setAttribute("iso_categories", ",".join(set(iso_cats)))

            if contact_parts:
                # Remove duplicates and join
                unique_contacts = []
                seen = set()
                for contact in contact_parts:
                    if contact not in seen:
                        unique_contacts.append(contact)
                        seen.add(contact)
                feature.setAttribute("contact_info", " | ".join(unique_contacts))

            if url_links:
                # Set additional links (excluding the main URL already set)
                feature.setAttribute("links", ",".join(set(url_links)))

        except Exception as e:
            feedback.pushDebugInfo(self.tr(f"Could not parse metadata XML: {str(e)}"))
            feature.setAttribute("metadata_present", False)

    def _write_geopackage(self, output_path, layer_name, fields, features, crs, feedback):
        """Write features to GeoPackage."""
        try:
            # Create vector layer writer options
            save_options = QgsVectorFileWriter.SaveVectorOptions()
            save_options.driverName = "GPKG"
            save_options.layerName = layer_name

            # Check if file exists to determine action type
            output_file = Path(output_path)
            if output_file.exists():
                save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            else:
                save_options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

            # Write the layer
            writer = QgsVectorFileWriter.create(
                output_path,
                fields,
                QgsWkbTypes.Polygon,
                crs,
                QgsProject.instance().transformContext(),
                save_options
            )

            if writer.hasError() != QgsVectorFileWriter.NoError:
                raise QgsProcessingException(
                    self.tr(f"Error creating GeoPackage: {writer.errorMessage()}")
                )

            # Add features with auto-incrementing ID
            for idx, feature in enumerate(features, start=1):
                feature.setAttribute("id", idx)
                writer.addFeature(feature)

            del writer
            feedback.pushInfo(self.tr(f"Successfully wrote {len(features)} features to {layer_name}"))

        except Exception as e:
            raise QgsProcessingException(self.tr(f"Error writing GeoPackage: {str(e)}"))
