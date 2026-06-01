import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Create a temporary data directory with mock config."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    (data_dir / "sapphires_edr_1d_spec").mkdir()
    (data_dir / "sapphires_edr_2d_spec").mkdir()
    (data_dir / "sapphires_edr_nircam_sci").mkdir()
    (data_dir / "sapphires_edr_spec_pdf").mkdir()
    (data_dir / "cutout_cache").mkdir()

    monkeypatch.setenv("PRISM_DATA_ROOT", str(data_dir))
    monkeypatch.setenv("PRISM_FIELD_NAME", "M0416")

    import importlib
    import backend.config
    importlib.reload(backend.config)

    return data_dir


@pytest.fixture
def mock_catalogs(tmp_path):
    """Create mock FITS catalogs."""
    from astropy.table import Table
    import numpy as np

    phot_cat = Table()
    phot_cat["ID"] = np.array([133, 203, 323, 408, 420])
    phot_cat["RA"] = np.array([150.123, 150.234, 150.345, 150.456, 150.567])
    phot_cat["DEC"] = np.array([2.345, 2.456, 2.567, 2.678, 2.789])

    spec_cat = Table()
    spec_cat["ID"] = np.array([133, 203, 408])
    spec_cat["zspec"] = np.array([1.19, 2.34, 3.21])

    return spec_cat, phot_cat


@pytest.fixture
def app(mock_config, mock_catalogs, tmp_path):
    """Create a test FastAPI app."""
    from fastapi.testclient import TestClient
    from backend.main import app as fastapi_app
    from backend.state import init_state, _merged_catalog, get_merged_catalog
    from backend.utils.fits_io import merge_catalogs
    import backend.config as config

    spec_cat, phot_cat = mock_catalogs

    spec_cat.write(os.path.join(config.DATA_ROOT, config.SPEC_CAT_FILE), format="fits", overwrite=True)
    phot_cat.write(os.path.join(config.DATA_ROOT, config.PHOT_CAT_FILE), format="fits", overwrite=True)

    import importlib
    import backend.state
    importlib.reload(backend.state)

    from backend.state import init_state, get_merged_catalog

    init_state()

    return TestClient(fastapi_app)


@pytest.fixture
def tags_db_file(tmp_path, monkeypatch):
    """Create a temporary tags_db.json."""
    import json
    db_path = tmp_path / "tags_db.json"
    db_content = {
        "sources": {
            "133": {"tags": ["galaxy", "emission"], "z_spec": 1.19, "notes": ""},
            "203": {"tags": ["AGN"], "z_spec": 2.34, "notes": ""},
        }
    }
    db_path.write_text(json.dumps(db_content))
    monkeypatch.setattr("backend.config.TAGS_DB_PATH", str(db_path))
    return db_path
