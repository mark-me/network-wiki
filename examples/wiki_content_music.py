"""
example_wiki_content.py
========================
Demonstrates every way to add wiki content to a network-wiki graph:

  1. Node wikis via WikiTemplateRenderer with per-type template FILES
     (templates/music/full_producer.html.j2, full_engineer.html.j2)
  2. Node wikis via per-type INLINE templates (for the "session_musician" type)
  3. Edge wikis via a plain Python callback (no templates at all)
  4. The built-in automatic wiki fallback (for any node type without an
     explicit template — try removing a type from the renderer to see it
     kick in)

The graph is a small music album production team: producers → engineers → session musicians,
with edges carrying a "recorded_date" and a "role_in_session" label.

Run with:
    python examples/example_wiki_content.py
    # Opens examples/music_album_production_wiki.html in your browser
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
# Graph: a music album production team
# ---------------------------------------------------------------------------

g = ig.Graph(directed=True)
g.add_vertices(7)

g.vs["name"] = [
    "Maya Rodriguez",      # 0 — producer
    "Alex Kim",            # 1 — mixing engineer
    "Sophie Laurent",      # 2 — mastering engineer
    "Javier Moreno",       # 3 — session musician
    "Emma Watson-Brown",   # 4 — session musician
    "Taro Suzuki",         # 5 — session musician
    "Nina Petrova",        # 6 — session musician (no template — uses auto-fallback)
]
g.vs["type"] = [
    "producer", "mixing_engineer", "mastering_engineer",
    "musician", "musician", "musician", "musician",
]
g.vs["title"] = [
    "Executive Producer", "Mixing Engineer", "Mastering Engineer",
    "Lead Guitarist", "Violinist", "Drummer", "Vocal Arranger",
]
g.vs["album"] = [
    "Midnight Echoes", "Midnight Echoes", "Midnight Echoes",
    "Midnight Echoes", "Midnight Echoes", "Midnight Echoes", "Midnight Echoes",
]
g.vs["bio"] = [
    "Oversaw the creative vision and production across all album sessions.",
    "Blended vocals and instrumentation into a cohesive sonic landscape.",
    "Applied final polish and ensured commercial-grade audio quality.",
    "Delivered signature guitar riffs and lead melodies throughout the album.",
    "Added orchestral textures and string arrangements to key tracks.",
    "Provided rhythmic foundation and dynamic percussion layers.",
    "Crafted vocal harmonies and choir arrangements for ballad tracks.",
]
g.vs["studio_location"] = [
    "Abbey Road Studios, London", "Electric Lady Studios, NYC", "Sterling Sound, NYC",
    "Live Remote", "Abbey Road Studios, London", "Air Studios, London", "Remote",
]
g.vs["sessions_count"] = [8, 12, 3, 4, 5, 6, 2]

g.add_edges([
    (1, 0),  # Alex → Maya
    (2, 0),  # Sophie → Maya
    (3, 1),  # Javier → Alex
    (4, 1),  # Emma → Alex
    (5, 2),  # Taro → Sophie
    (6, 2),  # Nina → Sophie
])
g.es["since"] = ["2021-03", "2022-01", "2023-06", "2023-09", "2022-11", "2023-02"]
g.es["relationship"] = ["contributes to session"] * 6

# ---------------------------------------------------------------------------
# Visual style
# ---------------------------------------------------------------------------

TYPE_COLOR = {
    "producer":       "#6f42c1",
    "mixing_engineer": "#0d6efd",
    "mastering_engineer": "#fd7e14",
    "musician":       "#20c997",
}
TYPE_SHAPE = {
    "producer":        "star",
    "mixing_engineer": "diamond",
    "mastering_engineer": "triangle_up",
    "musician":        "dot",
}

def node_style(v) -> NodeStyle:
    t = v["type"]
    return NodeStyle(
        shape=TYPE_SHAPE.get(t, "dot"),
        color=TYPE_COLOR.get(t, "#888"),
        size=30 if t == "producer" else (24 if "engineer" in t else 18),
        font=NodeFont(color="#ffffff", bold=(t == "producer")),
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
#   - "producer" and "mixing_engineer" use template FILES (templates/music/)
#   - "musician" uses an INLINE template (defined right here)
#   - anything else falls back to the automatic wiki
# ---------------------------------------------------------------------------

MUSICIAN_MINI = """
<div class="nw-mini-wiki">
  <div class="nw-node-type">{{ type_value | upper }}</div>
  <div class="nw-node-desc">{{ attrs.title }}</div>
  <div class="nw-attr-grid">
    <div class="nw-attr-box">
      <div class="nw-attr-label">Studio</div>
      <div class="nw-attr-value">{{ attrs.studio_location }}</div>
    </div>
    <div class="nw-attr-box">
      <div class="nw-attr-label">Sessions</div>
      <div class="nw-attr-value">{{ attrs.sessions_count }}</div>
    </div>
  </div>
</div>
"""

MUSICIAN_FULL = """
<h2>{{ label }}</h2>
<span class="badge text-bg-info mb-2">{{ attrs.title }}</span>
<p class="lead">{{ attrs.bio }}</p>
<table class="table table-sm table-striped">
  <tr><td>Album</td><td>{{ attrs.album }}</td></tr>
  <tr><td>Studio</td><td>{{ attrs.studio_location }}</td></tr>
  <tr><td>Total Sessions</td><td>{{ attrs.sessions_count }}</td></tr>
</table>
{% if neighbours %}
<h3>Contributes To Session With</h3>
<ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
{% endif %}
"""

node_wiki_renderer = WikiTemplateRenderer(
    template_dir="examples/templates/music",
    full_template_files_by_type={
        "producer":           "full_producer.html.j2",
        "mixing_engineer":    "full_mixer.html.j2",
    },
    mini_template_files_by_type={
        "producer":           "mini_producer.html.j2",
        # "mixing_engineer" has no dedicated mini template → falls through to bundled default
    },
    mini_templates_by_type={"musician": MUSICIAN_MINI},
    full_templates_by_type={"musician": MUSICIAN_FULL},
    global_context={"album_project": "Midnight Echoes"},
    undefined_strict=False,
)

# ---------------------------------------------------------------------------
# Edge wikis — plain Python callback, no Jinja2 involved.
# ---------------------------------------------------------------------------

def edge_wiki(e) -> WikiContent:
    src = g.vs[e.source]["name"]
    tgt = g.vs[e.target]["name"]
    mini = f"""
    <div class="nw-mini-wiki">
      <div class="nw-node-type">SESSION CONTRIBUTION</div>
      <div class="nw-node-desc">{tgt} ← {src}</div>
      <div class="nw-attr-grid">
        <div class="nw-attr-box">
          <div class="nw-attr-label">First Session</div>
          <div class="nw-attr-value">{e['since']}</div>
        </div>
      </div>
    </div>
    """
    full = f"""
    <h2>{tgt} ← {src}</h2>
    <span class="badge text-bg-secondary mb-2">{e['relationship']}</span>
    <table class="table table-sm table-striped">
      <tr><td>First Recorded</td><td>{e['since']}</td></tr>
      <tr><td>Role</td><td>{e['relationship']}</td></tr>
    </table>
    """
    return WikiContent(mini_html=mini, full_html=full)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

exporter = GraphExporter(
    g,
    title="Midnight Echoes — Album Production Team",
    theme=ThemeConfig(bootswatch_theme="darkly"),
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

exporter.export("examples/music_album_production_wiki.html")