'use client'

import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Scale, Keyboard, Command, ArrowRight,
  RotateCcw, Database
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchStats, search as apiSearch } from '@/lib/api'
import type { Stats, SearchResult } from '@/lib/api'
import ResultCard from '@/components/ResultCard'
import UploadZone from '@/components/UploadZone'
import StatsPanel from '@/components/StatsPanel'

const EXAMPLE_QUERIES = [
  'arbitration clauses in vendor agreements',
  'employment contract non-compete period',
  'payment terms for delayed invoices',
  'IP ownership clause startup agreement',
  'termination without cause notice period',
  'NDA confidentiality duration',
  'insurance coverage requirements',
]

function LoadingDots() {
  return (
    <div className="flex items-center gap-1.5 py-1">
      {[0, 1, 2].map(i => (
        <motion.div
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-brand-indigo"
          animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1, 0.8] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  )
}

function EmptyState({ onQuery }: { onQuery: (q: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-16 px-4 text-center"
    >
      <div className="p-4 rounded-2xl bg-brand-indigo/10 border border-brand-indigo/20 mb-5">
        <Scale size={32} className="text-brand-indigo opacity-80" />
      </div>
      <h2 className="text-lg font-semibold text-content-primary mb-2">
        Search your firm's memory
      </h2>
      <p className="text-sm text-content-tertiary mb-8 max-w-xs">
        Semantic search across all your contracts, agreements, and client communications.
      </p>
      <div className="w-full max-w-sm space-y-2">
        <p className="text-xs font-medium text-content-tertiary uppercase tracking-wider mb-3">
          Try asking
        </p>
        {EXAMPLE_QUERIES.map(q => (
          <motion.button
            key={q}
            whileHover={{ x: 4 }}
            transition={{ type: 'spring', stiffness: 400 }}
            onClick={() => onQuery(q)}
            className="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-xl
                       border border-white/[0.07] bg-bg-surface hover:bg-bg-elevated
                       hover:border-brand-indigo/30 transition-colors text-left group"
          >
            <ArrowRight size={13} className="text-content-tertiary group-hover:text-brand-indigo
                                             transition-colors flex-shrink-0" />
            <span className="text-sm text-content-secondary group-hover:text-content-primary
                             transition-colors truncate">
              {q}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<Stats | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)
  const [searchSource, setSearchSource] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const loadStats = useCallback(async () => {
    try {
      const s = await fetchStats()
      setStats(s)
    } catch {
      // backend might not be running
    } finally {
      setStatsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadStats()
    // Focus search on load
    setTimeout(() => inputRef.current?.focus(), 200)
  }, [loadStats])

  // Cmd+K / Ctrl+K shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
        inputRef.current?.select()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const runSearch = useCallback(async (q: string) => {
    if (!q.trim()) return
    setQuery(q)
    setLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const res = await apiSearch(q.trim(), 6)
      setResults(res.results)
      setSearchSource(res.source)
    } catch (err) {
      setError((err as Error).message)
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    runSearch(query)
  }

  const handleClear = () => {
    setQuery('')
    setResults([])
    setHasSearched(false)
    setError(null)
    inputRef.current?.focus()
  }

  return (
    <div className="min-h-screen bg-bg-base bg-gradient-mesh flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] glass sticky top-0 z-20">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-brand-indigo/15 border border-brand-indigo/20">
            <Scale size={18} className="text-brand-indigo" />
          </div>
          <div>
            <span className="text-sm font-bold text-content-primary tracking-tight">Legal Memory</span>
            <span className="hidden sm:inline text-xs text-content-tertiary ml-2">AI-Powered Search</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {stats?.supermemory_available && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium
                           border border-brand-gold/40 bg-brand-gold/10 text-brand-gold">
              <div className="w-1.5 h-1.5 rounded-full bg-brand-gold animate-pulse" />
              Supermemory
            </div>
          )}
          <div className="hidden sm:flex items-center gap-1 px-2 py-1 rounded-md bg-bg-elevated
                          border border-white/[0.08] text-xs text-content-tertiary">
            <Command size={10} />
            <span>K</span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col lg:flex-row gap-0 max-w-[1400px] w-full mx-auto">
        {/* Search column */}
        <div className="flex-1 flex flex-col min-h-0 border-b lg:border-b-0 lg:border-r border-white/[0.06]">
          {/* Search bar */}
          <div className="sticky top-[57px] z-10 glass px-4 lg:px-8 py-4 border-b border-white/[0.06]">
            <form onSubmit={handleSubmit} className="relative">
              <div className="relative flex items-center gap-3 px-4 py-3.5 rounded-xl
                              border border-white/[0.1] bg-bg-surface
                              focus-within:border-brand-indigo/50 focus-within:shadow-glow-indigo
                              transition-all duration-200">
                <Search size={17} className="flex-shrink-0 text-content-tertiary" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Ask anything about your firm's documents…"
                  className="flex-1 bg-transparent text-sm text-content-primary placeholder-content-tertiary
                             outline-none min-w-0"
                />
                {query && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="flex-shrink-0 p-1 rounded-md hover:bg-white/[0.06]
                               text-content-tertiary hover:text-content-primary transition-colors"
                  >
                    <RotateCcw size={13} />
                  </button>
                )}
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg
                             bg-brand-indigo hover:bg-brand-indigo-dim disabled:opacity-40
                             text-white text-xs font-semibold transition-all"
                >
                  {loading ? <LoadingDots /> : 'Search'}
                </button>
              </div>

              {/* Search meta */}
              {hasSearched && !loading && (
                <div className="flex items-center justify-between mt-2 px-1">
                  <span className="text-xs text-content-tertiary">
                    {results.length === 0
                      ? 'No results found'
                      : `${results.length} result${results.length !== 1 ? 's' : ''}`}
                  </span>
                  {searchSource && (
                    <span className="flex items-center gap-1 text-xs text-content-tertiary">
                      <Database size={10} />
                      via {searchSource}
                    </span>
                  )}
                </div>
              )}
            </form>
          </div>

          {/* Results / empty state */}
          <div className="flex-1 overflow-y-auto px-4 lg:px-8 py-6">
            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 px-4 py-3 rounded-xl border border-rose-500/20
                           bg-rose-500/5 text-sm text-rose-400"
              >
                {error}
              </motion.div>
            )}

            {/* Loading skeleton */}
            {loading && (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="rounded-xl border border-white/[0.07] bg-bg-surface p-4">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="shimmer w-7 h-7 rounded-lg" />
                      <div className="space-y-1.5">
                        <div className="shimmer h-3 w-36 rounded" />
                        <div className="shimmer h-2.5 w-20 rounded" />
                      </div>
                      <div className="shimmer ml-auto h-2 w-20 rounded" />
                    </div>
                    <div className="space-y-1.5">
                      <div className="shimmer h-2.5 w-full rounded" />
                      <div className="shimmer h-2.5 w-4/5 rounded" />
                      <div className="shimmer h-2.5 w-3/5 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Results */}
            {!loading && hasSearched && (
              <AnimatePresence mode="wait">
                {results.length > 0 ? (
                  <motion.div
                    key="results"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-3"
                  >
                    {results.map((r, i) => (
                      <ResultCard key={`${r.source_name}-${i}`} result={r} index={i} />
                    ))}
                  </motion.div>
                ) : !error ? (
                  <motion.div
                    key="no-results"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex flex-col items-center py-16 text-center"
                  >
                    <Search size={28} className="text-content-tertiary mb-3 opacity-50" />
                    <p className="text-sm text-content-secondary font-medium mb-1">No results found</p>
                    <p className="text-xs text-content-tertiary">
                      Try a different query or upload more documents
                    </p>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            )}

            {/* Empty state (never searched) */}
            {!hasSearched && !loading && (
              <EmptyState onQuery={q => runSearch(q)} />
            )}
          </div>
        </div>

        {/* Right panel */}
        <div className="w-full lg:w-[340px] flex-shrink-0">
          <div className="sticky top-[57px] h-[calc(100vh-57px)] overflow-y-auto">
            <div className="p-5 space-y-6">
              {/* Upload */}
              <section>
                <h3 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Keyboard size={12} />
                  Upload Documents
                </h3>
                <UploadZone onIngested={loadStats} />
              </section>

              {/* Stats */}
              <section>
                <h3 className="text-xs font-semibold text-content-tertiary uppercase tracking-wider mb-3">
                  Memory Index
                </h3>
                <StatsPanel stats={stats} loading={statsLoading} />
              </section>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
