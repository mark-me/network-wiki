# Themes

Customize the visual appearance of generated pages.

## Bootswatch Theme Selection

Choose from 25 Bootswatch 5 themes:

```python
from network_wiki import ThemeConfig

# Light theme
ThemeConfig(bootswatch_theme="minty")

# Dark theme
ThemeConfig(bootswatch_theme="darkly")

# Plain Bootstrap — no Bootswatch theme
ThemeConfig()
```

See the `BOOTSWATCH_THEMES` dictionary for the full list of names and their light/dark classification:

```python
from network_wiki import BOOTSWATCH_THEMES

print(BOOTSWATCH_THEMES)
# {"cerulean": "light", "cosmo": "light", ..., "darkly": "dark", ...}
```

**Light themes (19):** cerulean, cosmo, flatly, journal, litera, lumen, lux, materia, minty, morph, pulse, quartz, sandstone, simplex, sketchy, spacelab, united, yeti, zephyr

**Dark themes (6):** cyborg, darkly, slate, solar, superhero, vapor

## Accent Color Control

Override the primary UI accent color:

```python
ThemeConfig(bootswatch_theme="flatly", accent_color="#e94560")
```

Used for:

* Toolbar highlights
* Panel titles
* Wiki headings

## Dark/Light Mode Toggle

When no Bootswatch theme is set (`ThemeConfig()`), end-users see a toggle button in the toolbar that switches between light and dark mode. Their preference persists in `localStorage` and defaults to the OS setting (`prefers-color-scheme`) on first load.

!!! warning "The toggle is hidden when a Bootswatch theme is active"
    Bootswatch stylesheets are built for a single, fixed appearance — they
    don't respond to Bootstrap's `data-bs-theme` attribute the way plain
    Bootstrap does. If `bootswatch_theme` is set, the toggle would have no
    visible effect, so network-wiki hides it automatically rather than
    showing a button that does nothing.

    If you want end-users to be able to switch between light and dark mode,
    use plain Bootstrap (`ThemeConfig()` with no `bootswatch_theme`) and set
    `accent_color` for branding instead:

    ```python
    ThemeConfig(accent_color="#e94560")  # toggle is shown
    ```

    If you want a fixed, designer-chosen appearance instead, set
    `bootswatch_theme` and accept that the toggle won't appear:

    ```python
    ThemeConfig(bootswatch_theme="darkly")  # toggle is hidden
    ```
