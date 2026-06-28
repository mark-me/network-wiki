"""Visual style dataclasses for graph nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NodeColor:
    """Full colour specification for a node.

    All values are CSS colour strings (hex, rgb, or named colours).

    Args:
        background: Fill colour of the node body.
        border: Colour of the node border.
        highlight_background: Fill colour when the node is selected.
        highlight_border: Border colour when the node is selected.
        hover_background: Fill colour on mouse-over.
        hover_border: Border colour on mouse-over.
    """

    background: str = "#97C2FC"
    border: str = "#2B7CE9"
    highlight_background: str = "#D2E5FF"
    highlight_border: str = "#2B7CE9"
    hover_background: str = "#D2E5FF"
    hover_border: str = "#2B7CE9"

    def to_vis(self) -> dict:
        """Serialise to a vis.js colour options dict."""
        return {
            "background": self.background,
            "border": self.border,
            "highlight": {
                "background": self.highlight_background,
                "border": self.highlight_border,
            },
            "hover": {
                "background": self.hover_background,
                "border": self.hover_border,
            },
        }

    @classmethod
    def from_hex(cls, hex_color: str) -> "NodeColor":
        """Create a ``NodeColor`` from a single hex colour.

        Alpha variants for hover and highlight states are computed
        automatically by appending two-digit hex opacity suffixes.

        Args:
            hex_color: A CSS hex colour string, e.g. ``"#e94560"`` or ``"e94560"``.

        Returns:
            A :class:`NodeColor` with border, background, hover, and highlight
            variants derived from *hex_color*.
        """
        base = "#" + hex_color.strip("#")
        return cls(
            background=base + "33",
            border=base,
            highlight_background=base + "88",
            highlight_border=base,
            hover_background=base + "66",
            hover_border=base,
        )


@dataclass
class NodeFont:
    """Font settings for a node label.

    Args:
        color: CSS colour of the label text.
        size: Font size in points.
        face: CSS font-family string.
        bold: Render label in bold.
        italic: Render label in italic.
        align: Horizontal alignment: ``"center"``, ``"left"``, or ``"right"``.
    """

    color: str = "#343434"
    size: int = 14
    face: str = "Segoe UI, sans-serif"
    bold: bool = False
    italic: bool = False
    align: str = "center"

    def to_vis(self) -> dict:
        """Serialise to a vis.js font options dict."""
        return {
            "color": self.color,
            "size": self.size,
            "face": self.face,
            "bold": self.bold,
            "italic": self.italic,
            "align": self.align,
        }


@dataclass
class NodeStyle:
    """All visual properties of a node, mapped directly to vis.js node options.

    Args:
        shape: Node shape. Options: ``"ellipse"``, ``"circle"``, ``"database"``,
            ``"box"``, ``"text"``, ``"image"``, ``"circularImage"``,
            ``"diamond"``, ``"dot"``, ``"star"``, ``"triangle"``,
            ``"triangleDown"``, ``"hexagon"``, ``"square"``, ``"icon"``.
        size: Radius in pixels for round shapes; half-width for box shapes.
        color: A hex colour string (alpha variants computed automatically)
            or a :class:`NodeColor` for full control.
        border_width: Border line width in pixels.
        border_width_selected: Border width when the node is selected.
        border_dashes: Render border as a dashed line.
        label: Override label text.  ``None`` uses the vertex ``"name"`` attribute.
        font: Font settings for the label.
        show_label: Set to ``False`` to hide the label entirely.
        tooltip: HTML string shown on mouse-over (vis.js ``title``).
        shadow: Enable drop shadow.
        shadow_color: CSS colour of the shadow.
        shadow_size: Shadow blur radius in pixels.
        shadow_x: Shadow horizontal offset in pixels.
        shadow_y: Shadow vertical offset in pixels.
        value: When set, node size is scaled between *scaling_min* and
            *scaling_max* based on this value relative to other nodes.
        scaling_min: Minimum size in pixels when value-based scaling is active.
        scaling_max: Maximum size in pixels when value-based scaling is active.
        margin: Inner padding for ``"box"`` shape nodes.
        image: URL or data-URI for ``"image"`` and ``"circularImage"`` shapes.
        x: Fixed horizontal canvas position in pixels.
        y: Fixed vertical canvas position in pixels.
        fixed_x: Prevent physics from moving the node horizontally.
        fixed_y: Prevent physics from moving the node vertically.
        group: vis.js group name for shared group-level styling.
        extra: Any additional vis.js node properties not listed above.
            These are merged last and override earlier values.
    """

    shape: str = "box"
    size: int = 25
    color: NodeColor | str = field(default_factory=NodeColor)
    border_width: int = 2
    border_width_selected: int = 3
    border_dashes: bool = False
    label: Optional[str] = None
    font: NodeFont = field(default_factory=NodeFont)
    show_label: bool = True
    tooltip: Optional[str] = None
    shadow: bool = False
    shadow_color: str = "rgba(0,0,0,0.5)"
    shadow_size: int = 10
    shadow_x: int = 5
    shadow_y: int = 5
    value: Optional[float] = None
    scaling_min: int = 10
    scaling_max: int = 50
    margin: int = 10
    image: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    fixed_x: bool = False
    fixed_y: bool = False
    group: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_vis(self, node_id: int, label_fallback: str) -> dict:
        """Serialise this style to a vis.js node dict.

        Args:
            node_id: The integer vertex index used as the vis.js node id.
            label_fallback: Label text used when :attr:`label` is ``None``.

        Returns:
            A dict suitable for inclusion in the vis.js ``DataSet`` of nodes.
        """
        label = self.label if self.label is not None else label_fallback
        if not self.show_label:
            label = ""

        col = (
            NodeColor.from_hex(self.color).to_vis()
            if isinstance(self.color, str)
            else self.color.to_vis()
        )

        d: dict[str, Any] = {
            "id": node_id,
            "label": label,
            "shape": self.shape,
            "size": self.size,
            "color": col,
            "borderWidth": self.border_width,
            "borderWidthSelected": self.border_width_selected,
            "font": self.font.to_vis(),
            "margin": self.margin,
            "shadow": {
                "enabled": self.shadow,
                "color": self.shadow_color,
                "size": self.shadow_size,
                "x": self.shadow_x,
                "y": self.shadow_y,
            },
        }

        if self.border_dashes:
            d["shapeProperties"] = {"borderDashes": [5, 5]}
        if self.tooltip:
            d["title"] = self.tooltip
        if self.value is not None:
            d["value"] = self.value
            d["scaling"] = {"min": self.scaling_min, "max": self.scaling_max}
        if self.image:
            d["image"] = self.image
        if self.x is not None:
            d["x"] = self.x
        if self.y is not None:
            d["y"] = self.y
        if self.fixed_x or self.fixed_y:
            d["fixed"] = {"x": self.fixed_x, "y": self.fixed_y}
        if self.group:
            d["group"] = self.group

        d |= self.extra
        return d
