export type LangCode = 'mr' | 'hi' | 'en'

export type NavTab =
  | 'assistant'
  | 'crops'
  | 'mandi'
  | 'weather'
  | 'schemes'
  | 'admin'
  | 'settings'

export interface SourceDocument {
  filename: string
  title?: string
  publisher?: string
  source_url?: string
  publication_date?: string
  approval_status: string
  crop?: string
  region?: string
  page?: number
  chunk_index?: number
  score?: number
  snippet: string
}

export interface QueryResponse {
  conversation_id?: number
  session_id: string
  query: string
  transcript?: string
  stt_confidence?: number
  detected_lang: string
  intent: string
  entities: Record<string, any>
  decision: 'ANSWER' | 'CLARIFY' | 'REFUSE' | 'REFER'
  decision_reason: string
  generation_mode: string
  answer: string
  source_documents: SourceDocument[]
  audio_base64?: string
  audio_url?: string
  confidence?: number
  disclaimer?: string
  processing_time_ms?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  timestamp: string
  response?: QueryResponse
  feedbackSent?: number | null
}

export interface WeatherForecastDay {
  date: string
  temp_max_c?: number
  temp_min_c?: number
  rainfall_mm?: number
  description: string
}

export interface WeatherResponse {
  location: string
  temperature_celsius?: number
  feels_like_celsius?: number
  humidity_percent?: number
  wind_speed_kmh?: number
  rainfall_mm?: number
  description: string
  forecast_summary: string
  forecast_days: WeatherForecastDay[]
  agri_advisory: string
  source: string
  is_live: boolean
  cached: boolean
  retrieved_at: string
}

export interface MandiPrice {
  market: string
  state: string
  district: string
  commodity: string
  variety?: string
  min_price?: number
  max_price?: number
  modal_price?: number
  unit: string
  date?: string
}

export interface MandiResponse {
  commodity: string
  prices: MandiPrice[]
  source: string
  is_live: boolean
  cached: boolean
  data_status: string
  retrieved_at: string
  message: string
}

export interface SchemeItem {
  id: string
  name: string
  name_mr: string
  name_hi: string
  benefit: string
  eligibility: string
  documents: string[]
  source: string
  source_url: string
  publication_date: string
}

export interface HealthResponse {
  status: string
  version: string
  ollama_connected: boolean
  openai_configured: boolean
  whisper_loaded: boolean
  db_connected: boolean
  vector_count: number
  approved_docs_count: number
  message: string
}

export interface SessionPrefs {
  session_id: string
  channel: string
  preferred_language: LangCode
  state: string
  district: string
  consent_given: boolean
  audio_retention_opt_in: boolean
}
