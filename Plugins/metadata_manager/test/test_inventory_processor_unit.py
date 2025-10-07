import sys
import types
import unittest

# Create minimal fake qgis modules before importing the processor
qgis = types.ModuleType('qgis')
qgis_core = types.ModuleType('qgis.core')
qgis_PyQt = types.ModuleType('qgis.PyQt')
qgis_PyQt_QtCore = types.ModuleType('qgis.PyQt.QtCore')

class QVariant:
    String = 1
    Int = 2
    LongLong = 3
    Double = 4
    Bool = 5

class QgsField:
    def __init__(self, name, type_val=None):
        self._name = name
        self._type_val = type_val
    def name(self):
        return self._name

class QgsFields(list):
    def append(self, f):
        super().append(f)
    def toList(self):
        return list(self)

# Populate the minimal qgis.core module attributes used by inventory_processor
qgis_core.QgsField = QgsField
qgis_core.QgsFields = QgsFields
# Provide placeholders for other imported names to avoid import errors
qgis_core.QgsVectorLayer = object
qgis_core.QgsRasterLayer = object
qgis_core.QgsCoordinateReferenceSystem = object
qgis_core.QgsCoordinateTransform = object
qgis_core.QgsProject = object
qgis_core.QgsFeature = object
qgis_core.QgsGeometry = object
qgis_core.QgsRectangle = object
qgis_core.QgsPointXY = object
qgis_core.QgsVectorFileWriter = object
qgis_core.QgsWkbTypes = object
qgis_core.QgsMessageLog = object
qgis_core.Qgis = object

# Provide QVariant via qgis.PyQt.QtCore
qgis_PyQt_QtCore.QVariant = QVariant
qgis_PyQt.QtCore = qgis_PyQt_QtCore

# Insert into sys.modules so imports use these fakes
sys.modules['qgis'] = qgis
sys.modules['qgis.core'] = qgis_core
sys.modules['qgis.PyQt'] = qgis_PyQt
sys.modules['qgis.PyQt.QtCore'] = qgis_PyQt_QtCore

# Now import the InventoryProcessor
from Plugins.metadata_manager.processors.inventory_processor import InventoryProcessor

class TestInventoryProcessorFields(unittest.TestCase):
    def test_create_fields_count_and_names(self):
        params = {
            'directory': '.',
            'output_gpkg': 'out.gpkg',
            'layer_name': 'inv',
            'update_mode': False,
            'include_vectors': True,
            'include_rasters': True,
            'include_tables': True,
            'parse_metadata': False,
            'include_sidecar': False,
            'validate_files': False
        }
        proc = InventoryProcessor(params, feedback=None)
        fields = proc._create_fields()
        # Ensure fields is list-like and contains many items
        self.assertTrue(hasattr(fields, 'toList') or isinstance(fields, list))
        self.assertGreater(len(fields), 40)
        names = [f.name() for f in fields]
        for key in ('file_path', 'layer_name', 'data_type', 'file_size_bytes', 'metadata_status'):
            self.assertIn(key, names)

if __name__ == '__main__':
    unittest.main()
