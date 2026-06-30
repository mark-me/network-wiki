"""Unit tests for layout.py."""
import pytest
from network_wiki import LayoutConfig, ThemeConfig, BOOTSWATCH_THEMES
from network_wiki.layout import bootswatch_css_url, bootswatch_base_scheme


class TestBootswatchCatalogue:
    def test_known_light_theme(self):
        assert BOOTSWATCH_THEMES["flatly"] == "light"

    def test_known_dark_theme(self):
        assert BOOTSWATCH_THEMES["darkly"] == "dark"

    def test_all_values_are_light_or_dark(self):
        assert all(v in ("light", "dark") for v in BOOTSWATCH_THEMES.values())

    def test_at_least_20_themes(self):
        assert len(BOOTSWATCH_THEMES) >= 20


class TestBootswatchHelpers:
    def test_css_url_none_returns_bootstrap(self):
        url = bootswatch_css_url(None)
        assert "bootstrap@" in url
        assert "bootswatch" not in url

    def test_css_url_theme_returns_bootswatch(self):
        url = bootswatch_css_url("flatly")
        assert "bootswatch" in url
        assert "flatly" in url

    def test_css_url_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown Bootswatch theme"):
            bootswatch_css_url("nonexistent")

    def test_base_scheme_none_is_light(self):
        assert bootswatch_base_scheme(None) == "light"

    def test_base_scheme_dark_theme(self):
        assert bootswatch_base_scheme("darkly") == "dark"

    def test_base_scheme_light_theme(self):
        assert bootswatch_base_scheme("flatly") == "light"


class TestThemeConfig:
    def test_default_has_no_bootswatch(self):
        t = ThemeConfig()
        assert t.bootswatch_theme is None

    def test_valid_theme_accepted(self):
        t = ThemeConfig(bootswatch_theme="minty")
        assert t.bootswatch_theme == "minty"

    def test_theme_name_lowercased(self):
        t = ThemeConfig(bootswatch_theme="Flatly")
        assert t.bootswatch_theme == "flatly"

    def test_invalid_theme_raises(self):
        with pytest.raises(ValueError, match="Unknown Bootswatch theme"):
            ThemeConfig(bootswatch_theme="nonexistent")

    def test_css_url_property_no_bootswatch(self):
        t = ThemeConfig()
        assert "bootstrap@" in t.css_url
        assert "bootswatch" not in t.css_url

    def test_css_url_property_with_bootswatch(self):
        t = ThemeConfig(bootswatch_theme="darkly")
        assert "bootswatch" in t.css_url
        assert "darkly" in t.css_url

    def test_base_scheme_light(self):
        assert ThemeConfig(bootswatch_theme="flatly").base_scheme == "light"

    def test_base_scheme_dark(self):
        assert ThemeConfig(bootswatch_theme="darkly").base_scheme == "dark"

    def test_base_scheme_no_bootswatch_is_light(self):
        assert ThemeConfig().base_scheme == "light"

    def test_default_lang_is_en(self):
        assert ThemeConfig().lang == "en"


class TestLayoutConfig:
    def test_to_vis_has_physics_and_interaction(self):
        cfg = LayoutConfig().to_vis()
        assert "physics" in cfg
        assert "interaction" in cfg

    def test_hierarchical_disables_physics(self):
        cfg = LayoutConfig(hierarchical=True).to_vis()
        assert cfg["physics"]["enabled"] is False
        assert "layout" in cfg

    def test_hierarchical_direction(self):
        cfg = LayoutConfig(hierarchical=True, hierarchical_direction="UD").to_vis()
        assert cfg["layout"]["hierarchical"]["direction"] == "UD"

    def test_physics_disabled(self):
        cfg = LayoutConfig(physics_enabled=False).to_vis()
        assert cfg["physics"]["enabled"] is False
