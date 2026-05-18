'use client'

import { motion } from 'framer-motion'
import { FileText, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { SearchResult } from '@/lib/api'

interface Props {
  result: SearchResult
  index: number
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color =
    pct >= 75 ? 'from-emerald-500 to-emerald-400' :
    pct >= 50 ? 'from-amber-500 to-amber-400' :
    'from-rose-500 to-rose-400'

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 rounded-full bg-white/[0.06] overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.1 }}
        />
      </div>
      <span
        className={`text-xs font-semibold tabular-nums ${
          pct >= 75 ? 'text-emerald-400' :
          pct >= 50 ? 'text-amber-400' :
          'text-rose-400'
        }`}
      >
        {pct}%
      </span>
    </div>
  )
}

export default function ResultCard({ result, index }: Props) {
  const [expanded, setExpanded] = useState(false)
  const isWhatsApp = result.source_type === 'whatsapp'
  const Icon = isWhatsApp ? MessageSquare : FileText

  const excerpt = result.text.slice(0, 280).replace(/\n/g, ' ').trim()
  const hasMore = result.text.length > 280

  const metaParts: string[] = []
  if (!isWhatsApp && result.pages) metaParts.push(`p. ${result.pages}`)
  if (isWhatsApp && result.start_time) metaParts.push(result.start_time.slice(0, 10))
  if (result.senders) metaParts.push(`👤 ${result.senders}`)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.06, ease: 'easeOut' }}
      className="group relative rounded-xl border border-white/[0.07] bg-bg-surface
                 hover:border-brand-indigo/30 hover:bg-bg-elevated
                 transition-all duration-200 overflow-hidden cursor-pointer"
      onClick={() => hasMore && setExpanded(!expanded)}
    >
      {/* Left accent bar */}
      <div className={`absolute left-0 top-0 bottom-0 w-0.5 rounded-l-xl
        ${isWhatsApp ? 'bg-brand-gold' : 'bg-brand-indigo'}`}
      />

      <div className="p-4 pl-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className={`flex-shrink-0 p-1.5 rounded-lg
              ${isWhatsApp ? 'bg-brand-gold/10 text-brand-gold' : 'bg-brand-indigo/10 text-brand-indigo'}`}>
              <Icon size={14} />
            </div>
            <div className="min-w-0">
              <span className="text-sm font-semibold text-content-primary truncate block">
                {result.source_name}
              </span>
              {metaParts.length > 0 && (
                <span className="text-xs text-content-tertiary">
                  {metaParts.join(' · ')}
                </span>
              )}
            </div>
          </div>
          <ScoreBar score={result.score} />
        </div>

        {/* Text excerpt */}
        <p className="text-sm text-content-secondary leading-relaxed">
          {expanded ? result.text : excerpt}
          {!expanded && hasMore && (
            <span className="text-content-tertiary">…</span>
          )}
        </p>

        {/* Expand toggle */}
        {hasMore && (
          <button
            className="mt-2 flex items-center gap-1 text-xs text-brand-indigo/70
                       hover:text-brand-indigo transition-colors"
            onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
          >
            {expanded ? (
              <><ChevronUp size={12} /> Show less</>
            ) : (
              <><ChevronDown size={12} /> Show full text</>
            )}
          </button>
        )}
      </div>
    </motion.div>
  )
}
