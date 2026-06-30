# Node and Edge Styling

Control the visual appearance of nodes and edges with `NodeStyle` and `EdgeStyle` dataclasses, applied per-element through callbacks.

## ⚛️ NodeStyle

```python
from network_wiki import NodeStyle, NodeFont, NodeColor

NodeStyle(
    shape="box",            # box, dot, diamond, star, ellipse, database, image, circularImage, ...
    color="#2ecc71",        # hex string, or a NodeColor for fine-grained control
    size=24,
    font=NodeFont(color="#ffffff", bold=True),
    tooltip="Shown on hover",
    border_width=2,
    shadow=True,
    group="service",        # used for vis.js grouping/legends
)
```

For full control over background/border/highlight colors, pass a `NodeColor` instead of a hex string:

```python
NodeStyle(color=NodeColor(
    background="#2ecc71",
    border="#1a9850",
    highlight_background="#58d68d",
))
```

## 🔗 EdgeStyle

```python
from network_wiki import EdgeStyle, EdgeArrows

EdgeStyle(
    width=2,
    color="#adb5bd",
    dashes=False,
    arrows=EdgeArrows(to_enabled=True, to_scale=0.6),
    smooth_type="cubicBezier",
)
```

## 🖌️ Applying Styles per Element

Pass callbacks to the constructor, or set them after construction:

```python
exporter = GraphExporter(
    g,
    node_style_callback=lambda v: NodeStyle(
        color="#2ecc71" if v["status"] == "healthy" else "#e74c3c",
        shape="dot",
    ),
    edge_style_callback=lambda e: EdgeStyle(width=1 + e["weight"]),
)

# Equivalently, after construction:
exporter.set_node_style_callback(lambda v: NodeStyle(color="#2ecc71"))
exporter.set_edge_style_callback(lambda e: EdgeStyle(width=2))
```

Constructor arguments and setter calls write to the same internal callback — whichever happens last wins if you do both. In practice, pick one style and stick with it.

## 🛟 Fallback Styles

When no callback is registered, `default_node_style` / `default_edge_style` apply to every element:

```python
from network_wiki import GraphExporter, NodeStyle, EdgeStyle

exporter = GraphExporter(
    g,
    default_node_style=NodeStyle(color="#3498db", shape="dot"),
    default_edge_style=EdgeStyle(width=1, color="#ccc"),
)
```

## ⚡ Full vis.js Property Passthrough

Any vis.js node/edge property not modeled explicitly can be set via the `extra` field, which is merged into the generated dict last:

```python
NodeStyle(color="#2ecc71", extra={"physics": False, "fixed": True})
```

See the [vis.js node options](https://visjs.github.io/vis-network/docs/network/nodes.html) and [edge options](https://visjs.github.io/vis-network/docs/network/edges.html) reference for the full property list.
