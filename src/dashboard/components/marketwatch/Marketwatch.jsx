import React, { useEffect, useState } from 'react';
import './marketwatch.css';
import { API_BASE } from '../../../lib/api';
import Tip from '../../../lib/Tip';

const GROUPS = {
  index:     ["^GSPC","^DJI","^IXIC","^FTSE","^GDAXI","^FCHI","^N225","^HSI","000001.SS","^NSEI"],
  commodity: ["GC=F","SI=F","CL=F","BZ=F","NG=F","HG=F"],
};

const CACHE_KEY = 'dashboard-market-open-v1';
const CACHE_TTL = 8 * 60 * 60 * 1000;

const getCache = () => {
  try {
    const c = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
    if (!c || Date.now() - c.savedAt > CACHE_TTL) return null;
    return Array.isArray(c.data) ? c.data : null;
  } catch { return null; }
};

const setCache = (data) => {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify({ savedAt: Date.now(), data })); }
  catch {}
};

export default function MarketWatch() {
  const [data,       setData]       = useState([]);
  const [search,     setSearch]     = useState('');
  const [sortKey,    setSortKey]    = useState('name');
  const [sortAsc,    setSortAsc]    = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [loading,    setLoading]    = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    const cached = getCache();
    if (cached) { setData(cached); setLoading(false); }
    fetch(`${API_BASE}/marketwatch`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => { const m = d.market || []; setData(m); setCache(m); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [token]);

  const group = (sym) => {
    if (GROUPS.index.includes(sym))     return 'index';
    if (GROUPS.commodity.includes(sym)) return 'commodity';
    return 'other';
  };

  const filtered = [...data]
    .filter(i => {
      const q = search.toLowerCase();
      return !q || i.name?.toLowerCase().includes(q) || i.symbol?.toLowerCase().includes(q);
    })
    .filter(i => filterType === 'all' || group(i.symbol) === filterType)
    .sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey];
      if (va == null) return 1;
      if (vb == null) return -1;
      return sortAsc
        ? (typeof va === 'string' ? va.localeCompare(vb) : va - vb)
        : (typeof va === 'string' ? vb.localeCompare(va) : vb - va);
    });

  return (
    <div className="db-panel">
      <div className="db-panel-accent" />
      <div className="db-panel-header">
        <span className="db-panel-name">Market Watch</span>
        <span className="db-panel-badge">{filtered.length} shown</span>
      </div>

      {/* Controls */}
      <div className="mw-controls">
        <input
          className="mw-input"
          type="text"
          placeholder="Search markets…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select className="mw-select" value={filterType} onChange={e => setFilterType(e.target.value)}>
          <option value="all">All</option>
          <option value="index">Indices</option>
          <option value="commodity">Commodities</option>
        </select>
        <select className="mw-select" value={sortKey} onChange={e => setSortKey(e.target.value)}>
          <option value="name">Name</option>
          <option value="open_price">Price</option>
        </select>
        <button className="mw-sort" onClick={() => setSortAsc(a => !a)}>
          {sortAsc ? '↑' : '↓'}
        </button>
      </div>

      <div className="db-panel-body">
        {loading ? (
          <div style={{ display:'flex', justifyContent:'center', padding:'2.5rem' }}>
            <div className="spinner" style={{ width:28, height:28, borderWidth:2, margin:0 }} />
          </div>
        ) : filtered.length === 0 ? (
          <div className="mw-empty">No results for "{search}"</div>
        ) : (
          <table className="mw-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th className="mw-right">Open <Tip text="Today's opening price at market open" /></th>
                <th className="mw-right">Type</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item, i) => {
                const g = group(item.symbol);
                return (
                  <tr key={item.symbol || i}>
                    <td><span className="mw-sym">{item.symbol}</span></td>
                    <td><span className="mw-name">{item.name || item.symbol}</span></td>
                    <td className="mw-right">
                      <span className="mw-price">
                        {item.open_price != null ? item.open_price.toLocaleString('en-IN') : '—'}
                      </span>
                    </td>
                    <td className="mw-right">
                      <span className={`mw-tag mw-tag-${g}`}>
                        {g === 'index' ? 'Index' : g === 'commodity' ? 'Commod.' : 'Other'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
