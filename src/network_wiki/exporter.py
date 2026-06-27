"""GraphExporter — orkestreert node/edge-stijl, wiki-rendering en HTML-output."""

from __future__ import annotations

import importlib.resources as _pkg_res
import json
from pathlib import Path
from typing import Callable, Optional

from jinja2 import Environment, FileSystemLoader

from .edge_style import EdgeStyle
from .layout import LayoutConfig, ThemeConfig
from .node_style import NodeStyle
from .wiki import WikiContent, WikiTemplateRenderer, _auto_wiki


class GraphExporter:
    """
    Converteert een igraph.Graph naar een interactieve standalone HTML-pagina.

    De pagina bevat een vis.js-graph met Bootstrap 5 UI, een uitklapbaar
    wiki-sidepanel per node en een volledige wiki-modal. Het thema past zich
    automatisch aan aan de OS-voorkeur van de gebruiker (light/dark) en is
    ook handmatig te schakelen.

    Parameters
    ----------
    graph:
        De te exporteren graaf. Elke vertex heeft minimaal een "name"-attribuut.
    title:
        Paginatitel.
    layout:
        Physics- en layout-instellingen.
    theme:
        Thema-instellingen (accentkleur, paneelbreedte, standaard kleurschema).
    default_node_style:
        Fallback-stijl voor nodes zonder callback-resultaat.
    default_edge_style:
        Fallback-stijl voor edges zonder callback-resultaat.
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

    # ── Callback setters ──────────────────────────────────────────────────────

    def set_node_style_callback(self, cb: Callable) -> None:
        """Stel een functie in die per vertex een NodeStyle teruggeeft."""
        self._node_style_cb = cb

    def set_edge_style_callback(self, cb: Callable) -> None:
        """Stel een functie in die per edge een EdgeStyle teruggeeft."""
        self._edge_style_cb = cb

    def set_wiki_callback(self, cb: Callable) -> None:
        """
        Stel een functie in die per vertex een WikiContent teruggeeft.
        Wordt genegeerd als set_wiki_renderer ook is aangeroepen.
        """
        self._wiki_cb = cb

    def set_wiki_renderer(self, renderer: WikiTemplateRenderer) -> None:
        """
        Koppel een WikiTemplateRenderer voor Jinja2-gebaseerde wiki's.
        Heeft prioriteit boven set_wiki_callback.
        """
        self._wiki_renderer = renderer

    # ── Interne helpers ───────────────────────────────────────────────────────

    def _get_label(self, vertex) -> str:
        for attr in ("name", "label"):
            try:
                val = vertex[attr]
                if val is not None:
                    return str(val)
            except (KeyError, IndexError):
                pass
        return f"Node {vertex.index}"

    def _build_nodes(self) -> tuple[list[dict], dict[int, WikiContent]]:
        vis_nodes: list[dict] = []
        wiki_map: dict[int, WikiContent] = {}

        for v in self.graph.vs:
            label = self._get_label(v)
            style = self._node_style_cb(v) if self._node_style_cb else self.default_node_style
            vis_nodes.append(style.to_vis(v.index, label))

            if self._wiki_renderer:
                wiki = self._wiki_renderer.render(v, self.graph)
            elif self._wiki_cb:
                wiki = self._wiki_cb(v)
            else:
                wiki = _auto_wiki(v, self.graph)

            wiki_map[v.index] = wiki

        return vis_nodes, wiki_map

    def _build_edges(self) -> list[dict]:
        result = []
        for e in self.graph.es:
            style = self._edge_style_cb(e) if self._edge_style_cb else self.default_edge_style
            result.append(style.to_vis(e.source, e.target))
        return result

    # ── Export ────────────────────────────────────────────────────────────────

    def export(self, path: str | Path = "graph_wiki.html") -> Path:
        """
        Genereer de HTML-pagina en schrijf naar path.

        Returns
        -------
        Path
            Absoluut pad naar het gegenereerde bestand.
        """
        vis_nodes, wiki_map = self._build_nodes()
        vis_edges = self._build_edges()

        wiki_js = {
            vid: {
                "label": next(
                    (n["label"] for n in vis_nodes if n["id"] == vid), str(vid)
                ),
                "mini": wiki.mini_html or "",
                "full": wiki.full_html,
            }
            for vid, wiki in wiki_map.items()
        }

        t = self.theme
        page_tmpl_path = _pkg_res.files("network_wiki").joinpath("templates")
        env = Environment(loader=FileSystemLoader(str(page_tmpl_path)))
        html = env.get_template("page.html.j2").render(
            title=self.title,
            accent_color=t.accent_color,
            panel_width=t.panel_width_px,
            color_scheme=t.default_color_scheme,
            lang=t.lang,
            nodes_json=json.dumps(vis_nodes, ensure_ascii=False),
            edges_json=json.dumps(vis_edges, ensure_ascii=False),
            wiki_json=json.dumps(wiki_js, ensure_ascii=False),
            layout_json=json.dumps(self.layout.to_vis(), ensure_ascii=False),
        )

        out = Path(path).resolve()
        out.write_text(html, encoding="utf-8")
        print(f"Geexporteerd naar: {out}")
        return out
