import { useState, useEffect, lazy, Suspense } from 'react';
import axios from 'axios';
import { AnimatePresence, motion } from 'framer-motion';

import type { VerificationResponse } from './types';
import { pageVariants } from './animations';

import { Header }          from './components/Header';
import { InputSection }    from './components/InputSection';
import { LoadingPipeline } from './components/LoadingPipeline';
import { ResultCard }      from './components/ResultCard';
import { ActionSteps }     from './components/ActionSteps';
import { ErrorBanner }     from './components/ErrorBanner';

// Lazy-load below-the-fold components — only fetched after results arrive.
const DatabaseMatches = lazy(() =>
  import('./components/DatabaseMatches').then((m) => ({ default: m.DatabaseMatches }))
);
const ReportSection = lazy(() =>
  import('./components/ReportSection').then((m) => ({ default: m.ReportSection }))
);

const API_BASE  = 'http://localhost:8000';
const N_STEPS   = 6;
const STEP_MS   = 400;

type Scenario = 'green' | 'yellow' | 'red';

export default function App() {
  const [input,       setInput]       = useState('');
  const [loading,     setLoading]     = useState(false);
  const [result,      setResult]      = useState<VerificationResponse | null>(null);
  const [error,       setError]       = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(-1);

  // Advance the loading-pipeline step indicator every STEP_MS while loading.
  useEffect(() => {
    if (!loading) {
      setCurrentStep(-1);
      return;
    }
    setCurrentStep(0);
    const id = setInterval(() => {
      setCurrentStep((prev) => (prev < N_STEPS - 1 ? prev + 1 : prev));
    }, STEP_MS);
    return () => clearInterval(id);
  }, [loading]);

  async function runVerification(apiCall: () => Promise<{ data: VerificationResponse }>) {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const { data } = await apiCall();
      setResult(data);
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string } }; message?: string };
      setError(e?.response?.data?.detail ?? e?.message ?? 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  function onVerify(text: string) {
    if (!text.trim()) return;
    runVerification(() =>
      axios.post<VerificationResponse>(`${API_BASE}/verify`, { input_text: text, locale: 'en' })
    );
  }

  function onDemo(scenario: Scenario) {
    setInput('');
    runVerification(() =>
      axios.post<VerificationResponse>(`${API_BASE}/verify/demo?scenario=${scenario}`)
    );
  }

  return (
    <motion.div
      className="min-h-screen"
      style={{ background: '#0A0F1E' }}
      variants={pageVariants}
      initial="initial"
      animate="animate"
    >
      <div className="max-w-2xl mx-auto px-4 pb-4">
        <Header />

        <InputSection
          input={input}
          setInput={setInput}
          onVerify={onVerify}
          onDemo={onDemo}
          loading={loading}
        />

        {/* Error banner — sits above the pipeline/results */}
        <AnimatePresence>
          {error && (
            <ErrorBanner
              key="error"
              message={error}
              onDismiss={() => setError(null)}
            />
          )}
        </AnimatePresence>

        {/* Loading pipeline ↔ Results — mutually exclusive, crossfade */}
        <AnimatePresence mode="wait">
          {loading && (
            <LoadingPipeline key="loading" currentStep={currentStep} />
          )}

          {!loading && result && (
            <motion.div
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              role="region"
              aria-label="Verification results"
              aria-live="polite"
            >
              <ResultCard result={result} />
              <ActionSteps guidance={result.action_guidance} />

              <Suspense fallback={null}>
                <DatabaseMatches matches={result.database_matches} />
                {result.report && <ReportSection report={result.report} />}
              </Suspense>

              {/* Disclaimer */}
              <p
                className="text-xs text-center pb-12 leading-relaxed"
                style={{ color: '#374151' }}
              >
                {result.disclaimer}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
