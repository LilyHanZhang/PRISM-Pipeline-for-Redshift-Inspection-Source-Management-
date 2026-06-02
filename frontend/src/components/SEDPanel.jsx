import { useState, useEffect } from 'react'
import Plot from 'react-plotly.js'

const LAMBDA_REF_DICT = {
  'F070W': 7039.12,
  'F090W': 9021.53,
  'F115W': 11542.61,
  'F140M': 14053.23,
  'F150W': 15007.44,
  'F162M': 16272.47,
  'F182M': 18451.67,
  'F200W': 19886.48,
  'F210M': 20954.51,
  'F250M': 25032.33,
  'F277W': 27617.40,
  'F300M': 29891.21,
  'F356W': 35683.62,
  'F360M': 36241.76,
  'F410M': 40822.38,
  'F444W': 44043.15,
  'F335M': 33537.23,
}

function SEDPanel({ source }) {
  const [unit, setUnit] = useState('mag')
  const [isDark, setIsDark] = useState(() => document.documentElement.getAttribute('data-theme') === 'dark')

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.getAttribute('data-theme') === 'dark')
    })
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    return () => observer.disconnect()
  }, [])

  const photBands = source.phot_bands || {}

  const bands = []
  const waves = []
  const mags = []
  const magErrs = []

  for (const [key, val] of Object.entries(photBands)) {
    if (key.endsWith('_MAG') && !key.endsWith('_MAG_e')) {
      const bandName = key.replace('_MAG', '')
      const errKey = key + '_e'
      const wave = LAMBDA_REF_DICT[bandName]
      if (wave && val !== null && val !== undefined) {
        bands.push(bandName)
        waves.push(wave / 10000)
        mags.push(val)
        magErrs.push(photBands[errKey] || 0)
      }
    }
  }

  const sorted = bands.map((_, i) => i).sort((a, b) => waves[a] - waves[b])
  const sortedWaves = sorted.map(i => waves[i])
  const sortedMags = sorted.map(i => mags[i])
  const sortedErrs = sorted.map(i => magErrs[i])
  const sortedBands = sorted.map(i => bands[i])

  const fluxes = sortedMags.map(m => 3631 * Math.pow(10, -0.4 * m))

  if (bands.length === 0) {
    return (
      <div className="panel-yellow rounded-lg border p-8 text-center">
        <p className="text-yellow opacity-60">No photometric data available</p>
      </div>
    )
  }

  const sedColor = isDark ? '#facc15' : '#ca8a04'
  const gridColor = isDark ? '#374151' : '#e5e7eb'
  const fontColor = isDark ? '#d1d5db' : '#374151'

  return (
    <div className="panel-yellow rounded-lg border p-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold text-yellow">SED</h3>
        <button
          onClick={() => setUnit(unit === 'flux' ? 'mag' : 'flux')}
          className="text-xs px-2 py-1 rounded border border-yellow-300 dark:border-yellow-700 text-yellow"
        >
          {unit === 'flux' ? 'µJy' : 'AB mag'}
        </button>
      </div>
      <Plot
        data={[
          {
            x: sortedWaves,
            y: unit === 'flux' ? fluxes : sortedMags,
            error_y: {
              type: 'data',
              array: unit === 'flux'
                ? fluxes.map((f, i) => f * 0.4 * Math.LN10 * sortedErrs[i] / 2.5)
                : sortedErrs,
              visible: true,
            },
            type: 'scatter',
            mode: 'lines+markers+text',
            line: { color: sedColor, width: 2 },
            marker: { size: 8 },
            text: sortedBands,
            textposition: 'top center',
            textfont: { size: 10, color: sedColor },
            hovertemplate: '%{text}<br>λ=%{x:.2f} µm<br>%{y:.2f}<extra></extra>',
          },
        ]}
        layout={{
          margin: { t: 20, r: 10, b: 40, l: 55 },
          height: 250,
          xaxis: { title: 'Wavelength (µm)', gridcolor: gridColor, zerolinecolor: gridColor, font: { color: fontColor } },
          yaxis: {
            title: unit === 'flux' ? 'Flux (µJy)' : 'AB Magnitude',
            gridcolor: gridColor,
            zerolinecolor: gridColor,
            autorange: unit === 'mag',
            font: { color: fontColor },
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: fontColor },
        }}
        config={{ responsive: true, displayModeBar: false }}
        className="w-full"
      />
    </div>
  )
}

export default SEDPanel
