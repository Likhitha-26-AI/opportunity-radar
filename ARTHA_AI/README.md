# ⚡ ARTHA AI — Intelligent Market Operating System

> **Transform Indian stock market data into actionable, explainable, real-time investment intelligence.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![NSE](https://img.shields.io/badge/Market-NSE%20India-orange?style=flat-square)](https://nseindia.com)

---

## 🎯 Problem Statement

Indian retail investors lack access to institutional-grade market intelligence. Bloomberg terminals cost $24,000/year. TradingView's advanced features require paid subscriptions. Meanwhile, 14 crore+ Demat account holders make decisions based on noise, tips, and guesswork — not data.

**ARTHA AI** democratizes sophisticated market analysis. Every feature that hedge funds use — RSI, MACD, Bollinger Bands, Volume analysis, Pattern detection — now accessible to any Indian investor, for free.

---

## 💡 Solution

ARTHA AI is a full-stack fintech intelligence platform built on Python + Streamlit that delivers:

- **Real-time NSE data** via yfinance (.NS symbol resolution)
- **Institutional-grade technical analysis** across 5 core modules
- **Explainable AI verdicts** — not just signals, but *why* the signal exists
- **Portfolio risk intelligence** with diversification scoring
- **Video report generation** — shareable market summaries in MP4 format
- **Conversational market chat** — ask any question, get structured analysis

---

## 🚀 Features

### 1. 🎯 Opportunity Radar
Scans 20+ NSE blue-chip stocks simultaneously. Detects RSI extremes, volume spikes, breakout setups, and trend alignments. Ranks top opportunities by composite confidence score.

### 2. 🔍 Stock Deep Dive
Full technical breakdown for any NSE stock:
- Premium Plotly candlestick chart with MA20, MA50, Bollinger Bands
- RSI, MACD, Volume subplots
- Support & Resistance overlays
- Candlestick pattern detection (Hammer, Doji, Engulfing, Shooting Star)
- 52-week range position tracker

### 3. 💬 Market Chat Engine
Rule-based analytical engine. Ask any question about a stock and receive:
1. **ANALYSIS** — Company context + current chart pattern
2. **KEY SIGNALS** — RSI, Trend, Volume, S&R, MACD interpreted in plain English
3. **RISK FACTORS** — Explicit downside scenarios
4. **VERDICT** — BUY / HOLD / WATCH / AVOID with confidence %
5. **WHY** — Score-based reasoning from composite model

### 4. 📊 Portfolio Analyzer
Input any basket of NSE stocks and get:
- Portfolio risk score (Beta, Volatility, Max Drawdown)
- Diversification score with sector allocation chart
- Per-stock technical signals
- Actionable rebalancing suggestions

### 5. 🎬 Video Generator
Generate shareable 5–10 second MP4 market summary videos. Animated signal cards, price data, and ARTHA branding. Falls back gracefully to text report if FFmpeg unavailable.

---

## 🏗️ Architecture

```
ARTHA AI
│
├── app.py                  # Streamlit frontend + page routing
│
├── modules/
│   ├── data_fetch.py       # yfinance NSE data layer + symbol normalization
│   ├── indicators.py       # RSI, MA, EMA, MACD, Bollinger, Volume, S&R, Trend
│   ├── signals.py          # Composite signal engine + Opportunity Radar scanner
│   ├── patterns.py         # Chart pattern detection + Premium Plotly charts
│   ├── chat_engine.py      # Rule-based conversational analysis engine
│   ├── portfolio.py        # Portfolio risk + diversification analyzer
│   └── video_engine.py     # MoviePy MP4 generator with graceful fallback
│
├── assets/
│   ├── generated_videos/   # MP4 output directory
│   └── images/             # Static assets
│
└── requirements.txt
```

**Data Flow:**
```
NSE Live → yfinance → data_fetch → indicators → signals
                                              ↓
                              patterns + chat_engine + portfolio
                                              ↓
                                     Streamlit UI (app.py)
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.9+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/artha-ai.git
cd artha-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Install FFmpeg for video generation
# macOS:   brew install ffmpeg
# Ubuntu:  sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html

# 4. Launch ARTHA AI
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📸 Screenshots

> *(Add screenshots to /screenshots folder after running the app)*

| Module | Description |
|--------|-------------|
| `screenshots/radar.png` | Opportunity Radar — ranked signal table |
| `screenshots/deep_dive.png` | Stock Deep Dive — candlestick chart |
| `screenshots/chat.png` | Market Chat — structured verdict |
| `screenshots/portfolio.png` | Portfolio Analyzer — risk dashboard |
| `screenshots/video.png` | Video Generator — MP4 export |

---

## 🔧 Technical Stack

| Component | Technology |
|-----------|------------|
| Frontend | Streamlit + Custom CSS |
| Charts | Plotly (Candlestick, Pie, Subplots) |
| Data Source | yfinance (NSE via .NS suffix) |
| Technical Analysis | Custom NumPy/Pandas engine |
| Video Engine | MoviePy + Matplotlib |
| Auto-refresh | streamlit-autorefresh (60s) |
| Caching | @st.cache_data (TTL: 60s) |

---

## 📊 Supported NSE Stocks

ARTHA AI supports **any NSE-listed stock**. Common examples:

```
RELIANCE, TCS, INFY, HDFCBANK, ICICIBANK, WIPRO, BAJFINANCE,
SBIN, AXISBANK, KOTAKBANK, TATAMOTORS, SUNPHARMA, BHARTIARTL,
TITAN, NTPC, ONGC, HCLTECH, M&M, LT, ASIANPAINT, DMART...
```

Simply type the NSE symbol — ARTHA AI auto-resolves to `.NS` format.

---

## ⚠️ Disclaimer

ARTHA AI is built for **educational purposes only**. It is not SEBI-registered investment advice. All signals are based on technical analysis and do not guarantee future performance. Always do your own research (DYOR) and consult a SEBI-registered financial advisor before investing.

---

## 🤝 Contributing

PRs welcome. Fork → Feature branch → PR. Please maintain the Bloomberg-dark aesthetic for any UI contributions.

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.

---

<div align="center">
  <strong>Built with ❤️ for Indian Investors</strong><br>
  <sub>ARTHA AI — Because every investor deserves Bloomberg-grade intelligence.</sub>
</div>
