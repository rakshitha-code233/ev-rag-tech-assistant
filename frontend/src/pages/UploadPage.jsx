import { useEffect, useRef, useState } from 'react'
import {
  CloudUpload,
  FileText,
  Trash2,
  MoreVertical,
  CheckCircle,
  AlertCircle,
  Loader2,
  Upload,
} from 'lucide-react'
import Sidebar from '../components/layout/Sidebar'
import Header from '../components/layout/Header'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { listManuals, uploadManual, deleteManual } from '../services/manualService'

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

function formatDate(isoString) {
  if (!isoString) return ''
  try {
    return new Date(isoString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch {
    return isoString
  }
}

function ManualContextMenu({ filename, onDelete, onClose }) {
  return (
    <div
      className="absolute right-0 top-full mt-1 w-36 rounded-lg border border-blue-900/30 shadow-lg z-50 overflow-hidden"
      style={{ backgroundColor: '#0d1117' }}
      role="menu"
    >
      <button
        onClick={() => { onDelete(filename); onClose() }}
        className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-red-600/10 transition-colors"
        role="menuitem"
      >
        <Trash2 size={14} />
        Delete
      </button>
    </div>
  )
}

export default function UploadPage() {
  const [manuals, setManuals] = useState([])
  const [uploads, setUploads] = useState([]) // {id, file, status, progress, error}
  const [isDragActive, setIsDragActive] = useState(false)
  const [dropError, setDropError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [openMenuId, setOpenMenuId] = useState(null)
  const fileInputRef = useRef(null)

  // Load existing manuals
  useEffect(() => {
    listManuals()
      .then(setManuals)
      .catch(() => {})
      .finally(() => setIsLoading(false))
  }, [])

  // Close context menu on outside click
  useEffect(() => {
    if (!openMenuId) return
    const handler = () => setOpenMenuId(null)
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [openMenuId])

  const processFiles = (files) => {
    setDropError('')
    const pdfFiles = []
    const rejected = []

    for (const file of files) {
      if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
        pdfFiles.push(file)
      } else {
        rejected.push(file.name)
      }
    }

    if (rejected.length > 0) {
      setDropError('Only PDF files are supported')
    }

    pdfFiles.forEach((file) => {
      const id = `${file.name}-${Date.now()}`
      setUploads((prev) => [...prev, { id, file, status: 'uploading', progress: 0, error: '' }])

      uploadManual(file, (progress) => {
        setUploads((prev) =>
          prev.map((u) => (u.id === id ? { ...u, progress } : u))
        )
      })
        .then((meta) => {
          setUploads((prev) =>
            prev.map((u) => (u.id === id ? { ...u, status: 'done', progress: 100 } : u))
          )
          setManuals((prev) => {
            // Avoid duplicates
            const exists = prev.some((m) => m.filename === meta.filename)
            return exists ? prev : [...prev, meta]
          })
        })
        .catch((err) => {
          const msg = err.message || 'Upload failed. Please try again.'
          setUploads((prev) =>
            prev.map((u) => (u.id === id ? { ...u, status: 'error', error: msg } : u))
          )
        })
    })
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragActive(false)
    processFiles(Array.from(e.dataTransfer.files))
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragActive(true)
  }

  const handleDragLeave = () => setIsDragActive(false)

  const handleFileInput = (e) => {
    if (e.target.files?.length) {
      processFiles(Array.from(e.target.files))
      e.target.value = ''
    }
  }

  const handleDelete = async (filename) => {
    try {
      await deleteManual(filename)
      setManuals((prev) => prev.filter((m) => m.filename !== filename))
    } catch (err) {
      alert(err.message || 'Failed to delete manual')
    }
  }

  return (
    <div className="page-layout">
      <Sidebar />
      <div className="main-content">
        <Header />
        <main className="flex-1 overflow-y-auto px-6 lg:px-10 py-8">
          {/* Page header */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Upload size={16} className="text-purple-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Upload Manuals</h1>
              <p className="text-slate-400 text-sm">Add PDF repair manuals to power your diagnostic assistant</p>
            </div>
          </div>

          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200 mb-6 ${
              isDragActive
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-blue-900/40 hover:border-blue-700/60 hover:bg-blue-500/5'
            }`}
            role="region"
            aria-label="File drop zone"
          >
            <div className="flex flex-col items-center gap-4">
              <div
                className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${
                  isDragActive ? 'bg-blue-500/20' : 'bg-blue-500/10'
                }`}
              >
                <CloudUpload
                  size={28}
                  className={isDragActive ? 'text-blue-300' : 'text-blue-400'}
                />
              </div>
              <div>
                <p className="text-white font-medium mb-1">
                  {isDragActive ? 'Drop your PDF files here' : 'Drag & drop PDF files here'}
                </p>
                <p className="text-slate-400 text-sm">or click the button below to browse</p>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-primary flex items-center gap-2 px-4 py-2 whitespace-nowrap"
              >
                <FileText size={16} />
                Choose PDF Files
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                multiple
                onChange={handleFileInput}
                className="hidden"
                aria-label="Choose PDF files to upload"
              />
            </div>
          </div>

          {/* Drop error */}
          {dropError && (
            <div role="alert" className="flex items-center gap-2 text-red-400 text-sm mb-4">
              <AlertCircle size={14} />
              {dropError}
            </div>
          )}

          {/* Active uploads */}
          {uploads.length > 0 && (
            <div className="mb-6">
              <h2 className="text-white font-medium text-sm mb-3">Uploading</h2>
              <div className="space-y-2">
                {uploads.map((upload) => (
                  <div
                    key={upload.id}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl border border-blue-900/30"
                    style={{ backgroundColor: 'rgba(13, 25, 48, 0.5)' }}
                  >
                    <FileText size={18} className="text-blue-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm truncate">{upload.file.name}</p>
                      {upload.status === 'uploading' && (
                        <div className="mt-1.5 h-1 bg-blue-900/40 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full transition-all duration-300"
                            style={{ width: `${upload.progress}%` }}
                          />
                        </div>
                      )}
                      {upload.status === 'error' && (
                        <p className="text-red-400 text-xs mt-0.5">{upload.error}</p>
                      )}
                    </div>
                    <div className="flex-shrink-0">
                      {upload.status === 'uploading' && (
                        <Loader2 size={16} className="text-blue-400 animate-spin" />
                      )}
                      {upload.status === 'done' && (
                        <CheckCircle size={16} className="text-green-400" />
                      )}
                      {upload.status === 'error' && (
                        <AlertCircle size={16} className="text-red-400" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Uploaded manuals list */}
          <div>
            <h2 className="text-white font-medium text-sm mb-3">
              Uploaded Manuals
              {manuals.length > 0 && (
                <span className="ml-2 text-slate-500 font-normal">({manuals.length})</span>
              )}
            </h2>

            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : manuals.length === 0 ? (
              <div className="text-center py-10 border border-dashed border-blue-900/30 rounded-xl">
                <FileText size={32} className="text-slate-600 mx-auto mb-2" />
                <p className="text-slate-400 text-sm">No manuals uploaded yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {manuals.map((manual) => (
                  <div
                    key={manual.filename}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl border border-blue-900/30 hover:border-blue-700/40 transition-colors"
                    style={{ backgroundColor: 'rgba(13, 25, 48, 0.5)' }}
                  >
                    <div className="w-9 h-9 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0">
                      <FileText size={16} className="text-red-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm font-medium truncate">{manual.filename}</p>
                      <p className="text-slate-500 text-xs mt-0.5">
                        {formatBytes(manual.size)} · {formatDate(manual.uploaded_at)}
                      </p>
                    </div>
                    {/* Three-dot menu */}
                    <div className="relative flex-shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setOpenMenuId(openMenuId === manual.filename ? null : manual.filename)
                        }}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-colors"
                        aria-label={`Options for ${manual.filename}`}
                        aria-haspopup="true"
                        aria-expanded={openMenuId === manual.filename}
                      >
                        <MoreVertical size={16} />
                      </button>
                      {openMenuId === manual.filename && (
                        <ManualContextMenu
                          filename={manual.filename}
                          onDelete={handleDelete}
                          onClose={() => setOpenMenuId(null)}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
