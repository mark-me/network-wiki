# Graph Exporter

The `GraphExporter` class converts an `igraph.Graph` into a standalone interactive HTML page.

## 🏗️ Constructor

```python
GraphExporter(
    graph,
    title: str = "Graph Wiki",
    layout: LayoutConfig | None = None,
    theme: ThemeConfig | None = None,
    default_node_style: NodeStyle | None = None,
    default_edge_style: EdgeStyle | None = None,
    node_style_callback: Callable | None = None,
    edge_style_callback: Callable | None = None,
    wiki_callback: Callable | None = None,
    edge_wiki_callback: Callable | None = None,
    wiki_renderer: WikiTemplateRenderer | None = None,
)
```

## 📝 Parameters

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `graph` | `igraph.Graph` | The graph to export. Each vertex should have a `"name"` or `"label"` attribute; falls back to `"Node <index>"` if absent. |
| `title` | `str` | Browser tab and toolbar title |
| `layout` | `LayoutConfig` | Physics and layout configuration — see [Configuration](configuration.md) |
| `theme` | `ThemeConfig` | Visual theme (Bootswatch, accent color, panel width) — see [Themes](themes.md) |
| `default_node_style` | `NodeStyle` | Fallback style applied when no node callback is registered |
| `default_edge_style` | `EdgeStyle` | Fallback style applied when no edge callback is registered |
| `node_style_callback` | `Callable[[Vertex], NodeStyle]` | Per-node styling function — see [Styling](styling.md) |
| `edge_style_callback` | `Callable[[Edge], EdgeStyle]` | Per-edge styling function — see [Styling](styling.md) |
| `wiki_callback` | `Callable[[Vertex], WikiContent]` | Per-node wiki content generator |
| `edge_wiki_callback` | `Callable[[Edge], WikiContent]` | Per-edge wiki content generator |
| `wiki_renderer` | `WikiTemplateRenderer` | Jinja2-based renderer — takes priority over `wiki_callback` when both are set; see [Templates](templates.md) |

All callback parameters can also be set after construction with the matching `set_*` method (`set_node_style_callback`, `set_edge_style_callback`, `set_wiki_callback`, `set_edge_wiki_callback`, `set_wiki_renderer`) — useful when the callback depends on data resolved after the exporter is created.

## 📄 Output Methods

| Method | Returns | Use case |
| ------ | ------- | -------- |
| `export(path)` | `pathlib.Path` | Write a standalone HTML file to disk |
| `render_html()` | `str` | Render the page to a string without writing to disk — used internally by `GraphView` for Flask serving |

## 💡 Example Usage

```python
from network_wiki import GraphExporter, NodeStyle, ThemeConfig, WikiTemplateRenderer

exporter = GraphExporter(
    g,
    title="Pipeline View",
    theme=ThemeConfig(bootswatch_theme="cosmo"),
    node_style_callback=lambda v: NodeStyle(color="#2ecc71"),
    wiki_renderer=WikiTemplateRenderer(full_template_file="full.html.j2"),
)
exporter.export("output.html")
```

## 🌐 Serving Dynamically with Flask

`GraphExporter` instances integrate with `GraphView` for live HTTP serving — see [Flask Integration](../tutorial/flask.md).
