/**
 * AI Tutor slide-up panel — sends questions to /education/ask with optional
 * chart context (current indicator data + interpretation).
 */
import React, { useState, useRef, useEffect } from 'react';
import { API_BASE } from '../../lib/api';
import './tutorPanel.css';

const STARTERS = [
  'Why does RSI stay overbought in strong uptrends?',
  'Explain the difference between MACD line and histogram.',
  'Why do options buyers lose money even when directionally correct?',
  'What is IV crush and when does it happen?',
  'How do professionals use ATR for position sizing?',
  'What is a Bollinger squeeze and why does it matter?',
];

export default function TutorPanel({ open, onClose, chartContext }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 200);
    }
  }, [open]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const send = async (text) => {
    const q = (text || input).trim();
    if (!q || loading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/education/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, context: chartContext || null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'ai', text: data.answer }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'error',
        text: 'The tutor is unavailable right now. Make sure the backend is running.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className={`tp-backdrop ${open ? 'tp-open' : ''}`} onClick={e => { if (e.target.classList.contains('tp-backdrop')) onClose(); }}>
      <div className={`tp-panel ${open ? 'tp-panel-open' : ''}`} role="dialog" aria-label="AI Tutor">

        {/* Header */}
        <div className="tp-header">
          <div className="tp-header-left">
            <span className="tp-header-icon">◈</span>
            <div>
              <div className="tp-header-title">AI Chart Tutor</div>
              <div className="tp-header-sub">Ask about any financial concept, indicator, or option Greek</div>
            </div>
          </div>
          <button className="tp-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {chartContext && (
          <div className="tp-context-banner">
            <span className="tp-ctx-icon">◉</span>
            Chart context active: <strong>{chartContext.indicator?.toUpperCase()}</strong>
            {chartContext.ticker && <> · <strong>{chartContext.ticker}</strong></>}
          </div>
        )}

        {/* Messages */}
        <div className="tp-messages">
          {messages.length === 0 && (
            <div className="tp-starters">
              <div className="tp-starters-label">Ask about the chart — or try a starter:</div>
              <div className="tp-starters-grid">
                {STARTERS.map((s, i) => (
                  <button key={i} className="tp-starter-btn" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`tp-msg tp-msg-${m.role}`}>
              {m.role === 'ai' && <span className="tp-ai-icon">◈</span>}
              <div className="tp-msg-body">
                {m.text.split('\n').map((line, j) => (
                  <React.Fragment key={j}>
                    {line}
                    {j < m.text.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </div>
            </div>
          ))}

          {loading && (
            <div className="tp-msg tp-msg-ai tp-loading-msg">
              <span className="tp-ai-icon">◈</span>
              <div className="tp-typing">
                <span /><span /><span />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="tp-input-row">
          <textarea
            ref={inputRef}
            className="tp-input"
            placeholder="Ask about any concept or chart signal…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={2}
            disabled={loading}
          />
          <button
            className="tp-send"
            onClick={() => send()}
            disabled={!input.trim() || loading}
            aria-label="Send"
          >
            →
          </button>
        </div>
        <div className="tp-disclaimer">Educational only — not financial advice.</div>
      </div>
    </div>
  );
}
