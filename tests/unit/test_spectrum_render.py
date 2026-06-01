import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestSpectrumRender:
    def test_get_1d_path_pattern(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import importlib
        import backend.config
        importlib.reload(backend.config)

        from backend.utils.spectrum_render import get_1d_path

        spec_dir = tmp_path / "sapphires_edr_1d_spec"
        spec_dir.mkdir()
        test_file = spec_dir / "spec_1d_M0416_F356W_ID133_R.fits"
        test_file.touch()

        path = get_1d_path("133", "F356W", "R")
        assert path is not None
        assert "spec_1d_M0416_F356W_ID133_R.fits" in path

    def test_get_1d_path_nonexistent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import importlib
        import backend.config
        importlib.reload(backend.config)

        from backend.utils.spectrum_render import get_1d_path

        path = get_1d_path("999", "F356W", "R")
        assert path is None

    def test_get_2d_path_pattern(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import importlib
        import backend.config
        importlib.reload(backend.config)

        from backend.utils.spectrum_render import get_2d_path

        spec_dir = tmp_path / "sapphires_edr_2d_spec"
        spec_dir.mkdir()
        test_file = spec_dir / "spec_2d_M0416_F444W_ID203_C.fits"
        test_file.touch()

        path = get_2d_path("203", "F444W", "C")
        assert path is not None
        assert "spec_2d_M0416_F444W_ID203_C.fits" in path

    def test_apply_scale_zscale(self):
        import numpy as np
        from backend.utils.spectrum_render import apply_scale

        data = np.random.rand(10, 10) * 100
        result = apply_scale(data, "zscale")
        assert result is not None
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_linear(self):
        import numpy as np
        from backend.utils.spectrum_render import apply_scale

        data = np.random.rand(10, 10) * 100
        result = apply_scale(data, "linear")
        assert result is not None
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_sqrt(self):
        import numpy as np
        from backend.utils.spectrum_render import apply_scale

        data = np.random.rand(10, 10) * 100
        result = apply_scale(data, "sqrt")
        assert result is not None
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_none(self):
        from backend.utils.spectrum_render import apply_scale
        result = apply_scale(None, "zscale")
        assert result is None

    def test_render_2d_png_nonexistent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import importlib
        import backend.config
        importlib.reload(backend.config)

        from backend.utils.spectrum_render import render_2d_png

        result = render_2d_png("999", "F356W", "R")
        assert result is None
