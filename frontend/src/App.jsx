import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Shield, ShieldCheck, CheckCircle2, AlertTriangle,
  XCircle, Phone, Download, ChevronDown, ChevronUp,
  Loader2, ExternalLink, Database,
} from 'lucide-react'
import './index.css'

// ── Constants ─────────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:8000'

const RISK = {
  GREEN: {
    color: '#10B981',
    label: 'VERIFIED SAFE',
    icon: '✓',
    glow: 'rgba(16,185,129,0.18)',
  },
  YELLOW: {
    color: '#F59E0B',
    label: 'UNDER INVESTIGATION',
    icon: '⚠',
    glow: 'rgba(245,158,11,0.18)',
  },
  RED: {
    color: '#EF4444',
    label: 'COUNTERFEIT DETECTED',
    icon: '✕',
    glow: 'rgba(239,68,68,0.18)',
  },
}

const LOADING_STEPS = [
  { label: 'Reading medicine info...',   icon: ShieldCheck },
  { label: 'Checking WHO database...',   icon: Database },
  { label: 'Analyzing anomalies...',     icon: AlertTriangle },
  { label: 'Calculating risk score...',  icon: ShieldCheck },
  { label: 'Preparing guidance...',      icon: CheckCircle2 },
  { label: 'Generating report...',       icon: Download },
]

const SOURCE_LABELS = {
  WHO_GFMD:     'WHO GFMD',
  FDA:          'FDA',
  EMA:          'EMA',
  REGIONAL:     'Regional Authority',
  BATCH_ALERTS: 'Batch Alerts',
}

const DEMO_SCENARIOS = [
  { scenario: 'green',  label: '✓  GREEN',  color: '#10B981' },
  { scenario: 'yellow', label: '⚠  YELLOW', color: '#F59E0B' },
  { scenario: 'red',    label: '✕  RED',    color: '#EF4444' },
]

// ── Helpers ───────────────────────────────────────────────────────────────────

function downloadReport(report) {
  const blob = new Blob([report.markdown], { type: 'text/plain;charset=utf-8' })
  const url  = URL.createObjectURL(blob)
  const a    = Object.assign(document.createElement('a'), {
    href: url, download: `SafeRx_Report_${report.report_id}.txt`,
  })
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ── Shared primitives ─────────────────────────────────────────────────────────

function Card({ children, style, className = '' }) {
  return (
    <div
      className={`rounded-2xl ${className}`}
      style={{ background: '#111827', border: '1px solid #1F2937', ...style }}
    >
      {children}
    </div>
  )
}

function Tag({ label }) {
  return (
    <span
      className="text-xs px-3 py-1 rounded-full font-medium"
      style={{ background: '#1F2937', color: '#9CA3AF' }}
    >
      {label}
    </span>
  )
}

function SectionLabel({ children }) {
  return (
    <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#6B7280' }}>
      {children}
    </p>
  )
}

// ── Header ────────────────────────────────────────────────────────────────────

function Header() {
  return (
    <header className="text-center pt-10 pb-8">
      {/* Logo */}
      <div className="flex items-center justify-center gap-3 mb-3">
        <div className="relative w-10 h-10">
          <Shield className="w-10 h-10" style={{ color: '#3B82F6' }} strokeWidth={1.5} />
          <span
            className="absolute inset-0 flex items-end justify-center text-[10px] font-black pb-2"
            style={{ color: '#F9FAFB' }}
          >
            Rx
          </span>
        </div>
        <span className="text-3xl font-black tracking-tight" style={{ color: '#F9FAFB' }}>
          Safe<span style={{ color: '#3B82F6' }}>Rx</span>
        </span>
      </div>

      {/* Tagline */}
      <p className="text-base font-medium mb-5" style={{ color: '#9CA3AF' }}>
        Know before you swallow.
      </p>

      {/* DB badges */}
      <div className="flex items-center justify-center flex-wrap gap-2">
        {['WHO GFMD', 'FDA', 'EMA', 'Regional'].map(b => (
          <span
            key={b}
            className="text-xs px-2.5 py-1 rounded-md border font-semibold"
            style={{ color: '#6B7280', borderColor: '#1F2937', background: '#0D1424' }}
          >
            {b}
          </span>
        ))}
      </div>
    </header>
  )
}

// ── InputSection ──────────────────────────────────────────────────────────────

function InputSection({ input, setInput, onVerify, onDemo, loading }) {
  return (
    <Card className="p-6 mb-5">
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder={
          'Describe the medicine — name, manufacturer, batch number, any text on the packaging.\n\n' +
          'e.g. Artesunate 50mg, batch BX7741, manufactured by PharmaCorp, expiry 03/2026'
        }
        rows={5}
        disabled={loading}
        className="w-full resize-none rounded-xl p-4 text-sm leading-relaxed
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   disabled:opacity-50 placeholder:leading-relaxed"
        style={{
          background: '#0A0F1E',
          color: '#F9FAFB',
          border: '1px solid #374151',
          caretColor: '#3B82F6',
        }}
      />

      <p className="text-xs mt-2 mb-5" style={{ color: '#4B5563' }}>
        Enter any text visible on the packaging. The more detail, the more accurate the verification.
      </p>

      {/* Demo buttons */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <span className="text-xs font-semibold" style={{ color: '#4B5563' }}>
          Try a demo:
        </span>
        {DEMO_SCENARIOS.map(({ scenario, label, color }) => (
          <button
            key={scenario}
            onClick={() => onDemo(scenario)}
            disabled={loading}
            className="text-xs px-3 py-1.5 rounded-lg border font-bold
                       transition-opacity hover:opacity-80 disabled:opacity-40 cursor-pointer"
            style={{ color, borderColor: `${color}55`, background: `${color}12` }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Submit */}
      <button
        onClick={() => onVerify(input)}
        disabled={loading || !input.trim()}
        className="w-full py-3.5 rounded-xl font-bold text-sm tracking-wide
                   transition-opacity hover:opacity-90
                   disabled:opacity-40 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2 cursor-pointer"
        style={{ background: '#3B82F6', color: '#F9FAFB' }}
      >
        {loading ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Verifying…</>
        ) : (
          <><ShieldCheck className="w-4 h-4" /> Verify Medicine</>
        )}
      </button>
    </Card>
  )
}

// ── LoadingState ──────────────────────────────────────────────────────────────

function LoadingState({ currentStep }) {
  return (
    <motion.div
      key="loading"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="p-7 mb-5">
        <div className="flex items-center gap-3 mb-6">
          <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" style={{ color: '#3B82F6' }} />
          <span className="font-semibold text-sm" style={{ color: '#F9FAFB' }}>
            Verifying medicine safety across global databases…
          </span>
        </div>

        <div className="space-y-3.5">
          {LOADING_STEPS.map(({ label, icon: Icon }, i) => {
            const done   = i < currentStep
            const active = i === currentStep
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -14 }}
                animate={{ opacity: active || done ? 1 : 0.28, x: 0 }}
                transition={{ delay: i * 0.06, duration: 0.25 }}
                className="flex items-center gap-3"
              >
                {done ? (
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" style={{ color: '#10B981' }} />
                ) : active ? (
                  <Loader2 className="w-5 h-5 flex-shrink-0 animate-spin" style={{ color: '#3B82F6' }} />
                ) : (
                  <div
                    className="w-5 h-5 flex-shrink-0 rounded-full border-2"
                    style={{ borderColor: '#2D3748' }}
                  />
                )}
                <span
                  className="text-sm"
                  style={{ color: done ? '#10B981' : active ? '#F9FAFB' : '#4B5563' }}
                >
                  {label}
                </span>
              </motion.div>
            )
          })}
        </div>
      </Card>
    </motion.div>
  )
}

// ── ResultCard (signature element) ────────────────────────────────────────────

function ResultCard({ result }) {
  const cfg  = RISK[result.risk_level]
  const info = result.extracted_info

  const tags = [
    info.drug_name,
    info.strength,
    info.batch_number && `Batch ${info.batch_number}`,
    info.manufacturer,
    info.expiry_date  && `Exp ${info.expiry_date}`,
  ].filter(Boolean)

  return (
    <motion.div
      key="result-card"
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="rounded-2xl overflow-hidden mb-5"
      style={{ border: `1px solid ${cfg.color}45`, background: '#111827' }}
    >
      {/* Hero area with radial glow */}
      <div
        className="flex flex-col items-center px-6 pt-14 pb-10"
        style={{
          background: `radial-gradient(ellipse 75% 55% at 50% 0%, ${cfg.glow} 0%, transparent 72%)`,
        }}
      >
        {/* Pulsing circle assembly — THE signature element */}
        <div className="relative flex items-center justify-center mb-8" style={{ width: 180, height: 180 }}>
          {/* Expanding ring 1 */}
          <div
            className="absolute saferx-ring rounded-full"
            style={{
              width: 180, height: 180,
              border: `2px solid ${cfg.color}`,
              opacity: 0.4,
            }}
          />
          {/* Expanding ring 2 (delayed) */}
          <div
            className="absolute saferx-ring-delayed rounded-full"
            style={{
              width: 180, height: 180,
              border: `2px solid ${cfg.color}`,
              opacity: 0.22,
            }}
          />
          {/* Main solid circle */}
          <div
            className="absolute saferx-breathe rounded-full flex items-center justify-center"
            style={{
              width: 136, height: 136,
              background: `${cfg.color}1A`,
              border: `3px solid ${cfg.color}`,
              boxShadow: `0 0 40px ${cfg.color}30`,
            }}
          >
            <span
              className="text-5xl font-black leading-none select-none"
              style={{ color: cfg.color }}
            >
              {cfg.icon}
            </span>
          </div>
        </div>

        {/* Risk label */}
        <h2
          className="text-2xl sm:text-3xl font-black text-center mb-2"
          style={{ color: cfg.color, letterSpacing: '0.12em' }}
        >
          {cfg.label}
        </h2>

        {/* Score + timing */}
        <p className="text-sm mb-6" style={{ color: '#6B7280' }}>
          Risk score&nbsp;
          <span className="font-semibold" style={{ color: '#9CA3AF' }}>
            {Math.round(result.risk_assessment.score * 100)}%
          </span>
          {result.processing_time_ms != null && (
            <>&nbsp;·&nbsp;{result.processing_time_ms}ms</>
          )}
        </p>

        {/* Medicine info tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-center">
            {tags.map(t => <Tag key={t} label={t} />)}
          </div>
        )}
      </div>

      {/* Reasoning strip */}
      <div
        className="px-6 py-4 text-sm text-center leading-relaxed"
        style={{ color: '#9CA3AF', borderTop: `1px solid #1F2937` }}
      >
        {result.risk_assessment.reasoning}
      </div>
    </motion.div>
  )
}

// ── ActionSteps ───────────────────────────────────────────────────────────────

function ActionSteps({ guidance }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.35 }}
    >
      <Card className="p-6 mb-5">
        {/* Emergency banner */}
        {guidance.emergency && (
          <div
            className="flex items-center gap-3 rounded-xl px-4 py-3 mb-6 text-sm font-bold"
            style={{
              background: '#EF44441A',
              border: '1px solid #EF444455',
              color: '#EF4444',
            }}
          >
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            EMERGENCY — Immediate action required. Do not dispense.
          </div>
        )}

        <SectionLabel>Recommended Actions</SectionLabel>

        {/* Summary sentence */}
        <p className="text-sm font-semibold mb-5 leading-relaxed" style={{ color: '#E5E7EB' }}>
          {guidance.summary}
        </p>

        {/* Steps */}
        <div className="space-y-3">
          {guidance.steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 + i * 0.06, duration: 0.25 }}
              className="flex items-start gap-3"
            >
              <span
                className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center
                           text-xs font-bold mt-0.5"
                style={{ background: '#1F2937', color: '#9CA3AF' }}
              >
                {i + 1}
              </span>
              <p className="text-sm leading-relaxed" style={{ color: '#D1D5DB' }}>
                {step}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Contact authority */}
        {guidance.contact_authority && (
          <div
            className="mt-5 flex items-start gap-3 rounded-xl p-4 text-sm leading-relaxed"
            style={{ background: '#0A0F1E', border: '1px solid #1F2937', color: '#9CA3AF' }}
          >
            <Phone className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#3B82F6' }} />
            <span>{guidance.contact_authority}</span>
          </div>
        )}
      </Card>
    </motion.div>
  )
}

// ── DatabaseMatches ───────────────────────────────────────────────────────────

function DatabaseMatches({ matches }) {
  const [open, setOpen] = useState(false)
  const alertCount = matches.filter(m => m.matched && m.alert_type).length

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25, duration: 0.35 }}
      className="mb-5"
    >
      <Card>
        {/* Toggle header */}
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full flex items-center justify-between px-6 py-4
                     text-sm font-semibold hover:opacity-80 transition-opacity cursor-pointer"
          style={{ color: '#F9FAFB' }}
        >
          <span className="flex items-center gap-2">
            <Database className="w-4 h-4" style={{ color: '#3B82F6' }} />
            Sources Checked ({matches.length})
            {alertCount > 0 && (
              <span
                className="text-xs px-2 py-0.5 rounded-full font-bold"
                style={{ background: '#EF44441A', color: '#EF4444' }}
              >
                {alertCount} alert{alertCount !== 1 ? 's' : ''}
              </span>
            )}
          </span>
          {open
            ? <ChevronUp  className="w-4 h-4" style={{ color: '#6B7280' }} />
            : <ChevronDown className="w-4 h-4" style={{ color: '#6B7280' }} />
          }
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.22 }}
              style={{ overflow: 'hidden' }}
            >
              <div
                className="px-5 pb-5 space-y-2.5"
                style={{ borderTop: '1px solid #1F2937', paddingTop: 16 }}
              >
                {matches.map((m, i) => {
                  const flagged = m.matched && m.alert_type
                  return (
                    <div
                      key={i}
                      className="flex items-start justify-between gap-3
                                 rounded-xl px-4 py-3 text-sm"
                      style={{
                        background: '#0A0F1E',
                        border: `1px solid ${flagged ? '#EF444435' : '#1F2937'}`,
                      }}
                    >
                      {/* Left */}
                      <div className="flex items-start gap-2.5 flex-1 min-w-0">
                        <div
                          className="w-2 h-2 rounded-full flex-shrink-0 mt-1.5"
                          style={{ background: flagged ? '#EF4444' : '#2D3748' }}
                        />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold" style={{ color: '#E5E7EB' }}>
                              {SOURCE_LABELS[m.source] || m.source}
                            </span>
                            {m.alert_type && (
                              <span
                                className="text-xs px-2 py-0.5 rounded font-medium"
                                style={{ background: '#EF44441A', color: '#EF4444' }}
                              >
                                {m.alert_type.replace(/_/g, ' ')}
                              </span>
                            )}
                          </div>
                          {m.summary && (
                            <p className="text-xs mt-1 leading-relaxed" style={{ color: '#6B7280' }}>
                              {m.summary}
                            </p>
                          )}
                          {m.record_id && (
                            <p className="text-xs mt-0.5" style={{ color: '#4B5563' }}>
                              Ref: {m.record_id}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Right */}
                      <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
                        <span
                          className="text-xs font-bold"
                          style={{ color: flagged ? '#EF4444' : m.matched ? '#10B981' : '#4B5563' }}
                        >
                          {flagged ? 'FLAGGED' : m.matched ? 'MATCHED' : 'CLEAR'}
                        </span>
                        {m.url && (
                          <a href={m.url} target="_blank" rel="noreferrer">
                            <ExternalLink className="w-3.5 h-3.5" style={{ color: '#3B82F6' }} />
                          </a>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  )
}

// ── RegulatoryReport ──────────────────────────────────────────────────────────

function ReportSection({ report }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.35, duration: 0.35 }}
    >
      <Card className="px-6 py-5 mb-5">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <SectionLabel>Regulatory Report</SectionLabel>
            <p className="text-xs font-mono" style={{ color: '#4B5563' }}>
              {report.report_id}
            </p>
            <p className="text-xs mt-1.5 leading-relaxed" style={{ color: '#6B7280' }}>
              Full report ready for submission to health authorities.
            </p>
          </div>
          <button
            onClick={() => downloadReport(report)}
            className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5
                       rounded-xl text-sm font-semibold
                       transition-opacity hover:opacity-80 cursor-pointer"
            style={{ background: '#1F2937', color: '#F9FAFB' }}
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        </div>
      </Card>
    </motion.div>
  )
}

// ── Error banner ──────────────────────────────────────────────────────────────

function ErrorBanner({ message, onDismiss }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.25 }}
      className="flex items-start gap-3 rounded-xl px-5 py-4 mb-5 text-sm"
      style={{
        background: '#EF44441A',
        border: '1px solid #EF444440',
        color: '#EF4444',
      }}
    >
      <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <span className="font-bold">Unable to reach SafeRx API.</span>
        {' '}
        <span style={{ color: '#9CA3AF' }}>{message}</span>
        <p className="mt-1" style={{ color: '#6B7280' }}>
          Make sure the backend is running: <code className="text-xs">uvicorn agent.main:app --reload</code>
        </p>
      </div>
      <button
        onClick={onDismiss}
        className="text-xs underline hover:opacity-70 flex-shrink-0 cursor-pointer"
        style={{ color: '#9CA3AF' }}
      >
        Dismiss
      </button>
    </motion.div>
  )
}

// ── Disclaimer ────────────────────────────────────────────────────────────────

function Disclaimer({ text }) {
  return (
    <p className="text-xs text-center pb-12 leading-relaxed" style={{ color: '#374151' }}>
      {text}
    </p>
  )
}

// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  const [input,       setInput]       = useState('')
  const [loading,     setLoading]     = useState(false)
  const [result,      setResult]      = useState(null)
  const [error,       setError]       = useState(null)
  const [currentStep, setCurrentStep] = useState(-1)

  // Animate loading steps with 400ms cadence
  useEffect(() => {
    if (!loading) { setCurrentStep(-1); return }
    setCurrentStep(0)
    const id = setInterval(() => {
      setCurrentStep(prev =>
        prev < LOADING_STEPS.length - 1 ? prev + 1 : prev
      )
    }, 400)
    return () => clearInterval(id)
  }, [loading])

  async function runVerification(apiCall) {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const { data } = await apiCall()
      setResult(data)
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        err?.message ||
        'Unknown error'
      )
    } finally {
      setLoading(false)
    }
  }

  function onVerify(text) {
    if (!text.trim()) return
    runVerification(() =>
      axios.post(`${API_BASE}/verify`, { input_text: text, locale: 'en' })
    )
  }

  function onDemo(scenario) {
    setInput('')
    runVerification(() =>
      axios.post(`${API_BASE}/verify/demo?scenario=${scenario}`)
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#0A0F1E' }}>
      <div className="max-w-2xl mx-auto px-4">
        <Header />

        <InputSection
          input={input}
          setInput={setInput}
          onVerify={onVerify}
          onDemo={onDemo}
          loading={loading}
        />

        {/* Error — shown independently above main content */}
        <AnimatePresence>
          {error && (
            <ErrorBanner
              key="error"
              message={error}
              onDismiss={() => setError(null)}
            />
          )}
        </AnimatePresence>

        {/* Loading / Results — mutually exclusive */}
        <AnimatePresence mode="wait">
          {loading && (
            <LoadingState key="loading" currentStep={currentStep} />
          )}

          {!loading && result && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <ResultCard result={result} />
              <ActionSteps guidance={result.action_guidance} />
              <DatabaseMatches matches={result.database_matches} />
              {result.report && <ReportSection report={result.report} />}
              <Disclaimer text={result.disclaimer} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
