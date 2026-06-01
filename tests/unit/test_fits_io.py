import pytest
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestFitsIO:
    def test_load_catalog_nonexistent(self):
        from backend.utils.fits_io import load_catalog
        result = load_catalog("/nonexistent/path/file.fits")
        assert result is None

    def test_load_catalog_valid(self, tmp_path):
        from astropy.table import Table
        import numpy as np
        from backend.utils.fits_io import load_catalog

        cat = Table()
        cat["ID"] = np.array([1, 2, 3])
        cat["RA"] = np.array([10.0, 20.0, 30.0])
        filepath = tmp_path / "test_cat.fits"
        cat.write(str(filepath), format="fits", overwrite=True)

        result = load_catalog(str(filepath))
        assert result is not None
        assert len(result) == 3
        assert "ID" in result.colnames

    def test_merge_catalogs(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.fits_io import merge_catalogs

        phot = Table()
        phot["ID"] = np.array([1, 2, 3])
        phot["RA"] = np.array([10.0, 20.0, 30.0])
        phot["DEC"] = np.array([1.0, 2.0, 3.0])

        spec = Table()
        spec["ID"] = np.array([1, 2, 4])
        spec["z_spec"] = np.array([1.0, 2.0, 4.0])

        merged = merge_catalogs(spec, phot)
        assert len(merged) == 3
        assert "z_spec" in merged.colnames

    def test_merge_catalogs_no_phot(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.fits_io import merge_catalogs

        spec = Table()
        spec["ID"] = np.array([1, 2])
        spec["RA"] = np.array([10.0, 20.0])

        merged = merge_catalogs(spec, None)
        assert merged is spec

    def test_merge_catalogs_no_spec(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.fits_io import merge_catalogs

        phot = Table()
        phot["ID"] = np.array([1, 2])
        phot["RA"] = np.array([10.0, 20.0])

        merged = merge_catalogs(None, phot)
        assert merged is phot


class TestCoordSearch:
    def test_find_nearby_sources_empty_catalog(self):
        from backend.utils.coord_search import find_nearby_sources
        result = find_nearby_sources(150.0, 2.0, 10.0, None)
        assert result == []

    def test_find_nearby_sources_no_coord_cols(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.coord_search import find_nearby_sources

        cat = Table()
        cat["ID"] = np.array([1, 2])
        result = find_nearby_sources(150.0, 2.0, 10.0, cat)
        assert result == []

    def test_find_nearby_sources_basic(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.coord_search import find_nearby_sources

        cat = Table()
        cat["ID"] = np.array([1, 2, 3])
        cat["RA"] = np.array([150.0, 150.001, 160.0])
        cat["DEC"] = np.array([2.0, 2.001, 10.0])

        results = find_nearby_sources(150.0, 2.0, 10.0, cat)
        assert len(results) >= 1
        assert results[0]["id"] == "1"

    def test_find_nearby_sources_sorted_by_separation(self):
        from astropy.table import Table
        import numpy as np
        from backend.utils.coord_search import find_nearby_sources

        cat = Table()
        cat["ID"] = np.array([1, 2, 3])
        cat["RA"] = np.array([150.0, 150.0001, 150.001])
        cat["DEC"] = np.array([2.0, 2.0, 2.0])

        results = find_nearby_sources(150.0, 2.0, 100.0, cat)
        assert len(results) == 3
        assert results[0]["separation_arcsec"] <= results[1]["separation_arcsec"]
