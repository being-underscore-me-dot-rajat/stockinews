"""
Static educational content — CFA / Zerodha Varsity depth.
Each entry has: title, category, slug, tagline, body sections, formula, interpretation,
use_cases, limitations, and (for indicators) chart_config.
"""

CONCEPTS = {
    "mean": {
        "slug": "mean",
        "title": "Arithmetic Mean",
        "category": "statistics",
        "tagline": "The average return — the starting point of all risk analysis.",
        "formula": "μ = (Σ xᵢ) / n",
        "what": (
            "The arithmetic mean is the sum of all observations divided by the number of observations. "
            "In finance, it is the average daily return over a period. It tells you what a 'typical' "
            "outcome looks like, but it is blind to the path — a stock that goes up 100% then down 50% "
            "has the same arithmetic mean return as one that earns a steady 25% per year."
        ),
        "why": (
            "Mean return is the foundation of portfolio theory. It feeds into Expected Value calculations, "
            "Sharpe Ratio numerators, and regression models. However, for compounding contexts (long-term "
            "wealth), the geometric mean is more appropriate — arithmetic mean systematically overstates "
            "what you will actually earn when returns are volatile."
        ),
        "professional_use": (
            "Portfolio managers compute trailing 1-year, 3-year, and 5-year mean returns to benchmark "
            "against indices. Risk teams use rolling 20-day or 60-day mean returns to detect regime shifts. "
            "The difference between arithmetic mean and geometric mean (the 'variance drag') is a key metric "
            "for options traders: higher variance → larger drag → lower compounded return."
        ),
        "market_interpretation": (
            "A stock with a mean daily return of +0.1% implies roughly +28% annually (0.1 × 252 trading days). "
            "But if standard deviation is 3% daily, the actual compounded return is closer to +17% due to "
            "variance drag (approx. σ²/2 per period). This is why high-volatility stocks need higher mean "
            "returns just to break even with low-volatility alternatives."
        ),
        "where_it_fails": (
            "The mean is highly sensitive to outliers. A single +300% day in a small-cap stock will "
            "distort the mean upward for years. For fat-tailed distributions (Indian small-caps, crypto), "
            "the mean is a poor summary statistic. In such cases, use median or trimmed mean."
        ),
        "chart_type": "distribution",
    },
    "standard-deviation": {
        "slug": "standard-deviation",
        "title": "Standard Deviation",
        "category": "statistics",
        "tagline": "Volatility — the price of uncertainty.",
        "formula": "σ = √[ Σ(xᵢ − μ)² / (n−1) ]",
        "what": (
            "Standard deviation measures the average distance of each return from the mean. "
            "A σ of 2% daily means that on most days, the stock moves ±2% around its average. "
            "In finance, σ is the most universal measure of risk."
        ),
        "why": (
            "Standard deviation is the risk denominator in the Sharpe Ratio, the volatility input in "
            "Black-Scholes options pricing, and the basis for Value-at-Risk (VaR) models. Understanding "
            "σ lets you answer: 'How much can I lose in a bad month?' For a normal distribution, "
            "approximately 68% of outcomes fall within ±1σ, and 95% within ±2σ."
        ),
        "professional_use": (
            "Institutional traders use annualised σ (daily σ × √252) to compare cross-asset volatility. "
            "Options desks use σ to price premium — higher σ means more expensive options. "
            "Risk managers use σ to set position limits: a ₹1Cr position in a 3% daily σ stock has "
            "a 1-day 95% VaR of approximately ₹4.9L (1.645 × 3% × 1Cr)."
        ),
        "market_interpretation": (
            "NIFTY 50 has a historical annualised σ of approximately 15–20%. Individual large-cap stocks "
            "like RELIANCE or HDFC BANK typically have σ of 20–30%. Small-caps and mid-caps can reach "
            "40–60%+. High σ means higher option premiums, wider bid-ask spreads, and more extreme "
            "drawdowns. During crises (2020 Covid, 2008 GFC), NIFTY's σ spiked to 50%+."
        ),
        "where_it_fails": (
            "σ treats positive and negative deviations equally — it penalises upside as much as downside. "
            "This is why the Sortino Ratio (which uses downside deviation) is preferred for asymmetric "
            "strategies. σ also assumes a stationary process: in reality, volatility clusters (GARCH effects) "
            "— calm periods are followed by volatile periods, not random noise."
        ),
        "chart_type": "distribution",
    },
    "correlation": {
        "slug": "correlation",
        "title": "Correlation",
        "category": "statistics",
        "tagline": "Diversification only works when assets move independently.",
        "formula": "ρ(X,Y) = Cov(X,Y) / (σₓ · σᵧ)",
        "what": (
            "Correlation (ρ) measures how two assets move relative to each other, on a scale from "
            "-1 (perfect inverse) to +1 (perfect co-movement). ρ = 0 means no linear relationship. "
            "It is the mathematical foundation of portfolio diversification."
        ),
        "why": (
            "Adding two assets with ρ < 1 to a portfolio reduces overall portfolio σ without necessarily "
            "reducing expected return — this is the 'free lunch' of diversification. The lower the "
            "correlation, the more diversification benefit. At ρ = -1, you can theoretically eliminate "
            "all portfolio risk (perfect hedge)."
        ),
        "professional_use": (
            "Fund managers build correlation matrices across their holdings to ensure true diversification "
            "(not just owning many stocks that all move with the same factor). Pairs traders exploit "
            "temporary de-correlations between historically correlated stocks. Risk managers monitor "
            "'correlation spikes' during market stress — in 2020, nearly all assets went to ρ ≈ 1 briefly."
        ),
        "market_interpretation": (
            "BankNifty vs NIFTY 50: historically ρ ≈ 0.85–0.90 — highly correlated, offering little "
            "diversification benefit. Gold vs NIFTY 50: historically ρ ≈ -0.1 to 0.1 — good diversifier. "
            "IT stocks (TCS, Infosys) vs INR/USD: ρ ≈ -0.5 to -0.7 — IT earns in USD, so a weaker rupee "
            "is good for them while it signals stress elsewhere."
        ),
        "where_it_fails": (
            "Correlation only captures linear relationships. Two assets can have ρ = 0 yet be strongly "
            "related non-linearly. Correlations are also unstable — they shift with market regimes. "
            "During crises, historically low-correlation assets often spike toward ρ = 1, eliminating "
            "the diversification benefit exactly when you need it most."
        ),
        "chart_type": "scatter",
    },
    "beta": {
        "slug": "beta",
        "title": "Beta (β)",
        "category": "statistics",
        "tagline": "How much does a stock amplify the market's moves?",
        "formula": "β = Cov(Rₛ, Rₘ) / Var(Rₘ)",
        "what": (
            "Beta measures a stock's sensitivity to market movements. β = 1 means the stock moves in "
            "lockstep with the market. β = 1.5 means a 1% market move implies a 1.5% stock move. "
            "β = 0.5 means the stock is less sensitive than the market. β < 0 means the stock typically "
            "moves opposite to the market."
        ),
        "why": (
            "Beta is the core input in the Capital Asset Pricing Model (CAPM): Expected Return = "
            "Rf + β(Rm − Rf). It separates 'systematic risk' (market risk you cannot diversify away) "
            "from 'idiosyncratic risk' (company-specific risk). Beta-weighted position sizing ensures "
            "you understand how much market exposure your portfolio actually has."
        ),
        "professional_use": (
            "Portfolio managers target specific portfolio betas. A 'market-neutral' hedge fund keeps "
            "portfolio β ≈ 0. A bull market fund might lever up to β = 1.3+. Options traders use "
            "delta-adjusted beta to understand their true market exposure through derivatives. "
            "Smart beta ETFs systematically tilt toward low-beta (defensive) or high-beta (aggressive) stocks."
        ),
        "market_interpretation": (
            "In Indian markets: FMCG stocks (HUL, Nestle) typically β ≈ 0.4–0.7 — defensive. "
            "IT majors (TCS, Infosys) β ≈ 0.7–0.9 — moderate. PSU Banks (SBI, PNB) β ≈ 1.2–1.5 — aggressive. "
            "Small-cap momentum stocks β ≈ 1.5–2.0+. During 2020–2022 bull run, high-beta stocks "
            "massively outperformed; in the 2022–2023 correction, they fell hardest."
        ),
        "where_it_fails": (
            "Beta is calculated on historical data — it changes over time as a company's business evolves. "
            "A startup becoming a profitable large-cap will see β drift down. Also, β assumes a linear "
            "relationship to the market; in reality, stocks can have asymmetric betas (larger losses in "
            "down markets than gains in up markets). CAPM itself has been empirically weak in explaining "
            "cross-sectional returns."
        ),
        "chart_type": "scatter",
    },
    "sharpe-ratio": {
        "slug": "sharpe-ratio",
        "title": "Sharpe Ratio",
        "category": "statistics",
        "tagline": "Return per unit of risk — the most important performance metric.",
        "formula": "Sharpe = (Rₚ − Rf) / σₚ",
        "what": (
            "The Sharpe Ratio measures how much excess return (above the risk-free rate) you earn per "
            "unit of total risk (σ). A Sharpe of 1.0 means you earn 1% of excess return for every 1% "
            "of volatility taken. Higher is better. Most professional funds target Sharpe ≥ 1.0."
        ),
        "why": (
            "Without adjusting for risk, raw return is meaningless. A fund returning 30% but taking "
            "massive risk may be inferior to one returning 18% with minimal risk. The Sharpe Ratio "
            "allows apples-to-apples comparison across any asset, strategy, or fund manager. "
            "It is the cornerstone of modern portfolio construction."
        ),
        "professional_use": (
            "Hedge funds report Sharpe ratios to attract capital. The legendary Renaissance Medallion "
            "Fund is estimated to have a Sharpe > 2.0 after fees. Most actively managed mutual funds "
            "have Sharpe < 0.5. Quant strategies specifically optimise for Sharpe. The Sortino Ratio "
            "is a variant that only penalises downside volatility — preferred for asymmetric strategies."
        ),
        "market_interpretation": (
            "Indian risk-free rate ≈ 6–7% (10Y G-Sec). NIFTY 50 has a historical Sharpe of approximately "
            "0.4–0.7 over 10-year periods. An individual stock outperforming with Sharpe > 1.0 consistently "
            "is exceptional. Day traders and momentum strategies often have high Sharpe for short periods "
            "but mean-revert. Always evaluate Sharpe over at least 3 full market cycles."
        ),
        "where_it_fails": (
            "Sharpe uses σ as the risk measure, which penalises upside as much as downside. It also "
            "assumes returns are normally distributed — in reality, financial returns have fat tails. "
            "A strategy with many small gains and rare catastrophic losses (short volatility) can "
            "show an excellent Sharpe until it blows up ('picking up pennies in front of a steamroller')."
        ),
        "chart_type": "bar",
    },
    "volatility": {
        "slug": "volatility",
        "title": "Volatility",
        "category": "statistics",
        "tagline": "The heartbeat of markets — the source of both opportunity and ruin.",
        "formula": "σ_annualised = σ_daily × √252",
        "what": (
            "Volatility in financial markets refers to the degree of price variation over time. "
            "Realised (historical) volatility is computed from actual past price moves. "
            "Implied volatility (IV) is derived from option prices — it represents the market's "
            "expectation of future volatility. They are related but diverge significantly during uncertainty."
        ),
        "why": (
            "Volatility is the single most important variable in options pricing. Higher volatility "
            "makes options more expensive because the underlying can make larger moves, increasing "
            "the chance of the option expiring in-the-money. Volatility is also mean-reverting — "
            "periods of extreme calm are followed by spikes, and vice versa. This property is "
            "exploited by volatility traders and market makers."
        ),
        "professional_use": (
            "Options market makers delta-hedge their books and earn the spread between implied and "
            "realised volatility (the 'volatility risk premium'). Volatility arbitrageurs buy cheap "
            "volatility (when IV < expected realised) and sell expensive volatility (when IV > expected). "
            "India VIX (NSE) is the market's implied volatility index — spikes above 25 historically "
            "signal fear and buying opportunities; below 12 signals complacency."
        ),
        "market_interpretation": (
            "India VIX > 25: high fear, consider buying quality stocks or long straddles. "
            "India VIX < 12: complacency, options are cheap — consider buying protection. "
            "Individual stock IV: if a stock's IV is historically high (>80th percentile), "
            "selling options premium has an edge. If IV is historically low, buying options is cheap."
        ),
        "where_it_fails": (
            "Historical volatility looks backward and can be a poor predictor when market regimes change. "
            "Implied volatility can stay 'too high' or 'too low' for extended periods. The GARCH effect "
            "(volatility clustering) means high-volatility periods persist — 'sell vol' strategies can "
            "be catastrophically wrong in crash environments."
        ),
        "chart_type": "line",
    },
}

INDICATORS = {
    "rsi": {
        "slug": "rsi",
        "title": "Relative Strength Index (RSI)",
        "category": "momentum",
        "tagline": "Is the stock overbought or oversold — and is the momentum real?",
        "formula": "RSI = 100 − [100 / (1 + RS)]   where RS = Avg Gain / Avg Loss (14 periods)",
        "what": (
            "RSI is a bounded momentum oscillator (0–100) developed by J. Welles Wilder. "
            "It measures the speed and magnitude of recent price changes to evaluate whether "
            "a stock is overbought (>70) or oversold (<30). RSI quantifies how aggressively "
            "the stock has been bought relative to sold over the last 14 periods."
        ),
        "signals": {
            "overbought": "RSI > 70 — stock has likely been pushed up aggressively; watch for reversal or consolidation.",
            "oversold": "RSI < 30 — selling pressure has been extreme; watch for relief bounce or base formation.",
            "divergence": (
                "Price makes new highs but RSI makes lower highs (bearish divergence) — momentum is waning. "
                "Price makes new lows but RSI makes higher lows (bullish divergence) — selling is exhausting."
            ),
            "centerline": "RSI crossing 50 from below signals strengthening momentum (and vice versa).",
        },
        "professional_use": (
            "RSI is most powerful in ranging (sideways) markets. In strong trends, RSI can stay overbought "
            "or oversold for extended periods — this is not a signal to fade, but a signal that trend is "
            "intact. Professional traders combine RSI with trend filters: only take RSI oversold signals "
            "when the broader trend is up (on a higher timeframe)."
        ),
        "where_it_fails": (
            "RSI generates many false signals in trending markets. Stocks in strong uptrends can remain "
            "above 70 for weeks. The classic 70/30 thresholds work best in sideways markets; in bull markets, "
            "80/40 is more appropriate. RSI also gives equal weight to all price bars — it is backward-looking "
            "and cannot anticipate fundamental catalysts."
        ),
        "chart_type": "rsi",
        "default_ticker": "^NSEI",
        "zones": [{"y": 70, "label": "Overbought", "color": "rgba(239,68,68,0.15)"},
                  {"y": 30, "label": "Oversold",   "color": "rgba(34,197,94,0.15)"}],
    },
    "macd": {
        "slug": "macd",
        "title": "MACD",
        "category": "momentum",
        "tagline": "Where trend meets momentum — the most complete moving average indicator.",
        "formula": (
            "MACD Line = EMA(12) − EMA(26)\n"
            "Signal Line = EMA(9) of MACD Line\n"
            "Histogram = MACD Line − Signal Line"
        ),
        "what": (
            "MACD (Moving Average Convergence Divergence) combines trend-following with momentum. "
            "The MACD line is the difference between two exponential moving averages. The signal line "
            "is a smoothed version of MACD. The histogram shows the distance between them — "
            "it visualises acceleration and deceleration of momentum."
        ),
        "signals": {
            "bullish_crossover": "MACD line crosses above Signal line — momentum turning positive.",
            "bearish_crossover": "MACD line crosses below Signal line — momentum turning negative.",
            "zero_cross": "MACD crossing above zero confirms an uptrend change of character.",
            "histogram_divergence": "Rising histogram bars = accelerating momentum; shrinking bars = trend exhaustion.",
        },
        "professional_use": (
            "MACD works best on daily and weekly charts for swing trading and trend identification. "
            "Institutional desks use MACD to confirm breakouts — a price breakout with bullish MACD "
            "is higher probability. MACD on weekly charts is particularly powerful for identifying "
            "major trend changes. False signals are common on hourly/15-minute charts."
        ),
        "where_it_fails": (
            "MACD is a lagging indicator — it follows price, never leads it. In choppy sideways markets, "
            "MACD generates frequent crossovers that produce losses. The standard 12/26/9 settings may "
            "need adjustment for different asset classes or volatility regimes. Never use MACD alone; "
            "combine with volume and price action for confirmation."
        ),
        "chart_type": "macd",
        "default_ticker": "^NSEI",
    },
    "bollinger": {
        "slug": "bollinger",
        "title": "Bollinger Bands",
        "category": "volatility",
        "tagline": "Volatility is a cycle — squeeze, then expansion.",
        "formula": (
            "Middle Band = SMA(20)\n"
            "Upper Band = SMA(20) + 2σ\n"
            "Lower Band = SMA(20) − 2σ"
        ),
        "what": (
            "Bollinger Bands place statistical boundaries around price. The middle band is a 20-period "
            "simple moving average. The upper and lower bands are 2 standard deviations above and below. "
            "This means ~95% of price action should fall within the bands under normal distribution assumptions. "
            "Band width expands when volatility is high and contracts when volatility is low."
        ),
        "signals": {
            "squeeze": "Narrow bands = low volatility regime → explosive move imminent (direction unknown).",
            "breakout": "Price closes outside the band after a squeeze — high-probability directional move starting.",
            "walking_the_band": "Price repeatedly touching upper band in a strong uptrend = momentum confirmation.",
            "mean_reversion": "Price touches lower band then closes back inside = mean reversion opportunity in ranging market.",
        },
        "professional_use": (
            "The 'Bollinger Squeeze' (Bandwidth below its 6-month low) is one of the most reliable "
            "setups in technical analysis. Professionals wait for the squeeze, then trade the breakout "
            "direction using volume confirmation. In trending markets, 'walking the band' is a sign of "
            "strong institutional buying. Bollinger %B (position within the bands) is used for systematic "
            "mean-reversion strategies."
        ),
        "where_it_fails": (
            "Bollinger Bands do not predict direction — only the probability of a significant move. "
            "A squeeze on NIFTY before a major event (budget, RBI policy) is well-known but the direction "
            "of the breakout is unknown until it happens. Also, the normal distribution assumption breaks "
            "down in fat-tailed markets — more than 5% of price action exceeds ±2σ in Indian markets."
        ),
        "chart_type": "bollinger",
        "default_ticker": "^NSEI",
    },
    "ema-sma": {
        "slug": "ema-sma",
        "title": "EMA & SMA",
        "category": "trend",
        "tagline": "The backbone of every trend-following system.",
        "formula": (
            "SMA(n) = (P₁ + P₂ + ... + Pₙ) / n\n"
            "EMA(n) = α × Pₜ + (1−α) × EMA(t−1),  α = 2/(n+1)"
        ),
        "what": (
            "Simple Moving Average (SMA) equally weights all periods. Exponential Moving Average (EMA) "
            "gives more weight to recent prices, making it faster to respond to new developments. "
            "Key levels: 20 EMA (short-term trend), 50 EMA (medium-term), 200 EMA (long-term/institutional)."
        ),
        "signals": {
            "golden_cross": "50 EMA crosses above 200 EMA — powerful long-term bullish signal.",
            "death_cross": "50 EMA crosses below 200 EMA — major bearish signal, often triggers institutional selling.",
            "price_vs_ma": "Price above 200 EMA = bull regime; below = bear regime. Simple, powerful filter.",
            "ma_slope": "Rising 20 EMA in an uptrend = trend intact. Flattening 20 EMA = momentum loss.",
        },
        "professional_use": (
            "The 200-day SMA is watched by every institutional player in the world. NIFTY crossing "
            "its 200 DMA is a major event that triggers algorithmic buying/selling and media coverage. "
            "Many systematic trend-following funds use MA crossover systems as their core signal. "
            "The 20-day EMA acts as dynamic support in uptrends — every test and hold is a buying "
            "opportunity for trend followers."
        ),
        "where_it_fails": (
            "Moving averages are massively lagging — they confirm what already happened. In choppy "
            "markets, they generate constant false crossovers (whipsaws). The more periods in the MA, "
            "the smoother but more lagging. Also, all market participants know the 200 DMA — this "
            "makes it somewhat self-fulfilling but also subject to 'stop hunts' below it."
        ),
        "chart_type": "ema",
        "default_ticker": "^NSEI",
    },
    "vwap": {
        "slug": "vwap",
        "title": "VWAP",
        "category": "volume",
        "tagline": "The institutional price anchor — where the smart money traded.",
        "formula": "VWAP = Σ(Price × Volume) / Σ(Volume)",
        "what": (
            "VWAP (Volume Weighted Average Price) calculates the average price weighted by volume traded. "
            "It resets at the start of each trading day. Unlike simple price averages, VWAP reflects "
            "where the majority of rupee trading happened during the day — it is the fair value anchor "
            "used by institutional execution desks."
        ),
        "signals": {
            "above_vwap": "Price above VWAP = bullish intraday bias; institutions are net buyers.",
            "below_vwap": "Price below VWAP = bearish intraday bias; institutions are net sellers.",
            "vwap_rejection": "Price touches VWAP from above and bounces = strong buying interest at fair value.",
            "vwap_break": "Sustained break above VWAP on volume = trend change intraday.",
        },
        "professional_use": (
            "Every institutional algo uses VWAP as a benchmark. Large orders are broken into slices "
            "to buy/sell at or better than VWAP (VWAP execution algorithms). Retail traders use VWAP "
            "to avoid paying above institutional average. On NSE, watching VWAP reaction in the first "
            "30-60 minutes often defines the day's character. VWAP deviations (Standard Deviation bands "
            "around VWAP) are used for mean-reversion intraday strategies."
        ),
        "where_it_fails": (
            "VWAP is purely intraday — it has no predictive value across days. It also becomes less "
            "meaningful during low-volume sessions. On expiry days, VWAP can be significantly distorted "
            "by derivative rollovers and large block deals. VWAP is a tool for execution, not prediction."
        ),
        "chart_type": "vwap",
        "default_ticker": "^NSEI",
    },
    "atr": {
        "slug": "atr",
        "title": "Average True Range (ATR)",
        "category": "volatility",
        "tagline": "How much does this stock actually move — the volatility ruler.",
        "formula": "TR = max(High−Low, |High−PrevClose|, |Low−PrevClose|)\nATR(14) = EMA(14) of TR",
        "what": (
            "ATR measures the average range of price movement per period, accounting for gaps. "
            "True Range is the greatest of: today's high-low range, high minus yesterday's close, "
            "or yesterday's close minus today's low. ATR(14) smooths this over 14 periods. "
            "ATR tells you how volatile a stock is in absolute terms (rupees per share per day)."
        ),
        "signals": {
            "stop_loss_sizing": "Set stop losses at 1.5–2× ATR below entry to avoid being stopped by noise.",
            "position_sizing": "Risk ₹X per trade → position size = ₹X / (ATR × multiplier).",
            "volatility_breakout": "Price moves > 1.5× ATR from open in one direction = breakout trading signal.",
            "atr_expansion": "Rapidly rising ATR = increasing volatility, consider reducing position size.",
        },
        "professional_use": (
            "ATR-based stop losses are superior to fixed-percentage stops because they adapt to each "
            "stock's actual volatility. A 3% stop on HDFC BANK (low volatility) makes sense; the same "
            "3% on a small-cap (high volatility) would be hit constantly by noise. "
            "Professional traders often risk a fixed fraction (0.5–1%) of portfolio per trade, "
            "sized by ATR: shares = (portfolio × risk %) / (ATR × 2)."
        ),
        "where_it_fails": (
            "ATR does not tell you direction — only magnitude. A large ATR is neutral; it does not "
            "indicate whether the move will be up or down. ATR-based stops may be very wide during "
            "high-volatility periods, forcing you to reduce position sizes significantly or skip trades "
            "with otherwise good setups."
        ),
        "chart_type": "atr",
        "default_ticker": "^NSEI",
    },
    "stochastic": {
        "slug": "stochastic",
        "title": "Stochastic Oscillator",
        "category": "momentum",
        "tagline": "Where does today's close sit relative to recent price range?",
        "formula": "%K = 100 × (Close − Lowest Low₁₄) / (Highest High₁₄ − Lowest Low₁₄)\n%D = SMA(3) of %K",
        "what": (
            "The Stochastic Oscillator measures where the current close sits within the recent high-low range. "
            "A reading of 80 means the close is near the top 20% of the last 14 periods' range — bullish momentum. "
            "A reading of 20 means the close is near the bottom — potential exhaustion. "
            "The %D line (3-period SMA of %K) acts as the signal line."
        ),
        "signals": {
            "overbought": "%K or %D > 80 — price near the top of recent range. Watch for bearish crossover.",
            "oversold": "%K or %D < 20 — price near the bottom of recent range. Watch for bullish crossover.",
            "crossover": "%K crossing above %D below 20 = strong buy signal; crossing below above 80 = strong sell.",
            "divergence": "Price makes new high but Stochastic makes lower high — momentum fading, potential reversal.",
        },
        "professional_use": (
            "Stochastic works best in range-bound markets. Professionals combine it with a trend filter: "
            "only take oversold signals in an uptrend (price > 200 EMA), and only overbought signals in downtrends. "
            "The 'Stochastic divergence' setup — where price makes a new high but %K makes a lower high — "
            "is one of the most reliable reversal setups, especially at major resistance levels."
        ),
        "market_interpretation": (
            "In Indian markets, weekly Stochastic on NIFTY 50 is tracked by many swing traders. "
            "When weekly Stochastic is below 20 AND price is near a key support level, the combination "
            "is high-probability for a multi-week bounce. In the 2022 correction, NIFTY weekly Stochastic "
            "reached deep oversold (<10) twice, both coinciding with strong reversal rallies."
        ),
        "where_it_fails": (
            "Like RSI, Stochastic can stay overbought/oversold for extended periods in trending markets. "
            "A Stochastic reading of 90 in a strong uptrend is not a sell signal — it's a sign of strength. "
            "The 14-period default may be too short for long-term investors and too long for day traders. "
            "Always adjust the period to match your trading timeframe."
        ),
        "chart_type": "stochastic",
        "default_ticker": "^NSEI",
    },
    "obv": {
        "slug": "obv",
        "title": "On Balance Volume (OBV)",
        "category": "volume",
        "tagline": "Volume precedes price — OBV shows where the money is really flowing.",
        "formula": "OBV = Previous OBV + Volume (if Close > Prev Close)\nOBV = Previous OBV − Volume (if Close < Prev Close)",
        "what": (
            "On Balance Volume (OBV) is a cumulative volume indicator developed by Joe Granville. "
            "It adds the full day's volume when the close is up and subtracts it when the close is down. "
            "The idea: institutional accumulation drives OBV up before price moves, and distribution "
            "causes OBV to fall before the price does. OBV is a leading indicator — it often diverges "
            "from price before a major move."
        ),
        "signals": {
            "bullish_divergence": "Price makes lower low but OBV makes higher low — smart money is accumulating despite falling price.",
            "bearish_divergence": "Price makes higher high but OBV makes lower high — distribution happening at highs.",
            "trend_confirmation": "OBV rising with price = healthy uptrend. OBV falling with price = confirmed downtrend.",
            "breakout_confirmation": "OBV breaks to new highs before or with price breakout = high-conviction move.",
        },
        "professional_use": (
            "OBV divergences are considered one of the earliest warning signs of trend reversal. "
            "Hedge funds and institutional desks track OBV on major index ETFs and sector leaders. "
            "Before a bull run, OBV on large-caps typically breaks to new highs while price is still "
            "consolidating — signalling quiet accumulation. The most powerful OBV signal is when "
            "OBV breaks out to an all-time high while price is still 15-20% below its all-time high."
        ),
        "market_interpretation": (
            "In Indian markets, OBV on NIFTY 50 making new highs while the index consolidates is a "
            "strong forward-looking bullish signal. For individual stocks, consistent OBV accumulation "
            "over weeks even during price stagnation is a sign that mutual funds or FIIs are quietly "
            "building positions. This is visible in pre-breakout structures."
        ),
        "where_it_fails": (
            "OBV is highly sensitive to large-volume sessions with small price moves (e.g., expiry days, "
            "block deals). A single massive block deal can skew OBV significantly. Also, OBV ignores "
            "the magnitude of price moves — a 0.01% up day adds the same volume as a 3% up day. "
            "Chaikin Money Flow (CMF) addresses this limitation by weighting volume by price location."
        ),
        "chart_type": "obv",
        "default_ticker": "^NSEI",
    },
    "adx": {
        "slug": "adx",
        "title": "ADX — Average Directional Index",
        "category": "trend",
        "tagline": "How strong is the trend? ADX answers — not the direction, just the strength.",
        "formula": (
            "+DI = 100 × EMA(+DM) / ATR\n"
            "−DI = 100 × EMA(−DM) / ATR\n"
            "ADX = 100 × EMA(|+DI − −DI| / (+DI + −DI))"
        ),
        "what": (
            "ADX (Average Directional Index) measures trend strength on a scale of 0 to 100. "
            "It was developed by J. Welles Wilder (same person who created RSI and ATR). "
            "ADX does NOT tell you direction — only how strong the prevailing trend is. "
            "The companion +DI and -DI lines indicate direction: when +DI is above -DI, the trend is up."
        ),
        "signals": {
            "adx_below_20": "ADX < 20 — range-bound or weak trend. Avoid trend-following strategies; use mean-reversion.",
            "adx_above_25": "ADX > 25 — trend is strengthening. Trend-following systems have an edge.",
            "adx_above_40": "ADX > 40 — very strong trend. Continuation is likely; fade-the-trend trades are dangerous.",
            "di_crossover": "+DI crossing above -DI = bullish trend emerging. -DI crossing above +DI = bearish trend.",
        },
        "professional_use": (
            "ADX is a critical filter for systematic trend-following strategies. Most professional CTAs "
            "(Commodity Trading Advisors) only run their momentum systems when ADX is above 20-25. "
            "Applying ADX as a filter to RSI signals dramatically improves results: take RSI oversold "
            "signals only when ADX > 25 (strong trend), not in directionless markets (ADX < 20). "
            "The transition from ADX below 20 to above 25 is itself a powerful early-trend signal."
        ),
        "market_interpretation": (
            "During the 2023 NIFTY bull run, ADX on the weekly chart consistently stayed above 30, "
            "confirming the trend's strength and validating dip-buying strategies. When NIFTY consolidated "
            "sideways in mid-2024, ADX dropped below 20, correctly signalling that breakout trades were "
            "unreliable. BANKNIFTY often has higher ADX readings than NIFTY due to its sector concentration."
        ),
        "where_it_fails": (
            "ADX lags — it confirms a trend after it has already developed. A reading below 20 doesn't "
            "mean a trend won't emerge; it means one isn't present yet. ADX also doesn't distinguish "
            "between an uptrend and a downtrend at the same reading. Watch +DI/-DI crossovers alongside "
            "ADX for direction context. Also, ADX can peak while the trend is still ongoing — a falling "
            "ADX doesn't necessarily mean the trend is over, just that it's maturing."
        ),
        "chart_type": "adx",
        "default_ticker": "^NSEI",
    },
    "cci": {
        "slug": "cci",
        "title": "CCI — Commodity Channel Index",
        "category": "momentum",
        "tagline": "How far is price from its statistical average? CCI quantifies the deviation.",
        "formula": "CCI = (Typical Price − SMA₂₀) / (0.015 × Mean Deviation)\nTypical Price = (High + Low + Close) / 3",
        "what": (
            "CCI measures how many 'standard deviations' (approximately) the current typical price "
            "is from its 20-period moving average. Unlike RSI which is bounded 0-100, CCI is "
            "unbounded — it can reach +200 or -200 in extreme moves. Developed by Donald Lambert for "
            "commodities but equally applicable to equities and indices."
        ),
        "signals": {
            "above_100": "CCI > +100 — price significantly above its recent average. Strong upward momentum; entering overbought territory.",
            "below_minus_100": "CCI < -100 — price significantly below its recent average. Strong downward momentum; entering oversold territory.",
            "zero_cross": "CCI crossing above 0 from below = new bullish momentum; crossing below 0 = bearish shift.",
            "divergence": "Classic divergence pattern: higher price high + lower CCI high = bearish divergence.",
        },
        "professional_use": (
            "CCI is particularly popular among commodity traders and swing traders. The '±100 breakout' "
            "system — buying when CCI crosses above +100 and selling when it falls below +100 — "
            "performs well in trending markets. CCI on weekly charts identifies multi-week momentum cycles. "
            "Institutional desks use CCI to time entry into trending positions: a pullback that holds "
            "above CCI 0 (while the longer-term trend is up) is a quality setup."
        ),
        "market_interpretation": (
            "NIFTY CCI crossing above +100 historically correlates with strong continuation of the "
            "current move. In the 2020 V-shaped recovery, CCI shot to +200+ as the recovery was "
            "both rapid and sustained. CCI oscillating between -100 and +100 without reaching extremes "
            "usually signals a consolidating, range-bound market — reduce position sizes in such periods."
        ),
        "where_it_fails": (
            "CCI can stay extreme for extended periods in strong trends — a +150 CCI doesn't always "
            "mean 'sell'. The 0.015 constant was chosen to keep 70-80% of CCI values between ±100 "
            "under normal conditions, but this assumption breaks down for highly volatile assets. "
            "CCI is best used as a confirmation tool alongside price structure and volume, not in isolation."
        ),
        "chart_type": "cci",
        "default_ticker": "^NSEI",
    },
    "williams-r": {
        "slug": "williams-r",
        "title": "Williams %R",
        "category": "momentum",
        "tagline": "Inverse of Stochastic — where is the close relative to the high of the period?",
        "formula": "%R = −100 × (Highest High₁₄ − Close) / (Highest High₁₄ − Lowest Low₁₄)",
        "what": (
            "Williams %R (developed by Larry Williams) is the inverse of the Stochastic Oscillator, "
            "scaled from 0 to -100. A reading near 0 means the close is near the highest high of the "
            "period (bullish). A reading near -100 means the close is near the lowest low (bearish). "
            "Typical overbought threshold: -20. Oversold threshold: -80."
        ),
        "signals": {
            "overbought": "%R between 0 and -20 — price at top of recent range. Potential exhaustion point.",
            "oversold": "%R between -80 and -100 — price at bottom of recent range. Potential reversal zone.",
            "failure_swing": "Price makes new low but %R doesn't reach -80 or makes a higher low = bullish momentum shift.",
            "momentum_buy": "%R rising from -100 toward -50 while price is above 200 EMA = momentum building setup.",
        },
        "professional_use": (
            "Larry Williams famously used %R as part of his system to win the World Cup Trading Championship. "
            "He popularised the concept of trading from oversold in uptrends and overbought in downtrends. "
            "A particularly high-conviction setup: %R reaches -100 (maximum oversold, close equals the "
            "period low) and then immediately rallies — this signals exhaustive selling and a high-probability "
            "reversal. Williams %R is nearly identical to Stochastic %K but scaled differently."
        ),
        "market_interpretation": (
            "Williams %R on daily chart for individual NSE stocks reaching -90 to -100 after a prolonged "
            "downtrend, coinciding with a sector rotation catalyst, has historically been a strong entry point. "
            "The 14-period default captures 2.5 weeks of trading — appropriate for swing trading setups. "
            "For day traders, 5-period %R on 15-minute charts is popular for intraday mean reversion."
        ),
        "where_it_fails": (
            "Like all oscillators, Williams %R generates many false signals in strongly trending markets. "
            "A stock in free fall will repeatedly touch -100 without bouncing. The indicator must always "
            "be combined with a trend context — never use it standalone for entries in a downtrending "
            "stock. Also, the lack of smoothing (unlike %D in Stochastic) makes it more noisy."
        ),
        "chart_type": "williams_r",
        "default_ticker": "^NSEI",
    },
    "roc": {
        "slug": "roc",
        "title": "Rate of Change (ROC)",
        "category": "momentum",
        "tagline": "Pure price momentum — how much has the stock moved in the last N periods?",
        "formula": "ROC = ((Close − Close_n) / Close_n) × 100",
        "what": (
            "Rate of Change (ROC) is the simplest momentum indicator — it measures the percentage change "
            "in price over a specified number of periods. ROC > 0 means the stock is higher than N periods "
            "ago; ROC < 0 means it is lower. It oscillates around zero with no upper/lower bounds. "
            "ROC essentially answers: 'Is momentum increasing or decreasing?'"
        ),
        "signals": {
            "positive_roc": "ROC > 0 — the stock has gained over the lookback period; upward momentum.",
            "negative_roc": "ROC < 0 — the stock has fallen; downward momentum.",
            "zero_cross": "ROC crossing above 0 = bullish momentum trigger; below 0 = bearish.",
            "divergence": "Price makes new high but ROC makes lower high = waning momentum, potential reversal.",
        },
        "professional_use": (
            "ROC is the foundation of many momentum-based factor strategies. Quantitative funds use "
            "12-month ROC (excluding the most recent month to avoid short-term reversal effects) as the "
            "primary momentum factor in stock selection — this is the 'Jegadeesh-Titman momentum' used in "
            "most factor investing frameworks. NSE SmallCap momentum indices use 6-month ROC as a "
            "primary factor. Stocks with ROC in the top quintile of their universe consistently "
            "outperform over 3-12 month horizons in most market conditions."
        ),
        "market_interpretation": (
            "A simple ROC-based screener: identify NIFTY 500 stocks with 3-month ROC > 20% AND "
            "the ROC is still rising. This catches stocks in early-stage outperformance before they "
            "become crowded trades. Conversely, stocks with 3-month ROC below -20% and still falling "
            "are in distribution — avoid until ROC stabilises above -5%."
        ),
        "where_it_fails": (
            "ROC has no smoothing — it's highly sensitive to the specific period used. A stock with "
            "strong 12-month ROC may have terrible 1-month ROC (recent weakness). This is why factor "
            "funds typically exclude the most recent month (use 12-1 month ROC). Also, ROC compares "
            "to a single point in time — it can be distorted by one extreme day. "
        ),
        "chart_type": "roc",
        "default_ticker": "^NSEI",
    },
    "mfi": {
        "slug": "mfi",
        "title": "Money Flow Index (MFI)",
        "category": "volume",
        "tagline": "RSI with volume — a stronger overbought/oversold signal.",
        "formula": (
            "Typical Price = (H + L + C) / 3\n"
            "Raw Money Flow = Typical Price × Volume\n"
            "MFI = 100 − 100 / (1 + Positive Money Flow / Negative Money Flow)"
        ),
        "what": (
            "The Money Flow Index is a volume-weighted version of RSI. It uses typical price AND volume "
            "to assess buying and selling pressure. When typical price is higher than the previous period's, "
            "it's 'positive money flow' — volume is added. When lower, it's 'negative money flow'. "
            "The ratio of positive to negative money flow over 14 periods produces the MFI oscillator (0-100)."
        ),
        "signals": {
            "overbought": "MFI > 80 — both price and volume indicate excess buying pressure. High reversal risk.",
            "oversold": "MFI < 20 — both price and volume indicate excess selling pressure. Potential bounce.",
            "divergence": "Price rising but MFI falling = volume not confirming the rally — weak move, likely to reverse.",
            "volume_confirmed": "MFI and price both at new highs = high-conviction breakout backed by real buying volume.",
        },
        "professional_use": (
            "MFI divergences are considered more reliable than RSI divergences because they incorporate "
            "volume confirmation. A stock where price makes a new 52-week high but MFI is at a 6-month "
            "low means institutions are distributing — reducing quantity while maintaining price, "
            "a classic distribution pattern. Professional fund managers track MFI alongside price "
            "to confirm their fundamental thesis with technical/volume data."
        ),
        "market_interpretation": (
            "In Indian markets, MFI oversold readings (<20) in quality large-caps during broader market "
            "selloffs (budget day, Fed announcement, geopolitical shock) have historically been excellent "
            "entry points when the fundamental thesis remains intact. MFI on sector indices also helps "
            "identify sector rotation: a sector ETF with rising MFI while the broader index MFI is flat "
            "signals capital rotation into that sector."
        ),
        "where_it_fails": (
            "Like all volume-based indicators, MFI can be distorted by bulk deals, institutional block "
            "trades, and expiry-day volumes. A single day with extremely high volume and a small price "
            "move can dominate the MFI calculation. Also, MFI assumes all volume on up-days is 'buying' "
            "and all volume on down-days is 'selling' — a crude approximation of actual order flow."
        ),
        "chart_type": "mfi",
        "default_ticker": "^NSEI",
    },
    "ichimoku": {
        "slug": "ichimoku",
        "title": "Ichimoku Cloud",
        "category": "trend",
        "tagline": "Five lines, one chart — Japan's complete trend analysis system.",
        "formula": (
            "Tenkan-sen (Conversion) = (9H + 9L) / 2\n"
            "Kijun-sen (Base) = (26H + 26L) / 2\n"
            "Senkou Span A = (Tenkan + Kijun) / 2, plotted 26 periods ahead\n"
            "Senkou Span B = (52H + 52L) / 2, plotted 26 periods ahead\n"
            "Chikou Span = Current close, plotted 26 periods back"
        ),
        "what": (
            "Ichimoku Kinko Hyo ('one look equilibrium chart') is a complete technical system developed "
            "by Japanese journalist Goichi Hosoda in the 1930s. It shows trend direction, momentum, "
            "support, and resistance in a single chart using five lines. The 'cloud' (Kumo) between "
            "Senkou Span A and B is the most distinctive feature — price above the cloud is bullish, "
            "below is bearish, and inside is transitional."
        ),
        "signals": {
            "tk_cross": "Tenkan-sen crosses above Kijun-sen above the cloud = strong bullish signal (TK cross).",
            "cloud_breakout": "Price breaks above the cloud with expanding cloud = high-conviction bull trend.",
            "kumo_twist": "Span A crosses above Span B in the future cloud = future trend turning bullish.",
            "chikou_space": "Chikou Span (lagging line) above price/cloud 26 periods ago = trend confirmation.",
        },
        "professional_use": (
            "Ichimoku is widely used by Japanese institutional traders and has gained global adoption. "
            "The cloud provides dynamic support/resistance that self-adjusts to volatility. A stock "
            "above a thick, rising cloud is considered one of the strongest technical structures. "
            "The best Ichimoku setups require all five components to align: "
            "price above cloud, TK cross above cloud, Chikou Span above past price, and future cloud bullish."
        ),
        "market_interpretation": (
            "NIFTY 50 on weekly Ichimoku charts is tracked by technical analysts in institutional desk notes. "
            "When NIFTY is above the weekly cloud AND the cloud is rising AND the Chikou Span is above the "
            "cloud = full Ichimoku bull confirmation. This combination has historically marked sustained "
            "bull phases in Indian markets. The cloud acts as a 'bounce zone' during pullbacks."
        ),
        "where_it_fails": (
            "Ichimoku was designed for Japanese equity markets and the parameters (9, 26, 52) work best "
            "on daily charts. On intraday charts or with different market structures, the parameters may "
            "need adjustment. Also, the system generates a lot of information and can be overwhelming — "
            "beginners should master each component before using the full system. The 26-period lead/lag "
            "makes the chart visually complex."
        ),
        "chart_type": "ichimoku",
        "default_ticker": "^NSEI",
    },
    "parabolic-sar": {
        "slug": "parabolic-sar",
        "title": "Parabolic SAR",
        "category": "trend",
        "tagline": "A dynamic trailing stop — it follows price and tells you when the trend flips.",
        "formula": "SAR = Previous SAR + AF × (EP − Previous SAR)\nAF starts at 0.02, increases by 0.02 per new extreme, max 0.20\nEP = Extreme Point (highest high in uptrend / lowest low in downtrend)",
        "what": (
            "Parabolic SAR (Stop and Reverse) was developed by J. Welles Wilder. It plots a series of "
            "dots above or below price — dots below price signal an uptrend, dots above signal a downtrend. "
            "When price crosses the SAR dots, the trend reverses and the SAR flips to the other side. "
            "The 'parabolic' name comes from the accelerating factor (AF) that makes SAR catch up faster "
            "as the trend matures."
        ),
        "signals": {
            "uptrend": "SAR dots below price — hold long, use SAR as trailing stop-loss.",
            "downtrend": "SAR dots above price — stay out or short, SAR is resistance.",
            "flip": "Price crosses SAR and dots move to opposite side — exit current trade and consider reversing.",
            "tight_trailing": "As AF increases (new price extremes made), SAR tightens rapidly — expect trend exhaustion if price can't keep up.",
        },
        "professional_use": (
            "Parabolic SAR is primarily used as a trailing stop-loss tool rather than an entry signal. "
            "In a strong uptrend, SAR provides a systematic, emotionless method to trail stops upward. "
            "Many professional traders enter on their own signals (breakout, reversal pattern) but use "
            "SAR to manage the exit — the dot below current price becomes the stop. "
            "The accelerating factor is the key feature: SAR becomes a very tight stop near trend exhaustion."
        ),
        "market_interpretation": (
            "Parabolic SAR works exceptionally well in trending phases of NIFTY and sector indices. "
            "During NIFTY's 2020-2022 bull run, the daily SAR dots stayed below price for extended periods, "
            "providing clear trailing stops for position traders. When SAR flipped above price during "
            "corrections, it provided early warning of regime change. The indicator is less useful during "
            "NIFTY's sideways consolidation phases (common after sharp rallies)."
        ),
        "where_it_fails": (
            "In sideways markets, Parabolic SAR whipsaws constantly — it flips above and below price "
            "repeatedly, generating small losses on every trade. This is its primary weakness. "
            "It should only be used when ADX > 25 (trend is present). Also, the default AF settings "
            "(0.02 step, 0.20 max) were designed for commodity markets — equity traders sometimes use "
            "a slower AF (0.01 step, 0.10 max) to reduce whipsaws."
        ),
        "chart_type": "parabolic_sar",
        "default_ticker": "^NSEI",
    },
}

OPTIONS = {
    "calls-puts": {
        "slug": "calls-puts",
        "title": "Calls & Puts: The Basics",
        "category": "options",
        "tagline": "The right to buy or sell — asymmetric payoffs change everything.",
        "what": (
            "A Call Option gives the buyer the right (not obligation) to buy the underlying at a fixed "
            "price (strike) by a fixed date (expiry). A Put Option gives the buyer the right to sell "
            "at the strike. Option buyers pay premium upfront; their maximum loss is that premium. "
            "Option sellers collect premium upfront; their maximum loss is theoretically unlimited "
            "(for naked calls) or large (for puts)."
        ),
        "payoff_call": "Buyer profit = max(0, S−K) − Premium;  Seller profit = Premium − max(0, S−K)",
        "payoff_put":  "Buyer profit = max(0, K−S) − Premium;  Seller profit = Premium − max(0, K−S)",
        "why": (
            "Options allow leveraged, defined-risk exposure. A ₹100 premium buys the right to control "
            "a ₹1000 underlying — that's 10× leverage. If the underlying doubles, a correctly positioned "
            "call can return 10×+. Critically, the buyer's risk is capped at the premium paid while "
            "the upside is theoretically unlimited. This asymmetry is fundamental to options' appeal."
        ),
        "market_context": (
            "On NSE, options are cash-settled on the expiry date. Weekly NIFTY and BANKNIFTY options "
            "expire every Thursday. Monthly options expire on the last Thursday of the month. "
            "Lot size for NIFTY is 25 (as of 2025). With NIFTY at 24,000 and ATM straddle premium "
            "of ₹300, buying one lot of straddle costs ₹7,500 (300 × 25)."
        ),
        "where_it_fails": (
            "Option buyers fight against time decay (Theta). Even if you are directionally correct, "
            "if the move is too slow, Theta erodes the premium daily. More than 80% of options "
            "expire worthless — this is why systematic option selling (with defined risk through spreads) "
            "has a structural edge. Buying cheap OTM options on directional bets is statistically losing."
        ),
        "chart_type": "payoff",
    },
    "delta": {
        "slug": "delta",
        "title": "Delta (Δ)",
        "category": "greeks",
        "tagline": "How much does my option move when the stock moves ₹1?",
        "formula": "Δ = ∂V / ∂S   (change in option price / change in underlying price)",
        "what": (
            "Delta represents how much an option's price changes for a ₹1 move in the underlying. "
            "ATM options have Δ ≈ 0.5 (call) / -0.5 (put). Deep ITM call Δ → 1.0. "
            "Far OTM call Δ → 0.0. Delta also approximates the probability of an option expiring "
            "in-the-money (a 0.30 delta call has ~30% chance of being ITM at expiry)."
        ),
        "interpretation": {
            "delta_0.9": "Deep ITM call — behaves almost like owning the stock itself. Low leverage.",
            "delta_0.5": "ATM call — 50% chance ITM. Highest gamma, most sensitive to moves.",
            "delta_0.2": "OTM call — cheap in premium but low probability. High lottery-like leverage.",
        },
        "professional_use": (
            "Delta-hedging: Market makers buy/sell underlying shares to offset option delta, "
            "maintaining a delta-neutral book. They earn the spread between implied and realised volatility. "
            "Portfolio managers use delta to calculate total market exposure: a 0.7 delta option on "
            "100 shares has the same directional exposure as 70 shares of stock. "
            "Optimal delta for directional trades: 0.35–0.50 (good probability + meaningful premium)."
        ),
        "chart_type": "greek",
        "greek_name": "delta",
    },
    "theta": {
        "slug": "theta",
        "title": "Theta (Θ) — Time Decay",
        "category": "greeks",
        "tagline": "Options are wasting assets — every day, premium evaporates.",
        "formula": "Θ = ∂V / ∂t   (change in option price / change in time)",
        "what": (
            "Theta measures how much an option loses in value per day as time passes, all else equal. "
            "An option with Θ = -5 loses ₹5 in value per day. Time decay is not linear — it "
            "accelerates dramatically in the last 30 days, and most violently in the last week. "
            "ATM options have the highest theta in absolute terms."
        ),
        "interpretation": {
            "buyer_perspective": "Every day you hold an option, you lose Θ. Time is your enemy as a buyer.",
            "seller_perspective": "Every day that passes, you collect Θ. Time is your ally as a seller.",
            "expiry_week": "On weekly options, ATM options can decay 15–25% of their value in a single day near expiry.",
        },
        "professional_use": (
            "Option sellers (theta farmers) specifically target high-IV environments to sell premium "
            "and collect accelerated theta decay. Selling weekly straddles on NIFTY when IV is elevated "
            "is a well-known institutional strategy. Buyers must understand theta cost: "
            "if you buy an ATM call for ₹200 with Θ = -10, and the stock doesn't move, "
            "you lose ₹10/day — you need the stock to move enough to overcome this."
        ),
        "chart_type": "greek",
        "greek_name": "theta",
    },
    "gamma": {
        "slug": "gamma",
        "title": "Gamma (Γ)",
        "category": "greeks",
        "tagline": "The rate of change of delta — where options become explosive.",
        "formula": "Γ = ∂Δ / ∂S = ∂²V / ∂S²",
        "what": (
            "Gamma measures how much Delta changes for a ₹1 move in the underlying. "
            "If Delta is the speed, Gamma is the acceleration. ATM options have the highest Gamma. "
            "High Gamma means your position becomes more (or less) directional very quickly "
            "as the underlying moves. This is both opportunity and risk."
        ),
        "interpretation": {
            "atm_gamma": "ATM options have highest gamma — small moves create rapid delta changes.",
            "near_expiry": "Gamma spikes dramatically near expiry — ATM options become binary bets.",
            "gamma_squeeze": "Large short gamma positions force market makers to buy the underlying aggressively, amplifying moves.",
        },
        "professional_use": (
            "The 2021 GameStop short squeeze was partly a gamma squeeze: as GME rose, market makers "
            "with short calls had to buy more stock to stay delta-neutral, pushing price higher, "
            "creating more gamma exposure, forcing more buying — a feedback loop. "
            "On NSE, gamma risk is highest on expiry day for near-ATM strikes. "
            "Gamma scalping (buying gamma and delta-hedging constantly) is a strategy to earn "
            "from large intraday moves regardless of direction."
        ),
        "chart_type": "greek",
        "greek_name": "gamma",
    },
    "vega": {
        "slug": "vega",
        "title": "Vega (ν)",
        "category": "greeks",
        "tagline": "How much does IV change my option price?",
        "formula": "ν = ∂V / ∂σ   (change in option price / change in implied volatility)",
        "what": (
            "Vega measures how much an option's price changes for a 1% change in implied volatility. "
            "An option with ν = 8 gains ₹8 in value if IV rises 1%. Long options (buyer) have positive "
            "vega — they benefit from rising IV. Short options (seller) have negative vega — "
            "they suffer when IV rises. ATM options have the highest vega; far OTM have low vega."
        ),
        "interpretation": {
            "iv_expansion": "IV rising (fear) → option prices rise → option buyers profit, sellers lose.",
            "iv_compression": "IV falling (IV crush) → option prices fall rapidly after events (earnings, budget).",
            "iv_crush": "After a known event (election result), IV collapses 40–60% overnight — option buyers often lose even if directionally correct.",
        },
        "professional_use": (
            "IV crush is one of the most dangerous phenomena for options buyers. Before major Indian "
            "events (Union Budget, RBI policy, election results), IV spikes to extreme levels. "
            "Option buyers who are correct about direction but hold through the announcement often "
            "still lose money because IV collapses post-event. Professionals manage vega exposure: "
            "they either delta-hedge their vega, sell before the event, or use spreads to reduce vega risk."
        ),
        "chart_type": "greek",
        "greek_name": "vega",
    },
    "iv-crush": {
        "slug": "iv-crush",
        "title": "IV Crush",
        "category": "greeks",
        "tagline": "Why you can be right about direction and still lose money on options.",
        "what": (
            "IV Crush occurs when implied volatility collapses sharply after a major event — "
            "typically immediately after earnings, policy announcements, or election results. "
            "Before the event, uncertainty drives IV (and therefore option premiums) very high. "
            "Once the event passes (regardless of outcome), uncertainty resolves and IV plummets, "
            "taking option prices down with it — even if the underlying moved in your direction."
        ),
        "example": (
            "Scenario: INFY is at ₹1500. Quarterly results tomorrow. ATM call (1500 strike, 1 week expiry) "
            "is priced at ₹80 (reflecting 35% IV). Results beat expectations — INFY opens +3% at ₹1545. "
            "The call should be worth ₹45 intrinsically, but IV collapses from 35% to 18%. "
            "The call is now priced at ₹52. The option buyer was directionally correct but still lost ₹28 (35%)."
        ),
        "how_to_navigate": (
            "1. Sell options before the event to collect inflated IV, then buy back after IV crush. "
            "2. Use spreads (buy ATM, sell OTM) to reduce vega exposure while maintaining direction. "
            "3. Buy options well before the event builds IV — buy when IV is still low. "
            "4. Understand the IV term structure: weeklies get crushed far more than monthlies."
        ),
        "chart_type": "iv_crush",
    },
}
