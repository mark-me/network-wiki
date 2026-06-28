"""Wiki content dataclasses and Jinja2-based template rendering."""

from __future__ import annotations

import html as html_mod
import importlib.resources as _pkg_res
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

try:
    from jinja2 import (
        ChoiceLoader,
        DictLoader,
        Environment,
        FileSystemLoader,
        StrictUndefined,
        Undefined,
        select_autoescape,
    )
    _JINJA2_AVAILABLE = True
except ImportError:
    _JINJA2_AVAILABLE = False


@dataclass
class WikiContent:
    """HTML content for a single node's wiki.

    Args:
        mini_html: HTML shown in the collapsible side-panel (compact view).
            When ``None`` the exporter auto-generates content from vertex
            attributes.
        full_html: HTML shown in the full-screen modal.
            When ``None`` the "Full wiki" button is hidden for that node.
    """

    mini_html: Optional[str] = None
    full_html: Optional[str] = None


class WikiTemplateRenderer:
    """Render mini- and full-wiki HTML via Jinja2 templates.

    Every template receives the following context variables:

    ============== ===========================================================
    ``v``          The ``igraph.Vertex`` object.
    ``attrs``      Dict of all vertex attributes: ``{name: value}``.
    ``label``      Display name of the node (``str``).
    ``index``      Vertex index (``int``).
    ``n_in``       Number of incoming edges (``int``).
    ``n_out``      Number of outgoing edges (``int``).
    ``neighbours`` Names of all neighbouring nodes (``list[str]``).
    ``graph``      The full ``igraph.Graph`` object.
    ============== ===========================================================

    Additional keys supplied via ``global_context`` are available in every
    template.

    **Template resolution order** (first match wins):

    1. Per-type file   – ``*_template_files_by_type``
    2. Per-type inline – ``*_templates_by_type``
    3. Default file    – ``*_template_file``
    4. Default inline  – ``*_template``
    5. Bundled package fallback (``mini_default.html.j2`` / ``full_default.html.j2``)

    Args:
        template_dir: Directory containing user-supplied ``.html.j2`` files.
            When ``None``, only inline strings and package defaults are used.
        mini_template: Inline Jinja2 string for the mini-wiki (side-panel).
        full_template: Inline Jinja2 string for the full-wiki (modal).
        mini_template_file: Filename (relative to *template_dir*) for the
            mini-wiki template.
        full_template_file: Filename (relative to *template_dir*) for the
            full-wiki template.
        type_attr: Vertex attribute used to select per-type templates
            (default ``"type"``).
        mini_templates_by_type: Inline mini-templates keyed by type string.
        full_templates_by_type: Inline full-templates keyed by type string.
        mini_template_files_by_type: Filenames of mini-templates keyed by type.
        full_template_files_by_type: Filenames of full-templates keyed by type.
        global_context: Extra variables available in every template.
        undefined_strict: When ``True``, Jinja2 raises on unknown variables.
            Recommended during development.

    Example::

        renderer = WikiTemplateRenderer(
            template_dir="templates/wiki",
            full_template_file="full_default.html.j2",
            full_template_files_by_type={
                "pipeline": "full_pipeline.html.j2",
            },
            global_context={"project": "ETL v2"},
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
                "Jinja2 is required for WikiTemplateRenderer. "
                "Install it with: pip install jinja2"
            )

        self.type_attr = type_attr
        self.global_context = global_context or {}

        # Loader chain: user files → inline strings → bundled package templates.
        loaders = []

        if template_dir is not None:
            self._template_dir = Path(template_dir).resolve()
            loaders.append(FileSystemLoader(str(self._template_dir)))
        else:
            self._template_dir = None

        self._inline_store: dict[str, str] = {}
        loaders.append(DictLoader(self._inline_store))

        # importlib.resources works both when installed (pip) and in-place (src layout).
        _pkg_templates = _pkg_res.files("network_wiki").joinpath("templates")
        loaders.append(FileSystemLoader(str(_pkg_templates)))

        self._env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(["html", "j2"]),
            undefined=StrictUndefined if undefined_strict else Undefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self._mini_inline: Optional[str] = None
        self._full_inline: Optional[str] = None
        self._mini_file: Optional[str] = mini_template_file
        self._full_file: Optional[str] = full_template_file
        self._mini_by_type: dict[str, str] = mini_templates_by_type or {}
        self._full_by_type: dict[str, str] = full_templates_by_type or {}
        self._mini_files_by_type: dict[str, str] = mini_template_files_by_type or {}
        self._full_files_by_type: dict[str, str] = full_template_files_by_type or {}

        if mini_template:
            self._inline_store["__mini_default__"] = mini_template
            self._mini_inline = "__mini_default__"
        if full_template:
            self._inline_store["__full_default__"] = full_template
            self._full_inline = "__full_default__"
        for vtype, tmpl in self._mini_by_type.items():
            self._inline_store[f"__mini_{vtype}__"] = tmpl
        for vtype, tmpl in self._full_by_type.items():
            self._inline_store[f"__full_{vtype}__"] = tmpl

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_context(self, vertex, graph) -> dict:
        """Assemble the full Jinja2 context dict for *vertex*."""
        attrs: dict = {}
        for attr in graph.vertex_attributes():
            try:
                attrs[attr] = vertex[attr]
            except (KeyError, IndexError):
                pass

        label = _vertex_label(vertex, vertex.index)

        n_in = len(graph.predecessors(vertex.index))
        n_out = len(graph.successors(vertex.index))

        neighbours: list[str] = [
            _vertex_label(graph.vs[i], i)
            for i in graph.neighbors(vertex.index)
        ]

        ctx = {
            "v": vertex,
            "attrs": attrs,
            "label": label,
            "index": vertex.index,
            "n_in": n_in,
            "n_out": n_out,
            "neighbours": neighbours,
            "graph": graph,
        }
        ctx.update(self.global_context)
        return ctx

    def _resolve(
        self,
        vtype: Optional[str],
        by_type_inline: dict[str, str],
        by_type_files: dict[str, str],
        default_inline: Optional[str],
        default_file: Optional[str],
        prefix: str,
        package_fallback: str,
    ) -> str:
        """Return the template name to use, in priority order.

        Always returns at least the package fallback name.
        """
        if vtype:
            if vtype in by_type_inline:
                return f"__{prefix}_{vtype}__"
            if vtype in by_type_files:
                return by_type_files[vtype]
        if default_inline:
            return default_inline
        if default_file:
            return default_file
        return package_fallback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, vertex, graph) -> WikiContent:
        """Render mini- and full-wiki HTML for *vertex*.

        Args:
            vertex: ``igraph.Vertex`` to render wiki content for.
            graph: The parent ``igraph.Graph``.

        Returns:
            A :class:`WikiContent` with ``mini_html`` and ``full_html`` set.
        """
        ctx = self._build_context(vertex, graph)
        vtype = ctx["attrs"].get(self.type_attr)

        mini_name = self._resolve(
            vtype,
            self._mini_by_type, self._mini_files_by_type,
            self._mini_inline, self._mini_file,
            "mini", "mini_default.html.j2",
        )
        full_name = self._resolve(
            vtype,
            self._full_by_type, self._full_files_by_type,
            self._full_inline, self._full_file,
            "full", "full_default.html.j2",
        )

        return WikiContent(
            mini_html=self._env.get_template(mini_name).render(**ctx),
            full_html=self._env.get_template(full_name).render(**ctx),
        )


# ---------------------------------------------------------------------------
# Helpers used by GraphExporter when no wiki renderer/callback is set
# ---------------------------------------------------------------------------

def _vertex_label(vertex, fallback_index: int) -> str:
    """Return the display label for *vertex*, falling back to ``"Node <index>"``."""
    for key in ("name", "label"):
        try:
            val = vertex[key]
            if val is not None:
                return str(val)
        except (KeyError, IndexError):
            pass
    return f"Node {fallback_index}"


def _auto_wiki(vertex, graph) -> WikiContent:
    """Auto-generate :class:`WikiContent` from vertex attributes.

    Used when neither a :class:`WikiTemplateRenderer` nor a wiki callback is
    configured on the exporter.
    """
    attrs = {k: vertex[k] for k in graph.vertex_attributes() if vertex[k] is not None}
    label = next(
        (str(attrs[k]) for k in ("name", "label") if attrs.get(k) is not None),
        f"Node {vertex.index}",
    )
    n_in = len(graph.predecessors(vertex.index))
    n_out = len(graph.successors(vertex.index))

    attr_boxes = "".join(
        f'<div class="nw-attr-box">'
        f'<div class="nw-attr-label">{html_mod.escape(str(k))}</div>'
        f'<div class="nw-attr-value">{html_mod.escape(str(v))}</div>'
        f'</div>'
        for k, v in attrs.items()
    )
    mini = (
        f'<div class="nw-mini-wiki">'
        f'<div class="nw-node-type">Node {vertex.index}</div>'
        f'<div class="nw-attr-grid">{attr_boxes}</div>'
        f'<div class="nw-connections">'
        f'Incoming: <strong>{n_in}</strong>&nbsp;|&nbsp;Outgoing: <strong>{n_out}</strong>'
        f'</div></div>'
    )

    neighbour_ids = graph.neighbors(vertex.index)
    nbr_items = "".join(
        f"<li>{html_mod.escape(_vertex_label(graph.vs[i], i))}</li>"
        for i in neighbour_ids
    )
    full_rows = "".join(
        f"<tr><td>{html_mod.escape(str(k))}</td><td>{html_mod.escape(str(v))}</td></tr>"
        for k, v in attrs.items()
    )
    full = (
        f"<h2>{html_mod.escape(label)}</h2>"
        f"<table class='table table-sm table-striped'>"
        f"<thead><tr><th>Attribute</th><th>Value</th></tr></thead>"
        f"<tbody>{full_rows}</tbody></table>"
        f"<h5 class='mt-3'>Connected nodes</h5>"
        f"<ul>{nbr_items or '<li><em>None</em></li>'}</ul>"
    )
    return WikiContent(mini_html=mini, full_html=full)


def _auto_edge_wiki(edge, graph) -> WikiContent:
    """Auto-generate :class:`WikiContent` for an edge from its attributes.

    Used when no edge wiki callback is configured but the graph has edge
    attributes worth displaying.

    Args:
        edge: The ``igraph.Edge`` to generate wiki content for.
        graph: The parent ``igraph.Graph``.

    Returns:
        A :class:`WikiContent` with simple attribute table mini- and full-HTML.
    """
    attrs = {k: edge[k] for k in graph.edge_attributes() if edge[k] is not None}
    src_label = _vertex_label(graph.vs[edge.source], edge.source)
    tgt_label = _vertex_label(graph.vs[edge.target], edge.target)

    attr_boxes = "".join(
        f'<div class="nw-attr-box">'
        f'<div class="nw-attr-label">{html_mod.escape(str(k))}</div>'
        f'<div class="nw-attr-value">{html_mod.escape(str(v))}</div>'
        f'</div>'
        for k, v in attrs.items()
    )
    mini = (
        f'<div class="nw-mini-wiki">'
        f'<div class="nw-node-type">Edge {edge.index}</div>'
        f'<div class="nw-node-desc">{html_mod.escape(src_label)} &rarr; {html_mod.escape(tgt_label)}</div>'
        f'<div class="nw-attr-grid">{attr_boxes}</div>'
        f'</div>'
    )

    full_rows = "".join(
        f"<tr><td>{html_mod.escape(str(k))}</td><td>{html_mod.escape(str(v))}</td></tr>"
        for k, v in attrs.items()
    )
    full = (
        f"<h2>Edge {edge.index}: {html_mod.escape(src_label)} &rarr; {html_mod.escape(tgt_label)}</h2>"
        f"<table class='table table-sm table-striped'>"
        f"<thead><tr><th>Attribute</th><th>Value</th></tr></thead>"
        f"<tbody>{full_rows or '<tr><td colspan=2><em>No attributes</em></td></tr>'}</tbody></table>"
    )
    return WikiContent(mini_html=mini, full_html=full)
