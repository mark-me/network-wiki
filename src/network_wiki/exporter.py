"""
igraph_wiki_exporter.py
=======================
Generieke wrapper om een igraph.Graph te exporteren naar een interactieve
standalone HTML-pagina met vis.js, inclusief klikbare node-wiki's.

Gebruik
-------
    from igraph_wiki_exporter import GraphExporter, NodeStyle, EdgeStyle, WikiContent

    exporter = GraphExporter(graph)

    # Stijl per vertex instellen via vertex-attributen OF via callbacks
    exporter.set_node_style_callback(lambda v: NodeStyle(
        color=COLOR_MAP.get(v["type"], "#888"),
        shape=SHAPE_MAP.get(v["type"], "ellipse"),
        size=20 + v["weight"] * 2,
    ))

    exporter.set_wiki_callback(lambda v: WikiContent(
        mini_html=render_mini(v),
        full_html=render_full(v),
    ))

    exporter.export("output.html")
"""

from __future__ import annotations

import json
import html as html_mod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional, Any, Union
import textwrap

try:
    from jinja2 import (
        Environment, FileSystemLoader, BaseLoader,
        TemplateNotFound, StrictUndefined, select_autoescape,
    )
    _JINJA2_AVAILABLE = True
except ImportError:
    _JINJA2_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses voor visuele eigenschappen
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class NodeColor:
    """
    Kleurinstelling voor een node.
    Alle waarden zijn CSS-kleurstrings (hex, rgb, naam).
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


@dataclass
class NodeFont:
    """Lettertype-instellingen voor het node-label."""
    color: str = "#343434"
    size: int = 14                    # pt
    face: str = "Segoe UI, sans-serif"
    bold: bool = False
    italic: bool = False
    align: str = "center"            # center | left | right

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
    Alle visuele eigenschappen van een node.

    shape-opties (vis.js):
        "ellipse" | "circle" | "database" | "box" | "text" |
        "image" | "circularImage" | "diamond" | "dot" | "star" |
        "triangle" | "triangleDown" | "hexagon" | "square" | "icon"

    scaling:  grootte wordt bepaald door `size` (pixels).
              Als je `scaling_min`/`scaling_max` instelt wordt de grootte
              geschaald op basis van het `value`-attribuut van de node.
    """
    # Vorm
    shape: str = "box"
    size: int = 25                   # pixels (radius voor ronde shapes)

    # Kleur – geef een NodeColor of een hex-string
    color: NodeColor | str = field(default_factory=lambda: NodeColor())

    # Rand
    border_width: int = 2
    border_width_selected: int = 3
    border_dashes: bool = False      # True = stippellijn

    # Label
    label: Optional[str] = None      # None = gebruik vertex["name"]
    font: NodeFont = field(default_factory=NodeFont)
    show_label: bool = True

    # Tooltip (title-attribuut in vis.js)
    tooltip: Optional[str] = None

    # Schaduw
    shadow: bool = False
    shadow_color: str = "rgba(0,0,0,0.5)"
    shadow_size: int = 10
    shadow_x: int = 5
    shadow_y: int = 5

    # Schaling op basis van waarde
    value: Optional[float] = None    # als opgegeven: pas grootte aan op value
    scaling_min: int = 10
    scaling_max: int = 50

    # Marge binnen de box-shape
    margin: int = 10

    # Afbeelding (alleen voor shape="image" of "circularImage")
    image: Optional[str] = None

    # Vaste positie (None = physics bepaalt positie)
    x: Optional[float] = None
    y: Optional[float] = None
    fixed_x: bool = False
    fixed_y: bool = False

    # Groep (voor gedeelde styling via group-config)
    group: Optional[str] = None

    # Extra vis.js-properties die hier niet staan (worden samengevoegd)
    extra: dict = field(default_factory=dict)

    def to_vis(self, node_id: int, label_fallback: str) -> dict:
        """Zet NodeStyle om naar een vis.js node-dict."""
        label = self.label if self.label is not None else label_fallback
        if not self.show_label:
            label = ""

        # Kleur
        if isinstance(self.color, str):
            col = NodeColor(
                background=self.color + "33",
                border=self.color,
                highlight_background=self.color + "88",
                highlight_border=self.color,
                hover_background=self.color + "66",
                hover_border=self.color,
            ).to_vis()
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


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EdgeColor:
    """Kleurinstelling voor een edge."""
    color: str = "#848484"
    highlight: str = "#848484"
    hover: str = "#848484"
    inherit: str | bool = False      # "from" | "to" | "both" | False

    def to_vis(self) -> dict:
        return {
            "color": self.color,
            "highlight": self.highlight,
            "hover": self.hover,
            "inherit": self.inherit,
        }


@dataclass
class EdgeArrows:
    """Pijlconfiguratie voor edges."""
    to_enabled: bool = True
    to_scale: float = 0.8
    to_type: str = "arrow"           # arrow | bar | circle | box | crow | curve | diamond | inv_curve | inv_triangle | triangle | vee

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
    Alle visuele eigenschappen van een edge.

    smooth.type-opties:
        "dynamic" | "continuous" | "discrete" | "diagonalCross" |
        "straightCross" | "horizontal" | "vertical" | "curvedCW" |
        "curvedCCW" | "cubicBezier"
    """
    # Breedte
    width: float = 2.0
    width_selected: float = 3.0

    # Kleur
    color: EdgeColor | str = field(default_factory=lambda: EdgeColor())

    # Label
    label: Optional[str] = None
    font_color: str = "#343434"
    font_size: int = 12
    font_align: str = "middle"       # middle | top | bottom | horizontal

    # Pijlen
    arrows: EdgeArrows = field(default_factory=EdgeArrows)

    # Stijl
    dashes: bool = False             # True = stippellijn
    smooth_type: str = "cubicBezier"
    smooth_roundness: float = 0.5    # 0–1

    # Schaduw
    shadow: bool = False

    # Tooltip
    tooltip: Optional[str] = None

    # Gewicht (voor physics)
    length: Optional[int] = None     # gewenste lengte in pixels

    # Extra vis.js-properties
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


# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class WikiContent:
    """
    Wiki-inhoud voor één node.

    mini_html : HTML voor het sidepanel (compact overzicht).
    full_html : HTML voor de volledige wiki-modal.

    Als full_html None is, wordt de "Volledige wiki"-knop verborgen.
    Als mini_html None is, wordt er een automatische fallback gegenereerd
    op basis van alle vertex-attributen.
    """
    mini_html: Optional[str] = None
    full_html: Optional[str] = None


class WikiTemplateRenderer:
    """
    Rendert mini- en full-wiki HTML via Jinja2-templates.

    Templates ontvangen altijd de volgende context-variabelen:

        v          – het igraph Vertex-object zelf
        attrs      – dict van alle vertex-attributen  {naam: waarde}
        label      – display-naam van de node (str)
        index      – vertex-index (int)
        n_in       – aantal inkomende edges (int)
        n_out      – aantal uitgaande edges (int)
        neighbours – lijst van namen van alle buurknopen (list[str])
        graph      – de volledige igraph.Graph

    Aanvullende sleutels die je via `global_context` meegeeft zijn ook
    beschikbaar in elke template.

    Templateresolutie-volgorde (eerst gevonden wint):
        1. Per-type template  (mini of full) voor het type van deze vertex
        2. Standaard template (mini of full) van de renderer
        3. Auto-fallback      (gegenereerd op basis van vertex-attributen)

    Parameters
    ----------
    template_dir : str | Path | None
        Map met externe .html.j2 templatebestanden. Als None worden alleen
        inline-templates gebruikt.
    mini_template : str | None
        Inline Jinja2-templatestring voor de mini-wiki.
        Wordt genegeerd als `mini_template_file` is opgegeven.
    full_template : str | None
        Inline Jinja2-templatestring voor de full-wiki.
        Wordt genegeerd als `full_template_file` is opgegeven.
    mini_template_file : str | None
        Bestandsnaam (relatief aan template_dir) voor de mini-wiki template.
    full_template_file : str | None
        Bestandsnaam (relatief aan template_dir) voor de full-wiki template.
    type_attr : str
        Vertex-attribuut dat het type bepaalt voor per-type templates.
        Standaard "type".
    mini_templates_by_type : dict[str, str]
        Inline mini-templates per type:  {"source": "...", "target": "..."}
    full_templates_by_type : dict[str, str]
        Inline full-templates per type:  {"source": "...", "target": "..."}
    mini_template_files_by_type : dict[str, str]
        Bestandsnamen van mini-templates per type.
    full_template_files_by_type : dict[str, str]
        Bestandsnamen van full-templates per type.
    global_context : dict
        Extra variabelen beschikbaar in élke template.
    undefined_strict : bool
        Als True gooit Jinja2 een fout bij onbekende variabelen (aanbevolen
        tijdens ontwikkeling). Als False worden ze stil leeg.

    Voorbeeldgebruik
    ----------------
    Extern bestandsbeheer::

        renderer = WikiTemplateRenderer(
            template_dir="templates/wiki",
            mini_template_file="mini_default.html.j2",
            full_template_file="full_default.html.j2",
            full_template_files_by_type={
                "source": "full_source.html.j2",
                "target": "full_target.html.j2",
            },
        )
        exporter.set_wiki_renderer(renderer)

    Inline templates::

        renderer = WikiTemplateRenderer(
            mini_template=\"\"\"
            <div class="mini-wiki">
              <div class="node-type">{{ attrs.type }}</div>
              <div class="node-desc">{{ attrs.description }}</div>
              <div class="attr-grid">
                {% for key, val in attrs.items() %}
                <div class="attr-box">
                  <div class="attr-label">{{ key }}</div>
                  <div class="attr-value">{{ val }}</div>
                </div>
                {% endfor %}
              </div>
            </div>\"\"\",
            full_template=\"\"\"
            <h2>{{ label }}</h2>
            <p>{{ attrs.description }}</p>
            <h3>Attributen</h3>
            <table>
              {% for key, val in attrs.items() %}
              <tr><td>{{ key }}</td><td>{{ val }}</td></tr>
              {% endfor %}
            </table>\"\"\",
        )
        exporter.set_wiki_renderer(renderer)
    """

    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        mini_template: Optional[str] = None,
        full_template: Optional[str] = None,
        mini_template_file: Optional[str] = None,
        full_template_file: Optional[str] = None,
        type_attr: str = "type",
        mini_templates_by_type: Optional[dict[str, str]] = None,
        full_templates_by_type: Optional[dict[str, str]] = None,
        mini_template_files_by_type: Optional[dict[str, str]] = None,
        full_template_files_by_type: Optional[dict[str, str]] = None,
        global_context: Optional[dict] = None,
        undefined_strict: bool = True,
    ):
        if not _JINJA2_AVAILABLE:
            raise ImportError(
                "Jinja2 is vereist voor WikiTemplateRenderer. "
                "Installeer het via: pip install jinja2"
            )

        self.type_attr = type_attr
        self.global_context = global_context or {}
        self._undefined = StrictUndefined if undefined_strict else None

        # ── Jinja2-omgeving opzetten ──────────────────────────────────────
        # Loader-volgorde: gebruikersbestanden -> inline strings -> gebundelde package-templates
        from jinja2 import DictLoader, ChoiceLoader
        loaders = []

        # 1. Gebruiker: externe map met .j2-bestanden (hoogste prioriteit)
        if template_dir is not None:
            self._template_dir = Path(template_dir).resolve()
            loaders.append(FileSystemLoader(str(self._template_dir)))
        else:
            self._template_dir = None

        # 2. Gebruiker: inline template-strings
        self._inline_store: dict[str, str] = {}
        loaders.append(DictLoader(self._inline_store))

        # 3. Package: meegeleverde standaard-templates (laagste prioriteit).
        #    importlib.resources werkt zowel geinstalleerd (pip) als in-place (src-layout).
        import importlib.resources as _pkg_res
        _pkg_templates = _pkg_res.files("network_wiki").joinpath("templates")
        loaders.append(FileSystemLoader(str(_pkg_templates)))

        self._env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(["html", "j2"]),
            undefined=StrictUndefined if undefined_strict else self._env_undefined_cls(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # ── Template-registratie ──────────────────────────────────────────
        # Inline defaults
        self._mini_inline: Optional[str] = None
        self._full_inline: Optional[str] = None

        # File-based defaults
        self._mini_file: Optional[str] = mini_template_file
        self._full_file: Optional[str] = full_template_file

        # Per-type inline
        self._mini_by_type: dict[str, str] = mini_templates_by_type or {}
        self._full_by_type: dict[str, str] = full_templates_by_type or {}

        # Per-type file-based
        self._mini_files_by_type: dict[str, str] = mini_template_files_by_type or {}
        self._full_files_by_type: dict[str, str] = full_template_files_by_type or {}

        # Registreer inline templates in de DictLoader
        if mini_template:
            self._register_inline("__mini_default__", mini_template)
            self._mini_inline = "__mini_default__"

        if full_template:
            self._register_inline("__full_default__", full_template)
            self._full_inline = "__full_default__"

        for vtype, tmpl in self._mini_by_type.items():
            key = f"__mini_{vtype}__"
            self._register_inline(key, tmpl)

        for vtype, tmpl in self._full_by_type.items():
            key = f"__full_{vtype}__"
            self._register_inline(key, tmpl)

    def _env_undefined_cls(self):
        """Geef Undefined terug als de strict-mode uitstaat."""
        from jinja2 import Undefined
        return Undefined

    def _register_inline(self, key: str, source: str) -> None:
        """Voeg een inline template toe aan de DictLoader."""
        self._inline_store[key] = source
        # Herlaad de DictLoader door de store te muteren (werkt met DictLoader)

    def _build_context(self, vertex, graph) -> dict:
        """Stel de volledige template-context samen voor een vertex."""
        attrs = {}
        for attr in graph.vertex_attributes():
            try:
                val = vertex[attr]
                attrs[attr] = val
            except (KeyError, IndexError):
                pass

        # Label bepalen
        label = None
        for key in ("name", "label"):
            if key in attrs and attrs[key] is not None:
                label = str(attrs[key])
                break
        if label is None:
            label = f"Node {vertex.index}"

        n_in  = len(graph.predecessors(vertex.index))
        n_out = len(graph.successors(vertex.index))

        neighbour_ids = graph.neighbors(vertex.index)
        neighbours = []
        for i in neighbour_ids:
            nv = graph.vs[i]
            for key in ("name", "label"):
                try:
                    val = nv[key]
                    if val is not None:
                        neighbours.append(str(val))
                        break
                except (KeyError, IndexError):
                    pass
            else:
                neighbours.append(f"Node {i}")

        ctx = {
            "v":          vertex,
            "attrs":      attrs,
            "label":      label,
            "index":      vertex.index,
            "n_in":       n_in,
            "n_out":      n_out,
            "neighbours": neighbours,
            "graph":      graph,
        }
        ctx.update(self.global_context)
        return ctx

    def _resolve_template_name(
        self,
        vtype: Optional[str],
        by_type_inline: dict[str, str],
        by_type_files: dict[str, str],
        default_inline: Optional[str],
        default_file: Optional[str],
        prefix: str,
    ) -> Optional[str]:
        """
        Bepaal de te gebruiken template-naam in volgorde van prioriteit:
        per-type inline → per-type file → default inline → default file → None
        """
        if vtype:
            # 1. Per-type inline
            if vtype in by_type_inline:
                return f"__{prefix}_{vtype}__"
            # 2. Per-type file
            if vtype in by_type_files:
                return by_type_files[vtype]

        # 3. Default inline
        if default_inline:
            return default_inline

        # 4. Default file
        if default_file:
            return default_file

        return None

    def render(self, vertex, graph) -> WikiContent:
        """
        Render mini- en full-HTML voor een vertex.

        Parameters
        ----------
        vertex : igraph.Vertex
        graph  : igraph.Graph

        Returns
        -------
        WikiContent
        """
        ctx = self._build_context(vertex, graph)
        vtype = ctx["attrs"].get(self.type_attr)

        # ── Mini ──────────────────────────────────────────────────────────
        mini_name = self._resolve_template_name(
            vtype,
            self._mini_by_type,
            self._mini_files_by_type,
            self._mini_inline,
            self._mini_file,
            "mini",
        )
        if mini_name:
            mini_html = self._env.get_template(mini_name).render(**ctx)
        else:
            mini_html = None   # laat GraphExporter de auto-fallback gebruiken

        # ── Full ──────────────────────────────────────────────────────────
        full_name = self._resolve_template_name(
            vtype,
            self._full_by_type,
            self._full_files_by_type,
            self._full_inline,
            self._full_file,
            "full",
        )
        if full_name:
            full_html = self._env.get_template(full_name).render(**ctx)
        else:
            full_html = None

        return WikiContent(mini_html=mini_html, full_html=full_html)


@dataclass
class LayoutConfig:
    """
    Vis.js physics- en layout-instellingen.

    solver-opties: "barnesHut" | "forceAtlas2Based" | "repulsion" | "hierarchicalRepulsion"
    hierarchical.direction: "UD" | "DU" | "LR" | "RL"
    """
    # Physics
    physics_enabled: bool = True
    solver: str = "forceAtlas2Based"
    stabilization_iterations: int = 150
    gravity: float = -50
    spring_length: int = 200
    spring_constant: float = 0.05
    damping: float = 0.09

    # Hierarchisch layout
    hierarchical: bool = False
    hierarchical_direction: str = "LR"
    hierarchical_sort_method: str = "directed"  # directed | hubsize
    hierarchical_level_separation: int = 200
    hierarchical_node_spacing: int = 120

    # Interactie
    hover: bool = True
    multiselect: bool = True
    navigation_buttons: bool = False
    keyboard_navigation: bool = False
    zoom_speed: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0

    def to_vis(self) -> dict:
        cfg: dict[str, Any] = {
            "physics": {
                "enabled": self.physics_enabled,
                "solver": self.solver,
                "stabilization": {"iterations": self.stabilization_iterations},
                self.solver: {
                    "gravitationalConstant": self.gravity,
                    "springLength": self.spring_length,
                    "springConstant": self.spring_constant,
                    "damping": self.damping,
                },
            },
            "interaction": {
                "hover": self.hover,
                "multiselect": self.multiselect,
                "navigationButtons": self.navigation_buttons,
                "keyboard": self.keyboard_navigation,
                "zoomSpeed": self.zoom_speed,
                "zoomView": True,
                "minZoom": self.min_zoom,
                "maxZoom": self.max_zoom,
            },
        }
        if self.hierarchical:
            cfg["layout"] = {
                "hierarchical": {
                    "enabled": True,
                    "direction": self.hierarchical_direction,
                    "sortMethod": self.hierarchical_sort_method,
                    "levelSeparation": self.hierarchical_level_separation,
                    "nodeSpacing": self.hierarchical_node_spacing,
                }
            }
            cfg["physics"]["enabled"] = False  # physics incompatibel met hierarchisch
        return cfg


@dataclass
class ThemeConfig:
    """Kleurthema voor de HTML-pagina en wiki-panelen."""
    page_bg: str = "#1a1a2e"
    page_fg: str = "#e0e0e0"
    panel_bg: str = "#16213e"
    panel_header_bg: str = "#0f3460"
    accent: str = "#e94560"
    accent_secondary: str = "#a8dadc"
    panel_width_px: int = 360


# ─────────────────────────────────────────────────────────────────────────────
# Hoofd-exportklasse
# ─────────────────────────────────────────────────────────────────────────────

class GraphExporter:
    """
    Converteert een igraph.Graph naar een standalone interactieve HTML-pagina.

    Parameters
    ----------
    graph : igraph.Graph
        De te exporteren graaf. Elke vertex heeft minimaal een "name"-attribuut.
    title : str
        Paginatitel (ook zichtbaar in de browser-tab).
    layout : LayoutConfig
        Physics- en layout-instellingen.
    theme : ThemeConfig
        Kleurthema voor de UI.
    default_node_style : NodeStyle
        Fallback-stijl voor nodes die niet door de callback worden overschreven.
    default_edge_style : EdgeStyle
        Fallback-stijl voor edges die niet door de callback worden overschreven.
    """

    def __init__(
        self,
        graph,
        title: str = "Graph Wiki",
        layout: Optional[LayoutConfig] = None,
        theme: Optional[ThemeConfig] = None,
        default_node_style: Optional[NodeStyle] = None,
        default_edge_style: Optional[EdgeStyle] = None,
    ):
        self.graph = graph
        self.title = title
        self.layout = layout or LayoutConfig()
        self.theme = theme or ThemeConfig()
        self.default_node_style = default_node_style or NodeStyle()
        self.default_edge_style = default_edge_style or EdgeStyle()

        self._node_style_cb: Optional[Callable] = None
        self._edge_style_cb: Optional[Callable] = None
        self._wiki_cb: Optional[Callable] = None
        self._wiki_renderer: Optional[WikiTemplateRenderer] = None
        self._node_id_attr: str = "name"

    # ── Callback-setters ──────────────────────────────────────────────────

    def set_node_style_callback(self, cb: Callable[["igraph.Vertex"], NodeStyle]) -> None:
        """
        Stel een functie in die per vertex een NodeStyle teruggeeft.

        Voorbeeld:
            def my_style(v):
                return NodeStyle(
                    color=COLOR_MAP[v["type"]],
                    shape="diamond" if v["critical"] else "box",
                    size=10 + v["weight"],
                )
            exporter.set_node_style_callback(my_style)
        """
        self._node_style_cb = cb

    def set_edge_style_callback(self, cb: Callable[["igraph.Edge"], EdgeStyle]) -> None:
        """
        Stel een functie in die per edge een EdgeStyle teruggeeft.

        Voorbeeld:
            def my_edge_style(e):
                return EdgeStyle(
                    width=1 + e["weight"],
                    color=EdgeColor(color="#e94560") if e["critical"] else EdgeColor(),
                    dashes=e["optional"],
                )
            exporter.set_edge_style_callback(my_edge_style)
        """
        self._edge_style_cb = cb

    def set_wiki_callback(self, cb: Callable[["igraph.Vertex"], WikiContent]) -> None:
        """
        Stel een functie in die per vertex WikiContent teruggeeft.

        Als je dit niet instelt, genereert de exporter automatisch een
        wiki op basis van alle vertex-attributen.

        Voorbeeld:
            def my_wiki(v):
                return WikiContent(
                    mini_html=render_mini_template(v),
                    full_html=render_full_template(v),
                )
            exporter.set_wiki_callback(my_wiki)
        """
        self._wiki_cb = cb

    def set_wiki_renderer(self, renderer: "WikiTemplateRenderer") -> None:
        """
        Koppel een WikiTemplateRenderer voor Jinja2-gebaseerde wiki's.

        Heeft prioriteit boven set_wiki_callback als beide zijn ingesteld.

        Voorbeeld::

            renderer = WikiTemplateRenderer(
                template_dir="templates/wiki",
                mini_template_file="mini.html.j2",
                full_template_file="full.html.j2",
                full_template_files_by_type={
                    "source": "full_source.html.j2",
                    "pipeline": "full_pipeline.html.j2",
                },
                global_context={"project": "ETL v2"},
            )
            exporter.set_wiki_renderer(renderer)
        """
        self._wiki_renderer = renderer

    # ── Interne helpers ───────────────────────────────────────────────────

    def _get_label(self, vertex) -> str:
        """Haal het display-label op uit de vertex-attributen."""
        for attr in ("name", "label", "id"):
            try:
                val = vertex[attr]
                if val is not None:
                    return str(val)
            except (KeyError, IndexError):
                pass
        return f"Node {vertex.index}"

    def _auto_wiki(self, vertex) -> WikiContent:
        """Genereer automatisch een wiki op basis van alle vertex-attributen."""
        label = self._get_label(vertex)
        attrs = {k: vertex[k] for k in self.graph.vertex_attributes()
                 if vertex[k] is not None}

        # Mini-wiki: attributentabel
        rows = "".join(
            f'<div class="attr-box">'
            f'<div class="attr-label">{html_mod.escape(str(k))}</div>'
            f'<div class="attr-value">{html_mod.escape(str(v))}</div>'
            f'</div>'
            for k, v in attrs.items()
        )
        n_in = len(self.graph.predecessors(vertex.index))
        n_out = len(self.graph.successors(vertex.index))

        mini = f"""
        <div class="mini-wiki">
          <div class="node-type">Node {vertex.index}</div>
          <div class="node-desc"><em>Automatisch gegenereerde wiki</em></div>
          <div class="attr-grid">{rows}</div>
          <div class="connections">
            Inkomend: <strong>{n_in}</strong> &nbsp;|&nbsp;
            Uitgaand: <strong>{n_out}</strong>
          </div>
        </div>"""

        # Full wiki: alle attributen + neighbours
        neighbour_ids = self.graph.neighbors(vertex.index)
        neighbour_labels = [self._get_label(self.graph.vs[i]) for i in neighbour_ids]
        nbr_items = "".join(f"<li>{html_mod.escape(l)}</li>" for l in neighbour_labels)

        full_attr_rows = "".join(
            f"<tr><td>{html_mod.escape(str(k))}</td><td>{html_mod.escape(str(v))}</td></tr>"
            for k, v in attrs.items()
        )
        full = f"""
        <h2>{html_mod.escape(label)}</h2>
        <h3>Attributen</h3>
        <table>
          <tr><th>Attribuut</th><th>Waarde</th></tr>
          {full_attr_rows}
        </table>
        <h3>Verbonden nodes</h3>
        <ul>{nbr_items if nbr_items else '<li><em>Geen</em></li>'}</ul>"""

        return WikiContent(mini_html=mini, full_html=full)

    def _build_nodes(self) -> tuple[list[dict], dict[int, WikiContent]]:
        """Bouw de vis.js node-lijst en de wiki-data-dict."""
        vis_nodes = []
        wiki_map: dict[int, WikiContent] = {}

        for v in self.graph.vs:
            vid = v.index
            label = self._get_label(v)

            # Stijl bepalen
            if self._node_style_cb:
                style = self._node_style_cb(v)
            else:
                style = self.default_node_style

            node_dict = style.to_vis(vid, label)
            vis_nodes.append(node_dict)

            # Wiki bepalen  (volgorde: renderer > callback > auto)
            if self._wiki_renderer:
                wiki = self._wiki_renderer.render(v, self.graph)
                # Vul ontbrekende helft aan met auto-fallback
                if wiki.mini_html is None or wiki.full_html is None:
                    auto = self._auto_wiki(v)
                    wiki = WikiContent(
                        mini_html=wiki.mini_html if wiki.mini_html is not None else auto.mini_html,
                        full_html=wiki.full_html if wiki.full_html is not None else auto.full_html,
                    )
            elif self._wiki_cb:
                wiki = self._wiki_cb(v)
            else:
                wiki = self._auto_wiki(v)
            wiki_map[vid] = wiki

        return vis_nodes, wiki_map

    def _build_edges(self) -> list[dict]:
        """Bouw de vis.js edge-lijst."""
        vis_edges = []
        for e in self.graph.es:
            if self._edge_style_cb:
                style = self._edge_style_cb(e)
            else:
                style = self.default_edge_style
            vis_edges.append(style.to_vis(e.source, e.target))
        return vis_edges

    # ── Exportmethode ─────────────────────────────────────────────────────

    def export(self, path: str | Path = "graph_wiki.html") -> Path:
        """
        Genereer de HTML-pagina en schrijf naar `path`.

        Returns
        -------
        Path
            Absoluut pad naar het gegenereerde bestand.
        """
        vis_nodes, wiki_map = self._build_nodes()
        vis_edges = self._build_edges()
        layout_cfg = self.layout.to_vis()
        t = self.theme

        # Wiki-data als JavaScript-object: {nodeId: {mini: "...", full: "..."}}
        wiki_js: dict[int, dict] = {}
        for vid, wiki in wiki_map.items():
            label = next(
                (n["label"] for n in vis_nodes if n["id"] == vid), str(vid)
            )
            wiki_js[vid] = {
                "label": label,
                "mini": wiki.mini_html or "",
                "full": wiki.full_html,   # None → knop verborgen
            }

        nodes_json = json.dumps(vis_nodes, ensure_ascii=False, indent=2)
        edges_json = json.dumps(vis_edges, ensure_ascii=False, indent=2)
        wiki_json = json.dumps(wiki_js, ensure_ascii=False, indent=2)
        layout_json = json.dumps(layout_cfg, ensure_ascii=False, indent=2)

        html = self._render_html(
            nodes_json=nodes_json,
            edges_json=edges_json,
            wiki_json=wiki_json,
            layout_json=layout_json,
            theme=t,
        )

        out = Path(path).resolve()
        out.write_text(html, encoding="utf-8")
        print(f"✅ Geëxporteerd naar: {out}")
        return out

    def _render_html(
        self,
        nodes_json: str,
        edges_json: str,
        wiki_json: str,
        layout_json: str,
        theme: ThemeConfig,
    ) -> str:
        t = theme
        return textwrap.dedent(f"""\
        <!DOCTYPE html>
        <html lang="nl">
        <head>
          <meta charset="UTF-8">
          <title>{html_mod.escape(self.title)}</title>
          <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
          <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
              font-family: 'Segoe UI', sans-serif;
              background: {t.page_bg};
              color: {t.page_fg};
              height: 100vh;
              overflow: hidden;
            }}

            #graph-container {{ width: 100%; height: 100vh; }}

            /* ── Side panel ── */
            #wiki-panel {{
              position: fixed; right: 0; top: 0;
              width: {t.panel_width_px}px; height: 100vh;
              background: {t.panel_bg};
              border-left: 2px solid {t.panel_header_bg};
              transform: translateX(100%);
              transition: transform 0.3s ease;
              display: flex; flex-direction: column; z-index: 100;
              box-shadow: -4px 0 20px rgba(0,0,0,0.5);
            }}
            #wiki-panel.open {{ transform: translateX(0); }}

            #wiki-panel-header {{
              padding: 16px 20px;
              background: {t.panel_header_bg};
              display: flex; justify-content: space-between; align-items: center;
              flex-shrink: 0;
            }}
            #wiki-panel-title {{
              font-size: 1.1rem; font-weight: 600; color: {t.accent};
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
              max-width: 200px;
            }}
            .panel-actions {{ display: flex; gap: 8px; flex-shrink: 0; }}
            .panel-btn {{
              background: rgba(255,255,255,0.1); border: none; color: {t.page_fg};
              padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem;
              transition: background 0.2s; white-space: nowrap;
            }}
            .panel-btn:hover {{ background: rgba(255,255,255,0.2); }}
            .panel-btn.hidden {{ display: none; }}

            #wiki-panel-content {{ flex: 1; overflow-y: auto; padding: 20px; }}

            /* ── Modal ── */
            #wiki-modal {{
              display: none; position: fixed; inset: 0;
              background: rgba(0,0,0,0.8); z-index: 200;
              align-items: center; justify-content: center;
            }}
            #wiki-modal.open {{ display: flex; }}
            #wiki-modal-inner {{
              background: {t.panel_bg}; width: 80vw; max-width: 960px; height: 85vh;
              border-radius: 10px; border: 1px solid {t.panel_header_bg};
              display: flex; flex-direction: column;
              box-shadow: 0 20px 60px rgba(0,0,0,0.6);
            }}
            #wiki-modal-header {{
              padding: 16px 24px; background: {t.panel_header_bg};
              border-radius: 10px 10px 0 0;
              display: flex; justify-content: space-between; align-items: center;
              flex-shrink: 0;
            }}
            #wiki-modal-title {{ font-size: 1.4rem; font-weight: 700; color: {t.accent}; }}
            #wiki-modal-content {{ flex: 1; overflow-y: auto; padding: 28px; }}

            /* ── Wiki typografie ── */
            .wiki-body h2 {{ color: {t.accent}; margin: 20px 0 8px; }}
            .wiki-body h3 {{ color: {t.accent_secondary}; margin: 16px 0 6px; }}
            .wiki-body p  {{ line-height: 1.7; margin-bottom: 12px; color: #c0c0d0; }}
            .wiki-body ul {{ padding-left: 20px; margin-bottom: 12px; }}
            .wiki-body li {{ line-height: 1.8; color: #c0c0d0; }}
            .wiki-body table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
            .wiki-body th {{ background: {t.panel_header_bg}; color: {t.accent_secondary}; padding: 8px 12px; text-align: left; }}
            .wiki-body td {{ padding: 8px 12px; border-bottom: 1px solid {t.panel_header_bg}; color: #c0c0d0; }}
            .wiki-body .tag {{
              display: inline-block; background: {t.panel_header_bg}; color: {t.accent_secondary};
              padding: 2px 10px; border-radius: 20px; font-size: 0.8rem; margin: 2px;
            }}

            /* ── Mini-wiki ── */
            .mini-wiki .node-type {{
              font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px;
              color: {t.accent_secondary}; margin-bottom: 8px;
            }}
            .mini-wiki .node-desc {{ font-size: 0.9rem; line-height: 1.6; color: #c0c0d0; margin-bottom: 16px; }}
            .mini-wiki .attr-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px; }}
            .mini-wiki .attr-box {{ background: {t.panel_header_bg}; border-radius: 6px; padding: 10px; }}
            .mini-wiki .attr-label {{ font-size: 0.7rem; color: {t.accent_secondary}; text-transform: uppercase; letter-spacing: 0.5px; }}
            .mini-wiki .attr-value {{ font-size: 1rem; font-weight: 600; color: {t.page_fg}; }}
            .mini-wiki .tags-row {{ margin-bottom: 16px; }}
            .mini-wiki .tag {{
              display: inline-block; background: {t.page_bg}; color: {t.accent_secondary};
              padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; margin: 2px;
              border: 1px solid {t.panel_header_bg};
            }}
            .mini-wiki .connections {{ font-size: 0.85rem; color: #c0c0d0; }}
            .mini-wiki .connections strong {{ color: {t.accent}; }}

            #close-modal {{ background: none; border: none; color: {t.page_fg}; font-size: 1.4rem; cursor: pointer; }}
            #close-modal:hover {{ color: {t.accent}; }}
          </style>
        </head>
        <body>

        <div id="graph-container"></div>

        <div id="wiki-panel">
          <div id="wiki-panel-header">
            <span id="wiki-panel-title">Node</span>
            <div class="panel-actions">
              <button class="panel-btn" id="btn-full-wiki" onclick="openFullWiki()">📖 Volledige wiki</button>
              <button class="panel-btn" onclick="closePanel()">✕</button>
            </div>
          </div>
          <div id="wiki-panel-content" class="wiki-body"></div>
        </div>

        <div id="wiki-modal">
          <div id="wiki-modal-inner">
            <div id="wiki-modal-header">
              <span id="wiki-modal-title"></span>
              <button id="close-modal" onclick="closeModal()">✕</button>
            </div>
            <div id="wiki-modal-content" class="wiki-body"></div>
          </div>
        </div>

        <script>
        // ── Data (gegenereerd door Python) ────────────────────────────────────
        const WIKI_DATA  = {wiki_json};
        const VIS_NODES  = {nodes_json};
        const VIS_EDGES  = {edges_json};
        const LAYOUT_CFG = {layout_json};

        // ── Graph initialisatie ───────────────────────────────────────────────
        const container = document.getElementById("graph-container");
        const network = new vis.Network(
          container,
          {{
            nodes: new vis.DataSet(VIS_NODES),
            edges: new vis.DataSet(VIS_EDGES),
          }},
          LAYOUT_CFG
        );

        // ── Interactie ────────────────────────────────────────────────────────
        let currentNodeId = null;

        network.on("click", params => {{
          if (params.nodes.length > 0) {{
            openPanel(params.nodes[0]);
          }} else if (params.edges.length === 0) {{
            closePanel();
          }}
        }});

        function openPanel(id) {{
          currentNodeId = id;
          const data = WIKI_DATA[id];
          if (!data) return;

          document.getElementById("wiki-panel-title").textContent = data.label;
          document.getElementById("wiki-panel-content").innerHTML = data.mini || "<em>Geen wiki beschikbaar</em>";

          // Verberg "Volledige wiki"-knop als full_html null is
          const btnFull = document.getElementById("btn-full-wiki");
          if (data.full === null || data.full === undefined) {{
            btnFull.classList.add("hidden");
          }} else {{
            btnFull.classList.remove("hidden");
          }}

          document.getElementById("wiki-panel").classList.add("open");
        }}

        function closePanel() {{
          document.getElementById("wiki-panel").classList.remove("open");
          currentNodeId = null;
        }}

        function openFullWiki() {{
          if (currentNodeId === null) return;
          const data = WIKI_DATA[currentNodeId];
          if (!data || data.full === null) return;
          document.getElementById("wiki-modal-title").textContent = data.label;
          document.getElementById("wiki-modal-content").innerHTML = data.full;
          document.getElementById("wiki-modal").classList.add("open");
        }}

        function closeModal() {{
          document.getElementById("wiki-modal").classList.remove("open");
        }}

        document.getElementById("wiki-modal").addEventListener("click", e => {{
          if (e.target === document.getElementById("wiki-modal")) closeModal();
        }});

        document.addEventListener("keydown", e => {{
          if (e.key === "Escape") {{ closeModal(); closePanel(); }}
        }});
        </script>
        </body>
        </html>
        """)
