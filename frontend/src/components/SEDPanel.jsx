import { useState } from 'react'
import Plot from 'react-plotly.js'

function SEDPanel({ source }) {
  const [unit, setUnit] = useState('flux')

  if (!source.has_sed) {
    return (
      <div className="panel-yellow rounded-lg border p-8 text-center">
        <p className="text-yellow opacity-60">No photometric data available</p>
      </div>
    )
  }

  // Placeholder: in production, this would fetch photometry from the backend
  const mockData = {
    wave: [0.7, 0.9, 1.15, 1.5, 2.0, 2.77, 3.56, 4.44],
    flux: [1.2, 1.5, 2.1, 2.8, 3.2, 4.1, 4.8, 5.2],
    err: [0.1, 0.1, 0.15, 0.2, 0.2, 0.3, 0.3, 0.4],
    bands: ['F070W', 'F090W', 'F115W', 'F150W', 'F200W', 'F277W', 'F356W', 'F444W'],
  }

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
            x: mockData.wave,
            y: unit === 'flux' ? mockData.flux : mockData.flux.map(f => -2.5 * Math.log10(f / 3631)),
            error_y: {
              type: 'data',
              array: mockData.err,
              visible: true,
            },
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#ca8a04', width: 2 },
            marker: { size: 6 },
            text: mockData.bands,
            hovertemplate: '%{text}<br>λ=%{x:.2f} µm<br>Flux=%{y:.2f}<extra></extra>',
          },
        ]}
        layout={{
          margin: { t: 10, r: 10, b: 40, l: 50 },
          height: 250,
          xaxis: { title: 'Wavelength (µm)', gridcolor: '#e5e7eb' },
          yaxis: { title: unit === 'flux' ? 'Flux (µJy)' : 'AB Magnitude', gridcolor: '#e5e7eb' },
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

export default SEDPanel
