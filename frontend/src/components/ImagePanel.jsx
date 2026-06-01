import { useState, useEffect } from 'react'
import { getCutoutUrl, getRGBUrl, getBands } from '../utils/api'

const CMAPS = ['viridis', 'gray', 'inferno', 'hot', 'plasma', 'magma', 'RdBu']
const SCALES = ['zscale', 'linear', 'log', 'sqrt']

function ImagePanel({ source }) {
  const [bands, setBands] = useState([])
  const [activeBands, setActiveBands] = useState([])
  const [size, setSize] = useState(5)
  const [cmap, setCmap] = useState('viridis')
  const [scale, setScale] = useState('zscale')
  const [showRGB, setShowRGB] = useState(true)

  useEffect(() => {
    getBands().then(res => {
      setBands(res.data)
      setActiveBands(res.data.slice(0, 3))
    }).catch(() => setBands([]))
  }, [])

  const toggleBand = (band) => {
    setActiveBands(prev =>
      prev.includes(band) ? prev.filter(b => b !== band) : [...prev, band]
    )
  }

  return (
    <div className="panel-orange rounded-lg border p-3">
      <h3 className="font-semibold text-orange mb-2">NIRCam Cutouts</h3>

      {/* Controls */}
      <div className="flex flex-wrap gap-2 mb-3">
        <div className="flex gap-1">
          {bands.map(band => (
            <button
              key={band}
              onClick={() => toggleBand(band)}
              className={`text-xs px-2 py-1 rounded border transition ${
                activeBands.includes(band)
                  ? 'chip chip-orange'
                  : 'border-gray-300 dark:border-gray-600 text-gray-400'
              }`}
            >
              {band}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowRGB(!showRGB)}
          className={`text-xs px-2 py-1 rounded border ${
            showRGB ? 'chip chip-orange' : 'border-gray-300 dark:border-gray-600 text-gray-400'
          }`}
        >
          RGB
        </button>
      </div>

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

      {/* Cutouts */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {showRGB && source.has_rgb && (
          <div className="flex-shrink-0">
            <img
              src={getRGBUrl(source.id, size)}
              alt="RGB"
              className="w-40 h-40 object-cover rounded border border-orange-200 dark:border-orange-800"
            />
            <div className="text-xs text-center text-orange mt-1">RGB</div>
          </div>
        )}
        {activeBands.map(band => (
          <div key={band} className="flex-shrink-0">
            <img
              src={getCutoutUrl(source.id, band, size, cmap, scale)}
              alt={band}
              className="w-40 h-40 object-cover rounded border border-orange-200 dark:border-orange-800"
            />
            <div className="text-xs text-center text-orange mt-1">{band}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ImagePanel
