'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { Upload, FileText, MessageSquare, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useCallback, useState } from 'react'
import { ingestPDF, ingestWhatsApp } from '@/lib/api'

interface UploadItem {
  id: string
  name: string
  type: 'pdf' | 'whatsapp'
  status: 'uploading' | 'success' | 'error'
  message?: string
}

interface Props {
  onIngested: () => void
}

export default function UploadZone({ onIngested }: Props) {
  const [isDragging, setIsDragging] = useState(false)
  const [items, setItems] = useState<UploadItem[]>([])

  const processFile = useCallback(async (file: File) => {
    const isPdf = file.name.toLowerCase().endsWith('.pdf')
    const isTxt = file.name.toLowerCase().endsWith('.txt')
    if (!isPdf && !isTxt) return

    const id = `${Date.now()}-${file.name}`
    const type: 'pdf' | 'whatsapp' = isPdf ? 'pdf' : 'whatsapp'

    setItems(prev => [...prev, { id, name: file.name, type, status: 'uploading' }])

    try {
      const result = isPdf
        ? await ingestPDF(file)
        : await ingestWhatsApp(file)

      const msg = isPdf
        ? `${result.chunks} chunks · ${result.pages ?? 0} pages`
        : `${result.chunks} chunks · ${result.messages ?? 0} messages`

      setItems(prev =>
        prev.map(i => i.id === id ? { ...i, status: 'success', message: msg } : i)
      )
      onIngested()
    } catch (err) {
      setItems(prev =>
        prev.map(i =>
          i.id === id
            ? { ...i, status: 'error', message: (err as Error).message }
            : i
        )
      )
    }
  }, [onIngested])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    Array.from(e.dataTransfer.files).forEach(processFile)
  }, [processFile])

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    Array.from(e.target.files ?? []).forEach(processFile)
    e.target.value = ''
  }

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`relative rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer
          ${isDragging
            ? 'border-brand-indigo bg-brand-indigo/5 shadow-glow-indigo'
            : 'border-white/[0.1] hover:border-brand-indigo/40 hover:bg-bg-elevated'
          }`}
      >
        <label className="flex flex-col items-center gap-3 p-6 cursor-pointer">
          <motion.div
            animate={isDragging ? { scale: 1.1 } : { scale: 1 }}
            transition={{ type: 'spring', stiffness: 400 }}
            className={`p-3 rounded-xl transition-colors ${
              isDragging ? 'bg-brand-indigo/20 text-brand-indigo' : 'bg-white/[0.05] text-content-tertiary'
            }`}
          >
            <Upload size={22} />
          </motion.div>

          <div className="text-center">
            <p className="text-sm font-medium text-content-primary">
              {isDragging ? 'Drop files here' : 'Drop files or click to browse'}
            </p>
            <p className="text-xs text-content-tertiary mt-1">PDF contracts · WhatsApp .txt exports</p>
          </div>

          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-indigo/10
                             border border-brand-indigo/20 text-xs text-brand-indigo font-medium">
              <FileText size={11} /> PDF
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-gold/10
                             border border-brand-gold/20 text-xs text-brand-gold font-medium">
              <MessageSquare size={11} /> WhatsApp .txt
            </span>
          </div>

          <input
            type="file"
            accept=".pdf,.txt"
            multiple
            className="sr-only"
            onChange={handleInput}
          />
        </label>
      </div>

      {/* Upload queue */}
      <AnimatePresence>
        {items.map(item => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-bg-elevated
                            border border-white/[0.06]">
              <div className={`flex-shrink-0 ${
                item.type === 'pdf' ? 'text-brand-indigo' : 'text-brand-gold'
              }`}>
                {item.type === 'pdf' ? <FileText size={15} /> : <MessageSquare size={15} />}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-content-primary truncate">{item.name}</p>
                {item.message && (
                  <p className={`text-xs mt-0.5 ${
                    item.status === 'error' ? 'text-rose-400' : 'text-content-tertiary'
                  }`}>
                    {item.message}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0">
                {item.status === 'uploading' && (
                  <Loader2 size={14} className="animate-spin text-brand-indigo" />
                )}
                {item.status === 'success' && (
                  <CheckCircle size={14} className="text-emerald-400" />
                )}
                {item.status === 'error' && (
                  <XCircle size={14} className="text-rose-400" />
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
