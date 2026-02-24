# MapSplat

**Export QGIS projects to static web maps using PMTiles and MapLibre GL JS**

![MapSplat](docs/images/mapsplat_logo.png)

[![QGIS](https://img.shields.io/badge/QGIS-3.40%2B-green.svg)](https://qgis.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.5.5-orange.svg)](docs/CHANGELOG.md)

MapSplat is a QGIS plugin that exports your project layers to self-contained static web map packages. The output, including a baby python server, can be hosted on any static web server, cloud storage, or even run locally for quick sharing and prototyping. 

This was a little project with a focused use case that I whipped up for myself. It has some potential to do more, but it began as a way to show points on basemap with little more than a simple web server, without needing to set up a tile server or learn a new stack. Check the [docs](docs/) directory for thought history and a detailed assessment of the project's strengths, challenges, and technical feasibility - including why we chose PMTiles and MapLibre GL JS, and how we handle styling and basemap overlays.

**To run it, put the [pmtiles CLI](https://github.com/protomaps/go-pmtiles/releases) on your PATH, then export a web map from QGIS and run the included `serve.py` script.**



## Features

### Core Export
- **Vector Export**: Export vector layers to PMTiles format (single file or per-layer)
- **Automatic Styling**: Convert QGIS symbology to MapLibre GL Style JSON
- **Label Support**: Extract QGIS labels (text field, font, halo) to MapLibre symbol layers
- **Auto-Reprojection**: All layers automatically transformed to Web Mercator (EPSG:3857)
- **Style Roundtripping**: Export `style.json` for editing in Maputnik, then re-import

### Basemap Overlay Mode
- **Protomaps Basemap**: Overlay your data on a Protomaps-compatible basemap (local `.pmtiles` or URL)
- **Basemap Extraction**: Automatically clips basemap tiles to your data extent using the `pmtiles` CLI
- **Style Merging**: Merges basemap style with your data layers; your layers render on top

### Viewer
- **Interactive Viewer**: Self-contained `index.html` with click-to-identify popups
- **Layer Toggles**: Per-layer visibility controls in a side panel
- **Viewer Controls**: Configurable scale bar, geolocate, fullscreen, coordinates display, zoom display, reset view, and north reset buttons
- **Offline Capable**: Viewer assets (MapLibre GL JS, PMTiles) can be bundled locally
- **Built-in Dev Server**: `serve.py` included with every export — handles HTTP Range requests required by PMTiles

### Compatibility
- **Qt5/Qt6**: Works with QGIS 3.x (Qt5) and QGIS 4.x (Qt6)
- **Static Hosting**: No server-side processing; works on GitHub Pages, Netlify, S3, or any web host

## Limitations

- **Vector layers only**: Raster layers (WMS, GeoTIFF, etc.) are not exported
- **No 3D**: Extrusions, terrain, and 3D tiles are not supported
- **No live data**: Output is a static snapshot; layers are not updated after export
- **Rule-based renderer**: Simple rule filters are converted; complex nested rules fall back to a default style
- **Heatmap / Point Cluster renderers**: Fall back to a simple default style
- **Zoom range**: Tile generation is bounded by the max zoom set at export time (default 6); features are not visible above that zoom without re-exporting
- **Basemap overlay requires `pmtiles` CLI**: The [Protomaps CLI](https://github.com/protomaps/go-pmtiles/releases) must be on your PATH for basemap extraction; the plugin checks for it at export time
- **Basemap source URL requires internet at export time**: When extracting from a remote URL, an internet connection is required during export (not during viewing)
- **Single sprite sheet**: All custom icons share one sprite; icon names must be unique across all exported layers
- **No authentication**: The viewer and `serve.py` serve files without access control
- **`python -m http.server` will not work**: The standard Python dev server does not reliably support HTTP Range requests; always use the included `serve.py` or a proper web server

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| QGIS | 3.40+ | Also compatible with 4.0 beta |
| GDAL | 3.8+ | Required for native PMTiles support via `ogr2ogr` |
| Python | 3.9+ | Bundled with QGIS |
| pmtiles CLI | Any | Required only for basemap overlay mode |

## Installation

### From Source (Development)

**Linux/macOS:**
```bash
git clone https://github.com/johnzastrow/mqs.git
cd mqs/Plugins/mapsplat
make deploy
```

**Windows (Command Prompt):**
```cmd
git clone https://github.com/johnzastrow/mqs.git
cd mqs\Plugins\mapsplat
deploy.bat
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/johnzastrow/mqs.git
cd mqs\Plugins\mapsplat
.\deploy.ps1
```

Restart QGIS and enable the plugin in Plugin Manager.

### From ZIP (Release)

1. Download the latest `mapsplat.zip` from [Releases](https://github.com/johnzastrow/mqs/releases)
2. In QGIS: **Plugins > Manage and Install Plugins > Install from ZIP**
3. Select the downloaded ZIP file
4. Enable "MapSplat" in the plugin list

### Manual Installation

Copy the `mapsplat` folder to your QGIS plugins directory:

| OS | Path |
|----|------|
| Linux | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |
| macOS | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |
| Windows | `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\` |

## Usage

### Basic Export

1. Open a QGIS project with vector layers
2. Click the **MapSplat** button in the toolbar (or **Web > MapSplat**)
3. Select layers to export in the dockable panel
4. Choose export options:
   - **PMTiles mode**: Single file (all layers) or separate files per layer
   - **Export style.json**: Check to save an editable style file alongside the viewer
   - **Max zoom**: Highest zoom level at which tiles are generated (4–18; default 6)
5. Set output folder and project name
6. Click **Export Web Map**

### Basemap Overlay Export

1. Check **Use basemap overlay** in the export panel
2. Choose a basemap source:
   - **URL**: A hosted Protomaps `.pmtiles` file (requires internet at export time)
   - **File**: A locally downloaded Protomaps `.pmtiles` file
3. Provide a **basemap style.json** (download from [protomaps/basemaps](https://github.com/protomaps/basemaps/releases))
4. Ensure the `pmtiles` CLI is on your PATH
5. Export as normal — the basemap is clipped to your data extent and bundled in `data/basemap.pmtiles`

### Output Structure

**Standalone (no basemap):**
```
myproject_webmap/
├── index.html              # Interactive web map viewer
├── style.json              # MapLibre style (if "Export style.json" checked)
├── serve.py                # Local dev server with Range request support
├── data/
│   └── layers.pmtiles      # Vector tile data (all layers combined)
├── lib/
│   ├── maplibre-gl.js      # MapLibre GL JS library
│   ├── maplibre-gl.css     # MapLibre styles
│   └── pmtiles.js          # PMTiles protocol handler
└── sprites/                # Icon sprite sheet (if symbol layers present)
    ├── sprites.png
    └── sprites.json
```

**Basemap overlay:**
```
myproject_webmap/
├── index.html
├── style.json
├── serve.py
├── data/
│   ├── layers.pmtiles      # Your exported vector data
│   └── basemap.pmtiles     # Basemap tiles clipped to your extent
└── lib/  ...
```

## Local Viewing

**Important**: You cannot open `index.html` directly from the filesystem (`file://`). PMTiles requires HTTP Range requests, which only work over HTTP/HTTPS.

### Using the Included `serve.py` (Recommended)

Every MapSplat export includes a `serve.py` script that provides a lightweight HTTP server with proper Range request support:

```bash
cd myproject_webmap/
python serve.py
```

Then open http://localhost:8000 in your browser.

`serve.py` handles:
- HTTP Range requests (required for PMTiles random access)
- CORS headers (required if the viewer and tiles are on different origins)
- CORS preflight (`OPTIONS`) requests
- Clean shutdown on `Ctrl+C` or `SIGTERM`

> **Why not `python -m http.server`?** The standard Python dev server does not reliably support Range requests and will cause PMTiles to fail to load.

### Other Options

```bash
# Node.js (npx, no install needed)
npx serve myproject_webmap/

# PHP
cd myproject_webmap/
php -S localhost:8000
```

## Deployment

### Static Hosting (GitHub Pages, Netlify, Vercel, S3)

The web map is fully self-contained. Upload the entire output folder to any static host that supports Range requests (all major CDNs do).

**GitHub Pages:**
```bash
cd myproject_webmap/
git init && git add . && git commit -m "web map"
git remote add origin https://github.com/username/my-webmap.git
git push -u origin main
# Enable GitHub Pages in repository Settings → Pages
```

**Netlify / Vercel:** Drag and drop the output folder to the dashboard, or connect your repository.

**AWS S3:**
```bash
aws s3 sync myproject_webmap/ s3://my-bucket/webmap/ --acl public-read
```

### Linux VPS with systemd

`serve.py` can run as a persistent background service on a Linux VPS. It is suitable for low-to-moderate traffic (dozens of concurrent users). For higher traffic, use Nginx (see below).

**1. Copy files to the server:**
```bash
scp -r myproject_webmap/ user@yourserver:/var/www/myproject_webmap/
```

**2. Create the service file** at `/etc/systemd/system/mapsplat-myproject.service`:
```ini
[Unit]
Description=MapSplat Web Map — My Project
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/myproject_webmap
ExecStart=/usr/bin/python3 /var/www/myproject_webmap/serve.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**3. Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mapsplat-myproject
sudo systemctl start mapsplat-myproject
sudo systemctl status mapsplat-myproject
```

**Notes on `serve.py` as a service:**
- The `webbrowser.open()` call in `serve.py` silently fails on headless servers — the server still starts normally
- The server binds to all interfaces on port 8000; open that port in your firewall if needed
- Logs go to stdout/stderr and are captured by `journalctl -u mapsplat-myproject`
- Python's `http.server` is **single-threaded**: one request is processed at a time. This is sufficient for personal or small-team use but not for high-traffic public maps

**Firewall (ufw):**
```bash
sudo ufw allow 8000/tcp
```

### Linux VPS with Nginx (Recommended for Production)

Nginx handles Range requests natively, serves files in parallel, and can terminate HTTPS. Use it instead of `serve.py` for production deployments.

**Install Nginx:**
```bash
sudo apt install nginx
sudo cp -r myproject_webmap/ /var/www/myproject_webmap/
```

**`/etc/nginx/sites-available/myproject`:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/myproject_webmap;

    location / {
        try_files $uri $uri/ =404;
    }

    # CORS headers for PMTiles (needed if served from a different domain)
    location ~* \.pmtiles$ {
        add_header Access-Control-Allow-Origin  "*" always;
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Range" always;
        add_header Access-Control-Expose-Headers "Content-Length, Content-Range" always;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Add HTTPS with Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### CORS Configuration

CORS headers are only required if your `index.html` and `.pmtiles` files are served from **different origins**. When both are served from the same server and domain (the typical case), CORS is not needed.

**Apache (.htaccess):**
```apache
<FilesMatch "\.pmtiles$">
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, HEAD, OPTIONS"
    Header set Access-Control-Allow-Headers "Range"
    Header set Access-Control-Expose-Headers "Content-Length, Content-Range"
</FilesMatch>
```

**AWS S3 CORS policy:**
```json
[{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["Range"],
    "ExposeHeaders": ["Content-Range", "Content-Length", "ETag"],
    "MaxAgeSeconds": 3600
}]
```

### Offline Viewing

For fully offline operation (no CDN), replace the `unpkg.com` script tags in `index.html` with local copies, or ensure the `lib/` folder contains:

| File | Source |
|------|--------|
| `maplibre-gl.js` | https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js |
| `maplibre-gl.css` | https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css |
| `pmtiles.js` | https://unpkg.com/pmtiles@3.2.0/dist/pmtiles.js |

## Supported Symbology

| QGIS Renderer | Support | Notes |
|---------------|---------|-------|
| Single Symbol | Full | Fill, line, and marker symbol layers |
| Categorized | Full | MapLibre `match` expressions |
| Graduated | Full | MapLibre `step` expressions |
| Rule-based | Partial | Simple filter rules converted; nested/complex rules fall back to default style |
| Heatmap | Fallback | Rendered as simple circles with default style |
| Point Cluster | Fallback | Rendered as simple circles with default style |
| Labels | Partial | Text field, font family, size, and halo extracted; complex label expressions may simplify |

**Unsupported symbol layer types** (e.g., SVG markers, geometry generators) fall back to a simple geometry-appropriate default style.

**Unit conversion**: QGIS millimetre sizes are converted to pixels at 96 DPI (1 mm ≈ 3.78 px).

## Style Editing with Maputnik

1. Export with **Export style.json** checked
2. Open [Maputnik](https://maputnik.github.io/)
3. Click **Open > Upload** and select your `style.json`
4. Edit colors, widths, opacity, etc.
5. Click **Export > Download** to save the edited file
6. In MapSplat, use **Import style.json** to apply edits to future exports

## Troubleshooting

### Map is blank / tiles don't load

1. Open the browser console (F12 → Console) and look for errors
2. Confirm you are using `serve.py` or a proper web server — not `file://`
3. Verify `data/layers.pmtiles` exists and is not 0 bytes
4. If using basemap overlay, verify `data/basemap.pmtiles` also exists

### Culvert / POI icons missing in basemap overlay mode

Ensure you are on MapSplat v0.5.5 or later. Earlier versions passed `style.json` as a URL string to MapLibre, which prevented icon layers from rendering when two PMTiles sources were present. v0.5.5 fetches `style.json` at runtime and passes the parsed object, which resolves the issue.

### "ogr2ogr not found"

GDAL 3.8+ is required. Check your version:
```bash
ogr2ogr --version
```

On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install gdal-bin
```

### "pmtiles CLI not found" (basemap overlay)

Download the `pmtiles` binary from [go-pmtiles releases](https://github.com/protomaps/go-pmtiles/releases) and place it on your PATH:
```bash
# Example for Linux x86_64
wget https://github.com/protomaps/go-pmtiles/releases/latest/download/go-pmtiles_Linux_x86_64.tar.gz
tar xf go-pmtiles_Linux_x86_64.tar.gz
sudo mv pmtiles /usr/local/bin/
pmtiles --version
```

### Style not applied / wrong colors

Verify that layer names in `style.json` match the source-layer names in the PMTiles file. Use the [PMTiles Viewer](https://pmtiles.io/) to inspect your file.

## Development

### Building

```bash
cd Plugins/mapsplat

# Compile resources (after editing resources.qrc)
make compile

# Deploy to QGIS default profile
make deploy

# Create distribution ZIP
make package

# Run tests
make test
```

### Project Structure

```
mapsplat/
├── __init__.py              # Plugin entry point
├── mapsplat.py              # Plugin lifecycle (toolbar, menu, dockwidget)
├── mapsplat_dockwidget.py   # All UI; validates settings, fires export
├── exporter.py              # Orchestrates the full export workflow
├── style_converter.py       # QGIS renderer → MapLibre Style JSON
├── metadata.txt             # Plugin metadata (version, changelog)
├── Makefile                 # Build automation
├── docs/
│   ├── CHANGELOG.md
│   ├── PLAN.md
│   ├── REQUIREMENTS.md
│   └── TODO.md
└── test/                    # Unit tests (pure-Python helpers only)
```

### Architecture Notes

- `exporter.py` exports layers via `QgsVectorFileWriter` → GeoPackage, then calls `ogr2ogr` to convert to PMTiles
- `style_converter.py` walks QGIS renderers and builds MapLibre Style JSON v8; unit conversion constant `MM_TO_PX = 3.78`
- The generated `index.html` fetches `style.json` at runtime (not via URL string) to ensure MapLibre correctly resolves `pmtiles://` source URLs
- Basemap overlay uses the `pmtiles extract` CLI command via `QProcess`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes following the project versioning rules (bump `__version__` in all five `.py` files and `metadata.txt`, update `docs/CHANGELOG.md`)
4. Push and open a Pull Request

See [TODO.md](docs/TODO.md) for planned features and known issues.

## License

MIT License — see [LICENSE](../../LICENSE) for details.

## Credits

- [MapLibre GL JS](https://maplibre.org/) — Open-source map rendering
- [PMTiles](https://protomaps.com/docs/pmtiles) — Single-file tile archives
- [Protomaps Basemaps](https://github.com/protomaps/basemaps) — Open basemap tiles and styles
- [Maputnik](https://maputnik.github.io/) — Visual style editor
- [QGIS](https://qgis.org/) — Geographic Information System

## Links

- **Repository**: https://github.com/johnzastrow/mqs
- **Issues**: https://github.com/johnzastrow/mqs/issues
- **Documentation**: [docs/](docs/)
