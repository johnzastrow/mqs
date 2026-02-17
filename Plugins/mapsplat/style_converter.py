"""
MapSplat - Style Converter Module

This module converts QGIS layer styles to MapLibre GL Style JSON format.

Supported renderers:
- Single Symbol (fill, line, marker)
- Categorized
- Graduated

Unsupported renderers fall back to default styles.
"""

__version__ = "0.1.9"

from qgis.core import (
    QgsVectorLayer,
    QgsSingleSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsSymbol,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
)


class StyleConverter:
    """Converts QGIS styles to MapLibre style JSON."""

    # Default colors for fallback
    DEFAULT_FILL_COLOR = "#3388ff"
    DEFAULT_LINE_COLOR = "#333333"
    DEFAULT_POINT_COLOR = "#ff6600"

    def __init__(self, layers, settings):
        """Initialize converter.

        :param layers: List of QgsVectorLayer
        :param settings: Export settings dictionary
        """
        self.layers = layers
        self.settings = settings

    def convert(self, single_file=True):
        """Convert all layers to MapLibre style JSON.

        :param single_file: If True, all layers share one PMTiles source.
                           If False, each layer has its own PMTiles file.
        :returns: Style JSON dictionary
        """
        self._single_file = single_file

        if single_file:
            sources = {
                "mapsplat": {
                    "type": "vector",
                    "url": "pmtiles://data/layers.pmtiles"
                }
            }
        else:
            # Create separate source for each layer
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
            "layers": [
                # Background layer
                {
                    "id": "background",
                    "type": "background",
                    "paint": {
                        "background-color": "#f8f9fa"
                    }
                }
            ]
        }

        # Convert each layer
        for layer in self.layers:
            layer_styles = self._convert_layer(layer)
            style["layers"].extend(layer_styles)

        return style

    def _convert_layer(self, layer):
        """Convert a single layer to MapLibre layer definitions.

        :param layer: QgsVectorLayer
        :returns: List of MapLibre layer dictionaries
        """
        renderer = layer.renderer()
        source_layer = self._sanitize_name(layer.name())
        geom_type = layer.geometryType()

        # Determine source name based on single_file mode
        if self._single_file:
            source_name = "mapsplat"
        else:
            source_name = source_layer  # Each layer has its own source

        # Dispatch based on renderer type
        if isinstance(renderer, QgsSingleSymbolRenderer):
            return self._convert_single_symbol(layer, renderer, source_layer, geom_type, source_name)
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            return self._convert_categorized(layer, renderer, source_layer, geom_type, source_name)
        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            return self._convert_graduated(layer, renderer, source_layer, geom_type, source_name)
        else:
            # Fallback to default style
            return self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_single_symbol(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert single symbol renderer.

        :returns: List of MapLibre layer dictionaries
        """
        symbol = renderer.symbol()
        layer_id = f"{source_layer}"

        if geom_type == 2:  # Polygon
            return [self._symbol_to_fill_layer(symbol, layer_id, source_layer, source_name)]
        elif geom_type == 1:  # Line
            return [self._symbol_to_line_layer(symbol, layer_id, source_layer, source_name)]
        elif geom_type == 0:  # Point
            return [self._symbol_to_circle_layer(symbol, layer_id, source_layer, source_name)]

        return self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_categorized(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert categorized symbol renderer.

        :returns: List of MapLibre layer dictionaries
        """
        layers = []
        attr_name = renderer.classAttribute()

        # Build a match expression for colors
        categories = renderer.categories()

        if geom_type == 2:  # Polygon
            fill_colors = ["match", ["get", attr_name]]
            outline_colors = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                fill_color, outline_color = self._extract_fill_colors(symbol)

                if value is not None and value != "":
                    fill_colors.extend([value, fill_color])
                    outline_colors.extend([value, outline_color])

            # Default fallback
            fill_colors.append(self.DEFAULT_FILL_COLOR)
            outline_colors.append(self.DEFAULT_LINE_COLOR)

            layers.append({
                "id": source_layer,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": fill_colors,
                    "fill-opacity": 0.7,
                    "fill-outline-color": outline_colors
                }
            })

        elif geom_type == 1:  # Line
            line_colors = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                line_color = self._extract_line_color(symbol)

                if value is not None and value != "":
                    line_colors.extend([value, line_color])

            line_colors.append(self.DEFAULT_LINE_COLOR)

            layers.append({
                "id": source_layer,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": line_colors,
                    "line-width": 2
                }
            })

        elif geom_type == 0:  # Point
            circle_colors = ["match", ["get", attr_name]]

            for cat in categories:
                value = cat.value()
                symbol = cat.symbol()
                circle_color = self._extract_marker_color(symbol)

                if value is not None and value != "":
                    circle_colors.extend([value, circle_color])

            circle_colors.append(self.DEFAULT_POINT_COLOR)

            layers.append({
                "id": source_layer,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": circle_colors,
                    "circle-radius": 6,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1
                }
            })

        return layers if layers else self._create_default_style(layer, source_layer, geom_type, source_name)

    def _convert_graduated(self, layer, renderer, source_layer, geom_type, source_name):
        """Convert graduated symbol renderer.

        :returns: List of MapLibre layer dictionaries
        """
        layers = []
        attr_name = renderer.classAttribute()
        ranges = renderer.ranges()

        if not ranges:
            return self._create_default_style(layer, source_layer, geom_type, source_name)

        # Build step expression for colors based on ranges
        if geom_type == 2:  # Polygon
            fill_expr = ["step", ["get", attr_name]]
            # First color (below first break)
            first_color, _ = self._extract_fill_colors(ranges[0].symbol())
            fill_expr.append(first_color)

            for r in ranges:
                color, _ = self._extract_fill_colors(r.symbol())
                fill_expr.extend([r.lowerValue(), color])

            layers.append({
                "id": source_layer,
                "type": "fill",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "fill-color": fill_expr,
                    "fill-opacity": 0.7,
                    "fill-outline-color": "#333333"
                }
            })

        elif geom_type == 1:  # Line
            line_expr = ["step", ["get", attr_name]]
            first_color = self._extract_line_color(ranges[0].symbol())
            line_expr.append(first_color)

            for r in ranges:
                color = self._extract_line_color(r.symbol())
                line_expr.extend([r.lowerValue(), color])

            layers.append({
                "id": source_layer,
                "type": "line",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "line-color": line_expr,
                    "line-width": 2
                }
            })

        elif geom_type == 0:  # Point
            circle_expr = ["step", ["get", attr_name]]
            first_color = self._extract_marker_color(ranges[0].symbol())
            circle_expr.append(first_color)

            for r in ranges:
                color = self._extract_marker_color(r.symbol())
                circle_expr.extend([r.lowerValue(), color])

            layers.append({
                "id": source_layer,
                "type": "circle",
                "source": source_name,
                "source-layer": source_layer,
                "paint": {
                    "circle-color": circle_expr,
                    "circle-radius": 6,
                    "circle-stroke-color": "#ffffff",
                    "circle-stroke-width": 1
                }
            })

        return layers if layers else self._create_default_style(layer, source_layer, geom_type, source_name)

    def _symbol_to_fill_layer(self, symbol, layer_id, source_layer, source_name):
        """Convert fill symbol to MapLibre layer.

        :returns: MapLibre layer dictionary
        """
        fill_color, outline_color = self._extract_fill_colors(symbol)

        return {
            "id": layer_id,
            "type": "fill",
            "source": source_name,
            "source-layer": source_layer,
            "paint": {
                "fill-color": fill_color,
                "fill-opacity": 0.7,
                "fill-outline-color": outline_color
            }
        }

    def _symbol_to_line_layer(self, symbol, layer_id, source_layer, source_name):
        """Convert line symbol to MapLibre layer.

        :returns: MapLibre layer dictionary
        """
        line_color = self._extract_line_color(symbol)
        line_width = self._extract_line_width(symbol)

        return {
            "id": layer_id,
            "type": "line",
            "source": source_name,
            "source-layer": source_layer,
            "paint": {
                "line-color": line_color,
                "line-width": line_width
            }
        }

    def _symbol_to_circle_layer(self, symbol, layer_id, source_layer, source_name):
        """Convert marker symbol to MapLibre circle layer.

        :returns: MapLibre layer dictionary
        """
        circle_color = self._extract_marker_color(symbol)
        circle_radius = self._extract_marker_size(symbol)

        return {
            "id": layer_id,
            "type": "circle",
            "source": source_name,
            "source-layer": source_layer,
            "paint": {
                "circle-color": circle_color,
                "circle-radius": circle_radius,
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1
            }
        }

    def _create_default_style(self, layer, source_layer, geom_type, source_name):
        """Create default fallback style for unsupported renderers.

        :returns: List with single MapLibre layer dictionary
        """
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

    def _extract_fill_colors(self, symbol):
        """Extract fill and outline colors from a fill symbol.

        :param symbol: QgsSymbol
        :returns: Tuple of (fill_color, outline_color) as hex strings
        """
        fill_color = self.DEFAULT_FILL_COLOR
        outline_color = self.DEFAULT_LINE_COLOR

        if symbol and symbol.symbolLayerCount() > 0:
            layer = symbol.symbolLayer(0)
            if isinstance(layer, QgsSimpleFillSymbolLayer):
                fill_color = layer.fillColor().name()
                outline_color = layer.strokeColor().name()

        return fill_color, outline_color

    def _extract_line_color(self, symbol):
        """Extract line color from a line symbol.

        :param symbol: QgsSymbol
        :returns: Color as hex string
        """
        if symbol and symbol.symbolLayerCount() > 0:
            layer = symbol.symbolLayer(0)
            if isinstance(layer, QgsSimpleLineSymbolLayer):
                return layer.color().name()

        return self.DEFAULT_LINE_COLOR

    def _extract_line_width(self, symbol):
        """Extract line width from a line symbol.

        :param symbol: QgsSymbol
        :returns: Width in pixels
        """
        if symbol and symbol.symbolLayerCount() > 0:
            layer = symbol.symbolLayer(0)
            if isinstance(layer, QgsSimpleLineSymbolLayer):
                # Convert mm to approximate pixels (assuming 96 DPI)
                return max(1, layer.width() * 3.78)

        return 2

    def _extract_marker_color(self, symbol):
        """Extract marker color from a marker symbol.

        :param symbol: QgsSymbol
        :returns: Color as hex string
        """
        if symbol and symbol.symbolLayerCount() > 0:
            layer = symbol.symbolLayer(0)
            if isinstance(layer, QgsSimpleMarkerSymbolLayer):
                return layer.fillColor().name()

        return self.DEFAULT_POINT_COLOR

    def _extract_marker_size(self, symbol):
        """Extract marker size from a marker symbol.

        :param symbol: QgsSymbol
        :returns: Radius in pixels
        """
        if symbol and symbol.symbolLayerCount() > 0:
            layer = symbol.symbolLayer(0)
            if isinstance(layer, QgsSimpleMarkerSymbolLayer):
                # Size is diameter in mm, convert to radius in pixels
                return max(3, layer.size() * 1.89)

        return 6

    def _sanitize_name(self, name):
        """Sanitize layer name for use as source-layer.

        :param name: Original name
        :returns: Sanitized name
        """
        sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        return sanitized.strip("_").lower()
