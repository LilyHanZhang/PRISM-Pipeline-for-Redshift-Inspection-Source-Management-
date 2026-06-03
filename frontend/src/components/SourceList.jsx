import { useState, useMemo, useRef, useEffect, useCallback } from 'react'

function SourceList({ sources, selectedId, onSelect }) {
  const [search, setSearch] = useState('')
  const [activeTags, setActiveTags] = useState([])
  const [isFocused, setIsFocused] = useState(false)
  const listRef = useRef(null)
  const scrollContainerRef = useRef(null)
  const itemRefs = useRef({})

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

  const handleSelectWithFocus = useCallback((id) => {
    onSelect(id)
    setIsFocused(true)
  }, [onSelect])

  const handleKeyDown = useCallback((e) => {
    if (!isFocused) return
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return

    e.preventDefault()
    const currentIndex = filtered.findIndex(s => s.id === selectedId)
    if (currentIndex === -1) {
      if (filtered.length > 0) onSelect(filtered[0].id)
      return
    }

    let newIndex
    if (e.key === 'ArrowUp') {
      newIndex = currentIndex - 1
      if (newIndex < 0) return
    } else {
      newIndex = currentIndex + 1
      if (newIndex >= filtered.length) return
    }

    onSelect(filtered[newIndex].id)
  }, [isFocused, filtered, selectedId, onSelect])

  useEffect(() => {
    const el = listRef.current
    if (!el) return
    el.addEventListener('keydown', handleKeyDown)
    return () => el.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    if (!selectedId || !scrollContainerRef.current) return
    const item = itemRefs.current[selectedId]
    if (!item) return

    const container = scrollContainerRef.current
    const containerRect = container.getBoundingClientRect()
    const itemRect = item.getBoundingClientRect()

    if (itemRect.bottom > containerRect.bottom) {
      item.scrollIntoView({ block: 'nearest' })
    } else if (itemRect.top < containerRect.top) {
      item.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedId])

  return (
    <div
      ref={listRef}
      tabIndex={0}
      className={`flex flex-col h-full outline-none ${
        isFocused ? 'ring-2 ring-violet-400 ring-inset' : ''
      }`}
      onBlur={() => setIsFocused(false)}
    >
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
            {allTags.map(tag => {
              const isActive = activeTags.includes(tag)
              return (
                <span
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`chip cursor-pointer transition-all duration-150 ${
                    isActive
                      ? 'bg-violet-600 text-white border-violet-600 dark:bg-violet-500 dark:border-violet-500 shadow-sm scale-105'
                      : 'chip-violet hover:bg-violet-100 dark:hover:bg-violet-900 opacity-70'
                  }`}
                >
                  {isActive && (
                    <span className="mr-0.5 text-xs">✓</span>
                  )}
                  {tag}
                </span>
              )
            })}
          </div>
        )}
      </div>

      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto" style={{ overscrollBehavior: 'contain' }}>
        {filtered.map(source => {
          const isSelected = source.id === selectedId
          const z = source.z_spec ?? source.z_phot ?? '—'
          return (
            <div
              key={source.id}
              ref={el => { itemRefs.current[source.id] = el }}
              onClick={() => handleSelectWithFocus(source.id)}
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
