<!--
Short, actionable instructions for AI code assistants working on the MQS repository.
Keep this file concise (20-50 lines). Avoid repeating generic programming advice; focus on
project-specific conventions, commands, and examples that let an assistant be productive quickly.
-->

# MQS — AI assistant quick guide

- Big picture: this repo is a collection of QGIS Processing scripts (in `Scripts/`) and QGIS plugins (in `Plugins/`).
  - Scripts are small Processing toolbox algorithms (inherit from `QgsProcessingAlgorithm`).
  - The `metadata_manager` plugin (under `Plugins/metadata_manager`) integrates with the `inventory_miner` script by sharing a GeoPackage inventory (`geospatial_catalog.gpkg`).

- Key workflows (explicit commands/examples):
  - Compile plugin resources: go to the plugin directory and run `make` (or `pyrcc5 -o resources.py resources.qrc`).
    - Example: `cd Plugins/metadata_manager && make` (Windows: run from PowerShell).
  - Run tests: the project uses unittest; many tests are runnable with `python -m pytest` from repo root or by running individual test files directly.
    - Example: `python -m pytest` (preferred) or `python Plugins/metadata_manager/test/test_init.py` for a single test file.

- Code patterns and conventions to follow:
  - Every Processing script must define `__version__ = "x.y.z"` at top-level.
  - Scripts use group name "MQS Tools"; new algorithms should set `group()` accordingly.
  - Tests live next to docs under `docs/.../testing/` or `Plugins/<plugin>/test/` and use Python's `unittest`.
  - QGIS plugin entry point must provide `classFactory()` in `__init__.py` and include `metadata.txt`.

- Important files/directories (reference examples):
  - `Scripts/inventory_miner.py` — canonical example of a ProcessingAlgorithm and how inventory GeoPackage is written.
  - `Plugins/metadata_manager/MetadataManager.py` — plugin lifecycle, DB connection, and resource compilation expectations.
  - `docs/metadata_manager/README.md` — shows Makefile usage and test recommendations.

- Integration notes / gotchas:
  - The plugin and inventory script share a GeoPackage schema; database migrations and schema-version checks are performed (see `db/` inside the plugin). If you modify schema, update migrations and tests.
  - Tests often assume a QGIS/PyQGIS environment; prefer running unit tests that do not require a full QGIS GUI, or run them inside a QGIS-enabled Python when needed.

- Guidance for edits and PRs:
  - Add/adjust unit tests for any behavior change. Tests are required per repository policy.
  - Update `__version__` and corresponding `CHANGELOG.md` entry for non-trivial changes.
  - When changing plugin UI or resources, re-run resource compilation (`make` / `pyrcc5`) and include the generated `resources.py` in the PR.

- Quick examples (copy-paste friendly):
  - Compile resources (PowerShell):
    cd Plugins/metadata_manager; make
  - Run all tests:
    python -m pytest

If anything here is unclear or you want more detail for a specific subproject (vectors2gpkg, inventory_miner, or metadata_manager), say which area and I will expand the instructions with targeted examples and file pointers.
## Per-subproject quickstarts

- ExtractStylesfromDirectoriesForStyleManager
  - What: Finds .qgs/.qgz projects and extracts style symbols into a single XML for QGIS Style Manager.
  - Quickstart: Read `docs/ExtractStylesfromDirectoriesForStyleManager/README.md`; run the unit tests under `docs/ExtractStylesfromDirectoriesForStyleManager/testing/` with `python -m pytest docs/ExtractStylesfromDirectoriesForStyleManager/testing`.

- vectors2gpkg
  - What: Recursively collects vector layers and writes them into a GeoPackage with metadata and optional styles.
  - Quickstart: Script is `Scripts/vectors2gpkg.py`; docs are in `docs/vectors2gpkg/`. Run the subproject tests with `python -m pytest docs/vectors2gpkg/testing` or open the script in QGIS Processing Toolbox for interactive runs.

- rasters2gpkg (ABANDONED)
  - What: Historical/rationale docs live in `docs/rasters2gpkg/README.md`. This project was abandoned — prefer native raster formats (GeoTIFF) for analytical data.

- batchvectorrename
  - What: Safe batch rename operations for vector layers/databases with dry-run and rollback support.
  - Quickstart: See `Scripts/batchvectorrename.py` and `docs/batchvectorrename/README.md`. Run tests: `python -m pytest docs/batchvectorrename/testing`.

- inventory_miner
  - What: Canonical crawler that produces `geospatial_inventory` in a GeoPackage, used by Metadata Manager.
  - Quickstart: Open `Scripts/inventory_miner.py` for the algorithm example. Run its docs/tests at `docs/inventory_miner/testing` with `python -m pytest docs/inventory_miner/testing`. Note: full validation tests may require GDAL/OGR and PyQGIS available in the environment.

- metadata_manager (plugin)
  - What: QGIS plugin that reads/writes metadata and integrates with the inventory GeoPackage.
  - Quickstart: Compile resources then run plugin tests:
    - Compile resources (PowerShell):
      cd Plugins/metadata_manager; make
    - Run tests: `python -m pytest Plugins/metadata_manager/test`
    - Notes: Many plugin tests assume PyQGIS; run them in a QGIS-enabled Python or keep to pure-Python unit tests when possible.

***

## CI tips (GitHub Actions)

- PyQGIS/GDAL are heavy system dependencies — CI runners rarely have them preinstalled. Two practical options:
  1. Use a QGIS-enabled runner (self-hosted or specialized Docker images) and install GDAL/PyQGIS there before running tests.
  2. Keep CI focused on pure-Python unit tests: exclude tests that import QGIS/pyqgis or require GDAL. Many tests are organized under `docs/**/testing` and `Plugins/*/test` — mark GUI/PyQGIS tests or skip them in CI.

- Tip: Use an environment variable (for example SKIP_PYQGIS=1) in CI and wrap PyQGIS tests with `pytest.mark.skipif(os.getenv('SKIP_PYQGIS') == '1', reason='Skipping PyQGIS tests in CI')` or check for import errors in test setup.

***
