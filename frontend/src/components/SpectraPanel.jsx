import { useState, useEffect, useMemo } from 'react'
import Plot from 'react-plotly.js'
import { get2DSpectrumUrl, get1DSpectrum } from '../utils/api'
import { SPECTRAL_LINES, getObservedWavelength, FILTER_RANGES } from '../utils/specLines'

const CMAPS = ['viridis', 'gray', 'inferno', 'hot', 'plasma', 'magma', 'RdBu', 'seismic']
const SCALES = ['zscale', 'linear', 'log', 'sqrt']

function SpectraPanel({ source, filter, orient, mode = '2d' }) {
  const [cmap, setCmap] = useState('viridis')
  const [scale, setScale] = useState('zscale')
  const [spectrum1d, setSpectrum1d] = useState(null)

  const combo = `${filter}_${orient}`
  const hasData = mode === '2d'
    ? source.has_2d?.[combo]
    : source.has_1d?.[combo]

  const accentClass = filter === 'F356W' ? 'panel-blue' : 'panel-cyan'
  const textClass = filter === 'F356W' ? 'text-blue' : 'text-cyan'

  useEffect(() => {
    if (mode === '1d' && hasData) {
      get1DSpectrum(source.id, filter, orient)
        .then(res => setSpectrum1d(res.data))
        .catch(() => setSpectrum1d(null))
    }
  }, [source.id, filter, orient, mode, hasData])

  const spectralLines = useMemo(() => {
    if (!source.z_spec) return []
    const range = FILTER_RANGES[filter]
    return SPECTRAL_LINES
      .map(line => ({
        ...line,
        observed: getObservedWavelength(line.wavelength, source.z_spec),
      }))
      .filter(l => l.observed >= range.min && l.observed <= range.max)
  }, [source.z_spec, filter])

  if (!hasData) {
    return (
      <div className={`${accentClass} rounded-lg border p-8 text-center`}>
        <p className={`${textClass} opacity-60`}>
          {mode === '2d' ? '2D' : '1D'} spectrum: {filter} {orient} not available
        </p>
      </div>
    )
  }

  if (mode === '2d') {
    return (
      <div className={`${accentClass} rounded-lg border p-3`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`font-semibold ${textClass}`}>2D Spectrum — {filter} {orient}</h3>
          <div className="flex gap-2">
            <select
              value={cmap}
              onChange={e => setCmap(e.target.value)}
              className="text-sm px-2 py-1 rounded border bg-white dark:bg-gray-800"
            >
              {CMAPS.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select
              value={scale}
              onChange={e => setScale(e.target.value)}
              className="text-sm px-2 py-1 rounded border bg-white dark:bg-gray-800"
            >
              {SCALES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
        <div className="flex justify-center">
          <img
            src={get2DSpectrumUrl(source.id, filter, orient, cmap, scale)}
            alt={`2D spectrum ${filter} ${orient}`}
            className="max-w-full rounded"
          />
        </div>
      </div>
    )
  }

  // 1D mode
  if (!spectrum1d) {
    return (
      <div className="panel-green rounded-lg border p-8 text-center">
        <p className="text-green opacity-60">Loading 1D spectrum...</p>
      </div>
    )
  }

  const traces = [
    {
      x: spectrum1d.wave,
      y: spectrum1d.flux,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#16a34a', width: 1.5 },
      name: 'continuum',
    },
  ]

  if (spectrum1d.line) {
    traces.push({
      x: spectrum1d.wave,
      y: spectrum1d.line,
      type: 'scatter',
      mode: 'lines',
      line: { color: '#dc2626', width: 1.5, dash: 'dash' },
      name: 'line',
    })
  }

  if (spectrum1d.err) {
    const upper = spectrum1d.flux.map((f, i) => f + spectrum1d.err[i])
    const lower = spectrum1d.flux.map((f, i) => f - spectrum1d.err[i])
    traces.push({
      x: [...spectrum1d.wave, ...spectrum1d.wave.reverse()],
      y: [...upper, ...lower.reverse()],
      type: 'scatter',
      fill: 'toself',
      fillcolor: 'rgba(22, 163, 74, 0.15)',
      line: { color: 'transparent' },
      name: '±1σ',
      showlegend: false,
    })
  }

  const shapes = spectralLines
    .filter(l => l.observed > 0)
    .map(l => ({
      type: 'line',
      x0: l.observed,
      x1: l.observed,
      y0: 0,
      y1: 1,
      yref: 'paper',
      line: { color: '#16a34a', width: 1, dash: 'dash' },
    }))

  const annotations = spectralLines
    .filter(l => l.observed > 0)
    .map(l => ({
      x: l.observed,
      y: 1,
      yref: 'paper',
      text: l.name,
      showarrow: false,
      font: { size: 10, color: '#16a34a' },
    }))

  const range = FILTER_RANGES[filter]

  // Calculate y-axis range using 95th percentile (matching reference code approach)
  const fluxValues = spectrum1d.flux.filter(f => f !== null && f !== undefined && !isNaN(f) && f !== 0)
  let yRange = null
  if (fluxValues.length > 0) {
    const sorted = [...fluxValues].sort((a, b) => a - b)
    const p95 = sorted[Math.floor(sorted.length * 0.95)]
    const tmpMaxCounts = p95 * 1.5
    const yMin = -0.035
    const yMax = Math.max(Math.min(tmpMaxCounts, 1e8), 0.015)
    yRange = [yMin, yMax]
  }

  return (
    <div className="panel-green rounded-lg border p-3">
      <h3 className="font-semibold text-green mb-2">
        1D Spectrum — {filter} {orient} (z={source.z_spec ?? '—'})
      </h3>
      <Plot
        data={traces}
        layout={{
          margin: { t: 20, r: 20, b: 40, l: 50 },
          height: 250,
          showlegend: true,
          legend: { x: 1, y: 1, xanchor: 'right', yanchor: 'top', bgcolor: 'rgba(255,255,255,0.8)', bordercolor: 'rgba(0,0,0,0.2)', borderwidth: 1 },
          xaxis: {
            title: 'Wavelength (μm)',
            gridcolor: '#e5e7eb',
            range: [range.min, range.max],
          },
          yaxis: { 
            title: 'Flux', 
            gridcolor: '#e5e7eb',
            ...(yRange && { range: yRange }),
          },
          shapes,
          annotations,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#374151' },
        }}
        config={{ responsive: true, displayModeBar: false }}
        className="w-full"
      />
    </div>
  )
}

export default SpectraPanel
