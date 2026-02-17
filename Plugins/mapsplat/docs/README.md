# MapSplat

**Export QGIS projects to static web maps**

MapSplat is a QGIS plugin that exports your project layers to self-contained web map packages using PMTiles format and MapLibre GL JS for rendering.

## Features

- Export vector layers to PMTiles format
- Automatic symbology conversion to MapLibre styles
- Self-contained offline viewer (no CDN required)
- Style roundtripping with Maputnik editor
- Auto-reprojection to Web Mercator (EPSG:3857)
- Click-to-identify feature popups

## Requirements

- QGIS 3.40 or later
- GDAL 3.8 or later (for native PMTiles support)

## Installation

### From ZIP

1. Download the latest `mapsplat.zip` from releases
2. In QGIS, go to **Plugins > Manage and Install Plugins > Install from ZIP**
3. Select the downloaded ZIP file
4. Enable the plugin

### From Source

```bash
cd Plugins/mapsplat
make deploy
```

## Usage

1. Open a QGIS project with vector layers
2. Click the **MapSplat** button in the toolbar (or **Web > MapSplat**)
3. Select layers to export
4. Choose export options:
   - Single PMTiles file or separate files per layer
   - Export separate style.json for editing in Maputnik
5. Select output folder and project name
6. Click **Export Web Map**

## Output Structure

```
myproject_webmap/
├── index.html          # Web map viewer
├── style.json          # MapLibre style (optional)
├── data/
│   └── layers.pmtiles  # Vector tile data
├── lib/
│   └── maplibre-gl.*   # MapLibre assets
└── README.txt          # Deployment instructions
```

## Deployment

The output folder can be deployed to:

- Any static web server (nginx, Apache, Caddy)
- Cloud storage (AWS S3, Cloudflare R2, Google Cloud Storage)
- GitHub Pages
- Netlify, Vercel, etc.

The only requirement is HTTP Range Request support (standard on most servers).

## Supported Symbology

| Renderer Type | Support |
|---------------|---------|
| Single Symbol | Full |
| Categorized | Full |
| Graduated | Full |
| Rule-based | Fallback |
| Labels | Not yet |

Unsupported renderers fall back to a simple default style.

## Style Editing

Export a `style.json` file and edit it in [Maputnik](https://maputnik.github.io/):

1. Open Maputnik
2. Load your style.json
3. Edit colors, line widths, etc.
4. Export and reimport into MapSplat

## License

MIT License - see LICENSE file

## Contributing

Issues and pull requests welcome at:
https://github.com/johnzastrow/mqs
