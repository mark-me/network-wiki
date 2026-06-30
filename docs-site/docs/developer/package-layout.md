# Package Layout

## 📁 Source Structure

```text
network_wiki/
├── __init__.py       # Public API exports (version, constructors)
├── exporter.py        # GraphExporter class definition
├── flask_view.py       # Flask Blueprint infrastructure (GraphView)
├── layout.py           # Config dataclasses + Bootswatch CDN URL generators
├── node_style.py        # Node styling dataclasses
├── edge_style.py        # Edge styling dataclasses
├── wiki.py             # Wiki content rendering logic
└── templates/           # Jinja2 templates shipped with the package
    ├── page.html.j2         # Static export page shell
    ├── page_flask.html.j2    # Flask page shell (fetches data via JSON endpoint)
    ├── mini_default.html.j2   # Bundled side-panel fallback
    └── full_default.html.j2   # Bundled full-modal fallback
```

## 🧭 Import Paths

Public symbols exposed in `__all__`:

```python
from network_wiki import (
    NodeColor, NodeFont, NodeStyle,
    EdgeColor, EdgeArrows, EdgeStyle,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
    GraphExporter, GraphView,
)
```

`GraphView` requires Flask to be installed (`pip install network-wiki[flask]`); importing it without Flask available raises `ImportError` with an explanation.

## 🏷️ Version Tracking

Current version tracked in `__version__` within `network_wiki/__init__.py`, and mirrored in `pyproject.toml`. Both are bumped together on release — see [Contributing](contributing.md).
