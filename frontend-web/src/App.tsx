import React, { useEffect, useState } from 'react'
import {
  MessageCircle,
  Sprout,
  TrendingUp,
  CloudSun,
  Landmark,
  Shield,
  Settings,
  Wheat,
  PhoneCall,
} from 'lucide-react'
import { api } from './api'
import { UI_COPY } from './i18n'
import { ChatMessage, HealthResponse, LangCode, NavTab } from './types'
import { ChatAssistant } from './components/ChatAssistant'
import { CropAssistance } from './components/CropAssistance'
import { MandiPrices } from './components/MandiPrices'
import { WeatherPanel } from './components/WeatherPanel'
import { SchemesPanel } from './components/SchemesPanel'
import { AdminConsole } from './components/AdminConsole'
import { SettingsPanel } from './components/SettingsPanel'

export default function App() {
  const [lang, setLang] = useState<LangCode>('mr')
  const [tab, setTab] = useState<NavTab>('assistant')
  const [sessionId] = useState(() => `farmer_${Math.random().toString(36).slice(2, 9)}`)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [health, setHealth] = useState<HealthResponse | null>(null)

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
  }, [])

  const t = UI_COPY[lang]

  const navItems: { id: NavTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'assistant', label: t.nav.assistant, icon: MessageCircle },
    { id: 'crops', label: t.nav.crops, icon: Sprout },
    { id: 'mandi', label: t.nav.mandi, icon: TrendingUp },
    { id: 'weather', label: t.nav.weather, icon: CloudSun },
    { id: 'schemes', label: t.nav.schemes, icon: Landmark },
    { id: 'admin', label: t.nav.admin, icon: Shield },
    { id: 'settings', label: t.nav.settings, icon: Settings },
  ]

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#FAF8F1]">
      {/* Sidebar */}
      <aside className="w-full md:w-72 bg-agri-800 text-white flex flex-col justify-between shrink-0 shadow-xl">
        <div className="p-5 space-y-6">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/20 border border-emerald-400/30">
              <Wheat className="w-7 h-7 text-emerald-300" />
            </div>
            <div>
              <div className="font-extrabold text-xl tracking-tight">{t.brand}</div>
              <div className="text-[11px] text-agri-200 leading-tight">{t.tagline}</div>
            </div>
          </div>

          {/* Language Switcher */}
          <div className="grid grid-cols-3 gap-1.5 bg-agri-900/60 p-1 rounded-xl border border-white/10">
            {([
              { code: 'mr', label: 'मराठी' },
              { code: 'hi', label: 'हिन्दी' },
              { code: 'en', label: 'English' },
            ] as { code: LangCode; label: string }[]).map((l) => (
              <button
                key={l.code}
                onClick={() => setLang(l.code)}
                className={`py-1.5 rounded-lg text-xs font-bold transition ${
                  lang === l.code
                    ? 'bg-emerald-500 text-white shadow'
                    : 'text-agri-200 hover:bg-white/10'
                }`}
              >
                {l.label}
              </button>
            ))}
          </div>

          {/* Navigation */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = tab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => setTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
                    active
                      ? 'bg-agri-600 text-white shadow-sm border border-emerald-400/30'
                      : 'text-agri-100 hover:bg-white/10'
                  }`}
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Footer System Status & Kisan Helpline */}
        <div className="p-5 border-t border-white/10 space-y-3 text-xs">
          <div className="p-3 rounded-xl bg-agri-900/60 border border-white/10 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-emerald-300">
              <PhoneCall className="w-3.5 h-3.5" /> Kisan Call Centre
            </div>
            <div className="text-white font-mono text-sm font-bold">1800-180-1551</div>
          </div>

          <div className="flex items-center justify-between text-[11px] text-agri-200">
            <span className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'ok' ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              />
              {health?.status === 'ok' ? 'Backend Online' : 'Connecting...'}
            </span>
            <span>{health?.vector_count ?? 0} vectors</span>
          </div>
          <div className="text-[10px] text-agri-300/80">Sagveek Technologies Pvt. Ltd.</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-4 md:p-8 max-w-6xl w-full mx-auto">
        {tab === 'assistant' && (
          <ChatAssistant
            lang={lang}
            sessionId={sessionId}
            messages={messages}
            setMessages={setMessages}
          />
        )}
        {tab === 'crops' && <CropAssistance lang={lang} sessionId={sessionId} />}
        {tab === 'mandi' && <MandiPrices lang={lang} />}
        {tab === 'weather' && <WeatherPanel lang={lang} />}
        {tab === 'schemes' && <SchemesPanel lang={lang} />}
        {tab === 'admin' && <AdminConsole lang={lang} />}
        {tab === 'settings' && <SettingsPanel lang={lang} setLang={setLang} sessionId={sessionId} />}
      </main>
    </div>
  )
}
