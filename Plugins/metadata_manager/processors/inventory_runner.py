"""
Inventory Runner - Background processor for inventory scanning.

Wraps the inventory_miner Processing algorithm to run in a QThread with progress signals.

Author: John Zastrow
License: MIT
"""

__version__ = "0.6.0"

from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import (
    QgsProcessingFeedback,
    QgsMessageLog,
    Qgis
)


class InventoryFeedback(QgsProcessingFeedback):
    """Custom feedback class that emits Qt signals."""

    def __init__(self, runner):
        super().__init__()
        self.runner = runner
        self._stopped = False

    def setProgress(self, progress):
        """Override to emit progress signal."""
        super().setProgress(progress)
        self.runner.progress_updated.emit(int(progress))

    def pushInfo(self, info):
        """Override to emit log signal."""
        super().pushInfo(info)
        self.runner.log_message.emit("INFO", info)

    def pushDebugInfo(self, info):
        """Override to emit debug log signal."""
        super().pushDebugInfo(info)
        if self.runner.verbose:
            self.runner.log_message.emit("DEBUG", info)

    def pushCommandInfo(self, info):
        """Override to emit command log signal."""
        super().pushCommandInfo(info)
        self.runner.log_message.emit("INFO", info)

    def pushConsoleInfo(self, info):
        """Override to emit console log signal."""
        super().pushConsoleInfo(info)
        self.runner.log_message.emit("INFO", info)

    def reportError(self, error, fatalError=False):
        """Override to emit error signal."""
        super().reportError(error, fatalError)
        level = "CRITICAL" if fatalError else "ERROR"
        self.runner.log_message.emit(level, error)

    def isCanceled(self):
        """Check if processing was canceled."""
        return self._stopped

    def cancel(self):
        """Cancel processing."""
        self._stopped = True
        super().cancel()


class InventoryRunner(QObject):
    """
    Background runner for inventory scanning.

    Runs the inventory_miner algorithm in a separate thread with progress reporting.
    """

    # Signals
    progress_updated = pyqtSignal(int)  # percent
    status_updated = pyqtSignal(str, dict)  # status message, stats dict
    log_message = pyqtSignal(str, str)  # level, message
    finished = pyqtSignal(str, str, dict)  # gpkg_path, layer_name, stats
    error = pyqtSignal(str)  # error message

    def __init__(self, params):
        """
        Initialize inventory runner.

        Args:
            params: Dictionary of parameters:
                - directory: Root directory to scan
                - output_gpkg: Output GeoPackage path
                - layer_name: Name for inventory layer
                - update_mode: Boolean, preserve metadata status
                - include_vectors: Boolean
                - include_rasters: Boolean
                - include_tables: Boolean
                - parse_metadata: Boolean
                - include_sidecar: Boolean
                - validate_files: Boolean
        """
        super().__init__()
        self.params = params
        self.feedback = None
        self.verbose = False
        self._algorithm = None

    def run(self):
        """Run the inventory scan."""
        try:
            # Create feedback
            self.feedback = InventoryFeedback(self)

            # Import the processor (now in plugin)
            from .inventory_processor import InventoryProcessor

            # Create processor instance
            processor = InventoryProcessor(self.params, self.feedback)

            self.status_updated.emit("Scanning directory...", {})

            # Run the processor
            results = processor.process()

            if self.feedback.isCanceled():
                self.log_message.emit("WARNING", "Inventory scan was canceled by user")
                self.error.emit("Scan canceled by user")
                return

            # Extract statistics
            stats = results.get('stats', {
                'total': 0,
                'vectors': 0,
                'rasters': 0,
                'tables': 0
            })

            self.status_updated.emit("Inventory complete", stats)

            # Emit finished signal
            self.finished.emit(
                self.params['output_gpkg'],
                self.params['layer_name'],
                stats
            )

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.log_message.emit("CRITICAL", f"Fatal error: {str(e)}")
            self.error.emit(error_msg)

    def stop(self):
        """Stop the inventory scan."""
        if self.feedback:
            self.feedback.cancel()
