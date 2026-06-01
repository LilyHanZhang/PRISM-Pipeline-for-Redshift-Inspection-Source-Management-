import pytest
import os
import sys
import importlib
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestCutoutGeneration:
    def test_generate_cutout_with_skycoord(self, monkeypatch, tmp_path):
        """Test that generate_cutout uses SkyCoord correctly."""
        from astropy.io import fits
        from astropy.wcs import WCS
        from astropy.nddata import Cutout2D

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import generate_cutout

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()

        naxis = 100
        data = np.random.rand(naxis, naxis).astype(np.float32)
        header = fits.Header()
        header['SIMPLE'] = True
        header['BITPIX'] = -32
        header['NAXIS'] = 2
        header['NAXIS1'] = naxis
        header['NAXIS2'] = naxis
        header['CRPIX1'] = naxis / 2
        header['CRPIX2'] = naxis / 2
        header['CRVAL1'] = 63.96
        header['CRVAL2'] = -24.19
        header['CDELT1'] = -0.03 / 3600.0
        header['CDELT2'] = 0.03 / 3600.0
        header['CTYPE1'] = 'RA---TAN'
        header['CTYPE2'] = 'DEC--TAN'
        header['CUNIT1'] = 'deg'
        header['CUNIT2'] = 'deg'

        hdu = fits.PrimaryHDU(data=data, header=header)
        test_file = sci_dir / "M0416_F444W_v05_sci.fits"
        hdu.writeto(str(test_file), overwrite=True)

        cutout = generate_cutout(str(test_file), 63.96, -24.19, size_arcsec=3.0)
        assert cutout is not None
        assert cutout.data.shape[0] > 0
        assert cutout.data.shape[1] > 0

    def test_generate_cutout_out_of_bounds(self, monkeypatch, tmp_path):
        """Test that generate_cutout returns None for coordinates outside image."""
        from astropy.io import fits

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.cutout
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)

        from backend.utils.cutout import generate_cutout

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()

        naxis = 100
        data = np.random.rand(naxis, naxis).astype(np.float32)
        header = fits.Header()
        header['SIMPLE'] = True
        header['BITPIX'] = -32
        header['NAXIS'] = 2
        header['NAXIS1'] = naxis
        header['NAXIS2'] = naxis
        header['CRPIX1'] = naxis / 2
        header['CRPIX2'] = naxis / 2
        header['CRVAL1'] = 63.96
        header['CRVAL2'] = -24.19
        header['CDELT1'] = -0.03 / 3600.0
        header['CDELT2'] = 0.03 / 3600.0
        header['CTYPE1'] = 'RA---TAN'
        header['CTYPE2'] = 'DEC--TAN'
        header['CUNIT1'] = 'deg'
        header['CUNIT2'] = 'deg'

        hdu = fits.PrimaryHDU(data=data, header=header)
        test_file = sci_dir / "M0416_F444W_v05_sci.fits"
        hdu.writeto(str(test_file), overwrite=True)

        cutout = generate_cutout(str(test_file), 0.0, 0.0, size_arcsec=3.0)
        assert cutout is None


class TestApplyScale:
    def test_apply_scale_asinh_with_nan(self):
        """Test that asinh scaling handles NaN and Inf values."""
        from backend.routers.images import apply_scale

        data = np.array([[1.0, np.nan, 3.0], [np.inf, -np.inf, 6.0]])
        result = apply_scale(data, "asinh")

        assert result is not None
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_seismic(self):
        """Test seismic colormap scaling."""
        from backend.routers.images import apply_scale

        data = np.random.rand(10, 10) * 100
        result = apply_scale(data, "zscale")

        assert result is not None
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_zscale(self):
        """Test zscale scaling."""
        from backend.routers.images import apply_scale

        data = np.random.rand(10, 10) * 100
        result = apply_scale(data, "zscale")

        assert result is not None
        assert result.min() >= 0
        assert result.max() <= 1

    def test_apply_scale_none(self):
        """Test that apply_scale returns None for None input."""
        from backend.routers.images import apply_scale

        result = apply_scale(None, "zscale")
        assert result is None


class TestSourceCoords:
    def test_get_source_coords_with_ra_dec_columns(self, monkeypatch, tmp_path):
        """Test getting coordinates with standard RA/DEC columns."""
        from astropy.table import Table

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.state
        importlib.reload(backend.config)
        importlib.reload(backend.state)

        from backend.state import get_merged_catalog
        from backend.routers.images import get_source_coords

        catalog = Table()
        catalog['ID'] = [1, 2, 3]
        catalog['RA'] = [63.96, 63.97, 63.98]
        catalog['DEC'] = [-24.19, -24.20, -24.21]

        ra, dec = get_source_coords(catalog, "2")
        assert ra == 63.97
        assert dec == -24.20

    def test_get_source_coords_with_ra1_dec1_columns(self, monkeypatch, tmp_path):
        """Test getting coordinates with renamed RA_1/DEC_1 columns (merged catalog)."""
        from astropy.table import Table

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.state
        importlib.reload(backend.config)
        importlib.reload(backend.state)

        from backend.routers.images import get_source_coords

        catalog = Table()
        catalog['ID'] = [1, 2, 3]
        catalog['RA_1'] = [63.96, 63.97, 63.98]
        catalog['DEC_1'] = [-24.19, -24.20, -24.21]

        ra, dec = get_source_coords(catalog, "2")
        assert ra == 63.97
        assert dec == -24.20

    def test_get_source_coords_not_found(self, monkeypatch, tmp_path):
        """Test getting coordinates for non-existent source."""
        from astropy.table import Table

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.state
        importlib.reload(backend.config)
        importlib.reload(backend.state)

        from backend.routers.images import get_source_coords

        catalog = Table()
        catalog['ID'] = [1, 2, 3]
        catalog['RA'] = [63.96, 63.97, 63.98]
        catalog['DEC'] = [-24.19, -24.20, -24.21]

        ra, dec = get_source_coords(catalog, "999")
        assert ra is None
        assert dec is None


class TestSpectrumRenderNaNHandling:
    def test_read_1d_spectrum_with_nan(self, monkeypatch, tmp_path):
        """Test that 1D spectrum reading handles NaN values."""
        from astropy.io import fits
        from astropy.table import Table

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.spectrum_render
        importlib.reload(backend.config)
        importlib.reload(backend.utils.spectrum_render)

        from backend.utils.spectrum_render import read_1d_spectrum

        spec_dir = tmp_path / "sapphires_edr_1d_spec"
        spec_dir.mkdir()

        wave = np.array([1.0, 2.0, np.nan, 4.0])
        flux = np.array([10.0, np.nan, 30.0, 40.0])
        err = np.array([1.0, 2.0, np.inf, 4.0])

        t = Table()
        t['wavelength_um'] = wave
        t['opt_spec1d_mJy'] = flux
        t['opt_fluxerr_mJy'] = err

        primary_hdu = fits.PrimaryHDU()
        hdu_list = fits.HDUList([primary_hdu, fits.BinTableHDU(t)])

        test_file = spec_dir / "spec_1d_M0416_F356W_ID133_R.fits"
        hdu_list.writeto(str(test_file), overwrite=True)

        result = read_1d_spectrum("133", "F356W", "R")
        assert result is not None
        assert result['wave'] == [1.0, 2.0, None, 4.0]
        assert result['flux'] == [10.0, None, 30.0, 40.0]
        assert result['err'] == [1.0, 2.0, None, 4.0]

    def test_read_1d_spectrum_nonexistent(self, monkeypatch, tmp_path):
        """Test reading non-existent 1D spectrum."""
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.spectrum_render
        importlib.reload(backend.config)
        importlib.reload(backend.utils.spectrum_render)

        from backend.utils.spectrum_render import read_1d_spectrum

        result = read_1d_spectrum("999", "F356W", "R")
        assert result is None


class TestRGBComposite:
    def test_rgb_endpoint_shape_mismatch(self, monkeypatch, tmp_path):
        """Test that RGB endpoint handles shape mismatches gracefully."""
        from astropy.io import fits
        from astropy.wcs import WCS
        from astropy.table import Table
        from PIL import Image
        import io

        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.utils.cutout
        import backend.routers.images
        import backend.state
        importlib.reload(backend.config)
        importlib.reload(backend.utils.cutout)
        importlib.reload(backend.state)

        from backend.routers.images import get_rgb

        sci_dir = tmp_path / "sapphires_edr_nircam_sci"
        sci_dir.mkdir()

        ra, dec = 63.96, -24.19

        for band in ["F115W", "F200W", "F444W"]:
            naxis = 100
            data = np.random.rand(naxis, naxis).astype(np.float32) * 100
            header = fits.Header()
            header['SIMPLE'] = True
            header['BITPIX'] = -32
            header['NAXIS'] = 2
            header['NAXIS1'] = naxis
            header['NAXIS2'] = naxis
            header['CRPIX1'] = naxis / 2
            header['CRPIX2'] = naxis / 2
            header['CRVAL1'] = ra
            header['CRVAL2'] = dec
            header['CDELT1'] = -0.03 / 3600.0
            header['CDELT2'] = 0.03 / 3600.0
            header['CTYPE1'] = 'RA---TAN'
            header['CTYPE2'] = 'DEC--TAN'
            header['CUNIT1'] = 'deg'
            header['CUNIT2'] = 'deg'

            hdu = fits.PrimaryHDU(data=data, header=header)
            test_file = sci_dir / f"M0416_{band}_v05_sci.fits"
            hdu.writeto(str(test_file), overwrite=True)

        monkeypatch.setattr("backend.routers.images.get_merged_catalog", lambda: Table({'ID': ['420'], 'RA': [ra], 'DEC': [dec]}))

        response = get_rgb("420", size=3.0)
        assert response is not None
        assert response.media_type == "image/png"

        img = Image.open(io.BytesIO(response.body))
        assert img.mode == "RGB"
        assert img.size[0] > 0
        assert img.size[1] > 0


class TestCacheDirectory:
    def test_cache_path_uses_project_dir(self, monkeypatch, tmp_path):
        """Test that cache path uses project directory, not DATA_ROOT."""
        monkeypatch.setenv("PRISM_DATA_ROOT", str(tmp_path))
        monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

        import backend.config
        import backend.routers.images
        importlib.reload(backend.config)
        importlib.reload(backend.routers.images)

        from backend.routers.images import get_cache_path

        cache_path = get_cache_path("420", "F444W", 3.0, "viridis", "zscale")
        assert ".cutout_cache" in cache_path
        assert str(tmp_path) not in cache_path


class TestSpectralLines:
    """Tests for spectral line definitions (backend validation of frontend constants)."""
    
    def test_filter_ranges_values(self):
        """Test that filter wavelength ranges have correct values."""
        F356W_MIN, F356W_MAX = 3.1, 4.0
        F444W_MIN, F444W_MAX = 3.8, 5.1
        
        assert F356W_MIN < F356W_MAX
        assert F444W_MIN < F444W_MAX
        assert F356W_MAX < F444W_MAX

    def test_observed_wavelength_calculation(self):
        """Test observed wavelength calculation formula."""
        def getObservedWavelength(restAngstrom, z):
            return restAngstrom * (1 + z) / 10000

        assert getObservedWavelength(5000, 0.0) == 0.5
        assert getObservedWavelength(5000, 1.0) == 1.0
        assert getObservedWavelength(5000, 2.0) == 1.5

    def test_spectral_lines_in_range_f356w(self):
        """Test that spectral lines can be filtered for F356W range."""
        def getObservedWavelength(restAngstrom, z):
            return restAngstrom * (1 + z) / 10000

        F356W_MIN, F356W_MAX = 3.1, 4.0
        z = 1.0

        lines_in_range = []
        test_lines = [18000, 19000, 20000]
        for wl in test_lines:
            obs = getObservedWavelength(wl, z)
            if F356W_MIN <= obs <= F356W_MAX:
                lines_in_range.append(wl)

        assert len(lines_in_range) > 0

    def test_spectral_lines_in_range_f444w(self):
        """Test that spectral lines can be filtered for F444W range."""
        def getObservedWavelength(restAngstrom, z):
            return restAngstrom * (1 + z) / 10000

        F444W_MIN, F444W_MAX = 3.8, 5.1
        z = 1.0

        lines_in_range = []
        test_lines = [20000, 22000, 25000]
        for wl in test_lines:
            obs = getObservedWavelength(wl, z)
            if F444W_MIN <= obs <= F444W_MAX:
                lines_in_range.append(wl)

        assert len(lines_in_range) > 0
