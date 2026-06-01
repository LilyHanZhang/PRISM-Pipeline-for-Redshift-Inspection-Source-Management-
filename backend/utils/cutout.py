import os
import re
import numpy as np
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.wcs import WCS
from astropy.io import fits
from backend import config


def generate_cutout(hdu_or_path, ra, dec, size_arcsec=5.0):
    """Generate a cutout from a FITS file at the given coordinates."""
    if isinstance(hdu_or_path, str):
        with fits.open(hdu_or_path) as hdul:
            data = hdul[0].data
            wcs = WCS(hdul[0].header)
    else:
        data = hdu_or_path[0].data
        wcs = WCS(hdu_or_path[0].header)

    if data is None:
        return None

    position = (ra, dec) * u.deg
    size = size_arcsec * u.arcsec

    try:
        cutout = Cutout2D(data, position, size, wcs=wcs)
        return cutout
    except Exception:
        return None


def get_nircam_band_path(band):
    """Get the FITS file path for a given NIRCam band."""
    sci_dir = os.path.join(config.DATA_ROOT, config.NIRCAM_DIR)
    if not os.path.exists(sci_dir):
        return None

    # Pattern: {field}_{band}_v{ver}_sci.fits
    pattern = re.compile(
        rf"^{re.escape(config.FIELD_NAME)}_{re.escape(band)}_v\d+_sci\.fits$"
    )
    for fname in os.listdir(sci_dir):
        if pattern.match(fname):
            return os.path.join(sci_dir, fname)
    return None


def scan_available_bands():
    """Scan the NIRCam directory for available bands."""
    sci_dir = os.path.join(config.DATA_ROOT, config.NIRCAM_DIR)
    if not os.path.exists(sci_dir):
        return []

    bands = set()
    # Pattern: {field}_{band}_v{ver}_sci.fits
    pattern = re.compile(
        rf"^{re.escape(config.FIELD_NAME)}_(.+?)_v\d+_sci\.fits$"
    )
    for fname in os.listdir(sci_dir):
        m = pattern.match(fname)
        if m:
            bands.add(m.group(1))
    return sorted(bands)
