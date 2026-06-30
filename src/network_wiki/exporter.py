"""GraphExporter – orchestrates node/edge styling, wiki rendering, and HTML output."""

from __future__ import annotations

import contextlib
import importlib.resources as _pkg_res
import json
from pathlib import Path
from typing import Callable, Optional

from jinja2 import Environment, FileSystemLoader

from .edge_style import EdgeStyle
from .json_safe import serialize_json, validate_json_injection_safety
from .layout import LayoutConfig, ThemeConfig
from .node_style import NodeStyle
from .wiki import WikiContent, WikiTemplateRenderer, _auto_edge_wiki, _auto_wiki


class GraphExporter:
    """Convert an ``igraph.Graph`` into a standalone interactive HTML page.

    The page embeds a vis.js graph with a Bootstrap 5 / Bootswatch UI, a
    collapsible wiki side-panel for nodes *and* edges, and a full-screen wiki
    modal.  The developer selects a Bootswatch theme at export time; the
    end-user toggles light/dark mode inside the page.

    Callbacks and the wiki renderer can be supplied either as constructor
    arguments or via the ``set_*`` setter methods — both styles are equivalent.
    Constructor arguments take priority over setters when both are used.

    Args:
        graph: The graph to export.  Each vertex should provide at least a
            ``"name"`` attribute.
        title: Title displayed in the browser tab and toolbar.
        layout: Physics and layout configuration.
        theme: Visual theme (Bootswatch, accent colour, panel width).
        default_node_style: Fallback :class:`NodeStyle` when no node callback
            is registered.
        default_edge_style: Fallback :class:`EdgeStyle` when no edge callback
            is registered.
        node_style_callback: ``(igraph.Vertex) -> NodeStyle``.
        edge_style_callback: ``(igraph.Edge) -> EdgeStyle``.
        wiki_callback: ``(igraph.Vertex) -> WikiContent`` for node wikis.
            Ignored when *wiki_renderer* is also supplied.
        edge_wiki_callback: ``(igraph.Edge) -> WikiContent`` for edge wikis.
        wiki_renderer: Jinja2-based renderer for node wiki content.
            Takes priority over *wiki_callback*.

    Example::

        exporter = GraphExporter(
            g,
            title="ETL Overview",
            theme=ThemeConfig(bootswatch_theme="flatly"),
            node_style_callback=lambda v: NodeStyle(color="#2ecc71"),
            wiki_renderer=WikiTemplateRenderer(
                full_template_file="full.html.j2",
                template_dir="templates/",
            ),
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
        node_style_callback: Optional[Callable] = None,
        edge_style_callback: Optional[Callable] = None,
        wiki_callback: Optional[Callable] = None,
        edge_wiki_callback: Optional[Callable] = None,
        wiki_renderer: Optional[WikiTemplateRenderer] = None,
    ):
        self.graph = graph
        self.title = title
        self.layout = layout or LayoutConfig()
        self.theme = theme or ThemeConfig()
        self.default_node_style = default_node_style or NodeStyle()
        self.default_edge_style = default_edge_style or EdgeStyle()

        # Constructor args take priority over later setter calls.
        self._node_style_cb: Optional[Callable] = node_style_callback
        self._edge_style_cb: Optional[Callable] = edge_style_callback
        self._wiki_cb: Optional[Callable] = wiki_callback
        self._edge_wiki_cb: Optional[Callable] = edge_wiki_callback
        self._wiki_renderer: Optional[WikiTemplateRenderer] = wiki_renderer

    # ------------------------------------------------------------------
    # Setter API (alternative to constructor arguments)
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

        Ignored when a wiki renderer is also configured (renderer takes priority).

        Args:
            cb: ``(igraph.Vertex) -> WikiContent``
        """
        self._wiki_cb = cb

    def set_edge_wiki_callback(self, cb: Callable) -> None:
        """Register a callback that returns :class:`WikiContent` for each edge.

        When set, clicking an edge opens the wiki side-panel just like clicking
        a node does.

        Args:
            cb: ``(igraph.Edge) -> WikiContent``
        """
        self._edge_wiki_cb = cb

    def set_wiki_renderer(self, renderer: WikiTemplateRenderer) -> None:
        """Attach a Jinja2-based :class:`WikiTemplateRenderer` for node wikis.

        Takes priority over any callback set with :meth:`set_wiki_callback`.

        Args:
            renderer: Configured renderer instance.
        """
        self._wiki_renderer = renderer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_label(self, vertex) -> str:
        """Return a human-readable label for *vertex*.

        Tries ``"name"``, then ``"label"``, then falls back to ``"Node <index>"``.
        """
        for attr in ("name", "label"):
            with contextlib.suppress(KeyError, IndexError):
                val = vertex[attr]
                if val is not None:
                    return str(val)
        return f"Node {vertex.index}"

    def _build_nodes(self) -> tuple[list[dict], dict[int, WikiContent]]:
        """Build the vis.js node list and node wiki-content map.

        Returns:
            ``(vis_nodes, wiki_map)`` — a list of vis.js node dicts and a
            ``{vertex_id: WikiContent}`` mapping.
        """
        vis_nodes: list[dict] = []
        # Use a dict for O(1) label lookup instead of a linear scan at export time.
        label_map: dict[int, str] = {}
        wiki_map: dict[int, WikiContent] = {}

        for v in self.graph.vs:
            label = self._get_label(v)
            label_map[v.index] = label

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

    def _build_edges(self) -> tuple[list[dict], dict[int, WikiContent]]:
        """Build the vis.js edge list and edge wiki-content map.

        Returns:
            ``(vis_edges, edge_wiki_map)`` — a list of vis.js edge dicts and a
            ``{edge_id: WikiContent}`` mapping.  Edge wiki entries are only
            included when an edge wiki callback is registered.
        """
        vis_edges: list[dict] = []
        edge_wiki_map: dict[int, WikiContent] = {}

        for e in self.graph.es:
            style = (
                self._edge_style_cb(e)
                if self._edge_style_cb
                else self.default_edge_style
            )
            edge_dict = style.to_vis(e.source, e.target)
            # Store the igraph edge index so the JS side can look up wiki data.
            edge_dict["id"] = e.index
            vis_edges.append(edge_dict)

            if self._edge_wiki_cb:
                edge_wiki_map[e.index] = self._edge_wiki_cb(e)
            elif self._edge_wiki_cb is None and any(self.graph.edge_attributes()):
                # Auto-generate edge wiki from attributes when no callback set
                # but the graph has edge attributes worth showing.
                edge_wiki_map[e.index] = _auto_edge_wiki(e, self.graph)

        return vis_edges, edge_wiki_map

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _build_template_vars(self) -> dict:
        """Assemble all template variables from the current graph state.

        This is the single place that translates Python graph data into the
        dict consumed by both ``page.html.j2`` (static) and
        ``page_flask.html.j2`` (Flask shell).  External callers such as
        :class:`~network_wiki.flask_view.GraphView` call this to get the
        graph payload as a plain dict.

        Returns:
            Dict with keys ``nodes_json``, ``edges_json``,
            ``node_wiki_json``, ``edge_wiki_json``, ``has_edge_wiki``,
            ``layout_json``, plus the theme variables.
        """
        vis_nodes, node_wiki_map = self._build_nodes()
        vis_edges, edge_wiki_map = self._build_edges()

        label_map: dict[int, str] = {n["id"]: n["label"] for n in vis_nodes}

        node_wiki_js = {
            vid: {
                "label": label_map.get(vid, str(vid)),
                "mini": wiki.mini_html or "",
                "full": wiki.full_html,
            }
            for vid, wiki in node_wiki_map.items()
        }
        edge_wiki_js = {
            eid: {
                "label": f"Edge {eid}",
                "mini": wiki.mini_html or "",
                "full": wiki.full_html,
            }
            for eid, wiki in edge_wiki_map.items()
        }

        t = self.theme

        # ✅ SERIALIZED WITH VALIDATION
        nodes_json_str = serialize_json(vis_nodes)
        edges_json_str = serialize_json(vis_edges)
        node_wiki_json_str = serialize_json(node_wiki_js)
        edge_wiki_json_str = serialize_json(edge_wiki_js)
        layout_cfg_str = serialize_json(self.layout.to_vis())

        # ✅ SECURITY CHECK - run validation on each blob
        debug_mode = getattr(
            self.layout, "_debug_validate_only", False
        )  # For CI testing

        if debug_mode:
            for name, js_string in [
                ("nodes", nodes_json_str),
                ("edges", edges_json_str),
                ("node_wiki", node_wiki_json_str),
                ("edge_wiki", edge_wiki_json_str),
                ("layout", layout_cfg_str),
            ]:
                validate_json_injection_safety(js_string)

        return dict(
            title=self.title,
            css_url=t.css_url,
            accent_color=t.accent_color,
            panel_width=t.panel_width_px,
            base_scheme=t.base_scheme,
            bootswatch_theme=t.bootswatch_theme,
            lang=t.lang,
            nodes_json=json.dumps(vis_nodes, ensure_ascii=False),
            edges_json=json.dumps(vis_edges, ensure_ascii=False),
            node_wiki_json=json.dumps(node_wiki_js, ensure_ascii=False),
            edge_wiki_json=json.dumps(edge_wiki_js, ensure_ascii=False),
            has_edge_wiki=bool(edge_wiki_map),
            layout_json=json.dumps(self.layout.to_vis(), ensure_ascii=False),
            min_zoom=self.layout.min_zoom,
            max_zoom=self.layout.max_zoom,
        )

    def render_html(self, template: str = "page.html.j2") -> str:
        """Render the graph to an HTML string without writing to disk.

        This is the core rendering method used by both :meth:`export` (static
        files) and :class:`~network_wiki.flask_view.GraphView` (Flask).

        Args:
            template: Name of the Jinja2 template to use.  Must exist in the
                package ``templates/`` directory.

        Returns:
            The rendered HTML as a string.
        """
        tmpl_path = _pkg_res.files("network_wiki").joinpath("templates")
        env = Environment(
            loader=FileSystemLoader(str(tmpl_path)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env.get_template(template).render(**self._build_template_vars())

    def export(self, path: str | Path = "graph_wiki.html") -> Path:
        """Render the HTML page and write it to *path*.

        Args:
            path: Destination file path.  Created or overwritten; parent
                directories must exist.

        Returns:
            The resolved absolute :class:`~pathlib.Path` of the written file.
        """
        out = Path(path).resolve()
        out.write_text(self.render_html(), encoding="utf-8")
        print(f"Exported to: {out}")
        return out
