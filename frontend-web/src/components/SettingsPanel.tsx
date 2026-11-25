import React, { useEffect, useState } from 'react'
import { Settings, ShieldCheck, Save } from 'lucide-react'
import { api } from '../api'
import { LangCode, SessionPrefs } from '../types'

interface Props {
  lang: LangCode
  setLang: (l: LangCode) => void
  sessionId: string
}

export const SettingsPanel: React.FC<Props> = ({ lang, setLang, sessionId }) => {
  const [prefs, setPrefs] = useState<SessionPrefs>({
    session_id: sessionId,
    channel: 'web',
    preferred_language: lang,
    state: 'Maharashtra',
    district: 'Pune',
    consent_given: true,
    audio_retention_opt_in: false,
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.getSession(sessionId).then((res) => setPrefs({ ...res, preferred_language: lang })).catch(() => {})
  }, [sessionId])

  const save = async () => {
    const out = await api.saveSession({ ...prefs, preferred_language: lang })
    setPrefs(out)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-agri-100 text-agri-700">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Preferences, Region & Privacy Consent</h2>
            <p className="text-sm text-slate-500">Aligned with Indian Digital Personal Data Protection (DPDP) principles</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Preferred Language</label>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value as LangCode)}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200"
            >
              <option value="mr">मराठी (Marathi)</option>
              <option value="hi">हिन्दी (Hindi)</option>
              <option value="en">English</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">State</label>
            <input
              value={prefs.state}
              onChange={(e) => setPrefs({ ...prefs, state: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-600 mb-1">Default District / Mandi</label>
            <input
              value={prefs.district}
              onChange={(e) => setPrefs({ ...prefs, district: e.target.value })}
              className="w-full px-3 py-2.5 rounded-xl border border-slate-200"
            />
          </div>
        </div>

        <div className="space-y-3 pt-2 border-t border-slate-100">
          <label className="flex items-start gap-2.5 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={prefs.consent_given}
              onChange={(e) => setPrefs({ ...prefs, consent_given: e.target.checked })}
              className="mt-1 rounded text-agri-600"
            />
            <span>I consent to processing my voice/text agricultural queries to retrieve verified advisories. Minimal session data is collected.</span>
          </label>
          <label className="flex items-start gap-2.5 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={prefs.audio_retention_opt_in}
              onChange={(e) => setPrefs({ ...prefs, audio_retention_opt_in: e.target.checked })}
              className="mt-1 rounded text-agri-600"
            />
            <span>Allow temporary retention of voice recordings (automatically purged after 24 hours by default).</span>
          </label>
        </div>

        <button
          onClick={save}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold text-sm"
        >
          <Save className="w-4 h-4" /> Save Preferences
        </button>

        {saved && (
          <div className="inline-flex items-center gap-1.5 ml-3 text-sm font-semibold text-emerald-700">
            <ShieldCheck className="w-4 h-4" /> Preferences saved!
          </div>
        )}
      </div>
    </div>
  )
}
