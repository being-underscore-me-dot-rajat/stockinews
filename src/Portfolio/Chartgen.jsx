import React, { useEffect, useRef, useState } from 'react';
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement,
  Filler,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import { API_BASE } from '../lib/api';
import { C, tooltipDefaults, scaleDefaults } from '../lib/chartTheme';
import './chartgen.css';

ChartJS.register(
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale,
  BarElement, LineElement, PointElement,
  Filler,
);

// ── Donut: holdings distribution ─────────────────────────────────────────────

function HoldingsDonut({ portfolio }) {
  if (!portfolio.length) return null;

  const data = {
    labels: portfolio.map(i => i.ticker?.replace('.NS', '')),
    datasets: [{
      data: portfolio.map(i => +(i.quantity * i.avg_price).toFixed(0)),
      backgroundColor: C.palette.slice(0, portfolio.length),
      borderColor: C.bgSurface,
      borderWidth: 3,
      hoverOffset: 6,
    }],
  };

  const options = {
    cutout: '68%',
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: C.textSecondary,
          font: { family: C.fontSans, size: 11 },
          boxWidth: 8, boxHeight: 8,
          padding: 10,
          usePointStyle: true,
          pointStyle: 'circle',
        },
      },
      tooltip: {
        ...tooltipDefaults,
        callbacks: {
          label: (ctx) => {
            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
            const pct   = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
            return ` ₹${Number(ctx.parsed).toLocaleString('en-IN', { maximumFractionDigits: 0 })}  (${pct}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="cg-card">
      <div className="cg-card-head">
        <span className="cg-card-title">Holdings Distribution</span>
        <span className="cg-card-sub">by invested value</span>
      </div>
      <div className="cg-donut-wrap">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
}

// ── Bar: P&L per holding ──────────────────────────────────────────────────────

function PnLBar({ portfolio }) {
  if (!portfolio.length) return null;

  const values = portfolio.map(i =>
    +((i.current_price - i.avg_price) * i.quantity).toFixed(2)
  );

  const data = {
    labels: portfolio.map(i => i.ticker?.replace('.NS', '')),
    datasets: [{
      label: 'P&L ₹',
      data: values,
      backgroundColor: values.map(v =>
        v >= 0 ? 'rgba(34,197,94,0.75)' : 'rgba(239,68,68,0.75)'
      ),
      borderColor: values.map(v => v >= 0 ? C.green : C.red),
      borderWidth: 1,
      borderRadius: 3,
      borderSkipped: false,
    }],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        ...tooltipDefaults,
        callbacks: {
          label: (ctx) => {
            const v = ctx.parsed.y;
            const sign = v >= 0 ? '+' : '';
            return ` ${sign}₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
          },
        },
      },
    },
    scales: {
      x: {
        ...scaleDefaults,
        ticks: { ...scaleDefaults.ticks, font: { family: C.fontMono, size: 10 } },
      },
      y: {
        ...scaleDefaults,
        ticks: {
          ...scaleDefaults.ticks,
          callback: (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
        },
        grid: {
          ...scaleDefaults.grid,
          color: (ctx) =>
            ctx.tick.value === 0 ? 'rgba(255,255,255,0.18)' : C.borderDim,
        },
      },
    },
  };

  return (
    <div className="cg-card">
      <div className="cg-card-head">
        <span className="cg-card-title">Unrealised P&amp;L</span>
        <span className="cg-card-sub">per holding</span>
      </div>
      <Bar data={data} options={options} />
    </div>
  );
}

// ── Line: 6-month portfolio value ─────────────────────────────────────────────

function HistoryLine({ token }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(false);
  const chartRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/portfolios/histories`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { if (d.dates) setHistory(d); else setError(true); })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return (
    <div className="cg-card cg-card-line">
      <div className="cg-card-head">
        <span className="cg-card-title">Portfolio Value</span>
        <span className="cg-card-sub">6 months</span>
      </div>
      <div className="cg-loading"><div className="spinner" style={{ width:24, height:24, borderWidth:2, margin:0 }} /></div>
    </div>
  );

  if (error || !history) return (
    <div className="cg-card cg-card-line">
      <div className="cg-card-head">
        <span className="cg-card-title">Portfolio Value</span>
      </div>
      <div className="cg-empty">History not available — add holdings to generate this chart</div>
    </div>
  );

  const values = history.values;
  const first  = values[0] ?? 0;
  const last   = values[values.length - 1] ?? 0;
  const isUp   = last >= first;
  const lineColor = isUp ? C.green : C.red;

  const data = {
    labels: history.dates,
    datasets: [{
      label: 'Portfolio ₹',
      data: values,
      borderColor: lineColor,
      borderWidth: 2,
      backgroundColor: (ctx) => {
        if (!ctx.chart.chartArea) return 'transparent';
        const { top, bottom } = ctx.chart.chartArea;
        const g = ctx.chart.ctx.createLinearGradient(0, top, 0, bottom);
        g.addColorStop(0, isUp ? 'rgba(34,197,94,0.22)' : 'rgba(239,68,68,0.22)');
        g.addColorStop(1, 'rgba(0,0,0,0)');
        return g;
      },
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: lineColor,
      pointHoverBorderColor: C.bgSurface,
      pointHoverBorderWidth: 2,
    }],
  };

  const options = {
    responsive: true,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        ...tooltipDefaults,
        callbacks: {
          label: (ctx) =>
            ` ₹${Number(ctx.parsed.y).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
        },
      },
    },
    scales: {
      x: {
        ...scaleDefaults,
        ticks: {
          ...scaleDefaults.ticks,
          maxTicksLimit: 7,
        },
      },
      y: {
        ...scaleDefaults,
        position: 'right',
        ticks: {
          ...scaleDefaults.ticks,
          maxTicksLimit: 5,
          callback: (v) => {
            if (Math.abs(v) >= 1e7) return `₹${(v/1e7).toFixed(1)}Cr`;
            if (Math.abs(v) >= 1e5) return `₹${(v/1e5).toFixed(1)}L`;
            return `₹${(v/1e3).toFixed(0)}K`;
          },
        },
      },
    },
  };

  return (
    <div className="cg-card cg-card-line">
      <div className="cg-card-head">
        <span className="cg-card-title">Portfolio Value</span>
        <span className="cg-card-sub">6-month history (weekly)</span>
        <span className={`cg-card-pnl ${isUp ? 'up' : 'down'}`}>
          {isUp ? '+' : ''}₹{Number(last - first).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
        </span>
      </div>
      <Line ref={chartRef} data={data} options={options} />
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export default function Chartgen({ portfolio }) {
  const token = localStorage.getItem('token');

  return (
    <div className="cg-wrap">
      <div className="cg-header">
        <span className="cg-section-title">Visual Insights</span>
      </div>

      <div className="cg-top-row">
        <HoldingsDonut portfolio={portfolio} />
        <PnLBar        portfolio={portfolio} />
      </div>

      <HistoryLine token={token} />
    </div>
  );
}
