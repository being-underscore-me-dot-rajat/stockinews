import React, { useCallback, useEffect, useState } from 'react';
import './portfoliopage.css';
import { API_BASE }   from '../lib/api';
import Tip            from '../lib/Tip';
import AgentChat      from '../lib/AgentChat';
import Dropdown       from '../home/dropdown/Dropdown';
import Chartgen       from './chartgen';
import Navbar         from '../home/navbar/Navbar';
import { Link }       from 'react-router-dom';
import Footer         from '../home/navbar/footer/Footer';

const fmtRs = (n) =>
  n == null ? '—' : '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });

export default function Portfoliopage() {
  const [portfolio,    setPortfolio]    = useState([]);
  const [formData,     setFormData]     = useState({ ticker: '', quantity: '', price: '' });
  const [showAddForm,  setShowAddForm]  = useState(false);
  const [sellForms,    setSellForms]    = useState({});
  const [message,      setMessage]      = useState('');
  const [loading,      setLoading]      = useState(true);
  const token = localStorage.getItem('token');

  const fetchPortfolio = useCallback(() => {
    fetch(`${API_BASE}/api/portfolios`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => {
        if (d.portfolio) setPortfolio(d.portfolio);
        else setMessage(d.error || 'Failed to load portfolio');
      })
      .catch(() => setMessage('Error loading portfolio'))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => { fetchPortfolio(); }, [fetchPortfolio]);

  const invested = portfolio.reduce((s, x) => s + x.quantity * (x.avg_price || 0), 0);
  const current  = portfolio.reduce((s, x) => s + x.quantity * (x.current_price || 0), 0);
  const pnl      = current - invested;
  const pnlPct   = invested ? (pnl / invested) * 100 : 0;
  const isUp     = pnl >= 0;

  const handleAdd = (e) => {
    e.preventDefault();
    fetch(`${API_BASE}/api/portfolios/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ ...formData, action: 'BUY' }),
    })
      .then(r => r.json())
      .then(d => {
        setMessage(d.message || d.error);
        if (d.message) { setFormData({ ticker: '', quantity: '', price: '' }); setShowAddForm(false); fetchPortfolio(); }
      })
      .catch(() => setMessage('Error adding stock'));
  };

  const handleSell = (ticker, quantity, price) => {
    fetch(`${API_BASE}/api/portfolios/sell`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ ticker, quantity, price }),
    })
      .then(r => r.json())
      .then(d => {
        setMessage(d.message || d.error);
        if (d.message) { setSellForms({ ...sellForms, [ticker]: false }); fetchPortfolio(); }
      })
      .catch(() => setMessage('Error selling stock'));
  };

  const downloadHistory = () => {
    fetch(`${API_BASE}/api/portfolios/history`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (!r.ok) throw new Error('Failed to download PDF'); return r.blob(); })
      .then(blob => {
        const url  = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'portfolio_history.pdf');
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      })
      .catch(err => setMessage(err.message));
  };

  if (loading) {
    return (
      <div className="page-loader">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <div className="portfolio-container">

        {/* ── Header + Summary bar ─────────────────────────── */}
        <div className="pp-header">
          <div className="pp-header-accent" />
          <div className="pp-header-inner">
            <div className="pp-title-block">
              <h1 className="pp-page-title">Portfolio</h1>
              <span className="pp-page-sub">{portfolio.length} holding{portfolio.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="pp-summary">
              <div className="pp-stat">
                <span className="pp-stat-label">Invested <Tip text="Sum of quantity × average buy price" /></span>
                <span className="pp-stat-value">{fmtRs(invested)}</span>
              </div>
              <div className="pp-stat">
                <span className="pp-stat-label">Current Value <Tip text="Sum of quantity × current market price" /></span>
                <span className="pp-stat-value">{fmtRs(current)}</span>
              </div>
              <div className="pp-stat">
                <span className="pp-stat-label">P&amp;L <Tip text="Unrealised profit/loss across all holdings" /></span>
                <span className={`pp-stat-value ${isUp ? 'up' : 'down'}`}>
                  {isUp ? '+' : '−'}{fmtRs(Math.abs(pnl))}
                </span>
              </div>
              <div className="pp-stat">
                <span className="pp-stat-label">Return</span>
                <span className={`pp-stat-value ${isUp ? 'up' : 'down'}`}>
                  {isUp ? '+' : ''}{pnlPct.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {message && <div className="pp-message">{message}</div>}

        {/* ── Holdings table ───────────────────────────────── */}
        <div className="pp-table-card">
          <div className="pp-table-head-strip">
            <span className="pp-table-head-label">Holdings</span>
            <div className="pp-table-actions">
              <button className="pp-btn pp-btn-primary" onClick={() => setShowAddForm(s => !s)}>
                {showAddForm ? '✕ Cancel' : '+ Add Stock'}
              </button>
              <button className="pp-btn pp-btn-ghost" onClick={downloadHistory}>
                ↓ PDF
              </button>
            </div>
          </div>

          <div className="pp-table-scroll">
            <table className="pp-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th className="right">Qty <Tip text="Net shares held after all buys and sells" /></th>
                  <th className="right">Avg Buy <Tip text="Average cost basis per share" /></th>
                  <th className="right">Current <Tip text="Latest NSE market price" /></th>
                  <th className="right">P&amp;L <Tip text="(Current − Avg Buy) × Quantity" /></th>
                  <th className="right">Return</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {portfolio.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign:'center', padding:'2.5rem', color:'var(--text-muted)', fontFamily:'var(--font-mono)', fontSize:'12px' }}>
                      No holdings. Click + Add Stock to get started.
                    </td>
                  </tr>
                ) : portfolio.map((item) => {
                  const profit    = (item.current_price - item.avg_price) * item.quantity;
                  const retPct    = item.avg_price ? ((item.current_price - item.avg_price) / item.avg_price * 100) : 0;
                  const isItemUp  = profit >= 0;
                  const showSell  = sellForms[item.ticker];

                  return (
                    <React.Fragment key={item.ticker}>
                      <tr>
                        <td>
                          <Link to={`/company-page?company=${item.ticker}`} className="pp-ticker-link">
                            {item.ticker?.replace('.NS', '')}
                          </Link>
                        </td>
                        <td className="right">{item.quantity}</td>
                        <td className="right">{fmtRs(item.avg_price)}</td>
                        <td className="right">{fmtRs(item.current_price)}</td>
                        <td className={`right ${isItemUp ? 'pp-pnl-pos' : 'pp-pnl-neg'}`}>
                          {isItemUp ? '+' : '−'}{fmtRs(Math.abs(profit))}
                        </td>
                        <td className={`right ${isItemUp ? 'pp-pnl-pos' : 'pp-pnl-neg'}`}>
                          {isItemUp ? '+' : ''}{retPct.toFixed(2)}%
                        </td>
                        <td className="right">
                          <button
                            className="pp-btn pp-btn-sell"
                            onClick={() => setSellForms({ ...sellForms, [item.ticker]: !showSell })}
                          >
                            {showSell ? 'Cancel' : 'Sell'}
                          </button>
                        </td>
                      </tr>
                      {showSell && (
                        <tr className="pp-sell-row">
                          <td colSpan="7">
                            <form
                              className="pp-sell-form"
                              onSubmit={(e) => {
                                e.preventDefault();
                                handleSell(item.ticker, e.target.quantity.value, e.target.price.value);
                              }}
                            >
                              <span style={{ fontSize:12, color:'var(--text-secondary)', marginRight:4 }}>
                                Selling {item.ticker?.replace('.NS', '')}
                              </span>
                              <input className="pp-sell-input" name="quantity" type="number" placeholder="Qty" required min={1} max={item.quantity} />
                              <input className="pp-sell-input" name="price" type="number" step="0.01" placeholder="Price ₹" required min={0.01} />
                              <button type="submit" className="pp-btn pp-btn-sell">Confirm Sell</button>
                            </form>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Add stock form ───────────────────────────────── */}
        {showAddForm && (
          <div className="pp-add-card">
            <div className="pp-add-card-head">Add New Position</div>
            <form className="pp-add-form" onSubmit={handleAdd}>
              <div>
                <span className="pp-add-label">Company</span>
                <Dropdown onSelect={(c) => setFormData({ ...formData, ticker: c })} />
              </div>
              <div>
                <span className="pp-add-label">Quantity</span>
                <input
                  className="pp-add-input"
                  type="number"
                  placeholder="e.g. 10"
                  value={formData.quantity}
                  onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                  required
                  min={1}
                />
              </div>
              <div>
                <span className="pp-add-label">Buy Price ₹</span>
                <input
                  className="pp-add-input"
                  type="number"
                  step="0.01"
                  placeholder="e.g. 2840.50"
                  value={formData.price}
                  onChange={e => setFormData({ ...formData, price: e.target.value })}
                  required
                  min={0.01}
                />
              </div>
              <div style={{ display:'flex', gap:'0.4rem', alignItems:'flex-end' }}>
                <button type="submit" className="pp-btn pp-btn-primary" style={{ height:34 }}>Add</button>
                <button type="button" className="pp-btn pp-btn-ghost" style={{ height:34 }} onClick={() => setShowAddForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        )}

        {/* ── Charts ──────────────────────────────────────── */}
        <Chartgen portfolio={portfolio} />

        {/* ── AI Chat ─────────────────────────────────────── */}
        <AgentChat portfolioMode={true} />

      </div>
      <Footer />
    </>
  );
}
