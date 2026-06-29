import { motion } from 'framer-motion';
import { AlertTriangle, Phone } from 'lucide-react';
import type { ActionGuidance } from '../types';
import { containerVariants, itemVariants, cardVariants } from '../animations';

interface Props {
  guidance: ActionGuidance;
}

export function ActionSteps({ guidance }: Props) {
  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-2xl p-6 mb-5"
      style={{ background: '#111827', border: '1px solid #1F2937' }}
      role="region"
      aria-label="Recommended actions"
    >
      {/* Emergency banner */}
      {guidance.emergency && (
        <motion.div
          className="flex items-center gap-3 rounded-xl px-4 py-3 mb-6 text-sm font-bold"
          style={{
            background: '#EF44441A',
            border: '1px solid #EF444455',
            color: '#EF4444',
          }}
          initial={{ opacity: 0, scale: 0.96, y: -6 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 420, damping: 22 }}
          role="alert"
          aria-live="assertive"
        >
          <AlertTriangle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
          EMERGENCY — Immediate action required. Do not dispense.
        </motion.div>
      )}

      <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: '#6B7280' }}>
        Recommended Actions
      </p>

      <p className="text-sm font-semibold mb-5 leading-relaxed" style={{ color: '#E5E7EB' }}>
        {guidance.summary}
      </p>

      <motion.ol
        className="space-y-3"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {guidance.steps.map((step, i) => (
          <motion.li
            key={i}
            variants={itemVariants}
            className="flex items-start gap-3"
          >
            <span
              className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center
                         text-xs font-bold mt-0.5"
              style={{ background: '#1F2937', color: '#9CA3AF' }}
              aria-hidden="true"
            >
              {i + 1}
            </span>
            <p className="text-sm leading-relaxed" style={{ color: '#D1D5DB' }}>
              {step}
            </p>
          </motion.li>
        ))}
      </motion.ol>

      {guidance.contact_authority && (
        <motion.div
          className="mt-5 flex items-start gap-3 rounded-xl p-4 text-sm leading-relaxed"
          style={{ background: '#0A0F1E', border: '1px solid #1F2937', color: '#9CA3AF' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Phone className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#3B82F6' }} aria-hidden="true" />
          <span>{guidance.contact_authority}</span>
        </motion.div>
      )}
    </motion.div>
  );
}
