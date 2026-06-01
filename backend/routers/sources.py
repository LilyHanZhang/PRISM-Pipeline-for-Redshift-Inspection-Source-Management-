import os
import re
import numpy as np
from fastapi import APIRouter, HTTPException
from backend import config
from backend.state import get_merged_catalog, get_source_flags

router = APIRouter(prefix="/api/sources", tags=["sources"])


def _safe_float(val):
    """Safely convert a value to float, returning None if impossible."""
    if val is None:
        return None
    try:
        import numpy.ma as ma
        if ma.is_masked(val):
            return None
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def build_source_record(row, flags):
    """Build a source record dict from a catalog row and flags."""
    id_col = config.CATALOG_ID_COL
    ra_col = config.CATALOG_RA_COL
    dec_col = config.CATALOG_DEC_COL

    ra = None
    for c in [ra_col, "RA_1", "RA"]:
        if c and c in row.colnames:
            ra = _safe_float(row[c])
            if ra is not None:
                break

    dec = None
    for c in [dec_col, "DEC_1", "DEC"]:
        if c and c in row.colnames:
            dec = _safe_float(row[c])
            if dec is not None:
                break

    z_spec = None
    for col_name in [config.SPEC_CAT_ZSPEC_COL, "zspec", "z_spec", "ZSPEC"]:
        if col_name and col_name in row.colnames:
            z_spec = _safe_float(row[col_name])
            if z_spec is not None:
                break

    z_phot = None
    for col_name in [config.PHOT_CAT_ZPHOT_COL, "z_phot", "Z_PHOT", "zphot"]:
        if col_name and col_name in row.colnames:
            z_phot = _safe_float(row[col_name])
            if z_phot is not None:
                break

    phot_bands = {}
    for col in row.colnames:
        if col.endswith("_MAG") or col.endswith("_MAG_e"):
            val = _safe_float(row[col])
            if val is not None:
                phot_bands[col] = val

    return {
        "id": str(row[id_col]),
        "ra": ra,
        "dec": dec,
        "z_phot": z_phot,
        "z_spec": z_spec,
        "tags": [],
        "has_1d": flags.get("has_1d", {}),
        "has_2d": flags.get("has_2d", {}),
        "has_pdf": flags.get("has_pdf", {}),
        "has_sed": flags.get("has_sed", False),
        "has_rgb": flags.get("has_rgb", False),
        "has_spec": any(flags.get("has_1d", {}).values()) or any(flags.get("has_2d", {}).values()),
        "phot_bands": phot_bands,
    }


@router.get("/")
def get_sources(has_spec: bool = False):
    """Full source list with flags, z values, tags.

    If has_spec=True, only return sources with at least one grism spectrum.
    """
    catalog = get_merged_catalog()
    if catalog is None:
        return []

    id_col = config.CATALOG_ID_COL
    records = []
    for row in catalog:
        sid = str(row[id_col])
        flags = get_source_flags(sid)
        rec = build_source_record(row, flags)
        if has_spec and not rec["has_spec"]:
            continue
        records.append(rec)
    return records


@router.get("/search")
def search_sources(q: str = "", tag: str = ""):
    """Filter by ID substring and/or tag."""
    catalog = get_merged_catalog()
    if catalog is None:
        return []

    id_col = config.CATALOG_ID_COL
    results = []
    for row in catalog:
        sid = str(row[id_col])
        if q and q.lower() not in sid.lower():
            continue
        results.append(sid)
    return results


@router.get("/near")
def sources_near(ra: float, dec: float, r: float = 10.0):
    """Sources within radius r arcsec of coords."""
    from backend.utils.coord_search import find_nearby_sources

    catalog = get_merged_catalog()
    if catalog is None:
        return []

    max_r = min(r, config.COORD_SEARCH_MAX_RADIUS_ARCSEC)
    nearby = find_nearby_sources(ra, dec, max_r, catalog)
    return nearby


@router.get("/{source_id}")
def get_source(source_id: str):
    """Single source record."""
    catalog = get_merged_catalog()
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not available")

    id_col = config.CATALOG_ID_COL
    for row in catalog:
        if str(row[id_col]) == source_id:
            flags = get_source_flags(source_id)
            return build_source_record(row, flags)

    raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
