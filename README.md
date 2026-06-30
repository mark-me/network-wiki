# network-wiki

[![CI](https://github.com/mark-me/network-wiki/actions/workflows/ci.yml/badge.svg)](https://github.com/mark-me/network-wiki/actions/workflows/ci.yml)
[![Documentation](https://github.com/mark-me/network-wiki/actions/workflows/docs.yml/badge.svg)](https://mark-me.github.io/network-wiki/)
[![Python Versions](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Turn an [igraph](https://igraph.org) graph into an interactive HTML page where every node and edge has its own wiki page. A Python package for transforming igraph graphs into interactive wiki-enabled visualizations.

![Interactive Graph Preview](./docs-site/docs/images/banner.png)

## 🤔 Why

You already have the graph in Python — a pipeline, an org chart, a service topology, a network diagram. `network-wiki` (a Python package) turns it into something people can click around in: a force-directed layout where each node opens a side panel, and a full wiki page if there's more to say. No frontend code required.

- 📊 Interactive graphs powered by [vis.js](https://visjs.org/)
- 📖 Per-node and per-edge wikis — compact side panel + full-screen modal
- 🎨 25 [Bootswatch](https://bootswatch.com) themes, or plain Bootstrap with a user-toggleable light/dark mode
- 🖌️ Style every node and edge individually via simple callbacks
- 📝 Jinja2 templates for rich wiki content, with sensible auto-generated fallbacks
- 🌶️ Optional Flask integration — serve multiple graphs, swap them client-side, or rebuild from live data on every request
- 📦 Works as a single static HTML file with zero server required

## 📥 Install

```bash
pip install git+https://github.com/mark-me/network-wiki.git
# or, with Flask support:
pip install "network-wiki[flask] @ git+https://github.com/mark-me/network-wiki.git"
```

```bash
# uv
uv add git+https://github.com/mark-me/network-wiki.git
```

## 🚀 Quickstart

```python
import igraph as ig
from network_wiki import GraphExporter, ThemeConfig

g = ig.Graph(directed=True)
g.add_vertices(3)
g.vs["name"] = ["Source", "Pipeline", "Target"]
g.add_edges([(0, 1), (1, 2)])

exporter = GraphExporter(g, title="My Graph", theme=ThemeConfig(bootswatch_theme="flatly"))
exporter.export("graph.html")
```

Open `graph.html` — that's it, no server needed. Click a node to see its wiki.

Want it served dynamically instead? Three more lines with Flask:

```python
from flask import Flask
from network_wiki.flask_view import GraphView

app = Flask(__name__)
GraphView(exporter, url_prefix="/graph").register(app)
```

## 📖 Documentation

The README stops here on purpose — everything else lives in the docs:

**📚 [mark-me.github.io/network-wiki](https://mark-me.github.io/network-wiki/)**

- [Tutorial](https://mark-me.github.io/network-wiki/tutorial/) — installation through Flask deployment, step by step
- [User Guide](https://mark-me.github.io/network-wiki/user-guide/) — node/edge styling, Jinja2 templates, themes, layout config
- [Developer Guide](https://mark-me.github.io/network-wiki/developer/) — architecture, rendering pipeline, contributing

Runnable examples covering every feature, including a full org-chart with mixed wiki strategies, live in [`examples/`](examples/).

## 🛠️ Development

```bash
git clone https://github.com/mark-me/network-wiki.git
cd network-wiki
uv sync --extra dev --extra flask
uv run pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the pip-based workflow and PR guidelines.

## ⚖️ License

MIT — see [LICENSE](LICENSE).
