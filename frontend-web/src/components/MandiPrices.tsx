import React, { useState } from 'react'
import { TrendingUp, Search, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'
import { api } from '../api'
import { LangCode, MandiResponse } from '../types'

const COMMODITIES = ['Wheat', 'Onion', 'Cotton', 'Soybean', 'Rice', 'Maize', 'Tomato', 'Potato', 'Gram', 'Tur']
const STATES = ['Maharashtra', 'Madhya Pradesh', 'Uttar Pradesh', 'Punjab', 'Karnataka', 'Gujarat']

export const MandiPrices: React.FC<{ lang: LangCode }> = ({ lang }) => {
  const [commodity, setCommodity] = useState('Onion')
  const [state, setState] = useState('Maharashtra')
  const [market, setMarket] = useState('Pune')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<MandiResponse | null>(null)

  const fetchPrices = async () => {
    setLoading(true)
    try {
      const res = await api.mandi(commodity, market, state)
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-agri-100 text-agri-700">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {lang === 'mr' ? 'मंडी बाजारभाव (Agmarknet / e-NAM)' : lang === 'hi' ? 'मंडी बाज़ार भाव (Agmarknet)' : 'Live APMC Mandi Prices'}
            </h2>
            <p className="text-sm text-slate-500">
              Live commodity pricing directly from Government of India Agmarknet API (never static mock data)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <select
            value={commodity}
            onChange={(e) => setCommodity(e.target.value)}
            className="px-4 py-3 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-agri-500"
          >
            {COMMODITIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>

          <select
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="px-4 py-3 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-agri-500"
          >
            {STATES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <input
            type="text"
            value={market}
            onChange={(e) => setMarket(e.target.value)}
            placeholder="Market / APMC (e.g. Pune, Nashik)"
            className="px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-agri-500"
          />

          <button
            onClick={fetchPrices}
            disabled={loading}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold transition"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Check Prices
          </button>
        </div>
      </div>

      {data && (
        <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {data.is_live && data.prices.length > 0 ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  LIVE DATA · {data.source} {data.cached ? '(Cached <30m)' : ''}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 text-amber-800 text-xs font-bold border border-amber-200">
                  <AlertCircle className="w-3.5 h-3.5" />
                  STATUS: {data.data_status.toUpperCase()}
                </span>
              )}
            </div>
            <span className="text-xs text-slate-500">Retrieved: {data.retrieved_at}</span>
          </div>

          {data.prices.length === 0 ? (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm">
              {data.message}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left border-collapse">
                <thead>
                  <tr className="bg-agri-50 text-agri-900 border-b border-agri-200">
                    <th className="p-3 font-bold">Market</th>
                    <th className="p-3 font-bold">District / State</th>
                    <th className="p-3 font-bold">Min (₹/Q)</th>
                    <th className="p-3 font-bold">Max (₹/Q)</th>
                    <th className="p-3 font-bold">Modal (₹/Q)</th>
                    <th className="p-3 font-bold">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {data.prices.map((p, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="p-3 font-semibold">{p.market}</td>
                      <td className="p-3 text-slate-600">{p.district}, {p.state}</td>
                      <td className="p-3">₹{p.min_price}</td>
                      <td className="p-3">₹{p.max_price}</td>
                      <td className="p-3 font-bold text-agri-700">₹{p.modal_price}</td>
                      <td className="p-3 text-slate-500">{p.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
