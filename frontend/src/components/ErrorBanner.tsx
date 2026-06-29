import { motion } from 'framer-motion';
import { XCircle } from 'lucide-react';
import { errorVariants, subtleTap } from '../animations';

interface Props {
  message: string;
  onDismiss: () => void;
}

export function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <motion.div
      variants={errorVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="flex items-start gap-3 rounded-xl px-5 py-4 mb-5 text-sm"
      style={{
        background: '#EF44441A',
        border: '1px solid #EF444440',
        color: '#EF4444',
      }}
      role="alert"
      aria-live="assertive"
    >
      <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1">
        <span className="font-bold">Unable to reach SafeRx API.</span>{' '}
        <span style={{ color: '#9CA3AF' }}>{message}</span>
        <p className="mt-1" style={{ color: '#6B7280' }}>
          Make sure the backend is running:{' '}
          <code className="text-xs">uvicorn agent.main:app --reload</code>
        </p>
      </div>
      <motion.button
        onClick={onDismiss}
        whileTap={subtleTap}
        className="text-xs underline hover:opacity-70 flex-shrink-0 cursor-pointer"
        style={{ color: '#9CA3AF' }}
        aria-label="Dismiss error"
      >
        Dismiss
      </motion.button>
    </motion.div>
  );
}
