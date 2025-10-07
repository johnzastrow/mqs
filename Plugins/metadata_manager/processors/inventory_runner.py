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
    QgsProcessingContext,
    QgsApplication,
    QgsMessageLog,
    Qgis
)
from pathlib import Path
import sys


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
            # Add Scripts directory to path so we can import inventory_miner
            scripts_dir = Path(__file__).parents[3] / "Scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))

            # Import the algorithm
            try:
                from inventory_miner import InventoryMinerAlgorithm
            except ImportError as e:
                self.error.emit(f"Could not import inventory_miner: {str(e)}\n\n"
                              f"Please ensure inventory_miner.py is in the Scripts directory:\n"
                              f"{scripts_dir}")
                return

            # Create algorithm instance
            self._algorithm = InventoryMinerAlgorithm()
            self._algorithm.initAlgorithm()

            # Create feedback
            self.feedback = InventoryFeedback(self)

            # Create context
            context = QgsProcessingContext()
            context.setFeedback(self.feedback)

            # Prepare algorithm parameters
            alg_params = {
                'INPUT_DIRECTORY': self.params['directory'],
                'OUTPUT_GPKG': self.params['output_gpkg'],
                'LAYER_NAME': self.params['layer_name'],
                'UPDATE_MODE': self.params['update_mode'],
                'INCLUDE_VECTORS': self.params['include_vectors'],
                'INCLUDE_RASTERS': self.params['include_rasters'],
                'INCLUDE_TABLES': self.params['include_tables'],
                'PARSE_METADATA': self.params['parse_metadata'],
                'INCLUDE_SIDECAR': self.params['include_sidecar'],
                'VALIDATE_FILES': self.params['validate_files']
            }

            self.status_updated.emit("Scanning directory...", {})

            # Run the algorithm
            results = self._algorithm.processAlgorithm(alg_params, context, self.feedback)

            if self.feedback.isCanceled():
                self.log_message.emit("WARNING", "Inventory scan was canceled by user")
                self.error.emit("Scan canceled by user")
                return

            # Extract results
            output_layer = results.get('OUTPUT', None)
            if not output_layer:
                self.error.emit("No output layer produced by algorithm")
                return

            # Get statistics (would need to query the output layer)
            stats = {
                'total': 0,
                'vectors': 0,
                'rasters': 0,
                'tables': 0
            }

            # Try to get actual statistics from the created layer
            try:
                from qgis.core import QgsVectorLayer
                layer = QgsVectorLayer(output_layer, "inventory", "ogr")
                if layer.isValid():
                    stats['total'] = layer.featureCount()

                    # Count by data type
                    for feature in layer.getFeatures():
                        data_type = feature['data_type']
                        if data_type == 'vector':
                            stats['vectors'] += 1
                        elif data_type == 'raster':
                            stats['rasters'] += 1
                        elif data_type == 'table':
                            stats['tables'] += 1
            except Exception as e:
                self.log_message.emit("WARNING", f"Could not extract statistics: {str(e)}")

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
