import { Shield } from 'lucide-react';
import { motion } from 'framer-motion';
import { containerVariants, itemVariants } from '../animations';

const DB_BADGES = ['WHO GFMD', 'FDA', 'EMA', 'Regional'] as const;

export function Header() {
  return (
    <motion.header
      className="text-center pt-10 pb-8"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Logo */}
      <motion.div
        className="flex items-center justify-center gap-3 mb-3"
        variants={itemVariants}
      >
        <div className="relative w-10 h-10 flex-shrink-0">
          <Shield
            className="w-10 h-10"
            style={{ color: '#3B82F6' }}
            strokeWidth={1.5}
            aria-hidden="true"
          />
          <span
            className="absolute inset-0 flex items-end justify-center text-[10px] font-black pb-2"
            style={{ color: '#F9FAFB' }}
          >
            Rx
          </span>
        </div>
        <span
          className="text-3xl font-black tracking-tight select-none"
          style={{ color: '#F9FAFB' }}
        >
          Safe<span style={{ color: '#3B82F6' }}>Rx</span>
        </span>
      </motion.div>

      {/* Tagline */}
      <motion.p
        className="text-base font-medium mb-5"
        style={{ color: '#9CA3AF' }}
        variants={itemVariants}
      >
        Know before you swallow.
      </motion.p>

      {/* Database badges */}
      <motion.div
        className="flex items-center justify-center flex-wrap gap-2"
        variants={itemVariants}
      >
        {DB_BADGES.map((badge) => (
          <span
            key={badge}
            className="text-xs px-2.5 py-1 rounded-md border font-semibold"
            style={{ color: '#6B7280', borderColor: '#1F2937', background: '#0D1424' }}
          >
            {badge}
          </span>
        ))}
      </motion.div>
    </motion.header>
  );
}
