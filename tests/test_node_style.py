"""Unit tests for node_style.py."""
import pytest
from network_wiki import NodeColor, NodeFont, NodeStyle


class TestNodeColor:
    def test_to_vis_structure(self):
        c = NodeColor(background="#fff", border="#000",
                      highlight_background="#eee", highlight_border="#111",
                      hover_background="#ddd", hover_border="#222")
        vis = c.to_vis()
        assert vis["background"] == "#fff"
        assert vis["border"] == "#000"
        assert vis["highlight"]["background"] == "#eee"
        assert vis["highlight"]["border"] == "#111"
        assert vis["hover"]["background"] == "#ddd"
        assert vis["hover"]["border"] == "#222"

    def test_from_hex_produces_alpha_variants(self):
        c = NodeColor.from_hex("#ff0000")
        assert c.border == "#ff0000"
        assert c.background.startswith("#ff0000")
        assert len(c.background) > len("#ff0000")  # has alpha suffix

    def test_from_hex_strips_hash(self):
        c = NodeColor.from_hex("aabbcc")
        assert "#" in c.border


class TestNodeFont:
    def test_to_vis_defaults(self):
        f = NodeFont()
        vis = f.to_vis()
        assert vis["bold"] is False
        assert vis["italic"] is False
        assert vis["align"] == "center"

    def test_to_vis_custom(self):
        f = NodeFont(color="#red", size=18, bold=True, align="left")
        vis = f.to_vis()
        assert vis["size"] == 18
        assert vis["bold"] is True
        assert vis["align"] == "left"


class TestNodeStyle:
    def test_to_vis_basic(self):
        s = NodeStyle(shape="diamond", size=30)
        vis = s.to_vis(node_id=1, label_fallback="A")
        assert vis["id"] == 1
        assert vis["label"] == "A"
        assert vis["shape"] == "diamond"
        assert vis["size"] == 30

    def test_custom_label_overrides_fallback(self):
        s = NodeStyle(label="Custom")
        vis = s.to_vis(node_id=0, label_fallback="Fallback")
        assert vis["label"] == "Custom"

    def test_show_label_false_clears_label(self):
        s = NodeStyle(show_label=False)
        vis = s.to_vis(0, "X")
        assert vis["label"] == ""

    def test_hex_color_generates_variants(self):
        s = NodeStyle(color="#123456")
        vis = s.to_vis(0, "X")
        assert vis["color"]["border"] == "#123456"
        assert "background" in vis["color"]

    def test_node_color_object_passed_through(self):
        nc = NodeColor(background="#abc", border="#def")
        s = NodeStyle(color=nc)
        vis = s.to_vis(0, "X")
        assert vis["color"]["background"] == "#abc"

    def test_tooltip_added_as_title(self):
        s = NodeStyle(tooltip="My tip")
        vis = s.to_vis(0, "X")
        assert vis["title"] == "My tip"

    def test_shadow_dict_present(self):
        s = NodeStyle(shadow=True, shadow_size=15)
        vis = s.to_vis(0, "X")
        assert vis["shadow"]["enabled"] is True
        assert vis["shadow"]["size"] == 15

    def test_value_scaling(self):
        s = NodeStyle(value=5.0, scaling_min=10, scaling_max=50)
        vis = s.to_vis(0, "X")
        assert vis["value"] == 5.0
        assert vis["scaling"] == {"min": 10, "max": 50}

    def test_fixed_position(self):
        s = NodeStyle(x=100.0, y=200.0, fixed_x=True, fixed_y=False)
        vis = s.to_vis(0, "X")
        assert vis["x"] == 100.0
        assert vis["y"] == 200.0
        assert vis["fixed"] == {"x": True, "y": False}

    def test_extra_props_merged(self):
        s = NodeStyle(extra={"physics": False})
        vis = s.to_vis(0, "X")
        assert vis["physics"] is False

    def test_border_dashes(self):
        s = NodeStyle(border_dashes=True)
        vis = s.to_vis(0, "X")
        assert "shapeProperties" in vis
        assert vis["shapeProperties"]["borderDashes"] == [5, 5]

    def test_group_included(self):
        s = NodeStyle(group="pipeline")
        vis = s.to_vis(0, "X")
        assert vis["group"] == "pipeline"
