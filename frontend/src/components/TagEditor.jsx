import { useState, useEffect } from 'react'
import { getTagList, addTag, removeTag } from '../utils/api'

const DEFAULT_VOCAB = [
  'emission', 'continuum', 'galaxy', 'AGN', 'high-vel',
  'to-be-classified', 'star', 'artefact', 'blended',
]

function TagEditor({ source, onTagsUpdate }) {
  const [tags, setTags] = useState(source.tags || [])
  const [showAdd, setShowAdd] = useState(false)
  const [customTag, setCustomTag] = useState('')
  const [vocab, setVocab] = useState(DEFAULT_VOCAB)

  useEffect(() => {
    setTags(source.tags || [])
    setShowAdd(false)
    setCustomTag('')
  }, [source.id])

  const handleAdd = async (tag) => {
    try {
      await addTag(source.id, tag)
      const newTags = [...tags, tag]
      setTags(newTags)
      onTagsUpdate(newTags)
    } catch (e) {
      console.error('Failed to add tag', e)
    }
  }

  const handleRemove = async (tag) => {
    try {
      await removeTag(source.id, tag)
      const newTags = tags.filter(t => t !== tag)
      setTags(newTags)
      onTagsUpdate(newTags)
    } catch (e) {
      console.error('Failed to remove tag', e)
    }
  }

  const handleCustomAdd = () => {
    if (customTag.trim() && !tags.includes(customTag.trim())) {
      handleAdd(customTag.trim())
      setCustomTag('')
    }
    setShowAdd(false)
  }

  return (
    <div className="panel-pink rounded-lg border p-3">
      <h3 className="font-semibold text-pink mb-2">Tags</h3>
      <div className="flex flex-wrap gap-1">
        {tags.map(tag => (
          <span key={tag} className="chip chip-pink">
            {tag}
            <button
              onClick={() => handleRemove(tag)}
              className="ml-1 text-pink/60 hover:text-pink"
            >
              ×
            </button>
          </span>
        ))}
        <button
          onClick={() => setShowAdd(!showAdd)}
          className="text-xs px-2 py-1 rounded border border-pink-300 dark:border-pink-700 text-pink hover:bg-pink-100 dark:hover:bg-pink-900"
        >
          + add
        </button>
      </div>

      {showAdd && (
        <div className="mt-2 p-2 bg-pink-50 dark:bg-pink-950 rounded border border-pink-200 dark:border-pink-800">
          <div className="flex flex-wrap gap-1 mb-2">
            {vocab.filter(v => !tags.includes(v)).map(tag => (
              <button
                key={tag}
                onClick={() => handleAdd(tag)}
                className="text-xs px-2 py-1 rounded border border-pink-200 dark:border-pink-700 text-pink hover:bg-pink-100 dark:hover:bg-pink-900"
              >
                {tag}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            <input
              type="text"
              value={customTag}
              onChange={e => setCustomTag(e.target.value)}
              placeholder="Custom tag..."
              className="flex-1 text-sm px-2 py-1 rounded border border-pink-300 dark:border-pink-700 bg-white dark:bg-gray-800 text-pink"
              onKeyDown={e => e.key === 'Enter' && handleCustomAdd()}
            />
            <button
              onClick={handleCustomAdd}
              className="text-xs px-3 py-1 rounded bg-pink-500 text-white hover:bg-pink-600"
            >
              Add
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default TagEditor
