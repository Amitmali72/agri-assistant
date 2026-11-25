import React, { useRef, useState } from 'react'
import {
  Mic,
  Square,
  Send,
  Upload,
  Volume2,
  FileText,
  ThumbsUp,
  ThumbsDown,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Sparkles,
  ExternalLink,
  Loader2,
  Trash2,
} from 'lucide-react'
import { api } from '../api'
import { UI_COPY } from '../i18n'
import { ChatMessage, LangCode, QueryResponse } from '../types'

interface Props {
  lang: LangCode
  sessionId: string
  messages: ChatMessage[]
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>
}

const DECISION_STYLES: Record<string, { bg: string; label: string; icon: React.ReactNode }> = {
  ANSWER: {
    bg: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    label: 'ANSWER · Grounded',
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
  },
  CLARIFY: {
    bg: 'bg-amber-50 text-amber-800 border-amber-200',
    label: 'CLARIFY · More Details Needed',
    icon: <HelpCircle className="w-3.5 h-3.5" />,
  },
  REFUSE: {
    bg: 'bg-rose-50 text-rose-800 border-rose-200',
    label: 'REFUSE · Safety Gate',
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
  REFER: {
    bg: 'bg-indigo-50 text-indigo-800 border-indigo-200',
    label: 'REFER · Consult KVK / Expert',
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
}

export const ChatAssistant: React.FC<Props> = ({ lang, sessionId, messages, setMessages }) => {
  const t = UI_COPY[lang]
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [recording, setRecording] = useState(false)
  const [recSeconds, setRecSeconds] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const appendTurn = (userText: string, resp: QueryResponse) => {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    setMessages((prev) => [
      ...prev,
      { id: `u_${Date.now()}`, role: 'user', text: userText, timestamp: now },
      {
        id: `a_${Date.now() + 1}`,
        role: 'assistant',
        text: resp.answer,
        timestamp: now,
        response: resp,
        feedbackSent: null,
      },
    ])
  }

  const handleSendText = async (overrideQuery?: string) => {
    const q = (overrideQuery ?? input).trim()
    if (!q || loading) return
    if (!overrideQuery) setInput('')
    setError(null)
    setLoading(true)
    try {
      const resp = await api.query({ query: q, session_id: sessionId, language: lang, return_audio: true })
      appendTurn(q, resp)
    } catch (e: any) {
      setError(e.message || 'Backend connection failed')
    } finally {
      setLoading(false)
    }
  }

  const startRecording = async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
      const mr = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []
      mr.ondataavailable = (ev) => {
        if (ev.data.size > 0) chunksRef.current.push(ev.data)
      }
      mr.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop())
        const blob = new Blob(chunksRef.current, { type: mimeType })
        const ext = mimeType.includes('webm') ? 'webm' : 'ogg'
        await submitVoiceBlob(blob, `mic_recording.${ext}`)
      }
      mediaRecorderRef.current = mr
      mr.start()
      setRecording(true)
      setRecSeconds(0)
      timerRef.current = window.setInterval(() => setRecSeconds((s) => s + 1), 1000)
    } catch {
      setError('Microphone access denied or unavailable. Please allow mic permission or upload an audio file.')
    }
  }

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setRecording(false)
    mediaRecorderRef.current?.stop()
  }

  const submitVoiceBlob = async (blob: Blob, filename: string) => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.voiceQuery(blob, filename, sessionId, lang)
      const label = resp.transcript ? `🎤 "${resp.transcript}"` : `🎤 [${filename}]`
      appendTurn(label, resp)
    } catch (e: any) {
      setError(e.message || 'Voice processing error')
    } finally {
      setLoading(false)
    }
  }

  const handleAudioFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await submitVoiceBlob(file, file.name)
    e.target.value = ''
  }

  const sendFeedback = async (msgId: string, convId: number | undefined, rating: number) => {
    try {
      await api.feedback({ conversation_id: convId, session_id: sessionId, rating })
      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, feedbackSent: rating } : m))
      )
    } catch {
      // silent
    }
  }

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="rounded-2xl bg-gradient-to-br from-agri-700 via-agri-600 to-emerald-700 text-white p-6 md:p-8 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 text-xs font-semibold tracking-wide">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              ICAR · KVK · Open-Meteo · Agmarknet Grounded AI
            </div>
            <h1 className="text-2xl md:text-3xl font-bold leading-snug">{t.heroTitle}</h1>
            <p className="text-agri-100 text-sm md:text-base">{t.heroSubtitle}</p>
          </div>

          {/* Primary Voice Action Controls */}
          <div className="flex flex-col sm:flex-row gap-3 shrink-0">
            <button
              onClick={recording ? stopRecording : startRecording}
              disabled={loading}
              className={`flex items-center justify-center gap-2.5 px-6 py-4 rounded-xl font-bold text-base shadow-lg transition-all ${
                recording
                  ? 'bg-red-600 hover:bg-red-700 text-white pulse-ring'
                  : 'bg-white text-agri-800 hover:bg-agri-50'
              } disabled:opacity-60`}
            >
              {recording ? (
                <>
                  <Square className="w-5 h-5 fill-current" />
                  <span>
                    {t.recordStop} ({recSeconds}s)
                  </span>
                </>
              ) : (
                <>
                  <Mic className="w-5 h-5 text-agri-600" />
                  <span>{t.recordStart}</span>
                </>
              )}
            </button>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading || recording}
              className="flex items-center justify-center gap-2 px-4 py-4 rounded-xl bg-agri-800/70 hover:bg-agri-800 text-white font-semibold text-sm border border-white/20 transition"
            >
              <Upload className="w-4 h-4" />
              <span>{t.uploadAudio}</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".wav,.mp3,.ogg,.m4a,.webm,.flac,audio/*"
              onChange={handleAudioFile}
              className="hidden"
            />
          </div>
        </div>
      </div>

      {/* Text Input Bar */}
      <div className="bg-white rounded-2xl border border-agri-200 shadow-sm p-3 md:p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
            placeholder={t.placeholder}
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-agri-500 text-base"
          />
          <button
            onClick={() => handleSendText()}
            disabled={loading || !input.trim()}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-4 h-4" />}
            <span>{t.sendBtn}</span>
          </button>
        </div>

        {/* Example Scenarios */}
        <div className="mt-3 pt-3 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            {t.examplesTitle}
          </div>
          <div className="flex flex-wrap gap-2">
            {t.examples.map((ex, idx) => (
              <button
                key={idx}
                onClick={() => handleSendText(ex.query)}
                disabled={loading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-agri-50 hover:bg-agri-100 text-agri-800 text-xs font-medium border border-agri-200 transition"
              >
                <span className="px-1.5 py-0.5 rounded bg-white text-[10px] font-bold text-agri-700 border border-agri-200">
                  {ex.tag}
                </span>
                {ex.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Conversation Feed */}
      <div className="space-y-4">
        {messages.length > 0 && (
          <div className="flex justify-end">
            <button
              onClick={() => setMessages([])}
              className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-rose-600 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear Conversation
            </button>
          </div>
        )}

        {messages.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-2xl rounded-2xl rounded-tr-sm bg-agri-600 text-white px-5 py-3.5 shadow-sm">
                  <p className="text-sm md:text-base whitespace-pre-wrap">{msg.text}</p>
                  <div className="text-[11px] text-agri-100 mt-1 text-right">{msg.timestamp}</div>
                </div>
              </div>
            )
          }

          const resp = msg.response
          const badge = resp ? DECISION_STYLES[resp.decision] || DECISION_STYLES.ANSWER : null

          return (
            <div key={msg.id} className="flex justify-start">
              <div className="w-full max-w-3xl rounded-2xl rounded-tl-sm bg-white border border-agri-200 p-5 shadow-sm space-y-4">
                {/* Metadata badges */}
                {resp && (
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {badge && (
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full border font-semibold ${badge.bg}`}>
                        {badge.icon}
                        {badge.label}
                      </span>
                    )}
                    <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">
                      Intent: {resp.intent}
                    </span>
                    <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">
                      Lang: {resp.detected_lang.toUpperCase()}
                    </span>
                    <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
                      Mode: {resp.generation_mode}
                    </span>
                    {resp.processing_time_ms !== undefined && (
                      <span className="text-slate-400 ml-auto">{resp.processing_time_ms} ms</span>
                    )}
                  </div>
                )}

                {/* Speech Transcript Banner */}
                {resp?.transcript && (
                  <div className="p-3 rounded-xl bg-agri-50 border border-agri-200 text-xs text-agri-900">
                    <span className="font-bold">{t.transcriptLabel}:</span> "{resp.transcript}"
                    {resp.stt_confidence !== undefined && (
                      <span className="ml-2 text-agri-700">
                        (Confidence: {(resp.stt_confidence * 100).toFixed(0)}%)
                      </span>
                    )}
                  </div>
                )}

                {/* Answer Body */}
                <div className="text-slate-800 text-base leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </div>

                {/* Audio Playback */}
                {(resp?.audio_base64 || resp?.audio_url) && (
                  <div className="p-3.5 rounded-xl bg-emerald-50/70 border border-emerald-200 flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-emerald-900 shrink-0">
                      <Volume2 className="w-4 h-4 text-emerald-700" />
                      {t.listenAudio}
                    </div>
                    <audio
                      controls
                      className="w-full h-9"
                      src={
                        resp.audio_base64
                          ? `data:audio/mpeg;base64,${resp.audio_base64}`
                          : resp.audio_url
                      }
                    />
                  </div>
                )}

                {/* Verified Source Citations */}
                {resp?.source_documents && resp.source_documents.length > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-slate-600 uppercase tracking-wider">
                      <FileText className="w-3.5 h-3.5 text-agri-600" />
                      {t.sourcesTitle} ({resp.source_documents.length})
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                      {resp.source_documents.slice(0, 4).map((src, i) => (
                        <div
                          key={i}
                          className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1"
                        >
                          <div className="flex items-center justify-between gap-2 font-semibold text-slate-800">
                            <span className="truncate">{src.publisher || src.filename}</span>
                            <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] shrink-0">
                              p.{src.page || 1} · {Math.round((src.score || 0) * 100)}%
                            </span>
                          </div>
                          <div className="text-slate-500 text-[11px] flex items-center justify-between">
                            <span>{src.filename}</span>
                            {src.publication_date && <span>{src.publication_date}</span>}
                          </div>
                          <p className="text-slate-600 line-clamp-2 italic">"{src.snippet}..."</p>
                          {src.source_url && (
                            <a
                              href={src.source_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-agri-700 hover:underline font-medium"
                            >
                              Official Reference <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Disclaimer & Feedback */}
                <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-500">
                  <span className="italic">{resp?.disclaimer}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span>{t.helpfulQuestion}</span>
                    <button
                      onClick={() => sendFeedback(msg.id, resp?.conversation_id, 1)}
                      className={`p-1.5 rounded-lg border transition ${
                        msg.feedbackSent === 1
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'hover:bg-emerald-50 border-slate-200'
                      }`}
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => sendFeedback(msg.id, resp?.conversation_id, -1)}
                      className={`p-1.5 rounded-lg border transition ${
                        msg.feedbackSent === -1
                          ? 'bg-rose-600 text-white border-rose-600'
                          : 'hover:bg-rose-50 border-slate-200'
                      }`}
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
