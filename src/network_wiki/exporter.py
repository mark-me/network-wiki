"""GraphExporter – orchestrates node/edge styling, wiki rendering, and HTML output."""

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
    """Convert an ``igraph.Graph`` into a standalone interactive HTML page.

    The page embeds a vis.js graph with a Bootstrap 5 UI, a collapsible
    wiki side-panel per node, and a full-screen wiki modal.  The developer
    selects a Bootswatch theme at export time; the end-user can toggle
    between light and dark mode inside the page.

    Args:
        graph: The graph to export.  Each vertex should provide at least a
            ``"name"`` attribute.
        title: Title displayed in the browser tab and toolbar.
        layout: Physics and layout configuration.  Defaults to
            :class:`LayoutConfig` with ``forceAtlas2Based`` physics.
        theme: Visual theme.  Defaults to :class:`ThemeConfig` (plain
            Bootstrap, no Bootswatch).
        default_node_style: Fallback :class:`NodeStyle` used when no
            node-style callback is registered.
        default_edge_style: Fallback :class:`EdgeStyle` used when no
            edge-style callback is registered.

    Example::

        import igraph as ig
        from network_wiki import GraphExporter, NodeStyle, ThemeConfig

        g = ig.Graph(directed=True)
        g.add_vertices(3)
        g.vs["name"] = ["Source", "Pipeline", "Target"]
        g.add_edges([(0, 1), (1, 2)])

        exporter = GraphExporter(
            g,
            title="ETL Overview",
            theme=ThemeConfig(bootswatch_theme="flatly"),
        )
        exporter.set_node_style_callback(
            lambda v: NodeStyle(color="#2ecc71" if v["name"] == "Pipeline" else "#3498db")
        )
        exporter.export("etl.html")
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

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_node_style_callback(self, cb: Callable) -> None:
        """Register a callback that returns a :class:`NodeStyle` for each vertex.

        Args:
            cb: ``(igraph.Vertex) -> NodeStyle``
        """
        self._node_style_cb = cb

    def set_edge_style_callback(self, cb: Callable) -> None:
        """Register a callback that returns an :class:`EdgeStyle` for each edge.

        Args:
            cb: ``(igraph.Edge) -> EdgeStyle``
        """
        self._edge_style_cb = cb

    def set_wiki_callback(self, cb: Callable) -> None:
        """Register a callback that returns :class:`WikiContent` for each vertex.

        Ignored when :meth:`set_wiki_renderer` is also called (renderer takes
        priority).

        Args:
            cb: ``(igraph.Vertex) -> WikiContent``
        """
        self._wiki_cb = cb

    def set_wiki_renderer(self, renderer: WikiTemplateRenderer) -> None:
        """Attach a Jinja2-based :class:`WikiTemplateRenderer`.

        Takes priority over any callback registered with :meth:`set_wiki_callback`.

        Args:
            renderer: Configured template renderer instance.
        """
        self._wiki_renderer = renderer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_label(self, vertex) -> str:
        """Return a human-readable label for *vertex*.

        Tries the ``"name"`` attribute first, then ``"label"``, and falls back
        to ``"Node <index>"``.
        """
        for attr in ("name", "label"):
            with contextlib.suppress(KeyError, IndexError):
                val = vertex[attr]
                if val is not None:
                    return str(val)
        return f"Node {vertex.index}"

    def _build_nodes(self) -> tuple[list[dict], dict[int, WikiContent]]:
        """Build the vis.js node list and the wiki-content map.

        Returns:
            A tuple of ``(vis_nodes, wiki_map)`` where *vis_nodes* is a list
            of node dicts for vis.js and *wiki_map* maps vertex ids to their
            :class:`WikiContent`.
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
        """Build the vis.js edge list.

        Returns:
            A list of edge dicts formatted for vis.js.
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

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self, path: str | Path = "graph_wiki.html") -> Path:
        """Render the HTML page and write it to *path*.

        Args:
            path: Destination file path (``str`` or :class:`~pathlib.Path`).
                Created or overwritten; parent directories must exist.

        Returns:
            The resolved absolute :class:`~pathlib.Path` of the written file.
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
        tmpl_path = _pkg_res.files("network_wiki").joinpath("templates")
        env = Environment(loader=FileSystemLoader(str(tmpl_path)))
        html = env.get_template("page.html.j2").render(
            title=self.title,
            css_url=t.css_url,
            accent_color=t.accent_color,
            panel_width=t.panel_width_px,
            base_scheme=t.base_scheme,
            lang=t.lang,
            nodes_json=json.dumps(vis_nodes, ensure_ascii=False),
            edges_json=json.dumps(vis_edges, ensure_ascii=False),
            wiki_json=json.dumps(wiki_js, ensure_ascii=False),
            layout_json=json.dumps(self.layout.to_vis(), ensure_ascii=False),
        )

        out = Path(path).resolve()
        out.write_text(html, encoding="utf-8")
        print(f"Exported to: {out}")
        return out
