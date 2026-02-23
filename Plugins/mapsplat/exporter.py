"""
MapSplat - Exporter Module

This module handles the actual export process:
- Converting layers to GeoPackage
- Generating PMTiles using ogr2ogr
- Converting QGIS styles to MapLibre style JSON
- Generating the HTML viewer
"""

__version__ = "0.5.7"

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Windows: hide console window when spawning subprocesses
if sys.platform == "win32":
    # Use numeric values to ensure compatibility
    STARTUPINFO = subprocess.STARTUPINFO()
    STARTUPINFO.dwFlags |= 0x00000001  # STARTF_USESHOWWINDOW
    STARTUPINFO.wShowWindow = 0  # SW_HIDE
    CREATIONFLAGS = 0x08000000  # CREATE_NO_WINDOW
else:
    STARTUPINFO = None
    CREATIONFLAGS = 0

from qgis.PyQt.QtCore import QObject, pyqtSignal, QProcess, QTimer

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsCoordinateTransformContext,
)

try:
    from .style_converter import StyleConverter
except ImportError:
    from style_converter import StyleConverter  # test environment (no package)


def generate_html_viewer(settings, style_json, bounds, use_external_style=False):
    """Generate the HTML viewer as a standalone function (no Qt dependencies).

    :param settings: Settings dict; uses ``project_name`` and ``viewer_*`` keys.
                     Unknown/missing viewer keys default to True (control shown).
    :param style_json: Style JSON dict embedded inline (ignored when use_external_style).
    :param bounds: [west, south, east, north] in WGS-84.
    :param use_external_style: If True, reference ./style.json instead of embedding.
    :returns: Complete HTML string for the web viewer.
    """
    center_lng = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2
    project_name = settings.get("project_name", "Map")

    if use_external_style:
        # Fetch style.json at runtime and pass as inline object.
        # Passing './style.json' as a URL string causes MapLibre to normalise
        # source URLs against the style base URL, which prevents pmtiles://
        # sources from being queryable via querySourceFeatures.
        style_ref = "mapStyle"
        _init_open = "\n        fetch('./style.json').then(r => r.json()).then(function(mapStyle) {"
        _init_close = "\n        });"
    else:
        style_ref = json.dumps(style_json, indent=2)
        _init_open = ""
        _init_close = ""

    # ---------- Conditional control snippets ----------
    # Each snippet is an empty string when the control is disabled.
    scale_bar_js = (
        "\n        map.addControl(new maplibregl.ScaleControl(), 'bottom-left');"
        if settings.get('viewer_scale_bar', True) else ""
    )
    geolocate_js = (
        "\n        map.addControl(new maplibregl.GeolocateControl({"
        " positionOptions: { enableHighAccuracy: true },"
        " trackUserLocation: true }), 'top-right');"
        if settings.get('viewer_geolocate', True) else ""
    )
    fullscreen_js = (
        "\n        map.addControl(new maplibregl.FullscreenControl(), 'top-right');"
        if settings.get('viewer_fullscreen', True) else ""
    )

    # Compute top-right offset so custom buttons clear the stacked MapLibre controls.
    # NavigationControl is always added (96 px) + 10 px top margin.
    # FullscreenControl and GeolocateControl each add 39 px (10 px gap + 29 px button)
    # when enabled.  Add 8 px breathing room before our buttons.
    _tr_top = 10 + 96
    if settings.get('viewer_fullscreen', True):
        _tr_top += 39
    if settings.get('viewer_geolocate', True):
        _tr_top += 39
    _tr_top += 8

    # Compute bottom-left offset so custom labels clear the scale bar.
    # MapLibre's ScaleControl is ~22 px tall with a 10 px bottom margin ≈ 32 px.
    # Without scale bar keep a minimal 8 px gap.
    _bl_base = 36 if settings.get('viewer_scale_bar', True) else 8

    coords_html = (
        f'\n    <div id="coords-display"'
        f' style="position:absolute;bottom:{_bl_base + 30}px;left:10px;'
        'background:rgba(255,255,255,0.85);padding:4px 8px;border-radius:3px;'
        'font-family:monospace;font-size:12px;z-index:1;"></div>'
        if settings.get('viewer_coords', True) else ""
    )
    coords_js = (
        "\n        map.on('mousemove', (e) => {"
        " document.getElementById('coords-display').textContent ="
        " e.lngLat.lng.toFixed(5) + ', ' + e.lngLat.lat.toFixed(5); });"
        if settings.get('viewer_coords', True) else ""
    )
    zoom_html = (
        f'\n    <div id="zoom-display"'
        f' style="position:absolute;bottom:{_bl_base}px;left:10px;'
        'background:rgba(255,255,255,0.85);padding:4px 8px;border-radius:3px;'
        'font-family:monospace;font-size:12px;z-index:1;"></div>'
        if settings.get('viewer_zoom_display', True) else ""
    )
    zoom_js = (
        "\n        map.on('zoom', () => {"
        " document.getElementById('zoom-display').textContent ="
        " 'Z: ' + map.getZoom().toFixed(1); });"
        "\n        document.getElementById('zoom-display').textContent ="
        " 'Z: ' + map.getZoom().toFixed(1);"
        if settings.get('viewer_zoom_display', True) else ""
    )
    reset_view_html = (
        f'\n    <button id="reset-view"'
        f' style="position:absolute;top:{_tr_top}px;right:10px;z-index:1;'
        'background:white;border:1px solid #ccc;border-radius:4px;'
        'padding:4px 8px;cursor:pointer;font-size:12px;" title="Reset view">&#8962;</button>'
        if settings.get('viewer_reset_view', True) else ""
    )
    reset_view_js = (
        f"\n        document.getElementById('reset-view').addEventListener('click', () => {{"
        f" map.fitBounds([[{bounds[0]}, {bounds[1]}], [{bounds[2]}, {bounds[3]}]],"
        f" {{ padding: 50 }}); }});"
        if settings.get('viewer_reset_view', True) else ""
    )
    north_reset_html = (
        f'\n    <button id="north-reset"'
        f' style="position:absolute;top:{_tr_top + 37}px;right:10px;z-index:1;'
        'background:white;border:1px solid #ccc;border-radius:4px;'
        'padding:4px 8px;cursor:pointer;font-size:12px;" title="Reset north">N</button>'
        if settings.get('viewer_north_reset', True) else ""
    )
    north_reset_js = (
        "\n        document.getElementById('north-reset').addEventListener('click', () => {"
        " map.setBearing(0); map.setPitch(0); });"
        if settings.get('viewer_north_reset', True) else ""
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - MapSplat</title>
    <!-- MapLibre GL JS from CDN (replace with local files for offline use) -->
    <link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
    <script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
    <script src="https://unpkg.com/pmtiles@3.2.0/dist/pmtiles.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .info-panel {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(255, 255, 255, 0.95);
            padding: 10px 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            font-family: sans-serif;
            font-size: 14px;
            z-index: 1;
            max-width: 280px;
        }}
        .info-panel h3 {{
            margin: 0 0 5px 0;
            font-size: 16px;
        }}
        .info-panel small {{
            color: #666;
        }}
        .layer-control {{
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }}
        .layer-control h4 {{
            margin: 0 0 8px 0;
            font-size: 13px;
            color: #333;
        }}
        .layer-item {{
            display: flex;
            align-items: center;
            margin: 4px 0;
            cursor: pointer;
        }}
        .layer-item input {{
            margin-right: 6px;
            cursor: pointer;
        }}
        .legend-swatch {{
            width: 16px;
            height: 16px;
            min-width: 16px;
            border-radius: 3px;
            margin-right: 6px;
            border: 1px solid rgba(0,0,0,0.2);
        }}
        .legend-swatch.line {{
            height: 4px;
            align-self: center;
        }}
        .legend-swatch.circle {{
            border-radius: 50%;
            width: 12px;
            height: 12px;
            min-width: 12px;
        }}
        .layer-item label {{
            cursor: pointer;
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <div class="info-panel">
        <h3>{project_name}</h3>
        <small>Generated by MapSplat</small>
        <div class="layer-control">
            <h4>Layers</h4>
            <div id="layer-toggles"></div>
        </div>
    </div>{coords_html}{zoom_html}{reset_view_html}{north_reset_html}
    <script>
        // Register PMTiles protocol
        const protocol = new pmtiles.Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);{_init_open}

        // Initialize map
        const map = new maplibregl.Map({{
            container: 'map',
            style: {style_ref},
            center: [{center_lng}, {center_lat}],
            zoom: 4
        }});

        // Add navigation controls
        map.addControl(new maplibregl.NavigationControl(), 'top-right');{scale_bar_js}{geolocate_js}{fullscreen_js}

        // Fit to data bounds on load and create layer controls
        map.on('load', () => {{
            map.fitBounds([
                [{bounds[0]}, {bounds[1]}],
                [{bounds[2]}, {bounds[3]}]
            ], {{ padding: 50 }});

            // Create layer toggles
            const layerToggles = document.getElementById('layer-toggles');
            const style = map.getStyle();
            // Reverse so top layers appear first in the list (MapLibre renders bottom-to-top)
            const layers = style.layers.filter(l => l['source-layer']).reverse();

            // Helper to extract color from layer paint properties
            function getLayerColor(layer) {{
                const paint = layer.paint || {{}};
                // Try different color properties based on layer type
                return paint['fill-color'] || paint['line-color'] ||
                       paint['circle-color'] || paint['text-color'] ||
                       paint['icon-color'] || '#888888';
            }}

            // Helper to get layer geometry type
            function getLayerType(layer) {{
                return layer.type; // fill, line, circle, symbol, etc.
            }}

            // Group by source-layer (actual data layers)
            const seenLayers = new Set();
            layers.forEach(layer => {{
                const sourceLayer = layer['source-layer'];
                if (seenLayers.has(sourceLayer)) return;
                seenLayers.add(sourceLayer);

                const div = document.createElement('div');
                div.className = 'layer-item';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = 'toggle-' + sourceLayer;
                checkbox.checked = true;

                // Create legend swatch
                const swatch = document.createElement('div');
                swatch.className = 'legend-swatch';
                const color = getLayerColor(layer);
                const layerType = getLayerType(layer);

                // Style swatch based on geometry type
                if (layerType === 'line') {{
                    swatch.classList.add('line');
                    swatch.style.backgroundColor = color;
                }} else if (layerType === 'circle') {{
                    swatch.classList.add('circle');
                    swatch.style.backgroundColor = color;
                }} else {{
                    // fill or other
                    swatch.style.backgroundColor = color;
                    // Add outline color if different
                    const outlineColor = layer.paint?.['fill-outline-color'];
                    if (outlineColor && outlineColor !== color) {{
                        swatch.style.borderColor = outlineColor;
                        swatch.style.borderWidth = '2px';
                    }}
                }}

                const label = document.createElement('label');
                label.htmlFor = checkbox.id;
                label.textContent = sourceLayer.replace(/_/g, ' ');
                label.title = sourceLayer;

                checkbox.addEventListener('change', () => {{
                    // Toggle all layers with this source-layer
                    style.layers.forEach(l => {{
                        if (l['source-layer'] === sourceLayer) {{
                            map.setLayoutProperty(l.id, 'visibility',
                                checkbox.checked ? 'visible' : 'none');
                        }}
                    }});
                }});

                div.appendChild(checkbox);
                div.appendChild(swatch);
                div.appendChild(label);
                layerToggles.appendChild(div);
            }});
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
        }});{coords_js}{zoom_js}{reset_view_js}{north_reset_js}{_init_close}
    </script>
</body>
</html>'''


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

        # Cancellation support
        self._cancelled = False
        self._qprocess = None
        self._progress_timer = None
        self._pmtiles_path = None
        self._start_time = None

    def cancel(self):
        """Cancel the export process."""
        self._cancelled = True
        if self._qprocess and self._qprocess.state() != QProcess.NotRunning:
            self._qprocess.kill()
        if self._progress_timer:
            self._progress_timer.stop()

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

        single_file = self.settings.get("single_file", True)
        style_only = self.settings.get("style_only", False)
        use_basemap = self.settings.get("use_basemap", False)

        # [NEW] Basemap extraction
        if use_basemap and not style_only:
            if not self._check_pmtiles_cli():
                self.log_message.emit(
                    "pmtiles CLI not found. Install it from https://github.com/protomaps/go-pmtiles/releases",
                    "error"
                )
                self.finished.emit(False, "")
                return
            bounds = self._calculate_bounds(layers["vector"])
            self.log_message.emit("Extracting basemap to bounding box...", "info")
            success = self._extract_basemap(output_dir, bounds)
            if not success:
                self.finished.emit(False, "")
                return
            self.progress.emit(30)

        if style_only:
            # Skip data export, just generate style and HTML
            self.log_message.emit("Style-only mode: skipping data export", "info")
            self.progress.emit(60)
        elif single_file:
            # Single PMTiles file containing all layers
            self.log_message.emit("Exporting layers to GeoPackage...", "info")
            gpkg_path = os.path.join(output_dir, "data", "layers.gpkg")
            self._export_to_geopackage(layers["vector"], gpkg_path)
            self.progress.emit(40)

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
        else:
            # Separate PMTiles file per layer
            self.log_message.emit("Exporting layers separately...", "info")
            total_layers = len(layers["vector"])
            for i, layer in enumerate(layers["vector"]):
                if self._cancelled:
                    self.log_message.emit("Export cancelled.", "warning")
                    self.finished.emit(False, "")
                    return

                layer_name = self._sanitize_layer_name(layer.name())
                self.log_message.emit(f"Processing layer {i+1}/{total_layers}: {layer.name()}", "info")

                # Export single layer to GeoPackage
                gpkg_path = os.path.join(output_dir, "data", f"{layer_name}.gpkg")
                self._export_to_geopackage([layer], gpkg_path)

                # Convert to PMTiles
                pmtiles_path = os.path.join(output_dir, "data", f"{layer_name}.pmtiles")
                success = self._convert_to_pmtiles(gpkg_path, pmtiles_path)
                if not success:
                    self.log_message.emit(f"Failed to convert {layer_name}", "error")
                    # Continue with other layers instead of aborting
                    continue

                # Clean up intermediate GeoPackage
                if os.path.exists(gpkg_path):
                    os.remove(gpkg_path)

                # Update progress (10-60% range for conversion)
                progress = 10 + int(50 * (i + 1) / total_layers)
                self.progress.emit(progress)

            self.progress.emit(60)

        # Convert styles
        self.log_message.emit("Converting styles...", "info")
        style_converter = StyleConverter(
            layers["vector"],
            self.settings,
            log_callback=lambda msg: self.log_message.emit(msg, "info"),
        )
        style_json = style_converter.convert(
            single_file=single_file,
            output_dir=output_dir if not style_only else None,
        )

        # Handle style merging
        if use_basemap:
            basemap_style_path = self.settings.get("basemap_style_path", "")
            self.log_message.emit("Merging business layers into basemap style...", "info")
            style_json = self._merge_business_into_basemap(basemap_style_path, style_json)
        elif self.settings.get("imported_style_path"):
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

        # Write README and serve script
        self._write_readme(output_dir)
        self._write_serve_script(output_dir)
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
                options.ct = QgsCoordinateTransform(
                    layer.crs(),
                    self.target_crs,
                    self.project
                )

            error, error_message, new_filename, new_layer = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                gpkg_path,
                transform_context,
                options
            )

            if error != QgsVectorFileWriter.NoError:
                self.log_message.emit(f"  Warning: {error_message}", "warning")

    def _convert_to_pmtiles(self, gpkg_path, pmtiles_path):
        """Convert GeoPackage to PMTiles using ogr2ogr (blocking version for thread).

        :param gpkg_path: Input GeoPackage path
        :param pmtiles_path: Output PMTiles path
        :returns: True if successful
        """
        import time
        from qgis.PyQt.QtCore import QCoreApplication

        # Check GDAL version first
        gdal_version = self._check_gdal_version()
        if gdal_version:
            self.log_message.emit(f"  GDAL version: {gdal_version}", "info")

        # Check if PMTiles driver is available
        if not self._check_pmtiles_driver():
            self.log_message.emit(
                "PMTiles driver not available. GDAL 3.8+ required.",
                "error"
            )
            return False

        # Show input file size
        gpkg_size_mb = os.path.getsize(gpkg_path) / (1024 * 1024)
        self.log_message.emit(f"  GeoPackage size: {gpkg_size_mb:.1f} MB", "info")

        # List layers in GeoPackage
        layers_in_gpkg = self._list_gpkg_layers(gpkg_path)
        if layers_in_gpkg:
            self.log_message.emit(f"  Layers to convert: {', '.join(layers_in_gpkg)}", "info")
        else:
            self.log_message.emit("  Warning: Could not list layers in GeoPackage", "warning")

        # Normalize paths for Windows
        gpkg_path = os.path.normpath(gpkg_path)
        pmtiles_path = os.path.normpath(pmtiles_path)
        output_dir = os.path.dirname(pmtiles_path)

        # Build ogr2ogr command
        max_zoom = self.settings.get("max_zoom", 6)

        self.log_message.emit(f"  Max zoom: {max_zoom}", "info")
        self.log_message.emit(f"  Output: {pmtiles_path}", "info")
        self.log_message.emit("  Starting ogr2ogr (this runs in background)...", "info")

        # Use QProcess for non-blocking execution
        self._qprocess = QProcess()
        self._pmtiles_path = pmtiles_path
        self._output_dir = output_dir
        self._start_time = time.time()

        args = [
            "-f", "PMTiles",
            "-dsco", "MINZOOM=0",
            "-dsco", f"MAXZOOM={max_zoom}",
            "-t_srs", "EPSG:3857",
            pmtiles_path,
            gpkg_path
        ]

        self.log_message.emit(f"  Command: ogr2ogr {' '.join(args)}", "info")

        # Start process
        self._qprocess.start("ogr2ogr", args)

        if not self._qprocess.waitForStarted(5000):
            self.log_message.emit("  Failed to start ogr2ogr", "error")
            return False

        self.log_message.emit("  ogr2ogr started, waiting for completion...", "info")

        # Poll with event processing to keep UI responsive
        last_update = time.time()
        while self._qprocess.state() != QProcess.NotRunning:
            # Process Qt events to keep UI responsive
            QCoreApplication.processEvents()

            # Check for cancellation
            if self._cancelled:
                self._qprocess.kill()
                self._qprocess.waitForFinished(1000)
                self.log_message.emit("  Export cancelled by user.", "warning")
                return False

            # Update progress every 3 seconds
            now = time.time()
            if now - last_update >= 3:
                last_update = now
                elapsed = now - self._start_time
                if os.path.exists(pmtiles_path):
                    size_mb = os.path.getsize(pmtiles_path) / (1024 * 1024)
                    self.log_message.emit(f"  Processing... {elapsed:.0f}s, output: {size_mb:.1f} MB", "info")
                else:
                    self.log_message.emit(f"  Processing... {elapsed:.0f}s (building tiles)", "info")

            # Small sleep to avoid busy loop
            self._qprocess.waitForFinished(100)

        # Process finished
        elapsed = time.time() - self._start_time
        exit_code = self._qprocess.exitCode()
        stderr = bytes(self._qprocess.readAllStandardError()).decode('utf-8', errors='replace')
        stdout = bytes(self._qprocess.readAllStandardOutput()).decode('utf-8', errors='replace')

        self.log_message.emit(f"  Conversion finished in {elapsed:.1f} seconds", "info")

        if exit_code != 0:
            error_msg = stderr.strip() if stderr.strip() else stdout.strip()
            if not error_msg:
                error_msg = f"ogr2ogr exited with code {exit_code}"
            self.log_message.emit(f"  ogr2ogr error: {error_msg}", "error")
            return False

        # Show output file size
        if os.path.exists(pmtiles_path):
            pmtiles_size_mb = os.path.getsize(pmtiles_path) / (1024 * 1024)
            self.log_message.emit(f"  PMTiles size: {pmtiles_size_mb:.1f} MB", "info")

        return True

    def _check_gdal_version(self):
        """Check GDAL version.

        :returns: Version string or None
        """
        try:
            result = subprocess.run(
                ["ogr2ogr", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=STARTUPINFO,
                creationflags=CREATIONFLAGS
            )
            if result.returncode == 0:
                # Parse "GDAL 3.8.0, released 2023/..."
                return result.stdout.split(",")[0].strip()
        except Exception:
            pass
        return None

    def _check_pmtiles_driver(self):
        """Check if PMTiles driver is available.

        :returns: True if available
        """
        try:
            result = subprocess.run(
                ["ogr2ogr", "--formats"],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=STARTUPINFO,
                creationflags=CREATIONFLAGS
            )
            return "PMTiles" in result.stdout
        except Exception:
            return False

    def _list_gpkg_layers(self, gpkg_path):
        """List layers in a GeoPackage.

        :param gpkg_path: Path to GeoPackage
        :returns: List of layer names or empty list
        """
        try:
            result = subprocess.run(
                ["ogrinfo", "-so", "-q", gpkg_path],
                capture_output=True,
                text=True,
                timeout=30,
                startupinfo=STARTUPINFO,
                creationflags=CREATIONFLAGS
            )
            if result.returncode == 0:
                # Parse output like "1: layer_name (Multi Polygon)"
                layers = []
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        # Extract layer name between ": " and " ("
                        parts = line.split(": ", 1)
                        if len(parts) > 1:
                            layer_name = parts[1].split(" (")[0]
                            layers.append(layer_name)
                return layers
        except Exception:
            pass
        return []

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

    def _check_pmtiles_cli(self):
        """Check if the pmtiles CLI is available.

        :returns: True if pmtiles CLI is found and functional
        """
        try:
            result = subprocess.run(
                ["pmtiles", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=STARTUPINFO,
                creationflags=CREATIONFLAGS
            )
            return result.returncode == 0
        except Exception:
            return False

    def _extract_basemap(self, output_dir, bounds):
        """Run pmtiles extract to clip basemap to data bounding box.

        :param output_dir: Export output directory
        :param bounds: [west, south, east, north] in EPSG:4326
        :returns: True if successful
        """
        import time
        from qgis.PyQt.QtCore import QCoreApplication

        source = self.settings["basemap_source"]
        output_path = os.path.join(output_dir, "data", "basemap.pmtiles")
        west, south, east, north = bounds
        bbox_str = f"{west},{south},{east},{north}"
        max_zoom = self.settings.get("max_zoom", 10)

        self.log_message.emit(f"  Basemap source: {source}", "info")
        self.log_message.emit(f"  Bounding box: {bbox_str}", "info")
        self.log_message.emit(f"  Max zoom: {max_zoom}", "info")
        self.log_message.emit(f"  Output: {output_path}", "info")

        args = [
            "extract",
            source,
            output_path,
            f"--bbox={bbox_str}",
            f"--maxzoom={max_zoom}",
        ]

        self.log_message.emit(f"  Command: pmtiles {' '.join(args)}", "info")

        self._qprocess = QProcess()
        self._start_time = time.time()

        self._qprocess.start("pmtiles", args)

        if not self._qprocess.waitForStarted(10000):
            self.log_message.emit("  Failed to start pmtiles", "error")
            return False

        self.log_message.emit("  pmtiles extract started, waiting...", "info")

        last_update = time.time()
        while self._qprocess.state() != QProcess.NotRunning:
            QCoreApplication.processEvents()

            if self._cancelled:
                self._qprocess.kill()
                self._qprocess.waitForFinished(1000)
                self.log_message.emit("  Export cancelled by user.", "warning")
                return False

            now = time.time()
            if now - last_update >= 3:
                last_update = now
                elapsed = now - self._start_time
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    self.log_message.emit(
                        f"  Extracting... {elapsed:.0f}s, output: {size_mb:.1f} MB", "info"
                    )
                else:
                    self.log_message.emit(
                        f"  Extracting... {elapsed:.0f}s", "info"
                    )

            self._qprocess.waitForFinished(100)

        elapsed = time.time() - self._start_time
        exit_code = self._qprocess.exitCode()
        stderr = bytes(self._qprocess.readAllStandardError()).decode("utf-8", errors="replace")
        stdout = bytes(self._qprocess.readAllStandardOutput()).decode("utf-8", errors="replace")

        self.log_message.emit(f"  pmtiles extract finished in {elapsed:.1f}s", "info")

        if exit_code != 0:
            error_msg = stderr.strip() or stdout.strip() or f"pmtiles exited with code {exit_code}"
            self.log_message.emit(f"  pmtiles error: {error_msg}", "error")
            return False

        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            self.log_message.emit(f"  Basemap PMTiles size: {size_mb:.1f} MB", "info")

        return True

    def _merge_business_into_basemap(self, basemap_style_path, business_style_json):
        """Merge business layer sources and styles on top of a basemap style.

        The basemap's remote tile URL is replaced with the local extracted file.
        Business layer sources are injected and layers appended (background excluded).
        When the business style has a sprite, it overrides the basemap's sprite so
        that business icons always render from the local file (reliable offline).

        :param basemap_style_path: Path to Protomaps basemap style.json
        :param business_style_json: Style dict generated from QGIS layers
        :returns: Merged style dictionary
        """
        try:
            with open(basemap_style_path, "r", encoding="utf-8") as f:
                basemap = json.load(f)
        except Exception as e:
            self.log_message.emit(f"Failed to load basemap style: {e}", "error")
            return business_style_json

        # Update basemap's vector tile source URL to point to local extracted file.
        # Match any vector source that has a URL (not just Protomaps-hosted ones),
        # so locally-sourced basemaps (e.g. pmtiles://maine4.pmtiles) are rewritten too.
        for src_name, src in basemap.get("sources", {}).items():
            if src.get("type") == "vector" and src.get("url"):
                src["url"] = "pmtiles://data/basemap.pmtiles"
                self.log_message.emit(
                    f"  Updated basemap source '{src_name}' to local file", "info"
                )
                break

        # Inject business data sources
        basemap.setdefault("sources", {}).update(business_style_json.get("sources", {}))

        # Append business layers, skipping background (basemap provides its own)
        overlay_layers = [
            layer for layer in business_style_json.get("layers", [])
            if layer.get("id") != "background"
        ]
        basemap.setdefault("layers", []).extend(overlay_layers)

        self.log_message.emit(
            f"  Merged {len(overlay_layers)} business layer(s) into basemap style", "info"
        )

        # Handle sprites — always use the local business sprite directly.
        # Multi-sprite arrays with remote basemap URLs are unreliable when the remote
        # sprite is slow or unreachable; the local sprite is guaranteed to be present.
        # Basemap icon-image layers (shields, arrows, POIs) will silently render no icon,
        # but all fill/line/water/label layers continue to render normally.
        business_sprite = business_style_json.get("sprite")

        if business_sprite:
            basemap["sprite"] = business_sprite
            self.log_message.emit(
                "  Using local business sprite for icons", "info"
            )

        return basemap


    def _generate_html_viewer(self, output_dir, style_json, layers):
        """Generate the HTML viewer file.

        :param output_dir: Output directory
        :param style_json: Style JSON dictionary
        :param layers: Dictionary of layers
        """
        # Calculate initial bounds from layers
        bounds = self._calculate_bounds(layers["vector"])

        # If exporting style.json, reference it externally instead of embedding
        use_external_style = self.settings.get("export_style_json", False)
        html_content = self._get_html_template(style_json, bounds, use_external_style)
        html_path = os.path.join(output_dir, "index.html")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _calculate_bounds(self, layers):
        """Calculate combined bounds of all layers.

        :param layers: List of layers
        :returns: [west, south, east, north] in EPSG:4326
        """
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

    def _get_html_template(self, style_json, bounds, use_external_style=False):
        """Get the HTML template.

        :param style_json: Style JSON dictionary
        :param bounds: [west, south, east, north]
        :param use_external_style: If True, reference ./style.json instead of embedding
        :returns: HTML string
        """
        return generate_html_viewer(self.settings, style_json, bounds, use_external_style)

    def _copy_maplibre_assets(self, output_dir):
        """Copy MapLibre JS assets to output directory.

        :param output_dir: Output directory
        """
        lib_dir = os.path.join(output_dir, "lib")

        # Using CDN for now - assets downloaded at runtime by browser
        self.log_message.emit("  Using CDN for MapLibre assets", "info")

        # TODO: Optionally download and bundle for offline use
        # See TODO.md for planned offline bundling feature

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

    def _write_serve_script(self, output_dir):
        """Write a simple Python server script for local viewing.

        :param output_dir: Output directory
        """
        serve_script = '''#!/usr/bin/env python3
"""
HTTP server with Range request support for PMTiles.

Usage:
    python serve.py

Then open http://localhost:8000 in your browser.
Press Ctrl+C to stop the server (or close this window).
"""

import http.server
import os
import signal
import sys
import threading
import webbrowser

PORT = 8000
server_running = True

class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler with support for Range requests (required for PMTiles)."""

    def log_error(self, format, *args):
        """Suppress connection aborted errors (normal when browser cancels requests)."""
        if "ConnectionAbortedError" not in str(args):
            super().log_error(format, *args)

    def handle(self):
        """Handle requests, silently ignoring connection aborts."""
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass  # Browser cancelled the request, this is normal

    def send_head(self):
        """Handle HEAD requests and Range requests."""
        path = self.translate_path(self.path)

        if os.path.isdir(path):
            return super().send_head()

        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return None

        file_size = os.path.getsize(path)

        # Check for Range header
        range_header = self.headers.get("Range")

        if range_header:
            # Parse Range header (e.g., "bytes=0-1023")
            try:
                range_spec = range_header.replace("bytes=", "")
                start, end = range_spec.split("-")
                start = int(start) if start else 0
                end = int(end) if end else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)  # Partial Content
                self.send_header("Content-Type", self.guess_type(path))
                self.send_header("Content-Length", str(length))
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                f = open(path, "rb")
                f.seek(start)
                return _FileWrapper(f, length)
            except Exception as e:
                self.send_error(416, "Range Not Satisfiable")
                return None
        else:
            # Normal request
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return open(path, "rb")

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Length, Content-Range")
        self.end_headers()

class _FileWrapper:
    """Wrapper to read a specific byte range from a file."""
    def __init__(self, f, length):
        self.f = f
        self.remaining = length

    def read(self, size=None):
        if self.remaining <= 0:
            return b""
        if size is None or size > self.remaining:
            size = self.remaining
        data = self.f.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()

def shutdown_server(signum=None, frame=None):
    """Handle shutdown signal."""
    global server_running
    server_running = False
    print("\\nShutting down server...")
    httpd.shutdown()
    print("Server stopped.")
    sys.exit(0)

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")

    print(f"Starting server at http://localhost:{PORT}")
    print("Press Ctrl+C to stop (or close this window)\\n")

    httpd = http.server.HTTPServer(("", PORT), RangeRequestHandler)

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)
    # Windows-specific: handle Ctrl+Break
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, shutdown_server)

    # Run server in a daemon thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    webbrowser.open(f"http://localhost:{PORT}")

    try:
        # Keep main thread alive with a simple loop
        while server_running:
            server_thread.join(timeout=0.5)
            if not server_thread.is_alive():
                break
    except KeyboardInterrupt:
        shutdown_server()
'''
        serve_path = os.path.join(output_dir, "serve.py")
        with open(serve_path, "w", encoding="utf-8") as f:
            f.write(serve_script)

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
