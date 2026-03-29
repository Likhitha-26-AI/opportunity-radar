"""
ARTHA AI — Technical Indicators Engine
Computes RSI, Moving Averages, Volume Spike, Support/Resistance, Trend.
"""

import pandas as pd
import numpy as np


# ─── RSI ─────────────────────────────────────────────────────────────────────

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


# ─── Moving Averages ─────────────────────────────────────────────────────────

def compute_ma(series: pd.Series, window: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=window).mean()


def compute_ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=span, adjust=False).mean()


# ─── MACD ────────────────────────────────────────────────────────────────────

def compute_macd(series: pd.Series) -> tuple:
    """Returns (macd_line, signal_line, histogram)."""
    ema12 = compute_ema(series, 12)
    ema26 = compute_ema(series, 26)
    macd = ema12 - ema26
    signal = compute_ema(macd, 9)
    hist = macd - signal
    return macd, signal, hist


# ─── Bollinger Bands ─────────────────────────────────────────────────────────

def compute_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0) -> tuple:
    """Returns (upper, middle, lower) bands."""
    middle = compute_ma(series, window)
    std = series.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


# ─── Volume Spike ────────────────────────────────────────────────────────────

def compute_volume_spike(volume: pd.Series, window: int = 20) -> pd.Series:
    """Volume as % above/below rolling average."""
    avg = volume.rolling(window=window).mean()
    spike_pct = ((volume - avg) / avg * 100).fillna(0)
    return spike_pct


# ─── Support & Resistance ────────────────────────────────────────────────────

def compute_support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple:
    """Simple pivot-based support and resistance."""
    recent = df.tail(lookback)
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())
    return support, resistance


# ─── Trend Detection ─────────────────────────────────────────────────────────

def detect_trend(df: pd.DataFrame) -> str:
    """
    Classify price trend as BULLISH / BEARISH / SIDEWAYS
    using MA20 vs MA50 slope and price position.
    """
    if len(df) < 50:
        return "SIDEWAYS"

    close = df["Close"]
    ma20 = compute_ma(close, 20)
    ma50 = compute_ma(close, 50)

    last_ma20 = ma20.iloc[-1]
    last_ma50 = ma50.iloc[-1]
    prev_ma20 = ma20.iloc[-5]
    prev_ma50 = ma50.iloc[-5]
    last_close = close.iloc[-1]

    ma20_slope = (last_ma20 - prev_ma20) / prev_ma20 * 100
    ma50_slope = (last_ma50 - prev_ma50) / prev_ma50 * 100

    if last_ma20 > last_ma50 and ma20_slope > 0.1 and last_close > last_ma20:
        return "BULLISH"
    elif last_ma20 < last_ma50 and ma20_slope < -0.1 and last_close < last_ma20:
        return "BEARISH"
    else:
        return "SIDEWAYS"


# ─── Master Indicator Bundle ─────────────────────────────────────────────────

def compute_all_indicators(df: pd.DataFrame) -> dict:
    """
    Compute all indicators for a stock DataFrame.
    Returns a dictionary with latest values + full series.
    """
    if df.empty or len(df) < 20:
        return {}

    close = df["Close"]
    volume = df["Volume"]

    rsi_series = compute_rsi(close)
    ma20_series = compute_ma(close, 20)
    ma50_series = compute_ma(close, 50)
    ema9_series = compute_ema(close, 9)
    macd_line, macd_signal, macd_hist = compute_macd(close)
    bb_upper, bb_mid, bb_lower = compute_bollinger(close)
    vol_spike = compute_volume_spike(volume)
    support, resistance = compute_support_resistance(df)
    trend = detect_trend(df)

    latest_rsi = float(rsi_series.iloc[-1])
    latest_ma20 = float(ma20_series.iloc[-1]) if not pd.isna(ma20_series.iloc[-1]) else None
    latest_ma50 = float(ma50_series.iloc[-1]) if not pd.isna(ma50_series.iloc[-1]) else None
    latest_close = float(close.iloc[-1])
    latest_vol_spike = float(vol_spike.iloc[-1])
    latest_macd = float(macd_line.iloc[-1])
    latest_macd_signal = float(macd_signal.iloc[-1])
    latest_bb_upper = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
    latest_bb_lower = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None

    # Price change %
    prev_close = float(close.iloc[-2]) if len(close) > 1 else latest_close
    change_pct = (latest_close - prev_close) / prev_close * 100

    return {
        # Latest scalar values
        "rsi": round(latest_rsi, 2),
        "ma20": round(latest_ma20, 2) if latest_ma20 else None,
        "ma50": round(latest_ma50, 2) if latest_ma50 else None,
        "close": round(latest_close, 2),
        "change_pct": round(change_pct, 2),
        "volume_spike_pct": round(latest_vol_spike, 2),
        "macd": round(latest_macd, 4),
        "macd_signal": round(latest_macd_signal, 4),
        "bb_upper": round(latest_bb_upper, 2) if latest_bb_upper else None,
        "bb_lower": round(latest_bb_lower, 2) if latest_bb_lower else None,
        "support": round(support, 2),
        "resistance": round(resistance, 2),
        "trend": trend,
        # Full series for charting
        "series": {
            "rsi": rsi_series,
            "ma20": ma20_series,
            "ma50": ma50_series,
            "ema9": ema9_series,
            "macd": macd_line,
            "macd_signal": macd_signal,
            "macd_hist": macd_hist,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
            "vol_spike": vol_spike,
        }
    }
