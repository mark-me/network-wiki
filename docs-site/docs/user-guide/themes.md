# Themes

Customize the visual appearance of generated pages.

## Bootswatch Theme Selection

Choose from 23 Bootswatch 5 themes:

```python
from network_wiki import ThemeConfig

# Light theme
ThemeConfig(bootswatch_theme="minty")

# Dark theme
ThemeConfig(bootswatch_theme="darkly")
```

See BOOTSWATCH_THEMES dictionary for all available names.

Accent Color Control

Override the primary UI accent color:

```python
ThemeConfig(bootswatch_theme="flatly", accent_color="#e94560")
```

Used for:

* Toolbar highlights
* Panel titles
* Wiki headings

## Dark/Light Mode Toggle

End-users can toggle modes client-side. Their preference persists in localStorage and defaults to OS setting (prefers-color-scheme) on first load.

Set base_scheme implicitly by choosing light or dark Bootswatch themes.
