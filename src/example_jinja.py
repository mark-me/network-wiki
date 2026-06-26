"""
example_jinja.py
================
Demonstreert WikiTemplateRenderer met externe .j2-bestanden én inline templates.
Draai met: python example_jinja.py
"""

import igraph as ig
from igraph_wiki_exporter import (
    GraphExporter, WikiTemplateRenderer,
    NodeStyle, NodeFont, NodeColor,
    EdgeStyle, EdgeColor, EdgeArrows,
    LayoutConfig, ThemeConfig,
)

# ─── Graph (zelfde als in example_usage.py) ───────────────────────────────────

g = ig.Graph(directed=True)
g.add_vertices(6)
g.vs["name"]        = ["ETL Pipeline", "Bronmodel A", "Bronmodel B", "Bronmodel C", "DWH Feit", "DWH Dimensie"]
g.vs["type"]        = ["pipeline",     "source",      "source",      "source",      "target",   "target"]
g.vs["description"] = [
    "Centrale ETL-pipeline die ruwe brondata transformeert naar het datawarehouse.",
    "SAP CRM-bronmodel met klant- en contractdata.",
    "ERP-exports met financiële transacties via SFTP.",
    "REST API-feeds met real-time productdata.",
    "Centrale feitentabel in het datawarehouse.",
    "Klantdimensie met SCD Type 2 historisering.",
]
g.vs["status"]  = ["actief"] * 6
g.vs["owner"]   = ["Data Engineering", "SAP Team", "Finance", "IT", "Data Engineering", "Data Engineering"]
g.vs["weight"]  = [3, 1, 1, 1, 2, 2]

g.add_edges([(1, 0), (2, 0), (3, 0), (0, 4), (0, 5)])
g.es["critical"] = [True, False, True, True, False]
g.es["volume"]   = [800_000, 350_000, 50_000, 1_200_000, 1_200_000]


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIE A — Externe .j2-bestanden
# ═══════════════════════════════════════════════════════════════════════════════
# De templates staan in templates/wiki/:
#   mini_default.html.j2          → mini-wiki voor alle types
#   full_default.html.j2          → full-wiki fallback
#   full_pipeline.html.j2         → full-wiki specifiek voor type "pipeline"
#   full_source.html.j2           → full-wiki specifiek voor type "source"

renderer_extern = WikiTemplateRenderer(
    template_dir="templates/wiki",

    # Standaard templates (gebruikt als er geen per-type template is)
    mini_template_file="mini_default.html.j2",
    full_template_file="full_default.html.j2",

    # Per-type full-wiki templates (overschrijven de standaard)
    full_template_files_by_type={
        "pipeline": "full_pipeline.html.j2",
        "source":   "full_source.html.j2",
    },

    # Globale context: elke template heeft toegang tot {{ project }}
    global_context={"project": "ETL Landschap v2.1"},

    # Gooi een duidelijke fout als een template-variabele ontbreekt
    undefined_strict=True,
)


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIE B — Inline Jinja2-templatestrings (geen bestanden nodig)
# ═══════════════════════════════════════════════════════════════════════════════

MINI_INLINE = """
<div class="mini-wiki">
  <div class="node-type">{{ attrs.get('type', 'node') | upper }}</div>
  {% if attrs.description is defined %}
  <div class="node-desc">{{ attrs.description }}</div>
  {% endif %}
  <div class="attr-grid">
    <div class="attr-box">
      <div class="attr-label">Status</div>
      <div class="attr-value">{{ attrs.get('status', '—') }}</div>
    </div>
    <div class="attr-box">
      <div class="attr-label">Eigenaar</div>
      <div class="attr-value">{{ attrs.get('owner', '—') }}</div>
    </div>
    <div class="attr-box">
      <div class="attr-label">⬅️ In</div>
      <div class="attr-value">{{ n_in }}</div>
    </div>
    <div class="attr-box">
      <div class="attr-label">➡️ Uit</div>
      <div class="attr-value">{{ n_out }}</div>
    </div>
  </div>
</div>
"""

FULL_INLINE_DEFAULT = """
<h2>{{ label }}</h2>
{% if attrs.description is defined %}
<p>{{ attrs.description }}</p>
{% endif %}
<h3>Attributen</h3>
<table>
  <tr><th>Eigenschap</th><th>Waarde</th></tr>
  {% for key, val in attrs.items() if key != 'name' and val is not none %}
  <tr><td>{{ key }}</td><td>{{ val }}</td></tr>
  {% endfor %}
</table>
{% if neighbours %}
<h3>Buren</h3>
<ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
{% endif %}
"""

FULL_INLINE_TARGET = """
<h2>🏁 {{ label }}</h2>
<p>{{ attrs.description | default('') }}</p>
<h3>Target-details</h3>
<table>
  <tr><th>Eigenschap</th><th>Waarde</th></tr>
  <tr><td>Eigenaar</td><td>{{ attrs.get('owner', '—') }}</td></tr>
  <tr><td>Inkomende bronnen</td><td>{{ n_in }}</td></tr>
</table>
<p><span class="tag">DWH</span> <span class="tag">{{ project }}</span></p>
"""

renderer_inline = WikiTemplateRenderer(
    mini_template=MINI_INLINE,
    full_template=FULL_INLINE_DEFAULT,
    full_templates_by_type={
        "target": FULL_INLINE_TARGET,
    },
    global_context={"project": "ETL Landschap v2.1"},
    undefined_strict=False,  # bij inline templates handiger om fouten te slikken
)


# ─── Kies renderer (schakel tussen A en B) ────────────────────────────────────

GEBRUIK_EXTERN = True    # False = inline templates

renderer = renderer_extern if GEBRUIK_EXTERN else renderer_inline


# ─── Stijl-callbacks (ongewijzigd) ────────────────────────────────────────────

COLOR_MAP = {"pipeline": "#e94560", "source": "#a8dadc", "target": "#f5a623"}
SHAPE_MAP = {"pipeline": "diamond", "source": "box", "target": "ellipse"}

def node_style(v):
    base = COLOR_MAP.get(v["type"], "#888888")
    return NodeStyle(
        shape=SHAPE_MAP.get(v["type"], "box"),
        size=20 + v["weight"] * 8,
        color=base,
        border_width=3 if v["type"] == "pipeline" else 2,
        font=NodeFont(color="#ffffff", size=14, bold=(v["type"] == "pipeline")),
        shadow=(v["type"] == "pipeline"),
        tooltip=f"{v['name']} — {v['owner']}",
        group=v["type"],
    )

def edge_style(e):
    is_critical = e["critical"]
    vol = e["volume"] or 0
    return EdgeStyle(
        width=1 + min(vol / 300_000, 5),
        color=EdgeColor(color="#e94560" if is_critical else "#4a90d9", highlight="#fff", hover="#fff"),
        dashes=not is_critical,
        arrows=EdgeArrows(to_enabled=True, to_scale=0.8),
        smooth_type="cubicBezier",
        label=f"{vol // 1000}K" if vol else None,
        font_color="#a8dadc",
        font_size=10,
    )


# ─── Exporteren ───────────────────────────────────────────────────────────────

exporter = GraphExporter(
    graph=g,
    title="ETL Landschap — Jinja2 Wiki",
    layout=LayoutConfig(
        solver="forceAtlas2Based",
        gravity=-80,
        spring_length=250,
        stabilization_iterations=200,
        navigation_buttons=True,
    ),
    theme=ThemeConfig(panel_width_px=380),
)

exporter.set_node_style_callback(node_style)
exporter.set_edge_style_callback(edge_style)
exporter.set_wiki_renderer(renderer)          # ← Jinja2-renderer koppelen

exporter.export("etl_jinja_wiki.html")
