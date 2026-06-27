"""Visuele stijl-dataclasses voor edges."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EdgeColor:
    """Kleurinstelling voor een edge."""
    color: str = "#848484"
    highlight: str = "#848484"
    hover: str = "#848484"
    inherit: str | bool = False  # "from" | "to" | "both" | False

    def to_vis(self) -> dict:
        return {
            "color": self.color,
            "highlight": self.highlight,
            "hover": self.hover,
            "inherit": self.inherit,
        }


@dataclass
class EdgeArrows:
    """
    Pijlconfiguratie voor edges.

    type-opties:
        ``"arrow"`` | ``"bar"`` | ``"circle"`` | ``"box"`` | ``"crow"`` |
        ``"curve"`` | ``"diamond"`` | ``"inv_curve"`` | ``"inv_triangle"`` |
        ``"triangle"`` | ``"vee"``
    """
    to_enabled: bool = True
    to_scale: float = 0.8
    to_type: str = "arrow"

    from_enabled: bool = False
    from_scale: float = 0.8
    from_type: str = "arrow"

    middle_enabled: bool = False
    middle_scale: float = 0.8
    middle_type: str = "arrow"

    def to_vis(self) -> dict:
        d: dict[str, Any] = {}
        if self.to_enabled:
            d["to"] = {"enabled": True, "scaleFactor": self.to_scale, "type": self.to_type}
        if self.from_enabled:
            d["from"] = {"enabled": True, "scaleFactor": self.from_scale, "type": self.from_type}
        if self.middle_enabled:
            d["middle"] = {"enabled": True, "scaleFactor": self.middle_scale, "type": self.middle_type}
        return d


@dataclass
class EdgeStyle:
    """
    Alle visuele eigenschappen van een edge, direct mapped op vis.js edge-opties.

    smooth_type-opties:
        ``"dynamic"`` | ``"continuous"`` | ``"discrete"`` | ``"diagonalCross"`` |
        ``"straightCross"`` | ``"horizontal"`` | ``"vertical"`` |
        ``"curvedCW"`` | ``"curvedCCW"`` | ``"cubicBezier"``

    color:
        Geef een hex-string of een :class:`EdgeColor` voor volledige controle.

    extra:
        Eventuele vis.js edge-properties die hier niet staan (worden samengevoegd).
    """
    width: float = 2.0
    width_selected: float = 3.0

    color: EdgeColor | str = field(default_factory=lambda: EdgeColor())

    label: Optional[str] = None
    font_color: str = "#343434"
    font_size: int = 12
    font_align: str = "middle"  # middle | top | bottom | horizontal

    arrows: EdgeArrows = field(default_factory=EdgeArrows)

    dashes: bool = False
    smooth_type: str = "cubicBezier"
    smooth_roundness: float = 0.5  # 0–1

    shadow: bool = False
    tooltip: Optional[str] = None
    length: Optional[int] = None  # gewenste lengte in pixels (physics)

    extra: dict = field(default_factory=dict)

    def to_vis(self, from_id: int, to_id: int) -> dict:
        """Zet EdgeStyle om naar een vis.js edge-dict."""
        if isinstance(self.color, str):
            col = EdgeColor(color=self.color, highlight=self.color, hover=self.color).to_vis()
        else:
            col = self.color.to_vis()

        d: dict[str, Any] = {
            "from": from_id,
            "to": to_id,
            "width": self.width,
            "selectionWidth": self.width_selected,
            "color": col,
            "arrows": self.arrows.to_vis(),
            "smooth": {
                "type": self.smooth_type,
                "roundness": self.smooth_roundness,
            },
            "dashes": self.dashes,
            "shadow": self.shadow,
            "font": {
                "color": self.font_color,
                "size": self.font_size,
                "align": self.font_align,
            },
        }

        if self.label:
            d["label"] = self.label
        if self.tooltip:
            d["title"] = self.tooltip
        if self.length:
            d["length"] = self.length

        d.update(self.extra)
        return d
