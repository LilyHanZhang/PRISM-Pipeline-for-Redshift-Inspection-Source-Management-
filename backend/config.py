import os

# ── Data root ────────────────────────────────────────────────────────────────
# Override at runtime: PRISM_DATA_ROOT=/path/to/data uvicorn ...
DATA_ROOT = os.environ.get("PRISM_DATA_ROOT", "../data")

# ── Field name ────────────────────────────────────────────────────────────────
# Used to match files in spectra, PDF, and NIRCam directories.
# Supports multiple fields via list, e.g. ["M0416", "M0417"]
FIELD_NAME = os.environ.get("PRISM_FIELD_NAME", "M0416")

# ── Catalogs ─────────────────────────────────────────────────────────────────
SPEC_CAT_FILE = "sapphires_edr_spec_cat.fits"
PHOT_CAT_FILE = "sapphires_edr_phot_cat.fits"

CATALOG_ID_COL = "ID"
CATALOG_RA_COL = "RA"
CATALOG_DEC_COL = "DEC"
SPEC_CAT_ZSPEC_COL = "z_spec"
PHOT_CAT_ZPHOT_COL = "z_phot"

# ── Spectra directories ───────────────────────────────────────────────────────
SPEC_1D_DIR = "sapphires_edr_1d_spec"
SPEC_2D_DIR = "sapphires_edr_2d_spec"
SPEC_2D_FILTERS = ["F356W", "F444W"]
SPEC_2D_ORIENTS = ["R", "C"]

# File naming patterns — {field} prefix for flexibility across fields
SPEC_2D_PATTERN = "spec_2d_{field}_{filter}_ID{id}_{orient}.fits"
SPEC_1D_PATTERN = "spec_1d_{field}_{filter}_ID{id}_{orient}.fits"

# ── NIRCam mosaics ────────────────────────────────────────────────────────────
NIRCAM_DIR = "sapphires_edr_nircam_sci"
# Band filenames: {field}_{band}_v{ver}_sci.fits, e.g. 4750_F115W_v05_sci.fits
NIRCAM_PATTERN = "{field}_{band}_v{ver}_sci.fits"

# ── PDF summary sheets ────────────────────────────────────────────────────────
PDF_DIR = "sapphires_edr_spec_pdf"
# Per filter × orientation, each containing 2D + 1D spectrum
PDF_PATTERN = "spec_2d_{field}_{filter}_ID{id}_{orient}.pdf"

# ── Cutout cache ──────────────────────────────────────────────────────────────
CUTOUT_CACHE_DIR = "cutout_cache"  # relative to DATA_ROOT; auto-created

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CUTOUT_SIZE_ARCSEC = 5.0
DEFAULT_CMAP = "viridis"
DEFAULT_SCALE = "zscale"

# ── RGB composite mapping ─────────────────────────────────────────────────────
RGB_BANDS = {"r": "F444W", "g": "F200W", "b": "F115W"}
RGB_SCALE = "asinh"

# ── Coord search ──────────────────────────────────────────────────────────────
COORD_SEARCH_MAX_RADIUS_ARCSEC = 60.0

# ── Persistence ───────────────────────────────────────────────────────────────
TAGS_DB_PATH = "tags_db.json"  # relative to prism/ repo root

# ── Tag vocabulary ────────────────────────────────────────────────────────────
TAG_VOCABULARY = [
    "emission",
    "continuum",
    "galaxy",
    "AGN",
    "high-vel",
    "to-be-classified",
    "star",
    "artefact",
    "blended",
]
