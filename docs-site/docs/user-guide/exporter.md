# Graph Exporter

The `GraphExporter` class converts an `igraph.Graph` into a standalone interactive HTML page.

## Class Reference

```python
class GraphExporter(
    graph,
    title: str = "Graph Wiki",
    layout: Optional[LayoutConfig] = None,
    theme: Optional[ThemeConfig] = None,
    default_node_style: Optional[NodeStyle] = None,
    default_edge_style: Optional[EdgeStyle] = None,
    node_style_callback: Optional[Callable] = None,
    edge_style_callback: Optional[Callable] = None,
    wiki_callback: Optional[Callable] = None,
    edge_wiki_callback: Optional[Callable] = None,
    wiki_renderer: Optional[WikiTemplateRenderer] = None,
)
```

## Parameters

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `graph` | `Graph` | The `igraph.Graph` to export (each vertex needs a `"name"` attribute) |
| `title` | `str` | Browser tab and toolbar title |
| `layout` | `LayoutConfig` | Physics and layout configuration |
| `theme` | `ThemeConfig` | Visual theme (Bootswatch, accent color, panel width) |
| `default_node_style` | `NodeStyle` | Fallback style when no node callback is provided |
| `default_edge_style` | `EdgeStyle` | Fallback style when no edge callback is provided |
| `node_style_callback` | `Callable[[Vertex], NodeStyle]` | Per-node styling function |
| `edge_style_callback` | `Callable[[Edge], EdgeStyle]` | Per-edge styling function |
| `wiki_callback` | `Callable[[Vertex], WikiContent]` | Per-node wiki content generator |
| `edge_wiki_callback` | `Callable[[Edge], WikiContent]` | Per-edge wiki content generator |
| `wiki_renderer` | `WikiTemplateRenderer` | Jinja2-based renderer (overrides `wiki_callback`) |

## Example Usage

```python
exporter = GraphExporter(
    g,
    title="Pipeline View",
    theme=ThemeConfig(bootswatch_theme="cosmo"),
    node_style_callback=lambda v: NodeStyle(color="#2ecc71"),
    wiki_renderer=WikiTemplateRenderer(full_template_file="full.html.j2"),
)
exporter.export("output.html")
```
