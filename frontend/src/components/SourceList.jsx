import { useState, useMemo } from 'react'

function SourceList({ sources, selectedId, onSelect }) {
  const [search, setSearch] = useState('')
  const [activeTags, setActiveTags] = useState([])

  const allTags = useMemo(() => {
    const tags = new Set()
    sources.forEach(s => (s.tags || []).forEach(t => tags.add(t)))
    return Array.from(tags).sort()
  }, [sources])

  const filtered = useMemo(() => {
    return sources.filter(s => {
      if (search && !s.id.toLowerCase().includes(search.toLowerCase())) return false
      if (activeTags.length > 0) {
        const sourceTags = s.tags || []
        if (!activeTags.every(t => sourceTags.includes(t))) return false
      }
      return true
    })
  }, [sources, search, activeTags])

  const toggleTag = (tag) => {
    setActiveTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-violet-200 dark:border-violet-900">
        <input
          type="text"
          placeholder="Search ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full px-2 py-1 text-sm rounded border border-violet-300 dark:border-violet-700 bg-white dark:bg-gray-800 text-violet"
        />
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {allTags.map(tag => (
              <span
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`chip chip-violet cursor-pointer ${
                  activeTags.includes(tag) ? 'bg-violet-200 dark:bg-violet-800' : ''
                }`}
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto" style={{ overscrollBehavior: 'contain' }}>
        {filtered.map(source => {
          const isSelected = source.id === selectedId
          const z = source.z_spec ?? source.z_phot ?? '—'
          return (
            <div
              key={source.id}
              onClick={() => onSelect(source.id)}
              className={`flex items-center gap-2 px-3 py-2 cursor-pointer border-b border-violet-100 dark:border-violet-900 transition ${
                isSelected
                  ? 'bg-violet-200 dark:bg-violet-900'
                  : 'hover:bg-violet-100 dark:hover:bg-violet-950'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-violet truncate">{source.id}</div>
                <div className="text-xs text-violet/60">z: {z}</div>
              </div>
              <div className="flex gap-1">
                {source.tags?.slice(0, 2).map(t => (
                  <span key={t} className="chip chip-violet text-xs">{t}</span>
                ))}
              </div>
              <div className="flex gap-0.5">
                {[
                  source.has_1d && Object.values(source.has_1d).some(Boolean),
                  source.has_2d && Object.values(source.has_2d).some(Boolean),
                  source.has_pdf && Object.values(source.has_pdf).some(Boolean),
                  source.has_sed,
                  source.has_rgb,
                ].map((has, i) => (
                  <span
                    key={i}
                    className={`w-1.5 h-1.5 rounded-full ${
                      has ? 'bg-violet-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default SourceList
