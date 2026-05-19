import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData()
    const res = await fetch(`${BACKEND}/ingest/pdf`, { method: 'POST', body: form })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json(
        { detail: text || `Backend returned ${res.status}` },
        { status: res.status },
      )
    }
    return NextResponse.json(await res.json())
  } catch (e) {
    return NextResponse.json({ detail: `Backend unreachable: ${e}` }, { status: 502 })
  }
}
