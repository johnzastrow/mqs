"""
MapSplat - Exporter Module

This module handles the actual export process:
- Converting layers to GeoPackage
- Generating PMTiles using ogr2ogr
- Converting QGIS styles to MapLibre style JSON
- Generating the HTML viewer
"""

__version__ = "0.1.1"

import os
import json
import shutil
import subprocess
from pathlib import Path

from qgis.PyQt.QtCore import QObject, pyqtSignal

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext,
)

from .style_converter import StyleConverter


class MapSplatExporter(QObject):
    """Handles exporting QGIS layers to web map package."""

    # Signals
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str, str)  # message, level
    finished = pyqtSignal(bool, str)  # success, output_path

    def __init__(self, iface, settings):
        """Initialize exporter.

        :param iface: QGIS interface
        :param settings: Export settings dictionary
        """
        super().__init__()
        self.iface = iface
        self.settings = settings
        self.project = QgsProject.instance()

        # Target CRS (Web Mercator)
        self.target_crs = QgsCoordinateReferenceSystem("EPSG:3857")

    def run(self):
        """Run the export process."""
        try:
            self._do_export()
        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}", "error")
            self.finished.emit(False, "")

    def _do_export(self):
        """Internal export implementation."""
        output_base = self.settings["output_folder"]
        project_name = self.settings["project_name"]
        output_dir = os.path.join(output_base, f"{project_name}_webmap")

        # Create output directory structure
        self.log_message.emit(f"Creating output directory: {output_dir}", "info")
        self._create_output_structure(output_dir)
        self.progress.emit(10)

        # Get selected layers
        layers = self._get_selected_layers()
        if not layers:
            self.log_message.emit("No valid layers to export", "error")
            self.finished.emit(False, "")
            return

        # Export vector layers to GeoPackage
        self.log_message.emit("Exporting layers to GeoPackage...", "info")
        gpkg_path = os.path.join(output_dir, "data", "layers.gpkg")
        self._export_to_geopackage(layers["vector"], gpkg_path)
        self.progress.emit(40)

        # Convert to PMTiles
        self.log_message.emit("Converting to PMTiles...", "info")
        pmtiles_path = os.path.join(output_dir, "data", "layers.pmtiles")
        success = self._convert_to_pmtiles(gpkg_path, pmtiles_path)
        if not success:
            self.finished.emit(False, "")
            return
        self.progress.emit(60)

        # Clean up intermediate GeoPackage
        if os.path.exists(gpkg_path):
            os.remove(gpkg_path)

        # Convert styles
        self.log_message.emit("Converting styles...", "info")
        style_converter = StyleConverter(layers["vector"], self.settings)
        style_json = style_converter.convert()

        # Handle imported style merge
        if self.settings.get("imported_style_path"):
            style_json = self._merge_imported_style(style_json)

        self.progress.emit(75)

        # Write style.json if requested
        if self.settings["export_style_json"]:
            style_path = os.path.join(output_dir, "style.json")
            with open(style_path, "w", encoding="utf-8") as f:
                json.dump(style_json, f, indent=2)
            self.log_message.emit(f"Wrote style.json", "info")

        # Generate HTML viewer
        self.log_message.emit("Generating HTML viewer...", "info")
        self._generate_html_viewer(output_dir, style_json, layers)
        self.progress.emit(90)

        # Copy MapLibre assets
        self._copy_maplibre_assets(output_dir)

        # Write README
        self._write_readme(output_dir)
        self.progress.emit(100)

        self.log_message.emit("Export complete!", "success")
        self.finished.emit(True, output_dir)

    def _create_output_structure(self, output_dir):
        """Create the output directory structure."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(output_dir, "data")).mkdir(exist_ok=True)
        Path(os.path.join(output_dir, "lib")).mkdir(exist_ok=True)

    def _get_selected_layers(self):
        """Get the selected layers from the project.

        :returns: Dictionary with 'vector' and 'raster' layer lists
        """
        layers = {"vector": [], "raster": []}

        for layer_id in self.settings["layer_ids"]:
            layer = self.project.mapLayer(layer_id)
            if layer is None:
                continue

            if isinstance(layer, QgsVectorLayer):
                layers["vector"].append(layer)
            elif isinstance(layer, QgsRasterLayer):
                layers["raster"].append(layer)

        return layers

    def _export_to_geopackage(self, layers, gpkg_path):
        """Export vector layers to a GeoPackage.

        :param layers: List of QgsVectorLayer
        :param gpkg_path: Output GeoPackage path
        """
        transform_context = QgsCoordinateTransformContext()

        for i, layer in enumerate(layers):
            layer_name = self._sanitize_layer_name(layer.name())
            self.log_message.emit(f"  Exporting: {layer.name()} -> {layer_name}", "info")

            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.layerName = layer_name
            options.fileEncoding = "UTF-8"

            # Set action mode (create or append)
            if i == 0:
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
            else:
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

            # Transform to Web Mercator
            if layer.crs() != self.target_crs:
                options.ct = QgsCoordinateTransformContext()

            error, error_message, new_filename, new_layer = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                gpkg_path,
                transform_context,
                options
            )

            if error != QgsVectorFileWriter.NoError:
                self.log_message.emit(f"  Warning: {error_message}", "warning")

    def _convert_to_pmtiles(self, gpkg_path, pmtiles_path):
        """Convert GeoPackage to PMTiles using ogr2ogr.

        :param gpkg_path: Input GeoPackage path
        :param pmtiles_path: Output PMTiles path
        :returns: True if successful
        """
        # Build ogr2ogr command
        cmd = [
            "ogr2ogr",
            "-f", "PMTiles",
            "-dsco", "MINZOOM=0",
            "-dsco", "MAXZOOM=14",
            "-t_srs", "EPSG:3857",
            pmtiles_path,
            gpkg_path
        ]

        self.log_message.emit(f"  Running: {' '.join(cmd)}", "info")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                self.log_message.emit(f"  ogr2ogr error: {result.stderr}", "error")
                return False

            return True

        except FileNotFoundError:
            self.log_message.emit(
                "ogr2ogr not found. Ensure GDAL 3.8+ is installed.",
                "error"
            )
            return False
        except subprocess.TimeoutExpired:
            self.log_message.emit("PMTiles conversion timed out.", "error")
            return False

    def _merge_imported_style(self, style_json):
        """Merge imported style with generated style.

        :param style_json: Generated style dictionary
        :returns: Merged style dictionary
        """
        import_path = self.settings["imported_style_path"]
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                imported = json.load(f)

            # Merge layers from imported style (imported takes precedence)
            imported_layer_ids = {l["id"] for l in imported.get("layers", [])}
            for layer in style_json.get("layers", []):
                if layer["id"] not in imported_layer_ids:
                    imported.setdefault("layers", []).append(layer)

            self.log_message.emit("Merged imported style", "info")
            return imported

        except Exception as e:
            self.log_message.emit(f"Failed to merge style: {e}", "warning")
            return style_json

    def _generate_html_viewer(self, output_dir, style_json, layers):
        """Generate the HTML viewer file.

        :param output_dir: Output directory
        :param style_json: Style JSON dictionary
        :param layers: Dictionary of layers
        """
        # Calculate initial bounds from layers
        bounds = self._calculate_bounds(layers["vector"])

        html_content = self._get_html_template(style_json, bounds)
        html_path = os.path.join(output_dir, "index.html")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _calculate_bounds(self, layers):
        """Calculate combined bounds of all layers.

        :param layers: List of layers
        :returns: [west, south, east, north] in EPSG:4326
        """
        from qgis.core import QgsCoordinateTransform

        if not layers:
            return [-180, -85, 180, 85]

        combined = None
        crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")

        for layer in layers:
            extent = layer.extent()

            # Transform to WGS84
            if layer.crs() != crs_4326:
                transform = QgsCoordinateTransform(
                    layer.crs(),
                    crs_4326,
                    QgsProject.instance()
                )
                extent = transform.transformBoundingBox(extent)

            if combined is None:
                combined = extent
            else:
                combined.combineExtentWith(extent)

        if combined:
            return [
                combined.xMinimum(),
                combined.yMinimum(),
                combined.xMaximum(),
                combined.yMaximum()
            ]

        return [-180, -85, 180, 85]

    def _get_html_template(self, style_json, bounds):
        """Get the HTML template with embedded style.

        :param style_json: Style JSON dictionary
        :param bounds: [west, south, east, north]
        :returns: HTML string
        """
        # Calculate center
        center_lng = (bounds[0] + bounds[2]) / 2
        center_lat = (bounds[1] + bounds[3]) / 2

        style_str = json.dumps(style_json, indent=2)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.settings["project_name"]} - MapSplat</title>
    <link rel="stylesheet" href="lib/maplibre-gl.css">
    <script src="lib/maplibre-gl.js"></script>
    <script src="lib/pmtiles.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-family: sans-serif;
            font-size: 14px;
            z-index: 1;
        }}
        .info-panel h3 {{
            margin: 0 0 5px 0;
            font-size: 16px;
        }}
        .info-panel small {{
            color: #666;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>{self.settings["project_name"]}</h3>
        <small>Generated by MapSplat</small>
    </div>

    <script>
        // Register PMTiles protocol
        const protocol = new pmtiles.Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);

        // Initialize map
        const map = new maplibregl.Map({{
            container: 'map',
            style: {style_str},
            center: [{center_lng}, {center_lat}],
            zoom: 10,
            maxBounds: [{bounds}]
        }});

        // Add navigation controls
        map.addControl(new maplibregl.NavigationControl(), 'top-right');

        // Fit to data bounds on load
        map.on('load', () => {{
            map.fitBounds([
                [{bounds[0]}, {bounds[1]}],
                [{bounds[2]}, {bounds[3]}]
            ], {{ padding: 50 }});
        }});

        // Click handler for feature identification
        map.on('click', (e) => {{
            const features = map.queryRenderedFeatures(e.point);
            if (features.length > 0) {{
                const feature = features[0];
                const props = feature.properties;

                let html = '<div style="max-width:300px;max-height:200px;overflow:auto;">';
                for (const [key, value] of Object.entries(props)) {{
                    html += `<strong>${{key}}:</strong> ${{value}}<br>`;
                }}
                html += '</div>';

                new maplibregl.Popup()
                    .setLngLat(e.lngLat)
                    .setHTML(html)
                    .addTo(map);
            }}
        }});

        // Change cursor on feature hover
        map.on('mouseenter', () => {{
            map.getCanvas().style.cursor = 'pointer';
        }});
        map.on('mouseleave', () => {{
            map.getCanvas().style.cursor = '';
        }});
    </script>
</body>
</html>'''

    def _copy_maplibre_assets(self, output_dir):
        """Copy MapLibre JS assets to output directory.

        :param output_dir: Output directory
        """
        lib_dir = os.path.join(output_dir, "lib")

        # For now, create placeholder files with CDN references
        # In production, we'd bundle the actual files
        self.log_message.emit(
            "Note: MapLibre assets should be downloaded for offline use",
            "warning"
        )

        # Create a loader script that falls back to CDN
        loader_js = '''// MapLibre GL JS Loader
// For offline use, download maplibre-gl.js and maplibre-gl.css from:
// https://unpkg.com/maplibre-gl/dist/

// This file is a placeholder - the actual MapLibre files should be placed here
console.log("MapSplat: MapLibre assets loaded");
'''
        # Write placeholder (actual implementation would bundle real files)
        # For MVP, we'll modify the HTML to use CDN
        pass

    def _write_readme(self, output_dir):
        """Write README file with deployment instructions.

        :param output_dir: Output directory
        """
        readme_content = f'''# {self.settings["project_name"]} - Web Map

Generated by MapSplat QGIS Plugin

## Contents

- `index.html` - Main web map viewer
- `data/layers.pmtiles` - Vector tile data
- `style.json` - MapLibre style (if exported)
- `lib/` - JavaScript libraries

## Deployment

1. Upload this entire folder to any web server that supports HTTP Range Requests
2. Ensure CORS is configured if hosting on a different domain
3. Open index.html in a browser

### Supported Hosting

- Any static web server (nginx, Apache, Caddy)
- Cloud storage (AWS S3, Cloudflare R2, Google Cloud Storage)
- GitHub Pages
- Netlify, Vercel, etc.

### CORS Configuration

If hosting PMTiles on a different domain, configure CORS headers:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, HEAD
Access-Control-Allow-Headers: Range
Access-Control-Expose-Headers: Content-Range, Content-Length
```

## Offline Use

For fully offline operation, download MapLibre GL JS:
- https://unpkg.com/maplibre-gl/dist/maplibre-gl.js
- https://unpkg.com/maplibre-gl/dist/maplibre-gl.css
- https://unpkg.com/pmtiles/dist/pmtiles.js

Place these files in the `lib/` folder.

## Credits

- Generated by MapSplat (https://github.com/johnzastrow/mqs)
- Uses MapLibre GL JS (https://maplibre.org/)
- Uses PMTiles (https://protomaps.com/docs/pmtiles)
'''
        readme_path = os.path.join(output_dir, "README.txt")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _sanitize_layer_name(self, name):
        """Sanitize layer name for use in files/PMTiles.

        :param name: Original layer name
        :returns: Sanitized name
        """
        # Replace spaces and special chars with underscores
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        # Remove consecutive underscores
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        # Ensure lowercase for consistency
        return sanitized.lower()
