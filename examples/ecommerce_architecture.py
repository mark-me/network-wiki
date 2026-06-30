"""
example_generic.py
==================
Demonstrates network-wiki with a non-ETL graph: a small software architecture
diagram where nodes have a "layer" attribute instead of "type".

This example shows:
- Using type_attr to dispatch on any vertex attribute
- Generic bundled templates that adapt to any domain
- Per-type inline templates for domain-specific rendering
- Type-specific NodeStyle based on the "layer" attribute

Run with:
    python examples/example_generic.py
"""

import igraph as ig
from network_wiki import (
    GraphExporter, NodeStyle, NodeFont, EdgeStyle, EdgeArrows,
    WikiTemplateRenderer, WikiContent,
    LayoutConfig, ThemeConfig,
)

# ---------------------------------------------------------------------------
# Graph: software architecture (no ETL concepts)
# ---------------------------------------------------------------------------

g = ig.Graph(directed=True)
g.add_vertices(8)

g.vs["name"] = [
    "Mobile App",
    "Web Frontend",
    "API Gateway",
    "Auth Service",
    "Order Service",
    "Product Service",
    "PostgreSQL",
    "Redis Cache",
]
g.vs["layer"] = [          # <-- arbitrary domain attribute, not "type"
    "client",
    "client",
    "gateway",
    "service",
    "service",
    "service",
    "datastore",
    "datastore",
]
g.vs["description"] = [
    "React Native app for iOS and Android.",
    "React SPA served via CDN.",
    "Kong API Gateway — rate limiting, routing, auth.",
    "JWT-based authentication and authorisation.",
    "Handles order creation, fulfilment and tracking.",
    "Product catalogue, inventory and pricing.",
    "Primary relational database (PostgreSQL 15).",
    "In-memory cache for sessions and hot product data.",
]
g.vs["tech"] = [
    "React Native", "React / Vite", "Kong", "FastAPI",
    "FastAPI", "FastAPI", "PostgreSQL 15", "Redis 7",
]
g.vs["team"] = [
    "Mobile", "Frontend", "Platform", "Platform",
    "Orders", "Catalogue", "Data", "Data",
]

g.add_edges([
    (0, 2), (1, 2),           # clients → gateway
    (2, 3), (2, 4), (2, 5),   # gateway → services
    (4, 6), (5, 6),           # services → postgres
    (3, 7), (5, 7),           # services → redis
])
g.es["protocol"] = [
    "HTTPS", "HTTPS",
    "gRPC", "gRPC", "gRPC",
    "SQL", "SQL",
    "Redis protocol", "Redis protocol",
]
g.es["authenticated"] = [True, True, True, True, True, False, False, False, False]

# ---------------------------------------------------------------------------
# Visual style — keyed on "layer", not "type"
# ---------------------------------------------------------------------------

LAYER_COLOR = {
    "client":    "#4a90d9",
    "gateway":   "#e67e22",
    "service":   "#2ecc71",
    "datastore": "#9b59b6",
}
LAYER_SHAPE = {
    "client":    "ellipse",
    "gateway":   "diamond",
    "service":   "box",
    "datastore": "database",
}

def node_style(v) -> NodeStyle:
    layer = v["layer"]
    return NodeStyle(
        shape=LAYER_SHAPE.get(layer, "box"),
        color=LAYER_COLOR.get(layer, "#888"),
        size=28 if layer == "gateway" else 22,
        font=NodeFont(color="#ffffff", bold=(layer == "gateway")),
        shadow=(layer == "gateway"),
        tooltip=f"{v['name']} [{layer}] — {v['tech']}",
        group=layer,
    )

def edge_style(e) -> EdgeStyle:
    return EdgeStyle(
        width=2.0,
        color="#aaaaaa",
        dashes=not e["authenticated"],
        arrows=EdgeArrows(to_enabled=True, to_scale=0.7),
        label=e["protocol"],
        font_size=9,
        font_color="#888888",
        smooth_type="cubicBezier",
    )

# ---------------------------------------------------------------------------
# Wiki templates — use type_attr="layer" and type_value in templates
# ---------------------------------------------------------------------------

# The bundled mini_default.html.j2 uses {{ type_value }} generically,
# so it works for "layer" values without any modification.
#
# We add a per-layer full-wiki template only for services, to show
# domain-specific rendering without hardcoding ETL concepts.

FULL_SERVICE = """
<h2>{{ label }}</h2>
<span class="badge text-bg-success mb-2">{{ type_value | capitalize }}</span>
<p class="lead">{{ attrs.description }}</p>

<h3>Technical details</h3>
<table class="table table-sm table-striped">
  <thead><tr><th>Property</th><th>Value</th></tr></thead>
  <tbody>
  <tr><td>Technology</td><td>{{ attrs.tech | default('—') }}</td></tr>
  <tr><td>Team</td><td>{{ attrs.team | default('—') }}</td></tr>
  </tbody>
</table>

<h3>Connections</h3>
<table class="table table-sm">
  <tbody>
  <tr><td>Incoming</td><td><strong>{{ n_in }}</strong></td></tr>
  <tr><td>Outgoing</td><td><strong>{{ n_out }}</strong></td></tr>
  </tbody>
</table>

{% if neighbours %}
<h3>Connected components</h3>
<ul class="list-unstyled">
  {% for n in neighbours %}
  <li><i class="bi bi-diagram-3 me-1"></i>{{ n }}</li>
  {% endfor %}
</ul>
{% endif %}
"""

renderer = WikiTemplateRenderer(
    # Dispatch on "layer" instead of the default "type"
    type_attr="layer",

    # Per-layer inline full-wiki template (only for "service" nodes)
    full_templates_by_type={"service": FULL_SERVICE},

    # The bundled mini_default.html.j2 is generic — no override needed
    # The bundled full_default.html.j2 is the fallback for other layers

    global_context={"system": "E-commerce Platform"},
    undefined_strict=False,
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

exporter = GraphExporter(
    g,
    title="E-commerce Architecture",
    theme=ThemeConfig(bootswatch_theme="flatly", accent_color="#2ecc71"),
    layout=LayoutConfig(
        solver="forceAtlas2Based",
        gravity=-100,
        spring_length=220,
        stabilization_iterations=200,
        navigation_buttons=True,
    ),
    node_style_callback=node_style,
    edge_style_callback=edge_style,
    wiki_renderer=renderer,
)

exporter.export("examples/ecommerce_architecture.html")
