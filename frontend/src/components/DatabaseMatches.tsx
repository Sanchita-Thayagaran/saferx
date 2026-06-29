import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import type { DatabaseMatch } from '../types';
import { containerVariants, itemVariants, subtleTap } from '../animations';

const SOURCE_LABELS: Record<string, string> = {
  WHO_GFMD:        'WHO GFMD',
  FDA:             'FDA',
  FDA_ENFORCEMENT: 'FDA Enforcement',
  EMA:             'EMA',
  REGIONAL:        'Regional Authority',
  BATCH_ALERTS:    'Batch Alerts',
};

interface Props {
  matches: DatabaseMatch[];
}

export function DatabaseMatches({ matches }: Props) {
  const [open, setOpen] = useState(false);
  const alertCount = matches.filter((m) => m.matched && m.alert_type).length;

  return (
    <motion.div
      className="mb-5 rounded-2xl overflow-hidden"
      style={{ background: '#111827', border: '1px solid #1F2937' }}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 320, damping: 28, delay: 0.1 }}
    >
      {/* Toggle header */}
      <motion.button
        onClick={() => setOpen((o) => !o)}
        whileTap={subtleTap}
        className="w-full flex items-center justify-between px-6 py-4
                   text-sm font-semibold cursor-pointer"
        style={{ color: '#F9FAFB' }}
        aria-expanded={open}
        aria-controls="db-matches-panel"
      >
        <span className="flex items-center gap-2">
          <Database className="w-4 h-4" style={{ color: '#3B82F6' }} aria-hidden="true" />
          Sources Checked ({matches.length})
          {alertCount > 0 && (
            <motion.span
              className="text-xs px-2 py-0.5 rounded-full font-bold"
              style={{ background: '#EF44441A', color: '#EF4444' }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 500, damping: 20 }}
            >
              {alertCount} alert{alertCount !== 1 ? 's' : ''}
            </motion.span>
          )}
        </span>
        <motion.div
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ type: 'spring', stiffness: 400, damping: 28 }}
        >
          {open
            ? <ChevronUp  className="w-4 h-4" style={{ color: '#6B7280' }} aria-hidden="true" />
            : <ChevronDown className="w-4 h-4" style={{ color: '#6B7280' }} aria-hidden="true" />
          }
        </motion.div>
      </motion.button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id="db-matches-panel"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 340, damping: 30 }}
            style={{ overflow: 'hidden', borderTop: '1px solid #1F2937' }}
          >
            <motion.ul
              className="px-5 pb-5 pt-4 space-y-2.5"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              {matches.map((m, i) => {
                const flagged = m.matched && m.alert_type;
                return (
                  <motion.li
                    key={i}
                    variants={itemVariants}
                    className="flex items-start justify-between gap-3 rounded-xl px-4 py-3 text-sm"
                    style={{
                      background: '#0A0F1E',
                      border: `1px solid ${flagged ? '#EF444430' : '#1F2937'}`,
                    }}
                  >
                    <div className="flex items-start gap-2.5 flex-1 min-w-0">
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0 mt-1.5"
                        style={{ background: flagged ? '#EF4444' : m.matched ? '#10B981' : '#2D3748' }}
                        aria-hidden="true"
                      />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold" style={{ color: '#E5E7EB' }}>
                            {SOURCE_LABELS[m.source] ?? m.source}
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

                    <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
                      <span
                        className="text-xs font-bold"
                        style={{
                          color: flagged ? '#EF4444' : m.matched ? '#10B981' : '#4B5563',
                        }}
                      >
                        {flagged ? 'FLAGGED' : m.matched ? 'MATCHED' : 'CLEAR'}
                      </span>
                      {m.url && (
                        <a
                          href={m.url}
                          target="_blank"
                          rel="noreferrer"
                          aria-label={`View source record from ${SOURCE_LABELS[m.source] ?? m.source}`}
                        >
                          <ExternalLink className="w-3.5 h-3.5" style={{ color: '#3B82F6' }} aria-hidden="true" />
                        </a>
                      )}
                    </div>
                  </motion.li>
                );
              })}
            </motion.ul>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
