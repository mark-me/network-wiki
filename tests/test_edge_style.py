"""Unit tests for edge_style.py."""
import pytest
from network_wiki import EdgeColor, EdgeArrows, EdgeStyle


class TestEdgeColor:
    def test_to_vis_structure(self):
        ec = EdgeColor(color="#aaa", highlight="#bbb", hover="#ccc", inherit="from")
        vis = ec.to_vis()
        assert vis["color"] == "#aaa"
        assert vis["highlight"] == "#bbb"
        assert vis["hover"] == "#ccc"
        assert vis["inherit"] == "from"

    def test_inherit_false_by_default(self):
        assert EdgeColor().to_vis()["inherit"] is False


class TestEdgeArrows:
    def test_to_arrow_only_when_enabled(self):
        ea = EdgeArrows(to_enabled=True, from_enabled=False, middle_enabled=False)
        vis = ea.to_vis()
        assert "to" in vis
        assert "from" not in vis
        assert "middle" not in vis

    def test_all_arrows_enabled(self):
        ea = EdgeArrows(to_enabled=True, from_enabled=True, middle_enabled=True)
        vis = ea.to_vis()
        assert "to" in vis
        assert "from" in vis
        assert "middle" in vis

    def test_arrow_type_and_scale(self):
        ea = EdgeArrows(to_enabled=True, to_type="diamond", to_scale=1.5)
        vis = ea.to_vis()
        assert vis["to"]["type"] == "diamond"
        assert vis["to"]["scaleFactor"] == 1.5


class TestEdgeStyle:
    def test_to_vis_basic(self):
        es = EdgeStyle(width=3.0)
        vis = es.to_vis(from_id=0, to_id=1)
        assert vis["from"] == 0
        assert vis["to"] == 1
        assert vis["width"] == 3.0

    def test_hex_color_string(self):
        es = EdgeStyle(color="#ff0000")
        vis = es.to_vis(0, 1)
        assert vis["color"]["color"] == "#ff0000"
        assert vis["color"]["highlight"] == "#ff0000"

    def test_edge_color_object(self):
        ec = EdgeColor(color="#abc", highlight="#def")
        es = EdgeStyle(color=ec)
        vis = es.to_vis(0, 1)
        assert vis["color"]["color"] == "#abc"

    def test_dashes(self):
        es = EdgeStyle(dashes=True)
        vis = es.to_vis(0, 1)
        assert vis["dashes"] is True

    def test_label_included(self):
        es = EdgeStyle(label="800K")
        vis = es.to_vis(0, 1)
        assert vis["label"] == "800K"

    def test_no_label_key_when_none(self):
        es = EdgeStyle(label=None)
        vis = es.to_vis(0, 1)
        assert "label" not in vis

    def test_smooth_settings(self):
        es = EdgeStyle(smooth_type="horizontal", smooth_roundness=0.8)
        vis = es.to_vis(0, 1)
        assert vis["smooth"]["type"] == "horizontal"
        assert vis["smooth"]["roundness"] == 0.8

    def test_tooltip(self):
        es = EdgeStyle(tooltip="My edge")
        vis = es.to_vis(0, 1)
        assert vis["title"] == "My edge"

    def test_length(self):
        es = EdgeStyle(length=300)
        vis = es.to_vis(0, 1)
        assert vis["length"] == 300

    def test_extra_merged(self):
        es = EdgeStyle(extra={"hidden": True})
        vis = es.to_vis(0, 1)
        assert vis["hidden"] is True

    def test_font_always_present(self):
        vis = EdgeStyle().to_vis(0, 1)
        assert "font" in vis
        assert "color" in vis["font"]
