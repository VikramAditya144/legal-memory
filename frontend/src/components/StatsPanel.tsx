'use client'

import { motion } from 'framer-motion'
import { FileText, MessageSquare, Layers, Brain } from 'lucide-react'
import type { Stats } from '@/lib/api'

interface Props {
  stats: Stats | null
  loading: boolean
}

function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`shimmer rounded ${className}`} />
}

export default function StatsPanel({ stats, loading }: Props) {
  const totalDocs = (stats?.pdf_sources.length ?? 0) + (stats?.whatsapp_sources.length ?? 0)

  return (
    <div className="space-y-4">
      {/* Metrics row */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Chunks indexed', value: stats?.total_chunks ?? 0, icon: Layers, color: 'text-brand-indigo' },
          { label: 'Documents', value: totalDocs, icon: FileText, color: 'text-brand-gold' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label}
            className="rounded-xl border border-white/[0.07] bg-bg-surface p-3.5 flex flex-col gap-2">
            <div className={`${color} opacity-70`}><Icon size={16} /></div>
            {loading ? (
              <SkeletonLine className="h-6 w-10" />
            ) : (
              <motion.span
                key={value}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-2xl font-bold text-content-primary tabular-nums"
              >
                {value.toLocaleString()}
              </motion.span>
            )}
            <span className="text-xs text-content-tertiary">{label}</span>
          </div>
        ))}
      </div>

      {/* Supermemory badge */}
      {stats && (
        <div className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-xs font-medium
          ${stats.supermemory_available
            ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400'
            : 'border-white/[0.06] bg-bg-elevated text-content-tertiary'
          }`}>
          <Brain size={13} />
          <span>
            Supermemory {stats.supermemory_available ? 'connected' : 'not configured'}
          </span>
          <div className={`ml-auto w-2 h-2 rounded-full ${
            stats.supermemory_available ? 'bg-emerald-400 animate-pulse' : 'bg-white/20'
          }`} />
        </div>
      )}

      {/* Source lists */}
      {((stats?.pdf_sources.length ?? 0) > 0 || (stats?.whatsapp_sources.length ?? 0) > 0) && (
        <div className="space-y-3">
          {(stats?.pdf_sources.length ?? 0) > 0 && (
            <SourceList
              title={`PDFs (${stats!.pdf_sources.length})`}
              items={stats!.pdf_sources}
              icon={<FileText size={12} />}
              accent="text-brand-indigo"
              dotColor="bg-brand-indigo"
            />
          )}
          {(stats?.whatsapp_sources.length ?? 0) > 0 && (
            <SourceList
              title={`WhatsApp (${stats!.whatsapp_sources.length})`}
              items={stats!.whatsapp_sources}
              icon={<MessageSquare size={12} />}
              accent="text-brand-gold"
              dotColor="bg-brand-gold"
            />
          )}
        </div>
      )}

      {/* Empty state */}
      {!loading && stats?.total_chunks === 0 && (
        <div className="rounded-xl border border-dashed border-white/[0.08] p-5 text-center">
          <p className="text-xs text-content-tertiary leading-relaxed">
            No documents indexed yet.<br />Upload files above to get started.
          </p>
        </div>
      )}
    </div>
  )
}

function SourceList({
  title, items, icon, accent, dotColor,
}: {
  title: string
  items: string[]
  icon: React.ReactNode
  accent: string
  dotColor: string
}) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-bg-surface overflow-hidden">
      <div className={`flex items-center gap-1.5 px-3 py-2 border-b border-white/[0.06] ${accent}`}>
        {icon}
        <span className="text-xs font-semibold">{title}</span>
      </div>
      <div className="divide-y divide-white/[0.04]">
        {items.map(name => (
          <div key={name} className="flex items-center gap-2.5 px-3 py-2">
            <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 opacity-60 ${dotColor}`} />
            <span className="text-xs text-content-secondary truncate">{name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
