"""
PRISM Panel Application - Server-optimized version using Panel.
Pure Python, no Node.js/npm build required.
"""
import os
import sys
import json
import shutil
import io
import numpy as np
import param
import panel as pn
import plotly.graph_objects as go
from astropy.nddata import Cutout2D
from astropy import units as u
from astropy.wcs import WCS
from astropy.io import fits
from astropy.coordinates import SkyCoord
from PIL import Image
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from astropy.visualization import ZScaleInterval, AsinhStretch, ImageNormalize

# ── Import backend utilities ─────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import config
from backend.utils.fits_io import load_spec_cat, load_phot_cat, merge_catalogs
from backend.utils.spectrum_render import get_1d_path, get_2d_path, render_2d_png, read_1d_spectrum
from backend.utils.cutout import generate_cutout, get_nircam_band_path
from backend.utils.coord_search import find_nearby_sources

pn.extension('plotly', template='fast', sizing_mode='stretch_width')

# ── Global state ─────────────────────────────────────────────────────────────
_merged_catalog = None
_source_flags = None
_tags_db = None

LAMBDA_REF_DICT = {
    'F070W': 7039.12, 'F090W': 9021.53, 'F115W': 11542.61,
    'F140M': 14053.23, 'F150W': 15007.44, 'F162M': 16272.47,
    'F182M': 18451.67, 'F200W': 19886.48, 'F210M': 20954.51,
    'F250M': 25032.33, 'F277W': 27617.40, 'F300M': 29891.21,
    'F356W': 35683.62, 'F360M': 36241.76, 'F410M': 40822.38,
    'F444W': 44043.15, 'F335M': 33537.23,
}

FILTERS = ['F356W', 'F444W']
ORIENTS = ['R', 'C']
COMBOS = [(f, o) for f in FILTERS for o in ORIENTS]

TAG_VOCABULARY = config.TAG_VOCABULARY


def _safe_float(val):
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


def init_state():
    global _merged_catalog, _source_flags, _tags_db
    spec_cat = load_spec_cat()
    phot_cat = load_phot_cat()
    _merged_catalog = merge_catalogs(spec_cat, phot_cat)
    _source_flags = _scan_source_flags()
    _tags_db = _load_tags_db()


def get_merged_catalog():
    return _merged_catalog


def _scan_source_flags():
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
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            result[key] = get_1d_path(source_id, f, o) is not None
    return result


def _scan_2d_flags(source_id):
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            result[key] = get_2d_path(source_id, f, o) is not None
    return result


def _scan_pdf_flags(source_id):
    result = {}
    for f in config.SPEC_2D_FILTERS:
        for o in config.SPEC_2D_ORIENTS:
            key = f"{f}_{o}"
            pdf_filename = config.PDF_PATTERN.format(
                field=config.FIELD_NAME, filter=f, id=source_id, orient=o)
            pdf_path = os.path.join(config.DATA_ROOT, config.PDF_DIR, pdf_filename)
            result[key] = os.path.exists(pdf_path)
    return result


# ── Image rendering helpers ──────────────────────────────────────────────────
def _apply_scale(data, scale_method):
    if data is None:
        return None
    data = np.array(data, dtype=np.float64)
    if data.size == 0:
        return None
    if scale_method == "zscale":
        interval = ZScaleInterval()
        try:
            vmin, vmax = interval.get_limits(data)
        except Exception:
            return None
    elif scale_method == "asinh":
        interval = ZScaleInterval()
        try:
            vmin, vmax = interval.get_limits(data)
        except Exception:
            return None
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())
        data = norm(data)
        return np.clip(np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=0.0), 0, 1)
    else:
        vmin, vmax = np.nanpercentile(data, [1, 99])
    data = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
    return data


def _apply_cmap(data, cmap_name):
    cmap = cm.get_cmap(cmap_name)
    rgba = cmap(data)
    rgba = (rgba[:, :, :3] * 255).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGB")


def _render_cutout_png(ra, dec, band, size_arcsec=5.0, cmap='viridis', scale='zscale'):
    band_path = get_nircam_band_path(band)
    if band_path is None:
        return None
    cutout = generate_cutout(band_path, ra, dec, size_arcsec)
    if cutout is None or cutout.data is None:
        return None
    scaled = _apply_scale(cutout.data, scale)
    if scaled is None:
        return None
    img = _apply_cmap(scaled, cmap)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _render_rgb_png(ra, dec, size_arcsec=5.0):
    channels = {}
    ref_shape = None
    for ch, band in config.RGB_BANDS.items():
        band_path = get_nircam_band_path(band)
        if band_path is None:
            continue
        cutout = generate_cutout(band_path, ra, dec, size_arcsec)
        if cutout is None or cutout.data is None:
            continue
        scaled = _apply_scale(cutout.data, config.RGB_SCALE)
        if scaled is None:
            continue
        if ref_shape is None:
            ref_shape = scaled.shape
        elif scaled.shape != ref_shape:
            continue
        channels[ch] = scaled
    if len(channels) < 3:
        return None
    h, w = channels["r"].shape[:2]
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[:, :, 0] = (channels["r"] * 255).astype(np.uint8)
    rgb[:, :, 1] = (channels["g"] * 255).astype(np.uint8)
    rgb[:, :, 2] = (channels["b"] * 255).astype(np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def _load_tags_db():
    db_path = config.TAGS_DB_PATH
    if os.path.exists(db_path):
        try:
            with open(db_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"sources": {}}


def save_tags_db(db):
    global _tags_db
    _tags_db = db
    db_path = config.TAGS_DB_PATH
    bak_path = db_path + ".bak"
    if os.path.exists(db_path):
        shutil.copy2(db_path, bak_path)
    with open(db_path, "w") as f:
        json.dump(db, f, indent=2)


def build_source_record(row):
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
    for col in row.colnames:
        if col.endswith("_KRON") or col.endswith("_KRON_e"):
            val = _safe_float(row[col])
            if val is not None:
                phot_bands[col] = val

    sid = str(row[id_col])
    source_data = _tags_db.get("sources", {}).get(sid, {})
    tags = source_data.get("tags", [])
    z_spec_stored = source_data.get("z_spec", None)
    if z_spec_stored is not None:
        z_spec = z_spec_stored

    has_spec_z = z_spec is not None
    flags = _source_flags.get(sid, {})

    return {
        "id": sid, "ra": ra, "dec": dec, "z_phot": z_phot,
        "z_spec": z_spec, "tags": tags,
        "has_1d": flags.get("has_1d", {}),
        "has_2d": flags.get("has_2d", {}),
        "has_pdf": flags.get("has_pdf", {}),
        "has_sed": flags.get("has_sed", False),
        "has_rgb": flags.get("has_rgb", False),
        "has_spec_z": has_spec_z,
        "phot_bands": phot_bands,
    }


# ── Application State ────────────────────────────────────────────────────────
class AppState(param.Parameterized):
    selected_id = param.String(default=None)
    active_filter = param.String(default='F356W')
    active_orient = param.String(default='R')
    show_only_spec_z = param.Boolean(default=True)
    coord_ra = param.Number(default=None)
    coord_dec = param.Number(default=None)
    coord_radius = param.Number(default=10.0)
    coord_results = param.List(default=[])
    search_error = param.String(default='')
    source_list = param.List(default=[])
    filtered_sources = param.List(default=[])


app_state = AppState()


def get_all_sources():
    catalog = get_merged_catalog()
    if catalog is None:
        return []
    id_col = config.CATALOG_ID_COL
    records = []
    for row in catalog:
        rec = build_source_record(row)
        records.append(rec)
    return records


def get_sources_with_spec_z():
    catalog = get_merged_catalog()
    if catalog is None:
        return []
    id_col = config.CATALOG_ID_COL
    records = []
    for row in catalog:
        rec = build_source_record(row)
        if rec["has_spec_z"]:
            records.append(rec)
    return records


def update_source_list(*events):
    """Update source list based on filter and coord search results."""
    if app_state.show_only_spec_z:
        base = get_sources_with_spec_z()
    else:
        base = get_all_sources()

    if app_state.coord_results:
        sep_map = {r['id']: r['separation_arcsec'] for r in app_state.coord_results}
        id_set = set(r['id'] for r in app_state.coord_results)
        filtered = [s for s in base if s['id'] in id_set]
        filtered.sort(key=lambda s: sep_map.get(s['id'], float('inf')))
        app_state.filtered_sources = filtered
    else:
        app_state.filtered_sources = base


app_state.param.watch(update_source_list, ['show_only_spec_z', 'coord_results'])


# ── UI Components ────────────────────────────────────────────────────────────

def create_source_list_widget():
    """Create the source list with filtering and keyboard navigation."""
    source_selector = pn.widgets.Select(
        name='Sources',
        options=[],
        size=20,
        width=280,
    )

    def format_source_label(src):
        z_info = f"z={src['z_spec']:.3f}" if src.get('z_spec') is not None else f"zp={src['z_phot']:.3f}" if src.get('z_phot') is not None else ""
        return f"ID={src['id']} {z_info}"

    def update_selector():
        sources = app_state.filtered_sources
        options = {format_source_label(s): s['id'] for s in sources}
        source_selector.options = options
        if app_state.selected_id and app_state.selected_id in options.values():
            source_selector.value = app_state.selected_id

    def on_source_select(event):
        app_state.selected_id = event.new

    source_selector.param.watch(on_source_select, 'value')

    # Keyboard navigation
    def on_key_press(event):
        if event.key == 'ArrowDown':
            idx = list(source_selector.options.values()).index(source_selector.value) if source_selector.value else -1
            if idx < len(source_selector.options) - 1:
                source_selector.value = list(source_selector.options.values())[idx + 1]
        elif event.key == 'ArrowUp':
            idx = list(source_selector.options.values()).index(source_selector.value) if source_selector.value else 0
            if idx > 0:
                source_selector.value = list(source_selector.options.values())[idx - 1]

    # Bind to update
    update_selector()

    return source_selector, update_selector


def create_coord_search_widget(update_selector_cb):
    """Create coordinate search inputs."""
    ra_input = pn.widgets.FloatInput(name='RA (deg)', value=None, width=120)
    dec_input = pn.widgets.FloatInput(name='DEC (deg)', value=None, width=120)
    radius_input = pn.widgets.FloatInput(name='Radius (arcsec)', value=10.0, width=120)
    search_btn = pn.widgets.Button(name='Search', button_type='primary', width=80)
    clear_btn = pn.widgets.Button(name='Clear', button_type='warning', width=80)
    error_msg = pn.pane.Markdown('', css_classes=['error-msg'])

    def do_search(event):
        if ra_input.value is None or dec_input.value is None:
            error_msg.object = '⚠ Please enter both RA and DEC'
            return
        try:
            catalog = get_merged_catalog()
            nearby = find_nearby_sources(ra_input.value, dec_input.value, radius_input.value, catalog)
            app_state.coord_results = nearby
            app_state.search_error = ''
            error_msg.object = f'Found {len(nearby)} sources'
            update_selector_cb()
        except Exception as e:
            app_state.search_error = str(e)
            error_msg.object = f'Error: {str(e)}'

    def do_clear(event):
        ra_input.value = None
        dec_input.value = None
        radius_input.value = 10.0
        app_state.coord_results = []
        app_state.search_error = ''
        error_msg.object = ''
        update_selector_cb()

    search_btn.on_click(do_search)
    clear_btn.on_click(do_clear)

    return pn.Column(
        pn.Row(ra_input, dec_input, radius_input, search_btn, clear_btn),
        error_msg
    )


def create_spectra_2d_panel():
    """2D spectrum display."""
    img_pane = pn.pane.PNG('', width=800, height=200)
    status = pn.pane.Markdown('')

    def update_2d(event=None):
        if not app_state.selected_id:
            img_pane.object = ''
            status.object = 'Select a source'
            return
        key = f"{app_state.active_filter}_{app_state.active_orient}"
        flags = _source_flags.get(app_state.selected_id, {}).get('has_2d', {})
        if flags.get(key):
            png_bytes = render_2d_png(app_state.selected_id, app_state.active_filter, app_state.active_orient)
            if png_bytes:
                img_pane.object = io.BytesIO(png_bytes)
                status.object = ''
            else:
                status.object = 'Failed to render'
        else:
            img_pane.object = ''
            status.object = 'No 2D spectrum available'

    app_state.param.watch(update_2d, ['selected_id', 'active_filter', 'active_orient'])
    return pn.Column(img_pane, status)


def create_spectra_1d_panel():
    """1D spectrum display using Plotly."""
    plot_pane = pn.pane.Plotly()
    status = pn.pane.Markdown('')

    def update_1d(event=None):
        if not app_state.selected_id:
            plot_pane.object = None
            status.object = 'Select a source'
            return
        key = f"{app_state.active_filter}_{app_state.active_orient}"
        flags = _source_flags.get(app_state.selected_id, {}).get('has_1d', {})
        if flags.get(key):
            data = read_1d_spectrum(app_state.selected_id, app_state.active_filter, app_state.active_orient)
            if data:
                wave = data.get('wave', [])
                flux = data.get('flux', [])
                err = data.get('err', [])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=wave, y=flux, mode='lines',
                    line=dict(color='#facc15', width=1),
                    name='Flux'
                ))
                if err:
                    fig.add_trace(go.Scatter(
                        x=wave + wave[::-1],
                        y=[f + e for f, e in zip(flux, err)] + [f - e for f, e in zip(flux[::-1], err[::-1])],
                        fill='toself', fillcolor='rgba(250,204,21,0.2)',
                        line=dict(width=0), showlegend=False, name='Error'
                    ))
                fig.update_layout(
                    margin=dict(t=10, r=10, b=40, l=55),
                    height=250,
                    xaxis=dict(title='Wavelength (µm)', gridcolor='#374151'),
                    yaxis=dict(title='Flux', gridcolor='#374151'),
                    paper_bgcolor='transparent',
                    plot_bgcolor='transparent',
                    font=dict(color='#d1d5db'),
                )
                plot_pane.object = fig
                status.object = ''
            else:
                status.object = 'Failed to load'
        else:
            plot_pane.object = None
            status.object = 'No 1D spectrum available'

    app_state.param.watch(update_1d, ['selected_id', 'active_filter', 'active_orient'])
    return pn.Column(plot_pane, status)


def create_sed_panel():
    """SED display using Plotly."""
    plot_pane = pn.pane.Plotly()
    status = pn.pane.Markdown('')
    unit_toggle = pn.widgets.ToggleGroup(
        name='Unit', options=['AB mag', 'µJy'], behavior='radio', value='AB mag'
    )

    def update_sed(event=None):
        if not app_state.selected_id:
            plot_pane.object = None
            status.object = 'Select a source'
            return

        # Find source in catalog
        catalog = get_merged_catalog()
        id_col = config.CATALOG_ID_COL
        source_row = None
        for row in catalog:
            if str(row[id_col]) == app_state.selected_id:
                source_row = row
                break

        if source_row is None:
            status.object = 'Source not found'
            return

        rec = build_source_record(source_row)
        phot_bands = rec.get('phot_bands', {})

        bands = []
        waves = []
        mags = []
        mag_errs = []
        fluxes = []
        flux_errs = []

        for key, val in phot_bands.items():
            if key.endswith('_MAG') and not key.endswith('_MAG_e'):
                band_name = key.replace('_MAG', '')
                err_key = key + '_e'
                wave = LAMBDA_REF_DICT.get(band_name)
                if wave and val is not None:
                    bands.append(band_name)
                    waves.append(wave / 10000)
                    mags.append(val)
                    mag_errs.append(phot_bands.get(err_key, 0))

                    kron_key = band_name + '_KRON'
                    kron_val = phot_bands.get(kron_key)
                    kron_err_key = kron_key + '_e'
                    if kron_val is not None:
                        fluxes.append(kron_val)
                        flux_errs.append(phot_bands.get(kron_err_key, 0))
                    else:
                        f = 3631 * 10 ** (-0.4 * val)
                        fluxes.append(f)
                        flux_errs.append(f * 0.4 * np.log(10) * (phot_bands.get(err_key, 0)) / 2.5)

        if not bands:
            plot_pane.object = None
            status.object = 'No photometric data'
            return

        sorted_idx = sorted(range(len(waves)), key=lambda i: waves[i])
        sorted_waves = [waves[i] for i in sorted_idx]
        sorted_mags = [mags[i] for i in sorted_idx]
        sorted_errs = [mag_errs[i] for i in sorted_idx]
        sorted_bands = [bands[i] for i in sorted_idx]
        sorted_fluxes = [fluxes[i] for i in sorted_idx]
        sorted_flux_errs = [flux_errs[i] for i in sorted_idx]

        unit = unit_toggle.value
        y_data = sorted_fluxes if unit == 'µJy' else sorted_mags
        y_err = sorted_flux_errs if unit == 'µJy' else sorted_errs

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sorted_waves, y=y_data, mode='lines+markers+text',
            line=dict(color='#facc15', width=2),
            marker=dict(size=8),
            text=sorted_bands, textposition='top center',
            textfont=dict(size=10, color='#facc15'),
            error_y=dict(type='data', array=y_err, visible=True),
            hovertemplate='%{text}<br>λ=%{x:.2f} µm<br>%{y:.2f}<extra></extra>',
        ))
        fig.update_layout(
            margin=dict(t=10, r=10, b=40, l=55),
            height=250,
            xaxis=dict(title='Wavelength (µm)', gridcolor='#374151'),
            yaxis=dict(
                title='Flux (µJy)' if unit == 'µJy' else 'AB Magnitude',
                gridcolor='#374151',
                autorange='reversed' if unit == 'AB mag' else True,
            ),
            paper_bgcolor='transparent',
            plot_bgcolor='transparent',
            font=dict(color='#d1d5db'),
        )
        plot_pane.object = fig
        status.object = ''

    unit_toggle.param.watch(update_sed, 'value')
    app_state.param.watch(update_sed, ['selected_id'])
    return pn.Column(pn.Row(pn.pane.Markdown('**SED**'), unit_toggle), plot_pane, status)


def create_image_panel():
    """NIRCam cutout and RGB display."""
    cutout_pane = pn.pane.PNG('', width=300, height=300)
    rgb_pane = pn.pane.PNG('', width=300, height=300)
    status = pn.pane.Markdown('')

    def update_images(event=None):
        if not app_state.selected_id:
            cutout_pane.object = ''
            rgb_pane.object = ''
            status.object = 'Select a source'
            return

        catalog = get_merged_catalog()
        id_col = config.CATALOG_ID_COL
        source_row = None
        for row in catalog:
            if str(row[id_col]) == app_state.selected_id:
                source_row = row
                break

        if source_row is None:
            status.object = 'Source not found'
            return

        ra = None
        dec = None
        for c in [config.CATALOG_RA_COL, "RA_1", "RA"]:
            if c and c in source_row.colnames:
                ra = _safe_float(source_row[c])
                if ra is not None:
                    break
        for c in [config.CATALOG_DEC_COL, "DEC_1", "DEC"]:
            if c and c in source_row.colnames:
                dec = _safe_float(source_row[c])
                if dec is not None:
                    break

        if ra is not None and dec is not None:
            cutout_png = _render_cutout_png(ra, dec, 'F444W', size_arcsec=5.0)
            if cutout_png:
                cutout_pane.object = io.BytesIO(cutout_png)
            else:
                cutout_pane.object = ''

            rgb_png = _render_rgb_png(ra, dec, size_arcsec=5.0)
            if rgb_png:
                rgb_pane.object = io.BytesIO(rgb_png)
            else:
                rgb_pane.object = ''
        else:
            status.object = 'No coordinates available'

    app_state.param.watch(update_images, ['selected_id'])
    return pn.Column(
        pn.pane.Markdown('**NIRCam Images**'),
        pn.Row(cutout_pane, rgb_pane),
        status
    )


def create_pdf_viewer():
    """PDF viewer."""
    pdf_pane = pn.pane.PDF('', width=800, height=400)
    status = pn.pane.Markdown('')

    def update_pdf(event=None):
        if not app_state.selected_id:
            pdf_pane.object = ''
            status.object = 'Select a source'
            return
        key = f"{app_state.active_filter}_{app_state.active_orient}"
        flags = _source_flags.get(app_state.selected_id, {}).get('has_pdf', {})
        if flags.get(key):
            pdf_filename = config.PDF_PATTERN.format(
                field=config.FIELD_NAME, filter=app_state.active_filter,
                id=app_state.selected_id, orient=app_state.active_orient)
            pdf_path = os.path.join(config.DATA_ROOT, config.PDF_DIR, pdf_filename)
            if os.path.exists(pdf_path):
                pdf_pane.object = pdf_path
                status.object = ''
            else:
                status.object = 'PDF file not found'
        else:
            pdf_pane.object = ''
            status.object = 'No PDF available'

    app_state.param.watch(update_pdf, ['selected_id', 'active_filter', 'active_orient'])
    return pn.Column(pdf_pane, status)


def create_tag_editor():
    """Tag editor with add/remove functionality."""
    tag_display = pn.pane.Markdown('**Tags:** None')
    tag_selector = pn.widgets.Select(name='Add Tag', options=TAG_VOCABULARY, width=200)
    add_btn = pn.widgets.Button(name='Add', button_type='success', width=60)
    remove_btn = pn.widgets.Button(name='Remove Selected', button_type='danger', width=120)

    current_tags = []

    def update_display():
        tags_str = ', '.join(current_tags) if current_tags else 'None'
        tag_display.object = f'**Tags:** {tags_str}'

    def add_tag(event):
        tag = tag_selector.value
        if tag and tag not in current_tags:
            current_tags.append(tag)
            update_display()
            save_tags()

    def remove_tag(event):
        # Remove last tag for simplicity
        if current_tags:
            current_tags.pop()
            update_display()
            save_tags()

    def save_tags():
        if app_state.selected_id:
            db = _tags_db
            if "sources" not in db:
                db["sources"] = {}
            if app_state.selected_id not in db["sources"]:
                db["sources"][app_state.selected_id] = {}
            db["sources"][app_state.selected_id]["tags"] = current_tags
            save_tags_db(db)

    add_btn.on_click(add_tag)
    remove_btn.on_click(remove_tag)

    def on_source_change(event):
        nonlocal current_tags
        if app_state.selected_id:
            source_data = _tags_db.get("sources", {}).get(app_state.selected_id, {})
            current_tags = source_data.get("tags", [])
        else:
            current_tags = []
        update_display()

    app_state.param.watch(on_source_change, 'selected_id')
    update_display()

    return pn.Column(
        pn.pane.Markdown('**Tag Editor**'),
        tag_display,
        pn.Row(tag_selector, add_btn, remove_btn),
    )


def create_redshift_bar():
    """Redshift display and editor."""
    z_display = pn.pane.Markdown('**Redshift:** N/A')
    z_input = pn.widgets.FloatInput(name='New z_spec', value=None, width=150)
    z_apply = pn.widgets.Button(name='Apply', button_type='primary', width=60)

    def update_z_display(event=None):
        if not app_state.selected_id:
            z_display.object = '**Redshift:** N/A'
            return

        catalog = get_merged_catalog()
        id_col = config.CATALOG_ID_COL
        source_row = None
        for row in catalog:
            if str(row[id_col]) == app_state.selected_id:
                source_row = row
                break

        if source_row is None:
            z_display.object = '**Redshift:** N/A'
            return

        rec = build_source_record(source_row)
        z_spec = rec.get('z_spec')
        z_phot = rec.get('z_phot')
        ra = rec.get('ra')
        dec = rec.get('dec')

        z_spec_str = f"{z_spec:.4f}" if z_spec is not None else "N/A"
        z_phot_str = f"{z_phot:.4f}" if z_phot is not None else "N/A"
        ra_str = f"{ra:.6f}" if ra is not None else "N/A"
        dec_str = f"{dec:.6f}" if dec is not None else "N/A"

        z_display.object = f"""
**Redshift:**
- z_spec: {z_spec_str}
- z_phot: {z_phot_str}

**Coordinates:**
- RA: {ra_str}
- DEC: {dec_str}
"""

    def apply_z(event):
        if app_state.selected_id and z_input.value is not None:
            db = _tags_db
            if "sources" not in db:
                db["sources"] = {}
            if app_state.selected_id not in db["sources"]:
                db["sources"][app_state.selected_id] = {}
            db["sources"][app_state.selected_id]["z_spec"] = z_input.value
            save_tags_db(db)
            update_z_display()

    z_apply.on_click(apply_z)
    app_state.param.watch(update_z_display, 'selected_id')
    update_z_display()

    return pn.Column(z_display, pn.Row(z_input, z_apply))


def create_combo_buttons():
    """Filter/Orient combination buttons."""
    buttons = {}
    button_row = pn.Row()

    def make_click_handler(f, o):
        def handler(event):
            app_state.active_filter = f
            app_state.active_orient = o
        return handler

    for f, o in COMBOS:
        key = f"{f}_{o}"
        btn = pn.widgets.Button(name=key, button_type='primary', width=100)
        btn.on_click(make_click_handler(f, o))
        buttons[key] = btn
        button_row.append(btn)

    return button_row


# ── Main App Layout ──────────────────────────────────────────────────────────
def create_app():
    init_state()

    # Initialize state
    app_state.source_list = get_all_sources()
    app_state.filtered_sources = get_sources_with_spec_z()

    # Create components
    source_selector, update_selector_cb = create_source_list_widget()
    coord_search = create_coord_search_widget(update_selector_cb)
    spectra_2d = create_spectra_2d_panel()
    spectra_1d = create_spectra_1d_panel()
    sed_panel = create_sed_panel()
    image_panel = create_image_panel()
    pdf_viewer = create_pdf_viewer()
    tag_editor = create_tag_editor()
    redshift_bar = create_redshift_bar()
    combo_buttons = create_combo_buttons()

    # Filter toggle
    filter_toggle = pn.widgets.ToggleGroup(
        name='Filter', options=['spec-z', 'all'], behavior='radio', value='spec-z'
    )

    def on_filter_change(event):
        app_state.show_only_spec_z = (event.new == 'spec-z')
        update_selector_cb()

    filter_toggle.param.watch(on_filter_change, 'value')

    # Dark mode toggle (Panel doesn't support dark mode natively, but we can add CSS)
    theme_toggle = pn.widgets.Toggle(name='Dark Theme', value=True)

    # Layout
    header = pn.Row(
        pn.pane.Markdown('# PRISM'),
        filter_toggle,
        theme_toggle,
        sizing_mode='stretch_width'
    )

    left_panel = pn.Column(
        pn.pane.Markdown('### Sources'),
        source_selector,
        width=300,
        sizing_mode='stretch_height'
    )

    right_panel = pn.Column(
        combo_buttons,
        pn.pane.Markdown('### 2D Spectrum'),
        spectra_2d,
        pn.pane.Markdown('### 1D Spectrum'),
        spectra_1d,
        pn.pane.Markdown('### PDF'),
        pdf_viewer,
        pn.pane.Markdown('### NIRCam'),
        image_panel,
        pn.Row(sed_panel, pn.Column(tag_editor, redshift_bar)),
        sizing_mode='stretch_width',
        scroll=True,
    )

    main_layout = pn.Row(
        left_panel,
        right_panel,
        sizing_mode='stretch_both'
    )

    return pn.Column(header, main_layout)


# ── Run ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.servable()
