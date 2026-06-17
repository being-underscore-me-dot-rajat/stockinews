/**
 * Education Hub — Bloomberg-grade financial education platform.
 * Three sections: Statistics, Technical Indicators, Options/FnO.
 * Each module has rich content + live chart (where applicable) + AI Tutor.
 */
import React, { useState, useEffect, Suspense } from 'react';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import { Line } from 'react-chartjs-2';
import { API_BASE } from '../lib/api';
import { C, tooltipDefaults, scaleDefaults } from '../lib/chartTheme';
import Navbar from '../home/navbar/Navbar';
import IndicatorChart from './components/IndicatorChart';
import GreekChart from './components/GreekChart';
import TutorPanel from './components/TutorPanel';
import './education.css';
import './components/indicatorChart.css';
import './components/greekChart.css';
import './components/tutorPanel.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, annotationPlugin);

// ── Static nav structure ──────────────────────────────────────────────────────

const NAV = [
  {
    category: 'statistics',
    label: 'Statistics',
    icon: '∑',
    items: [
      { slug: 'mean',              label: 'Mean',              type: 'concept' },
      { slug: 'standard-deviation',label: 'Std Deviation',     type: 'concept' },
      { slug: 'correlation',       label: 'Correlation',       type: 'concept' },
      { slug: 'beta',              label: 'Beta (β)',          type: 'concept' },
      { slug: 'sharpe-ratio',      label: 'Sharpe Ratio',      type: 'concept' },
      { slug: 'volatility',        label: 'Volatility',        type: 'concept' },
    ],
  },
  {
    category: 'indicators',
    label: 'Indicators',
    icon: '⌇',
    items: [
      { slug: 'rsi',           label: 'RSI',              type: 'indicator' },
      { slug: 'macd',          label: 'MACD',             type: 'indicator' },
      { slug: 'bollinger',     label: 'Bollinger Bands',  type: 'indicator' },
      { slug: 'ema-sma',       label: 'EMA & SMA',        type: 'indicator' },
      { slug: 'vwap',          label: 'VWAP',             type: 'indicator' },
      { slug: 'atr',           label: 'ATR',              type: 'indicator' },
      { slug: 'stochastic',    label: 'Stochastic',       type: 'indicator' },
      { slug: 'obv',           label: 'OBV',              type: 'indicator' },
      { slug: 'adx',           label: 'ADX',              type: 'indicator' },
      { slug: 'cci',           label: 'CCI',              type: 'indicator' },
      { slug: 'williams-r',    label: 'Williams %R',      type: 'indicator' },
      { slug: 'roc',           label: 'ROC',              type: 'indicator' },
      { slug: 'mfi',           label: 'MFI',              type: 'indicator' },
      { slug: 'ichimoku',      label: 'Ichimoku Cloud',   type: 'indicator' },
      { slug: 'parabolic-sar', label: 'Parabolic SAR',    type: 'indicator' },
    ],
  },
  {
    category: 'options',
    label: 'Options & FnO',
    icon: 'Δ',
    items: [
      { slug: 'calls-puts', label: 'Calls & Puts',   type: 'option' },
      { slug: 'delta',      label: 'Delta (Δ)',      type: 'option', greek: 'delta' },
      { slug: 'theta',      label: 'Theta (Θ)',      type: 'option', greek: 'theta' },
      { slug: 'gamma',      label: 'Gamma (Γ)',      type: 'option', greek: 'gamma' },
      { slug: 'vega',       label: 'Vega (ν)',       type: 'option', greek: 'vega' },
      { slug: 'iv-crush',   label: 'IV Crush',       type: 'option' },
    ],
  },
];

// ── Content fetcher ───────────────────────────────────────────────────────────

function useContent(item) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!item) return;
    setContent(null);
    setLoading(true);
    const map = { concept: 'concepts', indicator: 'indicators', option: 'options' };
    fetch(`${API_BASE}/education/${map[item.type]}/${item.slug}`)
      .then(r => r.json())
      .then(d => { setContent(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [item?.slug, item?.type]);

  return { content, loading };
}

// ── Formula card ──────────────────────────────────────────────────────────────

function FormulaCard({ formula }) {
  if (!formula) return null;
  return (
    <div className="edu-formula-card">
      <span className="edu-formula-label">Formula</span>
      <pre className="edu-formula-body">{formula}</pre>
    </div>
  );
}

// ── Content sections ──────────────────────────────────────────────────────────

function Section({ title, text, accent }) {
  if (!text) return null;
  return (
    <div className={`edu-section ${accent ? 'edu-section-accent' : ''}`}>
      <div className="edu-section-title">{title}</div>
      <div className="edu-section-body">{text}</div>
    </div>
  );
}

function Signals({ signals }) {
  if (!signals) return null;
  return (
    <div className="edu-signals-block">
      <div className="edu-section-title">Signal Interpretation</div>
      <div className="edu-signals-grid">
        {Object.entries(signals).map(([k, v]) => (
          <div key={k} className="edu-signal-item">
            <span className="edu-signal-key">{k.replace(/_/g, ' ')}</span>
            <span className="edu-signal-val">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function InterpretationCards({ interp }) {
  if (!interp) return null;
  return (
    <div className="edu-interp-block">
      <div className="edu-section-title">Level Interpretation</div>
      <div className="edu-interp-grid">
        {Object.entries(interp).map(([k, v]) => (
          <div key={k} className="edu-interp-card">
            <span className="edu-interp-key">{k.replace(/_/g, ' ')}</span>
            <span className="edu-interp-val">{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Payoff diagram (static, for Calls & Puts) ──────────────────────────────────

function PayoffDiagram() {
  const prices = Array.from({ length: 60 }, (_, i) => 80 + i);
  const premium = 5;
  const strike = 100;

  const callPayoff  = prices.map(p => Math.max(0, p - strike) - premium);
  const callSeller  = prices.map(p => premium - Math.max(0, p - strike));
  const putPayoff   = prices.map(p => Math.max(0, strike - p) - premium);

  const ds = [
    { label: 'Call Buyer P&L', data: callPayoff,  borderColor: '#00d296', borderWidth: 2.5, pointRadius: 0, fill: false, tension: 0 },
    { label: 'Call Seller P&L', data: callSeller, borderColor: '#ef4444', borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0, borderDash: [5,4] },
    { label: 'Put Buyer P&L',   data: putPayoff,  borderColor: '#5ab4e5', borderWidth: 2,   pointRadius: 0, fill: false, tension: 0 },
  ];

  const options = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults },
      legend: { display: true, position: 'top', align: 'end' },
      annotation: {
        annotations: {
          zero:   { type: 'line', yMin: 0, yMax: 0, borderColor: 'rgba(255,255,255,0.2)', borderWidth: 1 },
          strike: { type: 'line', xMin: strike - 80, xMax: strike - 80, borderColor: '#00d296', borderWidth: 1, borderDash: [4,4],
                    label: { content: 'Strike ₹100', display: true, color: '#00d296', font: { size: 10 } } },
        },
      },
    },
    scales: {
      x: { ...scaleDefaults, title: { display: true, text: 'Underlying Price at Expiry', color: C.textMuted, font: { size: 10 } },
           ticks: { ...scaleDefaults.ticks, callback: (_, i) => prices[i] !== undefined ? `₹${prices[i]}` : '', maxTicksLimit: 8 } },
      y: { ...scaleDefaults, title: { display: true, text: 'P&L (₹ per share)', color: C.textMuted, font: { size: 10 } } },
    },
  };

  return (
    <div className="edu-payoff-wrap">
      <div className="edu-payoff-note">Assumes Strike = ₹100, Premium = ₹5. Horizontal axis = underlying price at expiry.</div>
      <div style={{ height: 260 }}>
        <Line data={{ labels: prices.map(p => `₹${p}`), datasets: ds }} options={options} />
      </div>
    </div>
  );
}

// ── Main content pane ─────────────────────────────────────────────────────────

function ContentPane({ item, content, loading, onAskTutor }) {
  if (!item) {
    return (
      <div className="edu-welcome">
        <div className="edu-welcome-icon">◈</div>
        <h2 className="edu-welcome-title">Financial Education Hub</h2>
        <p className="edu-welcome-sub">
          Select a concept, indicator, or options topic from the sidebar.<br />
          Every module includes interactive live charts, professional analysis, and AI tutoring.
        </p>
        <div className="edu-welcome-cards">
          <div className="edu-wc">
            <span className="edu-wc-icon">∑</span>
            <span>Statistics</span>
            <span className="edu-wc-sub">Mean, Std Dev, Beta, Sharpe</span>
          </div>
          <div className="edu-wc">
            <span className="edu-wc-icon">⌇</span>
            <span>Indicators</span>
            <span className="edu-wc-sub">RSI, MACD, Bollinger, ATR</span>
          </div>
          <div className="edu-wc">
            <span className="edu-wc-icon">Δ</span>
            <span>Options & FnO</span>
            <span className="edu-wc-sub">Greeks, Calls, IV Crush</span>
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <ContentSkeleton />;
  if (!content) return <div className="edu-empty">Content unavailable</div>;

  const hasIndicatorChart = item.type === 'indicator' && !['vwap'].includes(item.slug);
  const hasGreekChart = item.type === 'option' && item.greek;
  const hasPayoff = item.slug === 'calls-puts';

  return (
    <div className="edu-content-pane">
      {/* Title strip */}
      <div className="edu-content-header">
        <div className="edu-content-accent" />
        <div className="edu-content-header-inner">
          <div className="edu-content-category">{content.category?.toUpperCase()}</div>
          <h1 className="edu-content-title">{content.title}</h1>
          <p className="edu-content-tagline">{content.tagline}</p>
          <button className="edu-tutor-btn" onClick={onAskTutor}>
            <span>◈</span> Ask AI Tutor
          </button>
        </div>
      </div>

      {/* Live chart */}
      {hasIndicatorChart && (
        <div className="edu-chart-section">
          <IndicatorChart slug={item.slug} />
        </div>
      )}

      {/* Payoff diagram */}
      {hasPayoff && (
        <div className="edu-chart-section">
          <Suspense fallback={<div className="edu-chart-loading" />}>
            <PayoffDiagram />
          </Suspense>
        </div>
      )}

      {/* Greek curve */}
      {hasGreekChart && (
        <div className="edu-chart-section">
          <div className="edu-chart-label">
            {content.title} curve — mathematical model (Black-Scholes)
          </div>
          <GreekChart greekName={item.greek} />
        </div>
      )}

      {/* Content body */}
      <div className="edu-body">
        <FormulaCard formula={content.formula} />
        <Section title="What is it?" text={content.what} />
        <Section title="Why it matters" text={content.why} />
        {content.signals && <Signals signals={content.signals} />}
        {content.interpretation && <InterpretationCards interp={content.interpretation} />}
        <Section title="Professional application" text={content.professional_use} />
        <Section title="Market interpretation" text={content.market_interpretation} />
        <Section title="Market context" text={content.market_context} />
        <Section title="Example" text={content.example} accent />
        <Section title="How to navigate" text={content.how_to_navigate} />
        <Section title="Where it fails" text={content.where_it_fails} accent />

        {/* Payoff formulas */}
        {content.payoff_call && (
          <div className="edu-payoff-formulas">
            <FormulaCard formula={`Call: ${content.payoff_call}`} />
            <FormulaCard formula={`Put:  ${content.payoff_put}`} />
          </div>
        )}
      </div>
    </div>
  );
}

function ContentSkeleton() {
  return (
    <div className="edu-content-pane edu-skeleton-pane">
      <div className="edu-sk-header" />
      <div className="edu-sk-chart" />
      <div className="edu-sk-body">
        <div className="edu-sk-line" />
        <div className="edu-sk-line edu-sk-short" />
        <div className="edu-sk-line" />
        <div className="edu-sk-line edu-sk-medium" />
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function Education() {
  const [activeItem, setActiveItem]     = useState(null);
  const [expandedCats, setExpandedCats] = useState({ statistics: true, indicators: true, options: true });
  const [tutorOpen, setTutorOpen]       = useState(false);
  const [chartContext, setChartContext] = useState(null);

  const { content, loading } = useContent(activeItem);

  const handleSelect = (item) => {
    setActiveItem(item);
    setChartContext(null);
  };

  const handleAskTutor = () => {
    if (activeItem && content) {
      setChartContext({
        indicator: activeItem.slug,
        ticker: '^NSEI',
        category: activeItem.type,
        title: content.title,
        tagline: content.tagline,
      });
    }
    setTutorOpen(true);
  };

  const toggleCat = (cat) => {
    setExpandedCats(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  return (
    <div className="edu-page">
      <Navbar />

      <div className="edu-layout">
        {/* Sidebar */}
        <aside className="edu-sidebar">
          <div className="edu-sidebar-title">Education Hub</div>

          {NAV.map(section => (
            <div key={section.category} className="edu-nav-section">
              <button
                className="edu-nav-category"
                onClick={() => toggleCat(section.category)}
              >
                <span className="edu-nav-cat-icon">{section.icon}</span>
                <span>{section.label}</span>
                <span className={`edu-nav-arrow ${expandedCats[section.category] ? 'open' : ''}`}>▾</span>
              </button>

              {expandedCats[section.category] && (
                <div className="edu-nav-items">
                  {section.items.map(item => (
                    <button
                      key={item.slug}
                      className={`edu-nav-item ${activeItem?.slug === item.slug ? 'active' : ''}`}
                      onClick={() => handleSelect(item)}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          <div className="edu-sidebar-footer">
            <button className="edu-tutor-sidebar-btn" onClick={() => setTutorOpen(true)}>
              <span>◈</span> AI Tutor
            </button>
          </div>
        </aside>

        {/* Main content */}
        <main className="edu-main">
          <ContentPane
            item={activeItem}
            content={content}
            loading={loading}
            onAskTutor={handleAskTutor}
          />
        </main>
      </div>

      {/* Tutor panel */}
      <TutorPanel
        open={tutorOpen}
        onClose={() => setTutorOpen(false)}
        chartContext={chartContext}
      />
    </div>
  );
}
