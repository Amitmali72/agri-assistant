import React, { useState } from 'react'
import { Sprout, Bug, Droplets, ArrowRight, Loader2, Volume2 } from 'lucide-react'
import { api } from '../api'
import { LangCode, QueryResponse } from '../types'

interface Props {
  lang: LangCode
  sessionId: string
}

const CROP_GUIDES = [
  {
    crop: 'Cotton',
    title: { mr: 'कापूस (Cotton)', hi: 'कपास (Cotton)', en: 'Cotton' },
    season: 'Kharif',
    topics: [
      {
        label: { mr: 'पानांवरील पिवळे डाग व लाल्या', hi: 'पत्तों पर पीले धब्बे व लाल्या', en: 'Yellow Leaf Spots & Nutrient Deficiency' },
        query: 'कापसाच्या पानांवर पिवळे डाग पडत आहेत. याचे कारण काय असू शकते?',
      },
      {
        label: { mr: 'मावा, तुडतुडे व बोंडअळी नियंत्रण', hi: 'रस चूसक कीट व सुंडी नियंत्रण', en: 'Sucking Pests & Bollworm IPM' },
        query: 'Cotton sucking pests jassids whitefly neem spray management',
      },
    ],
  },
  {
    crop: 'Wheat',
    title: { mr: 'गहू (Wheat)', hi: 'गेहूं (Wheat)', en: 'Wheat' },
    season: 'Rabi',
    topics: [
      {
        label: { mr: 'पाने पिवळी पडण्याची कारणे', hi: 'गेहूं में पीले पत्ते क्यों होते हैं?', en: 'Why Wheat Leaves Turn Yellow' },
        query: 'गेहूं की फसल में पीले पत्ते क्यों हो रहे हैं?',
      },
      {
        label: { mr: 'पेरणी, खते (NPK) व पाणी वेळापत्रक', hi: 'बुवाई, खाद (NPK) व सिंचाई चक्र', en: 'Sowing, Fertilizer & CRI Irrigation' },
        query: 'गहू लागवड खत व्यवस्थापन आणि सिंचन अवस्था सांगा',
      },
    ],
  },
  {
    crop: 'Rice',
    title: { mr: 'भात / तांदूळ (Paddy)', hi: 'धान / चावल (Paddy)', en: 'Rice / Paddy' },
    season: 'Kharif',
    topics: [
      {
        label: { mr: 'रोपवाटिका, खत व खैरा रोग नियंत्रण', hi: 'नर्सरी, खाद व खैरा रोग प्रबंधन', en: 'Transplanting, NPK & Khaira Disease' },
        query: 'भात लागवड खते आणि झिंक कमतरता खैरा रोग उपाय सांगा',
      },
    ],
  },
  {
    crop: 'Soybean',
    title: { mr: 'सोयाबीन (Soybean)', hi: 'सोयाबीन (Soybean)', en: 'Soybean' },
    season: 'Kharif',
    topics: [
      {
        label: { mr: 'वाण, पेरणी अंतर व लष्करी अळी', hi: 'किस्में, बुवाई दूरी व इल्ली नियंत्रण', en: 'Varieties, Spacing & Armyworm Control' },
        query: 'सोयाबीन वाण पेरणी अंतर आणि अळी नियंत्रण उपाय सांगा',
      },
    ],
  },
]

export const CropAssistance: React.FC<Props> = ({ lang, sessionId }) => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [activeTitle, setActiveTitle] = useState('')

  const runAdvisory = async (crop: string, label: string, query: string) => {
    setLoading(true)
    setActiveTitle(`${crop} — ${label}`)
    try {
      const resp = await api.query({ query, session_id: sessionId, language: lang, crop, return_audio: true })
      setResult(resp)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2.5 rounded-xl bg-agri-100 text-agri-700">
            <Sprout className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {lang === 'mr' ? 'पीक व कीड-रोग मार्गदर्शन' : lang === 'hi' ? 'फसल व कीट-रोग सलाह' : 'Crop & Pest Advisory'}
            </h2>
            <p className="text-sm text-slate-500">
              Verified ICAR, MPKV Rahuri & CICR source-backed crop protection and cultivation guidance
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {CROP_GUIDES.map((g) => (
          <div key={g.crop} className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-agri-800">{g.title[lang]}</h3>
              <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 text-xs font-semibold border border-amber-200">
                {g.season}
              </span>
            </div>
            <div className="space-y-2">
              {g.topics.map((tp, idx) => (
                <button
                  key={idx}
                  onClick={() => runAdvisory(g.crop, tp.label[lang], tp.query)}
                  disabled={loading}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-agri-50 hover:bg-agri-100 text-left text-sm font-medium text-agri-900 border border-agri-200 transition"
                >
                  <span className="flex items-center gap-2">
                    {idx === 0 ? <Bug className="w-4 h-4 text-agri-600" /> : <Droplets className="w-4 h-4 text-agri-600" />}
                    {tp.label[lang]}
                  </span>
                  <ArrowRight className="w-4 h-4 text-agri-600 shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {loading && (
        <div className="bg-white rounded-2xl border border-agri-200 p-8 flex items-center justify-center gap-3 text-agri-700 font-semibold">
          <Loader2 className="w-5 h-5 animate-spin" />
          Fetching verified source recommendation...
        </div>
      )}

      {result && !loading && (
        <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-agri-800 text-lg">{activeTitle}</h3>
            <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-semibold border border-emerald-200">
              {result.decision} · {result.generation_mode}
            </span>
          </div>
          <p className="text-slate-800 whitespace-pre-wrap leading-relaxed">{result.answer}</p>
          {result.audio_base64 && (
            <div className="flex items-center gap-3 p-3 rounded-xl bg-agri-50 border border-agri-200">
              <Volume2 className="w-4 h-4 text-agri-700" />
              <audio controls className="w-full h-9" src={`data:audio/mpeg;base64,${result.audio_base64}`} />
            </div>
          )}
          {result.source_documents.length > 0 && (
            <div className="text-xs text-slate-600 pt-2 border-t border-slate-100">
              Sources: {result.source_documents.map((s) => `${s.publisher || s.filename} (p.${s.page})`).join(' · ')}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
