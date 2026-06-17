/**
 * Shared Chart.js v4 theme configuration.
 * Import applyChartDefaults() once at app entry and all charts inherit it.
 * Individual charts can override per-chart options as needed.
 */
import { Chart, defaults } from 'chart.js';

// ── Design system values mirrored from index.css ─────────────────────────────
export const C = {
  // Brand / accent
  emerald:   '#00d296',
  emeraldA20: 'rgba(0,210,150,0.20)',
  emeraldA05: 'rgba(0,210,150,0.05)',
  ice:       '#5ab4e5',
  iceA20:    'rgba(90,180,229,0.20)',

  // P&L
  green:     '#22c55e',
  greenA20:  'rgba(34,197,94,0.20)',
  red:       '#ef4444',
  redA20:    'rgba(239,68,68,0.20)',

  // Text
  textPrimary:   '#eef2f6',
  textSecondary: '#8a96a4',
  textMuted:     '#424e5a',

  // Backgrounds
  bgSurface: '#0f1216',
  bgRaised:  '#141820',
  bgOverlay: '#1a1f28',

  // Borders
  borderDim:  'rgba(255,255,255,0.06)',
  borderSoft: 'rgba(255,255,255,0.10)',

  // Font stack
  fontMono: "'IBM Plex Mono', monospace",
  fontSans: "'IBM Plex Sans', sans-serif",

  // Portfolio palette (for pie/donut slices)
  palette: [
    '#00d296', '#5ab4e5', '#f59e0b',
    '#a855f7', '#06b6d4', '#ec4899',
    '#84cc16', '#f97316',
  ],
};

// ── Shared tooltip config ────────────────────────────────────────────────────
export const tooltipDefaults = {
  enabled: true,
  backgroundColor: '#1a1f28',
  borderColor: 'rgba(255,255,255,0.12)',
  borderWidth: 1,
  titleColor: C.textPrimary,
  bodyColor: C.textSecondary,
  footerColor: C.textMuted,
  padding: { x: 12, y: 10 },
  cornerRadius: 6,
  displayColors: true,
  boxPadding: 4,
  titleFont: { family: C.fontMono, size: 11, weight: '600' },
  bodyFont:  { family: C.fontSans, size: 12 },
  callbacks: {},
};

// ── Shared scale (axis) config ───────────────────────────────────────────────
export const scaleDefaults = {
  grid: {
    color: C.borderDim,
    tickColor: 'transparent',
    drawBorder: false,
  },
  border: { display: false },
  ticks: {
    color: C.textMuted,
    font: { family: C.fontMono, size: 10 },
    maxRotation: 0,
  },
};

// ── Apply to all Chart.js instances globally ─────────────────────────────────
export function applyChartDefaults() {
  defaults.color            = C.textSecondary;
  defaults.font.family      = C.fontSans;
  defaults.font.size        = 12;
  defaults.borderColor      = C.borderDim;
  defaults.backgroundColor  = C.bgSurface;
  defaults.animation.duration = 400;
  defaults.animation.easing   = 'easeInOutQuart';

  // Legend
  defaults.plugins.legend.labels.color     = C.textSecondary;
  defaults.plugins.legend.labels.font      = { family: C.fontSans, size: 11 };
  defaults.plugins.legend.labels.boxWidth  = 10;
  defaults.plugins.legend.labels.boxHeight = 10;
  defaults.plugins.legend.labels.padding   = 16;
  defaults.plugins.legend.labels.usePointStyle = true;
  defaults.plugins.legend.labels.pointStyle    = 'circle';

  // Tooltip
  Object.assign(defaults.plugins.tooltip, tooltipDefaults);
}

// ── Gradient factory (must be called after chart mounts) ─────────────────────
export function makeGradient(ctx, height, colorTop, colorBottom) {
  const g = ctx.createLinearGradient(0, 0, 0, height);
  g.addColorStop(0,   colorTop);
  g.addColorStop(0.7, colorBottom);
  g.addColorStop(1,   colorBottom);
  return g;
}
