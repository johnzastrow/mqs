# QGIS Viewer

## Overall Goal

This subproject will document the approach for building a portable, executable version of QGIS, and then how to package the executable along with the data. The executable will be a updateable GIS data viewer, based on QGIS, along with pre-packaged data for a project, that can be easily distributed, executed by for non-GIS users (non-technical) and those without network/internet connections. The product of this effort will be called an `atlas` which is the combination of software+configurations+data.

### Technical Goals

1. Design a solution based on many stock resources (software straight from qgis.org without modification) as possible, thereby building few required specialized tools (scripts, complex configurations) to assist the staff in creating the distributable atlas.

2. Manage the size of distributable atlas to keep it reasonable to download from the internet in the frontier areas.

### Use Cases

Current use case is to support volunteers and board members that manage a land trust in Downeast coastal Maine USA. They need the ability to see monthly data on invasive species management, and land projects. The users are barely computer users let alone GIS users. Interface needs to be simple, but still provide more functions that pan/zoom/layers of+off/measure length. There is no budget to maintain a map service, especially when needs are primarily during growing season. Data are updated monthly at the most frequent and every few years for most layers. Layers are primarily vector, but orthophotography exists and is referenced. LIDAR elevation data have been converted to hillshades and contours. Outputs (jpg/png/pdf) from Viewer would be used by leaderhip in high-quality presentations (video call/slides/static download) after marking up.

Tasks needed to support:

    * Pan/zoom
    * Layers on/off
    * Identify features
    * Measure area and length in various units
    * Sketch and annotate on map [good solution not found]
    * Print reasonably high map layout containing sketches

## Audience

The project will allow a mildly-technical staff person to republish an atlas that will allow users within an organization to download a single file with the program and data, then perform simple actions to open the Viewer and immediately explore the pre-packaged data using a simplified QGIS user interface.

## Design objectives

1. Focus on keeping the number of files and directories as few as possible
2. Keep the distribution (program, configurations, data) small
3. Keep the process to rebuild the atlas simple and based on the stock programs from qgis.org. That is, limit or don't use customized configurations or code to create the solution.

## Possible process

Working process for Windows

* [X] Install QGIS Desktop onto thumb drive using the OSGeo4W installer and the Advanced options.
* [ ] Create a .bat file that somehow uses relative paths to run the nearby QGIS executable with program - *problems with complex path variables set by the original installer found myriad interwoven .bat and .env files and unable to wipe them/recreate them at runtime when Atlas is run in new computer*.
  * setup.bat/setup.bat.tmpl, qgis-bin.env, OSGeo4W.bat
  * **State on 10/17:** `RunAtlas.bat` doesn't execute QGIS. Directly running `gis-bin.exe` issues error popup, "Could not load qgis_app.dll". How do I regenerate setup.bat and qgis-bin.env at runtime?
* [X] Use same .bat to start QGIS with flags that starts QGIS with the following previously created and ready to use:
  * [X] Viewer profile to slim down the UI (in a Profiles directory),
  * [X] Data in a single file for good housekeeping (geopackage easy to send to user to update)
  * [X] Project in the same file (geopackage) with usable pre-built settings
  * [ ] Bonus: Popup an attractive intro screen with links, credits and brief explanations (user closes and gets to work)

[ ] Package (.zip?) the QGIS install to distribute

## Progress

Some of this is working

```bash
REM RunAtlas.bat

@echo off

REM Clean up any existing setup files

DEL "%~dp0\bin\setup.bat"
if exist "%~dp0\bin\setup.bat" (
    echo Failed to delete existing setup.bat
    exit /b 1
) else (
    echo Existing setup.bat deleted successfully.
)


REM Clean up any existing environment file
DEL "%~dp0\bin\qgis-bin.env"
if exist "%~dp0\bin\qgis-bin.env" (
    echo Failed to delete existing qgis-bin.env
    exit /b 1
) else (
    echo Existing qgis-bin.env deleted successfully.
)

REM Call OSGeo4W.bat to set up the environment again. Failing
call "%~dp0\OSGeo4W.bat"
if %ERRORLEVEL% neq 0 (
    echo Failed to set up OSGeo4W environment.
    exit /b %ERRORLEVEL%
) else (
    echo OSGeo4W environment set up successfully.
)

REM Launch QGIS with specific profile and project
rem @echo off
call "%~dp0\bin\qgis-bin.exe" --profiles-path "%~dp0\Profiles"  --profile "Viewer2" --project "geopackage:%~dp0\data.gpkg?projectName=main_project"

if %ERRORLEVEL% neq 0 (
    echo Failed to launch QGIS.
    exit /b %ERRORLEVEL%
)   else echo QGIS launched with custom profile and project.

```
