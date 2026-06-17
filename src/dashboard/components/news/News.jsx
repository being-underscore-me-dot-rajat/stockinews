import React, { useEffect, useState } from 'react';
import './News.css';
import { API_BASE } from '../../../lib/api';

const fmt = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  } catch { return ''; }
};

export default function News() {
  const [news,    setNews]    = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/news`)
      .then(r => r.json())
      .then(d => { if (d.news) setNews(d.news); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="db-panel">
      <div className="db-panel-accent" />
      <div className="db-panel-header">
        <span className="db-panel-name">Market News</span>
        {!loading && <span className="db-panel-badge">{news.length}</span>}
      </div>

      <div className="db-panel-body">
        {loading ? (
          <div style={{ display:'flex', justifyContent:'center', padding:'2.5rem' }}>
            <div className="spinner" style={{ width:28, height:28, borderWidth:2, margin:0 }} />
          </div>
        ) : news.length === 0 ? (
          <div className="nw-empty">No news available</div>
        ) : (
          news.map((article, i) => (
            <div key={i} className="nw-item">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="nw-title"
              >
                {article.title}
              </a>
              <div className="nw-meta">
                {article.source?.name && (
                  <span className="nw-source">{article.source.name}</span>
                )}
                {article.publishedAt && (
                  <span className="nw-date">{fmt(article.publishedAt)}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
