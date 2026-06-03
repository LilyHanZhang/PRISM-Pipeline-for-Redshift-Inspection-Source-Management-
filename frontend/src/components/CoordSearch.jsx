import { useState } from 'react'
import { sourcesNear } from '../utils/api'

function CoordSearch({ sources, onSelect, onFilter }) {
  const [ra, setRa] = useState('')
  const [dec, setDec] = useState('')
  const [radius, setRadius] = useState(10)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    if (!ra || !dec) return
    setLoading(true)
    try {
      const res = await sourcesNear(parseFloat(ra), parseFloat(dec), radius)
      setResults(res.data)
      onFilter(res.data.map(r => r.id))
    } catch (e) {
      setResults([])
      onFilter(null)
    }
    setLoading(false)
  }

  const handleClear = () => {
    setResults([])
    setRa('')
    setDec('')
    setRadius(10)
    onFilter(null)
  }

  return (
    <div>
      <div className="flex flex-wrap gap-2 items-center">
        <input
          type="number"
          step="any"
          placeholder="RA (deg)"
          value={ra}
          onChange={e => setRa(e.target.value)}
          className="w-32 text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
        />
        <input
          type="number"
          step="any"
          placeholder="Dec (deg)"
          value={dec}
          onChange={e => setDec(e.target.value)}
          className="w-32 text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
        />
        <input
          type="number"
          placeholder="Radius″"
          value={radius}
          onChange={e => setRadius(Number(e.target.value))}
          className="w-20 text-sm px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="text-sm px-3 py-1 rounded bg-violet-500 text-white hover:bg-violet-600 disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
        {results.length > 0 && (
          <button
            onClick={handleClear}
            className="text-sm px-3 py-1 rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Clear ({results.length} found)
          </button>
        )}
      </div>
    </div>
  )
}

export default CoordSearch
