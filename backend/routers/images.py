import os
import io
import hashlib
import numpy as np
from astropy.io import fits
from PIL import Image
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from backend import config
from backend.utils.cutout import generate_cutout, get_nircam_band_path, scan_available_bands
from backend.state import get_merged_catalog

router = APIRouter(prefix="/api/images", tags=["images"])


def get_cache_path(source_id, band, size, cmap, scale):
    """Get the cache file path for a cutout."""
    cache_dir = config.CUTOUT_CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)

    key = f"{source_id}_{band}_{size}_{cmap}_{scale}"
    filename = hashlib.md5(key.encode()).hexdigest() + ".png"
    return os.path.join(cache_dir, filename)


def apply_scale(data, scale_method):
    """Apply scaling to image data."""
    if data is None:
        return None

    data = np.array(data, dtype=np.float64)

    if scale_method == "zscale":
        from astropy.visualization import ZScaleInterval
        interval = ZScaleInterval()
        vmin, vmax = interval.get_limits(data)
    elif scale_method == "asinh":
        from astropy.visualization import AsinhStretch, ImageNormalize
        from astropy.visualization import ZScaleInterval
        interval = ZScaleInterval()
        vmin, vmax = interval.get_limits(data)
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=AsinhStretch())
        data = norm(data)
        data = np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=0.0)
        return np.clip(data, 0, 1)
    elif scale_method == "linear":
        vmin, vmax = np.nanpercentile(data, [1, 99])
    elif scale_method == "log":
        data = np.log10(np.maximum(data, np.nanmin(data[data > 0]) if np.any(data > 0) else 1))
        vmin, vmax = np.nanpercentile(data, [1, 99])
    elif scale_method == "sqrt":
        data = np.sqrt(np.maximum(data, 0))
        vmin, vmax = np.nanpercentile(data, [1, 99])
    else:
        vmin, vmax = np.nanpercentile(data, [1, 99])

    data = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
    return data


def apply_cmap(data, cmap_name):
    """Apply a colormap to normalized data and return PIL Image."""
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors

    cmap = cm.get_cmap(cmap_name)
    rgba = cmap(data)
    rgba = (rgba[:, :, :3] * 255).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGB")


def get_source_coords(catalog, source_id):
    """Get RA/DEC for a source from the merged catalog, handling column renaming."""
    id_col = config.CATALOG_ID_COL
    for r in catalog:
        if str(r[id_col]) == source_id:
            ra = None
            for c in [config.CATALOG_RA_COL, "RA_1", "RA"]:
                if c and c in r.colnames:
                    try:
                        ra = float(r[c])
                    except (TypeError, ValueError):
                        pass
                    break
            dec = None
            for c in [config.CATALOG_DEC_COL, "DEC_1", "DEC"]:
                if c and c in r.colnames:
                    try:
                        dec = float(r[c])
                    except (TypeError, ValueError):
                        pass
                    break
            if ra is not None and dec is not None:
                return ra, dec
    return None, None


@router.get("/cutout/{source_id}/{band}")
def get_cutout(
    source_id: str,
    band: str,
    size: float = Query(default=config.DEFAULT_CUTOUT_SIZE_ARCSEC),
    cmap: str = Query(default=config.DEFAULT_CMAP),
    scale: str = Query(default=config.DEFAULT_SCALE),
):
    """Cutout PNG for one NIRCam band."""
    cache_path = get_cache_path(source_id, band, size, cmap, scale)
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            return Response(content=f.read(), media_type="image/png")

    catalog = get_merged_catalog()
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not available")

    ra, dec = get_source_coords(catalog, source_id)
    if ra is None or dec is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} coordinates not found")

    band_path = get_nircam_band_path(band)
    if band_path is None:
        raise HTTPException(status_code=404, detail=f"Band {band} not found")

    cutout = generate_cutout(band_path, ra, dec, size)
    if cutout is None or cutout.data is None:
        raise HTTPException(status_code=404, detail="Cutout generation failed")

    scaled = apply_scale(cutout.data, scale)
    img = apply_cmap(scaled, cmap)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    png_bytes = buf.read()

    with open(cache_path, "wb") as f:
        f.write(png_bytes)

    return Response(content=png_bytes, media_type="image/png")


@router.get("/rgb/{source_id}")
def get_rgb(
    source_id: str,
    size: float = Query(default=config.DEFAULT_CUTOUT_SIZE_ARCSEC),
):
    """RGB composite PNG."""
    catalog = get_merged_catalog()
    if catalog is None:
        raise HTTPException(status_code=404, detail="Catalog not available")

    ra, dec = get_source_coords(catalog, source_id)
    if ra is None or dec is None:
        raise HTTPException(status_code=404, detail=f"Source {source_id} coordinates not found")
    channels = {}
    ref_shape = None

    for ch, band in config.RGB_BANDS.items():
        band_path = get_nircam_band_path(band)
        if band_path is None:
            continue
        cutout = generate_cutout(band_path, ra, dec, size)
        if cutout is None or cutout.data is None:
            continue
        
        scaled = apply_scale(cutout.data, config.RGB_SCALE)
        if scaled is None:
            continue
            
        if ref_shape is None:
            ref_shape = scaled.shape
        elif scaled.shape != ref_shape:
            continue
            
        channels[ch] = scaled

    if len(channels) < 3:
        raise HTTPException(status_code=404, detail="Not enough bands for RGB")

    h, w = channels["r"].shape[:2]
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[:, :, 0] = (channels["r"] * 255).astype(np.uint8)
    rgb[:, :, 1] = (channels["g"] * 255).astype(np.uint8)
    rgb[:, :, 2] = (channels["b"] * 255).astype(np.uint8)

    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.read(), media_type="image/png")


@router.get("/bands")
def get_bands():
    """List of available bands."""
    return scan_available_bands()
