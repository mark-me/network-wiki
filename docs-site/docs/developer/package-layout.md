# Package Layout

## Source Structure

```bash
network_wiki/
├── init.py # Public API exports (version, constructors)
├── exporter.py # GraphExporter class definition
├── flask_view.py # Flask Blueprint infrastructure
├── layout.py # Config dataclasses + CDN URL generators
├── node_style.py # Node styling dataclasses
├── edge_style.py # Edge styling dataclasses
├── wiki.py # Wiki content rendering logic
└── templates/ # Jinja2 templates shipped with package
    ├── page.html.j2
    ├── page_flask.html.j2
    ├── mini_default.html.j2
    └── full_default.html.j2
```

## Import Paths

Public symbols exposed in `__all__`:

```python
from network_wiki import (
    NodeColor, NodeFont, NodeStyle,
    EdgeColor, EdgeArrows, EdgeStyle,
    WikiContent, WikiTemplateRenderer,
    LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES,
    GraphExporter, GraphView
)
```

## Version tracking

Current version tracked in `__version__ = "0.5.0"` within `__init__.py`.
