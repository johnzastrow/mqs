# Original request

Create a PyQGIS script to be executed from the QGIS toolbox that will recurse through directories and subdirectories to find all QGIS project files of various types, extract all styles from each that it finds, and assimilate them into into a single "db" file - which is really an XML file. The script will be added and used from the QGIS Toolbox. Inputs will be 1. the top-level directory to seach into, 2. The file to save the styles into, 3. Types of styles to include (default is all. offer choices to the user)

The file `example_toolbox_script.py` in the `docs` is an example of how to structure the python so that it works in the QGIS toolbox. The XML files in the same directory provide examples of the current version of the style XMLs.

You may only use the standard library or use python libraries from QGIS itself as demonstrated in the example toolbox script.

## Answers to clarifying questions
1. QGIS Project File Types: all valid file types including  .qgs, .qgz
2. Style Types: all possible style types. Conduct research to enumerate them into this requirements document.
3. Style Extraction: The script extract styles from where ever it can find them, including Layers within the project files and the project files themselves
4. Output File Format: The QGIS Style Manager does not appear to be able to directly import QML. Therefore, the output here should be pure XML following the standard of the example files I provided. See if you can find documentation about this standard as I cannot. If not, try to deduce the standard from the example XML files I provided and and the file `docs/nearth_project_file.qgz`
5. Duplicate Handling: If the same style appears in multiple project files the script should keep all of them and increment the object names
6. Error Handling: If the script encounters a corrupted or unreadable project file Log the error and continue
7. Example Files: read through all files in the `docs/` directory. Example inputs to the script will be the `nearth_project_file.qgz` and example outputs will be the XML files.
Questions before implementing:
8. Style Selection UI: For the "Types of styles to include" parameter, should be A single multi-select dropdown with a default of all the items selected.
9. Symbol Naming: When extracting symbols from layers, the naming should follow: LayerName_SymbolName (e.g., "Roads_Primary Highway") then LayerName_CategoryValue for categorized renderers if no SymbolName exists, but a category does exist. Do not include the ProjectName.
10. Progress Feedback: The script should provide detailed feedback showing:
    - Each file being processed
    - Number of styles found per file
    - Total count at the end
    - Errors encountered
11. Embedded Style Databases: If a .qgz file contains an embedded .db style database, the script should also extract styles from that database as an option to the user. It should default to Yes
12. Script Output Location: The script output should be saved directly in the repo root, or in a specific directory input by the user if one is provided. 


## Other documentation

Here are some other links for additional documentation:
* https://qgis.org/pyqgis/3.40/core/index.html
* https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/index.html
* https://docs.qgis.org/3.40/en/docs/user_manual/appendices/qgis_file_formats.html
* https://docs.qgis.org/3.40/en/docs/user_manual/appendices/qgis_file_formats.html#qml-the-qgis-style-file-format
* https://docs.qgis.org/3.40/en/docs/user_manual/introduction/project_files.html
* https://docs.qgis.org/3.40/en/docs/user_manual/processing/toolbox.html

Learn context from these links as we will write other scripts for QGIS.


# Background

## QGIS Style Types (QGIS 3.40)

Based on research of QGIS documentation, the following style types can be stored in QGIS style databases:

Key Findings:

  1. Style Types: Enumerated all 8 QGIS style types (Symbols, Color Ramps, Text Formats, Label Settings, Legend
  Patch Shapes, 3D Symbols, Tags, Smart Groups)
  2. Output Format: The XML structure follows the qgis_style version="2" format with sections for each style type
  3. Project Structure:
    - .qgz files are ZIP archives containing .qgs XML files
    - Styles are embedded in layer <renderer-v2> sections
    - Symbols need to be extracted and renamed meaningfully


### Renderable Style Types (to extract and export):

1. **Symbols** (`QgsStyle.SymbolEntity` = 0)
   - XML Element: `<symbol>`
   - PyQGIS Classes: `QgsMarkerSymbol`, `QgsLineSymbol`, `QgsFillSymbol`
   - Types: Marker (point), Line, Fill (polygon), Hybrid
   - Description: Visual appearance of vector features

2. **Color Ramps** (`QgsStyle.ColorrampEntity` = 2)
   - XML Element: `<colorramp>`
   - PyQGIS Classes: `QgsGradientColorRamp`, `QgsRandomColorRamp`, `QgsLimitedRandomColorRamp`, `QgsPresetSchemeColorRamp`, `QgsColorBrewerColorRamp`
   - Description: Color gradients for thematic mapping

3. **Text Formats** (`QgsStyle.TextFormatEntity` = 4)
   - PyQGIS Class: `QgsTextFormat`
   - Description: Font, size, color, buffer, shadow, background settings
   - Added: QGIS 3.x

4. **Label Settings** (`QgsStyle.LabelSettingsEntity` = 5)
   - PyQGIS Class: `QgsPalLayerSettings`
   - Description: Complete label placement and rendering configuration
   - Added: QGIS 3.x

5. **Legend Patch Shapes** (`QgsStyle.LegendPatchShapeEntity` = 6)
   - XML Element: `<shape>`
   - PyQGIS Class: `QgsLegendPatchShape`
   - Description: Custom geometric shapes for legend display
   - Added: QGIS 3.14

6. **3D Symbols** (`QgsStyle.Symbol3DEntity` = 7)
   - XML Element: `<symbol>` (with type attribute)
   - PyQGIS Classes: `QgsPoint3DSymbol`, `QgsLine3DSymbol`, `QgsPolygon3DSymbol`, `QgsPointCloud3DSymbol`
   - Description: 3D rendering of GIS data
   - Added: QGIS 3.14 (Tech Preview)

### Organizational Types (not renderable, used for organizing):

7. **Tags** (`QgsStyle.TagEntity` = 1)
   - Description: Categorization metadata

8. **Smart Groups** (`QgsStyle.SmartgroupEntity` = 3)
   - Description: Dynamic collections based on rules

### Notes:
- The primary focus for extraction should be on renderable types: Symbols, Color Ramps, Text Formats, Label Settings, Legend Patch Shapes, and 3D Symbols
- Tags and Smart Groups are organizational metadata but may be included for completeness
- All styles use XML serialization for storage

## Output XML Format Analysis

Based on analysis of `states_style_db.xml` and `all_styles_dump.xml`:

### Structure:
```xml
<!DOCTYPE qgis_style>
<qgis_style version="2">
  <symbols>
    <symbol name="..." type="..." ...>...</symbol>
    ...
  </symbols>
  <colorramps>
    <colorramp name="..." type="...">...</colorramp>
    ...
  </colorramps>
  <textformats/>
  <labelsettings/>
  <legendpatchshapes/>
  <symbols3d/>
</qgis_style>
```

### Key Observations:
1. Root element: `<qgis_style version="2">` with DOCTYPE declaration
2. Main sections: `symbols`, `colorramps`, `textformats`, `labelsettings`, `legendpatchshapes`, `symbols3d`
3. Empty sections use self-closing tags (e.g., `<textformats/>`)
4. Symbol elements can have a `tags=""` attribute for metadata
5. Each symbol has a `name` attribute which must be unique (or incremented for duplicates)
6. Symbol types: `fill`, `line`, `marker` (matches Polygon, LineString, Point geometries)

## QGIS Project File Structure

Based on analysis of `nearth_project_file.qgz`:

### File Format:
- `.qgz` files are ZIP archives containing:
  - `*.qgs` - Main project XML file
  - Optional: embedded style databases (`.db` files)
  - Optional: other resources

### Style Locations in Project Files:
1. **Layer Renderers** - Within `<maplayer>` elements under `<renderer-v2>` section
   - Contains `<symbols>` with individual `<symbol>` elements
   - Each symbol has full XML definition identical to style database format

2. **Categorized/Graduated Renderers** - Have multiple symbols:
   - `<symbols>` section with named symbols (name="0", name="1", etc.)
   - `<source-symbol>` section with the base symbol

3. **Selection Symbols** - Under `<selectionSymbol>` in each layer

4. **Elevation Symbols** - Under `<elevation>` in 3D-capable layers

### Extraction Strategy:
1. Decompress `.qgz` files to access `.qgs` XML
2. Parse `.qgs` XML to find all `<maplayer>` elements
3. Extract symbols from:
   - `<renderer-v2><symbols><symbol>` elements
   - `<renderer-v2><source-symbol><symbol>` elements
4. Extract color ramps from renderer `<colorramp>` elements (if present)
5. Extract label settings from `<labeling>` sections
6. Assign meaningful names based on layer name + category/class name

