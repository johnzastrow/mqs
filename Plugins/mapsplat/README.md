# MapSplat

**Export QGIS projects to static web maps using PMTiles and MapLibre GL JS**

[![QGIS](https://img.shields.io/badge/QGIS-3.40%2B-green.svg)](https://qgis.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.4-orange.svg)](docs/CHANGELOG.md)

MapSplat is a QGIS plugin that exports your project layers to self-contained web map packages. The output can be hosted on any static web server, cloud storage, or CDN - no tile server required.

## Features

- **Vector Export**: Export vector layers to PMTiles format
- **Automatic Styling**: Convert QGIS symbology to MapLibre GL styles
- **Offline Capable**: Self-contained viewer with bundled MapLibre GL JS
- **Style Roundtripping**: Export/import style.json for editing in Maputnik
- **Auto-Reprojection**: Automatic transformation to Web Mercator (EPSG:3857)
- **Interactive Viewer**: Click-to-identify popups, zoom controls, navigation
- **Qt6 Compatible**: Works with QGIS 3.x (Qt5) and QGIS 4.x (Qt6)

## Requirements

| Requirement | Version |
|-------------|---------|
| QGIS | 3.40+ (also compatible with 4.0 beta) |
| GDAL | 3.8+ (for native PMTiles support) |
| Python | 3.9+ (bundled with QGIS) |

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/johnzastrow/mqs.git
cd mqs/Plugins/mapsplat

# Deploy to QGIS plugins directory
make deploy

# Restart QGIS and enable the plugin
```

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
   - **Export style.json**: Check to save editable style file
5. Set output folder and project name
6. Click **Export Web Map**

### Output Structure

```
myproject_webmap/
├── index.html              # Interactive web map viewer
├── style.json              # MapLibre style (if exported)
├── data/
│   └── layers.pmtiles      # Vector tile data
├── lib/
│   ├── maplibre-gl.js      # MapLibre GL JS library
│   ├── maplibre-gl.css     # MapLibre styles
│   └── pmtiles.js          # PMTiles protocol handler
└── README.txt              # Deployment instructions
```

## Deployment

The generated web map can be deployed to any platform that supports static file hosting with HTTP Range Requests.

### Quick Deployment Options

#### GitHub Pages

```bash
# In your output folder
git init
git add .
git commit -m "Initial web map"
git branch -M main
git remote add origin https://github.com/username/my-webmap.git
git push -u origin main

# Enable GitHub Pages in repository settings
```

#### Netlify / Vercel

Simply drag and drop the output folder to the Netlify/Vercel dashboard, or connect your repository.

#### AWS S3

```bash
# Upload to S3 bucket
aws s3 sync myproject_webmap/ s3://my-bucket/webmap/ --acl public-read

# Configure CORS (see below)
```

#### Simple Web Server (nginx)

```bash
# Copy files to web root
sudo cp -r myproject_webmap/* /var/www/html/webmap/
```

### CORS Configuration

If hosting PMTiles on a different domain than your HTML, configure CORS:

#### nginx

```nginx
location ~* \.pmtiles$ {
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, HEAD, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Range' always;
    add_header 'Access-Control-Expose-Headers' 'Content-Length, Content-Range' always;
}
```

#### Apache (.htaccess)

```apache
<FilesMatch "\.pmtiles$">
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, HEAD, OPTIONS"
    Header set Access-Control-Allow-Headers "Range"
    Header set Access-Control-Expose-Headers "Content-Length, Content-Range"
</FilesMatch>
```

#### AWS S3 CORS Policy

```json
[
    {
        "AllowedOrigins": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedHeaders": ["Range"],
        "ExposeHeaders": ["Content-Range", "Content-Length", "ETag"],
        "MaxAgeSeconds": 3600
    }
]
```

### Offline Viewing

For fully offline operation, ensure the `lib/` folder contains:
- `maplibre-gl.js`
- `maplibre-gl.css`
- `pmtiles.js`

Download from:
- https://unpkg.com/maplibre-gl/dist/maplibre-gl.js
- https://unpkg.com/maplibre-gl/dist/maplibre-gl.css
- https://unpkg.com/pmtiles/dist/pmtiles.js

## Supported Symbology

| QGIS Renderer | MapSplat Support | Notes |
|---------------|------------------|-------|
| Single Symbol | Full | Fill, line, and circle types |
| Categorized | Full | Match expressions |
| Graduated | Full | Step expressions |
| Rule-based | Fallback | Uses default style |
| Heatmap | Fallback | Uses default style |
| Labels | Not yet | Planned for future |

Unsupported renderers fall back to a simple default style with appropriate geometry type.

## Style Editing with Maputnik

1. Export with "Export separate style.json" checked
2. Open [Maputnik](https://maputnik.github.io/)
3. Click **Open** > **Upload** and select your `style.json`
4. Edit colors, line widths, opacity, etc.
5. Click **Export** > **Download** to save changes
6. In MapSplat, use **Import style.json** to apply edits to future exports

## Troubleshooting

### "ogr2ogr not found"

GDAL 3.8+ is required for PMTiles support. Check your version:

```bash
ogr2ogr --version
```

On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install gdal-bin
```

### Blank map in viewer

1. Check browser console for errors (F12 > Console)
2. Verify PMTiles file exists in `data/` folder
3. Check that `lib/` contains MapLibre files
4. Ensure CORS is configured if hosting on different domain

### Style not applied

Verify layer names in `style.json` match source-layer names in PMTiles. Use [PMTiles Viewer](https://pmtiles.io/) to inspect your file.

## Development

### Building

```bash
cd Plugins/mapsplat

# Compile resources (if modified)
make compile

# Deploy to QGIS
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
├── mapsplat.py              # Main plugin class
├── mapsplat_dockwidget.py   # UI widget
├── exporter.py              # Export logic
├── style_converter.py       # QGIS → MapLibre style conversion
├── metadata.txt             # Plugin metadata
├── Makefile                 # Build automation
├── docs/                    # Documentation
│   ├── CHANGELOG.md
│   ├── PLAN.md
│   ├── REQUIREMENTS.md
│   └── TODO.md
└── test/                    # Unit tests
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [TODO.md](docs/TODO.md) for planned features and known issues.

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Credits

- [MapLibre GL JS](https://maplibre.org/) - Open-source map rendering
- [PMTiles](https://protomaps.com/docs/pmtiles) - Single-file tile archives
- [Maputnik](https://maputnik.github.io/) - Visual style editor
- [QGIS](https://qgis.org/) - Geographic Information System

## Links

- **Repository**: https://github.com/johnzastrow/mqs
- **Issues**: https://github.com/johnzastrow/mqs/issues
- **Documentation**: [docs/](docs/)
