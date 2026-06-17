import React, { useCallback, useEffect, useState } from 'react';
import './watchlist.css';
import Dropdown from '../../../home/dropdown/Dropdown';
import { Link } from 'react-router-dom';
import { API_BASE } from '../../../lib/api';
import Tip from '../../../lib/Tip';

const CACHE_TTL = 8 * 60 * 60 * 1000;
const cacheKey  = (t) => `dashboard-watchlist-open-v5:${t?.slice(-12) || 'guest'}`;

const getCache = (token) => {
  try {
    const c = JSON.parse(localStorage.getItem(cacheKey(token)) || 'null');
    if (!c || Date.now() - c.savedAt > CACHE_TTL) return null;
    return Array.isArray(c.data) ? c.data : null;
  } catch { return null; }
};

const setCache = (token, data) => {
  try { localStorage.setItem(cacheKey(token), JSON.stringify({ savedAt: Date.now(), data })); }
  catch {}
};

export default function Watchlist() {
  const [watchlist,    setWatchlist]    = useState([]);
  const [newSymbol,    setNewSymbol]    = useState('');
  const [loading,      setLoading]      = useState(true);
  const [resetTrigger, setResetTrigger] = useState(false);
  const token = localStorage.getItem('token');

  const fetchWatchlist = useCallback(async () => {
    const cached = getCache(token);
    if (cached) { setWatchlist(cached); setLoading(false); }
    try {
      const res  = await fetch(`${API_BASE}/watchlist`, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (res.ok) { setWatchlist(data || []); setCache(token, data || []); }
    } catch {}
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetchWatchlist(); }, [fetchWatchlist]);

  const addSymbol = async () => {
    if (!newSymbol.trim()) return;
    await fetch(`${API_BASE}/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ symbol: newSymbol.toUpperCase() }),
    });
    setNewSymbol('');
    setResetTrigger(p => !p);
    localStorage.removeItem(cacheKey(token));
    fetchWatchlist();
  };

  const removeSymbol = async (symbol) => {
    await fetch(`${API_BASE}/watchlist/${symbol}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    localStorage.removeItem(cacheKey(token));
    setWatchlist(prev => prev.filter(i => i.symbol !== symbol));
  };

  return (
    <div className="db-panel">
      <div className="db-panel-accent" />
      <div className="db-panel-header">
        <span className="db-panel-name">Watchlist</span>
        <span className="db-panel-badge">{watchlist.length} stocks</span>
      </div>

      {/* Add row */}
      <div className="wl-add-row">
        <Dropdown onSelect={setNewSymbol} resetTrigger={resetTrigger} />
        <button className="wl-add-btn" onClick={addSymbol}>+ Add</button>
      </div>

      <div className="db-panel-body">
        {loading ? (
          <div style={{ display:'flex', justifyContent:'center', padding:'2rem' }}>
            <div className="spinner" style={{ width:24, height:24, borderWidth:2, margin:0 }} />
          </div>
        ) : watchlist.length === 0 ? (
          <div className="wl-empty">
            <div>No stocks added yet</div>
            <p>Search above and click + Add</p>
          </div>
        ) : (
          watchlist.map((item) => (
            <div key={item.symbol} className="wl-row">
              <Link to={`/company-page?company=${item.symbol}`} className="wl-ticker">
                {item.symbol?.replace('.NS', '')}
              </Link>
              <span className="wl-name">{item.name || '—'}</span>
              <div className="wl-price-cell">
                <span className="wl-price">
                  {item.open_price != null ? `₹${item.open_price.toLocaleString('en-IN')}` : '—'}
                  <Tip text="Today's NSE opening price" />
                </span>
                <span className="wl-price-sub">Open</span>
              </div>
              <button className="wl-remove" onClick={() => removeSymbol(item.symbol)} title="Remove">×</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
