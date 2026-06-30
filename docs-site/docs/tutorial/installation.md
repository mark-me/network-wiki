# Installation

## Requirements

* Python 3.11 or higher
* [`igraph`](https://igraph.org/python/) for graph operations
* [`jinja2`](https://jinja.palletsprojects.com/) for wiki templating (installed automatically as a core dependency)
* [`flask`](https://flask.palletsprojects.com/) — only needed for the Flask integration, see [`GraphView`](../tutorial/flask.md)

## Install

=== "pip"

    ```bash
    # Core package (static HTML export)
    pip install network-wiki

    # With Flask integration
    pip install "network-wiki[flask]"

    # Directly from GitHub
    pip install git+https://github.com/mark-me/network-wiki.git
    ```

=== "uv"

    ```bash
    # Core package
    uv add network-wiki

    # With Flask integration
    uv add "network-wiki[flask]"

    # Directly from GitHub
    uv add git+https://github.com/mark-me/network-wiki.git
    ```

## Verify the Install

```python
import network_wiki
print(network_wiki.__version__)
```

Continue to [Your First Graph](first-graph.md).
