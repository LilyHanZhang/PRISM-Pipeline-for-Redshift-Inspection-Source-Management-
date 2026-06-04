"""Unit tests for panel_app.py"""
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.fixture(scope="module")
def panel_app():
    """Import and initialize panel_app module."""
    import panel_app as app
    app.init_state()
    return app


class TestPanelAppInit:
    """Test panel app initialization."""

    def test_catalog_loaded(self, panel_app):
        catalog = panel_app.get_merged_catalog()
        assert catalog is not None
        assert len(catalog) > 0

    def test_source_flags_loaded(self, panel_app):
        assert panel_app._source_flags is not None
        assert len(panel_app._source_flags) > 0

    def test_tags_db_loaded(self, panel_app):
        assert panel_app._tags_db is not None
        assert "sources" in panel_app._tags_db


class TestPanelAppSourceRecord:
    """Test source record building."""

    def test_build_source_record(self, panel_app):
        catalog = panel_app.get_merged_catalog()
        rec = panel_app.build_source_record(catalog[0])
        assert "id" in rec
        assert "ra" in rec
        assert "dec" in rec
        assert "z_phot" in rec
        assert "z_spec" in rec
        assert "tags" in rec
        assert "has_1d" in rec
        assert "has_2d" in rec
        assert "has_pdf" in rec
        assert "has_sed" in rec
        assert "has_rgb" in rec
        assert "has_spec_z" in rec
        assert "phot_bands" in rec

    def test_source_record_has_kron(self, panel_app):
        catalog = panel_app.get_merged_catalog()
        rec = panel_app.build_source_record(catalog[0])
        kron_keys = [k for k in rec["phot_bands"] if "KRON" in k]
        assert len(kron_keys) > 0

    def test_source_record_has_mag(self, panel_app):
        catalog = panel_app.get_merged_catalog()
        rec = panel_app.build_source_record(catalog[0])
        mag_keys = [k for k in rec["phot_bands"] if "MAG" in k and "KRON" not in k]
        assert len(mag_keys) > 0


class TestPanelAppSourceList:
    """Test source list filtering."""

    def test_get_all_sources(self, panel_app):
        sources = panel_app.get_all_sources()
        assert len(sources) > 0

    def test_get_sources_with_spec_z(self, panel_app):
        sources = panel_app.get_sources_with_spec_z()
        assert len(sources) > 0
        for s in sources:
            assert s["has_spec_z"] is True

    def test_spec_z_subset_of_all(self, panel_app):
        all_sources = panel_app.get_all_sources()
        spec_z_sources = panel_app.get_sources_with_spec_z()
        all_ids = {s["id"] for s in all_sources}
        for s in spec_z_sources:
            assert s["id"] in all_ids


class TestPanelAppState:
    """Test app state management."""

    def test_default_state(self, panel_app):
        assert panel_app.app_state.selected_id is None
        assert panel_app.app_state.active_filter == 'F356W'
        assert panel_app.app_state.active_orient == 'R'
        assert panel_app.app_state.show_only_spec_z is True

    def test_state_change_filter(self, panel_app):
        panel_app.app_state.active_filter = 'F444W'
        assert panel_app.app_state.active_filter == 'F444W'
        panel_app.app_state.active_filter = 'F356W'

    def test_state_change_orient(self, panel_app):
        panel_app.app_state.active_orient = 'C'
        assert panel_app.app_state.active_orient == 'C'
        panel_app.app_state.active_orient = 'R'


class TestPanelAppImageRendering:
    """Test image rendering functions."""

    def test_apply_scale_zscale(self, panel_app):
        import numpy as np
        data = np.random.randn(100, 100)
        scaled = panel_app._apply_scale(data, 'zscale')
        assert scaled is not None
        assert scaled.min() >= 0
        assert scaled.max() <= 1

    def test_apply_scale_asinh(self, panel_app):
        import numpy as np
        data = np.random.randn(100, 100) + 10
        scaled = panel_app._apply_scale(data, 'asinh')
        assert scaled is not None
        assert scaled.min() >= 0
        assert scaled.max() <= 1

    def test_apply_cmap(self, panel_app):
        import numpy as np
        data = np.random.rand(100, 100)
        img = panel_app._apply_cmap(data, 'viridis')
        assert img is not None
        assert img.size == (100, 100)
