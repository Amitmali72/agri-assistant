import React, { useEffect, useState } from 'react'
import {
  Shield,
  Upload,
  Check,
  X,
  Trash2,
  BookOpen,
  BarChart3,
  MessageSquareWarning,
  Send,
  Lock,
} from 'lucide-react'
import { api } from '../api'
import { LangCode } from '../types'

export const AdminConsole: React.FC<{ lang: LangCode }> = ({ lang }) => {
  const [adminKey, setAdminKey] = useState('krishimitra-admin-2026')
  const [authenticated, setAuthenticated] = useState(false)
  const [subTab, setSubTab] = useState<'docs' | 'review' | 'glossary' | 'metrics'>('docs')
  const [docs, setDocs] = useState<any[]>([])
  const [queue, setQueue] = useState<any[]>([])
  const [glossary, setGlossary] = useState<any[]>([])
  const [metrics, setMetrics] = useState<any>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [errMsg, setErrMsg] = useState<string | null>(null)

  // Upload form
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [publisher, setPublisher] = useState('ICAR / MPKV Rahuri')
  const [sourceUrl, setSourceUrl] = useState('https://icar.org.in')
  const [pubDate, setPubDate] = useState('2026-01')
  const [crop, setCrop] = useState('Cotton')
  const [region, setRegion] = useState('Maharashtra')
  const [approvalStatus, setApprovalStatus] = useState('approved')

  // Glossary form
  const [gEn, setGEn] = useState('')
  const [gMr, setGMr] = useState('')
  const [gHi, setGHi] = useState('')
  const [gCat, setGCat] = useState('crop')

  // WhatsApp Mock
  const [waPhone, setWaPhone] = useState('919876543210')
  const [waText, setWaText] = useState('गहू पेरणीची योग्य वेळ कोणती आहे?')
  const [waResult, setWaResult] = useState<any>(null)

  const loadAdminData = async (key = adminKey) => {
    setErrMsg(null)
    try {
      const [d, q, g, m] = await Promise.all([
        api.adminDocuments(key),
        api.adminReviewQueue(key),
        api.glossary(),
        api.adminMetrics(key),
      ])
      setDocs(d.documents || [])
      setQueue(q.items || [])
      setGlossary(g.terms || [])
      setMetrics(m)
      setAuthenticated(true)
    } catch (e: any) {
      setAuthenticated(false)
      setErrMsg(e.message || 'Admin authentication failed')
    }
  }

  useEffect(() => {
    loadAdminData()
  }, [])

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pdfFile) return
    setStatusMsg(null)
    setErrMsg(null)
    const fd = new FormData()
    fd.append('file', pdfFile)
    fd.append('source_name', publisher)
    fd.append('publisher', publisher)
    fd.append('source_url', sourceUrl)
    fd.append('publication_date', pubDate)
    fd.append('crop', crop)
    fd.append('region', region)
    fd.append('approval_status', approvalStatus)
    try {
      const res = await api.uploadDocument(fd)
      setStatusMsg(res.message)
      setPdfFile(null)
      await loadAdminData()
    } catch (err: any) {
      setErrMsg(err.message)
    }
  }

  if (!authenticated) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-2xl border border-agri-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center gap-2 text-agri-800 font-bold text-lg">
          <Lock className="w-5 h-5" /> Admin & Expert Reviewer Login
        </div>
        <p className="text-xs text-slate-500">
          Default local dev key: <code>krishimitra-admin-2026</code> (configurable via <code>ADMIN_API_KEY</code>)
        </p>
        <input
          type="password"
          value={adminKey}
          onChange={(e) => setAdminKey(e.target.value)}
          className="w-full px-4 py-2.5 rounded-xl border border-slate-200"
        />
        {errMsg && <div className="text-xs text-rose-600">{errMsg}</div>}
        <button
          onClick={() => loadAdminData(adminKey)}
          className="w-full py-2.5 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold"
        >
          Unlock Admin Console
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-agri-100 text-agri-700">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Admin Console & Expert Review Loop</h2>
            <p className="text-xs text-slate-500">Knowledge provenance, approval workflow, failed query review, glossary & metrics</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'docs', label: 'Knowledge Base', icon: Upload },
            { id: 'review', label: `Review Queue (${queue.filter((x) => x.status === 'open').length})`, icon: MessageSquareWarning },
            { id: 'glossary', label: 'Agri Glossary', icon: BookOpen },
            { id: 'metrics', label: 'Metrics & WhatsApp', icon: BarChart3 },
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setSubTab(tab.id as any)}
                className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold border transition ${
                  subTab === tab.id
                    ? 'bg-agri-600 text-white border-agri-600'
                    : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-agri-50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>

      {statusMsg && <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm">{statusMsg}</div>}
      {errMsg && <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">{errMsg}</div>}

      {subTab === 'docs' && (
        <div className="space-y-5">
          <form onSubmit={handleUpload} className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-800">Ingest New Agricultural PDF</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
                className="px-3 py-2 rounded-xl border border-slate-200 text-sm"
                required
              />
              <input value={publisher} onChange={(e) => setPublisher(e.target.value)} placeholder="Publisher / Institution" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="Source URL" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <input value={pubDate} onChange={(e) => setPubDate(e.target.value)} placeholder="Publication Date (YYYY-MM)" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <input value={crop} onChange={(e) => setCrop(e.target.value)} placeholder="Crop(s)" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <select value={approvalStatus} onChange={(e) => setApprovalStatus(e.target.value)} className="px-3 py-2 rounded-xl border border-slate-200 text-sm">
                <option value="approved">Approved (Trusted)</option>
                <option value="pending">Pending Expert Review</option>
              </select>
            </div>
            <button type="submit" className="px-5 py-2.5 rounded-xl bg-agri-600 hover:bg-agri-700 text-white font-bold text-sm">
              Upload & Index PDF
            </button>
          </form>

          <div className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm overflow-x-auto">
            <h3 className="font-bold text-slate-800 mb-3">Managed Documents ({docs.length})</h3>
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-agri-50 text-agri-900 border-b border-agri-200">
                  <th className="p-2.5">Filename</th>
                  <th className="p-2.5">Publisher</th>
                  <th className="p-2.5">Crop / Region</th>
                  <th className="p-2.5">Chunks</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.id} className="border-b border-slate-100">
                    <td className="p-2.5 font-semibold">{d.filename}</td>
                    <td className="p-2.5 text-slate-600">{d.publisher || d.source}</td>
                    <td className="p-2.5">{d.crop || 'All'} · {d.region}</td>
                    <td className="p-2.5">{d.chunks_count}</td>
                    <td className="p-2.5">
                      <span className={`px-2 py-0.5 rounded-full font-bold ${
                        d.approval_status === 'approved'
                          ? 'bg-emerald-100 text-emerald-800'
                          : d.approval_status === 'rejected'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {d.approval_status}
                      </span>
                    </td>
                    <td className="p-2.5 flex items-center gap-1.5">
                      <button
                        onClick={() => api.adminReviewDocument(d.id, 'approved', adminKey).then(() => loadAdminData())}
                        className="p-1.5 rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                        title="Approve"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => api.adminReviewDocument(d.id, 'rejected', adminKey).then(() => loadAdminData())}
                        className="p-1.5 rounded bg-amber-50 text-amber-700 hover:bg-amber-100"
                        title="Reject"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => api.adminDeleteDocument(d.id, adminKey).then(() => loadAdminData())}
                        className="p-1.5 rounded bg-rose-50 text-rose-700 hover:bg-rose-100"
                        title="Delete & Re-index"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {subTab === 'review' && (
        <div className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm space-y-3">
          <h3 className="font-bold text-slate-800">Low-Confidence & Refused Query Queue</h3>
          {queue.length === 0 ? (
            <p className="text-sm text-slate-500">No flagged queries in review queue.</p>
          ) : (
            queue.map((item) => (
              <div key={item.id} className="p-3.5 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="text-sm font-bold text-slate-800">{item.user_query}</div>
                  <div className="text-xs text-slate-500">
                    Decision: <b>{item.decision}</b> · Reason: {item.reason} · Confidence: {item.confidence}
                  </div>
                </div>
                {item.status === 'open' ? (
                  <button
                    onClick={() => api.adminResolveReview(item.id, 'Reviewed by expert', adminKey).then(() => loadAdminData())}
                    className="px-3 py-1.5 rounded-lg bg-agri-600 text-white text-xs font-bold shrink-0"
                  >
                    Mark Resolved
                  </button>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">Resolved</span>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {subTab === 'glossary' && (
        <div className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800">Multilingual Agricultural Glossary ({glossary.length} terms)</h3>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
            <input value={gEn} onChange={(e) => setGEn(e.target.value)} placeholder="English term" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <input value={gMr} onChange={(e) => setGMr(e.target.value)} placeholder="Marathi (मराठी)" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <input value={gHi} onChange={(e) => setGHi(e.target.value)} placeholder="Hindi (हिन्दी)" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <select value={gCat} onChange={(e) => setGCat(e.target.value)} className="px-3 py-2 rounded-xl border border-slate-200 text-sm">
              <option value="crop">Crop</option>
              <option value="pest">Pest</option>
              <option value="disease">Disease</option>
              <option value="chemical">Chemical</option>
              <option value="scheme">Scheme</option>
            </select>
            <button
              onClick={() =>
                api.addGlossary({ term_en: gEn, term_mr: gMr, term_hi: gHi, category: gCat, notes: '' }, adminKey).then(() => {
                  setGEn(''); setGMr(''); setGHi(''); loadAdminData()
                })
              }
              className="px-4 py-2 rounded-xl bg-agri-600 text-white font-bold text-sm"
            >
              Add Term
            </button>
          </div>
          <div className="max-h-72 overflow-y-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="bg-agri-50 border-b border-agri-200">
                  <th className="p-2">Category</th>
                  <th className="p-2">English</th>
                  <th className="p-2">Marathi</th>
                  <th className="p-2">Hindi</th>
                </tr>
              </thead>
              <tbody>
                {glossary.map((g) => (
                  <tr key={g.id} className="border-b border-slate-100">
                    <td className="p-2 font-semibold uppercase text-agri-700">{g.category}</td>
                    <td className="p-2">{g.term_en}</td>
                    <td className="p-2">{g.term_mr}</td>
                    <td className="p-2">{g.term_hi}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {subTab === 'metrics' && metrics && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-agri-200">
              <div className="text-xs text-slate-500">Total Queries</div>
              <div className="text-2xl font-extrabold text-agri-800">{metrics.total_queries}</div>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-agri-200">
              <div className="text-xs text-slate-500">Avg Latency</div>
              <div className="text-2xl font-extrabold text-agri-800">{metrics.avg_latency_ms} ms</div>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-agri-200">
              <div className="text-xs text-slate-500">Indexed Vectors</div>
              <div className="text-2xl font-extrabold text-agri-800">{metrics.vector_count}</div>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-agri-200">
              <div className="text-xs text-slate-500">User Feedback</div>
              <div className="text-2xl font-extrabold text-agri-800">
                👍 {metrics.feedback_summary?.positive || 0} / 👎 {metrics.feedback_summary?.negative || 0}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-agri-200 p-5 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-800">WhatsApp Cloud API Mock Simulator</h3>
            <div className="flex flex-col sm:flex-row gap-2">
              <input value={waPhone} onChange={(e) => setWaPhone(e.target.value)} className="sm:w-44 px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <input value={waText} onChange={(e) => setWaText(e.target.value)} className="flex-1 px-3 py-2 rounded-xl border border-slate-200 text-sm" />
              <button
                onClick={() => api.whatsappMock({ sender_phone: waPhone, message_type: 'text', text_content: waText, language: lang }).then(setWaResult)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 text-white font-bold text-sm"
              >
                <Send className="w-3.5 h-3.5" /> Simulate WhatsApp
              </button>
            </div>
            {waResult && (
              <pre className="p-3 rounded-xl bg-slate-900 text-emerald-200 text-xs overflow-x-auto">
                {JSON.stringify(waResult, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
