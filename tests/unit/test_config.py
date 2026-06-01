import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestConfig:
    def test_data_root_default(self, monkeypatch):
        monkeypatch.delenv("PRISM_DATA_ROOT", raising=False)
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert backend.config.DATA_ROOT == "../data"

    def test_data_root_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert backend.config.DATA_ROOT == str(tmp_path)

    def test_field_name_default(self, monkeypatch):
        monkeypatch.delenv("PRISM_FIELD_NAME", raising=False)
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert backend.config.FIELD_NAME == "M0416"

    def test_field_name_from_env(self, monkeypatch):
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0417")
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert backend.config.FIELD_NAME == "M0417"

    def test_spec_patterns_include_field(self, monkeypatch):
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert "{field}" in backend.config.SPEC_1D_PATTERN
        assert "{field}" in backend.config.SPEC_2D_PATTERN
        assert "{field}" in backend.config.PDF_PATTERN

    def test_rgb_bands_mapping(self, monkeypatch):
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert "r" in backend.config.RGB_BANDS
        assert "g" in backend.config.RGB_BANDS
        assert "b" in backend.config.RGB_BANDS

    def test_tag_vocabulary_not_empty(self, monkeypatch):
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert len(backend.config.TAG_VOCABULARY) > 0

    def test_spec_filters_and_orients(self, monkeypatch):
        import importlib
        import backend.config
        importlib.reload(backend.config)
        assert backend.config.SPEC_2D_FILTERS == ["F356W", "F444W"]
        assert backend.config.SPEC_2D_ORIENTS == ["R", "C"]
