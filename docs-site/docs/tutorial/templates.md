# Templates

Customize wiki content using Jinja2 templates.

## Basic Setup

```python
from network_wiki import GraphExporter, WikiTemplateRenderer

renderer = WikiTemplateRenderer(
    template_dir="templates/wiki",
    full_template_file="full_default.html.j2",
    mini_template_file="mini_default.html.j2"
)

exporter = GraphExporter(g, title="Templated Graph")
exporter.set_wiki_renderer(renderer)
exporter.export("templated.html")
```

## Template Context Variables

Each template receives:

| Variable     | Type        | Description                            |
| ------------ | ----------- | -------------------------------------- |
| `v`          | `Vertex`    | The `igraph.Vertex` object             |
| `attrs`      | `dict`      | All vertex attributes `{name: value}`  |
| `label`      | `str`       | Display name                           |
| `index`      | `int`       | Vertex index                           |
| `n_in`       | `int`       | Incoming edge count                    |
| `n_out`      | `int`       | Outgoing edge count                    |
| `neighbours` | `list[str]` | Neighboring node names                 |
| `graph`      | `Graph`     | Full `igraph.Graph` object             |
| `type_value` | `str`       | Value of the configured type attribute |

## Per-Type Templates

Dispatch different templates by node type:

```python
renderer = WikiTemplateRenderer(
    type_attr="role",  # Use 'role' attribute instead of 'type'
    full_templates_by_type={
        "manager": "{{ '{% include %} manager_tmpl {{ '%' }}}" }}",
        "engineer": "{{ '{{%' include %}} engineer_tmpl {% %%}' }}"
    }
)
```

Available types are determined by values in your chosen type_attr column.
