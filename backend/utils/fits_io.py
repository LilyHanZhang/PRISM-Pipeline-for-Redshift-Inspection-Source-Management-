import os
import re
import numpy as np
from astropy.table import Table, join
from backend import config


def load_catalog(filepath):
    """Load a FITS catalog file."""
    if not os.path.exists(filepath):
        return None
    return Table.read(filepath)


def load_spec_cat():
    """Load the spectroscopic catalog."""
    path = os.path.join(config.DATA_ROOT, config.SPEC_CAT_FILE)
    return load_catalog(path)


def load_phot_cat():
    """Load the photometric catalog with z_phot from HDU 2."""
    path = os.path.join(config.DATA_ROOT, config.PHOT_CAT_FILE)
    if not os.path.exists(path):
        return None

    phot_tab = Table.read(path, hdu=1)

    try:
        zphot_tab = Table.read(path, hdu=2)
        id_col = config.CATALOG_ID_COL
        z_col = "z_map"
        if id_col in zphot_tab.colnames and z_col in zphot_tab.colnames:
            zphot_simple = zphot_tab[id_col, z_col]
            zphot_simple.rename_column(z_col, "z_phot")
            phot_tab = join(phot_tab, zphot_simple, keys=id_col, join_type="left")
    except Exception:
        pass

    return phot_tab


def merge_catalogs(spec_cat, phot_cat):
    """Merge spec and phot catalogs on ID column.

    phot_cat is the primary catalog (contains all sources).
    spec_cat data is joined onto it (only sources with spectra).
    """
    if phot_cat is None and spec_cat is None:
        return None
    if phot_cat is None:
        return spec_cat
    if spec_cat is None:
        return phot_cat

    id_col = config.CATALOG_ID_COL
    merged = join(phot_cat, spec_cat, keys=id_col, join_type="left")
    return merged


def get_source_id_col(table):
    """Get the ID column name from a table."""
    return config.CATALOG_ID_COL
