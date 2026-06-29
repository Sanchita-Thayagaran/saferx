import { motion } from 'framer-motion';
import { ShieldCheck, Loader2 } from 'lucide-react';
import { buttonHover, buttonTap, subtleTap, cardVariants } from '../animations';

const DEMO_SCENARIOS = [
  { scenario: 'green',  label: '✓  GREEN',  color: '#10B981' },
  { scenario: 'yellow', label: '⚠  YELLOW', color: '#F59E0B' },
  { scenario: 'red',    label: '✕  RED',    color: '#EF4444' },
] as const;

type Scenario = typeof DEMO_SCENARIOS[number]['scenario'];

interface Props {
  input: string;
  setInput: (v: string) => void;
  onVerify: (text: string) => void;
  onDemo: (scenario: Scenario) => void;
  loading: boolean;
}

export function InputSection({ input, setInput, onVerify, onDemo, loading }: Props) {
  return (
    <motion.div
      className="rounded-2xl p-6 mb-5"
      style={{ background: '#111827', border: '1px solid #1F2937' }}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
    >
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={
          'Describe the medicine — name, manufacturer, batch number, any text on the packaging.\n\n' +
          'e.g. Artesunate 50mg, batch BX7741, manufactured by PharmaCorp, expiry 03/2026'
        }
        rows={5}
        disabled={loading}
        aria-label="Medicine description input"
        className="w-full resize-none rounded-xl p-4 text-sm leading-relaxed
                   focus:outline-none focus:ring-2 focus:ring-blue-500
                   disabled:opacity-50 placeholder:leading-relaxed transition-shadow"
        style={{
          background: '#0A0F1E',
          color: '#F9FAFB',
          border: '1px solid #374151',
          caretColor: '#3B82F6',
        }}
      />

      <p className="text-xs mt-2 mb-5" style={{ color: '#6B7280' }}>
        Enter any text visible on the packaging. The more detail, the more accurate the verification.
      </p>

      {/* Demo buttons */}
      <div className="flex flex-wrap items-center gap-2 mb-5">
        <span className="text-xs font-semibold" style={{ color: '#4B5563' }}>
          Try a demo:
        </span>
        {DEMO_SCENARIOS.map(({ scenario, label, color }) => (
          <motion.button
            key={scenario}
            onClick={() => onDemo(scenario)}
            disabled={loading}
            whileHover={loading ? undefined : buttonHover}
            whileTap={loading ? undefined : subtleTap}
            className="text-xs px-3 py-1.5 rounded-lg border font-bold
                       disabled:opacity-40 cursor-pointer"
            style={{ color, borderColor: `${color}55`, background: `${color}12` }}
            aria-label={`Run ${scenario} demo scenario`}
          >
            {label}
          </motion.button>
        ))}
      </div>

      {/* Submit */}
      <motion.button
        onClick={() => onVerify(input)}
        disabled={loading || !input.trim()}
        whileHover={!loading && input.trim() ? buttonHover : undefined}
        whileTap={!loading && input.trim() ? buttonTap : undefined}
        className="w-full py-3.5 rounded-xl font-bold text-sm tracking-wide
                   disabled:opacity-40 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2 cursor-pointer"
        style={{ background: '#3B82F6', color: '#F9FAFB' }}
        aria-label="Verify medicine safety"
        aria-busy={loading}
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            Verifying…
          </>
        ) : (
          <>
            <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            Verify Medicine
          </>
        )}
      </motion.button>
    </motion.div>
  );
}
