import React, { useEffect, useState } from 'react'
import { Landmark, ExternalLink, FileCheck2, AlertTriangle } from 'lucide-react'
import { api } from '../api'
import { LangCode, SchemeItem } from '../types'

export const SchemesPanel: React.FC<{ lang: LangCode }> = ({ lang }) => {
  const [schemes, setSchemes] = useState<SchemeItem[]>([])

  useEffect(() => {
    api.schemes().then((res) => setSchemes(res.schemes || [])).catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-agri-100 text-agri-700">
            <Landmark className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {lang === 'mr' ? 'शासकीय कृषी योजना' : lang === 'hi' ? 'सरकारी कृषि योजनाएं' : 'Verified Government Agricultural Schemes'}
            </h2>
            <p className="text-sm text-slate-500">
              Official eligibility, benefits, required documents, and provenance dates
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {schemes.map((s) => (
          <div key={s.id} className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-lg font-bold text-agri-800">
                  {lang === 'mr' ? s.name_mr : lang === 'hi' ? s.name_hi : s.name}
                </h3>
                <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 text-[11px] font-bold border border-emerald-200 shrink-0">
                  {s.publication_date}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-agri-50 border border-agri-200 text-sm text-agri-950">
                <span className="font-bold">Benefit:</span> {s.benefit}
              </div>
              <p className="text-sm text-slate-700">
                <span className="font-bold">Eligibility:</span> {s.eligibility}
              </p>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase mb-1.5 flex items-center gap-1">
                  <FileCheck2 className="w-3.5 h-3.5" /> Required Documents
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {s.documents.map((d) => (
                    <span key={d} className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
              <span>{s.source}</span>
              <a
                href={s.source_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-agri-700 font-semibold hover:underline"
              >
                Official Portal <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        Always verify latest enrollment cut-off dates at your local CSC center or state agriculture portal before applying.
      </div>
    </div>
  )
}
