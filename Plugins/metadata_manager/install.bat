@echo off
REM Installation script for Metadata Manager plugin

echo.
echo ========================================
echo Metadata Manager Plugin Installer
echo ========================================
echo.

set PLUGIN_NAME=metadatamanager
set SOURCE_DIR=%~dp0
set QGIS_PLUGIN_DIR=%APPDATA%\QGIS\QGIS3\profiles\AdvancedUser\python\plugins\%PLUGIN_NAME%

echo Source: %SOURCE_DIR%
echo Target: %QGIS_PLUGIN_DIR%
echo.

REM Check if target directory exists
if exist "%QGIS_PLUGIN_DIR%" (
    echo Removing old plugin installation...
    rmdir /s /q "%QGIS_PLUGIN_DIR%"
)

echo Creating plugin directory...
mkdir "%QGIS_PLUGIN_DIR%"

echo Copying plugin files...

REM Copy Python files
copy /y "%SOURCE_DIR%*.py" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%*.txt" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%*.ui" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%*.qrc" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%*.png" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%*.cfg" "%QGIS_PLUGIN_DIR%\" >nul
copy /y "%SOURCE_DIR%Makefile" "%QGIS_PLUGIN_DIR%\" >nul

REM Copy directories
echo Copying db module...
xcopy /e /i /y "%SOURCE_DIR%db" "%QGIS_PLUGIN_DIR%\db" >nul

echo Copying widgets module...
xcopy /e /i /y "%SOURCE_DIR%widgets" "%QGIS_PLUGIN_DIR%\widgets" >nul

echo Copying i18n...
xcopy /e /i /y "%SOURCE_DIR%i18n" "%QGIS_PLUGIN_DIR%\i18n" >nul

echo Copying help...
xcopy /e /i /y "%SOURCE_DIR%help" "%QGIS_PLUGIN_DIR%\help" >nul

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Plugin installed to:
echo %QGIS_PLUGIN_DIR%
echo.
echo Next steps:
echo 1. Restart QGIS if it's running
echo 2. Go to Plugins ^> Manage and Install Plugins
echo 3. Enable "Metadata Manager" in Installed tab
echo 4. Click the Metadata Manager toolbar button
echo.
pause
