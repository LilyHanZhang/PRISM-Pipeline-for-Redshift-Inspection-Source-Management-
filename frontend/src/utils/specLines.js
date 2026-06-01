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
  { name: '[NII]', wavelength: 6585.27 },
  { name: '[SII]', wavelength: 6725.48 },
  { name: '[SIII]9071', wavelength: 9071.1 },
  { name: '[SIII]9533', wavelength: 9533.21 },
  { name: 'Paδ', wavelength: 10052.1 },
  { name: 'HeI10833', wavelength: 10833.3 },
  { name: 'Paγ', wavelength: 10941.0 },
  { name: '[FeII]', wavelength: 12570.2 },
  { name: 'Paβ', wavelength: 12821.5 },
  { name: '[FeII]16440', wavelength: 16440.5 },
  { name: 'Paα', wavelength: 18756.0 },
  { name: 'HeI20592', wavelength: 20592.5 },
  { name: 'H₂21223', wavelength: 21223.8 },
  { name: 'Brγ', wavelength: 21661.0 },
  { name: 'H₂24072', wavelength: 24072.6 },
  { name: 'H₂24243', wavelength: 24243.6 },
  { name: 'Brβ', wavelength: 26258.4 },
  { name: 'H₂28032', wavelength: 28032.6 },
  { name: 'PAH', wavelength: 32900 },
  { name: 'Pf8', wavelength: 37405.2 },
  { name: 'Brα', wavelength: 40522.3 },
]

export function getObservedWavelength(restAngstrom, z) {
  return restAngstrom * (1 + z) / 10000
}

export const FILTER_RANGES = {
  F356W: { min: 3.1, max: 4.0 },
  F444W: { min: 3.8, max: 5.1 },
}
