/**
 * Live indicator chart component — renders RSI, MACD, Bollinger, EMA, ATR
 * from backend /education/chart/* endpoints.
 */
import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Chart, CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Filler, Tooltip, Legend,
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import { Line, Bar } from 'react-chartjs-2';
import { C, tooltipDefaults, scaleDefaults, makeGradient } from '../../lib/chartTheme';
import { API_BASE } from '../../lib/api';
import './indicatorChart.css';

Chart.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, Filler, Tooltip, Legend, annotationPlugin,
);

const TICKER_OPTIONS = [
  { value: '^NSEI',    label: 'NIFTY 50' },
  { value: '^NSEBANK', label: 'BANKNIFTY' },
  { value: 'RELIANCE.NS', label: 'RELIANCE' },
  { value: 'TCS.NS',   label: 'TCS' },
  { value: 'HDFCBANK.NS', label: 'HDFC BANK' },
  { value: 'INFY.NS',  label: 'INFOSYS' },
];

function useIndicatorData(slug, ticker, extraParams = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ ticker, ...extraParams });
      const res = await fetch(`${API_BASE}/education/chart/${slug}?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError('Unable to load live data');
    } finally {
      setLoading(false);
    }
  }, [slug, ticker, JSON.stringify(extraParams)]);

  useEffect(() => { fetchData(); }, [fetchData]);
  return { data, loading, error, refetch: fetchData };
}

// ── Ticker selector ───────────────────────────────────────────────────────────

function TickerSelector({ value, onChange }) {
  return (
    <div className="ic-ticker-row">
      <span className="ic-ticker-label">Live data</span>
      <select className="ic-ticker-select" value={value} onChange={e => onChange(e.target.value)}>
        {TICKER_OPTIONS.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

// ── RSI Chart ─────────────────────────────────────────────────────────────────

function RSIChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('rsi', ticker);

  if (loading) return <ChartSkeleton />;
  if (error || !data)  return <ChartError msg={error} />;

  const dates    = data.dates;
  const priceDs  = {
    label: 'Price',
    data: data.price,
    borderColor: C.textSecondary,
    borderWidth: 1.5,
    pointRadius: 0,
    tension: 0.3,
    fill: false,
    yAxisID: 'yPrice',
  };
  const rsiDs = {
    label: 'RSI (14)',
    data: data.rsi,
    borderColor: C.emerald,
    borderWidth: 2,
    pointRadius: 0,
    tension: 0.3,
    fill: {
      target: { value: 50 },
      above: 'rgba(0,210,150,0.08)',
      below: 'rgba(239,68,68,0.08)',
    },
    yAxisID: 'yRSI',
  };

  const priceOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults },
      legend: { display: false },
      annotation: {
        annotations: {
          ob: { type: 'box', yScaleID: 'yRSI', yMin: 70, yMax: 100, backgroundColor: 'rgba(239,68,68,0.07)', borderWidth: 0 },
          os: { type: 'box', yScaleID: 'yRSI', yMin: 0,  yMax: 30,  backgroundColor: 'rgba(34,197,94,0.07)',  borderWidth: 0 },
          ob_line: { type: 'line', yScaleID: 'yRSI', yMin: 70, yMax: 70, borderColor: 'rgba(239,68,68,0.4)', borderWidth: 1, borderDash: [4, 4] },
          os_line: { type: 'line', yScaleID: 'yRSI', yMin: 30, yMax: 30, borderColor: 'rgba(34,197,94,0.4)', borderWidth: 1, borderDash: [4, 4] },
          mid:     { type: 'line', yScaleID: 'yRSI', yMin: 50, yMax: 50, borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1, borderDash: [2, 4] },
        },
      },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yPrice: { ...scaleDefaults, position: 'left', ticks: { ...scaleDefaults.ticks } },
      yRSI: {
        ...scaleDefaults,
        position: 'right',
        min: 0, max: 100,
        grid: { ...scaleDefaults.grid, drawOnChartArea: false },
        ticks: { ...scaleDefaults.ticks, callback: v => v },
      },
    },
  };

  const current = data.current;
  const rsiColor = current.rsi >= 70 ? C.red : current.rsi <= 30 ? C.green : C.emerald;

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="Current RSI" value={current.rsi} color={rsiColor} />
        <Stat label="Price" value={`₹${current.price?.toLocaleString('en-IN')}`} />
        <Stat label="As of" value={current.date} mono />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-zone-labels">
        <span className="ic-zone red">Overbought &gt; 70</span>
        <span className="ic-zone green">Oversold &lt; 30</span>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: dates, datasets: [priceDs, rsiDs] }} options={priceOptions} />
      </div>
      {data.signals.length > 0 && (
        <div className="ic-signals">
          <span className="ic-signals-label">Recent signals</span>
          {data.signals.slice(-5).reverse().map((s, i) => (
            <span key={i} className={`ic-signal-badge ${s.type}`}>
              {s.type === 'overbought' ? '↑ OB' : '↓ OS'} {s.value} · {s.date}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── MACD Chart ────────────────────────────────────────────────────────────────

function MACDChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('macd', ticker);

  if (loading) return <ChartSkeleton />;
  if (error || !data)  return <ChartError msg={error} />;

  const histColors = data.histogram.map(v =>
    v === null ? C.textMuted : v >= 0 ? 'rgba(34,197,94,0.7)' : 'rgba(239,68,68,0.7)'
  );
  const histBorders = data.histogram.map(v =>
    v === null ? C.textMuted : v >= 0 ? C.green : C.red
  );

  const datasets = [
    {
      type: 'line',
      label: 'MACD',
      data: data.macd,
      borderColor: C.emerald,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      yAxisID: 'y',
    },
    {
      type: 'line',
      label: 'Signal',
      data: data.signal,
      borderColor: C.ice,
      borderWidth: 1.5,
      pointRadius: 0,
      borderDash: [4, 3],
      tension: 0.3,
      yAxisID: 'y',
    },
    {
      type: 'bar',
      label: 'Histogram',
      data: data.histogram,
      backgroundColor: histColors,
      borderColor: histBorders,
      borderWidth: 1,
      borderRadius: 2,
      yAxisID: 'y',
    },
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults },
      legend: { display: true, position: 'top', align: 'end' },
      annotation: {
        annotations: {
          zero: { type: 'line', yMin: 0, yMax: 0, borderColor: 'rgba(255,255,255,0.15)', borderWidth: 1 },
        },
      },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      y: { ...scaleDefaults },
    },
  };

  const cur = data.current;
  const bullish = cur.macd > cur.signal;

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="MACD" value={cur.macd?.toFixed(2)} color={bullish ? C.green : C.red} />
        <Stat label="Signal" value={cur.signal?.toFixed(2)} />
        <Stat label="Histogram" value={cur.histogram?.toFixed(2)} color={cur.histogram >= 0 ? C.green : C.red} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      {data.crossovers.length > 0 && (
        <div className="ic-signals">
          <span className="ic-signals-label">Recent crossovers</span>
          {data.crossovers.slice(-4).reverse().map((c, i) => (
            <span key={i} className={`ic-signal-badge ${c.type}`}>
              {c.type === 'bullish' ? '↑ Bullish' : '↓ Bearish'} · {c.date}
            </span>
          ))}
        </div>
      )}
      <div className="ic-canvas-wrap">
        <Bar data={{ labels: data.dates, datasets }} options={options} />
      </div>
    </div>
  );
}

// ── Bollinger Chart ───────────────────────────────────────────────────────────

function BollingerChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('bollinger', ticker);
  const chartRef = useRef(null);

  if (loading) return <ChartSkeleton />;
  if (error || !data)  return <ChartError msg={error} />;

  const fillColor = 'rgba(0,210,150,0.06)';

  const datasets = [
    {
      label: 'Upper Band',
      data: data.upper,
      borderColor: 'rgba(239,68,68,0.5)',
      borderWidth: 1.5,
      borderDash: [3, 3],
      pointRadius: 0,
      fill: '+1',
      backgroundColor: fillColor,
      tension: 0.3,
    },
    {
      label: 'SMA 20',
      data: data.middle,
      borderColor: C.emerald,
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
    {
      label: 'Lower Band',
      data: data.lower,
      borderColor: 'rgba(34,197,94,0.5)',
      borderWidth: 1.5,
      borderDash: [3, 3],
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
    {
      label: 'Price',
      data: data.price,
      borderColor: C.textPrimary,
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults },
      legend: { display: true, position: 'top', align: 'end' },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      y: { ...scaleDefaults },
    },
  };

  const cur = data.current;
  const pbColor = cur.pct_b > 0.8 ? C.red : cur.pct_b < 0.2 ? C.green : C.textSecondary;

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="%B" value={cur.pct_b?.toFixed(2)} color={pbColor} />
        <Stat label="Bandwidth" value={`${cur.bandwidth?.toFixed(1)}%`} />
        <Stat label="Upper" value={`₹${cur.upper?.toLocaleString('en-IN')}`} />
        <Stat label="Lower" value={`₹${cur.lower?.toLocaleString('en-IN')}`} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-canvas-wrap">
        <Line ref={chartRef} data={{ labels: data.dates, datasets }} options={options} />
      </div>
      {data.squeezes.length > 0 && (
        <div className="ic-signals">
          <span className="ic-signals-label">Squeeze events</span>
          {data.squeezes.slice(-4).reverse().map((s, i) => (
            <span key={i} className={`ic-signal-badge ${s.type === 'squeeze_start' ? 'neutral' : 'bullish'}`}>
              {s.type === 'squeeze_start' ? '◎ Squeeze' : '→ Expansion'} · {s.date}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── EMA Chart ─────────────────────────────────────────────────────────────────

function EMAChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('ema', ticker);

  if (loading) return <ChartSkeleton />;
  if (error || !data)  return <ChartError msg={error} />;

  const datasets = [
    {
      label: 'Price',
      data: data.price,
      borderColor: 'rgba(238,242,246,0.6)',
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
    {
      label: 'EMA 20',
      data: data.ema20,
      borderColor: C.emerald,
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
    {
      label: 'EMA 50',
      data: data.ema50,
      borderColor: C.ice,
      borderWidth: 1.5,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
    {
      label: 'EMA 200',
      data: data.ema200,
      borderColor: '#f59e0b',
      borderWidth: 2,
      pointRadius: 0,
      fill: false,
      tension: 0.3,
    },
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults },
      legend: { display: true, position: 'top', align: 'end' },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      y: { ...scaleDefaults },
    },
  };

  const cur = data.current;
  const regime = cur.above_200 ? { label: 'Bull Regime', color: C.green } : { label: 'Bear Regime', color: C.red };

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="Regime" value={regime.label} color={regime.color} />
        <Stat label="EMA 20" value={`₹${cur.ema20?.toLocaleString('en-IN')}`} />
        <Stat label="EMA 50" value={`₹${cur.ema50?.toLocaleString('en-IN')}`} />
        <Stat label="EMA 200" value={`₹${cur.ema200?.toLocaleString('en-IN')}`} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      {data.crosses.length > 0 && (
        <div className="ic-signals">
          <span className="ic-signals-label">Golden / Death crosses</span>
          {data.crosses.slice(-4).reverse().map((c, i) => (
            <span key={i} className={`ic-signal-badge ${c.type === 'golden_cross' ? 'bullish' : 'bearish'}`}>
              {c.type === 'golden_cross' ? '✦ Golden Cross' : '✕ Death Cross'} · {c.date}
            </span>
          ))}
        </div>
      )}
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets }} options={options} />
      </div>
    </div>
  );
}

// ── ATR Chart ─────────────────────────────────────────────────────────────────

function ATRChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('atr', ticker);

  if (loading) return <ChartSkeleton />;
  if (error || !data)  return <ChartError msg={error} />;

  const datasets = [
    {
      label: 'ATR',
      data: data.atr,
      borderColor: C.emerald,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: {
        target: 'origin',
        above: 'rgba(0,210,150,0.08)',
      },
      yAxisID: 'yATR',
    },
    {
      label: 'ATR %',
      data: data.atr_pct,
      borderColor: C.ice,
      borderWidth: 1.5,
      pointRadius: 0,
      tension: 0.3,
      fill: false,
      yAxisID: 'yPct',
    },
  ];

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: {
        ...tooltipDefaults,
        callbacks: {
          label: ctx => {
            const ds = ctx.dataset;
            if (ds.yAxisID === 'yPct') return `ATR%: ${ctx.parsed.y?.toFixed(2)}%`;
            return `ATR: ₹${ctx.parsed.y?.toLocaleString('en-IN')}`;
          },
        },
      },
      legend: { display: true, position: 'top', align: 'end' },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yATR: { ...scaleDefaults, position: 'left' },
      yPct: {
        ...scaleDefaults,
        position: 'right',
        grid: { ...scaleDefaults.grid, drawOnChartArea: false },
        ticks: { ...scaleDefaults.ticks, callback: v => `${v}%` },
      },
    },
  };

  const cur = data.current;

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label={`ATR (${data.period})`} value={`₹${cur.atr?.toLocaleString('en-IN')}`} />
        <Stat label="ATR%" value={`${cur.atr_pct?.toFixed(2)}%`} color={cur.atr_pct > 2.5 ? C.red : C.textSecondary} />
        <Stat label="1× Stop" value={`₹${cur.stop_1x?.toLocaleString('en-IN')}`} />
        <Stat label="2× Stop" value={`₹${cur.stop_2x?.toLocaleString('en-IN')}`} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets }} options={options} />
      </div>
      <div className="ic-stop-guide">
        <span className="ic-sg-title">Stop-loss guide (from current price ₹{cur.price?.toLocaleString('en-IN')})</span>
        <span className="ic-sg-item">1× ATR stop: ₹{cur.stop_1x?.toLocaleString('en-IN')}</span>
        <span className="ic-sg-item">1.5× ATR stop: ₹{cur.stop_15x?.toLocaleString('en-IN')}</span>
        <span className="ic-sg-item">2× ATR stop: ₹{cur.stop_2x?.toLocaleString('en-IN')}</span>
      </div>
    </div>
  );
}

// ── Stochastic Chart ──────────────────────────────────────────────────────────

function StochasticChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('stochastic', ticker);
  if (loading) return <ChartSkeleton />;
  if (error || !data) return <ChartError msg={error} />;

  const cur = data.current;
  const kColor = cur.k > 80 ? C.red : cur.k < 20 ? C.green : C.emerald;

  const opts = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults }, legend: { display: true, position: 'top', align: 'end' },
      annotation: {
        annotations: {
          ob: { type: 'box', yMin: 80, yMax: 100, backgroundColor: 'rgba(239,68,68,0.07)', borderWidth: 0 },
          os: { type: 'box', yMin: 0,  yMax: 20,  backgroundColor: 'rgba(34,197,94,0.07)',  borderWidth: 0 },
          ob_l: { type: 'line', yMin: 80, yMax: 80, borderColor: 'rgba(239,68,68,0.4)', borderWidth: 1, borderDash: [4,4] },
          os_l: { type: 'line', yMin: 20, yMax: 20, borderColor: 'rgba(34,197,94,0.4)',  borderWidth: 1, borderDash: [4,4] },
        },
      },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yPrice: { ...scaleDefaults, position: 'left' },
      yStoch: { ...scaleDefaults, position: 'right', min: 0, max: 100, grid: { ...scaleDefaults.grid, drawOnChartArea: false } },
    },
  };

  const datasets = [
    { label: 'Price', data: data.price, borderColor: C.textSecondary, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yPrice' },
    { label: '%K', data: data.k, borderColor: C.emerald, borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yStoch' },
    { label: '%D (Signal)', data: data.d, borderColor: C.ice, borderWidth: 1.5, borderDash: [4,3], pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yStoch' },
  ];

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="%K" value={cur.k} color={kColor} />
        <Stat label="%D" value={cur.d} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-zone-labels">
        <span className="ic-zone red">Overbought &gt; 80</span>
        <span className="ic-zone green">Oversold &lt; 20</span>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets }} options={opts} />
      </div>
      {data.signals?.length > 0 && (
        <div className="ic-signals">
          <span className="ic-signals-label">Crossover signals</span>
          {data.signals.slice(-5).reverse().map((s, i) => (
            <span key={i} className={`ic-signal-badge ${s.type === 'bullish_cross' ? 'bullish' : 'bearish'}`}>
              {s.type === 'bullish_cross' ? '↑ Bull Cross' : '↓ Bear Cross'} {s.value} · {s.date}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── OBV Chart ─────────────────────────────────────────────────────────────────

function OBVChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('obv', ticker);
  if (loading) return <ChartSkeleton />;
  if (error || !data) return <ChartError msg={error} />;

  const opts = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { tooltip: { ...tooltipDefaults }, legend: { display: true, position: 'top', align: 'end' } },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yPrice: { ...scaleDefaults, position: 'left' },
      yOBV: { ...scaleDefaults, position: 'right', grid: { ...scaleDefaults.grid, drawOnChartArea: false },
               ticks: { ...scaleDefaults.ticks, callback: v => v >= 1e6 ? `${(v/1e6).toFixed(1)}M` : v >= 1e3 ? `${(v/1e3).toFixed(0)}K` : v } },
    },
  };

  const trend = data.current.obv_trend;
  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="OBV Trend" value={trend === 'rising' ? '↑ Rising' : '↓ Falling'} color={trend === 'rising' ? C.green : C.red} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets: [
          { label: 'Price', data: data.price, borderColor: C.textSecondary, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yPrice' },
          { label: 'OBV', data: data.obv, borderColor: C.emerald, borderWidth: 2, pointRadius: 0, tension: 0.3, fill: { target: 'origin', above: 'rgba(0,210,150,0.07)' }, yAxisID: 'yOBV' },
        ]}} options={opts} />
      </div>
    </div>
  );
}

// ── ADX Chart ─────────────────────────────────────────────────────────────────

function ADXChart({ ticker }) {
  const { data, loading, error } = useIndicatorData('adx', ticker);
  if (loading) return <ChartSkeleton />;
  if (error || !data) return <ChartError msg={error} />;

  const cur = data.current;
  const adxColor = cur.adx > 40 ? C.emerald : cur.adx > 25 ? C.ice : C.textMuted;

  const opts = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: { ...tooltipDefaults }, legend: { display: true, position: 'top', align: 'end' },
      annotation: {
        annotations: {
          weak: { type: 'line', yMin: 20, yMax: 20, yScaleID: 'yADX', borderColor: 'rgba(255,255,255,0.15)', borderWidth: 1, borderDash: [4,4] },
          strong: { type: 'line', yMin: 40, yMax: 40, yScaleID: 'yADX', borderColor: 'rgba(0,210,150,0.3)', borderWidth: 1, borderDash: [4,4] },
        },
      },
    },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yPrice: { ...scaleDefaults, position: 'left' },
      yADX: { ...scaleDefaults, position: 'right', min: 0, grid: { ...scaleDefaults.grid, drawOnChartArea: false } },
    },
  };

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label="ADX" value={cur.adx} color={adxColor} />
        <Stat label="+DI" value={cur.plus_di} color={C.green} />
        <Stat label="-DI" value={cur.minus_di} color={C.red} />
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets: [
          { label: 'Price', data: data.price, borderColor: C.textSecondary, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yPrice' },
          { label: 'ADX', data: data.adx, borderColor: C.emerald, borderWidth: 2.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yADX' },
          { label: '+DI', data: data.plus_di, borderColor: C.green, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yADX' },
          { label: '-DI', data: data.minus_di, borderColor: C.red, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yADX' },
        ]}} options={opts} />
      </div>
    </div>
  );
}

// ── Generic oscillator chart (CCI / Williams %R / ROC / MFI) ─────────────────

function OscillatorChart({ slug, ticker, fieldKey, label, ob, os, obColor, osColor, obLabel, osLabel, yMin, yMax, formatVal }) {
  const { data, loading, error } = useIndicatorData(slug, ticker);
  if (loading) return <ChartSkeleton />;
  if (error || !data) return <ChartError msg={error} />;

  const fieldData = data[fieldKey] || data.cci || data.williams_r || data.roc || data.mfi;
  const curVal = data.current[fieldKey] ?? data.current.cci ?? data.current.williams_r ?? data.current.roc ?? data.current.mfi;
  const fmtVal = formatVal ? formatVal(curVal) : curVal;
  const valColor = curVal != null ? (curVal > (ob || 80) ? (obColor || C.red) : curVal < (os || 20) ? (osColor || C.green) : C.textSecondary) : C.textSecondary;

  const annotations = {};
  if (ob != null) {
    annotations.ob_line = { type: 'line', yMin: ob, yMax: ob, borderColor: obColor || 'rgba(239,68,68,0.4)', borderWidth: 1, borderDash: [4,4] };
  }
  if (os != null) {
    annotations.os_line = { type: 'line', yMin: os, yMax: os, borderColor: osColor || 'rgba(34,197,94,0.4)',  borderWidth: 1, borderDash: [4,4] };
  }
  if (ob == null && os == null) {
    annotations.zero = { type: 'line', yMin: 0, yMax: 0, borderColor: 'rgba(255,255,255,0.15)', borderWidth: 1 };
  }

  const opts = {
    responsive: true, maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { tooltip: { ...tooltipDefaults }, legend: { display: false }, annotation: { annotations } },
    scales: {
      x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, maxTicksLimit: 8 } },
      yPrice: { ...scaleDefaults, position: 'left' },
      yOsc: {
        ...scaleDefaults, position: 'right',
        ...(yMin != null ? { min: yMin } : {}), ...(yMax != null ? { max: yMax } : {}),
        grid: { ...scaleDefaults.grid, drawOnChartArea: false },
      },
    },
  };

  return (
    <div className="ic-chart-wrap">
      <div className="ic-stat-row">
        <Stat label={label} value={fmtVal} color={valColor} />
        {ob != null && obLabel && <span className="ic-zone red">{obLabel}</span>}
        {os != null && osLabel && <span className="ic-zone green">{osLabel}</span>}
        <div className="ic-interp">{data.interpretation}</div>
      </div>
      <div className="ic-canvas-wrap">
        <Line data={{ labels: data.dates, datasets: [
          { label: 'Price', data: data.price, borderColor: C.textSecondary, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yPrice' },
          { label, data: fieldData, borderColor: C.emerald, borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'yOsc' },
        ]}} options={opts} />
      </div>
    </div>
  );
}

// ── Shared sub-components ─────────────────────────────────────────────────────

function Stat({ label, value, color, mono }) {
  return (
    <div className="ic-stat">
      <span className="ic-stat-label">{label}</span>
      <span className="ic-stat-value" style={color ? { color } : undefined}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="ic-chart-wrap ic-loading">
      <div className="ic-skeleton ic-sk-stats" />
      <div className="ic-skeleton ic-sk-canvas" />
    </div>
  );
}

function ChartError({ msg }) {
  return (
    <div className="ic-chart-wrap ic-error">
      <span className="ic-error-icon">⚠</span>
      <span>{msg || 'Failed to load chart data'}</span>
      <span className="ic-error-sub">Check that the backend is running on port 8000</span>
    </div>
  );
}

// ── Public component ──────────────────────────────────────────────────────────

const CCIChartWrapper       = ({ ticker }) => <OscillatorChart slug="cci"         ticker={ticker} fieldKey="cci"       label="CCI"        ob={100}   os={-100}  obColor="rgba(239,68,68,0.8)"  osColor="rgba(34,197,94,0.8)"  obLabel="Overbought >100" osLabel="Oversold <-100" />;
const WilliamsRChartWrapper = ({ ticker }) => <OscillatorChart slug="williams-r"  ticker={ticker} fieldKey="williams_r" label="Williams %R" ob={-20}   os={-80}   obColor="rgba(239,68,68,0.8)"  osColor="rgba(34,197,94,0.8)"  obLabel="Overbought >-20" osLabel="Oversold <-80" yMin={-100} yMax={0} />;
const ROCChartWrapper       = ({ ticker }) => <OscillatorChart slug="roc"         ticker={ticker} fieldKey="roc"       label="ROC %"      ob={null}  os={null} />;
const MFIChartWrapper       = ({ ticker }) => <OscillatorChart slug="mfi"         ticker={ticker} fieldKey="mfi"       label="MFI"        ob={80}    os={20}    obColor="rgba(239,68,68,0.8)"  osColor="rgba(34,197,94,0.8)"  obLabel="Overbought >80"  osLabel="Oversold <20"  yMin={0}    yMax={100} />;

const CHART_MAP = {
  rsi:           RSIChart,
  macd:          MACDChart,
  bollinger:     BollingerChart,
  'ema-sma':     EMAChart,
  ema:           EMAChart,
  atr:           ATRChart,
  stochastic:    StochasticChart,
  obv:           OBVChart,
  adx:           ADXChart,
  cci:           CCIChartWrapper,
  'williams-r':  WilliamsRChartWrapper,
  roc:           ROCChartWrapper,
  mfi:           MFIChartWrapper,
};

export default function IndicatorChart({ slug, onDataLoad }) {
  const [ticker, setTicker] = useState('^NSEI');

  const ChartComponent = CHART_MAP[slug];
  if (!ChartComponent) return null;

  return (
    <div className="ic-container">
      <div className="ic-header">
        <span className="ic-header-label">Live Chart</span>
        <TickerSelector value={ticker} onChange={setTicker} />
      </div>
      <ChartComponent ticker={ticker} />
    </div>
  );
}
