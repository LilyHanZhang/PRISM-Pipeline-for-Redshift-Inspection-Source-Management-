from astropy.io import fits
from astropy.wcs import WCS
from astropy.nddata import Cutout2D
from astropy import units as u
import numpy as np

path = 'sapphires_edr_nircam_sci/4750_F444W_v05_sci.fits'
with fits.open(path) as h:
    data = np.array(h[0].data, dtype=np.float64)
    wcs = WCS(h[0].header)
    
    ra, dec = 63.96065, -24.19155
    position = (ra * u.deg, dec * u.deg)
    size = 5.0 * u.arcsec
    
    try:
        cutout = Cutout2D(data, position, size, wcs=wcs)
        print('Cutout shape:', cutout.data.shape)
    except Exception as e:
        print('Cutout error:', type(e).__name__, e)
        
        # Try with pixel coords
        x, y = wcs.all_world2pix(ra, dec, 0)
        position_pix = (x, y)
        try:
            cutout = Cutout2D(data, position_pix, size, wcs=wcs)
            print('Cutout shape (pixel):', cutout.data.shape)
        except Exception as e2:
            print('Pixel cutout error:', type(e2).__name__, e2)
