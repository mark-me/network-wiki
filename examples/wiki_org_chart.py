"""
example_wiki_content.py
========================
Demonstrates every way to add wiki content to a network-wiki graph:

  1. Node wikis via WikiTemplateRenderer with per-type template FILES
     (templates/org/full_executive.html.j2, full_manager.html.j2)
  2. Node wikis via per-type INLINE templates (for the "contributor" type)
  3. Edge wikis via a plain Python callback (no templates at all)
  4. The built-in automatic wiki fallback (for any node type without an
     explicit template — try removing a type from the renderer to see it
     kick in)

The graph is a small company org chart: executives → managers → contributors,
with edges carrying a "since" date and a "relationship" label.

Run with:
    python examples/example_wiki_content.py
    # Opens examples/org_chart_wiki.html in your browser
"""

from __future__ import annotations

import igraph as ig
from network_wiki import (
    GraphExporter, NodeStyle, NodeFont,
    EdgeStyle, EdgeArrows,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig,
)

# ---------------------------------------------------------------------------
# Graph: a small org chart
# ---------------------------------------------------------------------------

g = ig.Graph(directed=True)
g.add_vertices(7)

g.vs["name"] = [
    "Avery Chen",      # 0 — executive
    "Jordan Patel",    # 1 — manager
    "Sam Okafor",      # 2 — manager
    "Riley Nakamura",  # 3 — contributor
    "Casey Lindqvist", # 4 — contributor
    "Drew Almeida",    # 5 — contributor
    "Quinn Forsberg",  # 6 — contributor (no template — uses auto-fallback)
]
g.vs["type"] = [
    "executive", "manager", "manager",
    "contributor", "contributor", "contributor", "contributor",
]
g.vs["title"] = [
    "VP of Engineering", "Engineering Manager", "Engineering Manager",
    "Senior Engineer", "Engineer", "Senior Engineer", "Designer",
]
g.vs["department"] = [
    "Engineering", "Platform Team", "Product Team",
    "Platform Team", "Platform Team", "Product Team", "Product Team",
]
g.vs["bio"] = [
    "Leads the engineering organisation across platform and product teams.",
    "Manages the platform team, focused on infrastructure and developer tooling.",
    "Manages the product team, focused on customer-facing features.",
    "Builds the core deployment pipeline and observability stack.",
    "Works on internal developer tooling and CI/CD.",
    "Owns the checkout and payments experience.",
    "Designs the product's visual language and component library.",
]
g.vs["location"] = [
    "San Francisco", "Remote", "Berlin",
    "Remote", "Remote", "Berlin", "Berlin",
]
g.vs["tenure_years"] = [6, 4, 3, 2, 1, 3, 2]

g.add_edges([
    (1, 0),  # Jordan → Avery
    (2, 0),  # Sam → Avery
    (3, 1),  # Riley → Jordan
    (4, 1),  # Casey → Jordan
    (5, 2),  # Drew → Sam
    (6, 2),  # Quinn → Sam
])
g.es["since"] = ["2021-03", "2022-01", "2023-06", "2023-09", "2022-11", "2023-02"]
g.es["relationship"] = ["reports to"] * 6

# ---------------------------------------------------------------------------
# Visual style
# ---------------------------------------------------------------------------

TYPE_COLOR = {
    "executive":   "#6f42c1",
    "manager":     "#0d6efd",
    "contributor": "#20c997",
}
TYPE_SHAPE = {
    "executive":   "star",
    "manager":     "diamond",
    "contributor": "dot",
}

def node_style(v) -> NodeStyle:
    t = v["type"]
    return NodeStyle(
        shape=TYPE_SHAPE.get(t, "dot"),
        color=TYPE_COLOR.get(t, "#888"),
        size=30 if t == "executive" else (24 if t == "manager" else 18),
        font=NodeFont(color="#ffffff", bold=(t == "executive")),
        tooltip=f"{v['name']} — {v['title']}",
        group=t,
    )

def edge_style(e) -> EdgeStyle:
    return EdgeStyle(
        width=1.5,
        color="#adb5bd",
        arrows=EdgeArrows(to_enabled=True, to_scale=0.6),
        smooth_type="cubicBezier",
    )

# ---------------------------------------------------------------------------
# Node wikis — mixed strategy:
#   - "executive" and "manager" use template FILES (templates/org/)
#   - "contributor" uses an INLINE template (defined right here)
#   - anything else (none in this graph) falls back to the automatic wiki
# ---------------------------------------------------------------------------

CONTRIBUTOR_MINI = """
<div class="nw-mini-wiki">
  <div class="nw-node-type">{{ type_value | upper }}</div>
  <div class="nw-node-desc">{{ attrs.title }}</div>
  <div class="nw-attr-grid">
    <div class="nw-attr-box">
      <div class="nw-attr-label">Department</div>
      <div class="nw-attr-value">{{ attrs.department }}</div>
    </div>
    <div class="nw-attr-box">
      <div class="nw-attr-label">Location</div>
      <div class="nw-attr-value">{{ attrs.location }}</div>
    </div>
  </div>
</div>
"""

CONTRIBUTOR_FULL = """
<h2>{{ label }}</h2>
<span class="badge text-bg-info mb-2">{{ attrs.title }}</span>
<p class="lead">{{ attrs.bio }}</p>
<table class="table table-sm table-striped">
  <tr><td>Department</td><td>{{ attrs.department }}</td></tr>
  <tr><td>Location</td><td>{{ attrs.location }}</td></tr>
  <tr><td>Tenure</td><td>{{ attrs.tenure_years }} years</td></tr>
</table>
{% if neighbours %}
<h3>Reports to</h3>
<ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
{% endif %}
"""

node_wiki_renderer = WikiTemplateRenderer(
    # type_attr defaults to "type" — matches g.vs["type"] above
    template_dir="examples/templates/org",
    full_template_files_by_type={
        "executive": "full_executive.html.j2",
        "manager":   "full_manager.html.j2",
    },
    mini_template_files_by_type={
        "executive": "mini_executive.html.j2",
        # "manager" has no dedicated mini template → falls through to the
        # bundled mini_default.html.j2, which renders all attributes
        # generically. This shows the resolution chain in action.
    },
    # "contributor" uses inline templates instead of files — both styles
    # can be mixed freely on the same renderer.
    mini_templates_by_type={"contributor": CONTRIBUTOR_MINI},
    full_templates_by_type={"contributor": CONTRIBUTOR_FULL},
    global_context={"company": "Acme Corp"},
    undefined_strict=False,
)

# ---------------------------------------------------------------------------
# Edge wikis — plain Python callback, no Jinja2 involved.
#
# Edge wikis use WikiContent directly rather than templates, which is often
# simpler when the content is short and doesn't need a templating language.
# ---------------------------------------------------------------------------

def edge_wiki(e) -> WikiContent:
    src = g.vs[e.source]["name"]
    tgt = g.vs[e.target]["name"]
    mini = f"""
    <div class="nw-mini-wiki">
      <div class="nw-node-type">REPORTING LINE</div>
      <div class="nw-node-desc">{src} → {tgt}</div>
      <div class="nw-attr-grid">
        <div class="nw-attr-box">
          <div class="nw-attr-label">Since</div>
          <div class="nw-attr-value">{e['since']}</div>
        </div>
      </div>
    </div>
    """
    full = f"""
    <h2>{src} → {tgt}</h2>
    <span class="badge text-bg-secondary mb-2">{e['relationship']}</span>
    <table class="table table-sm table-striped">
      <tr><td>Since</td><td>{e['since']}</td></tr>
      <tr><td>Relationship</td><td>{e['relationship']}</td></tr>
    </table>
    """
    return WikiContent(mini_html=mini, full_html=full)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

exporter = GraphExporter(
    g,
    title="Acme Corp — Org Chart",
    theme=ThemeConfig(),  # plain Bootstrap, so the light/dark toggle is shown
    layout=LayoutConfig(
        hierarchical=True,
        hierarchical_direction="UD",
        hierarchical_sort_method="directed",
        navigation_buttons=True,
    ),
    node_style_callback=node_style,
    edge_style_callback=edge_style,
    wiki_renderer=node_wiki_renderer,
    edge_wiki_callback=edge_wiki,
)

exporter.export("examples/org_chart_wiki.html")
