"""
Database Manager for Metadata Manager plugin.

Handles connection to unified GeoPackage database, schema initialization,
validation, and upgrade management.

Author: John Zastrow
License: MIT
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from qgis.core import QgsMessageLog, Qgis

from .schema import DatabaseSchema


class DatabaseManager:
    """
    Manages unified GeoPackage database shared with Inventory Miner.

    Responsibilities:
    - Validate database created by Inventory Miner
    - Initialize Metadata Manager tables
    - Track schema versions independently
    - Provide connection management
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to GeoPackage database (e.g., geospatial_catalog.gpkg)
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.is_connected = False

    def connect(self, db_path: str) -> bool:
        """
        Connect to database.

        Args:
            db_path: Path to GeoPackage database

        Returns:
            True if connected successfully
        """
        try:
            self.db_path = db_path
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row

            # Load SpatiaLite extension (required for GeoPackage operations)
            # This enables spatial functions like ST_IsEmpty used by inventory triggers
            self.connection.enable_load_extension(True)
            try:
                # Try loading SpatiaLite (path varies by platform)
                try:
                    self.connection.load_extension("mod_spatialite")
                except:
                    try:
                        self.connection.load_extension("libspatialite")
                    except:
                        # On Windows, might be in QGIS install
                        import platform
                        if platform.system() == "Windows":
                            import os
                            qgis_prefix = os.environ.get('QGIS_PREFIX_PATH', '')
                            if qgis_prefix:
                                spatialite_path = os.path.join(qgis_prefix, 'bin', 'mod_spatialite')
                                self.connection.load_extension(spatialite_path)
                        else:
                            raise
            except Exception as ext_error:
                QgsMessageLog.logMessage(
                    f"Warning: Could not load SpatiaLite extension: {ext_error}\n"
                    f"Spatial functions may not work in triggers.",
                    "Metadata Manager",
                    Qgis.Warning
                )
            finally:
                self.connection.enable_load_extension(False)

            self.is_connected = True

            QgsMessageLog.logMessage(
                f"Connected to database: {db_path}",
                "Metadata Manager",
                Qgis.Info
            )
            return True

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Failed to connect to database: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            self.is_connected = False
            return False

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.is_connected = False

    def validate_inventory_database(self) -> Tuple[bool, str]:
        """
        Validate that database was created by Inventory Miner.

        Returns:
            Tuple of (is_valid, message)
        """
        if not self.is_connected:
            return False, "Not connected to database"

        try:
            cursor = self.connection.cursor()

            # Check for geospatial_inventory table
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='geospatial_inventory'
            """)

            if cursor.fetchone() is None:
                return False, (
                    "This database was not created by Inventory Miner. "
                    "The 'geospatial_inventory' table is missing. "
                    "Please run Inventory Miner first to create the database."
                )

            # Check for required metadata tracking fields in inventory
            cursor.execute("PRAGMA table_info(geospatial_inventory)")
            columns = {row[1] for row in cursor.fetchall()}

            required_fields = {
                'metadata_status',
                'metadata_last_updated',
                'metadata_target',
                'metadata_cached',
                'retired_datetime'
            }

            missing_fields = required_fields - columns
            if missing_fields:
                return False, (
                    f"Inventory database is outdated. Missing fields: {', '.join(missing_fields)}. "
                    f"Please update Inventory Miner to v0.2.0 or higher and re-run it."
                )

            return True, "Database validated successfully"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def check_metadata_manager_tables_exist(self) -> bool:
        """
        Check if Metadata Manager tables already exist.

        Returns:
            True if tables exist
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()

            # Check for metadata_cache table as indicator
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='metadata_cache'
            """)

            return cursor.fetchone() is not None

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error checking tables: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return False

    def initialize_metadata_manager_tables(self) -> Tuple[bool, str]:
        """
        Create Metadata Manager tables in existing database.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_connected:
            return False, "Not connected to database"

        try:
            cursor = self.connection.cursor()

            # Create all tables
            schemas = DatabaseSchema.get_all_schemas()
            for schema_sql in schemas:
                cursor.execute(schema_sql)

            # Insert initial data
            initial_data = DatabaseSchema.get_initial_data()
            for data_sql in initial_data:
                cursor.execute(data_sql)

            self.connection.commit()

            QgsMessageLog.logMessage(
                "Metadata Manager tables created successfully",
                "Metadata Manager",
                Qgis.Success
            )

            return True, "Tables initialized successfully"

        except Exception as e:
            self.connection.rollback()
            error_msg = f"Failed to initialize tables: {str(e)}"
            QgsMessageLog.logMessage(
                error_msg,
                "Metadata Manager",
                Qgis.Critical
            )
            return False, error_msg

    def get_schema_version(self, schema_key: str = 'metadata_schema_version') -> Optional[str]:
        """
        Get schema version from plugin_info table.

        Args:
            schema_key: Version key ('inventory_schema_version' or 'metadata_schema_version')

        Returns:
            Version string or None if not found
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT value FROM plugin_info WHERE key = ?",
                (schema_key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting schema version: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def update_schema_version(self, version: str, schema_key: str = 'metadata_schema_version') -> bool:
        """
        Update schema version in plugin_info table.

        Args:
            version: New version string
            schema_key: Version key to update

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO plugin_info (key, value, updated)
                VALUES (?, ?, datetime('now'))
                """,
                (schema_key, version)
            )
            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Error updating schema version: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            return False

    def log_upgrade(self, from_version: str, to_version: str, success: bool, notes: str = "") -> bool:
        """
        Log schema upgrade to upgrade_history table.

        Args:
            from_version: Previous version
            to_version: New version
            success: Whether upgrade succeeded
            notes: Additional notes

        Returns:
            True if logged successfully
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO upgrade_history (from_version, to_version, tool, success, notes)
                VALUES (?, ?, 'metadata_manager', ?, ?)
                """,
                (from_version, to_version, 1 if success else 0, notes)
            )
            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Error logging upgrade: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return False

    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[sqlite3.Row]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of rows or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Query error: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """
        Execute an INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return True

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Update error: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return False

    def get_inventory_statistics(self) -> Optional[Dict[str, int]]:
        """
        Get metadata completion statistics from inventory.

        Returns:
            Dictionary with statistics or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()

            # Get total count (excluding retired)
            cursor.execute("""
                SELECT COUNT(*) FROM geospatial_inventory
                WHERE retired_datetime IS NULL
            """)
            total = cursor.fetchone()[0]

            # Get counts by status
            cursor.execute("""
                SELECT
                    COALESCE(metadata_status, 'none') as status,
                    COUNT(*) as count
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                GROUP BY metadata_status
            """)

            stats = {
                'total': total,
                'complete': 0,
                'partial': 0,
                'none': 0
            }

            for row in cursor.fetchall():
                status = row['status']
                count = row['count']
                if status in stats:
                    stats[status] = count

            return stats

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting statistics: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def get_statistics_by_directory(self) -> Optional[List[Dict]]:
        """
        Get metadata completion statistics grouped by directory.

        Returns:
            List of dictionaries with directory stats or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    parent_directory,
                    COUNT(*) as total,
                    SUM(CASE WHEN metadata_status = 'complete' THEN 1 ELSE 0 END) as complete,
                    SUM(CASE WHEN metadata_status = 'partial' THEN 1 ELSE 0 END) as partial,
                    SUM(CASE WHEN metadata_status IS NULL OR metadata_status = 'none' THEN 1 ELSE 0 END) as none
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                GROUP BY parent_directory
                ORDER BY none DESC, total DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'directory': row['parent_directory'] or 'Root',
                    'total': row['total'],
                    'complete': row['complete'],
                    'partial': row['partial'],
                    'none': row['none'],
                    'completion_pct': (row['complete'] / row['total'] * 100) if row['total'] > 0 else 0
                })

            return results

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting directory statistics: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def get_statistics_by_data_type(self) -> Optional[List[Dict]]:
        """
        Get metadata completion statistics grouped by data type.

        Returns:
            List of dictionaries with data type stats or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    data_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN metadata_status = 'complete' THEN 1 ELSE 0 END) as complete,
                    SUM(CASE WHEN metadata_status = 'partial' THEN 1 ELSE 0 END) as partial,
                    SUM(CASE WHEN metadata_status IS NULL OR metadata_status = 'none' THEN 1 ELSE 0 END) as none
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                GROUP BY data_type
                ORDER BY total DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'data_type': row['data_type'] or 'Unknown',
                    'total': row['total'],
                    'complete': row['complete'],
                    'partial': row['partial'],
                    'none': row['none'],
                    'completion_pct': (row['complete'] / row['total'] * 100) if row['total'] > 0 else 0
                })

            return results

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting data type statistics: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def get_statistics_by_file_format(self) -> Optional[List[Dict]]:
        """
        Get metadata completion statistics grouped by file format.

        Returns:
            List of dictionaries with file format stats or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    format,
                    COUNT(*) as total,
                    SUM(CASE WHEN metadata_status = 'complete' THEN 1 ELSE 0 END) as complete,
                    SUM(CASE WHEN metadata_status = 'partial' THEN 1 ELSE 0 END) as partial,
                    SUM(CASE WHEN metadata_status IS NULL OR metadata_status = 'none' THEN 1 ELSE 0 END) as none
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                GROUP BY format
                ORDER BY total DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'file_format': row['format'] or 'Unknown',
                    'total': row['total'],
                    'complete': row['complete'],
                    'partial': row['partial'],
                    'none': row['none'],
                    'completion_pct': (row['complete'] / row['total'] * 100) if row['total'] > 0 else 0
                })

            return results

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting file format statistics: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def get_statistics_by_crs(self) -> Optional[List[Dict]]:
        """
        Get metadata completion statistics grouped by CRS.

        Returns:
            List of dictionaries with CRS stats or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    crs_authid,
                    COUNT(*) as total,
                    SUM(CASE WHEN metadata_status = 'complete' THEN 1 ELSE 0 END) as complete,
                    SUM(CASE WHEN metadata_status = 'partial' THEN 1 ELSE 0 END) as partial,
                    SUM(CASE WHEN metadata_status IS NULL OR metadata_status = 'none' THEN 1 ELSE 0 END) as none
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                GROUP BY crs_authid
                ORDER BY total DESC
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'crs': row['crs_authid'] or 'Unknown',
                    'total': row['total'],
                    'complete': row['complete'],
                    'partial': row['partial'],
                    'none': row['none'],
                    'completion_pct': (row['complete'] / row['total'] * 100) if row['total'] > 0 else 0
                })

            return results

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting CRS statistics: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def get_priority_recommendations(self, limit: int = 5) -> Optional[List[Dict]]:
        """
        Get priority recommendations for metadata completion.

        Returns highest-impact directories/types needing metadata.

        Args:
            limit: Maximum number of recommendations

        Returns:
            List of dictionaries with recommendations or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()

            # Get directories with most layers lacking metadata
            cursor.execute("""
                SELECT
                    parent_directory,
                    format,
                    COUNT(*) as count
                FROM geospatial_inventory
                WHERE retired_datetime IS NULL
                  AND (metadata_status IS NULL OR metadata_status = 'none')
                GROUP BY parent_directory, format
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'directory': row['parent_directory'] or 'Root',
                    'file_format': row['format'] or 'Unknown',
                    'count': row['count'],
                    'recommendation': f"{row['count']} {row['format'] or 'files'} in {row['parent_directory'] or 'Root'} need metadata"
                })

            return results

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting recommendations: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def save_metadata_to_cache(self, layer_path: str, layer_name: str, metadata: Dict, in_sync: bool = False) -> bool:
        """
        Save metadata to metadata_cache table.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer (for container files with multiple layers)
            metadata: Dictionary containing metadata fields
            in_sync: Whether metadata has been written to target (file/database)

        Returns:
            True if saved successfully
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()

            # Convert metadata dict to JSON
            metadata_json = json.dumps(metadata, indent=2)

            # Insert or replace metadata cache entry
            # Use both layer_path AND layer_name to uniquely identify layers
            cursor.execute(
                """
                INSERT OR REPLACE INTO metadata_cache (
                    layer_path,
                    layer_name,
                    metadata_json,
                    created_date,
                    last_edited_date,
                    in_sync
                ) VALUES (?, ?, ?,
                    COALESCE((SELECT created_date FROM metadata_cache WHERE layer_path = ? AND layer_name = ?), datetime('now')),
                    datetime('now'),
                    ?
                )
                """,
                (layer_path, layer_name, metadata_json, layer_path, layer_name, 1 if in_sync else 0)
            )

            self.connection.commit()

            QgsMessageLog.logMessage(
                f"Metadata cached for: {layer_path} / {layer_name}",
                "Metadata Manager",
                Qgis.Info
            )
            return True

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Error saving metadata to cache: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            return False

    def load_metadata_from_cache(self, layer_path: str, layer_name: str = None) -> Optional[Dict]:
        """
        Load metadata from metadata_cache table.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer (for container files with multiple layers)

        Returns:
            Dictionary containing metadata or None if not found
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()

            # Use both layer_path and layer_name to uniquely identify layers
            if layer_name:
                cursor.execute(
                    "SELECT metadata_json FROM metadata_cache WHERE layer_path = ? AND layer_name = ?",
                    (layer_path, layer_name)
                )
            else:
                # Fallback for backward compatibility if layer_name not provided
                cursor.execute(
                    "SELECT metadata_json FROM metadata_cache WHERE layer_path = ?",
                    (layer_path,)
                )

            row = cursor.fetchone()
            if row:
                metadata = json.loads(row['metadata_json'])
                QgsMessageLog.logMessage(
                    f"Metadata loaded from cache: {layer_path}" + (f" / {layer_name}" if layer_name else ""),
                    "Metadata Manager",
                    Qgis.Info
                )
                return metadata
            else:
                return None

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error loading metadata from cache: {str(e)}",
                "Metadata Manager",
                Qgis.Warning
            )
            return None

    def update_inventory_metadata_status(
        self,
        layer_path: str,
        layer_name: str,
        status: str,
        target: str = 'file',
        cached: bool = True
    ) -> bool:
        """
        Update metadata tracking fields in geospatial_inventory table.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer (for container files with multiple layers)
            status: Metadata status ('complete', 'partial', 'none')
            target: Metadata target location ('file', 'database', 'sidecar')
            cached: Whether metadata is cached (default True)

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()

            # Match both file_path AND layer_name to uniquely identify the layer
            # This prevents updating all layers in a container file
            cursor.execute(
                """
                UPDATE geospatial_inventory
                SET
                    metadata_status = ?,
                    metadata_last_updated = datetime('now'),
                    metadata_target = ?,
                    metadata_cached = ?
                WHERE file_path = ? AND layer_name = ?
                """,
                (status, target, 1 if cached else 0, layer_path, layer_name)
            )

            self.connection.commit()

            if cursor.rowcount > 0:
                QgsMessageLog.logMessage(
                    f"✅ Inventory updated: {layer_path} / {layer_name} → status={status}",
                    "Metadata Manager",
                    Qgis.Success
                )
                return True
            else:
                # Try to find similar layers for debugging
                cursor.execute(
                    "SELECT file_path, layer_name FROM geospatial_inventory WHERE file_path = ? LIMIT 5",
                    (layer_path,)
                )
                similar = [f"{row['file_path']} / {row['layer_name']}" for row in cursor.fetchall()]
                QgsMessageLog.logMessage(
                    f"⚠ Layer not found in inventory: {layer_path} / {layer_name}\n"
                    f"Layers with same file_path: {similar[:3] if similar else 'none found'}",
                    "Metadata Manager",
                    Qgis.Warning
                )
                return False

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Error updating inventory: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            return False

    def fix_incorrect_metadata_status(self) -> tuple[bool, str]:
        """
        Fix layers incorrectly marked as 'complete' when they don't have metadata in cache.

        This can happen if layers were marked as complete due to a bug where all layers
        in a container file were updated when only one layer had metadata saved.

        Returns:
            Tuple of (success, message)
        """
        if not self.is_connected:
            return False, "Not connected to database"

        try:
            cursor = self.connection.cursor()

            # First, check how many layers need fixing
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM geospatial_inventory
                WHERE metadata_status = 'complete'
                AND NOT EXISTS (
                    SELECT 1 FROM metadata_cache
                    WHERE metadata_cache.layer_path = geospatial_inventory.file_path
                    AND metadata_cache.layer_name = geospatial_inventory.layer_name
                )
            """)

            incorrect_count = cursor.fetchone()[0]

            if incorrect_count == 0:
                return True, "No incorrect metadata status found. Database is correct."

            QgsMessageLog.logMessage(
                f"Found {incorrect_count} layers incorrectly marked as 'complete'",
                "Metadata Manager",
                Qgis.Info
            )

            # Fix the incorrect status
            cursor.execute("""
                UPDATE geospatial_inventory
                SET metadata_status = 'none',
                    metadata_cached = 0,
                    metadata_last_updated = datetime('now')
                WHERE metadata_status = 'complete'
                AND NOT EXISTS (
                    SELECT 1 FROM metadata_cache
                    WHERE metadata_cache.layer_path = geospatial_inventory.file_path
                    AND metadata_cache.layer_name = geospatial_inventory.layer_name
                )
            """)

            self.connection.commit()

            message = f"Fixed {cursor.rowcount} layers that were incorrectly marked as 'complete'"

            QgsMessageLog.logMessage(
                message,
                "Metadata Manager",
                Qgis.Success
            )

            return True, message

        except Exception as e:
            self.connection.rollback()
            error_msg = f"Error fixing metadata status: {str(e)}"
            QgsMessageLog.logMessage(
                error_msg,
                "Metadata Manager",
                Qgis.Critical
            )
            return False, error_msg

    def update_metadata_write_status(
        self,
        layer_path: str,
        layer_name: str,
        target_location: str,
        in_sync: bool = True
    ) -> bool:
        """
        Update metadata_cache with write status after writing to target.

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer
            target_location: Path to .qmd file or "embedded:path/to/file.gpkg"
            in_sync: Whether cache is in sync with target (default True after write)

        Returns:
            True if updated successfully
        """
        if not self.is_connected:
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                UPDATE metadata_cache
                SET
                    last_written_date = datetime('now'),
                    target_location = ?,
                    in_sync = ?
                WHERE layer_path = ? AND layer_name = ?
                """,
                (target_location, 1 if in_sync else 0, layer_path, layer_name)
            )

            self.connection.commit()

            if cursor.rowcount > 0:
                QgsMessageLog.logMessage(
                    f"Metadata write status updated: {layer_path} / {layer_name}",
                    "Metadata Manager",
                    Qgis.Success
                )
                return True
            else:
                QgsMessageLog.logMessage(
                    f"No metadata cache entry found to update: {layer_path} / {layer_name}",
                    "Metadata Manager",
                    Qgis.Warning
                )
                return False

        except Exception as e:
            self.connection.rollback()
            QgsMessageLog.logMessage(
                f"Error updating metadata write status: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            return False

    def get_smart_defaults(self, layer_path: str, layer_name: str) -> Optional[Dict]:
        """
        Get smart default metadata values from inventory table.

        Auto-populates metadata fields from inventory data to save time:
        - Title (from layer_name, converted to Title Case)
        - CRS and extents
        - Geometry type, feature count (vectors)
        - Raster dimensions, band count (rasters)
        - Field list
        - File metadata (creation date, format, etc.)
        - Existing GIS metadata if available

        Args:
            layer_path: Full path to the layer file
            layer_name: Name of the layer

        Returns:
            Dictionary with smart default values or None on error
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()

            # Query comprehensive metadata from inventory
            cursor.execute(
                """
                SELECT
                    layer_name,
                    file_path,
                    format,
                    data_type,
                    crs_authid,
                    native_extent,
                    wgs84_extent,
                    geometry_type,
                    feature_count,
                    field_names,
                    field_types,
                    band_count,
                    raster_width,
                    raster_height,
                    pixel_width,
                    pixel_height,
                    nodata_value,
                    data_types,
                    file_created,
                    file_modified,
                    file_size_mb,
                    layer_title,
                    layer_abstract,
                    keywords,
                    lineage,
                    constraints,
                    url,
                    contact_info,
                    parent_directory
                FROM geospatial_inventory
                WHERE file_path = ? AND layer_name = ? AND retired_datetime IS NULL
                """,
                (layer_path, layer_name)
            )

            row = cursor.fetchone()

            if not row:
                QgsMessageLog.logMessage(
                    f"Layer not found in inventory: {layer_path} / {layer_name}",
                    "Metadata Manager",
                    Qgis.Warning
                )
                return None

            # Convert layer name to Title Case for title
            title = self._convert_to_title_case(row['layer_name'])

            # Build smart defaults dictionary
            defaults = {
                # Essential fields
                'title': row['layer_title'] or title,  # Use existing title or generate
                'abstract': row['layer_abstract'] or '',
                'keywords': row['keywords'].split(',') if row['keywords'] else [],

                # Spatial information
                'crs': row['crs_authid'] or '',
                'native_extent': row['native_extent'],  # Format: "xmin,ymin,xmax,ymax"
                'wgs84_extent': row['wgs84_extent'],

                # Data type specific
                'data_type': row['data_type'] or 'dataset',
                'geometry_type': row['geometry_type'] or '',
                'feature_count': row['feature_count'],
                'field_names': row['field_names'].split(',') if row['field_names'] else [],
                'field_types': row['field_types'].split(',') if row['field_types'] else [],

                # Raster specific
                'band_count': row['band_count'],
                'raster_width': row['raster_width'],
                'raster_height': row['raster_height'],
                'pixel_width': row['pixel_width'],
                'pixel_height': row['pixel_height'],
                'nodata_value': row['nodata_value'],
                'data_types': row['data_types'],

                # File metadata
                'format': row['format'] or '',
                'file_path': row['file_path'],
                'file_created': row['file_created'],
                'file_modified': row['file_modified'],
                'file_size_mb': row['file_size_mb'],
                'parent_directory': row['parent_directory'],

                # Existing GIS metadata
                'lineage': row['lineage'] or '',
                'constraints': row['constraints'] or '',
                'url': row['url'] or '',
                'contact_info': row['contact_info'] or ''
            }

            QgsMessageLog.logMessage(
                f"Loaded smart defaults for: {layer_name} ({title})",
                "Metadata Manager",
                Qgis.Info
            )

            return defaults

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error getting smart defaults: {str(e)}",
                "Metadata Manager",
                Qgis.Critical
            )
            return None

    def _convert_to_title_case(self, layer_name: str) -> str:
        """
        Convert layer name to Title Case for use as metadata title.

        Examples:
            "roads_2024" -> "Roads 2024"
            "us_census_tracts" -> "US Census Tracts"
            "dem_10m" -> "DEM 10m"

        Args:
            layer_name: Layer name from database

        Returns:
            Title Case formatted string
        """
        if not layer_name:
            return "Untitled Layer"

        # Replace underscores and hyphens with spaces
        title = layer_name.replace('_', ' ').replace('-', ' ')

        # Remove common file extensions
        extensions = ['.shp', '.tif', '.tiff', '.gpkg', '.geojson', '.kml', '.gml']
        for ext in extensions:
            if title.lower().endswith(ext):
                title = title[:-len(ext)]

        # Convert to title case
        title = title.title()

        # Fix common abbreviations that should be uppercase
        abbreviations = {
            'Usa': 'USA', 'Us': 'US', 'Uk': 'UK',
            'Dem': 'DEM', 'Dsm': 'DSM', 'Dtm': 'DTM',
            'Gps': 'GPS', 'Gis': 'GIS', 'Crs': 'CRS',
            'Utm': 'UTM', 'Wgs': 'WGS', 'Nad': 'NAD',
            'Id': 'ID', 'Url': 'URL', 'Api': 'API'
        }

        words = title.split()
        for i, word in enumerate(words):
            if word in abbreviations:
                words[i] = abbreviations[word]

        return ' '.join(words)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
