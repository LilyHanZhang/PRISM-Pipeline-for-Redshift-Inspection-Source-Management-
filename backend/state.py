import os
import json
import shutil
from backend import config
from backend.utils.fits_io import load_spec_cat, load_phot_cat, merge_catalogs
from backend.utils.spectrum_render import get_1d_path, get_2d_path

_merged_catalog = None
_source_flags = None
_tags_db = None


def init_state():
    """Initialize all state at startup."""
    global _merged_catalog, _source_flags, _tags_db

    spec_cat = load_spec_cat()
    phot_cat = load_phot_cat()
    _merged_catalog = merge_catalogs(spec_cat, phot_cat)
    _source_flags = _scan_source_flags()
    _tags_db = _load_tags_db()


def get_merged_catalog():
    """Get the merged catalog."""
    return _merged_catalog


def get_source_flags(source_id):
    """Get availability flags for a source."""
    if _source_flags is None:
        return {}
    return _source_flags.get(source_id, {})


def get_tags_db():
    """Get the tags database."""
    global _tags_db
    if _tags_db is None:
        _tags_db = _load_tags_db()
    return _tags_db


def save_tags_db(db):
    """Save the tags database to disk."""
    global _tags_db
    _tags_db = db

    db_path = config.TAGS_DB_PATH
    bak_path = db_path + ".bak"

    if os.path.exists(db_path):
        shutil.copy2(db_path, bak_path)

    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)


def _load_tags_db():
    """Load the tags database from disk."""
    db_path = config.TAGS_DB_PATH
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sources": {}}


def _scan_source_flags():
    """Scan data directories and build availability flags for all sources."""
    if _merged_catalog is None:
        return {}

    id_col = config.CATALOG_ID_COL
    flags = {}

    for row in _merged_catalog:
        sid = str(row[id_col])
        flags[sid] = {
            "has_1d": _scan_1d_flags(sid),
            "has_2d": _scan_2d_flags(sid),
            "has_pdf": _scan_pdf_flags(sid),
            "has_sed": True,
            "has_rgb": True,
        }

    return flags


def _scan_1d_flags(source_id):
    """Check which 1D spectra exist for a source."""
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            result[key] = get_1d_path(source_id, f, o) is not None
    return result


def _scan_2d_flags(source_id):
    """Check which 2D spectra exist for a source."""
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            result[key] = get_2d_path(source_id, f, o) is not None
    return result


def _scan_pdf_flags(source_id):
    """Check which PDFs exist for a source."""
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            pdf_filename = config.PDF_PATTERN.format(
                field=config.FIELD_NAME,
                filter=f,
                id=source_id,
                orient=o,
            )
            pdf_path = os.path.join(config.DATA_ROOT, config.PDF_DIR, pdf_filename)
            result[key] = os.path.exists(pdf_path)
    return result
