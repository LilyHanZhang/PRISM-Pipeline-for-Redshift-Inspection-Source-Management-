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
            data = hdul[0].data
            if data is None:
                return None

            if isinstance(data, np.ndarray) and data.dtype.names:
                wave = data["WAVE"].tolist()
                flux = data["FLUX"].tolist()
                err = data["ERR"].tolist() if "ERR" in data.dtype.names else None
            else:
                if data.ndim == 2:
                    wave = data[0].tolist()
                    flux = data[1].tolist()
                    err = data[2].tolist() if data.shape[0] > 2 else None
                elif data.ndim == 1:
                    wave = list(range(len(data)))
                    flux = data.tolist()
                    err = None
                else:
                    return None

            return {
                "wave": [float(w) for w in wave],
                "flux": [float(f) for f in flux],
                "err": [float(e) for e in err] if err else None,
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
            data = hdul[0].data
            if data is None:
                return None

        scaled = apply_scale(data, scale)
        return apply_cmap_to_png(scaled, cmap)
    except Exception:
        return None
