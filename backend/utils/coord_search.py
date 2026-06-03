import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from backend import config


def find_nearby_sources(ra, dec, radius_arcsec, catalog):
    """Find sources within radius arcsec of the given coordinates."""
    if catalog is None:
        return []

    id_col = config.CATALOG_ID_COL

    # Find RA/DEC columns (may be RA_1/DEC_1 after merge, or RA/DEC)
    ra_col = None
    for c in [config.CATALOG_RA_COL, "RA_1", "RA"]:
        if c and c in catalog.colnames:
            ra_col = c
            break

    dec_col = None
    for c in [config.CATALOG_DEC_COL, "DEC_1", "DEC"]:
        if c and c in catalog.colnames:
            dec_col = c
            break

    if ra_col is None or dec_col is None:
        return []

    target = SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))
    sources = SkyCoord(
        ra=catalog[ra_col], dec=catalog[dec_col], unit=(u.deg, u.deg)
    )

    sep = target.separation(sources)
    mask = sep <= radius_arcsec * u.arcsec

    results = []
    for idx in np.where(mask)[0]:
        results.append(
            {
                "id": str(catalog[id_col][idx]),
                "separation_arcsec": sep[idx].arcsec,
                "ra": float(catalog[ra_col][idx]),
                "dec": float(catalog[dec_col][idx]),
            }
        )

    results.sort(key=lambda x: x["separation_arcsec"])
    return results
