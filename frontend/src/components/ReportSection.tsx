import { motion } from 'framer-motion';
import { Download } from 'lucide-react';
import type { RegulatoryReport } from '../types';
import { buttonHover, subtleTap } from '../animations';

function downloadReport(report: RegulatoryReport) {
  const blob = new Blob([report.markdown], { type: 'text/plain;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement('a'), {
    href: url,
    download: `SafeRx_Report_${report.report_id}.txt`,
  });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

interface Props {
  report: RegulatoryReport;
}

export function ReportSection({ report }: Props) {
  return (
    <motion.div
      className="rounded-2xl px-6 py-5 mb-5"
      style={{ background: '#111827', border: '1px solid #1F2937' }}
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 28, delay: 0.15 }}
      role="region"
      aria-label="Regulatory report"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: '#6B7280' }}>
            Regulatory Report
          </p>
          <p className="text-xs font-mono" style={{ color: '#4B5563' }}>
            {report.report_id}
          </p>
          <p className="text-xs mt-1.5 leading-relaxed" style={{ color: '#6B7280' }}>
            Full report ready for submission to health authorities.
          </p>
        </div>
        <motion.button
          onClick={() => downloadReport(report)}
          whileHover={buttonHover}
          whileTap={subtleTap}
          className="flex-shrink-0 flex items-center gap-2 px-4 py-2.5
                     rounded-xl text-sm font-semibold cursor-pointer"
          style={{ background: '#1F2937', color: '#F9FAFB' }}
          aria-label={`Download regulatory report ${report.report_id}`}
        >
          <Download className="w-4 h-4" aria-hidden="true" />
          Download
        </motion.button>
      </div>
    </motion.div>
  );
}
