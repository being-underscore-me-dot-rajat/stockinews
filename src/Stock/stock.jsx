import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import './stock.css';
import Navbar from '../home/navbar/Navbar';
import Footer from '../home/navbar/footer/Footer';
import { Chart } from 'chart.js/auto';
import annotationPlugin from 'chartjs-plugin-annotation';
Chart.register(annotationPlugin);
import { API_BASE } from '../lib/api';
import Tip from '../lib/Tip';
import AgentChat from '../lib/AgentChat';
import { C, makeGradient, tooltipDefaults, scaleDefaults } from '../lib/chartTheme';

const CHART_CACHE_TTL_MS = 6 * 60 * 60 * 1000;
const CHART_CACHE_VERSION = 'v3';

// ── Formatters ────────────────────────────────────────────────────────────────

const fmt = (n, digits = 2) =>
    n == null ? '-' : Number(n).toLocaleString('en-IN', { maximumFractionDigits: digits });

const fmtCr = (n) => {
    if (n == null) return '-';
    const cr = n / 1e7;
    if (cr >= 1e5) return `Rs. ${(cr / 1e5).toFixed(2)} L.Cr`;
    if (cr >= 1e3) return `Rs. ${(cr / 1e3).toFixed(2)} K.Cr`;
    return `Rs. ${cr.toFixed(2)} Cr`;
};

const fmtPct = (n) => (n == null ? '-' : `${(n * 100).toFixed(2)}%`);

const fmtDate = (iso) => {
    if (!iso) return '';
    try { return new Date(iso).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' }); }
    catch { return iso; }
};

const fmtNum = (n) => {
    if (n == null) return '-';
    const abs = Math.abs(n);
    if (abs >= 1e7) return `₹${(n / 1e7).toFixed(2)}Cr`;
    if (abs >= 1e5) return `₹${(n / 1e5).toFixed(2)}L`;
    if (abs >= 1000) return Number(n).toLocaleString('en-IN', { maximumFractionDigits: 2 });
    return Number(n).toFixed(2);
};

// ── Chart cache ───────────────────────────────────────────────────────────────

const chartCacheKey = (ticker, range) => `stock-chart:${CHART_CACHE_VERSION}:${ticker}:${range}`;

const getCachedChartData = (ticker, range) => {
    try {
        const cached = localStorage.getItem(chartCacheKey(ticker, range));
        if (!cached) return null;
        const parsed = JSON.parse(cached);
        if (!parsed.savedAt || Date.now() - parsed.savedAt > CHART_CACHE_TTL_MS) {
            localStorage.removeItem(chartCacheKey(ticker, range));
            return null;
        }
        return Array.isArray(parsed.data) ? parsed.data : null;
    } catch { return null; }
};

const setCachedChartData = (ticker, range, data) => {
    try {
        localStorage.setItem(chartCacheKey(ticker, range), JSON.stringify({ savedAt: Date.now(), data }));
    } catch { /* localStorage unavailable */ }
};

const simplifyChartData = (data, range) => {
    if (range !== 'max' || data.length <= 160) return data;
    const simplified = [data[0]];
    const step = (data.length - 2) / 158;
    for (let i = 1; i <= 158; i++) {
        const idx = Math.round(i * step);
        if (data[idx] && data[idx] !== simplified[simplified.length - 1]) simplified.push(data[idx]);
    }
    const last = data[data.length - 1];
    if (last && last !== simplified[simplified.length - 1]) simplified.push(last);
    return simplified;
};

const chartPointRadius = (range) => (range === 'max' ? 0 : 2);

// ── Client-side indicator computation ────────────────────────────────────────

function computeEMA(prices, period) {
    const k = 2 / (period + 1);
    const result = new Array(prices.length).fill(null);
    if (prices.length < period) return result;
    let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
    result[period - 1] = ema;
    for (let i = period; i < prices.length; i++) {
        ema = prices[i] * k + ema * (1 - k);
        result[i] = ema;
    }
    return result;
}

function computeSMA(prices, period) {
    const result = new Array(prices.length).fill(null);
    for (let i = period - 1; i < prices.length; i++) {
        let sum = 0;
        for (let j = i - period + 1; j <= i; j++) sum += prices[j];
        result[i] = sum / period;
    }
    return result;
}

function computeBollinger(prices, period = 20, mult = 2) {
    const mid = computeSMA(prices, period);
    const upper = new Array(prices.length).fill(null);
    const lower = new Array(prices.length).fill(null);
    for (let i = period - 1; i < prices.length; i++) {
        const mean = mid[i];
        let variance = 0;
        for (let j = i - period + 1; j <= i; j++) variance += (prices[j] - mean) ** 2;
        const std = Math.sqrt(variance / period);
        upper[i] = mean + mult * std;
        lower[i] = mean - mult * std;
    }
    return { upper, mid, lower };
}

function computeVWAP(ohlcv) {
    let cumVol = 0, cumPV = 0;
    return ohlcv.map(p => {
        const typical = ((p.High || p.Close) + (p.Low || p.Close) + p.Close) / 3;
        cumPV += typical * (p.Volume || 0);
        cumVol += p.Volume || 0;
        return cumVol > 0 ? cumPV / cumVol : null;
    });
}

function computeRSI(prices, period = 14) {
    const result = new Array(prices.length).fill(null);
    if (prices.length <= period) return result;
    let avgGain = 0, avgLoss = 0;
    for (let i = 1; i <= period; i++) {
        const diff = prices[i] - prices[i - 1];
        if (diff > 0) avgGain += diff; else avgLoss -= diff;
    }
    avgGain /= period; avgLoss /= period;
    result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    for (let i = period + 1; i < prices.length; i++) {
        const diff = prices[i] - prices[i - 1];
        avgGain = (avgGain * (period - 1) + Math.max(diff, 0)) / period;
        avgLoss = (avgLoss * (period - 1) + Math.max(-diff, 0)) / period;
        result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    return result;
}

function computeMACD(prices, fast = 12, slow = 26, signal = 9) {
    const emaFast = computeEMA(prices, fast);
    const emaSlow = computeEMA(prices, slow);
    const macd = prices.map((_, i) =>
        emaFast[i] != null && emaSlow[i] != null ? emaFast[i] - emaSlow[i] : null);
    const macdValues = [], macdIndices = [];
    macd.forEach((v, i) => { if (v != null) { macdValues.push(v); macdIndices.push(i); } });
    const sigValues = computeEMA(macdValues, signal);
    const sigFull = new Array(prices.length).fill(null);
    macdIndices.forEach((origIdx, j) => { sigFull[origIdx] = sigValues[j]; });
    const histogram = prices.map((_, i) =>
        macd[i] != null && sigFull[i] != null ? macd[i] - sigFull[i] : null);
    return { macd, signal: sigFull, histogram };
}

function computeStoch(ohlcv, k = 14, d = 3) {
    const kLine = new Array(ohlcv.length).fill(null);
    for (let i = k - 1; i < ohlcv.length; i++) {
        let low = Infinity, high = -Infinity;
        for (let j = i - k + 1; j <= i; j++) {
            if (ohlcv[j].Low < low) low = ohlcv[j].Low;
            if (ohlcv[j].High > high) high = ohlcv[j].High;
        }
        kLine[i] = high !== low ? ((ohlcv[i].Close - low) / (high - low)) * 100 : 50;
    }
    const kValues = [], kIndices = [];
    kLine.forEach((v, i) => { if (v != null) { kValues.push(v); kIndices.push(i); } });
    const dValues = computeSMA(kValues, d);
    const dLine = new Array(ohlcv.length).fill(null);
    kIndices.forEach((origIdx, j) => { dLine[origIdx] = dValues[j]; });
    return { k: kLine, d: dLine };
}

// ── Overlay / sub-panel config ────────────────────────────────────────────────

const OVERLAY_OPTIONS = [
    { key: 'ema20',    label: 'EMA 20',  color: '#60a5fa' },
    { key: 'ema50',    label: 'EMA 50',  color: '#fbbf24' },
    { key: 'ema200',   label: 'EMA 200', color: '#a78bfa' },
    { key: 'sma20',    label: 'SMA 20',  color: '#f97316' },
    { key: 'bollinger',label: 'BB(20)',   color: '#64748b' },
    { key: 'vwap',     label: 'VWAP',    color: '#34d399' },
];

const SUB_PANEL_OPTIONS = [
    { key: 'none',        label: 'None'       },
    { key: 'rsi',         label: 'RSI'        },
    { key: 'macd',        label: 'MACD'       },
    { key: 'stochastic',  label: 'Stochastic' },
    { key: 'volume',      label: 'Volume'     },
];

// ── Shared sub-components ─────────────────────────────────────────────────────

function Spinner() {
    return <div className="spinner-wrap"><div className="spinner" /></div>;
}

function Empty({ msg = 'No data available for this stock.' }) {
    return <p className="muted-text">{msg}</p>;
}

// Generic scrollable table
function DataTable({ rows, cols, renderCell, colTips = {} }) {
    if (!rows || !rows.length) return <Empty />;
    return (
        <div className="data-table-wrap">
            <table className="data-table">
                <thead>
                    <tr>{cols.map(c => <th key={c}>{c}{colTips[c] && <Tip text={colTips[c]} />}</th>)}</tr>
                </thead>
                <tbody>
                    {rows.map((row, i) => (
                        <tr key={i}>
                            {cols.map(c => <td key={c}>{renderCell ? renderCell(c, row[c]) : (row[c] ?? '-')}</td>)}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// ── Company info card — Bloomberg terminal style ──────────────────────────────

function CompanyInfoCard({ info }) {
    const [expanded, setExpanded] = useState(false);

    const sideMetrics = [
        { label: 'Market Cap', value: fmtCr(info.market_cap),                                            tip: 'Share price × shares outstanding — total equity value of the company.' },
        { label: 'P/E Ratio',  value: fmt(info.pe_ratio),                                                tip: 'Price ÷ Earnings per share. High P/E = growth expectations or possible overvaluation.' },
        { label: 'EPS',        value: info.eps       != null ? `₹${fmt(info.eps)}`       : '-',          tip: 'Net profit ÷ shares outstanding. Higher = more profitable per share.' },
        { label: '52W High',   value: info.week_52_high != null ? `₹${fmt(info.week_52_high)}` : '-',    tip: 'Highest closing price over the last 52 weeks.' },
        { label: '52W Low',    value: info.week_52_low  != null ? `₹${fmt(info.week_52_low)}`  : '-',    tip: 'Lowest closing price over the last 52 weeks.' },
        { label: 'Div. Yield', value: fmtPct(info.dividend_yield),                                       tip: 'Annual dividend ÷ share price.' },
        { label: 'Book Value', value: info.book_value != null ? `₹${fmt(info.book_value)}` : '-',        tip: 'Net assets per share. P/B < 1 may signal undervaluation.' },
    ];

    return (
        <div className="company-info-card">
            <div className="cci-accent" />

            {/* Header: name + tags */}
            <div className="cci-header">
                <div className="cci-identity">
                    <div className="cci-ticker">{info.symbol} · NSE</div>
                    <h1 className="cci-name">{info.name || info.symbol}</h1>
                </div>
                <div className="cci-tags">
                    {info.sector   && <span className="cci-tag">{info.sector}</span>}
                    {info.industry && <span className="cci-tag cci-tag-dim">{info.industry}</span>}
                </div>
            </div>

            {/* Data row: price + metrics */}
            <div className="cci-data-row">
                <div className="cci-price-block">
                    <span className="cci-price-label">Last Price</span>
                    <span className="cci-price-value">
                        {info.price != null ? `₹${fmt(info.price)}` : '—'}
                    </span>
                    <span className="cci-price-sub">NSE · Delayed 15 min</span>
                </div>

                <div className="cci-metrics">
                    {sideMetrics.map(m => (
                        <div key={m.label} className="cci-metric" tabIndex="0" data-tooltip={m.tip}>
                            <span className="cci-metric-label">{m.label}</span>
                            <span className="cci-metric-value">{m.value}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Description */}
            {info.description && (
                <div className="cci-desc">
                    <p>{expanded ? info.description : `${info.description.slice(0, 280)}…`}</p>
                    <button className="cci-desc-toggle" onClick={() => setExpanded(e => !e)}>
                        {expanded ? 'Show less' : 'Read more'}
                    </button>
                </div>
            )}
        </div>
    );
}

// ── News tab ──────────────────────────────────────────────────────────────────

function NewsSection({ articles, loading }) {
    if (loading) return <section className="container"><Spinner /></section>;
    if (!articles.length) return <section className="container"><Empty msg="No news found for this company." /></section>;
    return (
        <section className="container">
            <h4>Latest News</h4>
            <div className="news-grid">
                {articles.map((a, i) => (
                    <article key={i} className="news-card">
                        <a href={a.url} target="_blank" rel="noopener noreferrer" className="news-title">{a.title}</a>
                        <div className="news-meta">
                            {a.source && <span>{a.source}</span>}
                            {a.published_at && <span>&middot; {fmtDate(a.published_at)}</span>}
                        </div>
                        {a.summary && <p className="news-summary">{a.summary}</p>}
                    </article>
                ))}
            </div>
        </section>
    );
}

// ── Developments (overview tab) ───────────────────────────────────────────────

function DevelopmentsSection({ data }) {
    if (!data) return null;
    const { news = [], corporate_actions = [], calendar = {} } = data;
    if (!news.length && !corporate_actions.length && !Object.keys(calendar).length) return null;
    return (
        <section className="container developments">
            <h4>Recent Developments <Tip text="Corporate actions (dividends, splits), upcoming calendar events, and Yahoo Finance news" /></h4>
            <div className="dev-grid">
                {corporate_actions.length > 0 && (
                    <div className="dev-panel">
                        <h5>Corporate Actions</h5>
                        <table className="dev-table">
                            <thead><tr><th>Date</th><th>Type</th><th>Value</th></tr></thead>
                            <tbody>
                                {corporate_actions.map((a, i) => (
                                    <tr key={i}>
                                        <td>{a.date}</td><td>{a.type}</td>
                                        <td>{a.type === 'Dividend' ? `Rs. ${a.value}` : `${a.value}:1 split`}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
                {Object.keys(calendar).length > 0 && (
                    <div className="dev-panel">
                        <h5>Calendar</h5>
                        <dl className="dev-dl">
                            {Object.entries(calendar).map(([k, v]) => (
                                <React.Fragment key={k}><dt>{k}</dt><dd>{v}</dd></React.Fragment>
                            ))}
                        </dl>
                    </div>
                )}
                {news.length > 0 && (
                    <div className="dev-panel dev-panel-wide">
                        <h5>From Yahoo Finance</h5>
                        <ul className="dev-news">
                            {news.map((n, i) => (
                                <li key={i}>
                                    <a href={n.url} target="_blank" rel="noopener noreferrer">{n.title}</a>
                                    <span className="news-meta">{n.publisher}{n.published_at ? ` - ${fmtDate(n.published_at)}` : ''}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </section>
    );
}

// ── Financials tab ────────────────────────────────────────────────────────────

function FinancialTable({ data }) {
    if (!data) return <Empty />;
    const dates = Object.keys(data).sort().reverse().slice(0, 8);
    if (!dates.length) return <Empty />;
    const metrics = Object.keys(data[dates[0]] || {});
    return (
        <div className="data-table-wrap">
            <table className="data-table fin-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        {dates.map(d => <th key={d}>{d}</th>)}
                    </tr>
                </thead>
                <tbody>
                    {metrics.map(metric => (
                        <tr key={metric}>
                            <td className="metric-name-cell">{metric}</td>
                            {dates.map(d => <td key={d}>{fmtNum(data[d]?.[metric])}</td>)}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function FinancialsSection({ data, loading }) {
    const [subTab, setSubTab] = useState('income');
    const [period, setPeriod] = useState('annual');

    if (loading) return <section className="container"><Spinner /></section>;
    if (!data) return <section className="container"><Empty /></section>;

    const SUB_TABS = [
        { key: 'income',   label: 'Income Statement', src: data.income_statement, tip: 'Revenue, expenses, and profit over time' },
        { key: 'balance',  label: 'Balance Sheet',    src: data.balance_sheet,    tip: 'Assets, liabilities, and equity at a point in time' },
        { key: 'cashflow', label: 'Cash Flow',        src: data.cash_flow,        tip: 'Actual cash generated or used in operations, investing, and financing' },
    ];
    const current = SUB_TABS.find(t => t.key === subTab)?.src?.[period];

    return (
        <section className="container">
            <div className="fin-controls">
                <div className="fin-subtabs">
                    {SUB_TABS.map(t => (
                        <button key={t.key} className={`fin-sub-btn${subTab === t.key ? ' active' : ''}`}
                            onClick={() => setSubTab(t.key)}>{t.label}<Tip text={t.tip} /></button>
                    ))}
                </div>
                <div className="fin-period-toggle">
                    {[
                        { key: 'annual',    label: 'Annual',    tip: 'Full-year figures (last 4 years)' },
                        { key: 'quarterly', label: 'Quarterly', tip: 'Three-month figures (last 8 quarters)' },
                    ].map(p => (
                        <button key={p.key} className={`period-btn${period === p.key ? ' active' : ''}`}
                            onClick={() => setPeriod(p.key)}>{p.label}<Tip text={p.tip} /></button>
                    ))}
                </div>
            </div>
            <FinancialTable data={current} />
        </section>
    );
}

// ── Analysts tab ──────────────────────────────────────────────────────────────

function AnalystsSection({ data, loading }) {
    if (loading) return <section className="container"><Spinner /></section>;
    if (!data) return <section className="container"><Empty /></section>;

    const { recommendations, price_targets, earnings_estimate, revenue_estimate } = data;
    const recCols = recommendations?.length ? Object.keys(recommendations[0]) : [];
    const ptCols  = price_targets?.length   ? Object.keys(price_targets[0])   : [];

    return (
        <>
            {recommendations?.length > 0 && (
                <section className="container">
                    <h4>Analyst Recommendations <Tip text="Aggregate buy/hold/sell ratings from research analysts over time" /></h4>
                    <DataTable rows={recommendations.slice(0, 20)} cols={recCols} />
                </section>
            )}
            {price_targets?.length > 0 && (
                <section className="container">
                    <h4>Price Targets <Tip text="12-month price target estimates from sell-side analysts" /></h4>
                    <DataTable rows={price_targets} cols={ptCols} />
                </section>
            )}
            {earnings_estimate?.length > 0 && (
                <section className="container">
                    <h4>EPS Estimates <Tip text="Forward earnings-per-share estimates from analyst consensus" /></h4>
                    <DataTable rows={earnings_estimate} cols={Object.keys(earnings_estimate[0])} />
                </section>
            )}
            {revenue_estimate?.length > 0 && (
                <section className="container">
                    <h4>Revenue Estimates <Tip text="Forward revenue estimates from analyst consensus" /></h4>
                    <DataTable rows={revenue_estimate} cols={Object.keys(revenue_estimate[0])} />
                </section>
            )}
            {!recommendations?.length && !price_targets?.length && !earnings_estimate?.length && (
                <section className="container"><Empty msg="No analyst data available for this stock." /></section>
            )}
        </>
    );
}

// ── Holders tab ───────────────────────────────────────────────────────────────

function HoldersSection({ data, loading }) {
    if (loading) return <section className="container"><Spinner /></section>;
    if (!data) return <section className="container"><Empty /></section>;

    const { major_holders, institutional_holders, mutualfund_holders, insider_transactions } = data;
    const hasAny = major_holders || institutional_holders || mutualfund_holders || insider_transactions;
    if (!hasAny) return <section className="container"><Empty msg="No holder data available for this stock." /></section>;

    return (
        <>
            {major_holders?.length > 0 && (
                <section className="container">
                    <h4>Major Holders <Tip text="Top owners by % of shares outstanding" /></h4>
                    <DataTable rows={major_holders} cols={Object.keys(major_holders[0])} />
                </section>
            )}
            {institutional_holders?.length > 0 && (
                <section className="container">
                    <h4>Institutional Holders <Tip text="Large financial institutions (funds, banks, insurance) with positions in this stock" /></h4>
                    <DataTable rows={institutional_holders.slice(0, 25)} cols={Object.keys(institutional_holders[0])} />
                </section>
            )}
            {mutualfund_holders?.length > 0 && (
                <section className="container">
                    <h4>Mutual Fund Holders <Tip text="Mutual funds invested in this company" /></h4>
                    <DataTable rows={mutualfund_holders.slice(0, 25)} cols={Object.keys(mutualfund_holders[0])} />
                </section>
            )}
            {insider_transactions?.length > 0 && (
                <section className="container">
                    <h4>Insider Transactions <Tip text="Recent buy/sell activity by company directors and senior officers" /></h4>
                    <DataTable rows={insider_transactions.slice(0, 20)} cols={Object.keys(insider_transactions[0])} />
                </section>
            )}
        </>
    );
}

// ── Earnings tab ──────────────────────────────────────────────────────────────

function EarningsSection({ data, loading }) {
    if (loading) return <section className="container"><Spinner /></section>;
    if (!data) return <section className="container"><Empty /></section>;

    const { earnings_history, earnings_dates, dividends, splits } = data;

    return (
        <>
            {earnings_history?.length > 0 && (
                <section className="container">
                    <h4>Earnings History (EPS) <Tip text="Reported EPS vs. analyst estimate — positive surprise = beat" /></h4>
                    <DataTable rows={earnings_history.slice(0, 20)} cols={Object.keys(earnings_history[0])} />
                </section>
            )}
            {earnings_dates?.length > 0 && (
                <section className="container">
                    <h4>Earnings Dates <Tip text="Past and upcoming quarterly results announcement dates" /></h4>
                    <DataTable rows={earnings_dates.slice(0, 10)} cols={Object.keys(earnings_dates[0])} />
                </section>
            )}
            {dividends?.length > 0 && (
                <section className="container">
                    <h4>Dividend History <Tip text="Dividends paid per share over time — useful for tracking yield history" /></h4>
                    <div className="data-table-wrap">
                        <table className="data-table">
                            <thead><tr><th>Date</th><th>Dividend (Rs.)</th></tr></thead>
                            <tbody>
                                {dividends.slice(-20).reverse().map((d, i) => (
                                    <tr key={i}><td>{d.date}</td><td>{d.value != null ? d.value.toFixed(2) : '-'}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}
            {splits?.length > 0 && (
                <section className="container">
                    <h4>Stock Splits <Tip text="A 2:1 split doubles share count and halves the price per share" /></h4>
                    <div className="data-table-wrap">
                        <table className="data-table">
                            <thead><tr><th>Date</th><th>Split Ratio</th></tr></thead>
                            <tbody>
                                {splits.map((s, i) => (
                                    <tr key={i}><td>{s.date}</td><td>{s.value}</td></tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </section>
            )}
            {!earnings_history?.length && !dividends?.length && (
                <section className="container"><Empty msg="No earnings data available for this stock." /></section>
            )}
        </>
    );
}

// ── ESG tab ───────────────────────────────────────────────────────────────────

const ESG_KEY_MAP = {
    esgScore:         { label: 'Total ESG Score', group: 'total', tip: 'Combined ESG risk score. Lower = less unmanaged ESG risk.' },
    environmentScore: { label: 'Environmental',   group: 'env',   tip: 'Carbon emissions, water usage, and waste management score.' },
    socialScore:      { label: 'Social',          group: 'soc',   tip: 'Labor practices, supply chain, and community relations score.' },
    governanceScore:  { label: 'Governance',      group: 'gov',   tip: 'Board structure, executive pay, and shareholder rights score.' },
    totalEsg:         { label: 'Total ESG',       group: 'total', tip: 'Combined ESG risk score. Lower = less unmanaged ESG risk.' },
    peerGroup:        { label: 'Peer Group',      group: 'meta',  tip: 'Industry group used for ESG peer comparison.' },
    peerCount:        { label: 'Peer Count',      group: 'meta',  tip: 'Number of companies in the ESG peer group.' },
    percentile:       { label: 'ESG Percentile',  group: 'meta',  tip: 'Percentile rank within peer group — lower = better managed risk.' },
    esgPerformance:   { label: 'ESG Performance', group: 'meta',  tip: 'Qualitative risk performance category.' },
};

function ESGSection({ data, loading }) {
    if (loading) return <section className="container"><Spinner /></section>;
    if (!data || !Object.keys(data).length) return (
        <section className="container"><Empty msg="ESG data not available for this stock (common for NSE-listed companies)." /></section>
    );

    const scores = Object.entries(data).filter(([k]) => !ESG_KEY_MAP[k] || ESG_KEY_MAP[k].group !== 'meta');
    const meta   = Object.entries(data).filter(([k]) =>  ESG_KEY_MAP[k]?.group === 'meta');

    return (
        <section className="container">
            <h4>ESG / Sustainability Scores</h4>
            <div className="esg-grid">
                {scores.map(([k, v]) => (
                    <div key={k} className="esg-card">
                        <span className="esg-label">
                            {ESG_KEY_MAP[k]?.label || k}
                            {ESG_KEY_MAP[k]?.tip && <Tip text={ESG_KEY_MAP[k].tip} />}
                        </span>
                        <span className="esg-value">{v != null ? (typeof v === 'number' ? v.toFixed(2) : v) : 'N/A'}</span>
                    </div>
                ))}
            </div>
            {meta.length > 0 && (
                <dl className="dev-dl" style={{ marginTop: '1rem' }}>
                    {meta.map(([k, v]) => (
                        <React.Fragment key={k}>
                            <dt>{ESG_KEY_MAP[k]?.label || k}{ESG_KEY_MAP[k]?.tip && <Tip text={ESG_KEY_MAP[k].tip} />}</dt>
                            <dd>{v != null ? String(v) : 'N/A'}</dd>
                        </React.Fragment>
                    ))}
                </dl>
            )}
        </section>
    );
}

// ── Options tab ───────────────────────────────────────────────────────────────

const OPTIONS_COLS = ['strike', 'lastPrice', 'bid', 'ask', 'change', 'percentChange', 'volume', 'openInterest', 'impliedVolatility', 'inTheMoney'];

const OPTIONS_COL_TIPS = {
    strike:            'Price at which the option can be exercised',
    lastPrice:         'Last traded price of this option contract',
    bid:               'Highest current buy offer',
    ask:               'Lowest current sell offer',
    change:            'Price change from the previous session',
    percentChange:     '% price change from the previous session',
    volume:            'Number of contracts traded today',
    openInterest:      'Total open (unsettled) contracts — proxy for market activity',
    impliedVolatility: "Market's expectation of future price volatility — higher IV = more expensive options",
    inTheMoney:        'ITM = exercising now would be profitable at the current spot price',
};

function OptionsSection({ data, loading }) {
    const [view, setView] = useState('calls');

    if (loading) return <section className="container"><Spinner /></section>;
    if (!data || !data.expiry_dates?.length) return (
        <section className="container"><Empty msg="Options data not available for this stock." /></section>
    );

    const rows = view === 'calls' ? data.calls : data.puts;
    const availCols = rows?.length ? OPTIONS_COLS.filter(c => c in rows[0]) : OPTIONS_COLS;

    return (
        <section className="container">
            <div className="options-header">
                <h4 style={{ margin: 0 }}>Options Chain — {data.nearest_expiry}</h4>
                <div className="fin-period-toggle">
                    <button className={`period-btn${view === 'calls' ? ' active' : ''}`} onClick={() => setView('calls')}>Calls<Tip text="Right to buy shares at the strike price before expiry" /></button>
                    <button className={`period-btn${view === 'puts'  ? ' active' : ''}`} onClick={() => setView('puts')}>Puts<Tip text="Right to sell shares at the strike price before expiry" /></button>
                </div>
            </div>
            {data.expiry_dates.length > 1 && (
                <p className="muted-text" style={{ fontSize: '0.8rem', margin: '0.5rem 0 1rem' }}>
                    Other expiries: {data.expiry_dates.slice(1, 5).join(' · ')}
                </p>
            )}
            <DataTable
                rows={rows || []}
                cols={availCols}
                colTips={OPTIONS_COL_TIPS}
                renderCell={(col, val) => {
                    if (col === 'inTheMoney') return val ? <span className="badge" style={{ fontSize: '0.7rem' }}>ITM</span> : '-';
                    if (col === 'impliedVolatility' && val != null) return `${(val * 100).toFixed(1)}%`;
                    if (col === 'percentChange' && val != null) return `${val.toFixed(2)}%`;
                    return val ?? '-';
                }}
            />
        </section>
    );
}

// ── Tab navigation ────────────────────────────────────────────────────────────

const TABS = [
    { key: 'overview',   label: 'Overview',    tip: 'Price chart, key metrics, and recent corporate developments' },
    { key: 'news',       label: 'News',        tip: 'Latest news articles from financial sources' },
    { key: 'ai',         label: 'AI Analyst',  tip: 'Ask GPT-4o-mini questions grounded in real news from the knowledge base' },
    { key: 'financials', label: 'Financials',  tip: 'Income statement, balance sheet, and cash flow — annual & quarterly' },
    { key: 'analysts',   label: 'Analysts',    tip: 'Analyst ratings, price targets, and consensus earnings estimates' },
    { key: 'holders',    label: 'Holders',     tip: 'Shareholders, institutional & mutual fund holdings, and insider activity' },
    { key: 'earnings',   label: 'Earnings',    tip: 'Historical EPS, upcoming earnings dates, dividends, and stock splits' },
    { key: 'esg',        label: 'ESG',         tip: 'Environmental, Social & Governance sustainability scores' },
    { key: 'options',    label: 'Options',     tip: 'Nearest-expiry call and put options chain' },
];

const TIME_RANGES = [
    { key: '7d',  label: '7 Days'   },
    { key: '1mo', label: '1 Month'  },
    { key: '6mo', label: '6 Months' },
    { key: '1y',  label: '1 Year'   },
    { key: 'max', label: 'Max'      },
];

// ── Main Stock component ──────────────────────────────────────────────────────

function Stock() {
    const [searchParams] = useSearchParams();
    const company = searchParams.get('company');
    const ticker  = company?.split(':')[0].trim();

    // Overview data
    const [companyInfo,  setCompanyInfo]  = useState(null);
    const [developments, setDevelopments] = useState(null);
    const [newsData,     setNewsData]     = useState([]);
    const [chartData,    setChartData]    = useState([]);
    const [timeRange,    setTimeRange]    = useState('7d');

    const [infoLoading,    setInfoLoading]    = useState(true);
    const [newsLoading,    setNewsLoading]    = useState(true);
    const [chartLoading,   setChartLoading]   = useState(true);
    const [chartRefreshing,setChartRefreshing]= useState(false);
    const [chartCanvasReady, setChartCanvasReady] = useState(false);

    // Tab state
    const [activeTab,  setActiveTab]  = useState('overview');
    const [tabData,    setTabData]    = useState({});
    const [tabLoading, setTabLoading] = useState({});
    const loadedTabsRef = useRef(new Set());

    // Indicator overlay state
    const [overlays,   setOverlays]   = useState(new Set());
    const [subPanel,   setSubPanel]   = useState('none');
    const [aiAnalysis, setAiAnalysis] = useState(null);

    const chartRef         = useRef(null);
    const chartInstanceRef = useRef(null);
    const prefetchedRef    = useRef(null);
    const displayDataRef   = useRef([]);   // kept in sync by chart render effect for tooltip OHLCV

    const subChartRef         = useRef(null);
    const subChartInstanceRef = useRef(null);
    const [subChartCanvasReady, setSubChartCanvasReady] = useState(false);

    const setChartCanvasRef = useCallback((node) => {
        chartRef.current = node;
        setChartCanvasReady(Boolean(node));
    }, []);

    const setSubChartCanvasRef = useCallback((node) => {
        if (!node) {
            if (subChartInstanceRef.current) { subChartInstanceRef.current.destroy(); subChartInstanceRef.current = null; }
            setSubChartCanvasReady(false);
            return;
        }
        subChartRef.current = node;
        setSubChartCanvasReady(true);
    }, []);

    // ── Lazy tab data loader ────────────────────────────────────────────────

    const loadTab = useCallback((tab) => {
        if (loadedTabsRef.current.has(tab) || !ticker) return;
        loadedTabsRef.current.add(tab);
        setTabLoading(prev => ({ ...prev, [tab]: true }));
        fetch(`${API_BASE}/api/company/${tab}?ticker=${ticker}`)
            .then(r => r.json())
            .then(data => setTabData(prev => ({ ...prev, [tab]: data })))
            .catch(() => setTabData(prev => ({ ...prev, [tab]: null })))
            .finally(() => setTabLoading(prev => ({ ...prev, [tab]: false })));
    }, [ticker]);

    useEffect(() => {
        if (activeTab !== 'overview' && activeTab !== 'news') loadTab(activeTab);
    }, [activeTab, loadTab]);

    // ── Fetch company info ──────────────────────────────────────────────────

    useEffect(() => {
        if (!ticker) return;
        setInfoLoading(true);
        fetch(`${API_BASE}/api/company/info?ticker=${ticker}`)
            .then(r => r.json())
            .then(data => { setCompanyInfo(data); setInfoLoading(false); })
            .catch(() => setInfoLoading(false));
    }, [ticker]);

    useEffect(() => {
        if (!ticker) return;
        fetch(`${API_BASE}/api/company/developments?ticker=${ticker}`)
            .then(r => r.json())
            .then(setDevelopments)
            .catch(() => {});
    }, [ticker]);

    useEffect(() => {
        if (!ticker) return;
        setNewsLoading(true);
        fetch(`${API_BASE}/api/company/news?ticker=${ticker}&limit=15`)
            .then(r => r.json())
            .then(data => { setNewsData(data.articles || []); setNewsLoading(false); })
            .catch(() => setNewsLoading(false));
    }, [ticker]);

    // ── Chart data fetch ────────────────────────────────────────────────────

    useEffect(() => {
        if (!ticker) return;
        const cached = getCachedChartData(ticker, timeRange);
        if (cached) {
            setChartData(cached);
            setChartLoading(false);
            setChartRefreshing(false);
            return;
        }
        setChartLoading(chartData.length === 0);
        setChartRefreshing(chartData.length > 0);
        fetch(`${API_BASE}/api/chart?ticker=${ticker}&period=${timeRange}`)
            .then(r => r.json())
            .then(data => {
                setChartData(data);
                setCachedChartData(ticker, timeRange, data);
                setChartLoading(false);
                setChartRefreshing(false);
            })
            .catch(() => { setChartLoading(false); setChartRefreshing(false); });
    }, [ticker, timeRange, chartData.length]);

    // Prefetch all chart ranges
    useEffect(() => {
        if (!ticker || chartData.length === 0 || prefetchedRef.current === ticker) return;
        prefetchedRef.current = ticker;
        TIME_RANGES.filter(({ key }) => key !== '7d' && !getCachedChartData(ticker, key))
            .forEach(({ key }) => {
                fetch(`${API_BASE}/api/chart?ticker=${ticker}&period=${key}`)
                    .then(r => r.json())
                    .then(data => setCachedChartData(ticker, key, data))
                    .catch(() => {});
            });
    }, [ticker, chartData.length]);

    // ── Chart rendering ─────────────────────────────────────────────────────

    useEffect(() => {
        if (!chartData.length || !chartCanvasReady || !chartRef.current) return;
        const ctx = chartRef.current.getContext('2d');
        if (!ctx) return;
        if (chartInstanceRef.current) chartInstanceRef.current.destroy();

        const displayData = simplifyChartData(chartData, timeRange);
        const prices = displayData.map(p => p.Close);
        const first  = prices[0] ?? 0;
        const last   = prices[prices.length - 1] ?? 0;
        const isUp   = last >= first;
        const lineColor = isUp ? C.green : C.red;

        const gradient = makeGradient(
            ctx, chartRef.current.height,
            isUp ? 'rgba(34,197,94,0.22)' : 'rgba(239,68,68,0.22)',
            'rgba(0,0,0,0)'
        );

        // Keep reference for tooltip callbacks
        displayDataRef.current = displayData;

        // ── Volume bars (always shown, secondary axis) ───────────────────────
        const volMax = Math.max(...displayData.map(p => p.Volume || 0));
        const volDataset = {
            label: 'Volume',
            data: displayData.map(p => p.Volume || 0),
            type: 'bar',
            yAxisID: 'yVol',
            backgroundColor: displayData.map((p, i) => {
                if (i === 0) return 'rgba(100,116,139,0.25)';
                return p.Close >= displayData[i - 1].Close ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)';
            }),
            borderWidth: 0,
            pointRadius: 0,
        };

        // ── Overlay datasets ─────────────────────────────────────────────────
        const overlayDatasets = [];
        if (overlays.has('ema20'))  overlayDatasets.push({ label: 'EMA 20',  data: computeEMA(prices, 20),  borderColor: '#60a5fa', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y' });
        if (overlays.has('ema50'))  overlayDatasets.push({ label: 'EMA 50',  data: computeEMA(prices, 50),  borderColor: '#fbbf24', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y' });
        if (overlays.has('ema200')) overlayDatasets.push({ label: 'EMA 200', data: computeEMA(prices, 200), borderColor: '#a78bfa', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y' });
        if (overlays.has('sma20'))  overlayDatasets.push({ label: 'SMA 20',  data: computeSMA(prices, 20),  borderColor: '#f97316', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y',
            segment: { borderDash: (ctx) => [5, 3] } });
        if (overlays.has('vwap'))   overlayDatasets.push({ label: 'VWAP',    data: computeVWAP(displayData), borderColor: '#34d399', borderWidth: 2, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y',
            segment: { borderDash: (ctx) => [6, 3] } });
        if (overlays.has('bollinger')) {
            const bb = computeBollinger(prices, 20, 2);
            overlayDatasets.push({ label: 'BB Upper', data: bb.upper, borderColor: 'rgba(148,163,184,0.8)', borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y',
                segment: { borderDash: (ctx) => [4, 3] } });
            overlayDatasets.push({ label: 'BB Mid',   data: bb.mid,   borderColor: 'rgba(100,116,139,0.6)', borderWidth: 1,   pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y',
                segment: { borderDash: (ctx) => [4, 3] } });
            overlayDatasets.push({ label: 'BB Lower', data: bb.lower, borderColor: 'rgba(148,163,184,0.8)', borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y',
                segment: { borderDash: (ctx) => [4, 3] } });
        }

        chartInstanceRef.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: displayData.map(p => p.Datetime),
                datasets: [
                    {
                        label: 'Close ₹',
                        data: prices,
                        borderColor: lineColor,
                        borderWidth: 2,
                        backgroundColor: gradient,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointHoverBackgroundColor: lineColor,
                        pointHoverBorderColor: C.bgSurface,
                        pointHoverBorderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y',
                    },
                    volDataset,
                    ...overlayDatasets,
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        display: overlays.size > 0,
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: 'rgba(255,255,255,0.5)',
                            font: { size: 10 },
                            boxWidth: 12,
                            filter: (item) => !['Close ₹', 'Volume', 'BB Mid'].includes(item.text),
                        },
                    },
                    tooltip: {
                        ...tooltipDefaults,
                        callbacks: {
                            title: (items) => items[0]?.label ?? '',
                            label: (ctx) => {
                                if (ctx.dataset.label === 'Volume') return null;
                                const bar = displayDataRef.current[ctx.dataIndex];
                                if (ctx.dataset.label === 'Close ₹' && bar) {
                                    const vol = bar.Volume >= 1e7 ? `${(bar.Volume/1e7).toFixed(2)}Cr`
                                              : bar.Volume >= 1e5 ? `${(bar.Volume/1e5).toFixed(2)}L`
                                              : bar.Volume?.toLocaleString('en-IN') ?? '-';
                                    return [
                                        ` O  ₹${Number(bar.Open  ?? bar.Close).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
                                        ` H  ₹${Number(bar.High  ?? bar.Close).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
                                        ` L  ₹${Number(bar.Low   ?? bar.Close).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
                                        ` C  ₹${Number(bar.Close).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`,
                                        ` Vol ${vol}`,
                                    ];
                                }
                                return ` ${ctx.dataset.label}  ₹${Number(ctx.parsed.y).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        ...scaleDefaults,
                        ticks: {
                            ...scaleDefaults.ticks,
                            maxTicksLimit: 8,
                            callback(val) {
                                const lbl = this.getLabelForValue(val);
                                if (!lbl) return '';
                                if (lbl.includes(':') && !lbl.includes('-')) return lbl;
                                const parts = lbl.split('-');
                                if (parts.length >= 3) return `${parts[2]} ${['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][+parts[1]] ?? ''}`;
                                return lbl;
                            },
                        },
                    },
                    y: {
                        ...scaleDefaults,
                        position: 'right',
                        ticks: {
                            ...scaleDefaults.ticks,
                            maxTicksLimit: 6,
                            callback: (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`,
                        },
                    },
                    yVol: {
                        display: false,
                        position: 'left',
                        min: 0,
                        max: volMax * 6,
                        grid: { display: false },
                    },
                },
            },
        });
    }, [chartData, chartCanvasReady, timeRange, overlays]); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Sub-panel chart rendering ────────────────────────────────────────────

    useEffect(() => {
        if (subPanel === 'none' || !subChartCanvasReady || !subChartRef.current || !chartData.length) return;
        const ctx = subChartRef.current.getContext('2d');
        if (!ctx) return;
        if (subChartInstanceRef.current) subChartInstanceRef.current.destroy();

        const displayData = simplifyChartData(chartData, timeRange);
        const prices      = displayData.map(p => p.Close);
        const labels      = displayData.map(p => p.Datetime);

        const baseOpts = {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { tooltip: { ...tooltipDefaults } },
            scales: {
                x: { ...scaleDefaults, ticks: { ...scaleDefaults.ticks, display: false } },
            },
        };

        if (subPanel === 'rsi') {
            const rsi = computeRSI(prices, 14);
            subChartInstanceRef.current = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets: [{ label: 'RSI 14', data: rsi, borderColor: C.emerald, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false }] },
                options: {
                    ...baseOpts,
                    plugins: {
                        ...baseOpts.plugins,
                        legend: { display: false },
                        annotation: { annotations: {
                            ob: { type: 'box', yMin: 70, yMax: 100, backgroundColor: 'rgba(239,68,68,0.07)', borderWidth: 0 },
                            os: { type: 'box', yMin: 0,  yMax: 30,  backgroundColor: 'rgba(34,197,94,0.07)',  borderWidth: 0 },
                            ob_l: { type: 'line', yMin: 70, yMax: 70, borderColor: 'rgba(239,68,68,0.4)', borderWidth: 1, borderDash: [4,4] },
                            os_l: { type: 'line', yMin: 30, yMax: 30, borderColor: 'rgba(34,197,94,0.4)',  borderWidth: 1, borderDash: [4,4] },
                        }},
                    },
                    scales: { ...baseOpts.scales, y: { ...scaleDefaults, min: 0, max: 100, position: 'right', ticks: { ...scaleDefaults.ticks, maxTicksLimit: 5 } } },
                },
            });
        } else if (subPanel === 'macd') {
            const { macd, signal, histogram } = computeMACD(prices, 12, 26, 9);
            subChartInstanceRef.current = new Chart(ctx, {
                type: 'bar',
                data: { labels, datasets: [
                    { label: 'Histogram', data: histogram, backgroundColor: histogram.map(v => v == null ? 'transparent' : v >= 0 ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)'), borderWidth: 0, yAxisID: 'y' },
                    { label: 'MACD',      type: 'line', data: macd,   borderColor: C.emerald, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y' },
                    { label: 'Signal',    type: 'line', data: signal, borderColor: '#fbbf24', borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false, yAxisID: 'y', borderDash: [4, 3] },
                ]},
                options: { ...baseOpts, plugins: { ...baseOpts.plugins, legend: { display: true, position: 'top', align: 'end', labels: { color: 'rgba(255,255,255,0.4)', font: { size: 9 }, boxWidth: 10 } } }, scales: { ...baseOpts.scales, y: { ...scaleDefaults, position: 'right', ticks: { ...scaleDefaults.ticks, maxTicksLimit: 5 } } } },
            });
        } else if (subPanel === 'stochastic') {
            const { k, d } = computeStoch(displayData, 14, 3);
            subChartInstanceRef.current = new Chart(ctx, {
                type: 'line',
                data: { labels, datasets: [
                    { label: '%K', data: k, borderColor: C.emerald, borderWidth: 1.5, pointRadius: 0, tension: 0.3, fill: false },
                    { label: '%D', data: d, borderColor: '#fbbf24', borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, tension: 0.3, fill: false },
                ]},
                options: {
                    ...baseOpts,
                    plugins: {
                        ...baseOpts.plugins,
                        legend: { display: true, position: 'top', align: 'end', labels: { color: 'rgba(255,255,255,0.4)', font: { size: 9 }, boxWidth: 10 } },
                        annotation: { annotations: {
                            ob: { type: 'line', yMin: 80, yMax: 80, borderColor: 'rgba(239,68,68,0.4)', borderWidth: 1, borderDash: [4,4] },
                            os: { type: 'line', yMin: 20, yMax: 20, borderColor: 'rgba(34,197,94,0.4)',  borderWidth: 1, borderDash: [4,4] },
                        }},
                    },
                    scales: { ...baseOpts.scales, y: { ...scaleDefaults, min: 0, max: 100, position: 'right', ticks: { ...scaleDefaults.ticks, maxTicksLimit: 5 } } },
                },
            });
        } else if (subPanel === 'volume') {
            const volColors = displayData.map((p, i) =>
                i === 0 || p.Close >= displayData[i - 1].Close ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)');
            subChartInstanceRef.current = new Chart(ctx, {
                type: 'bar',
                data: { labels, datasets: [{ label: 'Volume', data: displayData.map(p => p.Volume), backgroundColor: volColors, borderWidth: 0 }] },
                options: { ...baseOpts, plugins: { ...baseOpts.plugins, legend: { display: false } }, scales: { ...baseOpts.scales, y: { ...scaleDefaults, position: 'right', ticks: { ...scaleDefaults.ticks, maxTicksLimit: 5, callback: v => v >= 1e6 ? `${(v/1e6).toFixed(0)}M` : v >= 1e3 ? `${(v/1e3).toFixed(0)}K` : v } } } },
            });
        }
    }, [chartData, subPanel, subChartCanvasReady, timeRange]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => () => {
        if (chartInstanceRef.current)    chartInstanceRef.current.destroy();
        if (subChartInstanceRef.current) subChartInstanceRef.current.destroy();
    }, []);

    // ── AI chart analysis ────────────────────────────────────────────────────

    const handleAIAnalysis = useCallback(async () => {
        if (!chartData.length) return;
        setAiAnalysis({ loading: true });

        const displayData = simplifyChartData(chartData, timeRange);
        const prices = displayData.map(p => p.Close);
        const last   = prices[prices.length - 1] ?? 0;
        const first  = prices[0] ?? 0;
        const pctChange = first !== 0 ? ((last - first) / first * 100).toFixed(2) : '0.00';

        const context = { indicator: 'multi', ticker, timeRange, currentPrice: last?.toFixed(2), priceChangePct: pctChange, overlays: [...overlays], subPanel };
        if (overlays.has('ema20'))  { const v = computeEMA(prices, 20);  context.ema20  = v[v.length - 1]?.toFixed(2); }
        if (overlays.has('ema50'))  { const v = computeEMA(prices, 50);  context.ema50  = v[v.length - 1]?.toFixed(2); }
        if (overlays.has('ema200')) { const v = computeEMA(prices, 200); context.ema200 = v[v.length - 1]?.toFixed(2); }
        if (subPanel === 'rsi') { const v = computeRSI(prices, 14); context.rsi = v[v.length - 1]?.toFixed(1); }

        const overlayText = [...overlays].join(', ') || 'none';
        const question = `Analyze the ${ticker} stock chart for the ${timeRange} period. Price: ₹${last?.toFixed(2)} (${pctChange > 0 ? '+' : ''}${pctChange}% change). Active overlays: ${overlayText}${subPanel !== 'none' ? `, ${subPanel} sub-panel` : ''}. What do the price action and indicators suggest about current trend, momentum, and key levels to watch? Keep it concise (3-4 short paragraphs).`;

        try {
            const res = await fetch(`${API_BASE}/education/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, context }),
            });
            const data = await res.json();
            setAiAnalysis({ loading: false, text: data.answer });
        } catch {
            setAiAnalysis({ loading: false, error: 'AI analysis unavailable. Check backend connection.' });
        }
    }, [chartData, timeRange, ticker, overlays, subPanel]);

    // ── Tab change — reset loaded tabs when ticker changes ──────────────────

    useEffect(() => {
        loadedTabsRef.current = new Set();
        setTabData({});
        setTabLoading({});
        setActiveTab('overview');
        setOverlays(new Set());
        setSubPanel('none');
        setAiAnalysis(null);
    }, [ticker]);

    // ── Render ──────────────────────────────────────────────────────────────

    if (infoLoading) {
        return (
            <div className="page-loader">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div>
            <Navbar />
            <main className="stock-page">
                {companyInfo && !companyInfo.error && <CompanyInfoCard info={companyInfo} />}

                {/* Tab navigation */}
                <nav className="stock-tabs">
                    {TABS.map(t => (
                        <button
                            key={t.key}
                            className={`stock-tab${activeTab === t.key ? ' active' : ''}`}
                            onClick={() => setActiveTab(t.key)}
                        >
                            {t.label}<Tip text={t.tip} />
                        </button>
                    ))}
                </nav>

                {/* Tab content */}
                {activeTab === 'overview' && (
                    <>
                        <DevelopmentsSection data={developments} />
                        <section className="container">
                            <h4>Stock Price Chart <Tip text="Historical close price from NSE via Yahoo Finance. Cached for 6 hours." /></h4>

                            {/* Period stats bar */}
                            {chartData.length > 0 && (() => {
                                const d = chartData;
                                const open  = d[0]?.Open  ?? d[0]?.Close;
                                const close = d[d.length - 1]?.Close;
                                const high  = Math.max(...d.map(p => p.High ?? p.Close));
                                const low   = Math.min(...d.map(p => p.Low  ?? p.Close));
                                const chg   = close != null && open != null ? close - open : null;
                                const pct   = chg != null && open ? (chg / open * 100) : null;
                                const up    = chg >= 0;
                                return (
                                    <div className="chart-stats-row">
                                        <span className="csr-item"><span className="csr-lbl">O</span><span className="csr-val">₹{fmt(open)}</span></span>
                                        <span className="csr-item"><span className="csr-lbl">H</span><span className="csr-val csr-green">₹{fmt(high)}</span></span>
                                        <span className="csr-item"><span className="csr-lbl">L</span><span className="csr-val csr-red">₹{fmt(low)}</span></span>
                                        <span className="csr-item"><span className="csr-lbl">C</span><span className="csr-val">₹{fmt(close)}</span></span>
                                        {chg != null && (
                                            <span className="csr-item">
                                                <span className={`csr-change ${up ? 'csr-green' : 'csr-red'}`}>
                                                    {up ? '+' : ''}{fmt(chg)} ({up ? '+' : ''}{pct?.toFixed(2)}%)
                                                </span>
                                            </span>
                                        )}
                                    </div>
                                );
                            })()}

                            {(chartLoading || chartRefreshing) && (
                                <span className="chart-refreshing">
                                    {chartLoading ? 'Loading chart...' : 'Updating...'}
                                </span>
                            )}

                            {/* Time range buttons */}
                            <div id="buttons">
                                {TIME_RANGES.map(({ key, label }) => (
                                    <button
                                        key={key}
                                        className={`btn${timeRange === key ? ' active' : ''}`}
                                        onClick={() => setTimeRange(key)}
                                    >
                                        {label}
                                    </button>
                                ))}
                            </div>

                            {/* Overlay indicator pills */}
                            <div className="ind-row">
                                <span className="ind-row-label">Overlays</span>
                                {OVERLAY_OPTIONS.map(opt => {
                                    const needsPoints = { ema20: 20, ema50: 50, ema200: 200, sma20: 20, bollinger: 20, vwap: 1 }[opt.key] ?? 1;
                                    const hasEnough = chartData.length >= needsPoints;
                                    return (
                                        <button
                                            key={opt.key}
                                            className={`ind-pill${overlays.has(opt.key) ? ' active' : ''}${!hasEnough ? ' ind-pill-na' : ''}`}
                                            style={overlays.has(opt.key) ? { borderColor: opt.color, color: opt.color } : {}}
                                            title={!hasEnough ? `Needs ${needsPoints}+ data points — switch to a longer period` : opt.label}
                                            onClick={() => setOverlays(prev => {
                                                const next = new Set(prev);
                                                if (next.has(opt.key)) next.delete(opt.key); else next.add(opt.key);
                                                return next;
                                            })}
                                        >
                                            {opt.label}{!hasEnough ? ' ·' : ''}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Sub-panel selector */}
                            <div className="ind-row">
                                <span className="ind-row-label">Sub-panel</span>
                                {SUB_PANEL_OPTIONS.map(opt => (
                                    <button
                                        key={opt.key}
                                        className={`ind-pill${subPanel === opt.key ? ' active sub-active' : ''}`}
                                        onClick={() => setSubPanel(opt.key)}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>

                            {/* Main chart */}
                            <div className="chart-shell">
                                {chartLoading && <div className="chart-overlay"><div className="spinner" /></div>}
                                <canvas ref={setChartCanvasRef} width="800" height="400" />
                            </div>

                            {/* Sub-panel chart */}
                            {subPanel !== 'none' && (
                                <div className="sub-panel-wrap">
                                    <span className="sub-panel-label">
                                        {SUB_PANEL_OPTIONS.find(o => o.key === subPanel)?.label}
                                    </span>
                                    <div className="sub-panel-canvas-wrap">
                                        <canvas ref={setSubChartCanvasRef} height="130" />
                                    </div>
                                </div>
                            )}

                            {/* AI chart analysis */}
                            <div className="ai-chart-section">
                                <div className="ai-chart-header">
                                    <span className="ai-chart-title">AI Chart Analysis</span>
                                    <span className="ai-chart-disclaimer">
                                        ⚠ AI-generated — may be inaccurate, not financial advice
                                    </span>
                                    <button
                                        className="ai-chart-btn"
                                        onClick={handleAIAnalysis}
                                        disabled={aiAnalysis?.loading || chartLoading}
                                    >
                                        {aiAnalysis?.loading ? 'Analyzing…' : 'Analyze chart'}
                                    </button>
                                </div>
                                {aiAnalysis && !aiAnalysis.loading && (
                                    <div className={`ai-chart-result${aiAnalysis.error ? ' error' : ''}`}>
                                        {aiAnalysis.error || aiAnalysis.text}
                                    </div>
                                )}
                            </div>
                        </section>
                    </>
                )}

                {activeTab === 'news' && (
                    <NewsSection articles={newsData} loading={newsLoading} />
                )}

                {activeTab === 'ai' && (
                    <AgentChat ticker={ticker} />
                )}

                {activeTab === 'financials' && (
                    <FinancialsSection data={tabData.financials} loading={!!tabLoading.financials} />
                )}

                {activeTab === 'analysts' && (
                    <AnalystsSection data={tabData.analysts} loading={!!tabLoading.analysts} />
                )}

                {activeTab === 'holders' && (
                    <HoldersSection data={tabData.holders} loading={!!tabLoading.holders} />
                )}

                {activeTab === 'earnings' && (
                    <EarningsSection data={tabData.earnings} loading={!!tabLoading.earnings} />
                )}

                {activeTab === 'esg' && (
                    <ESGSection data={tabData.esg} loading={!!tabLoading.esg} />
                )}

                {activeTab === 'options' && (
                    <OptionsSection data={tabData.options} loading={!!tabLoading.options} />
                )}

                <Footer />
            </main>
        </div>
    );
}

export default Stock;
