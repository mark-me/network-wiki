# Network-Wiki

Generate interactive standalone HTML graph visualizations with expandable per-node and per-edge wikis, Bootstrap 5 / Bootswatch theming, and Jinja2 templates.

## Quick Start

```python
import igraph as ig
from network_wiki import GraphExporter, ThemeConfig

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["A", "B", "C"]
g.add_edges([(0, 1), (1, 2)])

exporter = GraphExporter(
    g,
    title="My Graph",
    theme=ThemeConfig(bootswatch_theme="flatly"),
)
exporter.export("graph.html")
```

Open `graph.html` in a browser to see an interactive vis.js-powered graph with collapsible wiki side-panels.

## Key Features

* Interactive graphs powered by [vis.js](https://visjs.org/)
* Expandable wikis for nodes and edges, with a compact side-panel view and a full-screen modal
* 25 Bootswatch 5 themes, or plain Bootstrap with a user-toggleable light/dark mode (persisted in `localStorage`)
* Customizable styling for nodes and edges via callback functions
* Jinja2 templating for rich, per-type wiki content
* Flask integration via `GraphView` for serving one or more graphs dynamically, with live data support

## Where to Go Next

* New to network-wiki? Start with the **[Tutorial](tutorial/index.md)**
* Looking for a specific API or config option? See the **[User Guide](user-guide/index.md)**
* Want to contribute or understand the internals? See the **[Developer Guide](developer/index.md)**
