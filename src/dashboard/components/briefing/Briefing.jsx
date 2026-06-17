import React, { useState } from 'react';
import { API_BASE } from '../../../lib/api';
import './briefing.css';

export default function Briefing() {
  const [briefing, setBriefing] = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [fetched,  setFetched]  = useState(false);
  const [error,    setError]    = useState(null);
  const token = localStorage.getItem('token');

  const fetchBriefing = async () => {
    setLoading(true);
    setError(null);
    try {
      const res  = await fetch(`${API_BASE}/api/agent/briefing`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to generate briefing');
      setBriefing(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setFetched(true);
    }
  };

  const sentClass = {
    Bullish: 'br-bull', Bearish: 'br-bear', Neutral: 'br-neut',
  }[briefing?.sentiment] || 'br-neut';

  return (
    <div className="db-panel">
      <div className="db-panel-accent" />
      <div className="db-panel-header">
        <span className="db-panel-name">AI Briefing</span>
        <button className="br-gen-btn" onClick={fetchBriefing} disabled={loading}>
          {loading ? 'Generating…' : fetched ? '↻ Refresh' : 'Generate'}
        </button>
      </div>

      <div className="db-panel-body br-body">
        {!fetched && !loading && (
          <div className="br-idle">
            <span className="br-idle-icon">⚡</span>
            <p>AI-powered market briefing for your watchlist.</p>
            <small>Click Generate to analyse latest news</small>
          </div>
        )}

        {loading && (
          <div className="br-loading">
            <div className="spinner" style={{ width: 24, height: 24, borderWidth: 2, margin: 0 }} />
            <span>Analysing watchlist…</span>
          </div>
        )}

        {error && <div className="br-error">{error}</div>}

        {briefing && !loading && (
          <div className="br-result">
            <div className="br-result-head">
              <span className={`br-sent ${sentClass}`}>{briefing.sentiment}</span>
              <span className="br-conf">{Math.round((briefing.confidence || 0) * 100)}% confidence</span>
              {briefing.key_themes?.slice(0, 3).map((t, i) => (
                <span key={i} className="br-theme">{t}</span>
              ))}
            </div>

            {briefing.summary && (
              <p className="br-summary">{briefing.summary}</p>
            )}

            {briefing.directional_impact && (
              <p className="br-impact">{briefing.directional_impact}</p>
            )}

            {briefing.sources?.length > 0 && (
              <div className="br-sources">
                <span className="br-sources-label">Sources</span>
                {briefing.sources.slice(0, 3).map((s, i) => (
                  <a key={i} href={s.url} target="_blank" rel="noopener noreferrer" className="br-src-link">
                    {s.title || s.url}
                    {s.source && <em> — {s.source}</em>}
                  </a>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
