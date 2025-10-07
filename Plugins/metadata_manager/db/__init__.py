"""
Database management package for Metadata Manager plugin.

Handles unified GeoPackage database shared with Inventory Miner.
"""

__version__ = "0.1.0"

from .manager import DatabaseManager
from .schema import DatabaseSchema
from .metadata_writer import MetadataWriter

__all__ = ['DatabaseManager', 'DatabaseSchema', 'MetadataWriter']
