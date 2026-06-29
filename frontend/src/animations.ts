import type { Variants, Transition } from 'framer-motion';

// ── Shared spring presets ────────────────────────────────────────────────────

export const springs = {
  gentle:   { type: 'spring', stiffness: 260, damping: 28 } as Transition,
  standard: { type: 'spring', stiffness: 380, damping: 30 } as Transition,
  snappy:   { type: 'spring', stiffness: 520, damping: 26 } as Transition,
  // Risk-circle springs: each level has distinct physics so the "feel"
  // matches the urgency. RED oscillates before settling — intentional.
  riskGreen:  { type: 'spring', stiffness: 280, damping: 26 } as Transition,
  riskYellow: { type: 'spring', stiffness: 420, damping: 22 } as Transition,
  riskRed:    { type: 'spring', stiffness: 620, damping: 18 } as Transition,
} as const;

// ── Page / container ─────────────────────────────────────────────────────────

export const pageVariants: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.18 } },
  exit:    { opacity: 0, transition: { duration: 0.14 } },
};

// Stagger container — wraps a list of items that should appear sequentially.
export const containerVariants: Variants = {
  hidden:  { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.07, delayChildren: 0.04 },
  },
  exit: { opacity: 0, transition: { duration: 0.12 } },
};

// Generic item that springs up from below.
export const itemVariants: Variants = {
  hidden:  { opacity: 0, y: 14, scale: 0.98 },
  visible: {
    opacity: 1, y: 0, scale: 1,
    transition: springs.standard,
  },
  exit: { opacity: 0, y: -8, transition: { duration: 0.14 } },
};

// ── Loading pipeline steps ────────────────────────────────────────────────────

// Steps slide in from the left one-by-one as the pipeline progresses.
export const stepVariants: Variants = {
  hidden:  { opacity: 0, x: -18, scale: 0.97 },
  visible: {
    opacity: 1, x: 0, scale: 1,
    transition: springs.snappy,
  },
};

// ── Risk circle ───────────────────────────────────────────────────────────────

// Animate to named variant matching the RiskLevel value.
export const riskCircleVariants: Variants = {
  initial: { scale: 0.55, opacity: 0, rotate: -6 },
  GREEN: {
    scale: 1, opacity: 1, rotate: 0,
    transition: springs.riskGreen,
  },
  YELLOW: {
    scale: 1, opacity: 1, rotate: 0,
    transition: springs.riskYellow,
  },
  RED: {
    scale: 1, opacity: 1, rotate: 0,
    transition: springs.riskRed,
  },
};

export const riskIconVariants: Variants = {
  initial: { scale: 0, opacity: 0 },
  animate: {
    scale: 1, opacity: 1,
    transition: { ...springs.snappy, delay: 0.12 },
  },
};

// ── Card entrance ─────────────────────────────────────────────────────────────

export const cardVariants: Variants = {
  hidden:  { opacity: 0, y: 18, scale: 0.97 },
  visible: {
    opacity: 1, y: 0, scale: 1,
    transition: springs.gentle,
  },
  exit: { opacity: 0, y: -12, scale: 0.97, transition: { duration: 0.16 } },
};

// ── Error banner ──────────────────────────────────────────────────────────────

export const errorVariants: Variants = {
  initial: { opacity: 0, y: -14, scale: 0.96 },
  animate: {
    opacity: 1, y: 0, scale: 1,
    transition: springs.snappy,
  },
  exit: { opacity: 0, y: -14, scale: 0.96, transition: { duration: 0.18 } },
};

// ── Hover / tap micro-interactions ────────────────────────────────────────────

export const cardHover = { scale: 1.008, transition: { duration: 0.18 } };
export const buttonHover = { scale: 1.025, transition: { duration: 0.14 } };
export const buttonTap   = { scale: 0.96, y: 1 };
export const subtleTap   = { scale: 0.98 };
