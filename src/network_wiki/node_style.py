"""Visuele stijl-dataclasses voor nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class NodeColor:
    """
    Volledige kleurspecificatie voor een node.
    Alle waarden zijn CSS-kleurstrings (hex, rgb of kleurnaam).
    """
    background: str = "#97C2FC"
    border: str = "#2B7CE9"
    highlight_background: str = "#D2E5FF"
    highlight_border: str = "#2B7CE9"
    hover_background: str = "#D2E5FF"
    hover_border: str = "#2B7CE9"

    def to_vis(self) -> dict:
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
        """Maak een NodeColor van een enkele hex-kleur met automatische alpha-varianten."""
        h = hex_color.rstrip("#").lstrip("#")
        base = f"#{h}"
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
    """Lettertype-instellingen voor het node-label."""
    color: str = "#343434"
    size: int = 14
    face: str = "Segoe UI, sans-serif"
    bold: bool = False
    italic: bool = False
    align: str = "center"  # center | left | right

    def to_vis(self) -> dict:
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
    """
    Alle visuele eigenschappen van een node, direct mapped op vis.js node-opties.

    shape-opties:
        ``"ellipse"`` | ``"circle"`` | ``"database"`` | ``"box"`` | ``"text"`` |
        ``"image"`` | ``"circularImage"`` | ``"diamond"`` | ``"dot"`` | ``"star"`` |
        ``"triangle"`` | ``"triangleDown"`` | ``"hexagon"`` | ``"square"`` | ``"icon"``

    color:
        Geef een hex-string (alpha-varianten worden automatisch berekend)
        of een :class:`NodeColor` voor volledige controle.

    value:
        Indien opgegeven: node-grootte schaalt tussen ``scaling_min`` en
        ``scaling_max`` op basis van deze waarde relatief aan andere nodes.

    extra:
        Eventuele vis.js node-properties die hier niet staan (worden samengevoegd).
    """
    shape: str = "box"
    size: int = 25

    color: NodeColor | str = field(default_factory=lambda: NodeColor())

    border_width: int = 2
    border_width_selected: int = 3
    border_dashes: bool = False

    label: Optional[str] = None   # None = gebruik vertex "name"-attribuut
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
        """Zet NodeStyle om naar een vis.js node-dict."""
        label = self.label if self.label is not None else label_fallback
        if not self.show_label:
            label = ""

        if isinstance(self.color, str):
            col = NodeColor.from_hex(self.color).to_vis()
        else:
            col = self.color.to_vis()

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

        d.update(self.extra)
        return d
