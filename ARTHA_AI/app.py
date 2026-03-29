"""
ARTHA AI — Intelligent Market Operating System
Production-grade fintech dashboard for Indian Stock Market Intelligence.

Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime

# ─── Page Config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="ARTHA AI — Market OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Module Imports ───────────────────────────────────────────────────────────
from modules.data_fetch import (
    fetch_stock_data, fetch_stock_info, fetch_multiple_stocks,
    normalize_symbol, validate_symbol, RADAR_STOCKS
)
from modules.indicators import compute_all_indicators
from modules.signals import (
    generate_signal, detect_breakout, radar_scan,
    get_signal_color, get_signal_emoji, SIGNAL_COLORS
)
from modules.patterns import (
    build_candlestick_chart, analyze_chart_pattern, detect_patterns_in_df
)
from modules.chat_engine import artha_chat, handle_generic_query
from modules.portfolio import analyze_portfolio
from modules.video_engine import generate_summary_video


# ─── Auto-refresh every 60s ───────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="artha_refresh")
except ImportError:
    pass


# ─── Global CSS — Bloomberg/TradingView Dark Premium UI ──────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0e1117;
    color: #e6edf3;
}
.main { background-color: #0e1117; padding: 0 !important; }
.block-container { padding: 1.5rem 2rem 2rem 2rem !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0d1117 !important;
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .stMarkdown { color: #8b949e; }

/* ── Cards ── */
.artha-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    transition: border-color 0.2s;
}
.artha-card:hover { border-color: #30363d; }

/* ── Metric Cards ── */
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
    min-height: 90px;
}
.metric-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 6px;
    font-family: 'IBM Plex Mono', monospace;
}
.metric-value {
    font-size: 26px;
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1;
}
.metric-sub {
    font-size: 11px;
    color: #8b949e;
    margin-top: 4px;
}

/* ── Signal Badge ── */
.signal-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Section Headers ── */
.section-header {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #8b949e;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Brand Header ── */
.artha-header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border-bottom: 1px solid #21262d;
    padding: 16px 0 14px 0;
    margin-bottom: 24px;
}
.artha-brand {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #e6edf3;
    font-family: 'IBM Plex Mono', monospace;
}
.artha-brand span { color: #00d4ff; }
.artha-tagline {
    font-size: 11px;
    color: #8b949e;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* ── Verdicts ── */
.verdict-buy { background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.3); border-radius: 8px; padding: 16px 20px; }
.verdict-watch { background: rgba(255,204,0,0.08); border: 1px solid rgba(255,204,0,0.3); border-radius: 8px; padding: 16px 20px; }
.verdict-avoid { background: rgba(255,51,51,0.08); border: 1px solid rgba(255,51,51,0.3); border-radius: 8px; padding: 16px 20px; }
.verdict-hold { background: rgba(139,148,158,0.08); border: 1px solid rgba(139,148,158,0.3); border-radius: 8px; padding: 16px 20px; }

/* ── Radar Table ── */
.radar-row { border-bottom: 1px solid #21262d; }

/* ── Input overrides ── */
.stTextInput input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stTextInput input:focus { border-color: #00d4ff !important; box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important; }

/* ── Buttons ── */
.stButton button {
    background: #00d4ff !important;
    color: #0e1117 !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton button:hover { background: #00b8d9 !important; transform: translateY(-1px); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0e1117; }
::-webkit-scrollbar-thumb { background: #21262d; border-radius: 3px; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #21262d; }
[data-testid="stTabs"] [data-baseweb="tab"] { background: transparent; color: #8b949e; font-weight: 500; }
[data-testid="stTabs"] [aria-selected="true"] { color: #00d4ff !important; border-bottom: 2px solid #00d4ff !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #00d4ff !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background: #161b22; border: 1px solid #21262d; border-radius: 8px; }

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def signal_color(sig: str) -> str:
    return SIGNAL_COLORS.get(sig, "#aaaaaa")


def colored_metric(label: str, value: str, sublabel: str = "", color: str = "#e6edf3"):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{value}</div>
        {'<div class="metric-sub">' + sublabel + '</div>' if sublabel else ''}
    </div>
    """


def signal_badge(sig: str) -> str:
    color = signal_color(sig)
    emoji = get_signal_emoji(sig)
    return f'<span class="signal-badge" style="background:rgba(0,0,0,0.4);border:1px solid {color};color:{color}">{emoji} {sig}</span>'


def render_header():
    now = datetime.now().strftime("%H:%M IST · %d %b %Y")
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
         padding:16px 0 20px 0;border-bottom:1px solid #21262d;margin-bottom:24px;">
        <div>
            <div class="artha-brand">⚡ <span>ARTHA</span> AI</div>
            <div class="artha-tagline">INTELLIGENT MARKET OPERATING SYSTEM · NSE INDIA</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:11px;color:#8b949e;font-family:'IBM Plex Mono',monospace;">{now}</div>
            <div style="font-size:10px;color:#3d4450;margin-top:2px;font-family:'IBM Plex Mono',monospace;">
                LIVE · NSE · POWERED BY YFINANCE
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 0 12px 0;">
            <div style="font-size:18px;font-weight:700;color:#e6edf3;font-family:'IBM Plex Mono',monospace;">
                ⚡ ARTHA AI
            </div>
            <div style="font-size:10px;color:#8b949e;letter-spacing:1.5px;margin-top:4px;">
                MARKET OPERATING SYSTEM
            </div>
        </div>
        <div style="height:1px;background:#21262d;margin-bottom:20px;"></div>
        """, unsafe_allow_html=True)

        menu = st.radio(
            "NAVIGATION",
            ["🎯 Opportunity Radar", "🔍 Stock Deep Dive", "💬 Market Chat", "📊 Portfolio Analyzer", "🎬 Video Generator"],
            label_visibility="visible",
        )

        st.markdown("""
        <div style="height:1px;background:#21262d;margin:20px 0;"></div>
        <div style="font-size:10px;color:#3d4450;letter-spacing:1px;font-family:'IBM Plex Mono',monospace;">
            DATA: NSE LIVE VIA YFINANCE<br>
            REFRESH: 60 SEC AUTO<br>
            VERSION: 1.0.0
        </div>
        """, unsafe_allow_html=True)

    return menu


# ─── PAGE 1: Opportunity Radar ────────────────────────────────────────────────

def page_opportunity_radar():
    render_header()
    st.markdown('<div class="section-header">OPPORTUNITY RADAR — TOP NSE SIGNALS</div>', unsafe_allow_html=True)

    with st.spinner("🔍 Scanning NSE universe for opportunities..."):
        stock_data = fetch_multiple_stocks(RADAR_STOCKS, period="3mo")
        radar_df = radar_scan(stock_data)

    if radar_df.empty:
        st.error("⚠️ Unable to fetch market data. Check your internet connection.")
        return

    # Summary metrics
    total = len(radar_df)
    bullish = len(radar_df[radar_df["Signal"].isin(["STRONG_BUY", "BUY"])])
    neutral = len(radar_df[radar_df["Signal"].isin(["WATCH", "HOLD"])])
    bearish = len(radar_df[radar_df["Signal"].isin(["CAUTION", "AVOID"])])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(colored_metric("STOCKS SCANNED", str(total), "NSE Universe", "#e6edf3"), unsafe_allow_html=True)
    with c2:
        st.markdown(colored_metric("BULLISH", str(bullish), "BUY + STRONG BUY", "#00ff88"), unsafe_allow_html=True)
    with c3:
        st.markdown(colored_metric("NEUTRAL", str(neutral), "WATCH + HOLD", "#ffcc00"), unsafe_allow_html=True)
    with c4:
        st.markdown(colored_metric("BEARISH", str(bearish), "CAUTION + AVOID", "#ff4466"), unsafe_allow_html=True)

    st.markdown('<div class="section-header">RANKED SIGNAL TABLE</div>', unsafe_allow_html=True)

    # Build formatted display table
    display_df = radar_df.copy()

    def fmt_signal(sig):
        color = signal_color(sig)
        emoji = get_signal_emoji(sig)
        return f"{emoji} {sig}"

    def fmt_change(val):
        return f"+{val:.2f}%" if val >= 0 else f"{val:.2f}%"

    def fmt_trend(t):
        icons = {"BULLISH": "↑", "BEARISH": "↓", "SIDEWAYS": "→"}
        return f"{icons.get(t, '→')} {t}"

    display_df["Signal"] = display_df["Signal"].apply(fmt_signal)
    display_df["Change %"] = display_df["Change %"].apply(fmt_change)
    display_df["Trend"] = display_df["Trend"].apply(fmt_trend)
    display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x}%")
    display_df["RSI"] = display_df["RSI"].apply(lambda x: f"{x:.1f}")
    display_df["Vol Spike %"] = display_df["Vol Spike %"].apply(lambda x: f"{x:+.1f}%")
    display_df["Price (₹)"] = display_df["Price (₹)"].apply(lambda x: f"₹{x:,.2f}")

    # Columns to show
    show_cols = ["Symbol", "Price (₹)", "Change %", "Signal", "Confidence", "RSI", "Trend", "Vol Spike %", "Pattern"]
    st.dataframe(
        display_df[show_cols],
        use_container_width=True,
        height=480,
        hide_index=True,
    )

    # Top 3 highlight
    st.markdown('<div class="section-header">TOP PICKS — HIGHEST CONFIDENCE</div>', unsafe_allow_html=True)
    top3 = radar_df.head(3)
    cols = st.columns(3)
    for i, (_, row) in enumerate(top3.iterrows()):
        with cols[i]:
            sc = signal_color(row["Signal"])
            chg = row["Change %"]
            chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"
            chg_color = "#00ff88" if chg >= 0 else "#ff4466"
            st.markdown(f"""
            <div class="artha-card" style="border-left:3px solid {sc};">
                <div style="font-size:20px;font-weight:700;color:#e6edf3;font-family:'IBM Plex Mono',monospace;">
                    {row['Symbol']}
                </div>
                <div style="font-size:24px;font-weight:700;color:#e6edf3;margin:8px 0;">
                    ₹{row['Price (₹)']:,.2f}
                    <span style="font-size:14px;color:{chg_color}"> {chg_str}</span>
                </div>
                <div>{signal_badge(row['Signal'])}</div>
                <div style="margin-top:12px;font-size:12px;color:#8b949e;font-family:'IBM Plex Mono',monospace;">
                    RSI: {row['RSI']:.1f} &nbsp;|&nbsp; Conf: {row['Confidence']}% &nbsp;|&nbsp; {row['Trend']}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── PAGE 2: Stock Deep Dive ──────────────────────────────────────────────────

def page_stock_deep_dive():
    render_header()
    st.markdown('<div class="section-header">STOCK DEEP DIVE — TECHNICAL ANALYSIS</div>', unsafe_allow_html=True)

    col_inp, col_period = st.columns([3, 1])
    with col_inp:
        ticker_input = st.text_input(
            "Enter Stock Symbol",
            value="RELIANCE",
            placeholder="e.g. RELIANCE, TCS, INFY, HDFC...",
            help="Enter NSE symbol. Auto-converted to .NS format.",
        )
    with col_period:
        period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)

    symbol = normalize_symbol(ticker_input)

    with st.spinner(f"Fetching live data for {symbol}..."):
        df = fetch_stock_data(symbol, period=period)
        info = fetch_stock_info(symbol)

    if df.empty:
        st.error(f"⚠️ Invalid or unsupported symbol: **{symbol}**. Try RELIANCE, TCS, INFY, HDFCBANK.")
        return

    indicators = compute_all_indicators(df)
    signal_data = generate_signal(indicators)
    breakout_data = detect_breakout(df, indicators)
    chart_pattern = analyze_chart_pattern(df, indicators)
    candle_patterns = detect_patterns_in_df(df)

    # ── Top Info Bar
    chg = indicators.get("change_pct", 0)
    chg_color = "#00ff88" if chg >= 0 else "#ff4466"
    chg_str = f"+{chg:.2f}%" if chg >= 0 else f"{chg:.2f}%"

    st.markdown(f"""
    <div class="artha-card" style="border-left:3px solid {signal_color(signal_data['signal'])};">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
            <div>
                <div style="font-size:13px;color:#8b949e;font-family:'IBM Plex Mono',monospace;letter-spacing:1px;">
                    {info.get('name', symbol)} · {symbol}
                </div>
                <div style="font-size:36px;font-weight:700;font-family:'IBM Plex Mono',monospace;color:#e6edf3;">
                    ₹{indicators['close']:,.2f}
                    <span style="font-size:18px;color:{chg_color};"> {chg_str}</span>
                </div>
                <div style="margin-top:6px;font-size:12px;color:#8b949e;">
                    {info.get('sector','N/A')} · {info.get('industry','N/A')}
                </div>
            </div>
            <div style="text-align:right;">
                <div>{signal_badge(signal_data['signal'])}</div>
                <div style="margin-top:8px;font-size:22px;font-weight:700;font-family:'IBM Plex Mono',monospace;
                     color:{signal_color(signal_data['signal'])};">
                    {signal_data['confidence']}% Confidence
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metrics Row
    m_cols = st.columns(6)
    metrics_data = [
        ("RSI", f"{indicators['rsi']:.1f}",
         "Oversold" if indicators['rsi'] < 30 else "Overbought" if indicators['rsi'] > 70 else "Neutral",
         "#00ff88" if indicators['rsi'] < 40 else "#ff4466" if indicators['rsi'] > 70 else "#e6edf3"),
        ("MA 20", f"₹{indicators['ma20']:,.0f}" if indicators['ma20'] else "N/A", "20-day MA", "#f7c948"),
        ("MA 50", f"₹{indicators['ma50']:,.0f}" if indicators['ma50'] else "N/A", "50-day MA", "#8b5cf6"),
        ("Vol Spike", f"{indicators['volume_spike_pct']:+.1f}%", "vs 20d avg",
         "#00d4ff" if indicators['volume_spike_pct'] > 20 else "#8b949e"),
        ("Support", f"₹{indicators['support']:,.0f}", "Key level", "#00ff88"),
        ("Resistance", f"₹{indicators['resistance']:,.0f}", "Key level", "#ff4466"),
    ]
    for col, (label, val, sub, color) in zip(m_cols, metrics_data):
        with col:
            st.markdown(colored_metric(label, val, sub, color), unsafe_allow_html=True)

    # ── Chart
    st.markdown('<div class="section-header">PRICE CHART + INDICATORS</div>', unsafe_allow_html=True)
    fig = build_candlestick_chart(df, symbol.replace(".NS", ""), indicators)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

    # ── Pattern + Signals Analysis
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<div class="section-header">CHART PATTERN</div>', unsafe_allow_html=True)
        prob_color = "#00ff88" if chart_pattern["probability"] > 65 else "#ffcc00" if chart_pattern["probability"] > 45 else "#ff4466"
        st.markdown(f"""
        <div class="artha-card">
            <div style="font-size:16px;font-weight:700;color:#e6edf3;margin-bottom:8px;">
                {chart_pattern['pattern'].replace('_',' ')}
            </div>
            <div style="font-size:13px;color:#8b949e;line-height:1.6;margin-bottom:12px;">
                {chart_pattern['description']}
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <div>
                    <div style="font-size:10px;color:#8b949e;letter-spacing:1px;">PROBABILITY</div>
                    <div style="font-size:24px;font-weight:700;color:{prob_color};font-family:'IBM Plex Mono',monospace;">
                        {chart_pattern['probability']}%
                    </div>
                </div>
                <div>
                    <div style="font-size:10px;color:#8b949e;letter-spacing:1px;">ACTION</div>
                    <div style="font-size:14px;font-weight:600;color:#e6edf3;">{chart_pattern['action']}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if candle_patterns:
            st.markdown('<div class="section-header">CANDLESTICK PATTERNS DETECTED</div>', unsafe_allow_html=True)
            for p in candle_patterns[-4:]:
                ptype_color = "#00ff88" if p["type"] == "BULLISH" else "#ff4466" if p["type"] == "BEARISH" else "#ffcc00"
                st.markdown(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;
                     padding:8px 12px;border-radius:6px;background:#161b22;margin-bottom:6px;
                     border-left:2px solid {ptype_color};">
                    <span style="font-size:12px;color:#e6edf3;font-weight:600;">{p['pattern']}</span>
                    <span style="font-size:10px;color:{ptype_color};font-family:'IBM Plex Mono',monospace;">{p['type']}</span>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-header">SIGNAL BREAKDOWN</div>', unsafe_allow_html=True)
        breakdown = signal_data.get("signals_breakdown", [])
        for item in breakdown:
            score = item["weight"]
            bar_color = "#00ff88" if score > 0 else "#ff4466" if score < 0 else "#8b949e"
            bar_width = min(100, abs(score) * 4)
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                    <span style="font-size:11px;color:#8b949e;font-family:'IBM Plex Mono',monospace;">
                        {item['indicator']}
                    </span>
                    <span style="font-size:11px;color:{bar_color};font-weight:600;">
                        {item['signal']}
                    </span>
                </div>
                <div style="background:#21262d;border-radius:4px;height:6px;overflow:hidden;">
                    <div style="width:{bar_width}%;height:100%;background:{bar_color};
                         margin-left:{'0' if score >= 0 else f'calc(50% - {bar_width/2}%)'};">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">52-WEEK RANGE</div>', unsafe_allow_html=True)
        high52 = info.get("52w_high")
        low52 = info.get("52w_low")
        if high52 and low52:
            pos = (indicators["close"] - low52) / (high52 - low52) * 100
            st.markdown(f"""
            <div class="artha-card">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                    <span style="font-size:11px;color:#8b949e;">52W Low: ₹{low52:,.0f}</span>
                    <span style="font-size:11px;color:#8b949e;">52W High: ₹{high52:,.0f}</span>
                </div>
                <div style="background:#21262d;border-radius:6px;height:10px;position:relative;">
                    <div style="width:{pos:.0f}%;height:100%;background:linear-gradient(90deg,#00ff88,#00d4ff);border-radius:6px;"></div>
                    <div style="position:absolute;left:{pos:.0f}%;top:-4px;transform:translateX(-50%);
                         width:18px;height:18px;background:#00d4ff;border-radius:50%;border:2px solid #0e1117;">
                    </div>
                </div>
                <div style="text-align:center;margin-top:12px;font-size:12px;color:#8b949e;">
                    Current price at <strong style="color:#00d4ff;">{pos:.0f}%</strong> of 52-week range
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─── PAGE 3: Market Chat ──────────────────────────────────────────────────────

def page_market_chat():
    render_header()
    st.markdown('<div class="section-header">MARKET CHAT — AI-POWERED ANALYSIS ENGINE</div>', unsafe_allow_html=True)

    col_sym, _ = st.columns([2, 3])
    with col_sym:
        ticker_input = st.text_input("Stock Symbol", value="TCS", placeholder="e.g. RELIANCE, INFY, HDFC...")

    symbol = normalize_symbol(ticker_input)

    with st.spinner(f"Loading context for {symbol}..."):
        df = fetch_stock_data(symbol, period="3mo")
        info = fetch_stock_info(symbol)

    if df.empty:
        st.error(f"⚠️ Could not load data for {symbol}")
        return

    indicators = compute_all_indicators(df)
    signal_data = generate_signal(indicators)
    breakout_data = detect_breakout(df, indicators)

    # Query examples
    st.markdown("""
    <div style="margin-bottom:16px;">
        <span style="font-size:11px;color:#8b949e;">SUGGESTED QUERIES: </span>
        <span style="font-size:11px;color:#3d4450;">
            "Should I buy now?" · "What's the risk?" · "Explain the trend" · "Is this oversold?" · "Give me a full analysis"
        </span>
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input(
        "Your Question",
        placeholder=f"Ask anything about {symbol}...",
        key="chat_query",
    )

    if st.button("🔍 ANALYZE", key="analyze_btn"):
        if not query.strip():
            query = f"Give me a full analysis of {symbol}"

        with st.spinner("Running analysis..."):
            response = artha_chat(
                query=query,
                symbol=symbol,
                indicators=indicators,
                signal_data=signal_data,
                breakout_data=breakout_data,
                stock_info=info,
            )

        # Render response
        st.markdown(f"""
        <div style="margin-bottom:12px;">
            <span style="font-size:11px;color:#8b949e;font-family:'IBM Plex Mono',monospace;">
                ARTHA ANALYSIS · {response['timestamp']}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 1. Analysis
        st.markdown('<div class="section-header">1 · ANALYSIS</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="artha-card">{response["analysis"]}</div>', unsafe_allow_html=True)

        # 2. Key Signals
        st.markdown('<div class="section-header">2 · KEY SIGNALS</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for i, signal_text in enumerate(response["key_signals"]):
            with cols[i % 2]:
                st.markdown(f'<div class="artha-card" style="font-size:13px;line-height:1.6;">{signal_text}</div>', unsafe_allow_html=True)

        # 3. Risk Factors
        st.markdown('<div class="section-header">3 · RISK FACTORS</div>', unsafe_allow_html=True)
        for risk in response["risk_factors"]:
            st.markdown(f'<div style="padding:8px 14px;background:#161b22;border-radius:6px;margin-bottom:6px;font-size:13px;">{risk}</div>', unsafe_allow_html=True)

        # 4. Verdict
        vtype = response["verdict_type"]
        vclass_map = {"BUY": "verdict-buy", "WATCH": "verdict-watch", "AVOID": "verdict-avoid", "HOLD": "verdict-hold", "CAUTION": "verdict-avoid"}
        vclass = vclass_map.get(vtype, "verdict-hold")
        st.markdown('<div class="section-header">4 · VERDICT</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="{vclass}">{response["verdict"]}</div>', unsafe_allow_html=True)

        # 5. Why
        st.markdown('<div class="section-header">5 · WHY</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="artha-card" style="font-size:13px;">{response["why"]}</div>', unsafe_allow_html=True)

        st.markdown('<div style="font-size:10px;color:#3d4450;margin-top:16px;">⚠️ ARTHA AI is for educational purposes only. Not SEBI-registered investment advice.</div>', unsafe_allow_html=True)


# ─── PAGE 4: Portfolio Analyzer ──────────────────────────────────────────────

def page_portfolio_analyzer():
    render_header()
    st.markdown('<div class="section-header">PORTFOLIO ANALYZER — RISK & DIVERSIFICATION</div>', unsafe_allow_html=True)

    default_portfolio = "RELIANCE, TCS, HDFCBANK, INFY, SUNPHARMA"
    portfolio_input = st.text_area(
        "Enter Portfolio Stocks (comma-separated)",
        value=default_portfolio,
        height=80,
        help="e.g. RELIANCE, TCS, INFY, HDFCBANK, WIPRO",
    )

    if st.button("📊 ANALYZE PORTFOLIO"):
        raw_symbols = [s.strip() for s in portfolio_input.split(",") if s.strip()]
        symbols = [normalize_symbol(s) for s in raw_symbols]

        with st.spinner("Analyzing portfolio..."):
            stock_data = fetch_multiple_stocks(symbols, period="3mo")
            result = analyze_portfolio(stock_data)

        if "error" in result:
            st.error(result["error"])
            return

        risk = result["risk"]
        diversification = result["diversification"]
        suggestions = result["suggestions"]
        stock_metrics = result["stock_metrics"]

        # ── Summary Metrics
        r_color = "#00ff88" if risk["score"] < 30 else "#ffcc00" if risk["score"] < 55 else "#ff4466"
        d_color = "#00ff88" if diversification["score"] > 65 else "#ffcc00" if diversification["score"] > 40 else "#ff4466"

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(colored_metric("STOCKS", str(result["stock_count"]), "in portfolio", "#e6edf3"), unsafe_allow_html=True)
        with c2:
            st.markdown(colored_metric("RISK SCORE", f"{risk['score']:.0f}/100", risk["label"], r_color), unsafe_allow_html=True)
        with c3:
            st.markdown(colored_metric("DIVERSIFICATION", f"{diversification['score']:.0f}/100", diversification["label"], d_color), unsafe_allow_html=True)
        with c4:
            st.markdown(colored_metric("SECTORS", str(diversification["n_sectors"]), "unique sectors", "#8b5cf6"), unsafe_allow_html=True)

        col_left, col_right = st.columns([1, 1])

        with col_left:
            # Risk Breakdown
            st.markdown('<div class="section-header">RISK BREAKDOWN</div>', unsafe_allow_html=True)
            for label, val in risk.get("breakdown", {}).items():
                bar_w = min(100, val * 4)
                bar_color = "#ff4466" if val > 15 else "#ffcc00" if val > 8 else "#00ff88"
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:11px;color:#8b949e;">{label}</span>
                        <span style="font-size:11px;color:{bar_color};font-weight:600;">{val}</span>
                    </div>
                    <div style="background:#21262d;border-radius:4px;height:6px;">
                        <div style="width:{bar_w}%;height:100%;background:{bar_color};border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">PORTFOLIO STATS</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="artha-card">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                    <div>
                        <div class="metric-label">Avg Beta</div>
                        <div class="metric-value" style="font-size:20px;color:#e6edf3;">{risk.get('avg_beta','N/A')}</div>
                    </div>
                    <div>
                        <div class="metric-label">Avg Volatility</div>
                        <div class="metric-value" style="font-size:20px;color:#e6edf3;">{risk.get('avg_volatility','N/A')}%</div>
                    </div>
                    <div>
                        <div class="metric-label">Max Drawdown</div>
                        <div class="metric-value" style="font-size:20px;color:#ff4466;">-{risk.get('avg_drawdown','N/A')}%</div>
                    </div>
                    <div>
                        <div class="metric-label">Dominant Sector</div>
                        <div class="metric-value" style="font-size:16px;color:#e6edf3;">{diversification.get('dominant_sector','N/A')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_right:
            # Sector pie
            st.markdown('<div class="section-header">SECTOR ALLOCATION</div>', unsafe_allow_html=True)
            sectors = diversification.get("sectors", {})
            if sectors:
                fig_pie = go.Figure(go.Pie(
                    labels=list(sectors.keys()),
                    values=list(sectors.values()),
                    hole=0.55,
                    marker=dict(
                        colors=["#00d4ff","#00ff88","#ff4466","#f7c948","#8b5cf6","#ff6b35","#00b8d9","#e040fb"],
                        line=dict(color="#0e1117", width=2),
                    ),
                    textfont=dict(color="#e6edf3", size=11),
                ))
                fig_pie.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#161b22",
                    plot_bgcolor="#161b22",
                    font=dict(color="#e6edf3"),
                    legend=dict(font=dict(size=11)),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280,
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        # Individual stock table
        st.markdown('<div class="section-header">INDIVIDUAL STOCK METRICS</div>', unsafe_allow_html=True)
        sm_df = pd.DataFrame(stock_metrics)
        if not sm_df.empty:
            sm_display = sm_df[["symbol", "sector", "beta", "volatility", "max_drawdown", "rsi", "trend", "signal", "confidence"]].copy()
            sm_display.columns = ["Symbol", "Sector", "Beta", "Volatility %", "Max Drawdown %", "RSI", "Trend", "Signal", "Confidence %"]
            st.dataframe(sm_display, use_container_width=True, hide_index=True)

        # Suggestions
        st.markdown('<div class="section-header">ARTHA RECOMMENDATIONS</div>', unsafe_allow_html=True)
        for s in suggestions:
            priority_colors = {"HIGH": "#ff4466", "MEDIUM": "#ffcc00", "LOW": "#00ff88", "INFO": "#8b949e"}
            pc = priority_colors.get(s.get("priority", "INFO"), "#8b949e")
            st.markdown(f"""
            <div class="artha-card" style="border-left:3px solid {pc};">
                <div style="font-size:10px;color:{pc};font-weight:700;letter-spacing:1px;margin-bottom:4px;">
                    {s.get('priority','INFO')} PRIORITY · {s.get('type','').replace('_',' ')}
                </div>
                <div style="font-size:13px;color:#e6edf3;">{s['text']}</div>
            </div>
            """, unsafe_allow_html=True)


# ─── PAGE 5: Video Generator ──────────────────────────────────────────────────

def page_video_generator():
    render_header()
    st.markdown('<div class="section-header">VIDEO GENERATOR — MARKET SUMMARY MP4</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="artha-card">
        <div style="font-size:14px;color:#8b949e;line-height:1.7;">
            Generate a <strong style="color:#e6edf3;">short market summary video</strong> for any NSE stock.
            The video renders signal, RSI, trend, and price data into a shareable 8-second MP4.
            <br><br>
            <strong style="color:#ffcc00;">⚠️ Note:</strong> Requires MoviePy + FFmpeg installed. Falls back to text summary if unavailable.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_sym, col_dur = st.columns([3, 1])
    with col_sym:
        ticker_input = st.text_input("Stock Symbol", value="RELIANCE", key="video_ticker")
    with col_dur:
        duration = st.selectbox("Duration (sec)", [5, 8, 10], index=1)

    symbol = normalize_symbol(ticker_input)

    if st.button("🎬 GENERATE VIDEO"):
        with st.spinner(f"Loading {symbol} data..."):
            df = fetch_stock_data(symbol, period="3mo")

        if df.empty:
            st.error(f"⚠️ No data for {symbol}")
            return

        indicators = compute_all_indicators(df)
        signal_data = generate_signal(indicators)

        with st.spinner("Generating video... This may take 15-30 seconds."):
            result = generate_summary_video(
                symbol=symbol,
                signal=signal_data.get("signal", "HOLD"),
                confidence=signal_data.get("confidence", 50),
                rsi=indicators.get("rsi", 50),
                trend=indicators.get("trend", "SIDEWAYS"),
                close=indicators.get("close", 0),
                close_series=df["Close"],
                duration=duration,
            )

        if result["success"]:
            st.success(f"✅ {result['message']}")
            video_path = result["filepath"]
            if video_path.endswith(".mp4"):
                try:
                    with open(video_path, "rb") as f:
                        st.video(f.read())
                except Exception:
                    st.info(f"Video saved to: `{video_path}`")
            st.code(f"Saved: {video_path}", language="bash")
        else:
            st.warning(result["message"])
            if "fallback_text" in result:
                st.markdown(f'<div class="artha-card"><pre style="color:#8b949e;font-size:12px;">{result["fallback_text"]}</pre></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">HOW IT WORKS</div>', unsafe_allow_html=True)
    steps = [
        ("01", "Live Data", f"Fetch OHLCV data for {normalize_symbol(ticker_input)} from NSE via yfinance"),
        ("02", "Compute", "Run technical analysis — RSI, MA, MACD, Volume, Trend"),
        ("03", "Signal", "Generate ARTHA AI signal with confidence score"),
        ("04", "Render", "MoviePy renders frames with animated price chart overlay"),
        ("05", "Export", "MP4 saved to assets/generated_videos/"),
    ]
    cols = st.columns(5)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"""
            <div class="artha-card" style="text-align:center;">
                <div style="font-size:22px;font-weight:700;color:#00d4ff;font-family:'IBM Plex Mono',monospace;">{num}</div>
                <div style="font-size:12px;font-weight:700;color:#e6edf3;margin:6px 0;">{title}</div>
                <div style="font-size:11px;color:#8b949e;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ─── Main Router ──────────────────────────────────────────────────────────────

def main():
    page = render_sidebar()

    if page == "🎯 Opportunity Radar":
        page_opportunity_radar()
    elif page == "🔍 Stock Deep Dive":
        page_stock_deep_dive()
    elif page == "💬 Market Chat":
        page_market_chat()
    elif page == "📊 Portfolio Analyzer":
        page_portfolio_analyzer()
    elif page == "🎬 Video Generator":
        page_video_generator()


if __name__ == "__main__":
    main()
