# QGIS Viewer

## Overall Goal

This subproject will document the approach for building a portable, executable version of QGIS, and then how to package the executable along with the data. The executable will be a updateable GIS data viewer, based on QGIS, along with pre-packaged data and a project, that can be easily distributed, executed by for non-GIS users (non-technical) and those without network/internet connections. The product of this effort will be called an `atlas` which is the combination of software+configurations+data. History and the internet seem littered with attempts (both current and abandoned) to build the "portable" QGIS part. It feels like the process is brittle, perhaps due to shifting QGIS packaging/deployment layouts, and the secret (Google doesn't show any formal docs) recipes for producing these portable installs must get out of date people stop producing the builds. 

### Technical Goals

1. Design a solution based on many stock resources (software straight from qgis.org without modification) as possible, thereby building few required specialized tools (scripts, complex configurations) to assist the staff in creating the distributable atlas.

2. Document the above so that we all can reference the recipe and adjust it as QGIS deployments evolve.

3. Manage the size of distributable atlas to keep it reasonable to download from the internet in the frontier areas.

### Use Cases

Current use case is to support volunteers and board members that manage a land trust in Downeast coastal Maine USA. They need the ability to see spatial data regarding the wildlands they manage (i.e., invasive species management, trail and land projects). Some users have primitive computer skills and effectively none are GIS users. Therefore, the interface needs to be simple but still provide more functions that pan/zoom/layers of+off/measure length. There is no budget or in-house ability to maintain a map service. Data are updated monthly at the most frequent and every few years for most layers. Layers are primarily vector, but orthophotography exists and is referenced. LIDAR elevation data have been converted to hillshades and contours. Outputs (jpg/png/pdf) from Viewer would be used by leadership in high-quality presentations (video call/slides/static download) after marking up.

Tasks needed to support:

    * Pan/zoom
    * Layers on/off
    * Identify features
    * Measure area and length in various units
    * Sketch and annotate on map [good solution not found]
    * Print reasonably high map layout containing sketches

## Audience

The project will allow a mildly-technical staff person to republish an atlas with updated data (or just updated data + project) that will allow users within an organization to download a single .zip file with the program and data, then perform simple actions to open the Viewer and immediately explore the pre-packaged data using a simplified QGIS user interface. No scripts or software would need to be adjusted.

## Design objectives

1. Focus on keeping the number of files and directories as few as possible
2. Keep the distribution (program, configurations, data) small
3. Keep the process to rebuild the atlas simple and based on the stock programs from qgis.org. That is, limit or don't use customized/complex configurations or code to create the solution.

## Possible process

Working process for Windows - with status checked off

* [X] Install QGIS Desktop onto thumb drive using the OSGeo4W installer and the Advanced options.
* [ ] Create a .bat file that somehow uses relative paths to run the nearby QGIS executable with program - **problems** *with complex path variables set by the original installer found myriad interwoven .bat and .env files and unable to wipe them/recreate them at runtime when Atlas is run in new computer*.
  * setup.bat/setup.bat.tmpl, qgis-bin.env, OSGeo4W.bat
  * **State on 10/17:** `RunAtlas.bat` doesn't execute QGIS. Directly running `gis-bin.exe` issues error popup, "Could not load qgis_app.dll". How do I regenerate setup.bat and qgis-bin.env at runtime?
* [X] Use same .bat to start QGIS with flags that starts QGIS with the following previously created and ready to use:
  * [X] Viewer profile to slim down the UI (in a Profiles directory),
  * [X] Data in a single file for good housekeeping (geopackages + GeoTiffs? - easy to send to user to update)
  * [X] Project in the same file (geopackage = styles + layers + metadata + non-spatial tables with rships) with usable pre-built settings
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


## Notes

Just saw this `Light` plugin referenced in another QEP. Not quite what we're after, but interesting. Doesn't meet the Download/Run level of simplicity.

https://github.com/itc-crib/qgis-light
