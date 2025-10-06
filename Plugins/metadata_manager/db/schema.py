"""
Database schema definitions for Metadata Manager.

Defines all tables added by Metadata Manager to the unified GeoPackage database.
Inventory Miner creates the geospatial_inventory table; Metadata Manager adds
its own tables for metadata management.

Author: John Zastrow
License: MIT
"""

__version__ = "0.1.0"


class DatabaseSchema:
    """Schema definitions for Metadata Manager tables."""

    # Current schema version for Metadata Manager
    METADATA_SCHEMA_VERSION = "0.1.0"

    @staticmethod
    def get_plugin_info_schema():
        """Plugin version tracking table (shared with Inventory Miner)."""
        return """
        CREATE TABLE IF NOT EXISTS plugin_info (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def get_organizations_schema():
        """Reusable organization profiles table."""
        return """
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            abbreviation TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            postal_code TEXT,
            country TEXT,
            website TEXT,
            email TEXT,
            phone TEXT,
            fax TEXT,
            logo_path TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def get_contacts_schema():
        """Contact information with roles table."""
        return """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER,
            name TEXT NOT NULL,
            position TEXT,
            email TEXT,
            phone TEXT,
            role TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        );
        """

    @staticmethod
    def get_keywords_schema():
        """Keyword library with hierarchical organization table."""
        return """
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            category TEXT,
            parent_id INTEGER,
            vocabulary TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES keywords(id)
        );
        """

    @staticmethod
    def get_keyword_sets_schema():
        """Predefined keyword collections tables."""
        return [
            """
            CREATE TABLE IF NOT EXISTS keyword_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS keyword_set_members (
                set_id INTEGER,
                keyword_id INTEGER,
                PRIMARY KEY (set_id, keyword_id),
                FOREIGN KEY (set_id) REFERENCES keyword_sets(id) ON DELETE CASCADE,
                FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE
            );
            """
        ]

    @staticmethod
    def get_templates_schema():
        """Metadata templates table."""
        return """
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            metadata_json TEXT NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def get_settings_schema():
        """User preferences and defaults table."""
        return """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def get_metadata_cache_schema():
        """Detailed metadata cache table with sync tracking."""
        return [
            """
            CREATE TABLE IF NOT EXISTS metadata_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                layer_path TEXT NOT NULL UNIQUE,
                layer_name TEXT NOT NULL,
                file_type TEXT,
                metadata_json TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_edited_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_written_date TIMESTAMP,
                target_location TEXT,
                in_sync INTEGER DEFAULT 1,
                UNIQUE(layer_path)
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_metadata_cache_path
            ON metadata_cache(layer_path);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_metadata_cache_sync
            ON metadata_cache(in_sync);
            """
        ]

    @staticmethod
    def get_upgrade_history_schema():
        """Schema upgrade history table."""
        return """
        CREATE TABLE IF NOT EXISTS upgrade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_version TEXT,
            to_version TEXT,
            tool TEXT,
            upgrade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success INTEGER DEFAULT 1,
            notes TEXT
        );
        """

    @staticmethod
    def get_all_schemas():
        """Return all schema definitions in creation order."""
        schemas = []

        # Plugin info (shared)
        schemas.append(DatabaseSchema.get_plugin_info_schema())

        # Core metadata manager tables
        schemas.append(DatabaseSchema.get_organizations_schema())
        schemas.append(DatabaseSchema.get_contacts_schema())
        schemas.append(DatabaseSchema.get_keywords_schema())
        schemas.extend(DatabaseSchema.get_keyword_sets_schema())
        schemas.append(DatabaseSchema.get_templates_schema())
        schemas.append(DatabaseSchema.get_settings_schema())
        schemas.extend(DatabaseSchema.get_metadata_cache_schema())
        schemas.append(DatabaseSchema.get_upgrade_history_schema())

        return schemas

    @staticmethod
    def get_initial_data():
        """Return initial data inserts for new database."""
        return [
            # Set metadata schema version
            f"""
            INSERT OR REPLACE INTO plugin_info (key, value)
            VALUES ('metadata_schema_version', '{DatabaseSchema.METADATA_SCHEMA_VERSION}');
            """,
            # Set plugin installation date
            """
            INSERT OR REPLACE INTO plugin_info (key, value)
            VALUES ('metadata_manager_installed', datetime('now'));
            """,
        ]
