import { motion } from 'framer-motion';
import type { VerificationResponse, RiskConfigMap } from '../types';
import { cardVariants, riskCircleVariants, riskIconVariants } from '../animations';

export const RISK: RiskConfigMap = {
  GREEN: {
    color: '#10B981',
    label: 'VERIFIED SAFE',
    icon: '✓',
    glow: 'rgba(16,185,129,0.15)',
    spring: { stiffness: 280, damping: 26 },
  },
  YELLOW: {
    color: '#F59E0B',
    label: 'UNDER INVESTIGATION',
    icon: '⚠',
    glow: 'rgba(245,158,11,0.15)',
    spring: { stiffness: 420, damping: 22 },
  },
  RED: {
    color: '#EF4444',
    label: 'COUNTERFEIT DETECTED',
    icon: '✕',
    glow: 'rgba(239,68,68,0.15)',
    spring: { stiffness: 620, damping: 18 },
  },
};

interface Props {
  result: VerificationResponse;
}

function Tag({ label }: { label: string }) {
  return (
    <span
      className="text-xs px-3 py-1 rounded-full font-medium"
      style={{ background: '#1F2937', color: '#9CA3AF' }}
    >
      {label}
    </span>
  );
}

export function ResultCard({ result }: Props) {
  const cfg  = RISK[result.risk_level];
  const info = result.extracted_info;

  const tags = [
    info.drug_name,
    info.strength,
    info.batch_number   && `Batch ${info.batch_number}`,
    info.manufacturer,
    info.expiry_date    && `Exp ${info.expiry_date}`,
  ].filter((t): t is string => Boolean(t));

  return (
    <motion.article
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="rounded-2xl overflow-hidden mb-5"
      style={{ border: `1px solid ${cfg.color}45`, background: '#111827' }}
      aria-label={`Risk assessment: ${cfg.label}`}
      role="region"
    >
      {/* Hero area */}
      <div
        className="flex flex-col items-center px-6 pt-14 pb-10"
        style={{
          background: `radial-gradient(ellipse 80% 60% at 50% 0%, ${cfg.glow} 0%, transparent 70%)`,
        }}
      >
        {/* Animated risk circle */}
        <motion.div
          className="relative flex items-center justify-center mb-8"
          style={{ width: 180, height: 180 }}
          aria-hidden="true"
        >
          {/* Expanding ring 1 */}
          <motion.div
            className="absolute rounded-full saferx-ring"
            style={{ width: 180, height: 180, border: `2px solid ${cfg.color}`, opacity: 0.35 }}
          />
          {/* Expanding ring 2 (delayed) */}
          <motion.div
            className="absolute rounded-full saferx-ring-delayed"
            style={{ width: 180, height: 180, border: `2px solid ${cfg.color}`, opacity: 0.18 }}
          />
          {/* Main circle — spring-in with risk-level-specific physics */}
          <motion.div
            className="absolute rounded-full flex items-center justify-center saferx-breathe"
            style={{
              width: 136, height: 136,
              background: `${cfg.color}1A`,
              border: `3px solid ${cfg.color}`,
              boxShadow: `0 0 48px ${cfg.color}28`,
            }}
            variants={riskCircleVariants}
            initial="initial"
            animate={result.risk_level}
          >
            <motion.span
              className="text-5xl font-black leading-none select-none"
              style={{ color: cfg.color }}
              variants={riskIconVariants}
              initial="initial"
              animate="animate"
            >
              {cfg.icon}
            </motion.span>
          </motion.div>
        </motion.div>

        {/* Risk label */}
        <motion.h2
          className="text-2xl sm:text-3xl font-black text-center mb-2"
          style={{ color: cfg.color, letterSpacing: '0.1em' }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, type: 'spring', stiffness: 300, damping: 28 }}
        >
          {cfg.label}
        </motion.h2>

        {/* Score + timing */}
        <motion.p
          className="text-sm mb-6"
          style={{ color: '#6B7280' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Risk score{' '}
          <span className="font-semibold" style={{ color: '#9CA3AF' }}>
            {Math.round(result.risk_assessment.score * 100)}%
          </span>
          {result.processing_time_ms != null && (
            <> · {result.processing_time_ms}ms</>
          )}
        </motion.p>

        {/* Tags */}
        {tags.length > 0 && (
          <motion.div
            className="flex flex-wrap gap-2 justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35 }}
          >
            {tags.map((t) => (
              <Tag key={t} label={t} />
            ))}
          </motion.div>
        )}
      </div>

      {/* Reasoning strip */}
      <div
        className="px-6 py-4 text-sm text-center leading-relaxed"
        style={{ color: '#9CA3AF', borderTop: '1px solid #1F2937' }}
      >
        {result.risk_assessment.reasoning}
      </div>
    </motion.article>
  );
}
