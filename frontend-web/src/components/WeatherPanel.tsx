import React, { useEffect, useState } from 'react'
import { CloudSun, Droplets, Wind, Thermometer, Loader2, CheckCircle2, Sprout } from 'lucide-react'
import { api } from '../api'
import { LangCode, WeatherResponse } from '../types'

export const WeatherPanel: React.FC<{ lang: LangCode }> = ({ lang }) => {
  const [location, setLocation] = useState('Pune')
  const [state, setState] = useState('Maharashtra')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<WeatherResponse | null>(null)

  const fetchWeather = async () => {
    setLoading(true)
    try {
      const res = await api.weather(location, state, lang)
      setData(res)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWeather()
  }, [lang])

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-xl bg-sky-100 text-sky-700">
            <CloudSun className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {lang === 'mr' ? 'थेट हवामान व कृषी सल्ला' : lang === 'hi' ? 'लाइव मौसम व कृषि सलाह' : 'Live Agricultural Weather & Forecast'}
            </h2>
            <p className="text-sm text-slate-500">
              Real-time meteorological data & 3-day outlook via Open-Meteo / OpenWeatherMap
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="District / City (e.g. Pune, Nashik, Nagpur)"
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-agri-500"
          />
          <input
            type="text"
            value={state}
            onChange={(e) => setState(e.target.value)}
            placeholder="State"
            className="sm:w-48 px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-agri-500"
          />
          <button
            onClick={fetchWeather}
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold flex items-center justify-center gap-2 transition"
          >
            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
            Get Live Weather
          </button>
        </div>
      </div>

      {data && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="text-2xl font-bold text-slate-900">{data.location}</h3>
                <p className="text-sm text-slate-500">{data.description}</p>
              </div>
              <div className="text-right">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {data.is_live ? 'LIVE' : 'UNAVAILABLE'} · {data.source} {data.cached ? '(Cached)' : ''}
                </span>
                <div className="text-[11px] text-slate-400 mt-1">{data.retrieved_at}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
                  <Thermometer className="w-4 h-4" /> Temperature
                </div>
                <div className="text-2xl font-extrabold text-amber-950 mt-1">
                  {data.temperature_celsius ?? '--'}°C
                </div>
              </div>
              <div className="p-4 rounded-xl bg-sky-50 border border-sky-200">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-sky-800">
                  <Droplets className="w-4 h-4" /> Humidity
                </div>
                <div className="text-2xl font-extrabold text-sky-950 mt-1">
                  {data.humidity_percent ?? '--'}%
                </div>
              </div>
              <div className="p-4 rounded-xl bg-blue-50 border border-blue-200">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-800">
                  <CloudSun className="w-4 h-4" /> Rainfall
                </div>
                <div className="text-2xl font-extrabold text-blue-950 mt-1">
                  {data.rainfall_mm ?? 0} mm
                </div>
              </div>
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                  <Wind className="w-4 h-4" /> Wind Speed
                </div>
                <div className="text-2xl font-extrabold text-slate-900 mt-1">
                  {data.wind_speed_kmh ?? '--'} km/h
                </div>
              </div>
            </div>

            {data.agri_advisory && (
              <div className="p-4 rounded-xl bg-agri-50 border border-agri-200 flex items-start gap-3">
                <Sprout className="w-5 h-5 text-agri-700 shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-agri-800 uppercase tracking-wider">
                    Agricultural Weather Advisory
                  </div>
                  <p className="text-sm font-medium text-agri-950 mt-0.5">{data.agri_advisory}</p>
                </div>
              </div>
            )}

            {data.forecast_days && data.forecast_days.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
                  3-Day Forecast
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {data.forecast_days.map((d) => (
                    <div key={d.date} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70">
                      <div className="font-bold text-slate-800 text-sm">{d.date}</div>
                      <div className="text-xs text-slate-600 mt-0.5">{d.description}</div>
                      <div className="mt-2 flex items-center justify-between text-xs font-semibold">
                        <span>{d.temp_min_c}°C – {d.temp_max_c}°C</span>
                        <span className="text-sky-700">{d.rainfall_mm} mm rain</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
