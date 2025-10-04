# MQS
My QGIS Stuff - A random assortment of things I might reuse. These might be images, styles, scripts or just documentation.

## Support
These are my resources that I make freely available to the world. You can ask me for help using them, but I may not be able to provide it due to knowledge or time constraints. 

## Scripts
Lately I'm doing work using python scripts to be used the in the [QGIS Toolbox](https://docs.qgis.org/3.40/en/docs/user_manual/processing/toolbox.html). You can use these scripts by downloading them, then importing them into your toolbox as following

1. Open your QGIS Toolbox
2. Select `Add script to toolbox` from the little python button
![Screenshot showing the QGIS Toolbox interface with the Add script to toolbox option highlighted. The Python button is selected, and a dialog box is open for importing a new script. The workspace background displays various QGIS tool categories. The tone is instructional and neutral. Visible text includes Add script to toolbox.](docs/ExtractStylesfromDirectoriesForStyleManager/images/adding_script_to_toolbox.png)
The QGIS Toolbox interface displays a list of tool categories including Vector tiles, GDAL, Lat Lon tools, Models, QuickOSM, Scripts, and Style Management. The script Extract Styles from Project Files is highlighted under Style Management, indicated by a blue selection bar and a gear icon. Below the toolbox, controls for Magnifier, Rotation, and Render are visible. The environment is neutral and instructional. Visible text includes Vector tiles, GDAL, Lat Lon tools, Models, QuickOSM, Scripts, Style Management, Extract Styles from Project Files, Magnifier, Rotation, and Render.
3. Double clicking the script name from the toolbox will run it and open the associated dialog screen 
Screenshot of the QGIS Style Management dialog for extracting styles from project files. The interface displays options to select an input directory, style types to include, and whether to extract from embedded style databases. The right panel provides instructions and parameter descriptions for the extraction process. Buttons for running, canceling, and closing the dialog are visible at the bottom, along with a progress bar set at zero percent. The environment is neutral and instructional. Visible text includes Style Management - Extract Styles From Project Files, Extract Styles from Project Files, Input directory to search, Style types to include, Extract from embedded style databases, Output XML file, Advanced, Run as Batch Process, Run, Cancel, and Close.

## Repository Structure

This repository contains multiple QGIS-related subprojects:

### Subprojects

#### ExtractStylesfromDirectoriesForStyleManager
Location: `docs/ExtractStylesfromDirectoriesForStyleManager/`
Script: `Scripts/extract_styles_from_projects.py`

A QGIS Processing toolbox script that recursively searches directories for QGIS project files (.qgs, .qgz) and extracts all styles into a single XML file compatible with QGIS Style Manager.

**Features:**
- Extracts symbols, color ramps, text formats, label settings, and more
- Handles duplicate names automatically
- Tags styles with source project name
- Intelligent naming based on layer and symbol type
- Detailed progress feedback

See `docs/ExtractStylesfromDirectoriesForStyleManager/REQUIREMENTS.md` for detailed documentation.
