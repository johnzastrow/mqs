# MQS — Requirements and developer setup

This file lists the recommended system and Python dependencies required to develop and run the MQS repository tools (QGIS Processing scripts and QGIS plugins).

## High-level requirements

- QGIS: 3.40 or newer (tested against 3.40+). Required for running Processing scripts and plugin UI/tests that import `qgis`/`pyqgis`.
- GDAL/OGR: system GDAL (matching QGIS-provided GDAL where possible) for raster/vector discovery and metadata extraction.
- Python: 3.10 or 3.11 recommended (use the Python that accompanies your QGIS install for PyQGIS-based tests).

## Platform notes

- Windows: use the Python bundled with QGIS when running plugin tests or anything that imports `qgis` (PyQGIS). Install QGIS via the official installer.
- Linux: use system packages or prebuilt QGIS images. For CI, use a QGIS-enabled Docker image or self-hosted runner if you need full PyQGIS testing.
- macOS: use the QGIS macOS installer and its bundled Python for PyQGIS tests.

## Python packages (developer / test)

For development and running pure-Python tests, install the packages in `requirements-dev.txt`:

```text
# requirements-dev.txt (dev/test packages)
pytest
pytest-mock
flake8
black
pylint
# Optional: install ogr/gdal Python bindings from your platform package manager or conda
```

Note: do not expect `pip install gdal` to provide a compatible GDAL on all platforms — prefer the platform package manager or the Python bundled with QGIS.

## Build / developer commands

- Compile plugin resources (run inside plugin directory):

```powershell
cd Plugins/metadata_manager
make
# or
pyrcc5 -o resources.py resources.qrc
```

- Run tests (pure-Python):

```powershell
python -m pytest
```

- Running plugin tests that require PyQGIS:
  - Use the Python interpreter that ships with QGIS (Windows/Mac) or a QGIS-enabled conda environment.
  - Example (Windows): open the OSGeo4W Shell / QGIS Python shell and run pytest from repo root.

## CI guidance

- For CI that needs to run PyQGIS tests, use one of:
  - A self-hosted runner with QGIS installed.
  - A Docker image that includes QGIS/PyQGIS.
- For GitHub Actions focused on pure-Python tests, run `pytest` with `SKIP_PYQGIS=1` to skip QGIS-dependent tests.

## Where to look for per-subproject requirements

- `docs/*/REQUIREMENTS.md` — many subprojects include their own requirements and notes (see `docs/metadata_manager/REQUIREMENTS.md`, `docs/vectors2gpkg/REQUIREMENTS.md`).

If you want, I can create a small `contrib/` script to help developers create a QGIS-enabled virtualenv or provide Docker configurations for CI.
