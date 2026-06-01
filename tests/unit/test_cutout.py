import pytest
import os
import sys
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCutout:
    def test_get_nircam_band_path(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()
        test_file = sci_dir / "M0416_F115W_v05_sci.fits"
        test_file.touch()

        # Force reload config and cutout modules
        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import get_nircam_band_path

        path = get_nircam_band_path("F115W")
        assert path is not None
        assert "F115W" in path

    def test_get_nircam_band_path_nonexistent(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import get_nircam_band_path

        path = get_nircam_band_path("F999W")
        assert path is None

    def test_scan_available_bands(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()
        (sci_dir / "M0416_F070W_v05_sci.fits").touch()
        (sci_dir / "M0416_F115W_v05_sci.fits").touch()
        (sci_dir / "M0416_F200W_v05_sci.fits").touch()

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import scan_available_bands

        bands = scan_available_bands()
        assert "F070W" in bands
        assert "F115W" in bands
        assert "F200W" in bands
        assert len(bands) == 3

    def test_scan_available_bands_empty_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import scan_available_bands

        bands = scan_available_bands()
        assert bands == []

    def test_scan_available_bands_nonexistent_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import scan_available_bands

        bands = scan_available_bands()
        assert bands == []
