# MQS
My QGIS Stuff - A random assortment of things I might reuse. These might be images, styles, scripts or just documentation.

---

## Support

These are my resources that I make freely available to the world. You can ask me for help using them, but I may not be able to provide it due to knowledge or time constraints. 

Have a look at my [blog post](https://johnzastrow.github.io/2025-10-01-qgis-tutorial-materials/) for some more usefulness

---

## Scripts

Lately I'm doing work using python scripts to be used the in the [QGIS Toolbox](https://docs.qgis.org/3.40/en/docs/user_manual/processing/toolbox.html). You can use these scripts by downloading them, then importing them into your toolbox as following

1. Open your QGIS Toolbox
2. Select `Add script to toolbox` from the little python button
![Screenshot showing the QGIS Toolbox interface with the Add script to toolbox option highlighted. The Python button is selected, and a dialog box is open for importing a new script. The workspace background displays various QGIS tool categories. The tone is instructional and neutral. Visible text includes Add script to toolbox.](docs/ExtractStylesfromDirectoriesForStyleManager/images/adding_script_to_toolbox.png)
3. Double clicking the script name from the toolbox will run it and open the associated dialog screen 
![example toolbox screen from this repo](docs/ExtractStylesfromDirectoriesForStyleManager/images/script_running.png)

---

## Repository Structure

This repository contains multiple QGIS-related subprojects:

---

### Subprojects

---

#### ExtractStylesfromDirectoriesForStyleManager
Location: `docs/ExtractStylesfromDirectoriesForStyleManager/`
Script: `Scripts/extract_styles_from_projects.py`

A QGIS Processing toolbox script that recursively searches directories for QGIS project files (.qgs, .qgz) and extracts all styles into a single XML file compatible with QGIS Style Manager. Use it to create a monster default set of reusable styles from all your hard work across your projects. This script uses tags based on the project names that it finds the styles in to help you organize them.

[!IMPORTANT]
This makes it really easy to create duplicates and otherwise pollute your global styles. It's easy to clean them up, but be prepared for housekeeping if you use this tool in anger.

**Features:**
- Extracts symbols, color ramps, text formats, label settings, and more
- Handles duplicate names automatically
- Tags styles with source project name
- Intelligent naming based on layer and symbol type
- Detailed progress feedback

See `docs/ExtractStylesfromDirectoriesForStyleManager/REQUIREMENTS.md` for detailed documentation.

---

#### vectors2gpkg
Location: `docs/vectors2gpkg/`
Script: `Scripts/vectors2gpkg.py`

A QGIS Processing Toolbox script that recursively searches directories for vector files and loads them into a single GeoPackage with metadata preservation and optional style application. Consolidates scattered vector data from complex directory structures into a modern, portable GeoPackage format.

**Features:**
- Supports 10 vector formats: shapefiles, GeoJSON, KML/KMZ, GPX, GML, GeoPackages, File Geodatabases, SpatiaLite, MapInfo, standalone dBase files
- Container format support: copies all layers from GeoPackages, File Geodatabases, and SpatiaLite databases
- Non-spatial table handling: loads attribute-only tables from container formats and standalone dBase files
- User-selectable file types with multi-select controls
- Spatial indexing and metadata preservation
- QML style file application
- Smart layer naming with invalid character replacement and duplicate collision handling
- Automatic duplicate resolution with incrementing numbers (roads, roads_1, roads_2, etc.)

See `docs/vectors2gpkg/README.md` for detailed documentation.

---

#### Resources

Files that I might want to reuse and you might find useful

1. **Resources\qgis_styles_for_style_manager.xml** - Some styles I might to reuse across my QGIS installs, compiled using `extract_styles_from_projects.py`. I'll be adding to these.

---

#### Scripts

Usually python scripts that correspond to the subprojects listed above. The rest of the development files for these scripts will be found under the `docs` directory -- and you don't likely need to look at that stuff unless you want to learn more. Just grab scripts from this directory.

1. **Scripts\extract_styles_from_projects.py** - see ExtractStylesfromDirectoriesForStyleManager above
2. **Scripts\vectors2gpkg.py** - see vectors2gpkg above
