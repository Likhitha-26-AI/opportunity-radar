"""
ARTHA AI — Signal Generation Engine
Converts technical indicators into BUY / SELL / HOLD / WATCH signals with confidence scores.
"""

import pandas as pd
import numpy as np
from modules.indicators import compute_all_indicators


# ─── Signal Classification ───────────────────────────────────────────────────

def classify_rsi(rsi: float) -> tuple:
    """Returns (signal, score_contribution)"""
    if rsi < 30:
        return "OVERSOLD", 25
    elif rsi < 45:
        return "BULLISH_BIAS", 15
    elif rsi > 70:
        return "OVERBOUGHT", -20
    elif rsi > 60:
        return "BEARISH_BIAS", -10
    else:
        return "NEUTRAL", 0


def classify_volume(spike_pct: float) -> tuple:
    if spike_pct > 100:
        return "EXTREME_VOLUME", 20
    elif spike_pct > 50:
        return "HIGH_VOLUME", 12
    elif spike_pct > 20:
        return "ABOVE_AVG_VOLUME", 6
    elif spike_pct < -30:
        return "LOW_VOLUME", -8
    else:
        return "NORMAL_VOLUME", 0


def classify_trend(trend: str) -> tuple:
    if trend == "BULLISH":
        return "UPTREND", 20
    elif trend == "BEARISH":
        return "DOWNTREND", -20
    else:
        return "SIDEWAYS", 0


def classify_macd(macd: float, macd_signal: float) -> tuple:
    if macd > macd_signal and macd > 0:
        return "MACD_BULLISH", 15
    elif macd > macd_signal and macd < 0:
        return "MACD_CROSSING_UP", 8
    elif macd < macd_signal and macd < 0:
        return "MACD_BEARISH", -15
    elif macd < macd_signal and macd > 0:
        return "MACD_CROSSING_DOWN", -8
    else:
        return "MACD_NEUTRAL", 0


def classify_price_vs_ma(close: float, ma20: float, ma50: float) -> tuple:
    score = 0
    label = []
    if close > ma20:
        score += 8
        label.append("ABOVE_MA20")
    else:
        score -= 8
        label.append("BELOW_MA20")
    if ma50 and close > ma50:
        score += 7
        label.append("ABOVE_MA50")
    elif ma50:
        score -= 7
        label.append("BELOW_MA50")
    return "+".join(label), score


# ─── Master Signal Generator ─────────────────────────────────────────────────

def generate_signal(indicators: dict) -> dict:
    """
    Given computed indicators, generate a final signal with confidence.
    Returns dict: {signal, confidence, signals_breakdown, score}
    """
    if not indicators:
        return {
            "signal": "NO_DATA",
            "confidence": 0,
            "signals_breakdown": [],
            "score": 0,
        }

    score = 0
    breakdown = []

    # RSI
    rsi_label, rsi_score = classify_rsi(indicators["rsi"])
    score += rsi_score
    breakdown.append({"indicator": "RSI", "value": indicators["rsi"], "signal": rsi_label, "weight": rsi_score})

    # Volume
    vol_label, vol_score = classify_volume(indicators["volume_spike_pct"])
    score += vol_score
    breakdown.append({"indicator": "VOLUME", "value": f"{indicators['volume_spike_pct']:+.1f}%", "signal": vol_label, "weight": vol_score})

    # Trend
    trend_label, trend_score = classify_trend(indicators["trend"])
    score += trend_score
    breakdown.append({"indicator": "TREND", "value": indicators["trend"], "signal": trend_label, "weight": trend_score})

    # MACD
    macd_label, macd_score = classify_macd(indicators["macd"], indicators["macd_signal"])
    score += macd_score
    breakdown.append({"indicator": "MACD", "value": f"{indicators['macd']:.4f}", "signal": macd_label, "weight": macd_score})

    # Price vs MA
    if indicators["ma20"] and indicators["ma50"]:
        ma_label, ma_score = classify_price_vs_ma(indicators["close"], indicators["ma20"], indicators["ma50"])
        score += ma_score
        breakdown.append({"indicator": "PRICE_VS_MA", "value": f"₹{indicators['close']}", "signal": ma_label, "weight": ma_score})

    # Normalize to 0-100 confidence
    max_possible = 90
    confidence = min(100, max(0, int((score + max_possible) / (2 * max_possible) * 100)))

    # Final signal classification
    if score >= 35:
        signal = "STRONG_BUY"
    elif score >= 15:
        signal = "BUY"
    elif score >= 5:
        signal = "WATCH"
    elif score >= -15:
        signal = "HOLD"
    elif score >= -30:
        signal = "CAUTION"
    else:
        signal = "AVOID"

    return {
        "signal": signal,
        "confidence": confidence,
        "score": score,
        "signals_breakdown": breakdown,
    }


# ─── Breakout Detection ───────────────────────────────────────────────────────

def detect_breakout(df: pd.DataFrame, indicators: dict) -> dict:
    """Detect if price is breaking out above resistance or breaking down below support."""
    if df.empty or not indicators:
        return {"type": "NONE", "strength": 0, "description": "Insufficient data"}

    close = df["Close"].iloc[-1]
    support = indicators["support"]
    resistance = indicators["resistance"]
    vol_spike = indicators["volume_spike_pct"]

    distance_to_resistance = (resistance - close) / close * 100
    distance_to_support = (close - support) / close * 100

    if distance_to_resistance < 1.5 and vol_spike > 30:
        return {
            "type": "BREAKOUT_IMMINENT",
            "strength": min(95, 70 + vol_spike // 5),
            "description": f"Price within {distance_to_resistance:.1f}% of resistance ₹{resistance:.0f} with high volume",
        }
    elif close > resistance:
        return {
            "type": "BREAKOUT_CONFIRMED",
            "strength": min(95, 80 + vol_spike // 10),
            "description": f"Price broke above resistance ₹{resistance:.0f}",
        }
    elif close < support:
        return {
            "type": "BREAKDOWN",
            "strength": 25,
            "description": f"Price broke below support ₹{support:.0f} — caution advised",
        }
    elif distance_to_support < 2:
        return {
            "type": "AT_SUPPORT",
            "strength": 60,
            "description": f"Price near support ₹{support:.0f} — potential reversal zone",
        }
    else:
        return {
            "type": "CONSOLIDATING",
            "strength": 45,
            "description": f"Trading between support ₹{support:.0f} and resistance ₹{resistance:.0f}",
        }


# ─── Radar Scan (Opportunity Scanner) ────────────────────────────────────────

def radar_scan(stock_data_dict: dict) -> pd.DataFrame:
    """
    Scan multiple stocks and return a ranked signal table.
    Input: {symbol: df}
    Output: DataFrame sorted by confidence
    """
    rows = []
    for symbol, df in stock_data_dict.items():
        try:
            if df.empty or len(df) < 20:
                continue
            inds = compute_all_indicators(df)
            sig = generate_signal(inds)
            brk = detect_breakout(df, inds)

            rows.append({
                "Symbol": symbol.replace(".NS", ""),
                "Price (₹)": inds.get("close", 0),
                "Change %": inds.get("change_pct", 0),
                "Signal": sig["signal"],
                "Confidence": sig["confidence"],
                "RSI": inds.get("rsi", 0),
                "Trend": inds.get("trend", "N/A"),
                "Vol Spike %": inds.get("volume_spike_pct", 0),
                "Pattern": brk["type"],
                "Support ₹": inds.get("support", 0),
                "Resistance ₹": inds.get("resistance", 0),
            })
        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows)
    result = result.sort_values("Confidence", ascending=False).reset_index(drop=True)
    return result


# ─── Signal Color Mapping ────────────────────────────────────────────────────

SIGNAL_COLORS = {
    "STRONG_BUY": "#00ff88",
    "BUY": "#00cc66",
    "WATCH": "#ffcc00",
    "HOLD": "#aaaaaa",
    "CAUTION": "#ff8800",
    "AVOID": "#ff3333",
    "NO_DATA": "#555555",
}

SIGNAL_EMOJI = {
    "STRONG_BUY": "🚀",
    "BUY": "📈",
    "WATCH": "👁️",
    "HOLD": "⏸️",
    "CAUTION": "⚠️",
    "AVOID": "🚨",
    "NO_DATA": "❓",
}


def get_signal_color(signal: str) -> str:
    return SIGNAL_COLORS.get(signal, "#aaaaaa")


def get_signal_emoji(signal: str) -> str:
    return SIGNAL_EMOJI.get(signal, "")
