import numpy as np
from astropy.coordinates import SkyCoord
import astropy.units as u
from backend import config


def find_nearby_sources(ra, dec, radius_arcsec, catalog):
    """Find sources within radius arcsec of the given coordinates."""
    if catalog is None:
        return []

    id_col = config.CATALOG_ID_COL
    ra_col = config.CATALOG_RA_COL
    dec_col = config.CATALOG_DEC_COL

    if ra_col not in catalog.colnames or dec_col not in catalog.colnames:
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
