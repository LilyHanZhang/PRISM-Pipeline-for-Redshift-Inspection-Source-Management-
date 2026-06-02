# 1D & 2D plots
```python
idx = 1
# obs_pa = 0.0
plt.close()
for i, tmp_spec_path in enumerate(list_spec[idx:idx+1]):
    tmp_spec_fits = fits.open(tmp_spec_path)
    '''source information'''
    tmp_id = tmp_spec_fits[0].header['ID']        
    tmp_filter = tmp_spec_fits[0].header['FILTER'] 
    if 'GS_V3_PA' in tmp_spec_fits[0].header: obs_pa = tmp_spec_fits[0].header['GS_V3_PA']
    if tmp_filter == 'F444W': WRANGE = np.array([3.8, 5.1]); mag_keyword = 'F444W_mag'
    elif tmp_filter == 'F322W2': WRANGE = np.array([2.35, 4.1]); mag_keyword = 'F356W_mag'
    elif tmp_filter == 'F356W': WRANGE = np.array([3.05, 4.0]); mag_keyword = 'F356W_mag'
    # if 'F444W_mag' in np.concatenate(np.array(tmp_spec_fits[0].header.cards)):
    #     mag_keyword = 'F444W_mag'
    # elif 'F160W_mag' in np.concatenate(np.array(tmp_spec_fits[0].header.cards)):
    #     mag_keyword = 'F160W_mag'
    tmp_mag = tmp_spec_fits[0].header[mag_keyword]   
    if tmp_mag == 'nan': tmp_mag = 99.; tmp_spec_fits[0].header[mag_keyword] = 99.
    tmp_flux_mJy = 10**(-0.4 * tmp_spec_fits[0].header[mag_keyword]) * 3631e3 # 10**(-0.4 * tmp_spec_fits[0].header['MAG_AUTO']) * 3631e3 
    if mag_keyword == '1mm_mag': tmp_flux_mJy = tmp_mag
    tmp_N_R = tmp_spec_fits[0].header['N_R']
    tmp_N_C = tmp_spec_fits[0].header['N_C']
    if tmp_N_C > tmp_N_R: obs_pa = obs_pa - 90
    tmp_tb_stats = Table(tmp_spec_fits['STATS'].data)
    tmp_N_A, tmp_N_B = np.sum(tmp_tb_stats['module'] == 'A'), np.sum(tmp_tb_stats['module'] == 'B')
    tmp_RA, tmp_DEC = tmp_spec_fits[0].header['RA0'], tmp_spec_fits[0].header['DEC0']
    tmp_coord = SkyCoord(tmp_RA, tmp_DEC, unit = (u.deg, u.deg))
    tmp_x0, tmp_y0 = wcs.utils.skycoord_to_pixel(tmp_coord, wcs_LW)
    
    '''optional optimal extraction?'''
    do_boxcar = False
    tmp_opt_profile_name = 'none'
    try:
        ### morphological parameters
        # tmp_A, tmp_B, tmp_PA = 3.0, 3.0, 0.0
        #tmp_A, tmp_B, tmp_PA = tmp_spec_fits[0].header['A'], tmp_spec_fits[0].header['B'], tmp_spec_fits[0].header['PA']
        #tmp_A, tmp_B = tmp_A * 0.03, tmp_B * 0.03
        #tmp_A, tmp_B = np.clip(tmp_A, 0.06, 10), np.clip(tmp_B, 0.06, 10)
        #tmp_PA = (tmp_PA + obs_pa) % 180
        '''Prepare profile'''
        tmp_x0, tmp_y0 = wcs.utils.skycoord_to_pixel(tmp_coord, wcs_LW)
        hf_box = int(0.0629 * tmp_spec_fits['spec2d'].data.shape[0] * 1.5 / pix_LW )
        # tmp_img = img_LW[int(tmp_y0)-hf_box-1:int(tmp_y0)+hf_box+2,int(tmp_x0)-hf_box-1:int(tmp_x0)+hf_box+2]
        tmp_img = Cutout2D(img_LW, position = tmp_coord, size = (hf_box, hf_box), wcs = wcs_LW).data
        tmp_img_rot = ndimage.rotate(np.nan_to_num(tmp_img), obs_pa, reshape = False); tmp_img_rot[tmp_img_rot == 0] = np.nan
        tmp_y_model_data = np.nansum(tmp_img_rot, axis = 1)
        tmp_y_model_data_img = tmp_y_model_data.copy()
        tmp_opt_profile_name = 'image_collapse'
        ### fit gaussian model to collapsed image model
        try:
            popt, pcov = optimize.curve_fit(f = gauss, xdata = np.arange(len(tmp_y_model_data)), ydata = tmp_y_model_data / np.max(tmp_y_model_data),
                                            p0 = [len(tmp_y_model_data)//2 , 1, 1])
            ### overall chi^2
            chisq_gaussian = np.sum((gauss(np.arange(len(tmp_y_model_data)), *popt) - tmp_y_model_data / np.max(tmp_y_model_data))**2)
            ### central 1/3 chi^2
            arg_center_profile = np.arange(int(len(tmp_y_model_data) * 0.33), int(len(tmp_y_model_data) * 0.66))
            chisq_gaussian_center = np.sum((gauss(np.arange(len(tmp_y_model_data)), *popt)[arg_center_profile] - tmp_y_model_data[arg_center_profile] / np.max(tmp_y_model_data[arg_center_profile]))**2)
        except (ValueError, RuntimeError) as e: chisq_gaussian, chisq_gaussian_center, popt = np.nan, np.nan, np.array([np.nan, np.nan, np.nan])
        #### default: directly using the collapsed image cutout as profile: `tmp_y_model_data`
        #### use central best-fit gaussian profile, if the full fit is bad and best fit is centralized?
        if (chisq_gaussian**0.5 > 0.5) & (chisq_gaussian_center**0.5 < 0.5) & (np.abs(popt[0] - len(tmp_y_model_data)/2) <= len(tmp_y_model_data) / 10):
            tmp_y_model_data = gauss(np.arange(len(tmp_y_model_data)), *popt)
            tmp_opt_profile_name = 'image_collapse_gaussian'
        #### use parametrized profile, if image model is bad?
        '''elif (np.sum(np.isfinite(tmp_y_model_data) & (tmp_y_model_data != 0)) == 0) | np.isnan(chisq_gaussian_center) | (chisq_gaussian**0.5 > 0.5) | (np.abs(popt[0] - len(tmp_y_model_data)/2) > len(tmp_y_model_data) / 10):
            ## spatial direction profile (sersic, read from JADES catalog)
            xx, yy = np.meshgrid(np.arange(tmp_img.shape[0]), np.arange(tmp_img.shape[1]))
            tmp_2d_model = models.Sersic2D(x_0 = hf_box / 2 , y_0 = hf_box / 2, amplitude = 1., r_eff = tmp_A / pix_LW, n = 1,
                                           ellip = 1 - tmp_B/tmp_A, theta = np.deg2rad(tmp_PA))
            tmp_y_model_data = np.sum(tmp_2d_model(xx, yy), axis = 1)
            tmp_y_model_data_param = tmp_y_model_data.copy()
            tmp_opt_profile_name = 'image_SExtractor_model'
        '''
        # try:
        #     tmp_y_model = interpolate.UnivariateSpline(np.arange(tmp_img.shape[1]) * pix_LW / 0.0629, 
        #                                                tmp_y_model_data, s = 0, k = 1, ext = 'zeros')
        try:
            tmp_y_model = interpolate.UnivariateSpline((np.arange(len(tmp_y_model_data)) - len(tmp_y_model_data)//2) * pix_LW / 0.0629 + tmp_spec_fits['spec2d'].data.shape[0]//2, 
                                                       tmp_y_model_data / np.max(tmp_y_model_data), s = 0, k = 1, ext = 'zeros')
        except:
            tmp_y_model = interpolate.UnivariateSpline(np.arange(31), 
                                                       np.concatenate((np.zeros(13), np.ones(5), np.zeros(13))), 
                                                       s = 0, k = 1, ext = 'zeros')
            tmp_opt_profile_name = 'boxcar_5pix'
    except KeyError:
        tmp_opt_profile_name = 'none'
        do_boxcar = True

    # do_boxcar = True
    ### extract spectra from images with continuum?
    try:
        cont_mag_limit = np.log10(9 / 10 * 2 * (tmp_spec_fits[0].header['EFFEXPTM'] / 1e4)**-0.5 / 3631e6) * -2.5
    except KeyError:
        cont_mag_limit = 23.0
    if tmp_mag < cont_mag_limit: is_cont = True
    else:  is_cont = False
    
    # is_cont = True
    
    '''2d spec'''
    tmp_spec_2d = tmp_spec_fits['spec2d'].data
    tmp_line_2d = tmp_spec_fits['line2d'].data
    tmp_wht_2d  = tmp_spec_fits['wht2d'].data
    wave_sample_c = tmp_spec_fits[1].header['WAVE_1'] + np.arange(tmp_spec_fits[1].header['NAXIS1']) * tmp_spec_fits[1].header['D_WAVE']
    
    '''optional new median filtering'''
    tmp_line_2d_old = tmp_line_2d.copy()
    tmp_highSN_mask_2d = tmp_line_2d_old / tmp_wht_2d**-0.5 > 2.0
    tmp_spec_2d_cts = tmp_spec_2d * f_sens_AR(wave_sample_c)
    arg_x_isnum = np.where(np.sum(np.isnan(tmp_spec_2d_cts), axis = 0) != len(tmp_spec_2d_cts))[0]
    tmp_spec_2d_cts_medflt = tmp_spec_2d_cts.copy()
    tmp_spec_2d_cts_medflt[:,arg_x_isnum]= ndimage.median_filter(tmp_spec_2d_cts[:,arg_x_isnum], footprint = np.ones((1, 150)), mode = 'reflect')
    tmp_spec_2d_cts[tmp_highSN_mask_2d] = tmp_spec_2d_cts_medflt[tmp_highSN_mask_2d]
    tmp_spec_2d_cts_medflt_new = tmp_spec_2d_cts_medflt.copy()
    tmp_spec_2d_cts_medflt_new[:,arg_x_isnum] = ndimage.median_filter(tmp_spec_2d_cts[:,arg_x_isnum], footprint = np.ones((1, 50)), mode = 'reflect')
    tmp_line_2d_new = tmp_spec_2d - np.nan_to_num(tmp_spec_2d_cts_medflt_new / f_sens_AR(wave_sample_c))
    if sigma_clipped_stats(tmp_line_2d_new, sigma = 2)[2] <= sigma_clipped_stats(tmp_line_2d_old, sigma = 2)[2]:
        tmp_line_2d = tmp_line_2d_new
    else: tmp_line_2d = tmp_line_2d_old
    # tmp_line_2d = tmp_line_2d_old

    ## if not enough wavelength coverage, then skip
    if np.sum(np.isnan(np.nansum(tmp_spec_2d, axis = 0)) == False) < 200: continue
        
    ## get y center:
    tmp_spec_ydir = np.nansum(tmp_spec_2d * tmp_wht_2d, axis = 1) / np.nansum(tmp_wht_2d, axis = 1)
    tmp_yc   = tmp_spec_2d.shape[0]//2
    tmp_aper = 2
    
    '''>>> extract 1d spectra <<<'''
    if do_boxcar == False: 
        '''### optimized extraction'''
        profile_1d = tmp_y_model(np.arange(tmp_line_2d.shape[0]) + 0.) 
        profile_1d = profile_1d / np.nansum(profile_1d)
        numerator_cont = np.nansum(((tmp_spec_2d * tmp_wht_2d).T * profile_1d), axis = 1)
        numerator      = np.nansum(((tmp_line_2d * tmp_wht_2d).T * profile_1d), axis = 1)
        denominator    = np.nansum(tmp_wht_2d.T * profile_1d**2, axis = 1)
        tmp_spec_1d      = numerator      / denominator
        tmp_spec_1d_cont = numerator_cont / denominator
        tmp_unc_1d = np.nansum(tmp_wht_2d.T * profile_1d**2, axis = 1)**-0.5
        ### good wave masking
        arg_good_wave = np.where(np.sum(tmp_wht_2d == 0, axis = 0) == 0)[0]
        wave_sample_c_opt, tmp_spec_1d_cont_opt = wave_sample_c[arg_good_wave], tmp_spec_1d_cont[arg_good_wave]
        tmp_spec_1d_opt, tmp_unc_1d_opt = tmp_spec_1d[arg_good_wave], tmp_unc_1d[arg_good_wave]
    '''### boxcar extraction'''
    tmp_spec_1d_cont = np.nansum(tmp_spec_2d[tmp_yc-tmp_aper:tmp_yc+tmp_aper+1], axis = 0) 
    tmp_spec_1d      = np.nansum(tmp_line_2d[tmp_yc-tmp_aper:tmp_yc+tmp_aper+1], axis = 0) 
    tmp_unc_1d = np.nansum(tmp_wht_2d[tmp_yc-tmp_aper:tmp_yc+tmp_aper+1]**-1, axis = 0)**0.5
    ### aperture correction:
    profile_1d = tmp_y_model(np.arange(tmp_line_2d.shape[0]) + 0.)
    profile_1d = profile_1d / np.nansum(profile_1d)
    tmp_aper_corr = np.sum(profile_1d) / np.sum(profile_1d[tmp_yc-tmp_aper:tmp_yc+tmp_aper+1]) 
    tmp_spec_1d_cont = tmp_spec_1d_cont * tmp_aper_corr 
    tmp_spec_1d      = tmp_spec_1d      * tmp_aper_corr
    tmp_unc_1d       = tmp_unc_1d       * tmp_aper_corr
    ### good wave masking
    arg_good_wave = np.where(np.sum(tmp_wht_2d[tmp_yc-tmp_aper:tmp_yc+tmp_aper+1] == 0, axis = 0) == 0)[0]
    wave_sample_c_box, tmp_spec_1d_cont_box = wave_sample_c[arg_good_wave], tmp_spec_1d_cont[arg_good_wave]
    tmp_spec_1d_box, tmp_unc_1d_box         = tmp_spec_1d[arg_good_wave], tmp_unc_1d[arg_good_wave]

    if do_boxcar == True: 
        wave_sample_c, tmp_spec_1d_cont, tmp_spec_1d, tmp_unc_1d = wave_sample_c_box, tmp_spec_1d_cont_box, tmp_spec_1d_box, tmp_unc_1d_box
    elif do_boxcar == False: 
        snr_cont_opt = np.nanmedian((tmp_spec_1d_cont_opt/tmp_unc_1d_opt)[tmp_unc_1d_opt < np.nanmedian(tmp_unc_1d_opt) * 2])
        snr_cont_box = np.nanmedian((tmp_spec_1d_cont_box/tmp_unc_1d_box)[tmp_unc_1d_box < np.nanmedian(tmp_unc_1d_box) * 2])
        if (snr_cont_opt > snr_cont_box) & (is_cont == True):
            wave_sample_c, tmp_spec_1d_cont, tmp_spec_1d, tmp_unc_1d = wave_sample_c_opt, tmp_spec_1d_cont_opt, tmp_spec_1d_opt, tmp_unc_1d_opt
        else:
            do_boxcar = True
            wave_sample_c, tmp_spec_1d_cont, tmp_spec_1d, tmp_unc_1d = wave_sample_c_box, tmp_spec_1d_cont_box, tmp_spec_1d_box, tmp_unc_1d_box

    if np.nanmedian(tmp_spec_1d[tmp_spec_1d!=0]) < 0:
        tmp_spec_1d = tmp_spec_1d - np.nanmedian(tmp_spec_1d[tmp_spec_1d!=0])


    '''
    Plot Spectra:
    '''
    ### figure layout
    e_fig, b_fig = 0.1, 0.9  # edge space, bottom space
    x_fig, y_fig = 16 + e_fig * 3, 7 + e_fig * 3 + b_fig
    fig = plt.figure(figsize = (x_fig / y_fig * 6, 6))
    ax_im = fig.add_axes([e_fig/x_fig, (5 + b_fig + 2 * e_fig)/y_fig, 2 / x_fig , 2 / y_fig]) # direct image - 1
    ax_2d = fig.add_axes([(2 + e_fig*2)/x_fig, (5 + b_fig + 2 * e_fig)/y_fig, 14 / x_fig , 2 / y_fig]) # 2d spec (cont)
    ax_li = fig.add_axes([(2 + e_fig*2)/x_fig, (3 + b_fig + e_fig)/y_fig, 14 / x_fig , 2 / y_fig]) # 2d spec (line)
    ax_1d = fig.add_axes([(2 + e_fig*2)/x_fig, b_fig/y_fig, 14 / x_fig , 3 / y_fig]) # 1d spec
    ax = [ax_2d, ax_li, ax_1d]
    ### ax[0]: 2D spectra with continuum
    vmin_zscale, vmax_zscale = ZScaleInterval().get_limits(tmp_spec_2d[:,100:-100])
    tmp_aspect = (np.diff(WRANGE) - 0.1) / tmp_spec_fits[1].header['D_WAVE'] / (tmp_spec_2d.shape[0]-1) / 7
    tmp_xticks = (np.arange(np.ceil((WRANGE[0] + 0.05) * 10)/10, WRANGE[1] - 0.05 + 0.01, 0.1) - tmp_spec_fits[1].header['WAVE_1'])/tmp_spec_fits[1].header['D_WAVE']
    ax[0].imshow(tmp_spec_2d, aspect = tmp_aspect, vmin = vmin_zscale, vmax = vmax_zscale,
                 cmap = plt.cm.gist_gray_r, origin = 'lower')
    ax[0].set(ylim = (0.5, tmp_spec_2d.shape[0] - 0.5), xticks = [], 
              aspect = tmp_aspect,
              xlim = (0.05 / tmp_spec_fits[1].header['D_WAVE'], 
                      (WRANGE[1] - WRANGE[0] - 0.05) / tmp_spec_fits[1].header['D_WAVE']))
    ax[0].set_yticks([tmp_spec_2d.shape[0] / 2.]); ax[0].set_yticklabels([""])
    ax[0].set_xticks(tmp_xticks);  ax[0].set_xticklabels([])
    
    
    ### ax[1]: 2D spectra, line only
    vmin_zscale, vmax_zscale = ZScaleInterval().get_limits(tmp_line_2d[:,100:-100])
    ax[1].imshow(tmp_line_2d,  vmin = vmin_zscale/2., vmax = vmax_zscale,
                 cmap = plt.cm.gist_gray_r, origin = 'lower')
    ax[1].set(ylim = (0.5, tmp_spec_2d.shape[0] - 0.5), xticks = [], 
              aspect = tmp_aspect,
              xlim = (0.05 / tmp_spec_fits[1].header['D_WAVE'], 
                      (WRANGE[1] - WRANGE[0] - 0.05) / tmp_spec_fits[1].header['D_WAVE']))
    ax[1].set_yticks([tmp_spec_2d.shape[0] / 2.]); ax[1].set_yticklabels([""])
    ax[1].set_xticks(tmp_xticks);  ax[1].set_xticklabels([])
    for tmp_ax in ax[:2]:
        tmp_ax.yaxis.set_tick_params(width = 1.5, size = 4, right = True)
    if is_cont:
        ax[0].axhline(tmp_yc + tmp_aper + 1.5, color = 'w', ls = '--', dashes = (4, 4))
        ax[0].axhline(tmp_yc - tmp_aper - 0.5, color = 'w', ls = '--', dashes = (4, 4))
    ax[1].axhline(tmp_yc + tmp_aper + 1.5, color = 'w', ls = '--', dashes = (4, 4))
    ax[1].axhline(tmp_yc - tmp_aper - 0.5, color = 'w', ls = '--', dashes = (4, 4))
    
    
    ### ax[2]: 1D spectra
    kwargs_1dspec = dict(lw = 1.5, drawstyle = 'steps-mid')
    ax[2].plot(wave_sample_c, ndimage.gaussian_filter1d(tmp_spec_1d, 0.6), # tmp_spec_1d, #
               color = 'k', zorder = 100, **kwargs_1dspec)
    if is_cont:
        ax[2].plot(wave_sample_c, ndimage.gaussian_filter1d(tmp_spec_1d_cont, 0.6), color = 'dimgrey', **kwargs_1dspec)
        
        tmp_max_counts = np.nanpercentile(tmp_spec_1d_cont[(np.isnan(tmp_spec_1d_cont) == False) & (tmp_spec_1d_cont != 0)], 95) * 1.25
    else:
        tmp_max_counts = np.nanpercentile(tmp_spec_1d[(np.isnan(tmp_spec_1d) == False) & (tmp_spec_1d != 0)], 95) * 1.5
    try:
        ax[2].axhline(0, color = 'grey', ls = '--')
    except LinAlgError: continue
    ax[2].set(xlim = (WRANGE[0] + 0.05, WRANGE[1] - 0.05), 
              xticks = np.arange(np.ceil((WRANGE[0] + 0.05) * 10)/10, WRANGE[1] - 0.05 + 0.01, 0.1),
              xlabel = 'Observed Wavelength (µm)', ylabel = 'Flux Density [mJy]')
    ax[2].set_ylim(np.clip(vmin_zscale * 2.0, -0.035, 0), np.clip(tmp_max_counts, 0.015, 1e8)) 

    ### annotate axes
    corner_text(ax[0], loc = 2, s = 'ID%s' % (tmp_id), weight = 'semibold', color = 'r', fontsize = 20, edge = 5e-3)
    corner_text(ax[0], loc = 1, s = '%s=%.2f' % (mag_keyword, tmp_mag), color = 'r', fontsize = 15, edge = 5e-3)
    if tmp_N_A == 0: corner_text(ax[0], s = 'modB', loc = 3, color = 'r', fontsize = 14, edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    elif tmp_N_B == 0: corner_text(ax[0], s = 'modA', loc = 3, color = 'r', fontsize = 14, edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    else: corner_text(ax[0], s = 'modA:%d / modB:%d' % (tmp_N_A, tmp_N_B), loc = 3, color = 'r', fontsize = 14, edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    corner_text(ax[1], loc = 3, s = 'Continuum Subtracted', color = 'r', fontsize = 15, edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    corner_text(ax[1], loc = 4, s = '(%.5f, %.5f)' % (tmp_RA, tmp_DEC), color = 'r', fontsize = 15, edge = 5e-3)
    corner_text(ax[2], loc = 1, s = '$f_\mathrm{%s}$=%.3f mJy' % (mag_keyword.split('_')[0], tmp_flux_mJy), fontsize = 15, color = 'r', edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    corner_text(ax[2], loc = 2, s = 'N(C)=%2d' % tmp_N_C, fontsize = 14, color = 'r', 
                edge = 5e-3, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
    
    ### redshift and line indicator
    # tmp_spec_fits[0].header['zspec'] = 2.938 / 0.6564 - 1
    if 'zspec' in tmp_spec_fits[0].header:
        corner_text(ax[2], loc = 4, s = 'z=%.3f' % tmp_spec_fits[0].header['zspec'], color = 'r', fontsize = 15,
                    edge = 5e-3, zorder = 999, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])
        kwargs_axvline = dict(ymin = 0.0, ymax = 1.0, zorder = -5, lw = 5, alpha = 0.5, color = 'skyblue') # 0.90, 0.98
        arr_line_name = np.array([r'[O$\,$II]', r'H$\rm\beta$',  r'[O$\,$III]',   r'[O$\,$III]',  r'H$\rm\alpha$',   
                                  r'[N$\,$II]', r'[S$\,$II]', r'[S$\,$III]', r'[S$\,$III]',
                                  r'Pa$\rm\delta$',  r'He$\,$I', r'Pa$\rm\gamma$', r'[Fe$\,$II]', r'Pa$\rm\beta$',  
                                  r'[Fe$\,$II]', r'Pa$\rm\alpha$', r'He$\,$I', 'H$_2$', r'Br$\rm\gamma$', 'H$_2$', 'H$_2$',
                                  r'Br$\rm\beta$', 'H$_2$', 'PAH',  r'Pf$\,$8', r'Br$\rm\alpha$'])
        arr_line_wave = np.array([3728.5,  4862.67,   4960.295,  5008.24,  6564.61,  6585.27,  6725.48,
                                  9071.1,  9533.21,    10052.1,  10833.3,  10941.0,  12570.2,  12821.5,
                                  16440.5, 18756.0,    20592.5,  21223.8,  21661.0,  24072.6,  24243.6,
                                  26258.4, 28032.6,      32900,  37405.2,  40522.3
                                 ])
        for p in range(len(arr_line_wave))[::-1]:
            if (1 + tmp_spec_fits[0].header['zspec']) * arr_line_wave[p] / 1e4 < WRANGE[0] + 0.05: continue
            if (1 + tmp_spec_fits[0].header['zspec']) * arr_line_wave[p] / 1e4 > WRANGE[1] - 0.05: continue
            ax[2].axvline((1 + tmp_spec_fits[0].header['zspec']) * arr_line_wave[p] / 1e4, **kwargs_axvline)
            ax[2].text((1 + tmp_spec_fits[0].header['zspec']) * arr_line_wave[p] / 1e4,
                       ax[2].get_ylim()[0] * 0.25 + ax[2].get_ylim()[1] * 0.75, s = arr_line_name[p], zorder = -2, color = 'b',
                       ha = 'center', va = 'center', rotation = 90, fontsize = 14,
                       path_effects = [pe.withStroke(linewidth = 5, foreground = "w")])
        # for Ca_T in [0.8498, 0.8542, 0.8662]:
        #     ax[2].axvline((1 + tmp_spec_fits[0].header['zspec']) * Ca_T, color = 'b', ymin = ymin, ymax = ymax)
        # fig.subplots_adjust(hspace = -0.20, wspace = 0, bottom = 0.13, top = 1.10, right = 0.98, left = 0.15)
    elif 'z_a' in tmp_spec_fits[0].header:
        corner_text(ax[2], loc = 4, s = 'z=%.2f (%.2f–%.2f)' % (tmp_spec_fits[0].header['z_a'], tmp_spec_fits[0].header['l95'], tmp_spec_fits[0].header['u95']),
                    color = 'r', fontsize = 15, edge = 5e-3, zorder = 999, path_effects = [pe.withStroke(linewidth = 2.5, foreground = "w")])


    ### ax_im: Direct Image
    hf_box = int(0.0629 * (tmp_spec_2d.shape[0] - 1) / 2. / pix_LW)
    # tmp_img = img_LW[int(tmp_y0)-hf_box-1:int(tmp_y0)+hf_box+2,int(tmp_x0)-hf_box-1:int(tmp_x0)+hf_box+2]
    orig_size_as = 0.0629 * tmp_spec_2d.shape[0] * 1.5
    orig_size_pix = int(orig_size_as / pix_LW) # pixel
    tmp_img = Cutout2D(img_LW, position = tmp_coord, size = (orig_size_pix, orig_size_pix), wcs = wcs_LW).data
    tmp_img_rot = ndimage.rotate(np.nan_to_num(tmp_img), obs_pa, reshape = False); tmp_img_rot[tmp_img_rot == 0] = np.nan
    '''if np.prod(img_LW_b.shape) > 1e3:
        tmp_img_b = Cutout2D(img_LW_b, position = tmp_coord, size = (orig_size_pix, orig_size_pix), wcs = wcs_LW).data
        tmp_img_g = Cutout2D(img_LW_g, position = tmp_coord, size = (orig_size_pix, orig_size_pix), wcs = wcs_LW).data
        tmp_img_rot_g = ndimage.rotate(np.nan_to_num(tmp_img_g), obs_pa, reshape = False); tmp_img_rot_g[tmp_img_rot_g == 0] = np.nan
        tmp_img_rot_b = ndimage.rotate(np.nan_to_num(tmp_img_b), obs_pa, reshape = False); tmp_img_rot_b[tmp_img_rot_b == 0] = np.nan
        tmp_img_rot_rgb = np.dstack((tmp_img_rot, tmp_img_rot_g, tmp_img_rot_b))
        tmp_img_rot_rgb = np.clip((np.log10(tmp_img_rot_rgb / np.clip(np.nanpercentile(tmp_img_rot_rgb, 99.5), 1, 10) + 10**-2.0) + 2.0) / 2.0, 0, 1)
    else:
        tmp_img_rot_rgb = np.dstack((tmp_img_rot, np.zeros_like(tmp_img_rot), np.zeros_like(tmp_img_rot)))
        tmp_img_rot_rgb = np.clip((np.log10(tmp_img_rot_rgb / np.clip(np.nanpercentile(tmp_img_rot_rgb, 99.5), 1, 10) + 10**-2.0) + 2.0) / 2.0, 0, 1)
    '''
    if (tmp_N_A == 0) & (tmp_N_C == 0): 
        tmp_img_rot = tmp_img_rot[:,::-1]; tmp_img_rot_rgb = tmp_img_rot_rgb[:,::-1,:]
    if tmp_N_R == 0: 
        tmp_img_rot = tmp_img_rot[:,::-1]; tmp_img_rot_rgb = tmp_img_rot_rgb[:,::-1,:]
    try:
        tmp_img_vmin, tmp_img_vmax = ZScaleInterval().get_limits(tmp_img_rot[np.isfinite(tmp_img_rot)])
        tmp_img_vmin, tmp_img_vmax = tmp_img_vmin, tmp_img_vmax * 2
    except IndexError:
        tmp_img_vmin, tmp_img_vmax = 0.0, 0.1
    ax_im.imshow(np.nan_to_num(tmp_img_rot), 
                 # vmin = tmp_img_vmin, vmax = tmp_img_vmax,
                 # vmin = np.nanpercentile(tmp_img_rot, 2.5), vmax = np.nanpercentile(tmp_img_rot, 97.5),
                 cmap = plt.cm.gist_heat, origin = 'lower')
    
    ax_im.set(xlim = (orig_size_pix//2-hf_box-1, orig_size_pix//2+hf_box-1),
              ylim = (orig_size_pix//2-hf_box-1, orig_size_pix//2+hf_box-1))
    ax_im.set_xticks([])
    ax_im.set_yticks([])
    corner_text(ax_im, loc = 4, s = '(%.1f, %.1f)' % (tmp_x0, tmp_y0), color = 'w', fontsize = 10)
    corner_text(ax_im, loc = 2, s = '090-200-444', color = 'w', fontsize = 13, weight = 'semibold')
    print(i, tmp_id, '%s=%.2f' % (mag_keyword, tmp_mag), 'chi_img_model=%.3f' % chisq_gaussian**0.5, tmp_opt_profile_name, 'do_boxcar=', do_boxcar)
    # tmp_spec_fits.close()
    '''
    Save spectral plot (remember to change the path)
    '''

    plt.savefig(tmp_spec_path.replace('.fits', '.pdf'), dpi = 150)
    
    '''
    Save 1D spectra (remember to change the path)
    '''
    tb_1dspec_box = Table(names = ['wavelength_um', 'box_spec1d_mJy', 'box_line1d_mJy', 'box_fluxerr_mJy'], 
                          data  = [wave_sample_c_box, tmp_spec_1d_cont_box, tmp_spec_1d_box, tmp_unc_1d_box])
    if tmp_opt_profile_name != 'none':
        tb_1dspec_opt = Table(names = ['wavelength_um', 'opt_spec1d_mJy', 'opt_line1d_mJy', 'opt_fluxerr_mJy'], 
                              data  = [wave_sample_c_opt, tmp_spec_1d_cont_opt, tmp_spec_1d_opt, tmp_unc_1d_opt])
        tb_1dspec = join(tb_1dspec_opt, tb_1dspec_box, keys = 'wavelength_um', join_type = 'outer')
    else: tb_1dspec = tb_1dspec_box
    for col in tb_1dspec.colnames: 
        tb_1dspec[col].fill_value = np.nan
        if 'mJy' in col: tb_1dspec[col].info.format = '.5f'
        else: tb_1dspec[col].info.format = '.4f'
    tb_1dspec = tb_1dspec.filled()
    # tb_1dspec = Table(names = ['wavelength_um', 'cont_flux_mJy', 'flux_mJy', 'fluxerr_mJy'], 
    #                   data  = [wave_sample_c, tmp_spec_1d_cont, tmp_spec_1d, tmp_unc_1d])
    # tb_1dspec['wavelength_um'].info.format = '.4f'
    # tb_1dspec['cont_flux_mJy'].info.format = '.5f'
    # tb_1dspec['flux_mJy'].info.format = '.5f'
    # tb_1dspec['fluxerr_mJy'].info.format = '.5f'
    ### comments of the 1D spectra
    tb_1dspec.meta['comments'] = ['-' * 70]
    # for y in [' = '.join(map(str, x[:2])) for x in tmp_spec_fits[0].header.cards][4:]:
    #     tb_1dspec.meta['comments'].append(y)
    # tb_1dspec.meta['comments'].append('-' * 70)
    tb_1dspec.meta['comments'].append('1D spectrum was extracted at y_c=%.1f with full aperture height = %.1f' % (tmp_yc, tmp_aper * 2 + 1))
    if is_cont:
        tb_1dspec.meta['comments'].append('I only subtracted common grism sky background. Contaminants are not subtracted.')
    else:
        tb_1dspec.meta['comments'].append('Extracted from 2D grism images that have been continuum/background-subtracted.')
    tb_1dspec.meta['comments'].append('Be careful about potential contaminant & aperture loss.')
    tb_1dspec.meta['comments'].append('' * 70)
    tb_1dspec.meta['comments'].append('Produced by F. Sun (CfA | Harvard & Smithsonian, %s)' % time.strftime("%Y/%m/%d",  time.localtime()))
    tb_1dspec.meta['comments'].append('-' * 70)
    # ascii.write(tb_1dspec, tmp_spec_path.replace('/2D_spec/', '/1D_spec/').replace('/spec_2d_', '/spec_1d_').replace('.fits', '.dat'), 
    #             format = 'commented_header', overwrite = True)
    tmp_spec_1d_fits = fits.BinTableHDU(tb_1dspec)
    for x in tmp_spec_fits[0].header.cards[4:]: tmp_spec_1d_fits.header['HIERARCH ' + x[0]] = (x[1], x[2])
    tmp_spec_1d_fits.header['N_A']      = (tmp_N_A, 'number of mod A exposure')
    tmp_spec_1d_fits.header['N_B']      = (tmp_N_B, 'number of mod A exposure')
    tmp_spec_1d_fits.header['boxcar']   = (do_boxcar, 'is extracted using boxcar method')
    tmp_spec_1d_fits.header['y_c']      = (tmp_yc,   'y_center [pix] of boxcar aperture in 2d spectrum')
    tmp_spec_1d_fits.header['aper']     = (tmp_aper * 2 + 1, 'total aperture height [pix] of boxcar')
    tmp_spec_1d_fits.header['profile']  = (tmp_opt_profile_name, 'image profile used for aperture correction factor')
    tmp_spec_1d_fits.header['apercorr'] = (tmp_aper_corr, 'aperture correction factor for boxcar spectrum')
    tmp_spec_1d_fits.writeto(tmp_spec_path.replace('/2D_spec/', '/1D_spec/').replace('/spec_2d_', '/spec_1d_'), overwrite = True)
plt.show()
```