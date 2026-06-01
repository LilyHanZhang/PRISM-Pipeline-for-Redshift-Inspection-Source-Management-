import { useState, useEffect, useCallback } from 'react'
import SourceList from './components/SourceList'
import SpectraPanel from './components/SpectraPanel'
import SEDPanel from './components/SEDPanel'
import ImagePanel from './components/ImagePanel'
import PDFViewer from './components/PDFViewer'
import TagEditor from './components/TagEditor'
import RedshiftBar from './components/RedshiftBar'
import CoordSearch from './components/CoordSearch'
import { getSources } from './utils/api'

const FILTERS = ['F356W', 'F444W']
const ORIENTS = ['R', 'C']
const COMBOS = FILTERS.flatMap(f => ORIENTS.map(o => ({ filter: f, orient: o })))

function App() {
  const [sources, setSources] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [activeCombo, setActiveCombo] = useState({ filter: 'F356W', orient: 'R' })
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('prism-theme') === 'dark'
  })
  const [showCoordSearch, setShowCoordSearch] = useState(false)
  const [tagsDb, setTagsDb] = useState({})

  useEffect(() => {
    getSources().then(res => setSources(res.data)).catch(() => setSources([]))
  }, [])

  useEffect(() => {
    const theme = darkMode ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('prism-theme', theme)
  }, [darkMode])

  const selectedSource = sources.find(s => s.id === selectedId) || null

  const handleSelectSource = useCallback((id) => {
    setSelectedId(id)
  }, [])

  const handleTagsUpdate = useCallback((sourceId, tags) => {
    setSources(prev => prev.map(s =>
      s.id === sourceId ? { ...s, tags } : s
    ))
  }, [])

  const handleZSpecUpdate = useCallback((sourceId, zSpec) => {
    setSources(prev => prev.map(s =>
      s.id === sourceId ? { ...s, z_spec: zSpec } : s
    ))
  }, [])

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <h1 className="text-xl font-bold rainbow-text">PRISM</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCoordSearch(!showCoordSearch)}
            className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            🔍 Coord Search
          </button>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            {darkMode ? '☀ Light' : '🌙 Dark'}
          </button>
        </div>
      </header>

      {showCoordSearch && (
        <div className="border-b border-gray-200 dark:border-gray-800 p-3 bg-gray-50 dark:bg-gray-900">
          <CoordSearch sources={sources} onSelect={handleSelectSource} />
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Source list */}
        <aside className="w-64 border-r border-gray-200 dark:border-gray-800 overflow-y-auto panel-violet">
          <SourceList
            sources={sources}
            selectedId={selectedId}
            onSelect={handleSelectSource}
          />
        </aside>

        {/* Right panels */}
        <main className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50 dark:bg-gray-950">
          {!selectedSource ? (
            <div className="flex items-center justify-center h-64 text-gray-400">
              Select a source from the list to begin
            </div>
          ) : (
            <>
              {/* Filter/Orient tabs */}
              <div className="flex gap-1">
                {COMBOS.map(({ filter, orient }) => {
                  const isActive = activeCombo.filter === filter && activeCombo.orient === orient
                  const has2d = selectedSource.has_2d?.[`${filter}_${orient}`]
                  const accentClass = filter === 'F356W' ? 'panel-blue' : 'panel-cyan'
                  return (
                    <button
                      key={`${filter}_${orient}`}
                      onClick={() => setActiveCombo({ filter, orient })}
                      className={`px-4 py-2 text-sm font-medium rounded-t border-b-0 transition ${
                        isActive
                          ? `${accentClass} border-b-2`
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-500'
                      } ${!has2d ? 'opacity-50' : ''}`}
                      disabled={!has2d}
                    >
                      {filter} {orient}
                    </button>
                  )
                })}
              </div>

              {/* 2D spectrum */}
              <SpectraPanel
                source={selectedSource}
                filter={activeCombo.filter}
                orient={activeCombo.orient}
              />

              {/* 1D spectrum */}
              <SpectraPanel
                source={selectedSource}
                filter={activeCombo.filter}
                orient={activeCombo.orient}
                mode="1d"
              />

              {/* PDF viewer */}
              <PDFViewer
                source={selectedSource}
                filter={activeCombo.filter}
                orient={activeCombo.orient}
              />

              {/* SED + Image panels side by side */}
              <div className="grid grid-cols-2 gap-3">
                <SEDPanel source={selectedSource} />
                <ImagePanel source={selectedSource} />
              </div>

              {/* Tags + Redshift bar */}
              <TagEditor
                source={selectedSource}
                onTagsUpdate={(tags) => handleTagsUpdate(selectedSource.id, tags)}
              />
              <RedshiftBar
                source={selectedSource}
                onZSpecUpdate={(z) => handleZSpecUpdate(selectedSource.id, z)}
              />
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
