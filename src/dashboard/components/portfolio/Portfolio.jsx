import React, { useEffect, useState } from 'react';
import { API_BASE } from '../../../lib/api';
import Tip from '../../../lib/Tip';
import { useNavigate } from 'react-router-dom';
import './portfolio.css';

const fmt = (n) =>
  n == null ? '—' : '₹' + Math.abs(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState([]);
  const [loading,   setLoading]   = useState(true);
  const token    = localStorage.getItem('token');
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API_BASE}/api/portfolios`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { if (d.portfolio) setPortfolio(d.portfolio); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  const invested = portfolio.reduce((s, x) => s + x.quantity * (x.avg_price || 0), 0);
  const current  = portfolio.reduce((s, x) => s + x.quantity * (x.current_price || 0), 0);
  const pnl      = current - invested;
  const pnlPct   = invested ? (pnl / invested) * 100 : 0;
  const isUp     = pnl >= 0;

  return (
    <div
      className="pb-card"
      onClick={() => navigate('/portfolio')}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && navigate('/portfolio')}
    >
      <div className="pb-accent" />
      <div className="pb-inner">
        <div className="pb-left">
          <span className="pb-eyebrow">Portfolio Overview</span>
          <span className="pb-hint">Click to view full portfolio →</span>
        </div>

        {loading ? (
          <div className="pb-loading"><div className="spinner" style={{ margin: 0, width: 20, height: 20, borderWidth: 2 }} /></div>
        ) : (
          <div className="pb-stats">
            <div className="pb-stat">
              <span className="pb-stat-label">Invested <Tip text="Sum of quantity × avg buy price" /></span>
              <span className="pb-stat-value">{fmt(invested)}</span>
            </div>
            <div className="pb-divider" />
            <div className="pb-stat">
              <span className="pb-stat-label">Current Value <Tip text="Sum of quantity × current market price" /></span>
              <span className="pb-stat-value">{fmt(current)}</span>
            </div>
            <div className="pb-divider" />
            <div className="pb-stat">
              <span className="pb-stat-label">P&amp;L <Tip text="Unrealised profit/loss" /></span>
              <span className={`pb-stat-value pb-stat-pnl ${isUp ? 'up' : 'down'}`}>
                {isUp ? '+' : '−'}{fmt(Math.abs(pnl))}
              </span>
            </div>
            <div className="pb-divider" />
            <div className="pb-stat">
              <span className="pb-stat-label">Return</span>
              <span className={`pb-stat-value pb-stat-pnl ${isUp ? 'up' : 'down'}`}>
                {isUp ? '+' : ''}{pnlPct.toFixed(2)}%
              </span>
            </div>
            <div className="pb-divider" />
            <div className="pb-stat">
              <span className="pb-stat-label">Holdings</span>
              <span className="pb-stat-value">{portfolio.length}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
