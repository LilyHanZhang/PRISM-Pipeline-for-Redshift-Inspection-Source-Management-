import { useState } from 'react'
import { updateZSpec } from '../utils/api'

function RedshiftBar({ source, onZSpecUpdate }) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(source.z_spec ?? '')

  const dzIndicator = (() => {
    if (source.z_spec == null) return { text: 'no z_spec', color: 'text-gray-400' }
    if (source.z_phot == null) return { text: 'no z_phot', color: 'text-gray-400' }
    const dz = Math.abs(source.z_spec - source.z_phot) / (1 + source.z_spec)
    if (dz < 0.1) return { text: '✓ consistent', color: 'text-green-500' }
    return { text: '⚠ discrepant', color: 'text-amber-500' }
  })()

  const handleSave = async () => {
    const z = parseFloat(value)
    if (isNaN(z)) return
    try {
      await updateZSpec(source.id, z)
      onZSpecUpdate(z)
      setEditing(false)
    } catch (e) {
      console.error('Failed to update z_spec', e)
    }
  }

  return (
    <div className="panel-pink rounded-lg border p-3">
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-sm text-pink font-medium">z_spec:</span>
          {editing ? (
            <div className="flex items-center gap-1">
              <input
                type="number"
                step="0.001"
                value={value}
                onChange={e => setValue(e.target.value)}
                className="w-24 text-sm px-2 py-1 rounded border border-pink-300 dark:border-pink-700 bg-white dark:bg-gray-800 text-pink"
                onKeyDown={e => e.key === 'Enter' && handleSave()}
                autoFocus
              />
              <button
                onClick={handleSave}
                className="text-sm px-2 py-1 rounded bg-pink-500 text-white hover:bg-pink-600"
              >
                ✓
              </button>
              <button
                onClick={() => { setEditing(false); setValue(source.z_spec ?? '') }}
                className="text-sm px-2 py-1 rounded border border-pink-300 dark:border-pink-700 text-pink"
              >
                ✗
              </button>
            </div>
          ) : (
            <button
              onClick={() => { setEditing(true); setValue(source.z_spec ?? '') }}
              className="text-sm text-pink hover:underline"
            >
              {source.z_spec ?? '—'} ✏
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-pink font-medium">z_phot:</span>
          <span className="text-sm text-pink/60">{source.z_phot ?? '—'}</span>
        </div>

        <div className={`text-sm font-medium ${dzIndicator.color}`}>
          Δz: {dzIndicator.text}
        </div>
      </div>
      <div className="flex items-center gap-4 flex-wrap mt-2 text-xs text-pink/50">
        <span>RA: {source.ra?.toFixed(6) ?? '—'}</span>
        <span>Dec: {source.dec?.toFixed(6) ?? '—'}</span>
      </div>
    </div>
  )
}

export default RedshiftBar
