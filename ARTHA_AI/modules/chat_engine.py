"""
ARTHA AI — Market Chat Engine
Rule-based conversational intelligence for stock analysis queries.
"""

import re
from datetime import datetime


# ─── Response Templates ──────────────────────────────────────────────────────

def _rsi_interpretation(rsi: float) -> str:
    if rsi < 30:
        return f"RSI at {rsi:.1f} — **deeply oversold** territory. Historically, this signals a high-probability reversal zone. Risk: further selling if broader market weak."
    elif rsi < 40:
        return f"RSI at {rsi:.1f} — **oversold**. Buying interest may emerge. Watch for reversal candles."
    elif rsi < 55:
        return f"RSI at {rsi:.1f} — **neutral zone**. No strong momentum in either direction."
    elif rsi < 70:
        return f"RSI at {rsi:.1f} — **building momentum**. Trend is strengthening but not yet overbought."
    else:
        return f"RSI at {rsi:.1f} — **overbought**. Profit-booking risk increases. Wait for pullback before fresh entry."


def _trend_interpretation(trend: str, ma20: float, ma50: float, close: float) -> str:
    if trend == "BULLISH":
        return (f"Primary trend: **BULLISH**. MA20 (₹{ma20:.0f}) above MA50 (₹{ma50:.0f}), "
                f"price (₹{close:.0f}) respecting moving averages. Golden Cross formation in effect.")
    elif trend == "BEARISH":
        return (f"Primary trend: **BEARISH**. MA20 (₹{ma20:.0f}) below MA50 (₹{ma50:.0f}), "
                f"indicating a Death Cross. Selling pressure dominant.")
    else:
        return (f"Trend: **SIDEWAYS / CONSOLIDATION**. MA20 ₹{ma20:.0f} and MA50 ₹{ma50:.0f} "
                f"converging. Breakout direction unclear — wait for confirmation.")


def _volume_interpretation(vol_spike: float) -> str:
    if vol_spike > 100:
        return f"Volume spike: **{vol_spike:+.0f}% above 20-day average** — institutional activity likely. High conviction move."
    elif vol_spike > 50:
        return f"Volume spike: **{vol_spike:+.0f}%** — significant accumulation/distribution signal."
    elif vol_spike > 20:
        return f"Volume: **{vol_spike:+.0f}% above average** — moderate participation."
    elif vol_spike < -30:
        return f"Volume: **{vol_spike:+.0f}% below average** — low conviction, choppy price action expected."
    else:
        return f"Volume: **Normal range ({vol_spike:+.0f}%)**. No unusual institutional activity detected."


def _support_resistance_interpretation(close: float, support: float, resistance: float) -> str:
    dist_to_support = (close - support) / close * 100
    dist_to_resistance = (resistance - close) / close * 100
    return (f"Support: ₹{support:.0f} ({dist_to_support:.1f}% below current price). "
            f"Resistance: ₹{resistance:.0f} ({dist_to_resistance:.1f}% above). "
            f"Risk-reward ratio: **{dist_to_resistance:.1f}:{dist_to_support:.1f}**.")


def _verdict(signal: str, confidence: int, indicators: dict) -> tuple:
    """Returns (verdict_text, verdict_type)"""
    rsi = indicators.get("rsi", 50)
    trend = indicators.get("trend", "SIDEWAYS")

    if signal in ("STRONG_BUY", "BUY"):
        verdict_type = "BUY"
        text = (f"**BUY** — Confidence: **{confidence}%**\n\n"
                f"Multiple indicators align bullishly. "
                f"{'RSI in accumulation zone. ' if rsi < 45 else ''}"
                f"{'Trend momentum is your ally. ' if trend == 'BULLISH' else ''}"
                f"Entry near support ₹{indicators.get('support', 0):.0f} offers asymmetric risk-reward.")
    elif signal == "WATCH":
        verdict_type = "WATCH"
        text = (f"**WATCH** — Confidence: **{confidence}%**\n\n"
                f"Setup is developing but not fully confirmed. "
                f"Add to watchlist and wait for volume confirmation or a clean breakout above resistance.")
    elif signal == "HOLD":
        verdict_type = "HOLD"
        text = (f"**HOLD** — Confidence: **{confidence}%**\n\n"
                f"No strong buy or sell signal. If already invested, hold with stop-loss at ₹{indicators.get('support', 0):.0f}. "
                f"Fresh positions not advised until clearer direction.")
    elif signal == "CAUTION":
        verdict_type = "CAUTION"
        text = (f"**CAUTION / REDUCE EXPOSURE** — Confidence: **{confidence}%**\n\n"
                f"Weakening technicals. Consider booking partial profits. "
                f"RSI: {rsi:.1f}. Trend: {trend}.")
    else:
        verdict_type = "AVOID"
        text = (f"**AVOID** — Confidence: **{confidence}%**\n\n"
                f"Bearish signals dominant. Not suitable for fresh buying. "
                f"{'RSI overbought — selling pressure likely.' if rsi > 65 else ''} "
                f"Wait for technical structure to improve.")

    return text, verdict_type


# ─── Main Chat Function ──────────────────────────────────────────────────────

def artha_chat(
    query: str,
    symbol: str,
    indicators: dict,
    signal_data: dict,
    breakout_data: dict,
    stock_info: dict,
) -> dict:
    """
    Main chat engine. Takes a user query + stock context and returns
    a structured analytical response.

    Returns dict with keys: analysis, key_signals, risk_factors, verdict, why, verdict_type
    """
    query_lower = query.lower()

    # Parse query intent
    intent_map = {
        "buy": ["buy", "purchase", "entry", "accumulate", "invest"],
        "sell": ["sell", "exit", "book", "profit"],
        "risk": ["risk", "safe", "dangerous", "volatile"],
        "trend": ["trend", "direction", "uptrend", "downtrend"],
        "target": ["target", "upside", "potential", "where is it going"],
        "overview": ["analysis", "overview", "tell me", "what do you think", "should i"],
    }

    detected_intent = "overview"
    for intent, keywords in intent_map.items():
        if any(kw in query_lower for kw in keywords):
            detected_intent = intent
            break

    rsi = indicators.get("rsi", 50)
    trend = indicators.get("trend", "SIDEWAYS")
    close = indicators.get("close", 0)
    ma20 = indicators.get("ma20", close)
    ma50 = indicators.get("ma50", close)
    vol_spike = indicators.get("volume_spike_pct", 0)
    support = indicators.get("support", 0)
    resistance = indicators.get("resistance", 0)
    signal = signal_data.get("signal", "HOLD")
    confidence = signal_data.get("confidence", 50)
    sector = stock_info.get("sector", "N/A")
    company = stock_info.get("name", symbol)
    pattern = breakout_data.get("type", "CONSOLIDATING")
    pattern_desc = breakout_data.get("description", "")

    # ── 1. ANALYSIS ──────────────────────────────────────────────────────────
    analysis = (
        f"**{company}** ({symbol}) | Sector: **{sector}** | CMP: ₹{close:.2f}\n\n"
        f"The stock is currently in a **{trend}** phase. "
        f"Chart pattern: **{pattern.replace('_', ' ')}** — {pattern_desc}\n\n"
        f"Price is {'+' if close > (ma20 or close) else ''}{((close - (ma20 or close)) / (ma20 or close) * 100):.1f}% "
        f"relative to its 20-day moving average."
    )

    # ── 2. KEY SIGNALS ───────────────────────────────────────────────────────
    key_signals = [
        f"📊 **RSI**: {_rsi_interpretation(rsi)}",
        f"📈 **Trend**: {_trend_interpretation(trend, ma20 or close, ma50 or close, close)}",
        f"🔊 **Volume**: {_volume_interpretation(vol_spike)}",
        f"🎯 **S&R**: {_support_resistance_interpretation(close, support, resistance)}",
        f"⚡ **MACD**: {'Bullish crossover — momentum building.' if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else 'Bearish — momentum fading.'}",
    ]

    # ── 3. RISK FACTORS ──────────────────────────────────────────────────────
    risks = []
    if rsi > 70:
        risks.append("🔴 **Overbought RSI** — short-term correction risk is elevated.")
    if trend == "BEARISH":
        risks.append("🔴 **Bearish trend** — buying into weakness carries higher risk.")
    if vol_spike < -20:
        risks.append("🟡 **Low volume** — price moves on thin volume may not sustain.")
    if pattern == "BREAKDOWN":
        risks.append("🔴 **Breakdown pattern** — support violation signals further downside.")
    if close < (ma50 or close):
        risks.append("🟡 **Price below MA50** — medium-term trend unfavorable.")
    if not risks:
        risks.append("🟢 **No critical risk flags** — technicals relatively clean.")
    risks.append("⚠️ **General**: Markets are inherently uncertain. Always use stop-losses.")

    # ── 4 & 5. VERDICT + WHY ─────────────────────────────────────────────────
    verdict_text, verdict_type = _verdict(signal, confidence, indicators)

    why = (
        f"This verdict is driven by: **{trend} trend** + RSI at **{rsi:.1f}** + "
        f"Volume **{vol_spike:+.0f}%** vs average + **{pattern.replace('_', ' ')}** pattern. "
        f"Overall composite score: **{signal_data.get('score', 0):+d} / 90** on ARTHA's proprietary scoring model."
    )

    return {
        "analysis": analysis,
        "key_signals": key_signals,
        "risk_factors": risks,
        "verdict": verdict_text,
        "verdict_type": verdict_type,
        "why": why,
        "timestamp": datetime.now().strftime("%H:%M:%S IST, %d %b %Y"),
    }


# ─── Simple Query Router ──────────────────────────────────────────────────────

def handle_generic_query(query: str) -> str:
    """Handle queries not tied to a specific stock."""
    q = query.lower()
    if "nifty" in q or "market" in q:
        return "Please select a specific NSE stock in the sidebar for detailed analysis. For Nifty, try NIFTY50 or use ^NSEI."
    if "how" in q and "work" in q:
        return "ARTHA AI combines RSI, Moving Averages, Volume analysis, MACD, and Bollinger Bands to generate composite signals with confidence scores."
    if "help" in q:
        return "Try asking: 'Should I buy Reliance?', 'What's the trend for TCS?', 'Is HDFC Bank risky?'"
    return "Please load a stock first using the ticker search, then ask your analysis question."
