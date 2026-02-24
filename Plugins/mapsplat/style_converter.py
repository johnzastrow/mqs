"""
MapSplat - Style Converter Module

This module converts QGIS layer styles to MapLibre GL Style JSON format.

Supported renderers:
- Single Symbol (fill, line, marker)
- Categorized
- Graduated
- Rule-based

Supported style properties:
- Fill/stroke colors and opacity
- Line width, dash patterns, cap/join styles
- Marker size, color, stroke
- Labels (text field, font, size, color, halo, placement)
- Multiple symbol layers
"""

__version__ = "0.6.2"

import os
from qgis.core import (
    QgsVectorLayer,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer,
    QgsSymbol,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
    QgsSvgMarkerSymbolLayer,
    QgsFontMarkerSymbolLayer,
    QgsLinePatternFillSymbolLayer,
    QgsPointPatternFillSymbolLayer,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsUnitTypes,
    Qgis,
)

# Try to import labeling classes (may vary by QGIS version)
try:
    from qgis.core import QgsVectorLayerSimpleLabeling
except ImportError:
    QgsVectorLayerSimpleLabeling = None


class StyleConverter:
    """Converts QGIS styles to MapLibre style JSON."""

    # Default colors for fallback
    DEFAULT_FILL_COLOR = "#3388ff"
    DEFAULT_LINE_COLOR = "#333333"
    DEFAULT_POINT_COLOR = "#ff6600"
    DEFAULT_TEXT_COLOR = "#000000"
    DEFAULT_HALO_COLOR = "#ffffff"

    # Unit conversion (mm to pixels at 96 DPI)
    MM_TO_PX = 3.78

    def __init__(self, layers, settings, log_callback=None):
        """Initialize converter.

        :param layers: List of QgsVectorLayer
        :param settings: Export settings dictionary
        :param log_callback: Optional callable(message: str) for logging during sprite generation
        """
        self.layers = layers
        self.settings = settings
        self._layer_counter = {}
        self._log_callback = log_callback
        self._svg_sprite_map = {}  # populated by _generate_sprites(); {source_layer: sprite_key}

    def _log(self, message):
        """Emit a log message via callback if one was provided."""
        if self._log_callback:
            self._log_callback(message)

    def convert(self, single_file=True, output_dir=None):
        """Convert all layers to MapLibre style JSON.

        :param single_file: If True, all layers share one PMTiles source.
                           If False, each layer has its own PMTiles file.
        :param output_dir: If provided, SVG single-symbol point layers are rendered
                           to a sprite atlas (sprites.png + sprites.json) in this
                           directory and the style gets a "sprite" key.
        :returns: Style JSON dictionary
        """
        self._single_file = single_file

        self._svg_sprite_map = {}  # reset for each convert() call

        # Pre-generate sprites for SVG single-symbol point layers
        has_sprites = False
        if output_dir:
            try:
                has_sprites = self._generate_sprites(output_dir)
            except Exception as e:
                self._log(f"Sprite generation skipped: {e}")

        if single_file:
            sources = {
                "mapsplat": {
                    "type": "vector",
                    "url": "pmtiles://data/layers.pmtiles"
                }
            }
        else:
            sources = {}
            for layer in self.layers:
                source_name = self._sanitize_name(layer.name())
                sources[source_name] = {
                    "type": "vector",
                    "url": f"pmtiles://data/{source_name}.pmtiles"
                }

        style = {
            "version": 8,
            "name": self.settings.get("project_name", "MapSplat Export"),
            "sources": sources,
            "glyphs": "https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf",
            "layers": [
                {
                    "id": "background",
                    "type": "background",
                    "paint": {
                        "background-color": "#f8f9fa"
                    }
                }
            ]
        }

        if has_sprites:
            style["sprite"] = "./sprites"

        # Convert each layer
        for layer in self.layers:
            layer_styles = self._convert_layer(layer)
            style["layers"].extend(layer_styles)

            # Add labels if enabled
            label_layer = self._convert_labels(layer)
            if label_layer:
                style["layers"].append(label_layer)

        return style

    def _convert_layer(self, layer):
        """Convert a single layer to MapLibre layer definitions.

        :param layer: QgsVectorLayer
        :returns: List of MapLibre layer dictionaries
        """
        renderer = layer.renderer()
        source_layer = self._sanitize_name(layer.name())
        geom_type = layer.geometryType()

        if self._single_file:
            source_name = "mapsplat"
        else:
            source_name = source_layer

        # Reset layer counter for this source layer
        self._layer_counter[source_layer] = 0

        # Dispatch based on renderer type
        if isinstance(renderer, QgsSingleSymbolRenderer):
            return self._convert_single_symbol(layer, renderer, source_layer, geom_type, source_name)
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            return self._convert_categorized(layer, renderer, source_layer, geom_type, source_name)
        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            return self._convert_graduated(layer, renderer, source_layer, geom_type, source_name)
        elif isinstance(renderer, QgsRuleBasedRenderer):
            return self._convert_rule_based(layer, renderer, source_layer, geom_type, source_name)
        else:
            return self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_labels(self, layer):
        """Convert layer labels to MapLibre symbol layer.

        :param layer: QgsVectorLayer
        :returns: MapLibre layer dictionary or None
        """
        if not layer.labelsEnabled():
            return None

        labeling = layer.labeling()
        if labeling is None:
            return None

        source_layer = self._sanitize_name(layer.name())
        source_name = "mapsplat" if self._single_file else source_layer

        # Get label settings
        try:
            if QgsVectorLayerSimpleLabeling and isinstance(labeling, QgsVectorLayerSimpleLabeling):
                settings = labeling.settings()
            else:
                # Try to get settings from provider
                settings = labeling.settings()
        except Exception:
            return None

        if settings is None:
            return None

        # Extract text field
        field_name = settings.fieldName
        if not field_name:
            return None

        # Clean up field name (remove quotes if present)
        clean_field = field_name.strip().replace('"', '').replace("'", "")

        # Check if it's an expression or field name
        if settings.isExpression:
            # For expressions, try to extract field name or use as-is
            # Simple case: just a field name in quotes
            text_field = ["to-string", ["get", clean_field]]
        else:
            # Use format string for simple field reference
            text_field = ["to-string", ["get", clean_field]]

        # Extract text format
        text_format = settings.format()

        # Font settings
        font_family = text_format.font().family()
        font_size = self._convert_size(text_format.size(), text_format.sizeUnit())
        if font_size < 8:
            font_size = 12  # Default to reasonable size
        text_color = text_format.color().name()

        # Halo/buffer settings
        buffer_settings = text_format.buffer()
        halo_color = self.DEFAULT_HALO_COLOR
        halo_width = 1  # Default small halo for readability
        if buffer_settings.enabled():
            halo_color = buffer_settings.color().name()
            halo_width = max(1, self._convert_size(buffer_settings.size(), buffer_settings.sizeUnit()))

        # Build the symbol layer
        label_layer = {
            "id": f"{source_layer}_labels",
            "type": "symbol",
            "source": source_name,
            "source-layer": source_layer,
            "layout": {
                "visibility": "visible",
                "text-field": text_field,
                "text-font": ["Noto Sans Regular"],
                "text-size": font_size,
                "text-anchor": "center",
                "text-justify": "center",
                "text-allow-overlap": False,
                "text-ignore-placement": False,
                "text-optional": True,
                "text-padding": 2,
            },
            "paint": {
                "text-color": text_color,
                "text-halo-color": halo_color,
                "text-halo-width": halo_width,
            }
        }

        # Placement based on geometry type
        geom_type = layer.geometryType()
        if geom_type == 1:  # Line
            label_layer["layout"]["symbol-placement"] = "line"
            label_layer["layout"]["text-rotation-alignment"] = "map"
            label_layer["layout"]["symbol-spacing"] = 250
        elif geom_type == 2:  # Polygon
            label_layer["layout"]["symbol-placement"] = "point"
        elif geom_type == 0:  # Point
            label_layer["layout"]["text-offset"] = [0, 1.5]
            label_layer["layout"]["text-anchor"] = "top"

        return label_layer

    def _convert_single_symbol(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert single symbol renderer with all symbol layers."""
        symbol = renderer.symbol()
        return self._symbol_to_layers(symbol, source_layer, source_layer, geom_type, source_name)

    def _symbol_to_layers(self, symbol, layer_id_base, source_layer, geom_type, source_name, filter_expr=None):
        """Convert a symbol (potentially with multiple symbol layers) to MapLibre layers.

        :param symbol: QgsSymbol
        :param layer_id_base: Base ID for the layer
        :param source_layer: Source layer name in PMTiles
        :param geom_type: Geometry type (0=point, 1=line, 2=polygon)
        :param source_name: PMTiles source name
        :param filter_expr: Optional MapLibre filter expression
        :returns: List of MapLibre layer dictionaries
        """
        layers = []

        if symbol is None:
            return self._create_default_style(None, source_layer, geom_type, source_name)

        # Process each symbol layer (bottom to top)
        for i in range(symbol.symbolLayerCount()):
            sym_layer = symbol.symbolLayer(i)

            # Generate unique layer ID
            self._layer_counter[source_layer] = self._layer_counter.get(source_layer, 0) + 1
            count = self._layer_counter[source_layer]
            layer_id = f"{layer_id_base}" if count == 1 else f"{layer_id_base}_{count}"

            ml_layer = None

            if geom_type == 2:  # Polygon
                ml_layer = self._fill_symbol_layer_to_maplibre(sym_layer, layer_id, source_layer, source_name)
            elif geom_type == 1:  # Line
                ml_layer = self._line_symbol_layer_to_maplibre(sym_layer, layer_id, source_layer, source_name)
            elif geom_type == 0:  # Point
                ml_layer = self._marker_symbol_layer_to_maplibre(sym_layer, layer_id, source_layer, source_name)

            if ml_layer:
                if filter_expr:
                    ml_layer["filter"] = filter_expr
                layers.append(ml_layer)

        return layers if layers else self._create_default_style(None, source_layer, geom_type, source_name)

    def _fill_symbol_layer_to_maplibre(self, sym_layer, layer_id, source_layer, source_name):
        """Convert a fill symbol layer to MapLibre layer."""
        if isinstance(sym_layer, QgsSimpleFillSymbolLayer):
            fill_color = sym_layer.fillColor()
            stroke_color = sym_layer.strokeColor()
            stroke_width = self._convert_size(sym_layer.strokeWidth(), sym_layer.strokeWidthUnit())

            # Extract opacity
            fill_opacity = fill_color.alphaF()
            stroke_opacity = stroke_color.alphaF()

            result = {
                "id": layer_id,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": fill_color.name(),
                    "fill-opacity": fill_opacity,
                }
            }

            # Add outline as separate line layer if stroke is visible
            if stroke_width > 0 and stroke_opacity > 0:
                result["paint"]["fill-outline-color"] = stroke_color.name()

            return result

        # Pattern fills - note as comment, limited MapLibre support
        elif isinstance(sym_layer, (QgsLinePatternFillSymbolLayer, QgsPointPatternFillSymbolLayer)):
            # Patterns need image sprites - use solid color fallback
            return {
                "id": layer_id,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": self.DEFAULT_FILL_COLOR,
                    "fill-opacity": 0.5,
                }
            }

        return None

    def _line_symbol_layer_to_maplibre(self, sym_layer, layer_id, source_layer, source_name):
        """Convert a line symbol layer to MapLibre layer."""
        if isinstance(sym_layer, QgsSimpleLineSymbolLayer):
            color = sym_layer.color()
            width = self._convert_size(sym_layer.width(), sym_layer.widthUnit())
            opacity = color.alphaF()

            result = {
                "id": layer_id,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": color.name(),
                    "line-width": max(0.5, width),
                    "line-opacity": opacity,
                }
            }

            # Line cap
            pen_cap = sym_layer.penCapStyle()
            cap_map = {0: "flat", 1: "square", 2: "round"}  # Qt.FlatCap, SquareCap, RoundCap
            if pen_cap in cap_map:
                result["layout"] = result.get("layout", {})
                result["layout"]["line-cap"] = cap_map[pen_cap]

            # Line join
            pen_join = sym_layer.penJoinStyle()
            join_map = {0: "miter", 1: "bevel", 2: "round"}  # Qt.MiterJoin, BevelJoin, RoundJoin
            if pen_join in join_map:
                result["layout"] = result.get("layout", {})
                result["layout"]["line-join"] = join_map[pen_join]

            # Dash pattern
            if sym_layer.useCustomDashPattern():
                dash_vector = sym_layer.customDashVector()
                if dash_vector:
                    # Convert from mm to pixels, normalize to line width
                    dash_array = [self._convert_size(d, sym_layer.customDashPatternUnit()) for d in dash_vector]
                    if dash_array and all(d > 0 for d in dash_array):
                        result["paint"]["line-dasharray"] = dash_array

            return result

        return None

    def _marker_symbol_layer_to_maplibre(self, sym_layer, layer_id, source_layer, source_name):
        """Convert a marker symbol layer to MapLibre layer."""
        if isinstance(sym_layer, QgsSimpleMarkerSymbolLayer):
            fill_color = sym_layer.fillColor()
            stroke_color = sym_layer.strokeColor()
            size = self._convert_size(sym_layer.size(), sym_layer.sizeUnit())
            stroke_width = self._convert_size(sym_layer.strokeWidth(), sym_layer.strokeWidthUnit())

            fill_opacity = fill_color.alphaF()
            stroke_opacity = stroke_color.alphaF()

            return {
                "id": layer_id,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": fill_color.name(),
                    "circle-opacity": fill_opacity,
                    "circle-radius": max(2, size / 2),  # Size is diameter, radius for MapLibre
                    "circle-stroke-color": stroke_color.name(),
                    "circle-stroke-width": stroke_width,
                    "circle-stroke-opacity": stroke_opacity,
                }
            }

        elif isinstance(sym_layer, QgsSvgMarkerSymbolLayer):
            sprite_key = self._svg_sprite_map.get(source_layer)
            size = self._convert_size(sym_layer.size(), sym_layer.sizeUnit())
            if sprite_key:
                # Single-symbol SVG with a pre-rendered sprite — emit symbol layer
                return self._build_symbol_layer_for_sprite(
                    layer_id, sprite_key, source_name, source_layer, size
                )
            # Categorized/graduated SVG, or sprite generation not run — circle fallback
            fill_color = sym_layer.fillColor() if hasattr(sym_layer, 'fillColor') else None
            return {
                "id": layer_id,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": fill_color.name() if fill_color else self.DEFAULT_POINT_COLOR,
                    "circle-radius": max(2, size / 2),
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1,
                },
            }

        elif isinstance(sym_layer, QgsFontMarkerSymbolLayer):
            # Font markers - use circle fallback
            color = sym_layer.color()
            size = self._convert_size(sym_layer.size(), sym_layer.sizeUnit())

            return {
                "id": layer_id,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": color.name(),
                    "circle-radius": max(2, size / 2),
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1,
                }
            }

        return None

    def _build_symbol_layer_for_sprite(self, layer_id, sprite_key, source_name, source_layer, size_px):
        """Build a MapLibre symbol layer referencing a pre-rendered sprite entry.

        :param layer_id: MapLibre layer ID string
        :param sprite_key: Key in the sprite manifest (sprites.json)
        :param source_name: PMTiles source name in the style
        :param source_layer: Source-layer name in PMTiles
        :param size_px: Original icon size in pixels (reserved for future icon-size scaling)
        :returns: MapLibre layer dict with type "symbol"
        """
        return {
            "id": layer_id,
            "type": "symbol",
            "source": source_name,
            "source-layer": source_layer,
            "layout": {
                "icon-image": sprite_key,
                "icon-size": 1.0,
                "icon-allow-overlap": True,
                "icon-ignore-placement": True,
            },
        }


    def _convert_categorized(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert categorized symbol renderer."""
        layers = []
        attr_name = renderer.classAttribute()
        categories = renderer.categories()

        if geom_type == 2:  # Polygon
            fill_colors = ["match", ["get", attr_name]]
            outline_colors = ["match", ["get", attr_name]]
            opacities = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                if value is not None and value != "" and symbol and symbol.symbolLayerCount() > 0:
                    sym_layer = symbol.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleFillSymbolLayer):
                        fill_colors.extend([value, sym_layer.fillColor().name()])
                        outline_colors.extend([value, sym_layer.strokeColor().name()])
                        opacities.extend([value, sym_layer.fillColor().alphaF()])

            fill_colors.append(self.DEFAULT_FILL_COLOR)
            outline_colors.append(self.DEFAULT_LINE_COLOR)
            opacities.append(0.7)

            layers.append({
                "id": source_layer,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": fill_colors,
                    "fill-opacity": opacities,
                    "fill-outline-color": outline_colors
                }
            })

        elif geom_type == 1:  # Line
            line_colors = ["match", ["get", attr_name]]
            line_widths = ["match", ["get", attr_name]]
            opacities = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                if value is not None and value != "" and symbol and symbol.symbolLayerCount() > 0:
                    sym_layer = symbol.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleLineSymbolLayer):
                        line_colors.extend([value, sym_layer.color().name()])
                        line_widths.extend([value, self._convert_size(sym_layer.width(), sym_layer.widthUnit())])
                        opacities.extend([value, sym_layer.color().alphaF()])

            line_colors.append(self.DEFAULT_LINE_COLOR)
            line_widths.append(2)
            opacities.append(1.0)

            layers.append({
                "id": source_layer,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": line_colors,
                    "line-width": line_widths,
                    "line-opacity": opacities,
                }
            })

        elif geom_type == 0:  # Point
            circle_colors = ["match", ["get", attr_name]]
            circle_radii = ["match", ["get", attr_name]]
            stroke_colors = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                if value is not None and value != "" and symbol and symbol.symbolLayerCount() > 0:
                    sym_layer = symbol.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleMarkerSymbolLayer):
                        circle_colors.extend([value, sym_layer.fillColor().name()])
                        circle_radii.extend([value, self._convert_size(sym_layer.size(), sym_layer.sizeUnit()) / 2])
                        stroke_colors.extend([value, sym_layer.strokeColor().name()])

            circle_colors.append(self.DEFAULT_POINT_COLOR)
            circle_radii.append(6)
            stroke_colors.append("#ffffff")

            layers.append({
                "id": source_layer,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": circle_colors,
                    "circle-radius": circle_radii,
                    "circle-stroke-color": stroke_colors,
                    "circle-stroke-width": 1
                }
            })

        return layers if layers else self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_graduated(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert graduated symbol renderer."""
        layers = []
        attr_name = renderer.classAttribute()
        ranges = renderer.ranges()

        if not ranges:
            return self._create_default_style(layer, source_layer, geom_type, source_name)

        if geom_type == 2:  # Polygon
            # Use interpolate for smoother gradients
            fill_expr = ["step", ["get", attr_name]]
            opacity_expr = ["step", ["get", attr_name]]

            first_sym = ranges[0].symbol()
            if first_sym and first_sym.symbolLayerCount() > 0:
                first_layer = first_sym.symbolLayer(0)
                if isinstance(first_layer, QgsSimpleFillSymbolLayer):
                    fill_expr.append(first_layer.fillColor().name())
                    opacity_expr.append(first_layer.fillColor().alphaF())
                else:
                    fill_expr.append(self.DEFAULT_FILL_COLOR)
                    opacity_expr.append(0.7)
            else:
                fill_expr.append(self.DEFAULT_FILL_COLOR)
                opacity_expr.append(0.7)

            for r in ranges:
                sym = r.symbol()
                if sym and sym.symbolLayerCount() > 0:
                    sym_layer = sym.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleFillSymbolLayer):
                        fill_expr.extend([r.lowerValue(), sym_layer.fillColor().name()])
                        opacity_expr.extend([r.lowerValue(), sym_layer.fillColor().alphaF()])

            layers.append({
                "id": source_layer,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": fill_expr,
                    "fill-opacity": opacity_expr,
                    "fill-outline-color": "#333333"
                }
            })

        elif geom_type == 1:  # Line
            line_expr = ["step", ["get", attr_name]]
            width_expr = ["step", ["get", attr_name]]

            first_sym = ranges[0].symbol()
            if first_sym and first_sym.symbolLayerCount() > 0:
                first_layer = first_sym.symbolLayer(0)
                if isinstance(first_layer, QgsSimpleLineSymbolLayer):
                    line_expr.append(first_layer.color().name())
                    width_expr.append(self._convert_size(first_layer.width(), first_layer.widthUnit()))
                else:
                    line_expr.append(self.DEFAULT_LINE_COLOR)
                    width_expr.append(2)
            else:
                line_expr.append(self.DEFAULT_LINE_COLOR)
                width_expr.append(2)

            for r in ranges:
                sym = r.symbol()
                if sym and sym.symbolLayerCount() > 0:
                    sym_layer = sym.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleLineSymbolLayer):
                        line_expr.extend([r.lowerValue(), sym_layer.color().name()])
                        width_expr.extend([r.lowerValue(), self._convert_size(sym_layer.width(), sym_layer.widthUnit())])

            layers.append({
                "id": source_layer,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": line_expr,
                    "line-width": width_expr
                }
            })

        elif geom_type == 0:  # Point
            color_expr = ["step", ["get", attr_name]]
            radius_expr = ["step", ["get", attr_name]]

            first_sym = ranges[0].symbol()
            if first_sym and first_sym.symbolLayerCount() > 0:
                first_layer = first_sym.symbolLayer(0)
                if isinstance(first_layer, QgsSimpleMarkerSymbolLayer):
                    color_expr.append(first_layer.fillColor().name())
                    radius_expr.append(self._convert_size(first_layer.size(), first_layer.sizeUnit()) / 2)
                else:
                    color_expr.append(self.DEFAULT_POINT_COLOR)
                    radius_expr.append(6)
            else:
                color_expr.append(self.DEFAULT_POINT_COLOR)
                radius_expr.append(6)

            for r in ranges:
                sym = r.symbol()
                if sym and sym.symbolLayerCount() > 0:
                    sym_layer = sym.symbolLayer(0)
                    if isinstance(sym_layer, QgsSimpleMarkerSymbolLayer):
                        color_expr.extend([r.lowerValue(), sym_layer.fillColor().name()])
                        radius_expr.extend([r.lowerValue(), self._convert_size(sym_layer.size(), sym_layer.sizeUnit()) / 2])

            layers.append({
                "id": source_layer,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": color_expr,
                    "circle-radius": radius_expr,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1
                }
            })

        return layers if layers else self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_rule_based(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert rule-based renderer to multiple filtered layers."""
        layers = []
        root_rule = renderer.rootRule()

        self._process_rule(root_rule, layers, source_layer, geom_type, source_name, 0)

        return layers if layers else self._create_default_style(layer, source_layer, geom_type, source_name)

    def _process_rule(self, rule, layers, source_layer, geom_type, source_name, depth):
        """Recursively process rule-based renderer rules."""
        # Process this rule if it has a symbol
        if rule.symbol():
            filter_expr = self._convert_qgis_expression_to_maplibre(rule.filterExpression())
            rule_layers = self._symbol_to_layers(
                rule.symbol(),
                f"{source_layer}_rule{len(layers)}",
                source_layer,
                geom_type,
                source_name,
                filter_expr
            )
            layers.extend(rule_layers)

        # Process child rules
        for child in rule.children():
            if child.active():
                self._process_rule(child, layers, source_layer, geom_type, source_name, depth + 1)

    def _convert_qgis_expression_to_maplibre(self, expr_str):
        """Convert a QGIS filter expression to MapLibre filter.

        :param expr_str: QGIS expression string
        :returns: MapLibre filter array or None
        """
        if not expr_str or expr_str.strip() == "":
            return None

        expr_str = expr_str.strip()

        # Simple equality: "field" = 'value' or "field" = value
        import re

        # Pattern for: "field" = 'value'
        match = re.match(r'"([^"]+)"\s*=\s*\'([^\']+)\'', expr_str)
        if match:
            return ["==", ["get", match.group(1)], match.group(2)]

        # Pattern for: "field" = number
        match = re.match(r'"([^"]+)"\s*=\s*(-?\d+\.?\d*)', expr_str)
        if match:
            return ["==", ["get", match.group(1)], float(match.group(2))]

        # Pattern for: "field" > number
        match = re.match(r'"([^"]+)"\s*>\s*(-?\d+\.?\d*)', expr_str)
        if match:
            return [">", ["get", match.group(1)], float(match.group(2))]

        # Pattern for: "field" < number
        match = re.match(r'"([^"]+)"\s*<\s*(-?\d+\.?\d*)', expr_str)
        if match:
            return ["<", ["get", match.group(1)], float(match.group(2))]

        # Pattern for: "field" >= number
        match = re.match(r'"([^"]+)"\s*>=\s*(-?\d+\.?\d*)', expr_str)
        if match:
            return [">=", ["get", match.group(1)], float(match.group(2))]

        # Pattern for: "field" <= number
        match = re.match(r'"([^"]+)"\s*<=\s*(-?\d+\.?\d*)', expr_str)
        if match:
            return ["<=", ["get", match.group(1)], float(match.group(2))]

        # Pattern for: "field" != 'value'
        match = re.match(r'"([^"]+)"\s*!=\s*\'([^\']+)\'', expr_str)
        if match:
            return ["!=", ["get", match.group(1)], match.group(2)]

        # Pattern for: "field" IS NOT NULL
        match = re.match(r'"([^"]+)"\s+IS\s+NOT\s+NULL', expr_str, re.IGNORECASE)
        if match:
            return ["has", match.group(1)]

        # Pattern for: "field" IS NULL
        match = re.match(r'"([^"]+)"\s+IS\s+NULL', expr_str, re.IGNORECASE)
        if match:
            return ["!", ["has", match.group(1)]]

        # Complex expressions not yet supported - return None (no filter)
        return None

    def _create_default_style(self, layer, source_layer, geom_type, source_name):
        """Create default fallback style for unsupported renderers."""
        if geom_type == 2:  # Polygon
            return [{
                "id": source_layer,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": self.DEFAULT_FILL_COLOR,
                    "fill-opacity": 0.5,
                    "fill-outline-color": "#1a5276"
                }
            }]
        elif geom_type == 1:  # Line
            return [{
                "id": source_layer,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": self.DEFAULT_LINE_COLOR,
                    "line-width": 2
                }
            }]
        elif geom_type == 0:  # Point
            return [{
                "id": source_layer,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": self.DEFAULT_POINT_COLOR,
                    "circle-radius": 6,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1
                }
            }]

        return []

    def _convert_size(self, size, unit):
        """Convert a size value from QGIS units to pixels.

        :param size: Size value
        :param unit: QgsUnitTypes unit
        :returns: Size in pixels
        """
        if size is None:
            return 0

        # Handle different unit types
        try:
            if unit == QgsUnitTypes.RenderMillimeters:
                return size * self.MM_TO_PX
            elif unit == QgsUnitTypes.RenderPixels:
                return size
            elif unit == QgsUnitTypes.RenderPoints:
                return size * 1.33  # Points to pixels
            elif unit == QgsUnitTypes.RenderInches:
                return size * 96  # Inches to pixels at 96 DPI
            elif unit == QgsUnitTypes.RenderMapUnits:
                # Map units are tricky - use a rough approximation
                return size * 0.1
            else:
                return size * self.MM_TO_PX  # Default to mm
        except Exception:
            return size * self.MM_TO_PX

    def _sanitize_name(self, name):
        """Sanitize layer name for use as source-layer.

        :param name: Original name
        :returns: Sanitized name
        """
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        return sanitized.strip("_").lower()

    def _is_svg_single_symbol(self, layer):
        """Return True if a layer uses a single-symbol renderer with an SVG marker.

        :param layer: QgsVectorLayer
        :returns: bool
        """
        renderer = layer.renderer()
        if not isinstance(renderer, QgsSingleSymbolRenderer):
            return False
        symbol = renderer.symbol()
        if symbol is None or symbol.symbolLayerCount() == 0:
            return False
        return isinstance(symbol.symbolLayer(0), QgsSvgMarkerSymbolLayer)

    def _render_svg_to_qimage(self, svg_path, size_px, fill_color, stroke_color, stroke_width_px):
        """Rasterize an SVG marker via the QGIS SVG cache.

        :param svg_path: Absolute path to SVG file (or QGIS resource path)
        :param size_px: Output image dimension in pixels (square)
        :param fill_color: QColor for SVG fill
        :param stroke_color: QColor for SVG stroke
        :param stroke_width_px: Stroke width in pixels
        :returns: QImage on success, None on failure
        """
        try:
            from qgis.core import QgsApplication
            cache = QgsApplication.svgCache()

            def _call(stroke_w):
                result = cache.svgAsImage(
                    svg_path, float(size_px), fill_color, stroke_color, float(stroke_w), 1.0
                )
                # PyQGIS binding may return (QImage, bool) or just QImage depending on version
                if isinstance(result, tuple):
                    return result[0]
                return result

            img = _call(stroke_width_px)
            if img and not img.isNull():
                return img
            # Retry without color substitution (some SVGs ignore fill/stroke params)
            img = _call(0.0)
            return img if img and not img.isNull() else None
        except Exception as e:
            self._log(f"SVG render failed for '{svg_path}': {e}")
            return None

    def _generate_sprites(self, output_dir):
        """Render SVG single-symbol point layers to a sprite atlas.

        Writes sprites.png and sprites.json to output_dir.
        Populates self._svg_sprite_map with {source_layer_name: sprite_key} for
        each layer successfully rendered.

        :param output_dir: Directory to write sprite files (same level as index.html)
        :returns: True if at least one sprite was generated
        """
        import json as _json
        from qgis.PyQt.QtGui import QImage, QPainter
        from qgis.PyQt.QtCore import Qt

        images = {}
        images_2x = {}
        for layer in self.layers:
            if layer.geometryType() != 0:  # points only
                continue
            if not self._is_svg_single_symbol(layer):
                continue

            renderer = layer.renderer()
            symbol = renderer.symbol()
            sym_layer = symbol.symbolLayer(0)

            svg_path = sym_layer.path()
            size_px = max(16, int(self._convert_size(sym_layer.size(), sym_layer.sizeUnit())))
            fill_color = sym_layer.fillColor()
            stroke_color = sym_layer.strokeColor()
            stroke_width = self._convert_size(sym_layer.strokeWidth(), sym_layer.strokeWidthUnit())

            img = self._render_svg_to_qimage(svg_path, size_px, fill_color, stroke_color, stroke_width)
            img_2x = self._render_svg_to_qimage(svg_path, size_px * 2, fill_color, stroke_color, stroke_width)

            source_layer = self._sanitize_name(layer.name())
            if img and not img.isNull():
                images[source_layer] = img
                self._svg_sprite_map[source_layer] = source_layer
                self._log(f"Rendered sprite for '{layer.name()}' ({size_px}px)")
            else:
                self._log(
                    f"Warning: could not render SVG for '{layer.name()}', using circle fallback"
                )
            if img_2x and not img_2x.isNull():
                images_2x[source_layer] = img_2x

        if not images:
            return False

        # Compute atlas layout
        sizes = {name: (img.width(), img.height()) for name, img in images.items()}
        manifest, total_w, total_h = self._compute_sprite_layout(sizes)

        # Compose atlas image
        atlas = QImage(max(total_w, 1), max(total_h, 1), QImage.Format_ARGB32)
        if atlas.isNull():
            self._log("Warning: failed to allocate sprite atlas image")
            return False
        atlas.fill(Qt.transparent)
        painter = QPainter(atlas)
        for name, entry in manifest.items():
            painter.drawImage(entry["x"], entry["y"], images[name])
        painter.end()

        # Write sprites.png and sprites.json
        atlas_path = os.path.join(output_dir, "sprites.png")
        json_path = os.path.join(output_dir, "sprites.json")
        if not atlas.save(atlas_path):
            self._log(f"Warning: failed to write sprite atlas to '{atlas_path}'")
            return False
        with open(json_path, "w", encoding="utf-8") as f:
            _json.dump(manifest, f, indent=2)

        self._log(f"Wrote sprite atlas: {len(images)} icon(s) → {atlas_path}")

        # Write @2x sprite files — MapLibre 4.x on high-DPI displays requests these
        # first and does not fall back to 1x when they are missing.
        if images_2x:
            sizes_2x = {name: (img.width(), img.height()) for name, img in images_2x.items()}
            manifest_2x, total_w_2x, total_h_2x = self._compute_sprite_layout(sizes_2x)
            for entry in manifest_2x.values():
                entry["pixelRatio"] = 2
            atlas_2x = QImage(max(total_w_2x, 1), max(total_h_2x, 1), QImage.Format_ARGB32)
            if not atlas_2x.isNull():
                atlas_2x.fill(Qt.transparent)
                painter_2x = QPainter(atlas_2x)
                for name, entry in manifest_2x.items():
                    painter_2x.drawImage(entry["x"], entry["y"], images_2x[name])
                painter_2x.end()
                atlas_2x_path = os.path.join(output_dir, "sprites@2x.png")
                json_2x_path = os.path.join(output_dir, "sprites@2x.json")
                if atlas_2x.save(atlas_2x_path):
                    with open(json_2x_path, "w", encoding="utf-8") as f:
                        _json.dump(manifest_2x, f, indent=2)
                    self._log(f"Wrote @2x sprite atlas → {atlas_2x_path}")

        return True

    def _compute_sprite_layout(self, sprite_sizes):
        """Compute x/y offsets for a single-row sprite atlas.

        :param sprite_sizes: dict mapping name -> (width, height) in pixels
        :returns: (manifest_dict, total_width, total_height)
                  manifest_dict maps name -> {"x", "y", "width", "height", "pixelRatio"}
        """
        manifest = {}
        x = 0
        max_height = 0
        for name, (w, h) in sprite_sizes.items():
            manifest[name] = {
                "x": x,
                "y": 0,
                "width": w,
                "height": h,
                "pixelRatio": 1,
            }
            x += w
            max_height = max(max_height, h)
        return manifest, x, max_height

