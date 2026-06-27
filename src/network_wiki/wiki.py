"""Wiki-inhoud en Jinja2-template rendering."""

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
    """
    Wiki-inhoud voor één node.

    Parameters
    ----------
    mini_html:
        HTML voor het sidepanel (compact overzicht).
        Als ``None``: automatisch gegenereerd op basis van vertex-attributen.
    full_html:
        HTML voor de volledige wiki-modal.
        Als ``None``: de "Volledige wiki"-knop wordt verborgen.
    """
    mini_html: Optional[str] = None
    full_html: Optional[str] = None


class WikiTemplateRenderer:
    """
    Rendert mini- en full-wiki HTML via Jinja2-templates.

    Elke template ontvangt de volgende context-variabelen:

    =========== ============================================================
    ``v``       igraph Vertex-object
    ``attrs``   dict van alle vertex-attributen ``{naam: waarde}``
    ``label``   display-naam van de node (str)
    ``index``   vertex-index (int)
    ``n_in``    aantal inkomende edges (int)
    ``n_out``   aantal uitgaande edges (int)
    ``neighbours`` lijst van namen van alle buurknopen (list[str])
    ``graph``   de volledige igraph.Graph
    =========== ============================================================

    Aanvullende sleutels die je via ``global_context`` meegeeft zijn ook
    beschikbaar in elke template.

    Templateresolutie-volgorde (eerste match wint):

    1. Per-type bestand  via ``*_template_files_by_type``
    2. Per-type inline   via ``*_templates_by_type``
    3. Standaard bestand via ``*_template_file``
    4. Standaard inline  via ``*_template``
    5. Gebundeld package-standaard (``mini_default.html.j2`` / ``full_default.html.j2``)

    Parameters
    ----------
    template_dir:
        Map met externe ``.html.j2``-bestanden. Als ``None``, worden alleen
        inline-templates en package-standaarden gebruikt.
    mini_template:
        Inline Jinja2-templatestring voor de mini-wiki.
    full_template:
        Inline Jinja2-templatestring voor de full-wiki.
    mini_template_file:
        Bestandsnaam (relatief aan ``template_dir``) voor de mini-wiki template.
    full_template_file:
        Bestandsnaam (relatief aan ``template_dir``) voor de full-wiki template.
    type_attr:
        Vertex-attribuut dat het type bepaalt voor per-type templates (standaard ``"type"``).
    mini_templates_by_type:
        Inline mini-templates per type: ``{"source": "...", "target": "..."}``.
    full_templates_by_type:
        Inline full-templates per type: ``{"source": "...", "target": "..."}``.
    mini_template_files_by_type:
        Bestandsnamen van mini-templates per type.
    full_template_files_by_type:
        Bestandsnamen van full-templates per type.
    global_context:
        Extra variabelen beschikbaar in elke template.
    undefined_strict:
        Als ``True``: Jinja2 gooit een fout bij onbekende variabelen.
        Aanbevolen tijdens ontwikkeling.
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
                "Installeer via: pip install jinja2"
            )

        self.type_attr = type_attr
        self.global_context = global_context or {}

        # ── Loader-volgorde: gebruikersbestanden -> inline -> package-standaard ─
        loaders = []

        # 1. Gebruiker: externe map (hoogste prioriteit)
        if template_dir is not None:
            self._template_dir = Path(template_dir).resolve()
            loaders.append(FileSystemLoader(str(self._template_dir)))
        else:
            self._template_dir = None

        # 2. Gebruiker: inline strings
        self._inline_store: dict[str, str] = {}
        loaders.append(DictLoader(self._inline_store))

        # 3. Package: meegeleverde standaard-templates (laagste prioriteit)
        #    importlib.resources werkt zowel geinstalleerd (pip) als in-place.
        _pkg_templates = _pkg_res.files("network_wiki").joinpath("templates")
        loaders.append(FileSystemLoader(str(_pkg_templates)))

        self._env = Environment(
            loader=ChoiceLoader(loaders),
            autoescape=select_autoescape(["html", "j2"]),
            undefined=StrictUndefined if undefined_strict else Undefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # ── Template-registratie ──────────────────────────────────────────────
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

    # ── Context ───────────────────────────────────────────────────────────────

    def _build_context(self, vertex, graph) -> dict:
        """Stel de volledige template-context samen voor een vertex."""
        attrs = {}
        for attr in graph.vertex_attributes():
            try:
                attrs[attr] = vertex[attr]
            except (KeyError, IndexError):
                pass

        label = next(
            (str(attrs[k]) for k in ("name", "label") if attrs.get(k) is not None),
            f"Node {vertex.index}",
        )

        n_in = len(graph.predecessors(vertex.index))
        n_out = len(graph.successors(vertex.index))

        neighbours = []
        for i in graph.neighbors(vertex.index):
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

    # ── Template-resolutie ───────────────────────────────────────────────────

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
        """
        Bepaal de template-naam in prioriteitsvolgorde.
        Geeft altijd een naam terug (uiterlijk de package-fallback).
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

    # ── Publieke methode ──────────────────────────────────────────────────────

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



def _vertex_label(vertex, fallback_index: int) -> str:
    for key in ('name', 'label'):
        try:
            val = vertex[key]
            if val is not None:
                return str(val)
        except (KeyError, IndexError):
            pass
    return f'Node {fallback_index}'


def _auto_wiki(vertex, graph) -> WikiContent:
    """
    Genereer automatisch een WikiContent op basis van vertex-attributen.
    Wordt gebruikt als er geen renderer of callback is ingesteld.
    """
    attrs = {k: vertex[k] for k in graph.vertex_attributes()
             if vertex[k] is not None}
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
        f'Inkomend: <strong>{n_in}</strong> &nbsp;|&nbsp; Uitgaand: <strong>{n_out}</strong>'
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
        f"<thead><tr><th>Attribuut</th><th>Waarde</th></tr></thead>"
        f"<tbody>{full_rows}</tbody></table>"
        f"<h5 class='mt-3'>Verbonden nodes</h5>"
        f"<ul>{nbr_items or '<li><em>Geen</em></li>'}</ul>"
    )
    return WikiContent(mini_html=mini, full_html=full)
