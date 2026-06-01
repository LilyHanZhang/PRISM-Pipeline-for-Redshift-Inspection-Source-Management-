import { useState, useEffect } from 'react'
import { getCutoutUrl, getRGBUrl, getBands } from '../utils/api'

const CMAPS = ['viridis', 'gray', 'inferno', 'hot', 'plasma', 'magma', 'RdBu', 'seismic']
const SCALES = ['zscale', 'linear', 'log', 'sqrt']

function ImagePanel({ source }) {
  const [bands, setBands] = useState([])
  const [expandedBands, setExpandedBands] = useState({})
  const [size, setSize] = useState(3)
  const [cmap, setCmap] = useState('viridis')
  const [scale, setScale] = useState('zscale')
  const [showRGB, setShowRGB] = useState(true)
  const [expanded, setExpanded] = useState(true)

  useEffect(() => {
    getBands().then(res => {
      setBands(res.data)
      const initial = {}
      res.data.forEach(b => { initial[b] = true })
      setExpandedBands(initial)
    }).catch(() => setBands([]))
  }, [])

  const toggleBand = (band) => {
    setExpandedBands(prev => ({ ...prev, [band]: !prev[band] }))
  }

  return (
    <div className="panel-orange rounded-lg border">
      <div className="flex items-center justify-between p-3">
        <h3 className="font-semibold text-orange">NIRCam Cutouts</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setShowRGB(!showRGB)}
            className={`text-xs px-2 py-1 rounded border ${
              showRGB ? 'chip chip-orange' : 'border-gray-300 dark:border-gray-600 text-gray-400'
            }`}
          >
            RGB
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs px-2 py-1 rounded border border-orange-300 dark:border-orange-700 text-orange hover:bg-orange-100 dark:hover:bg-orange-900"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-orange-200 dark:border-orange-800 p-3">
          {/* Controls */}
          <div className="flex flex-wrap gap-2 mb-3">
            <input
              type="number"
              value={size}
              onChange={e => setSize(Number(e.target.value))}
              className="w-16 text-sm px-2 py-1 rounded border bg-white dark:bg-gray-800"
              min={1}
              max={30}
            />
            <span className="text-xs self-center text-orange/60">arcsec</span>
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

          {/* RGB */}
          {showRGB && source.has_rgb && (
            <div className="mb-3">
              <div className="flex justify-center">
                <img
                  src={getRGBUrl(source.id, size)}
                  alt="RGB"
                  className="w-48 h-48 object-cover rounded border border-orange-200 dark:border-orange-800"
                />
              </div>
              <div className="text-xs text-center text-orange mt-1">RGB Composite</div>
            </div>
          )}

          {/* Individual bands */}
          <div className="grid grid-cols-3 gap-3">
            {bands.map(band => (
              <div key={band} className="border border-orange-200 dark:border-orange-800 rounded p-2">
                <button
                  onClick={() => toggleBand(band)}
                  className="w-full text-xs font-medium text-orange hover:underline text-left"
                >
                  {band} {expandedBands[band] ? '▾' : '▸'}
                </button>
                {expandedBands[band] && (
                  <div className="mt-2 flex justify-center">
                    <img
                      src={getCutoutUrl(source.id, band, size, cmap, scale)}
                      alt={band}
                      className="w-40 h-40 object-cover rounded border border-orange-100 dark:border-orange-900"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ImagePanel
