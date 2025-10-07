import sys
import types
import importlib.util
from importlib.machinery import SourceFileLoader

# Setup minimal fake qgis modules
QVAR = types.SimpleNamespace(String=1, Int=2, LongLong=3, Double=4, Bool=5)

qgis_core = types.ModuleType('qgis.core')
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

# Minimal attributes used
qgis_core.QgsField = QgsField
qgis_core.QgsFields = QgsFields
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

qgis_PyQt_QtCore = types.ModuleType('qgis.PyQt.QtCore')
qgis_PyQt_QtCore.QVariant = QVAR
qgis_PyQt = types.ModuleType('qgis.PyQt')
qgis_PyQt.QtCore = qgis_PyQt_QtCore

# Insert fake modules
sys.modules['qgis'] = types.ModuleType('qgis')
sys.modules['qgis.core'] = qgis_core
sys.modules['qgis.PyQt'] = qgis_PyQt
sys.modules['qgis.PyQt.QtCore'] = qgis_PyQt_QtCore

# Minimal osgeo stubs (gdal, ogr) used during module import
osgeo = types.ModuleType('osgeo')
gdal = types.ModuleType('gdal')
ogr = types.ModuleType('ogr')
# Provide minimal attributes used by the module during import
gdal.GA_ReadOnly = 0
gdal.GA_Update = 1
def _gdal_open(path, mode=0):
    return None
gdal.Open = _gdal_open
def _ogr_open(path):
    return None
ogr.Open = _ogr_open
osgeo.gdal = gdal
osgeo.ogr = ogr
sys.modules['osgeo'] = osgeo
sys.modules['osgeo.gdal'] = gdal
sys.modules['osgeo.ogr'] = ogr

# Now load inventory_processor by path
path = r"Plugins\metadata_manager\processors\inventory_processor.py"
loader = SourceFileLoader('inventory_processor', path)
spec = importlib.util.spec_from_loader(loader.name, loader)
mod = importlib.util.module_from_spec(spec)
loader.exec_module(mod)

InventoryProcessor = mod.InventoryProcessor

# Run the test scenario without invoking __init__ (QGIS classes not available)
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
# Create an uninitialized instance and set required attributes manually
proc = object.__new__(InventoryProcessor)
proc.params = params
proc.feedback = None
fields = mod.InventoryProcessor._create_fields(proc)
print('Field count:', len(fields))
print('First 10 field names:', [f.name() for f in fields[:10]])

# Basic assertions
assert len(fields) > 40, 'Expected more than 40 fields'
names = [f.name() for f in fields]
for key in ('file_path', 'layer_name', 'data_type', 'file_size_bytes', 'metadata_status'):
    assert key in names, f"Missing field {key}"

print('OK')
