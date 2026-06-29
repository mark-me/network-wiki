# Architecture

## Component Responsibilities

| Component | Responsibility |
| --------- | -------------- |
| `GraphExporter` | Orchestrates node/edge styling, wiki rendering, HTML output |
| `GraphView` | Flask Blueprint wrapping exporters for HTTP serving |
| `NodeStyle` / `EdgeStyle` | Dataclasses mapping Python styles to vis.js options |
| `WikiTemplateRenderer` | Jinja2 environment managing template resolution |
| `LayoutConfig` | Vis.js physics/layout configuration |
| `ThemeConfig` | Bootstrap/Bootswatch theme metadata |

## Data Flow

```mermaid
flowchart TD
    A[igraph.Graph] --> B[GraphExporter._build_nodes]
    B --> C[vis.js node DataSet]
    A --> D[GraphExporter._build_edges]
    D --> E[vis.js edge DataSet]
    A --> F[WikiTemplateRenderer.render]
    F --> G[WikiContent objects]
    C --> H[Jinja2 page.html.j2 template]
    E --> H
    G --> H
    H --> I[Final HTML output]
```

## Extension Points

- Style callbacks for per-element customization
- Wiki callbacks/renderer for custom content
- Custom Jinja2 template inheritance
- Flask factory pattern for live data feeds
