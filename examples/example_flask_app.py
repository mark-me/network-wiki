"""
example_flask_app.py
====================
Demonstrates network-wiki inside a Flask application.

Shows two patterns side by side:
  1. Static graph  — built once at startup, served on every request.
  2. Dynamic graph — rebuilt on every request (simulates live data from a
                     database or external API).

Run with:
    pip install flask
    python examples/example_flask_app.py

Then open:
    http://localhost:5000/graphs/          → redirects to first graph
    http://localhost:5000/graphs/arch/     → software architecture (static)
    http://localhost:5000/graphs/live/     → live graph (random, rebuilt each request)
"""

from __future__ import annotations

import random
import igraph as ig
from flask import Flask
from network_wiki import GraphExporter, ThemeConfig, WikiTemplateRenderer
from network_wiki import NodeStyle, NodeFont, EdgeStyle, EdgeArrows
from network_wiki.flask_view import GraphView

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Graph 1 — static software architecture graph
# ---------------------------------------------------------------------------

def build_arch_graph() -> ig.Graph:
    g = ig.Graph(directed=True)
    g.add_vertices(6)
    g.vs["name"]  = ["Mobile App", "Web Frontend", "API Gateway",
                      "Auth Service", "Order Service", "PostgreSQL"]
    g.vs["layer"] = ["client", "client", "gateway", "service", "service", "datastore"]
    g.vs["tech"]  = ["React Native", "React/Vite", "Kong",
                      "FastAPI", "FastAPI", "PostgreSQL 15"]
    g.vs["team"]  = ["Mobile", "Frontend", "Platform", "Platform", "Orders", "Data"]
    g.add_edges([(0, 2), (1, 2), (2, 3), (2, 4), (3, 5), (4, 5)])
    g.es["protocol"] = ["HTTPS", "HTTPS", "gRPC", "gRPC", "SQL", "SQL"]
    return g


LAYER_COLOR = {
    "client": "#4a90d9", "gateway": "#e67e22",
    "service": "#2ecc71", "datastore": "#9b59b6",
}

arch_exporter = GraphExporter(
    graph=build_arch_graph(),
    title="Software Architecture",
    theme=ThemeConfig(bootswatch_theme="flatly", accent_color="#2ecc71"),
    node_style_callback=lambda v: NodeStyle(
        color=LAYER_COLOR.get(v["layer"], "#888"),
        shape={"gateway": "diamond", "datastore": "database"}.get(v["layer"], "box"),
        font=NodeFont(color="#fff"),
        tooltip=f"{v['name']} · {v['tech']} · {v['team']} team",
        group=v["layer"],
    ),
    edge_style_callback=lambda e: EdgeStyle(
        width=2, label=e["protocol"], font_size=9, font_color="#888",
        arrows=EdgeArrows(to_enabled=True, to_scale=0.7),
    ),
    wiki_renderer=WikiTemplateRenderer(
        type_attr="layer",
        full_templates_by_type={
            "service": """
                <h2>{{ label }}</h2>
                <span class="badge text-bg-success mb-2">{{ type_value }}</span>
                <table class="table table-sm table-striped">
                  <tr><td>Technology</td><td>{{ attrs.tech }}</td></tr>
                  <tr><td>Team</td><td>{{ attrs.team }}</td></tr>
                  <tr><td>Incoming</td><td>{{ n_in }}</td></tr>
                  <tr><td>Outgoing</td><td>{{ n_out }}</td></tr>
                </table>
                {% if neighbours %}
                <h3>Connected to</h3>
                <ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
                {% endif %}
            """,
        },
        undefined_strict=False,
    ),
)

# ---------------------------------------------------------------------------
# Graph 2 — dynamic graph, rebuilt on every request
# ---------------------------------------------------------------------------

def build_live_graph() -> GraphExporter:
    """Simulate a graph that changes over time (e.g. from a database query)."""
    n = random.randint(4, 8)
    g = ig.Graph(directed=True)
    g.add_vertices(n)
    g.vs["name"]   = [f"Node {i}" for i in range(n)]
    g.vs["status"] = random.choices(["healthy", "degraded", "down"], k=n)
    g.vs["load"]   = [round(random.uniform(0, 100), 1) for _ in range(n)]

    # Add random edges (simple random DAG)
    for i in range(n - 1):
        if random.random() > 0.3:
            g.add_edge(i, i + 1)
        if i + 2 < n and random.random() > 0.6:
            g.add_edge(i, i + 2)

    STATUS_COLOR = {"healthy": "#2ecc71", "degraded": "#f39c12", "down": "#e74c3c"}

    return GraphExporter(
        graph=g,
        title=f"Live Graph ({n} nodes)",
        theme=ThemeConfig(bootswatch_theme="darkly", accent_color="#2ecc71"),
        node_style_callback=lambda v: NodeStyle(
            color=STATUS_COLOR.get(v["status"], "#888"),
            shape="dot",
            size=10 + v["load"] / 5,
            tooltip=f"{v['name']} — {v['status']} — load: {v['load']}%",
        ),
    )

# ---------------------------------------------------------------------------
# Register both graphs under a single GraphView
# ---------------------------------------------------------------------------

view = GraphView(url_prefix="/graphs")
view.add("arch", arch_exporter,  title="Software Architecture")
view.add("live", build_live_graph, title="Live Graph")   # factory: rebuilt per request
view.register(app)

# ---------------------------------------------------------------------------
# Root redirect
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    from flask import redirect
    return redirect("/graphs/")

if __name__ == "__main__":
    app.run(debug=True)
