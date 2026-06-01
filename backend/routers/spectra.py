import os
import io
import numpy as np
from astropy.io import fits
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from backend import config
from backend.utils.spectrum_render import render_2d_png, read_1d_spectrum

router = APIRouter(prefix="/api/spectra", tags=["spectra"])


@router.get("/{source_id}/1d/{filter_name}/{orient}")
def get_1d_spectrum(source_id: str, filter_name: str, orient: str):
    """1D spectrum as JSON {wave, flux, err}."""
    data = read_1d_spectrum(source_id, filter_name, orient)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"1D spectrum not found for {source_id} {filter_name} {orient}",
        )
    return data


@router.get("/{source_id}/2d/{filter_name}/{orient}")
def get_2d_spectrum(
    source_id: str,
    filter_name: str,
    orient: str,
    cmap: str = Query(default="viridis"),
    scale: str = Query(default="zscale"),
):
    """2D spectrum as PNG."""
    png_bytes = render_2d_png(source_id, filter_name, orient, cmap, scale)
    if png_bytes is None:
        raise HTTPException(
            status_code=404,
            detail=f"2D spectrum not found for {source_id} {filter_name} {orient}",
        )
    return Response(content=png_bytes, media_type="image/png")
