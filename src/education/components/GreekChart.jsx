/**
 * Option Greek chart — renders Delta/Theta/Gamma/Vega curves from
 * /education/chart/greek/{greek} endpoint.
 * Mathematical curves, not live data. No ticker selector needed.
 */
import React, { useEffect, useState } from 'react';
import { Chart, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { C, tooltipDefaults, scaleDefaults } from '../../lib/chartTheme';
import { API_BASE } from '../../lib/api';

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const GREEK_COLORS = ['#00d296', '#5ab4e5', '#f59e0b', '#a855f7', '#ef4444', '#22c55e'];

export default function GreekChart({ greekName }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/education/chart/greek/${greekName}`)
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setError(true); setLoading(false); });
  }, [greekName]);

  if (loading) return <div className="gc-skeleton" />;
  if (error || !data) return <div className="gc-error">Could not load {greekName} curve</div>;
  if (data.error) return <div className="gc-error">{data.error}</div>;
  if (!data.series || data.series.length === 0) return <div className="gc-error">No curve data available</div>;

  const datasets = (data.series || []).map((s, i) => ({
    label: s.label,
    data: s.values,
    borderColor: GREEK_COLORS[i % GREEK_COLORS.length],
    borderWidth: s.tte === 0.25 ? 2.5 : s.tte === 0.08 ? 1.8 : 1.2,
    pointRadius: 0,
    tension: 0.4,
    fill: false,
    borderDash: s.type === 'put' ? [5, 4] : undefined,
  }));

  // Annotation for ATM line
  const xLabels = data.x || [];
  const atmIdx = xLabels.findIndex(v => v === 100 || (v > 99 && v < 101));

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      tooltip: {
        ...tooltipDefaults,
        callbacks: {
          title: ctx => `${data.x_label}: ${xLabels[ctx[0]?.dataIndex]}`,
        },
      },
      legend: { display: true, position: 'top', align: 'end' },
    },
    scales: {
      x: {
        ...scaleDefaults,
        ticks: {
          ...scaleDefaults.ticks,
          maxTicksLimit: 10,
          callback: (_, i) => xLabels[i] !== undefined ? xLabels[i] : '',
        },
      },
      y: {
        ...scaleDefaults,
        title: {
          display: true,
          text: data.y_label,
          color: C.textMuted,
          font: { family: C.fontSans, size: 10 },
        },
      },
    },
  };

  return (
    <div className="gc-container">
      <div className="gc-canvas-wrap">
        <Line
          data={{ labels: xLabels, datasets }}
          options={options}
        />
      </div>

      {data.annotations && (
        <div className="gc-annotations">
          {data.annotations.map((a, i) => (
            <span key={i} className="gc-annotation" style={{ borderColor: a.color }}>
              <span className="gc-ann-dot" style={{ background: a.color }} />
              {a.label} (x={a.x})
            </span>
          ))}
        </div>
      )}

      {data.key_insight && (
        <div className="gc-insight">
          <span className="gc-insight-icon">◈</span>
          <span>{data.key_insight}</span>
        </div>
      )}
    </div>
  );
}
