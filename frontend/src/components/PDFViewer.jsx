import { useState } from 'react'
import { getPdfUrl } from '../utils/api'

function PDFViewer({ source, filter, orient }) {
  const [expanded, setExpanded] = useState(true)
  const combo = `${filter}_${orient}`
  const hasPdf = source.has_pdf?.[combo]

  if (!hasPdf) {
    return (
      <div className="panel-red rounded-lg border p-8 text-center">
        <p className="text-red opacity-60">PDF not available for {filter} {orient}</p>
      </div>
    )
  }

  return (
    <div className="panel-red rounded-lg border">
      <div className="flex items-center justify-between p-3">
        <h3 className="font-semibold text-red">PDF Summary — {filter} {orient}</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs px-2 py-1 rounded border border-red-300 dark:border-red-700 text-red hover:bg-red-100 dark:hover:bg-red-900"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
        </div>
      </div>
      {expanded && (
        <div className="border-t border-red-200 dark:border-red-800">
          <iframe
            src={getPdfUrl(source.id, filter, orient)}
            className="w-full h-[600px] border-0"
            title={`PDF for ${source.id} ${filter} ${orient}`}
          />
        </div>
      )}
    </div>
  )
}

export default PDFViewer
