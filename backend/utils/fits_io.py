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
    """Load the photometric catalog."""
    path = os.path.join(config.DATA_ROOT, config.PHOT_CAT_FILE)
    return load_catalog(path)


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
