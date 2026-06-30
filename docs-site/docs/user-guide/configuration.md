# Configuration

Fine-tune physics, layout, and interaction behavior.

## ⚙️ LayoutConfig

Physics and interaction settings passed directly to vis.js.

```python
@dataclass
class LayoutConfig:
    # Physics
    physics_enabled: bool = True
    solver: str = "forceAtlas2Based"
    stabilization_iterations: int = 150
    gravity: float = -50
    spring_length: int = 200
    spring_constant: float = 0.05
    damping: float = 0.09

    # Hierarchical layout
    hierarchical: bool = False
    hierarchical_direction: str = "LR"
    hierarchical_sort_method: str = "directed"

    # Interaction
    hover: bool = True
    multiselect: bool = True
    navigation_buttons: bool = False
    keyboard_navigation: bool = False
    zoom_speed: float = 1.0
    min_zoom: float = 0.1
    max_zoom: float = 10.0
```

## 🧲 Physics Solver Options

* barnesHut
* forceAtlas2Based (recommended)
* repulsion
* hierarchicalRepulsion

## 🌳 Hierarchical Direction Options

* UD — Up-down
* DU — Down-up
* LR — Left-right (recommended)
* RL — Right-left

Enable hierarchical layout to disable physics simulation.
