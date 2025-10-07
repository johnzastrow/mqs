"""
Processors package for Metadata Manager.

Contains background processing classes for inventory scanning and metadata operations.

Author: John Zastrow
License: MIT
"""

from .inventory_runner import InventoryRunner

__all__ = ['InventoryRunner']
