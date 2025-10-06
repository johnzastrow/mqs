"""
Database migration system for Metadata Manager.

Handles schema upgrades for Metadata Manager tables only.
Inventory Miner handles its own migrations.

Author: John Zastrow
License: MIT
"""

from typing import List, Tuple, Callable
from qgis.core import QgsMessageLog, Qgis

from .schema import DatabaseSchema


class Migration:
    """Represents a single database migration."""

    def __init__(self, from_version: str, to_version: str, description: str,
                 upgrade_func: Callable):
        """
        Initialize migration.

        Args:
            from_version: Starting version
            to_version: Target version
            description: Migration description
            upgrade_func: Function to execute migration
        """
        self.from_version = from_version
        self.to_version = to_version
        self.description = description
        self.upgrade_func = upgrade_func

    def execute(self, db_manager) -> Tuple[bool, str]:
        """
        Execute migration.

        Args:
            db_manager: DatabaseManager instance

        Returns:
            Tuple of (success, message)
        """
        try:
            return self.upgrade_func(db_manager)
        except Exception as e:
            return False, f"Migration failed: {str(e)}"


class MigrationManager:
    """Manages database migrations for Metadata Manager."""

    def __init__(self):
        """Initialize migration manager."""
        self.migrations: List[Migration] = []
        self._register_migrations()

    def _register_migrations(self):
        """Register all available migrations."""
        # Future migrations will be registered here
        # Example:
        # self.migrations.append(Migration(
        #     "0.1.0", "0.2.0",
        #     "Add new field to templates table",
        #     self._migrate_0_1_to_0_2
        # ))
        pass

    def get_migration_path(self, current_version: str, target_version: str) -> List[Migration]:
        """
        Get list of migrations needed to upgrade from current to target version.

        Args:
            current_version: Current schema version
            target_version: Desired schema version

        Returns:
            List of migrations in order
        """
        # For now, simple version comparison
        # In future, build migration chain for multi-step upgrades
        migration_path = []

        for migration in self.migrations:
            if migration.from_version == current_version and migration.to_version == target_version:
                migration_path.append(migration)

        return migration_path

    def needs_upgrade(self, current_version: str) -> bool:
        """
        Check if database needs upgrade.

        Args:
            current_version: Current schema version

        Returns:
            True if upgrade needed
        """
        if current_version is None:
            return True

        return current_version != DatabaseSchema.METADATA_SCHEMA_VERSION

    def perform_upgrade(self, db_manager, current_version: str) -> Tuple[bool, str]:
        """
        Perform upgrade from current version to latest.

        Args:
            db_manager: DatabaseManager instance
            current_version: Current schema version

        Returns:
            Tuple of (success, message)
        """
        if current_version is None:
            # New installation - initialize tables
            return db_manager.initialize_metadata_manager_tables()

        target_version = DatabaseSchema.METADATA_SCHEMA_VERSION

        if current_version == target_version:
            return True, "Database is already at latest version"

        # Get migration path
        migrations = self.get_migration_path(current_version, target_version)

        if not migrations:
            # No migrations defined yet, just update version
            QgsMessageLog.logMessage(
                f"No migrations defined from {current_version} to {target_version}. "
                f"Updating version number only.",
                "Metadata Manager",
                Qgis.Info
            )

            if db_manager.update_schema_version(target_version):
                db_manager.log_upgrade(
                    current_version,
                    target_version,
                    True,
                    "Version update only"
                )
                return True, f"Updated to version {target_version}"
            else:
                return False, "Failed to update version"

        # Execute migrations in order
        for migration in migrations:
            QgsMessageLog.logMessage(
                f"Executing migration: {migration.description}",
                "Metadata Manager",
                Qgis.Info
            )

            success, message = migration.execute(db_manager)

            if not success:
                db_manager.log_upgrade(
                    migration.from_version,
                    migration.to_version,
                    False,
                    f"Failed: {message}"
                )
                return False, f"Migration failed: {message}"

            # Update version after successful migration
            db_manager.update_schema_version(migration.to_version)
            db_manager.log_upgrade(
                migration.from_version,
                migration.to_version,
                True,
                migration.description
            )

        return True, f"Successfully upgraded to version {target_version}"

    # Example migration functions (for future use)

    # def _migrate_0_1_to_0_2(self, db_manager) -> Tuple[bool, str]:
    #     """
    #     Migrate from 0.1.0 to 0.2.0.
    #
    #     Example migration that adds a new column.
    #     """
    #     try:
    #         cursor = db_manager.connection.cursor()
    #
    #         # Add new column to templates table
    #         cursor.execute("""
    #             ALTER TABLE templates
    #             ADD COLUMN is_public INTEGER DEFAULT 0
    #         """)
    #
    #         db_manager.connection.commit()
    #         return True, "Added is_public column to templates"
    #
    #     except Exception as e:
    #         db_manager.connection.rollback()
    #         return False, str(e)
