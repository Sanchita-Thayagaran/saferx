import { motion } from 'framer-motion';
import {
  ShieldCheck, Database, AlertTriangle,
  CheckCircle2, Download, Loader2,
} from 'lucide-react';
import { stepVariants, containerVariants } from '../animations';

const STEPS = [
  { label: 'Reading medicine info',          icon: ShieldCheck },
  { label: 'Cross-checking WHO & FDA live',  icon: Database },
  { label: 'Analysing anomalies',            icon: AlertTriangle },
  { label: 'Calculating risk score',         icon: ShieldCheck },
  { label: 'Preparing action guidance',      icon: CheckCircle2 },
  { label: 'Generating regulatory report',   icon: Download },
] as const;

interface Props {
  currentStep: number;
}

export function LoadingPipeline({ currentStep }: Props) {
  return (
    <motion.div
      key="loading"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10, transition: { duration: 0.15 } }}
      transition={{ duration: 0.2 }}
      className="rounded-2xl p-7 mb-5"
      style={{ background: '#111827', border: '1px solid #1F2937' }}
      role="status"
      aria-label="Verifying medicine safety"
      aria-live="polite"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Loader2
          className="w-5 h-5 animate-spin flex-shrink-0"
          style={{ color: '#3B82F6' }}
          aria-hidden="true"
        />
        <span className="font-semibold text-sm" style={{ color: '#F9FAFB' }}>
          Verifying medicine safety across global databases…
        </span>
      </div>

      {/* Steps */}
      <motion.ol
        className="space-y-2.5"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        aria-label="Verification pipeline steps"
      >
        {STEPS.map(({ label, icon: Icon }, i) => {
          const done   = i < currentStep;
          const active = i === currentStep;
          const show   = i <= currentStep;

          return (
            <motion.li
              key={i}
              variants={stepVariants}
              animate={show ? 'visible' : 'hidden'}
              className="relative flex items-center gap-3 rounded-xl px-4 py-3 transition-colors"
              style={{
                background: active ? 'rgba(59,130,246,0.07)' : 'transparent',
                border: active
                  ? '1px solid rgba(59,130,246,0.25)'
                  : '1px solid transparent',
              }}
              aria-current={active ? 'step' : undefined}
            >
              {/* Status icon */}
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {done ? (
                  <motion.div
                    initial={{ scale: 0, rotate: -30 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 20 }}
                  >
                    <CheckCircle2 className="w-5 h-5" style={{ color: '#10B981' }} aria-hidden="true" />
                  </motion.div>
                ) : active ? (
                  <Loader2 className="w-5 h-5 animate-spin" style={{ color: '#3B82F6' }} aria-hidden="true" />
                ) : (
                  <Icon
                    className="w-5 h-5"
                    style={{ color: '#374151' }}
                    aria-hidden="true"
                  />
                )}
              </div>

              {/* Label */}
              <span
                className="text-sm font-medium"
                style={{
                  color: done ? '#10B981' : active ? '#F9FAFB' : '#4B5563',
                }}
              >
                {label}
              </span>

              {/* Active shimmer overlay */}
              {active && (
                <motion.div
                  className="absolute inset-0 rounded-xl pointer-events-none saferx-shimmer"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  aria-hidden="true"
                />
              )}
            </motion.li>
          );
        })}
      </motion.ol>
    </motion.div>
  );
}
