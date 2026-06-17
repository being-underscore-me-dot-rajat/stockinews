import React, { useState } from 'react';
import { API_BASE } from './api';
import './agentchat.css';

export default function AgentChat({ ticker = null, portfolioMode = false }) {
    const [question, setQuestion] = useState('');
    const [result, setResult]     = useState(null);
    const [loading, setLoading]   = useState(false);
    const [error, setError]       = useState(null);
    const token = localStorage.getItem('token');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!question.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);
        try {
            const endpoint = portfolioMode ? '/api/agent/portfolio' : '/api/agent/query';
            const body = portfolioMode ? { question } : { ticker, question };
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Request failed');
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const placeholder = portfolioMode
        ? 'Ask about your portfolio, e.g. "Which of my holdings have the most positive news?"'
        : `Ask about ${ticker}, e.g. "What is the latest news and outlook?"`;

    return (
        <section className="container agent-chat">
            <h4 className="agent-title">AI Analyst</h4>
            <form className="agent-form" onSubmit={handleSubmit}>
                <input
                    className="agent-input"
                    value={question}
                    onChange={e => setQuestion(e.target.value)}
                    placeholder={placeholder}
                    disabled={loading}
                />
                <button className="agent-submit" type="submit" disabled={loading || !question.trim()}>
                    {loading ? 'Analyzing…' : 'Ask'}
                </button>
            </form>

            {error && <p className="agent-error">{error}</p>}
            {loading && <div className="agent-loading"><div className="spinner" /></div>}
            {result && !loading && <AgentResult result={result} />}
        </section>
    );
}

function AgentResult({ result }) {
    const sentimentClass = {
        Bullish: 'sentiment-bullish',
        Bearish: 'sentiment-bearish',
        Neutral: 'sentiment-neutral',
    }[result.sentiment] || 'sentiment-neutral';

    const confidence = Math.round((result.confidence || 0) * 100);

    return (
        <div className="agent-result">
            <div className="agent-result-header">
                <span className={`agent-sentiment ${sentimentClass}`}>{result.sentiment || 'Neutral'}</span>
                <span className="agent-confidence">{confidence}% confidence</span>
            </div>

            {result.summary && (
                <p className="agent-summary">{result.summary}</p>
            )}

            {result.key_themes?.length > 0 && (
                <div className="agent-themes">
                    {result.key_themes.map((t, i) => (
                        <span key={i} className="theme-chip">{t}</span>
                    ))}
                </div>
            )}

            {result.directional_impact && (
                <p className="agent-impact">{result.directional_impact}</p>
            )}

            {result.sources?.length > 0 && (
                <div className="agent-sources">
                    <h6>Sources</h6>
                    {result.sources.map((s, i) => (
                        <a
                            key={i}
                            href={s.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-link"
                        >
                            {s.title || s.url}
                            {s.source && <em> — {s.source}</em>}
                        </a>
                    ))}
                </div>
            )}
        </div>
    );
}
