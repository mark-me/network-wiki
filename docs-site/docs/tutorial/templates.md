# Wiki Templates

Customize wiki content using Jinja2 templates.

## 🏗️ Basic Setup

```python
from network_wiki import GraphExporter, WikiTemplateRenderer

renderer = WikiTemplateRenderer(
    template_dir="templates/wiki",
    full_template_file="full_default.html.j2",
    mini_template_file="mini_default.html.j2",
)

exporter = GraphExporter(g, title="Templated Graph", wiki_renderer=renderer)
exporter.export("templated.html")
```

`wiki_renderer` can also be set after construction with `exporter.set_wiki_renderer(renderer)`.

## 🧩 Template Context Variables

Each template receives:

| Variable     | Type        | Description                             |
| ------------ | ----------- | --------------------------------------- |
| `v`          | `Vertex`    | The `igraph.Vertex` object              |
| `attrs`      | `dict`      | All vertex attributes `{name: value}`   |
| `label`      | `str`       | Display name                            |
| `index`      | `int`       | Vertex index                            |
| `n_in`       | `int`       | Incoming edge count                     |
| `n_out`      | `int`       | Outgoing edge count                     |
| `neighbours` | `list[str]` | Neighboring node names                  |
| `graph`      | `Graph`     | Full `igraph.Graph` object              |
| `type_value` | `str`       | Value of the configured type attribute, or `""` |

## 🗂️ Per-Type Templates

Dispatch different templates by node type using inline strings:

```python
MANAGER_TMPL = """
<h2>{{ label }}</h2>
<span class="badge text-bg-success">{{ type_value }}</span>
<p>{{ attrs.bio }}</p>
<h3>Team</h3>
<ul>{% for n in neighbours %}<li>{{ n }}</li>{% endfor %}</ul>
"""

ENGINEER_TMPL = """
<h2>{{ label }}</h2>
<span class="badge text-bg-info">{{ type_value }}</span>
<p>{{ attrs.bio }}</p>
"""

renderer = WikiTemplateRenderer(
    type_attr="role",  # use the "role" attribute instead of "type"
    full_templates_by_type={
        "manager": MANAGER_TMPL,
        "engineer": ENGINEER_TMPL,
    },
)
```

Or with template files instead of inline strings:

```python
renderer = WikiTemplateRenderer(
    type_attr="role",
    template_dir="templates/org",
    full_template_files_by_type={
        "manager": "full_manager.html.j2",
        "engineer": "full_engineer.html.j2",
    },
)
```

Available types are determined by the values present in your chosen `type_attr` column. Types without a matching template fall through to the [resolution chain](../user-guide/templates.md#template-resolution-order) and ultimately to the bundled default template, which renders all attributes generically.

## 🌊 Edge Wikis

Edges get the same side-panel / full-modal treatment, but through a plain Python callback rather than a template renderer:

```python
from network_wiki import WikiContent

def edge_wiki(e) -> WikiContent:
    return WikiContent(
        mini_html=f"<p>{e['relationship']} since {e['since']}</p>",
        full_html=f"<h2>{e['relationship']}</h2><p>Since {e['since']}</p>",
    )

exporter = GraphExporter(g, edge_wiki_callback=edge_wiki)
```

## 🚀 A Complete, Runnable Example

See [`examples/wiki_org_chart.py`](https://github.com/mark-me/network-wiki/blob/main/examples/wiki_org_chart.py) in the repository for a full org-chart graph that demonstrates every wiki mechanism side by side: per-type template files, per-type inline templates, the automatic fallback for untemplated types, and an edge wiki callback.
