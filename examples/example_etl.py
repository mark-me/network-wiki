"""
example_etl.py
==============
Demonstrates network-wiki with an ETL pipeline graph.

Node types are dispatched via the default type_attr="type".
Per-type templates live in examples/templates/etl/ and are
passed via full_template_files_by_type.

Run with:
    python examples/example_etl.py
"""

import igraph as ig
from network_wiki import (
    GraphExporter, NodeStyle, NodeFont,
    EdgeStyle, EdgeColor, EdgeArrows,
    WikiTemplateRenderer,
    LayoutConfig, ThemeConfig,
)

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

g = ig.Graph(directed=True)
g.add_vertices(6)
g.vs["name"] = [
    "ETL Pipeline", "Source A", "Source B", "Source C",
    "DWH Fact", "DWH Dimension",
]
g.vs["type"]        = ["pipeline", "source", "source", "source", "target", "target"]
g.vs["description"] = [
    "Central ETL pipeline transforming raw source data into the data warehouse.",
    "SAP CRM source model with customer and contract data.",
    "ERP exports with financial transactions via SFTP.",
    "REST API feeds with real-time product data.",
    "Central fact table in the data warehouse.",
    "Customer dimension with SCD Type 2 historisation.",
]
g.vs["status"]  = ["active"] * 6
g.vs["owner"]   = ["Data Engineering", "SAP Team", "Finance", "IT",
                    "Data Engineering", "Data Engineering"]
g.vs["weight"]  = [3, 1, 1, 1, 2, 2]

g.add_edges([(1, 0), (2, 0), (3, 0), (0, 4), (0, 5)])
g.es["critical"] = [True, False, True, True, False]
g.es["volume"]   = [800_000, 350_000, 50_000, 1_200_000, 1_200_000]

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

COLOR_MAP = {"pipeline": "#e94560", "source": "#a8dadc", "target": "#f5a623"}
SHAPE_MAP = {"pipeline": "diamond", "source": "box", "target": "ellipse"}

def node_style(v) -> NodeStyle:
    base = COLOR_MAP.get(v["type"], "#888")
    return NodeStyle(
        shape=SHAPE_MAP.get(v["type"], "box"),
        size=20 + v["weight"] * 8,
        color=base,
        border_width=3 if v["type"] == "pipeline" else 2,
        font=NodeFont(color="#ffffff", bold=(v["type"] == "pipeline")),
        shadow=(v["type"] == "pipeline"),
        tooltip=f"{v['name']} — {v['owner']}",
        group=v["type"],
    )

def edge_style(e) -> EdgeStyle:
    vol = e["volume"] or 0
    return EdgeStyle(
        width=1 + min(vol / 300_000, 5),
        color=EdgeColor(
            color="#e94560" if e["critical"] else "#4a90d9",
            highlight="#ffffff", hover="#ffffff",
        ),
        dashes=not e["critical"],
        arrows=EdgeArrows(to_enabled=True, to_scale=0.8),
        label=f"{vol // 1000}K" if vol else None,
        font_color="#888888", font_size=10,
    )

# ---------------------------------------------------------------------------
# Wiki — per-type templates from examples/templates/etl/
# ---------------------------------------------------------------------------

renderer = WikiTemplateRenderer(
    # type_attr defaults to "type" — matches vs["type"] in this graph
    template_dir="examples/templates/etl",
    full_template_files_by_type={
        "pipeline": "full_pipeline.html.j2",
        "source":   "full_source.html.j2",
    },
    global_context={"project": "ETL Landscape v2"},
    undefined_strict=False,
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

exporter = GraphExporter(
    g,
    title="ETL Landscape",
    theme=ThemeConfig(bootswatch_theme="darkly", accent_color="#e94560"),
    layout=LayoutConfig(
        solver="forceAtlas2Based",
        gravity=-80,
        spring_length=250,
        stabilization_iterations=200,
        navigation_buttons=True,
    ),
    node_style_callback=node_style,
    edge_style_callback=edge_style,
    wiki_renderer=renderer,
)

exporter.export("etl_landscape.html")
