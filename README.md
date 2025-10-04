# MQS
My QGIS Stuff - A random assortment of things I might reuse. These might be images, styles, scripts or just documentation.

## Support
These are my resources that I make freely available to the world. You can ask me for help using them, but I may not be able to provide it due to knowledge or time constraints. 

## Scripts
Lately I'm doing work using python scripts to be used the in the [QGIS Toolbox](https://docs.qgis.org/3.40/en/docs/user_manual/processing/toolbox.html). You can use these scripts by downloading them, then importing them into your toolbox as following

1. Open your QGIS Toolbox
2. Select `Add script to toolbox` from the little python button
![Screenshot showing the QGIS Toolbox interface with the Add script to toolbox option highlighted. The Python button is selected, and a dialog box is open for importing a new script. The workspace background displays various QGIS tool categories. The tone is instructional and neutral. Visible text includes Add script to toolbox.](docs/ExtractStylesfromDirectoriesForStyleManager/images/adding_script_to_toolbox.png)
3. Double clicking the script name from the toolbox will run it and open the associated dialog screen 
![example toolbox screen from this repo](docs/ExtractStylesfromDirectoriesForStyleManager/images/script_running.png)

## Repository Structure

This repository contains multiple QGIS-related subprojects:

### Subprojects

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

#### ExtractStylesfromDirectoriesForStyleManager
