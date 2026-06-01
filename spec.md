# PRISM — Pipeline for Redshift Inspection & Source Management
## Specification v0.3

---

## 1. Overview

PRISM is a local-first web application for inspecting grism spectroscopic data from the SAPPHIRES EDR dataset. It provides a unified interface to browse sources, examine 1D/2D spectra across two grism filters (F356W + F444W) in two orientations (R + C), explore multi-band NIRCam imaging, manage redshifts, tag sources for classification, and view pre-rendered PDF summary sheets — all from a single browser window served from a local (or remote) Python server.

The UI uses a **rainbow colour theme** with full light and dark mode support. Each functional zone of the interface is assigned a hue from the visible spectrum (violet → red), giving every panel a distinct identity while remaining cohesive.

---

## 2. Tech Stack

| Layer        | Choice              | Rationale                                               |
|--------------|---------------------|---------------------------------------------------------|
| Backend      | Python / FastAPI    | Async, fast, native astropy/numpy ecosystem             |
| FITS I/O     | astropy + reproject | Catalog reading, cutout generation, WCS handling        |
| Image output | matplotlib / pillow | Render colormaps to PNG on the fly                      |
| Spectra plot | Plotly (frontend)   | Interactive pan/zoom/hover; redshift line overlays      |
| SED plot     | Plotly (frontend)   | Same library, consistent UX                             |
| Frontend     | React + Vite        | Fast dev, component-based, easy state management        |
| Styling      | Tailwind CSS        | Utility-first, dark-mode ready; extended with custom CSS variables for rainbow theme |
| HTTP client  | axios               | REST calls from frontend to backend                     |

---

## 3. Directory Layout

```
prism/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # All data paths and tuneable defaults  ← edit this
│   ├── routers/
│   │   ├── sources.py           # Source list, search, coords query
│   │   ├── spectra.py           # 1D/2D spectra endpoints
│   │   ├── images.py            # Cutout generation, RGB
│   │   ├── pdf.py               # Serve per-source PDF summary sheets
│   │   ├── tags.py              # Tag CRUD, bulk import from .txt
│   │   └── redshift.py          # z_spec read/write, z_phot read
│   └── utils/
│       ├── fits_io.py           # Catalog and image helpers
│       ├── cutout.py            # Cutout engine (astropy Cutout2D)
│       └── coord_search.py      # Sky-coord nearest-neighbour search
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── theme.css            # Rainbow CSS variables (light + dark)
│   │   ├── components/
│   │   │   ├── SourceList.jsx   # Left panel: list + search + tag filter
│   │   │   ├── SpectraPanel.jsx # 2D + 1D panels for F356W & F444W, R & C
│   │   │   ├── PDFViewer.jsx    # Embedded PDF summary sheet per source
│   │   │   ├── SEDPanel.jsx     # SED plot (photometry points)
│   │   │   ├── ImagePanel.jsx   # Multi-band cutouts + RGB
│   │   │   ├── TagEditor.jsx    # Tag chips, add/remove, bulk import
│   │   │   ├── RedshiftBar.jsx  # z_spec / z_phot display + manual edit
│   │   │   └── CoordSearch.jsx  # Contamination finder by sky coords
│   │   └── utils/
│   │       ├── api.js           # All axios calls, one place
│   │       └── specLines.js     # Rest-frame line wavelengths table
│   └── public/
├── tags_db.json                 # Persistent tag + z_spec store (flat file)
├── requirements.txt
├── run.sh                       # One-command launch (backend + frontend)
└── README.md
```

### 3.1 Data directory (external — configured in config.py)

The data directory lives **outside** the prism/ repo root. Its location differs between local and server deployments and is set via `DATA_ROOT` in `config.py` (or overridden by the `PRISM_DATA_ROOT` environment variable).

```
<DATA_ROOT>/                              # e.g. ../data  or  /mnt/sapphires
├── sapphires_edr_spec_cat.fits           # Spectroscopic catalog  (ID + z_spec + coords + …)
├── sapphires_edr_phot_cat.fits           # Photometric catalog    (ID + z_phot + photometry)
├── sapphires_edr_1d_spec/                # 1D spectra FITS files
│   └── spec_1d_{field}_{filter}_ID{id}_{orient}.fits
│                                         #   e.g. spec_1d_M0416_F356W_ID1028_R.fits
├── sapphires_edr_2d_spec/                # 2D spectra FITS files
│   └── spec_2d_{field}_{filter}_ID{id}_{orient}.fits
│                                         #   e.g. spec_2d_M0416_F356W_ID133_R.fits
├── sapphires_edr_nircam_sci/             # NIRCam mosaic FITS files
│   └── {field}_{band}_v{ver}_sci.fits    #   e.g. 4750_F115W_v05_sci.fits
├── sapphires_edr_spec_pdf/               # Pre-rendered PDF summary sheets
│   └── spec_2d_{field}_{filter}_ID{id}_{orient}.pdf
│                                         #   e.g. spec_2d_M0416_F356W_ID1028_R.pdf
│                                         #   one per filter × orientation; contains 2D + 1D
└── cutout_cache/                         # Auto-created; cutout PNGs written here
```

The `cutout_cache/` folder is created automatically by the backend on first run if absent.

**Field name**: The `{field}` token (e.g. `M0416`) is configurable via `FIELD_NAME` in `config.py`. The pipeline scans all files matching the configured field pattern, allowing support for multiple fields in future deployments.

---

## 4. Data Model

### 4.1 Catalogs

Two FITS catalogs are joined at startup on the shared `'ID'` column:

| Catalog                         | Key columns used                                      |
|---------------------------------|-------------------------------------------------------|
| `sapphires_edr_spec_cat.fits`   | `ID`, `RA`, `DEC`, `z_spec` (and any other spec cols) |
| `sapphires_edr_phot_cat.fits`   | `ID`, `z_phot`, flux/magnitude columns for SED        |

The merged table is loaded once into memory at startup and re-used for all source queries. Catalog column names are configurable in `config.py`.

### 4.2 1D and 2D spectra file naming convention

Files include a `{field}` prefix (e.g. `M0416`) and follow these patterns, configurable in `config.py`:

**1D spectra:**
```
spec_1d_{field}_{filter}_ID{id}_{orient}.fits
```

**2D spectra:**
```
spec_2d_{field}_{filter}_ID{id}_{orient}.fits
```

Where:
- `{field}` = field name (e.g. `M0416`), set via `FIELD_NAME` in config
- `{filter}` = `F356W` or `F444W`
- `{id}` = source ID number
- `{orient}` = `R` (Row) or `C` (Column)

Four 2D files may exist per source (filter × orientation), and up to four 1D files:

| File                                       | Type | Filter | Orientation |
|--------------------------------------------|------|--------|-------------|
| `spec_2d_M0416_F356W_ID133_R.fits`         | 2D   | F356W  | Row (R)     |
| `spec_2d_M0416_F356W_ID133_C.fits`         | 2D   | F356W  | Column (C)  |
| `spec_2d_M0416_F444W_ID133_R.fits`         | 2D   | F444W  | Row (R)     |
| `spec_2d_M0416_F444W_ID133_C.fits`         | 2D   | F444W  | Column (C)  |
| `spec_1d_M0416_F356W_ID133_R.fits`         | 1D   | F356W  | Row (R)     |
| `spec_1d_M0416_F444W_ID133_R.fits`         | 1D   | F444W  | Row (R)     |

The naming patterns are set via `SPEC_1D_PATTERN` and `SPEC_2D_PATTERN` in `config.py`. If a file is absent, the corresponding panel renders a "not available" placeholder.

### 4.3 PDF summary sheets

PDFs are generated **per filter × orientation** (not per source), matching the 2D spectrum naming:

```
spec_2d_{field}_{filter}_ID{id}_{orient}.pdf
```

Each PDF contains:
- The 2D spectrum image for that filter and orientation
- The corresponding 1D spectrum for that filter and orientation

This means up to 4 PDFs per source (F356W-R, F356W-C, F444W-R, F444W-C). The frontend displays the relevant PDF alongside its corresponding 2D+1D spectrum panel.

### 4.4 Source record (assembled at runtime)

```json
{
  "id":          "12345",
  "ra":          150.123456,
  "dec":         2.345678,
  "z_phot":      1.23,
  "z_spec":      1.19,
  "tags":        ["galaxy", "emission"],
  "has_1d":      { "F356W_R": true, "F356W_C": false, "F444W_R": true, "F444W_C": false },
  "has_2d":      { "F356W_R": true, "F356W_C": true, "F444W_R": true, "F444W_C": false },
  "has_pdf":     { "F356W_R": true, "F356W_C": false, "F444W_R": true, "F444W_C": false },
  "has_sed":     true,
  "has_rgb":     true
}
```

`has_*` flags are computed at startup by scanning the data directories. Missing panels show a placeholder, never an error crash.

### 4.5 tags_db.json schema

```json
{
  "sources": {
    "12345": {
      "tags":   ["galaxy", "emission"],
      "z_spec": 1.19,
      "notes":  ""
    }
  }
}
```

Written on every tag/z_spec change. A `.bak` copy is written before each save. `z_spec` stored here overrides the catalog value (allows manual correction without modifying the original FITS file).

---

## 5. Backend API

All endpoints return JSON unless noted. Images return `image/png`. PDFs return `application/pdf`.

### 5.1 Sources

| Method | Path                        | Description                                        |
|--------|-----------------------------|----------------------------------------------------|
| GET    | `/sources`                  | Full source list with flags, z values, tags        |
| GET    | `/sources/{id}`             | Single source record                               |
| GET    | `/sources/search?q=&tag=`   | Filter by ID substring and/or tag (client can also filter locally) |
| GET    | `/sources/near?ra=&dec=&r=` | Sources within radius `r` arcsec of coords         |

### 5.2 Spectra

| Method | Path                                                    | Description                                          |
|--------|---------------------------------------------------------|------------------------------------------------------|
| GET    | `/spectra/{id}/1d/{filter}/{orient}`                    | 1D spectrum as JSON `{wave, flux, err}`              |
| GET    | `/spectra/{id}/2d/{filter}/{orient}`                    | 2D spectrum as PNG; filter ∈ {F356W,F444W}, orient ∈ {R,C} |

The 2D endpoint reads the FITS file `spec_2d_{field}_{filter}_ID{id}_{orient}.fits`, applies the requested `cmap` and `scale` query params, and returns a PNG. The 1D endpoint reads `spec_1d_{field}_{filter}_ID{id}_{orient}.fits` and returns arrays; the frontend renders interactively with Plotly.

### 5.3 Images

| Method | Path                                        | Description                                          |
|--------|---------------------------------------------|------------------------------------------------------|
| GET    | `/images/{id}/cutout/{band}?size=&cmap=&scale=` | Cutout PNG for one NIRCam band; `size` in arcsec |
| GET    | `/images/{id}/rgb?size=`                    | RGB composite PNG                                    |
| GET    | `/images/bands`                             | List of available bands (scanned from mosaics dir)   |

Cutouts are cached to `<DATA_ROOT>/cutout_cache/` keyed by `{id}_{band}_{size}_{cmap}_{scale}.png`. The NIRCam band filenames follow the pattern `{field}_{band}_v{ver}_sci.fits`; the backend extracts available bands by parsing filenames.

### 5.4 PDF

| Method | Path                                | Description                                      |
|--------|-------------------------------------|--------------------------------------------------|
| GET    | `/pdf/{id}/{filter}/{orient}`       | Stream the PDF for a specific filter × orientation |

PDFs are served directly from `sapphires_edr_spec_pdf/spec_2d_{field}_{filter}_ID{id}_{orient}.pdf`. Each PDF contains the 2D spectrum image and the corresponding 1D spectrum for that filter and orientation. The frontend embeds the relevant PDF via `<iframe>` or `<object>` alongside the matching spectrum panel.

### 5.5 Tags

| Method | Path                | Description                                          |
|--------|---------------------|------------------------------------------------------|
| GET    | `/tags/list`        | Vocabulary of all defined tags                       |
| POST   | `/tags/{id}/add`    | `{ "tag": "emission" }`                              |
| DELETE | `/tags/{id}/remove` | `{ "tag": "emission" }`                              |
| POST   | `/tags/bulk`        | Bulk import from .txt file; see §5.5.1               |

#### 5.5.1 Bulk tag import

`POST /tags/bulk` accepts `multipart/form-data`:
- `file` — the .txt (or .csv) file
- `id_column` — column name or 0-based index for source IDs
- `tag` — tag string to apply to all matched sources

Returns `{ "matched": N, "not_found": ["id1", "id2", …] }`.

### 5.6 Redshift

| Method | Path             | Description                           |
|--------|------------------|---------------------------------------|
| PATCH  | `/redshift/{id}` | `{ "z_spec": 1.23 }` — update z_spec  |

---

## 6. Frontend Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🌈 PRISM                                        [Coord Search]  [☀/🌙]  [⚙] │
├───────────────┬──────────────────────────────────────────────────────────────┤
│               │  ╔══ F356W ═══════════════╦══ F444W ═══════════════╗         │
│  SOURCE LIST  │  ║  2D-R  │  2D-C         ║  2D-R  │  2D-C         ║         │
│               │  ╚════════════════════════╩════════════════════════╝         │
│  [search…]    │  ┌─────────────────────────────────────────────────┐         │
│  [tag filter] │  │  1D spectrum (Plotly)  z_spec lines │ z_phot    │         │
│               │  └─────────────────────────────────────────────────┘         │
│  ○ 12345  1.2 │  ┌──────────────────┬──────────────────────────────┐         │
│  ○ 67890  0.8 │  │  SED             │  NIRCam cutouts  [RGB]        │         │
│  ○ 11111  2.1 │  │  (Plotly)        │  [band chips] [size″] [cmap] │         │
│  ...          │  └──────────────────┴──────────────────────────────┘         │
│               │  ┌─────────────────────────────────────────────────┐         │
│               │  │  PDF summary sheet  (embedded <iframe>)         │         │
│               │  └─────────────────────────────────────────────────┘         │
│               │  ┌─────────────────────────────────────────────────┐         │
│               │  │ Tags: [galaxy×] [emission×]  [+ add] [import]   │         │
│               │  │ z_spec: 1.19 ✏   z_phot: 1.23  Δz: ok          │         │
│               │  └─────────────────────────────────────────────────┘         │
└───────────────┴──────────────────────────────────────────────────────────────┘
```

### 6.1 Rainbow theme

Each panel is assigned a hue from the visible spectrum. The theme is implemented as CSS custom properties in `theme.css` with separate light and dark mode values under `[data-theme="light"]` and `[data-theme="dark"]`:

| Panel              | Hue        | Light mode accent   | Dark mode accent    |
|--------------------|------------|---------------------|---------------------|
| Source list        | Violet     | `#7c3aed` / bg `#f5f3ff` | `#a78bfa` / bg `#1e1b2e` |
| 2D spectra (F356W) | Blue       | `#2563eb` / bg `#eff6ff` | `#60a5fa` / bg `#1e2a3e` |
| 2D spectra (F444W) | Cyan       | `#0891b2` / bg `#ecfeff` | `#22d3ee` / bg `#0e2a2e` |
| 1D spectrum        | Green      | `#16a34a` / bg `#f0fdf4` | `#4ade80` / bg `#0f2a1a` |
| SED                | Yellow     | `#ca8a04` / bg `#fefce8` | `#facc15` / bg `#2a2600` |
| Image cutouts      | Orange     | `#ea580c` / bg `#fff7ed` | `#fb923c` / bg `#2a1800` |
| PDF viewer         | Red        | `#dc2626` / bg `#fef2f2` | `#f87171` / bg `#2a0f0f` |
| Tags / z bar       | Pink       | `#db2777` / bg `#fdf2f8` | `#f472b6` / bg `#2a1020` |

Panel borders, header text, active tab indicators, and chip colours all use their panel's accent colour. Backgrounds use the soft tinted surface colour. The global page background is neutral (white / near-black) so the rainbow panels pop.

A light/dark mode toggle in the top bar writes `data-theme` to `<html>` and persists the choice to `localStorage`.

### 6.2 Source list (left panel — violet)

- Displays `ID`, `z_spec` (or `z_phot` if no spec), miniature tag chips
- Availability dot row: one dot per data type (1D · 2D · PDF · SED · RGB), coloured if present, grey if absent
- Search box: real-time client-side filter on ID string
- Tag filter: multi-select chip picker; shows only sources possessing ALL selected tags
- Click → loads all right-hand panels for that source
- Keyboard: ↑ / ↓ to move, Enter to select

### 6.3 Spectra panel (blue + cyan + green)

**2D sub-panel (blue = F356W, cyan = F444W)**
- Two column groups side by side, each containing R and C orientation tabs
- Selecting a tab shows the 2D image + the corresponding 1D spectrum + the PDF for that filter × orientation
- Images served as PNG from backend (FITS → zscale → cmap → PNG)
- Optional "interactive" toggle: requests the raw FITS data and renders as a Plotly heatmap (enables contrast/stretch adjustments in browser)
- Stretch controls per image: cmap dropdown + scale dropdown (zscale / linear / log / sqrt)
- Missing files → grey placeholder with text "F356W_C not available"

**1D sub-panel (green, shown within each filter × orientation tab)**
- Plotly line chart: wavelength (µm) on x-axis, flux on y-axis, ±1σ shading
- Spectral line overlay at z_spec: solid vertical dashed lines, labelled (Lyα, CIV, CIII], MgII, [OII], Hβ, [OIII] 4959+5007, Hα)
- z_phot lines: same lines at lighter opacity and dotted style
- Hover tooltip: wavelength + flux value + nearest line name if within 50Å
- When z_spec is edited (§6.8), lines update in real time without re-fetching data

### 6.4 SED panel (yellow)

- Plotly scatter + connecting line: filter pivot wavelength (µm) vs flux density (µJy) or AB magnitude; toggle between units
- Error bars when available in phot_cat
- Upper limits: downward-pointing triangle markers
- Band name labels on hover
- Greyed-out if no photometric data found for source

### 6.5 Image panel (orange)

- Band chip selector: one chip per NIRCam mosaic found in `sapphires_edr_nircam_sci/`; toggling a chip shows/hides that cutout
- Cutout size: numeric input (arcsec), default 5″; applies globally to all bands
- Colormap dropdown: viridis (default), gray, inferno, hot, plasma, magma, RdBu
- Scale dropdown: zscale (default), linear, log, sqrt
- Cutouts displayed in a scrollable horizontal row; band label below each
- RGB composite shown as a dedicated cell labelled "RGB"; bands mapping defined in config
- "Refresh cutouts" button: forces cache invalidation for this source

### 6.6 PDF viewer (red)

- Embedded `<iframe src="/api/pdf/{id}/{filter}/{orient}">` showing the PDF for the currently selected filter × orientation
- Each PDF contains the 2D spectrum image and the corresponding 1D spectrum for that filter and orientation
- "Open in new tab" link for full-screen viewing
- Collapsed by default with a toggle to expand (saves vertical space)
- Grey placeholder if no PDF found for the selected filter × orientation

### 6.7 Tag editor (pink)

- Tag chips: colour-coded removable chips for current tags
- Predefined vocabulary: `emission` · `continuum` · `galaxy` · `AGN` · `high-vel` · `to-be-classified` · `star` · `artefact` · `blended`
- "+ add" button → popover with vocabulary list + free-text custom tag input
- "Import from file" button → modal:
  1. Upload .txt / .csv file
  2. Preview first 5 rows as a table
  3. Select ID column (dropdown)
  4. Enter tag to apply
  5. Confirm → backend applies, returns match summary

### 6.8 Redshift bar (pink, alongside tags)

- `z_spec: 1.19  ✏` — click pencil → inline numeric input, confirm with Enter or ✓
- `z_phot: 1.23` — read-only
- Δz indicator: green "✓ consistent" if |Δz|/(1+z_spec) < 0.1, amber "⚠ discrepant" otherwise, grey "no z_spec" if unset
- Saving z_spec: PATCH `/redshift/{id}`, updates tags_db.json, immediately re-renders 1D line overlays

### 6.9 Coord search / contamination tool (top bar)

- Input: RA + Dec (decimal degrees or hh:mm:ss / dd:mm:ss), radius in arcsec
- Returns a table of nearby sources sorted by separation, with columns: ID, separation″, z_spec, z_phot, tags
- Click any row → navigate to that source
- Designed to identify sources whose spectra might contaminate the selected target

---

## 7. Config (backend/config.py)

```python
import os

# ── Data root ────────────────────────────────────────────────────────────────
# Override at runtime: PRISM_DATA_ROOT=/path/to/data uvicorn ...
DATA_ROOT = os.environ.get("PRISM_DATA_ROOT", "../data")

# ── Field name ────────────────────────────────────────────────────────────────
# Used to match files in spectra, PDF, and NIRCam directories.
# Supports multiple fields via list, e.g. ["M0416", "M0417"]
FIELD_NAME = os.environ.get("PRISM_FIELD_NAME", "M0416")

# ── Catalogs ─────────────────────────────────────────────────────────────────
SPEC_CAT_FILE  = "sapphires_edr_spec_cat.fits"
PHOT_CAT_FILE  = "sapphires_edr_phot_cat.fits"

CATALOG_ID_COL  = "ID"
CATALOG_RA_COL  = "RA"
CATALOG_DEC_COL = "DEC"
SPEC_CAT_ZSPEC_COL  = "z_spec"   # column in spec_cat; None if absent
PHOT_CAT_ZPHOT_COL  = "z_phot"   # column in phot_cat; None if absent

# ── Spectra directories ───────────────────────────────────────────────────────
SPEC_1D_DIR  = "sapphires_edr_1d_spec"
SPEC_2D_DIR  = "sapphires_edr_2d_spec"
SPEC_2D_FILTERS  = ["F356W", "F444W"]
SPEC_2D_ORIENTS  = ["R", "C"]

# File naming patterns — {field} prefix for flexibility across fields
SPEC_2D_PATTERN  = "spec_2d_{field}_{filter}_ID{id}_{orient}.fits"
SPEC_1D_PATTERN  = "spec_1d_{field}_{filter}_ID{id}_{orient}.fits"

# ── NIRCam mosaics ────────────────────────────────────────────────────────────
NIRCAM_DIR   = "sapphires_edr_nircam_sci"
# Band filenames: {field}_{band}_v{ver}_sci.fits, e.g. 4750_F115W_v05_sci.fits
# Backend extracts band name by parsing the filename

# ── PDF summary sheets ────────────────────────────────────────────────────────
PDF_DIR      = "sapphires_edr_spec_pdf"
# Per filter × orientation, each containing 2D + 1D spectrum
PDF_PATTERN  = "spec_2d_{field}_{filter}_ID{id}_{orient}.pdf"

# ── Cutout cache ──────────────────────────────────────────────────────────────
CUTOUT_CACHE_DIR = "cutout_cache"   # relative to DATA_ROOT; auto-created

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_CUTOUT_SIZE_ARCSEC = 5.0
DEFAULT_CMAP   = "viridis"
DEFAULT_SCALE  = "zscale"

# ── RGB composite mapping ─────────────────────────────────────────────────────
RGB_BANDS  = {"r": "F444W", "g": "F200W", "b": "F115W"}
RGB_SCALE  = "asinh"

# ── Coord search ──────────────────────────────────────────────────────────────
COORD_SEARCH_MAX_RADIUS_ARCSEC = 60.0

# ── Persistence ───────────────────────────────────────────────────────────────
TAGS_DB_PATH = "tags_db.json"   # relative to prism/ repo root
```

Switching between local and server deployments only requires changing `DATA_ROOT` (or setting the `PRISM_DATA_ROOT` env variable). Nothing else changes.

---

## 8. Persistence

- `tags_db.json` lives in the prism/ repo root (not in the data directory, so it can be committed separately).
- Written immediately on every tag add/remove and z_spec edit.
- A `.bak` copy is written before each save.
- On startup: spec_cat z_spec is loaded as the default; any z_spec stored in tags_db.json **overrides** the catalog value, allowing manual corrections without modifying original FITS files.
- The catalog `z_phot` is always read-only (from phot_cat).

---

## 9. Deployment

### Local

```bash
# 1. Set data path (if not ../data relative to prism/)
export PRISM_DATA_ROOT=/path/to/your/data

# 2. Backend
cd prism
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173  (Vite proxies /api/* → localhost:8000)
```

### Server

```bash
# Build frontend static files
cd frontend && npm run build

# Serve everything from FastAPI (static + API)
export PRISM_DATA_ROOT=/mnt/sapphires/data
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

- FastAPI serves the built `frontend/dist/` as static files at `/`
- CORS restricted to server hostname in `main.py`
- Optional: `PRISM_PASSWORD` env var enables HTTP Basic Auth middleware
- Optional: swap `tags_db.json` for SQLite if multiple users write simultaneously

10. Future extensions (out of scope for v2)

Spectral line fitting (Gaussian) with interactive line selection
Redshift fitting / cross-correlation against template spectra
Export: selected sources → DS9 region file, CSV, or ECSV
Side-by-side source comparison (split view)
Annotation notes per source (free-text field in tags_db.json — already reserved)
WebSocket push for long-running cutout generation
Authentication / multi-user support