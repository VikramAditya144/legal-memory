const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface SearchResult {
  score: number
  text: string
  source_type: 'pdf' | 'whatsapp' | string
  source_name: string
  start_time?: string
  pages?: string
  senders?: string
}

export interface SearchResponse {
  results: SearchResult[]
  source: string
  query: string
}

export interface Stats {
  total_chunks: number
  pdf_sources: string[]
  whatsapp_sources: string[]
  supermemory_available: boolean
}

export interface IngestResult {
  success: boolean
  filename: string
  chunks: number
  pages?: number
  messages?: number
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`)
  if (!res.ok) throw new Error('Failed to fetch stats')
  return res.json()
}

export async function search(query: string, topK = 5): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || 'Search failed')
  }
  return res.json()
}

export async function ingestPDF(file: File): Promise<IngestResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/ingest/pdf`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || 'PDF ingestion failed')
  }
  return res.json()
}

export async function ingestWhatsApp(file: File): Promise<IngestResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/ingest/whatsapp`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail || 'WhatsApp ingestion failed')
  }
  return res.json()
}
