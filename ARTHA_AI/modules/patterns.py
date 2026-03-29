"""
ARTHA AI — Chart Pattern Intelligence
Detects candlestick patterns and generates Plotly premium charts.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ─── Color Palette ────────────────────────────────────────────────────────────

COLORS = {
    "bg": "#0e1117",
    "bg_card": "#161b22",
    "grid": "#21262d",
    "text": "#e6edf3",
    "accent": "#00d4ff",
    "bullish": "#00ff88",
    "bearish": "#ff4466",
    "ma20": "#f7c948",
    "ma50": "#8b5cf6",
    "volume": "#334155",
    "volume_spike": "#00d4ff",
}


# ─── Candlestick Pattern Detection ───────────────────────────────────────────

def detect_doji(df: pd.DataFrame, idx: int, threshold: float = 0.05) -> bool:
    row = df.iloc[idx]
    body = abs(row["Close"] - row["Open"])
    wick = row["High"] - row["Low"]
    return wick > 0 and (body / wick) < threshold


def detect_hammer(df: pd.DataFrame, idx: int) -> bool:
    row = df.iloc[idx]
    body = abs(row["Close"] - row["Open"])
    lower_wick = min(row["Open"], row["Close"]) - row["Low"]
    upper_wick = row["High"] - max(row["Open"], row["Close"])
    return (lower_wick >= 2 * body) and (upper_wick <= body * 0.3) and (body > 0)


def detect_shooting_star(df: pd.DataFrame, idx: int) -> bool:
    row = df.iloc[idx]
    body = abs(row["Close"] - row["Open"])
    upper_wick = row["High"] - max(row["Open"], row["Close"])
    lower_wick = min(row["Open"], row["Close"]) - row["Low"]
    return (upper_wick >= 2 * body) and (lower_wick <= body * 0.3) and (body > 0)


def detect_engulfing(df: pd.DataFrame, idx: int) -> str:
    if idx < 1:
        return "NONE"
    curr = df.iloc[idx]
    prev = df.iloc[idx - 1]
    curr_body = curr["Close"] - curr["Open"]
    prev_body = prev["Close"] - prev["Open"]
    if (curr_body > 0 and prev_body < 0 and
            curr["Open"] < prev["Close"] and curr["Close"] > prev["Open"]):
        return "BULLISH_ENGULFING"
    if (curr_body < 0 and prev_body > 0 and
            curr["Open"] > prev["Close"] and curr["Close"] < prev["Open"]):
        return "BEARISH_ENGULFING"
    return "NONE"


def detect_patterns_in_df(df: pd.DataFrame) -> list:
    """Scan last 10 candles for patterns."""
    patterns = []
    scan_range = min(10, len(df))
    for i in range(len(df) - scan_range, len(df)):
        date = df.index[i]
        if detect_doji(df, i):
            patterns.append({"date": date, "pattern": "Doji", "type": "NEUTRAL", "candle_idx": i})
        if detect_hammer(df, i):
            patterns.append({"date": date, "pattern": "Hammer", "type": "BULLISH", "candle_idx": i})
        if detect_shooting_star(df, i):
            patterns.append({"date": date, "pattern": "Shooting Star", "type": "BEARISH", "candle_idx": i})
        eng = detect_engulfing(df, i)
        if eng != "NONE":
            patterns.append({"date": date, "pattern": eng.replace("_", " ").title(), "type": eng.split("_")[0], "candle_idx": i})
    return patterns


def analyze_chart_pattern(df: pd.DataFrame, indicators: dict) -> dict:
    """High-level chart pattern: Breakout, Breakdown, or Sideways."""
    if df.empty or not indicators:
        return {
            "pattern": "UNKNOWN",
            "description": "Insufficient data.",
            "probability": 0,
            "action": "WAIT",
        }

    close = df["Close"]
    recent_high = close.tail(20).max()
    recent_low = close.tail(20).min()
    current = close.iloc[-1]
    resistance = indicators.get("resistance", recent_high)
    support = indicators.get("support", recent_low)
    rsi = indicators.get("rsi", 50)
    vol_spike = indicators.get("volume_spike_pct", 0)
    trend = indicators.get("trend", "SIDEWAYS")

    range_pct = (resistance - support) / support * 100
    pos_in_range = (current - support) / (resistance - support) * 100 if (resistance != support) else 50

    if trend == "BULLISH" and pos_in_range > 75 and vol_spike > 30:
        return {
            "pattern": "BREAKOUT",
            "description": f"Strong breakout pattern. Price at {pos_in_range:.0f}% of trading range with elevated volume ({vol_spike:+.0f}%). Bullish momentum confirmed by MA alignment.",
            "probability": min(88, 65 + int(vol_spike / 5)),
            "action": "BUY / WATCH CLOSELY",
        }
    elif trend == "BEARISH" and pos_in_range < 25 and vol_spike > 20:
        return {
            "pattern": "BREAKDOWN",
            "description": f"Breakdown detected. Price at {pos_in_range:.0f}% of trading range with selling pressure (Vol spike: {vol_spike:+.0f}%). Bearish momentum dominant.",
            "probability": min(85, 60 + int(abs(vol_spike) / 5)),
            "action": "AVOID / EXIT",
        }
    elif range_pct < 5:
        return {
            "pattern": "TIGHT_CONSOLIDATION",
            "description": f"Price coiling in a tight range ({range_pct:.1f}%). Often precedes a significant move. Monitor for volume expansion.",
            "probability": 55,
            "action": "WATCH — BREAKOUT LIKELY SOON",
        }
    elif pos_in_range > 40 and pos_in_range < 60:
        return {
            "pattern": "SIDEWAYS",
            "description": f"Stock consolidating between ₹{support:.0f} (support) and ₹{resistance:.0f} (resistance). No clear directional bias currently.",
            "probability": 48,
            "action": "HOLD / WAIT FOR DIRECTION",
        }
    elif trend == "BULLISH" and rsi < 50:
        return {
            "pattern": "PULLBACK_IN_UPTREND",
            "description": f"Healthy pullback in an uptrend. RSI at {rsi:.0f} — potential accumulation opportunity near support ₹{support:.0f}.",
            "probability": 68,
            "action": "ACCUMULATE AT SUPPORT",
        }
    else:
        return {
            "pattern": "INDECISIVE",
            "description": f"Mixed signals. Trend: {trend}, RSI: {rsi:.0f}. Wait for clearer setup.",
            "probability": 40,
            "action": "WAIT",
        }


# ─── Premium Candlestick Chart ────────────────────────────────────────────────

def build_candlestick_chart(df: pd.DataFrame, symbol: str, indicators: dict) -> go.Figure:
    """Generate a premium Plotly candlestick chart with MA overlays and volume."""
    series = indicators.get("series", {})
    ma20 = series.get("ma20")
    ma50 = series.get("ma50")
    bb_upper = series.get("bb_upper")
    bb_lower = series.get("bb_lower")
    vol_spike = series.get("vol_spike")

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("", "", ""),
    )

    # ── Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price",
        increasing_line_color=COLORS["bullish"],
        decreasing_line_color=COLORS["bearish"],
        increasing_fillcolor=COLORS["bullish"],
        decreasing_fillcolor=COLORS["bearish"],
        line_width=1,
    ), row=1, col=1)

    # ── Bollinger Bands
    if bb_upper is not None and bb_lower is not None:
        fig.add_trace(go.Scatter(
            x=df.index, y=bb_upper,
            name="BB Upper", line=dict(color="rgba(0,212,255,0.3)", width=1, dash="dot"),
            showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=bb_lower,
            name="BB Lower", line=dict(color="rgba(0,212,255,0.3)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(0,212,255,0.04)",
            showlegend=True,
        ), row=1, col=1)

    # ── MA Lines
    if ma20 is not None:
        fig.add_trace(go.Scatter(
            x=df.index, y=ma20,
            name="MA 20", line=dict(color=COLORS["ma20"], width=1.5),
        ), row=1, col=1)
    if ma50 is not None:
        fig.add_trace(go.Scatter(
            x=df.index, y=ma50,
            name="MA 50", line=dict(color=COLORS["ma50"], width=1.5),
        ), row=1, col=1)

    # ── Support / Resistance lines
    supp = indicators.get("support")
    resi = indicators.get("resistance")
    if supp:
        fig.add_hline(y=supp, line_dash="dash", line_color="rgba(0,255,136,0.4)",
                      annotation_text=f"S: ₹{supp:.0f}", annotation_position="left",
                      annotation_font_color="rgba(0,255,136,0.8)", row=1, col=1)
    if resi:
        fig.add_hline(y=resi, line_dash="dash", line_color="rgba(255,68,102,0.4)",
                      annotation_text=f"R: ₹{resi:.0f}", annotation_position="left",
                      annotation_font_color="rgba(255,68,102,0.8)", row=1, col=1)

    # ── RSI subplot
    rsi_series = series.get("rsi")
    if rsi_series is not None:
        fig.add_trace(go.Scatter(
            x=df.index, y=rsi_series,
            name="RSI", line=dict(color=COLORS["accent"], width=1.5),
        ), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="rgba(255,68,102,0.5)", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="rgba(0,255,136,0.5)", row=2, col=1)

    # ── Volume subplot
    volume_colors = [
        COLORS["bullish"] if df["Close"].iloc[i] >= df["Open"].iloc[i] else COLORS["bearish"]
        for i in range(len(df))
    ]
    fig.add_trace(go.Bar(
        x=df.index,
        y=df["Volume"],
        name="Volume",
        marker_color=volume_colors,
        marker_line_width=0,
        opacity=0.7,
    ), row=3, col=1)

    # ── Layout
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(family="'IBM Plex Mono', monospace", color=COLORS["text"], size=11),
        title=dict(
            text=f"<b>{symbol}</b>  |  NSE",
            font=dict(size=18, color=COLORS["accent"]),
            x=0.02,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="left", x=0,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        height=720,
        margin=dict(l=10, r=10, t=60, b=10),
    )

    for i in [1, 2, 3]:
        fig.update_xaxes(
            row=i, col=1,
            gridcolor=COLORS["grid"],
            showgrid=True,
            zeroline=False,
            showspikes=True,
            spikethickness=1,
            spikecolor=COLORS["accent"],
        )
        fig.update_yaxes(
            row=i, col=1,
            gridcolor=COLORS["grid"],
            showgrid=True,
            zeroline=False,
        )

    fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
    fig.update_yaxes(title_text="Volume", row=3, col=1)

    return fig


def build_mini_sparkline(df: pd.DataFrame, color: str = "#00ff88") -> go.Figure:
    """Tiny sparkline chart for radar table."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=f"rgba(0,255,136,0.05)",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=60,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
