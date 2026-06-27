"""GraphExporter — orchestrates node/edge styling, wiki rendering, and HTML output."""


from __future__ import annotations

import contextlib
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
    """Convert an igraph.Graph into an interactive standalone HTML page.
    Provide an explorable graph view with per-node wiki content and theming controls.

    Args:
        graph: The graph to export. Each vertex must at least provide a "name" attribute.
        title: Title for the generated page.
        layout: Physics and layout configuration for the visualization.
        theme: Theme configuration (accent color, panel width, default color scheme).
        default_node_style: Fallback style for nodes when no callback style is provided.
        default_edge_style: Fallback style for edges when no callback style is provided.
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
        """Initialize a GraphExporter with graph, layout, theme and style defaults.
        Prepare callback hooks and configuration used to render the HTML wiki page.

        Args:
            graph: The ``igraph.Graph`` instance that will be exported.
            title: The ``str`` title shown on the generated HTML page.
            layout: Optional ``LayoutConfig``; defaults to a standard layout.
            theme: Optional ``ThemeConfig``; defaults to a standard theme.
            default_node_style: Optional ``NodeStyle`` used when no node-style callback is set.
            default_edge_style: Optional ``EdgeStyle`` used when no edge-style callback is set.
        """
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
        """Register a callback that determines the visual style for each node.
        Use this to customize node appearance beyond the default node style.

        Args:
            cb: A callable that receives a vertex and returns a ``NodeStyle`` instance.
        """

        self._node_style_cb = cb

    def set_edge_style_callback(self, cb: Callable) -> None:
        """Register a callback that determines the visual style for each edge.
        Use this to customize edge appearance beyond the default edge style.

        Args:
            cb: A callable that receives an edge and returns an ``EdgeStyle`` instance.
        """
        self._edge_style_cb = cb

    def set_wiki_callback(self, cb: Callable) -> None:
        """
        Register a callback that determines the wiki content for each vertex.
        Ignored if ``set_wiki_renderer`` is also called.

        Args:
            cb: A callable that receives a vertex and returns a ``WikiContent`` instance.
        """
        self._wiki_cb = cb

    def set_wiki_renderer(self, renderer: WikiTemplateRenderer) -> None:
        """Set a template-based wiki renderer for node-specific content.
        Overrides the wiki callback when both are configured.

        Args:
            renderer: The template renderer used to generate wiki content per vertex.
        """
        self._wiki_renderer = renderer

    # ── Interne helpers ───────────────────────────────────────────────────────

    def _get_label(self, vertex) -> str:
        """Determine a readable label text for a vertex based on known attributes.
        Fall back to a generated name when no suitable attribute is available.

        Args:
            vertex: The vertex for which a label should be determined.

        Returns:
            str: The chosen label text for the vertex.
        """
        for attr in ("name", "label"):
            with contextlib.suppress(KeyError, IndexError):
                val = vertex[attr]
                if val is not None:
                    return str(val)
        return f"Node {vertex.index}"

    def _build_nodes(self) -> tuple[list[dict], dict[int, WikiContent]]:
        """Construct the node payload for the visualization and associated wiki content.
        Combine labels, styles and rendered wiki HTML for each vertex in the graph.

        Returns:
            tuple[list[dict], dict[int, WikiContent]]: A list of node dictionaries for vis.js,
                and a mapping from vertex id to its ``WikiContent``.
        """
        vis_nodes: list[dict] = []
        wiki_map: dict[int, WikiContent] = {}

        for v in self.graph.vs:
            label = self._get_label(v)
            style = (
                self._node_style_cb(v)
                if self._node_style_cb
                else self.default_node_style
            )
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
        """Assemble the edge payload for the visualization library.
        Apply either callback-provided styles or the default edge style to each edge.

        Returns:
            list[dict]: A list of edge dictionaries formatted for the vis.js graph.
        """
        result = []
        for e in self.graph.es:
            style = (
                self._edge_style_cb(e)
                if self._edge_style_cb
                else self.default_edge_style
            )
            result.append(style.to_vis(e.source, e.target))
        return result

    # ── Export ────────────────────────────────────────────────────────────────

    def export(self, path: str | Path = "graph_wiki.html") -> Path:
        """Generate the standalone HTML graph wiki page and write it to disk.
        Build the visualization, wiki payloads and layout configuration before saving.

        Args:
            path: The ``str`` or ``Path`` destination for the HTML file, relative or absolute.

        Returns:
            Path: The absolute path to the generated HTML file.
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
