import {
  HealthResponse,
  LangCode,
  MandiResponse,
  QueryResponse,
  SchemeItem,
  SessionPrefs,
  WeatherResponse,
} from './types'

const BASE = '' // Proxied via Vite in dev, or served same-origin by FastAPI

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `HTTP ${res.status}`
    try {
      const data = await res.json()
      msg = data.detail || data.message || msg
    } catch {
      // ignore
    }
    throw new Error(msg)
  }
  return res.json() as Promise<T>
}

export const api = {
  async health(): Promise<HealthResponse> {
    return handleJson(await fetch(`${BASE}/health`))
  },

  async query(payload: {
    query: string
    session_id: string
    language?: LangCode
    crop?: string
    region?: string
    return_audio?: boolean
  }): Promise<QueryResponse> {
    return handleJson(
      await fetch(`${BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ return_audio: true, ...payload }),
      })
    )
  },

  async voiceQuery(
    audioBlob: Blob,
    filename: string,
    sessionId: string,
    language?: LangCode
  ): Promise<QueryResponse> {
    const form = new FormData()
    form.append('audio_file', audioBlob, filename)
    form.append('session_id', sessionId)
    if (language) form.append('language', language)
    return handleJson(
      await fetch(`${BASE}/voice-query`, {
        method: 'POST',
        body: form,
      })
    )
  },

  async weather(location: string, state: string, language: LangCode): Promise<WeatherResponse> {
    const params = new URLSearchParams({ location, state, language })
    return handleJson(await fetch(`${BASE}/weather?${params}`))
  },

  async mandi(commodity: string, market: string, state: string): Promise<MandiResponse> {
    const params = new URLSearchParams({ commodity, state })
    if (market) params.set('market', market)
    return handleJson(await fetch(`${BASE}/mandi-prices?${params}`))
  },

  async schemes(): Promise<{ schemes: SchemeItem[] }> {
    return handleJson(await fetch(`${BASE}/schemes`))
  },

  async feedback(payload: {
    conversation_id?: number
    session_id: string
    rating: number
    comment?: string
  }) {
    return handleJson(
      await fetch(`${BASE}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    )
  },

  async getSession(sessionId: string): Promise<SessionPrefs> {
    return handleJson(await fetch(`${BASE}/settings/session/${encodeURIComponent(sessionId)}`))
  },

  async saveSession(prefs: SessionPrefs): Promise<SessionPrefs> {
    return handleJson(
      await fetch(`${BASE}/settings/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      })
    )
  },

  async uploadDocument(formData: FormData): Promise<{ message: string }> {
    return handleJson<{ message: string }>(
      await fetch(`${BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
      })
    )
  },

  async adminDocuments(adminKey: string) {
    return handleJson<{ documents: any[] }>(
      await fetch(`${BASE}/admin/documents`, {
        headers: { 'X-Admin-Key': adminKey },
      })
    )
  },

  async adminReviewDocument(docId: number, status: string, adminKey: string) {
    return handleJson(
      await fetch(`${BASE}/admin/documents/${docId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
        body: JSON.stringify({ approval_status: status, reviewed_by: 'admin_console' }),
      })
    )
  },

  async adminDeleteDocument(docId: number, adminKey: string) {
    return handleJson(
      await fetch(`${BASE}/admin/documents/${docId}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Key': adminKey },
      })
    )
  },

  async adminReviewQueue(adminKey: string) {
    return handleJson<{ items: any[] }>(
      await fetch(`${BASE}/admin/review-queue`, {
        headers: { 'X-Admin-Key': adminKey },
      })
    )
  },

  async adminResolveReview(itemId: number, notes: string, adminKey: string) {
    return handleJson(
      await fetch(`${BASE}/admin/review-queue/${itemId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
        body: JSON.stringify({ reviewer_notes: notes }),
      })
    )
  },

  async adminMetrics(adminKey: string) {
    return handleJson<any>(
      await fetch(`${BASE}/admin/metrics`, {
        headers: { 'X-Admin-Key': adminKey },
      })
    )
  },

  async glossary() {
    return handleJson<{ terms: any[] }>(await fetch(`${BASE}/admin/glossary`))
  },

  async addGlossary(
    term: { term_en: string; term_mr: string; term_hi: string; category: string; notes: string },
    adminKey: string
  ) {
    return handleJson(
      await fetch(`${BASE}/admin/glossary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Key': adminKey },
        body: JSON.stringify(term),
      })
    )
  },

  async whatsappMock(payload: {
    sender_phone: string
    message_type: 'text'
    text_content: string
    language: LangCode
  }) {
    return handleJson<any>(
      await fetch(`${BASE}/whatsapp/test-mock`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    )
  },
}
