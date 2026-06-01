import { useState } from 'react'
import { sourcesNear } from '../utils/api'

function CoordSearch({ sources, onSelect }) {
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
    } catch (e) {
      setResults([])
    }
    setLoading(false)
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
      </div>

      {results.length > 0 && (
        <div className="mt-2 max-h-48 overflow-y-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-1 px-2">ID</th>
                <th className="text-left py-1 px-2">Sep″</th>
                <th className="text-left py-1 px-2">z_spec</th>
                <th className="text-left py-1 px-2">z_phot</th>
              </tr>
            </thead>
            <tbody>
              {results.map(r => {
                const src = sources.find(s => s.id === r.id)
                return (
                  <tr
                    key={r.id}
                    onClick={() => onSelect(r.id)}
                    className="cursor-pointer hover:bg-violet-50 dark:hover:bg-violet-950 border-b border-gray-100 dark:border-gray-800"
                  >
                    <td className="py-1 px-2 text-violet font-medium">{r.id}</td>
                    <td className="py-1 px-2">{r.separation_arcsec.toFixed(2)}</td>
                    <td className="py-1 px-2">{src?.z_spec ?? '—'}</td>
                    <td className="py-1 px-2">{src?.z_phot ?? '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default CoordSearch
