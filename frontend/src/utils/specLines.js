export const SPECTRAL_LINES = [
  { name: 'Lyα', wavelength: 1215.67 },
  { name: 'CIV', wavelength: 1549.06 },
  { name: 'CIII]', wavelength: 1908.73 },
  { name: 'MgII', wavelength: 2798.75 },
  { name: '[OII]', wavelength: 3727.09 },
  { name: 'Hδ', wavelength: 4101.74 },
  { name: 'Hγ', wavelength: 4340.47 },
  { name: 'Hβ', wavelength: 4861.33 },
  { name: '[OIII]4959', wavelength: 4958.91 },
  { name: '[OIII]5007', wavelength: 5006.84 },
  { name: 'Hα', wavelength: 6562.82 },
]

export function getObservedWavelength(restAngstrom, z) {
  return restAngstrom * (1 + z) / 10000
}
