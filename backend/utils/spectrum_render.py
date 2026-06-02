import os
import io
import re
import numpy as np
from astropy.io import fits
from PIL import Image
from backend import config


def get_1d_path(source_id, filter_name, orient):
    """Get the 1D spectrum FITS file path."""
    spec_dir = os.path.join(config.DATA_ROOT, config.SPEC_1D_DIR)
    filename = config.SPEC_1D_PATTERN.format(
        field=config.FIELD_NAME,
        filter=filter_name,
        id=source_id,
        orient=orient,
    )
    path = os.path.join(spec_dir, filename)
    return path if os.path.exists(path) else None


def get_2d_path(source_id, filter_name, orient):
    """Get the 2D spectrum FITS file path."""
    spec_dir = os.path.join(config.DATA_ROOT, config.SPEC_2D_DIR)
    filename = config.SPEC_2D_PATTERN.format(
        field=config.FIELD_NAME,
        filter=filter_name,
        id=source_id,
        orient=orient,
    )
    path = os.path.join(spec_dir, filename)
    return path if os.path.exists(path) else None


def read_1d_spectrum(source_id, filter_name, orient):
    """Read a 1D spectrum FITS file and return {wave, flux, err}."""
    path = get_1d_path(source_id, filter_name, orient)
    if path is None:
        return None

    try:
        with fits.open(path) as hdul:
            if len(hdul) < 2:
                return None

            table = hdul[1].data
            if table is None:
                return None

            col_names = table.dtype.names

            wave_col = None
            for c in ["wavelength_um", "WAVE", "wavelength", "WAVELENGTH"]:
                if c in col_names:
                    wave_col = c
                    break

            flux_col = None
            for c in ["opt_spec1d_mJy", "FLUX", "flux", "SPEC1D"]:
                if c in col_names:
                    flux_col = c
                    break

            line_col = None
            for c in ["opt_line1d_mJy", "LINE", "line", "SPEC1D_LINE"]:
                if c in col_names:
                    line_col = c
                    break

            err_col = None
            for c in ["opt_fluxerr_mJy", "ERR", "flux_err", "fluxerr", "SPEC1D_ERR"]:
                if c in col_names:
                    err_col = c
                    break

            if wave_col is None or flux_col is None:
                return None

            wave = table[wave_col].tolist()
            flux = table[flux_col].tolist()
            line = table[line_col].tolist() if line_col else None
            err = table[err_col].tolist() if err_col else None

            def clean_floats(arr):
                result = []
                for v in arr:
                    try:
                        fv = float(v)
                        if np.isnan(fv) or np.isinf(fv):
                            result.append(None)
                        else:
                            result.append(fv)
                    except (TypeError, ValueError):
                        result.append(None)
                return result

            return {
                "wave": clean_floats(wave),
                "flux": clean_floats(flux),
                "line": clean_floats(line) if line else None,
                "err": clean_floats(err) if err else None,
            }
    except Exception:
        return None


def apply_scale(data, scale_method):
    """Apply scaling to image data and return normalized array."""
    if data is None:
        return None

    data = np.array(data, dtype=np.float64)

    if scale_method == "zscale":
        from astropy.visualization import ZScaleInterval
        interval = ZScaleInterval()
        try:
            vmin, vmax = interval.get_limits(data)
        except Exception:
            vmin, vmax = np.nanpercentile(data, [1, 99])
    elif scale_method == "linear":
        vmin, vmax = np.nanpercentile(data, [1, 99])
    elif scale_method == "log":
        positive = data[data > 0]
        if len(positive) > 0:
            min_val = np.nanmin(positive)
        else:
            min_val = 1
        data = np.log10(np.maximum(data, min_val))
        vmin, vmax = np.nanpercentile(data, [1, 99])
    elif scale_method == "sqrt":
        data = np.sqrt(np.maximum(data, 0))
        vmin, vmax = np.nanpercentile(data, [1, 99])
    else:
        vmin, vmax = np.nanpercentile(data, [1, 99])

    denom = vmax - vmin
    if denom == 0:
        denom = 1e-10
    data = np.clip((data - vmin) / denom, 0, 1)
    return data


def apply_cmap_to_png(data, cmap_name):
    """Apply a colormap to normalized data and return PNG bytes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.cm as cm

    cmap = cm.get_cmap(cmap_name)
    rgba = cmap(data)
    rgba = (rgba[:, :, :3] * 255).astype(np.uint8)
    img = Image.fromarray(rgba, mode="RGB")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def render_2d_png(source_id, filter_name, orient, cmap="viridis", scale="zscale"):
    """Render a 2D spectrum FITS file to PNG bytes."""
    path = get_2d_path(source_id, filter_name, orient)
    if path is None:
        return None

    try:
        with fits.open(path) as hdul:
            if len(hdul) < 2:
                return None
            data = hdul[1].data
            if data is None:
                return None

        scaled = apply_scale(data, scale)
        return apply_cmap_to_png(scaled, cmap)
    except Exception:
        return None
