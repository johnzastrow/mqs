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

    def save_metadata_to_cache(self, layer_path: str, metadata: Dict, in_sync: bool = False) -> bool:
        """
        Save metadata to metadata_cache table.

        Args:
            layer_path: Full path to the layer file
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
                    COALESCE((SELECT created_date FROM metadata_cache WHERE layer_path = ?), datetime('now')),
                    datetime('now'),
                    ?
                )
                """,
                (layer_path, metadata.get('title', 'Unknown'), metadata_json, layer_path, 1 if in_sync else 0)
            )

            self.connection.commit()

            QgsMessageLog.logMessage(
                f"Metadata cached for: {layer_path}",
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

    def load_metadata_from_cache(self, layer_path: str) -> Optional[Dict]:
        """
        Load metadata from metadata_cache table.

        Args:
            layer_path: Full path to the layer file

        Returns:
            Dictionary containing metadata or None if not found
        """
        if not self.is_connected:
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT metadata_json FROM metadata_cache WHERE layer_path = ?",
                (layer_path,)
            )

            row = cursor.fetchone()
            if row:
                metadata = json.loads(row['metadata_json'])
                QgsMessageLog.logMessage(
                    f"Metadata loaded from cache: {layer_path}",
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
        status: str,
        target: str = 'file',
        cached: bool = True
    ) -> bool:
        """
        Update metadata tracking fields in geospatial_inventory table.

        Args:
            layer_path: Full path to the layer file
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

            # Check if we need to disable triggers (if SpatiaLite not available)
            # Triggers on geospatial_inventory may use spatial functions
            disable_triggers = False
            try:
                # Test if spatial functions are available
                cursor.execute("SELECT InitSpatialMetadata(1)")
            except:
                disable_triggers = True

            if disable_triggers:
                # Temporarily disable triggers to avoid ST_IsEmpty errors
                cursor.execute("PRAGMA recursive_triggers = OFF")

            cursor.execute(
                """
                UPDATE geospatial_inventory
                SET
                    metadata_status = ?,
                    metadata_last_updated = datetime('now'),
                    metadata_target = ?,
                    metadata_cached = ?
                WHERE file_path = ?
                """,
                (status, target, 1 if cached else 0, layer_path)
            )

            if disable_triggers:
                # Re-enable triggers
                cursor.execute("PRAGMA recursive_triggers = ON")

            self.connection.commit()

            if cursor.rowcount > 0:
                QgsMessageLog.logMessage(
                    f"✅ Inventory updated: {layer_path} → status={status}",
                    "Metadata Manager",
                    Qgis.Success
                )
                return True
            else:
                # Try to find similar paths for debugging
                cursor.execute("SELECT file_path FROM geospatial_inventory WHERE file_path LIKE ? LIMIT 5", (f"%{layer_path.split('/')[-1]}%",))
                similar = [row['file_path'] for row in cursor.fetchall()]
                QgsMessageLog.logMessage(
                    f"⚠ Layer not found in inventory: {layer_path}\n"
                    f"Similar paths in inventory: {similar[:3] if similar else 'none found'}",
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

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
